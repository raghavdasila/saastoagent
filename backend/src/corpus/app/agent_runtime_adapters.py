from __future__ import annotations

import json
import hashlib
import threading
import uuid
from collections.abc import Mapping
from collections.abc import Callable
from dataclasses import dataclass
from importlib.metadata import PackageNotFoundError, version as package_version
from pathlib import Path
from typing import Any

import ollama
from langchain_core.language_models import BaseChatModel
from pydantic import BaseModel, ConfigDict, Field

from agent_execution_runtime import ApiCallResult, RoutingCandidate, RoutingDecision
from agent_execution_runtime.ports import ModelDecision, ModelToolRequest, ReviewResult

from corpus.features.builder.domain import BuilderInputSnapshot, BuilderRecord, RuntimeBuildArtifact
from corpus.features.builder.ports import BuilderRuntimeGateway, BuilderUnavailable
from corpus.features.builder.navgraph import compile_agent_navgraph
from corpus.features.sandbox.domain import RuntimeSandboxRun
from corpus.features.sources.connectors.api.engine import SourceManagedParameter
from corpus.features.sources.connectors.api.toolrouter import ToolRouterApiSourceEngine
from corpus.app.agent_routedeck_runtime import AgentRouteDeckSupervisor, agent_route_session
from corpus.integrations.agent_execution import (
    BuildConnectionSpec, EvaluationCaseSpec, ImmutableBuildSpec,
    NeutralAgentExecutionAdapter, NeutralEvaluationAdapter, SandboxRunSpec,
)
from corpus.integrations.api_execution.routed import RoutedApiExecutionAdapter, RoutedApiExecutionTarget


class _ToolRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    call_id: str = Field(min_length=1, max_length=80)
    query: str = Field(min_length=1, max_length=4_000)


class _Decision(BaseModel):
    model_config = ConfigDict(extra="forbid")
    action: str = Field(pattern="^(answer|api)$")
    response: str = Field(default="", max_length=12_000)
    requests: tuple[_ToolRequest, ...] = Field(default=(), max_length=4)


class _EvaluationReview(BaseModel):
    model_config = ConfigDict(extra="forbid")
    passed: bool
    reasons: tuple[str, ...] = Field(default=(), max_length=12)


class CorpusAgentModelPort:
    def __init__(self, model: BaseChatModel, *, plain_json: bool = False) -> None:
        self.model = model
        self.plain_json = plain_json
        self.decision_model = model if plain_json else model.with_structured_output(_Decision)

    def decide(self, build, message: str) -> ModelDecision:
        system = (
            "You operate one immutable Corpus Agent build. Answer directly when no external "
            "operation is needed. When the user needs external data, set action to api and "
            "pass the user's unresolved intent to the router. Do not choose an allowed "
            "operation by name or split one ambiguous intent merely to avoid clarification; "
            "ToolRouter owns operation selection and clarification. Split only when the user "
            "explicitly requests multiple distinct facts. Never use answer to ask for an "
            "operation choice or missing external input. If the user requests connected "
            "data, action must be api even when required details are missing; pass one "
            "unresolved request so ToolRouter can preserve the waiting run. When action is "
            "api, response must be empty and requests must be nonempty. When action is "
            "answer, requests must be empty. Never invent inputs or credentials."
        )
        if self.plain_json:
            system += (
                " Return only one JSON object matching exactly: "
                '{"action":"answer|api","response":"string","requests":'
                '[{"call_id":"unique string","query":"exact user request"}]}. '
                "Use an empty requests array for answer and at least one request for api."
            )
        result = self.decision_model.invoke([
            ("system", system),
            ("system", f"Allowed operation identities: {', '.join(build.allowed_operations)}"),
            ("human", message),
        ])
        if self.plain_json:
            result = _Decision.model_validate(_plain_json_object(result))
        elif not isinstance(result, _Decision):
            result = _Decision.model_validate(result)
        requests = tuple(ModelToolRequest(item.call_id, item.query) for item in result.requests)
        if result.action == "api" and not requests:
            raise ValueError("agent_model_api_requests_required")
        if result.action == "answer" and requests:
            raise ValueError("agent_model_direct_answer_cannot_request_api")
        return ModelDecision(action=result.action, requests=requests, response=result.response)

    def answer(self, build, message: str, results) -> str:
        safe_results = [{
            "operation_id": item.operation_id, "status": item.status,
            "http_status": item.http_status, "error_code": item.error_code,
            "public_message": item.public_message, "outcome_verified": item.outcome_verified,
            "response": item.response,
        } for item in results]
        response = self.model.invoke([
            ("system", "Answer as the immutable Corpus Agent build using only the safe execution outcomes. State unavailable details plainly; never claim unseen response content."),
            ("human", json.dumps({"request": message, "results": safe_results}, sort_keys=True)),
        ])
        text = _message_text(response)
        if not text:
            raise RuntimeError("agent_model_empty_response")
        return text


class CorpusEvaluationReviewerPort:
    def __init__(self, model: BaseChatModel, model_identity: Callable[[], tuple[str, str]], *, plain_json: bool = False) -> None:
        self.plain_json = plain_json
        self.model = model if plain_json else model.with_structured_output(_EvaluationReview)
        self.model_identity = model_identity

    def review(self, case, run, events) -> ReviewResult:
        evidence = {
            "expected_operation_ids": list(case.expected_operations),
            "run_status": run.status.value,
            "final_response": run.final_response,
            "events": [
                {"sequence": event.sequence, "kind": event.kind, "safe_data": dict(event.safe_data)}
                for event in events if event.kind not in {"user.message", "model.decision", "router.decision"}
            ],
        }
        prompt = json.dumps(evidence, sort_keys=True, separators=(",", ":"), default=str)
        system = (
            "Review this immutable Agent evaluation evidence. Pass only when the final "
            "response is truthful and consistent with the completed safe operation evidence. "
            "Raw API response bodies are intentionally absent for privacy. Do not fail merely "
            "because a truthful body-content statement cannot be independently reconstructed "
            "from the redacted response summary; fail when the final response contradicts the "
            "retained status, operation, validation, outcome, or response-shape evidence. "
            "Return concise non-secret reasons."
        )
        if self.plain_json:
            system += ' Return only one JSON object matching exactly: {"passed":true|false,"reasons":["concise reason"]}.'
        value = self.model.invoke([
            ("system", system),
            ("human", prompt),
        ])
        if self.plain_json:
            value = _EvaluationReview.model_validate(_plain_json_object(value))
        elif not isinstance(value, _EvaluationReview):
            value = _EvaluationReview.model_validate(value)
        model_name, model_digest = self.model_identity()
        return ReviewResult(
            value.passed, value.reasons, model_name, model_digest,
            hashlib.sha256(prompt.encode("utf-8")).hexdigest(), 0,
        )


def _plain_json_object(response: object) -> dict[str, object]:
    content = getattr(response, "content", response)
    if not isinstance(content, str):
        raise ValueError("agent_model_json_text_required")
    text = content.strip()
    if text.startswith("```json\n") and text.endswith("\n```"):
        text = text[len("```json\n") : -len("\n```")].strip()
    value = json.loads(text)
    if not isinstance(value, dict):
        raise ValueError("agent_model_json_object_required")
    return value


def _message_text(response: object) -> str:
    content = getattr(response, "content", response)
    if isinstance(content, str):
        return content.strip()
    text = getattr(response, "text", None)
    if isinstance(text, str):
        return text.strip()
    raise RuntimeError("agent_model_text_response_required")


@dataclass(frozen=True)
class CorpusEvaluationRuntimeGateway:
    runtime: NeutralEvaluationAdapter

    def promote(self, *, tenant_id, run_id, message, expected_operation_ids, required_response_fields, require_write_verification):
        return self.runtime.promote(EvaluationCaseSpec(
            tenant_id=tenant_id, run_id=run_id, message=message,
            expected_operation_ids=expected_operation_ids,
            required_response_fields=required_response_fields,
            require_write_verification=require_write_verification,
        ))

    def evaluate(self, tenant_id, runtime_case_id):
        return self.runtime.evaluate(tenant_id, runtime_case_id)

    def eligibility(self, runtime_build_hash, runtime_case_ids):
        return self.runtime.eligibility(runtime_build_hash, runtime_case_ids)


class CorpusExecutionBindingRegistry:
    def __init__(self) -> None:
        self._lock = threading.RLock()
        self._bindings: dict[str, tuple[dict[str, object], ...]] = {}
        self._builds: dict[str, BuilderRecord] = {}

    def bind(self, build: BuilderRecord) -> None:
        if build.runtime_build_hash is None or not build.source_bindings:
            raise BuilderUnavailable("The exact runtime build bindings are unavailable.")
        with self._lock:
            existing = self._bindings.get(build.runtime_build_hash)
            if existing is not None and existing != build.source_bindings:
                raise BuilderUnavailable("The runtime build binding identity is inconsistent.")
            self._bindings[build.runtime_build_hash] = build.source_bindings
            existing_build = self._builds.get(build.runtime_build_hash)
            if existing_build is not None and existing_build != build:
                raise BuilderUnavailable("The runtime build identity is inconsistent.")
            self._builds[build.runtime_build_hash] = build

    def get(self, build_hash: str) -> tuple[dict[str, object], ...]:
        with self._lock:
            value = self._bindings.get(build_hash)
        if value is None:
            raise BuilderUnavailable("The exact runtime build bindings are unavailable.")
        return value

    def get_build(self, build_hash: str) -> BuilderRecord:
        with self._lock:
            value = self._builds.get(build_hash)
        if value is None:
            raise BuilderUnavailable("The exact runtime build identity is unavailable.")
        return value


class CorpusToolRouterPort:
    def __init__(self, engine: ToolRouterApiSourceEngine, bindings: CorpusExecutionBindingRegistry) -> None:
        self.engine, self.bindings = engine, bindings

    def route(self, build, query: str, provided: Mapping[str, Any]) -> RoutingDecision:
        selected = provided.get("__selected_operation_id")
        routed_inputs = _toolrouter_inputs(provided)
        bindings = self.bindings.get(build.content_hash)
        if selected is not None:
            selected = str(selected)
            matching_bindings = tuple(
                item
                for item in bindings
                if selected in tuple(map(str, item["included_operation_ids"]))
            )
            if len(matching_bindings) != 1:
                raise BuilderUnavailable(
                    "The selected clarification operation is not uniquely bound."
                )
            bindings = matching_bindings
        results = []
        for binding in bindings:
            allowed_operations = (
                (selected,)
                if selected is not None
                else tuple(map(str, binding["included_operation_ids"]))
            )
            endpoint_by_operation = _toolrouter_endpoint_map(
                Path(str(binding["artifact_dir"])), allowed_operations
            )
            operation_by_endpoint = {
                endpoint_id: operation_id
                for operation_id, endpoint_id in endpoint_by_operation.items()
            }
            managed = ()
            if binding.get("authentication_method") == "api_key" and binding.get("credential_name"):
                managed = (SourceManagedParameter(name=str(binding["credential_name"]), location="header"),)
            result = self.engine.retrieve(
                artifact_dir=Path(str(binding["artifact_dir"])), query=query, top_k=5,
                trace_mode="bounded", provided_params=routed_inputs,
                allowed_endpoint_ids=tuple(
                    endpoint_by_operation[value] for value in allowed_operations
                ),
                managed_parameters=managed,
            )
            results.append((result, operation_by_endpoint))
        candidates = tuple(sorted((
            RoutingCandidate(operation_by_endpoint[item.item_id], item.score)
            for result, operation_by_endpoint in results
            for step in result.steps for item in step.ranked_items
        ), key=lambda item: item.score, reverse=True)[:5])
        if not candidates:
            return RoutingDecision("NO_TOOL", "no_candidate_in_accepted_build")
        matching = [
            result
            for result, _operation_by_endpoint in results
            if any(step.ranked_items for step in result.steps)
        ]
        if len(matching) == 1:
            result = matching[0]
            return RoutingDecision(result.decision_type, result.decision_reason, candidates, result.missing_inputs)
        return RoutingDecision("ASK_DISAMBIGUATE", "multiple_accepted_sources_match", candidates)


def _toolrouter_endpoint_map(
    artifact_dir: Path, operation_ids: tuple[str, ...]
) -> dict[str, str]:
    graph_path = artifact_dir / "graph" / "semantic_graph.json"
    graph = json.loads(graph_path.read_text(encoding="utf-8"))
    matches = {operation_id: set() for operation_id in operation_ids}
    for node in graph.get("nodes", ()):
        if not isinstance(node, dict):
            continue
        facets = node.get("facets")
        operation_id = facets.get("operation_id") if isinstance(facets, dict) else None
        endpoint_id = node.get("endpoint_id")
        if operation_id in matches and isinstance(endpoint_id, str) and endpoint_id:
            matches[str(operation_id)].add(endpoint_id)
    invalid = [key for key, values in matches.items() if len(values) != 1]
    if invalid:
        raise BuilderUnavailable(
            "Every accepted operation must resolve to one exact persisted endpoint."
        )
    return {key: next(iter(values)) for key, values in matches.items()}


class CorpusApiExecutorPort:
    def __init__(self, execution: RoutedApiExecutionAdapter, bindings: CorpusExecutionBindingRegistry) -> None:
        self.execution, self.bindings = execution, bindings
        self.supervisor = None

    def attach_supervisor(self, supervisor) -> None:
        if self.supervisor is not None:
            raise RuntimeError("agent_routedeck_supervisor_already_attached")
        self.supervisor = supervisor

    async def execute(self, *, build, tenant_id: str, operation_id: str, inputs: Mapping[str, Any], execution_id: str) -> ApiCallResult:
        if self.supervisor is None:
            raise BuilderUnavailable("The Agent RouteDeck supervisor is unavailable.")
        record = self.bindings.get_build(build.content_hash)
        supervised = await self.supervisor.execute(
            build=record,
            tenant_id=tenant_id,
            operation_id=operation_id,
            inputs=_routedeck_tool_arguments(inputs),
            execution_id=execution_id,
        )
        if supervised.api_result is not None:
            return supervised.api_result
        if supervised.operation.disposition.value == "requires_review":
            return ApiCallResult(
                execution_id, operation_id, "failed", None, None,
                "review_required", False,
                "Review is required before this Agent can send the external write.", (),
            )
        failure = supervised.operation.failure
        return ApiCallResult(
            execution_id, operation_id, "failed", None, None,
            failure.code if failure is not None else "routedeck_operation_failed", False,
            failure.public_message if failure is not None else "The supervised Agent operation did not complete.", (),
        )

    async def execute_direct(
        self,
        *,
        build: BuilderRecord,
        tenant_id: str,
        operation_id: str,
        inputs: Mapping[str, Any],
        execution_id: str,
        approved_write: bool,
    ) -> ApiCallResult:
        matches = [item for item in build.source_bindings if operation_id in set(map(str, item["included_operation_ids"]))]
        if len(matches) != 1:
            raise BuilderUnavailable("The operation does not have one exact runtime Source binding.")
        binding = matches[0]
        document = json.loads(Path(str(binding["document_path"])).read_text(encoding="utf-8"))
        split = lambda name: inputs.get(name, {}) if isinstance(inputs.get(name, {}), Mapping) else {}
        result, response_body = await self.execution.execute_for_agent(RoutedApiExecutionTarget(
            execution_id=execution_id, owner_id=uuid.UUID(tenant_id),
            connection_profile_id=str(binding["profile_id"]), base_url=str(binding["base_url"]),
            authentication_method=str(binding["authentication_method"]),
            credential_name=(str(binding["credential_name"]) if binding.get("credential_name") else None),
            credential_reference_id=(uuid.UUID(str(binding["credential_reference_id"])) if binding.get("credential_reference_id") else None),
            credential_version=(int(binding["credential_version"]) if binding.get("credential_version") is not None else None),
            document_hash=str(binding["document_hash"]), document=document, operation_id=operation_id,
            path=split("path"), query=split("query"), header=split("header"), cookie=split("cookie"),
            body=inputs.get("body"), approved_write=approved_write,
        ))
        return ApiCallResult(
            execution_id, operation_id, result.status, result.status_code,
            response_body,
            result.error_code, result.outcome_verified, result.public_message,
            tuple(f"{phase}: contract validation failed" for phase in result.validation_phases),
        )


@dataclass(frozen=True)
class CorpusBuilderRuntimeGateway(BuilderRuntimeGateway):
    runtime: NeutralAgentExecutionAdapter
    model_identity: Callable[[], tuple[str, str]]

    async def assemble(self, snapshot: BuilderInputSnapshot) -> RuntimeBuildArtifact:
        model_name, model_digest = self.model_identity()
        navgraph = compile_agent_navgraph(snapshot)
        operations = tuple(operation for item in snapshot.source_bindings for operation in item.included_operation_ids)
        projection = self.runtime.assemble(ImmutableBuildSpec(
            build_id=str(snapshot.build_id), version=1, name=snapshot.name,
            instructions=snapshot.instructions, model=model_name, model_digest=model_digest,
            source_path=f"corpus://design-revisions/{snapshot.design_revision_id}",
            source_hash=snapshot.input_fingerprint, allowed_operations=operations,
            preauthorized_write_operations=(),
            connections=tuple(BuildConnectionSpec(
                connection_id=item.profile_id, revision=item.credential_version or 1,
                base_url=item.base_url, openapi_path=str(item.document_path), openapi_hash=item.document_hash,
                auth_plugin_id=item.authentication_method,
                credential_ref=(str(item.credential_reference_id) if item.credential_reference_id else None),
                operation_ids=item.included_operation_ids,
            ) for item in snapshot.source_bindings),
        ))
        return RuntimeBuildArtifact(
            projection.content_hash, model_name, model_digest, projection.operation_ids,
            navgraph.navgraph_hash, navgraph.compiled_navgraph, navgraph.frontend_contract,
        )

    async def validate_immutable_build(self, runtime_build_hash: str) -> None:
        try:
            projection = self.runtime.load_build(runtime_build_hash)
        except Exception as error:
            raise BuilderUnavailable("The exact immutable Agent build is unavailable.") from error
        if projection.content_hash != runtime_build_hash:
            raise BuilderUnavailable("The exact immutable Agent build identity is inconsistent.")


@dataclass(frozen=True)
class CorpusSandboxRuntimeGateway:
    runtime: NeutralAgentExecutionAdapter
    bindings: CorpusExecutionBindingRegistry
    routedeck: AgentRouteDeckSupervisor

    async def start(self, *, organization_id, session_id, run_id, build, message):
        self.bindings.bind(build)
        with agent_route_session(session_id):
            projection = await self.runtime.run(SandboxRunSpec(
                tenant_id=str(organization_id), session_id=session_id,
                build_hash=build.runtime_build_hash, message=message, run_id=run_id,
            ))
        routedeck_projection = await self.routedeck.projection(build, session_id, str(organization_id))
        return RuntimeSandboxRun(
            projection.run_id, projection.status, projection.awaiting, projection.final_response,
            projection.api_call_count,
            sandbox_safe_events(build, projection.events),
            routedeck_projection,
        )

    async def resume(
        self,
        *,
        organization_id,
        record,
        build,
        message,
        selected_operation_id,
        answers,
    ):
        candidates, missing = clarification_context(record.safe_events)
        operation_id = selected_operation_id
        if operation_id is None and len(candidates) == 1:
            operation_id = candidates[0]
        if operation_id is None or operation_id not in candidates:
            raise BuilderUnavailable("Choose one exact operation from the waiting run.")
        if set(answers) != set(missing):
            raise BuilderUnavailable("Answer every exact missing input and no others.")
        provided = clarification_inputs(
            self.bindings.get(build.runtime_build_hash), operation_id, answers
        )
        with agent_route_session(record.runtime_session_id):
            projection = await self.runtime.run(SandboxRunSpec(
                tenant_id=str(organization_id),
                session_id=record.runtime_session_id,
                build_hash=build.runtime_build_hash,
                message=message,
                run_id=record.runtime_run_id,
                command="resume",
                selected_operation_id=operation_id,
                provided_inputs=provided,
            ))
        routedeck_projection = await self.routedeck.projection(
            build, record.runtime_session_id, str(organization_id)
        )
        return RuntimeSandboxRun(
            projection.run_id,
            projection.status,
            projection.awaiting,
            projection.final_response,
            projection.api_call_count,
            sandbox_safe_events(build, projection.events),
            routedeck_projection,
        )


def sandbox_safe_events(build, events) -> tuple[dict[str, object], ...]:
    labels = _sandbox_operation_labels(build)
    result: list[dict[str, object]] = []
    for item in events:
        if isinstance(item, Mapping):
            sequence = item.get("sequence")
            kind = item.get("kind")
            occurred_at = item.get("occurred_at")
            raw_safe_data = item.get("safe_data", {})
        else:
            sequence = getattr(item, "sequence", None)
            kind = getattr(item, "kind", None)
            occurred_at = getattr(item, "occurred_at", None)
            raw_safe_data = getattr(item, "safe_data", {})
        if not isinstance(raw_safe_data, Mapping):
            raise BuilderUnavailable("The Sandbox runtime event evidence is invalid.")
        safe_data: dict[str, object] = dict(raw_safe_data)
        if kind == "router.decision":
            raw_candidates = safe_data.get("candidates", ())
            if not isinstance(raw_candidates, (list, tuple)):
                raise BuilderUnavailable("The Sandbox clarification candidates are invalid.")
            candidates: list[dict[str, object]] = []
            for raw_candidate in raw_candidates:
                if not isinstance(raw_candidate, Mapping) or not raw_candidate.get("operation_id"):
                    raise BuilderUnavailable("The Sandbox clarification candidate is invalid.")
                operation_id = str(raw_candidate["operation_id"])
                label = labels.get(operation_id)
                if label is None:
                    raise BuilderUnavailable("The Sandbox clarification candidate is not in the immutable NavGraph.")
                candidates.append({**dict(raw_candidate), "label": label})
            safe_data["candidates"] = candidates
        result.append({
            "sequence": sequence,
            "kind": kind,
            "occurred_at": occurred_at,
            "safe_data": safe_data,
        })
    return tuple(result)


def _sandbox_operation_labels(build) -> dict[str, str]:
    navgraph = getattr(build, "compiled_navgraph", None)
    raw_nodes = navgraph.get("nodes") if isinstance(navgraph, Mapping) else None
    if not isinstance(raw_nodes, list):
        raise BuilderUnavailable("The immutable Sandbox NavGraph is unavailable.")
    labels: dict[str, str] = {}
    for raw_node in raw_nodes:
        if not isinstance(raw_node, Mapping):
            continue
        raw_operations = raw_node.get("operations", ())
        if not isinstance(raw_operations, list):
            raise BuilderUnavailable("The immutable Sandbox NavGraph operations are invalid.")
        for raw_operation in raw_operations:
            if not isinstance(raw_operation, Mapping):
                continue
            metadata = raw_operation.get("public_metadata")
            operation_id = metadata.get("source_operation_id") if isinstance(metadata, Mapping) else None
            title = raw_operation.get("title")
            if not isinstance(operation_id, str) or not operation_id or not isinstance(title, str) or not title:
                continue
            previous = labels.get(operation_id)
            if previous is not None and previous != title:
                raise BuilderUnavailable("The immutable Sandbox NavGraph has conflicting operation labels.")
            labels[operation_id] = title
    return labels


def clarification_context(events) -> tuple[tuple[str, ...], tuple[str, ...]]:
    def parts(item):
        if isinstance(item, Mapping):
            return item.get("kind"), item.get("safe_data", {})
        return getattr(item, "kind", None), getattr(item, "safe_data", {})

    decisions = [parts(item)[1] for item in events if parts(item)[0] == "router.decision"]
    if not decisions:
        raise BuilderUnavailable("The waiting run has no safe clarification evidence.")
    safe_data = decisions[-1]
    if not isinstance(safe_data, Mapping):
        raise BuilderUnavailable("The waiting clarification evidence is invalid.")
    candidates = tuple(dict.fromkeys(
        str(item.get("operation_id"))
        for item in safe_data.get("candidates", ())
        if isinstance(item, Mapping) and item.get("operation_id")
    ))
    missing = tuple(dict.fromkeys(
        str(item) for item in safe_data.get("missing_params", ()) if str(item)
    ))
    if not candidates:
        raise BuilderUnavailable("The waiting run has no allowed operation candidate.")
    return candidates, missing


def clarification_inputs(bindings, operation_id: str, answers: Mapping[str, str]):
    matches = tuple(
        item
        for item in bindings
        if operation_id in tuple(map(str, item.get("included_operation_ids", ())))
    )
    if len(matches) != 1:
        raise BuilderUnavailable("The clarification operation binding is unavailable.")
    document = json.loads(Path(str(matches[0]["document_path"])).read_text(encoding="utf-8"))
    operation_match = None
    for path_template, raw_path_item in document.get("paths", {}).items():
        if not isinstance(raw_path_item, Mapping):
            continue
        for method, raw_operation in raw_path_item.items():
            if method.casefold() not in {"get", "post", "put", "patch", "delete", "head", "options"}:
                continue
            if isinstance(raw_operation, Mapping) and raw_operation.get("operationId") == operation_id:
                operation_match = (raw_path_item, raw_operation)
    if operation_match is None:
        raise BuilderUnavailable("The clarification operation contract is unavailable.")
    path_item, operation = operation_match
    parameters = [*(path_item.get("parameters") or ()), *(operation.get("parameters") or ())]
    located: dict[str, str] = {}
    for name in answers:
        choices = tuple(
            str(item.get("in"))
            for item in parameters
            if isinstance(item, Mapping)
            and str(item.get("name", "")).casefold() == name.casefold()
            and str(item.get("in")) in {"path", "query", "header", "cookie"}
        )
        if len(choices) != 1:
            raise BuilderUnavailable("Each clarification input must have one exact declared location.")
        located[name] = choices[0]
    provided: dict[str, object] = {
        "__selected_operation_id": operation_id,
        **{name: value for name, value in answers.items()},
    }
    for name, location in located.items():
        bucket = provided.setdefault(location, {})
        assert isinstance(bucket, dict)
        bucket[name] = answers[name]
    return provided


def _toolrouter_inputs(provided: Mapping[str, Any]) -> dict[str, Any]:
    routed: dict[str, Any] = {}
    for name, value in provided.items():
        if name == "__selected_operation_id" or name in {"path", "query", "header", "cookie"}:
            continue
        routed[str(name)] = value
    for location in ("path", "query", "header", "cookie"):
        values = provided.get(location, {})
        if not isinstance(values, Mapping):
            raise BuilderUnavailable("Clarification inputs have an invalid location binding.")
        for name, value in values.items():
            key = str(name)
            if key in routed and routed[key] != value:
                raise BuilderUnavailable("Clarification inputs contain conflicting values.")
            routed[key] = value
    return routed


def _routedeck_tool_arguments(provided: Mapping[str, Any]) -> dict[str, Any]:
    """Remove router-only coordination values before RouteDeck validates a tool call."""
    arguments: dict[str, Any] = {}
    for location in ("path", "query", "header", "cookie"):
        value = provided.get(location)
        if value is None:
            continue
        if not isinstance(value, Mapping):
            raise BuilderUnavailable("Agent tool inputs have an invalid location binding.")
        arguments[location] = dict(value)
    if "body" in provided:
        arguments["body"] = provided["body"]
    return arguments


def resolve_ollama_model_identity(base_url: str, model: str) -> tuple[str, str]:
    try:
        listing = ollama.Client(host=base_url).list()
    except Exception as error:
        raise BuilderUnavailable("The configured local model inventory is unavailable.") from error
    for value in listing.models:
        if value.model == model or value.model == f"{model}:latest":
            digest = str(value.digest or "")
            if digest:
                return model, digest
    raise BuilderUnavailable("The configured local model does not expose an immutable digest.")


def resolve_openai_model_identity(model: str) -> tuple[str, str]:
    """Return the exact configured OpenAI runtime identity without switching providers."""
    normalized = model.strip()
    if not normalized:
        raise BuilderUnavailable("The configured OpenAI model identity is unavailable.")
    try:
        adapter_version = package_version("langchain-openai")
    except PackageNotFoundError as error:
        raise BuilderUnavailable("The configured OpenAI adapter identity is unavailable.") from error
    identity = f"openai:{normalized}:langchain-openai:{adapter_version}"
    return f"openai/{normalized}", hashlib.sha256(identity.encode("utf-8")).hexdigest()


__all__ = [
    "CorpusAgentModelPort", "CorpusApiExecutorPort", "CorpusBuilderRuntimeGateway",
    "CorpusEvaluationReviewerPort", "CorpusEvaluationRuntimeGateway",
    "CorpusExecutionBindingRegistry", "CorpusSandboxRuntimeGateway", "CorpusToolRouterPort",
    "clarification_context", "clarification_inputs", "resolve_ollama_model_identity",
    "resolve_openai_model_identity", "sandbox_safe_events",
]
