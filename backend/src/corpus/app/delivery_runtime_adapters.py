from __future__ import annotations

import asyncio
import re
import uuid

from agent_execution_runtime import ApiCallResult
from agent_delivery_runtime.domain import DeployableAgentBundle
from agent_delivery_runtime.ports import RuntimeProjection, RuntimeReadiness

from corpus.clarification import (
    ClarificationInputRejected,
    parse_clarification_answers,
)
from corpus.app.agent_runtime_adapters import clarification_context, clarification_inputs
from corpus.app.agent_routedeck_runtime import AgentRouteDeckSupervisor, agent_route_session
from corpus.integrations.agent_execution import NeutralAgentExecutionAdapter, SandboxRunSpec


class CorpusDeployedAgentRuntimePort:
    """Runs deployment-pinned builds through the Corpus execution boundary."""

    def __init__(
        self,
        execution: NeutralAgentExecutionAdapter,
        bindings,
        builds,
        routedeck: AgentRouteDeckSupervisor,
    ) -> None:
        self.execution = execution
        self.bindings = bindings
        self.builds = builds
        self.routedeck = routedeck

    def verify(self, bundle: DeployableAgentBundle) -> RuntimeReadiness:
        build_hash, tenant_id = _runtime_identity(bundle)
        self._restore_binding(bundle, build_hash)
        build = self.execution.load_build(build_hash)
        if build.content_hash != bundle.content_hash:
            raise ValueError("deployment_build_hash_mismatch")
        return RuntimeReadiness(
            ready=True,
            provider="corpus-agent-execution-runtime",
            model=str(bundle.runtime_config.get("model", "pinned")),
            evidence={
                "build_hash": build.content_hash,
                "tenant_id_hash": _opaque(tenant_id),
                "operation_count": len(build.operation_ids),
            },
        )

    def create_session(self, bundle: DeployableAgentBundle) -> str:
        _runtime_identity(bundle)
        return str(uuid.uuid4())

    def projection(self, bundle: DeployableAgentBundle, runtime_session_id: str) -> RuntimeProjection:
        build_hash, tenant_id = _runtime_identity(bundle)
        build = self._restore_binding(bundle, build_hash)
        route_projection = asyncio.run(
            self.routedeck.projection(build, runtime_session_id, tenant_id)
        )
        waiting = self.execution.waiting_run(tenant_id, runtime_session_id, build_hash)
        messages = self.execution.session_messages(
            tenant_id, runtime_session_id, build_hash
        )
        return _projection(waiting, route_projection, messages)

    def invoke(
        self,
        bundle: DeployableAgentBundle,
        runtime_session_id: str,
        text: str,
        request_id: str,
    ) -> RuntimeProjection:
        build_hash, tenant_id = _runtime_identity(bundle)
        build = self._restore_binding(bundle, build_hash)
        waiting = self.execution.waiting_run(tenant_id, runtime_session_id, build_hash)
        if waiting is None:
            spec = SandboxRunSpec(
                tenant_id=tenant_id,
                session_id=runtime_session_id,
                build_hash=build_hash,
                message=text,
                run_id=request_id,
            )
        else:
            candidates, missing = clarification_context(waiting.events)
            operation_id = _selected_operation(text, candidates, missing)
            try:
                answers = parse_clarification_answers(text, missing)
            except ClarificationInputRejected:
                return _projection(waiting, asyncio.run(
                    self.routedeck.projection(build, runtime_session_id, tenant_id)
                ), self.execution.session_messages(
                    tenant_id, runtime_session_id, build_hash
                ))
            if operation_id is None:
                return _projection(waiting, asyncio.run(
                    self.routedeck.projection(build, runtime_session_id, tenant_id)
                ), self.execution.session_messages(
                    tenant_id, runtime_session_id, build_hash
                ))
            provided = clarification_inputs(
                self.bindings.get(build_hash), operation_id, answers
            )
            spec = SandboxRunSpec(
                tenant_id=tenant_id,
                session_id=runtime_session_id,
                build_hash=build_hash,
                message=text,
                run_id=waiting.run_id,
                command="resume",
                selected_operation_id=operation_id,
                provided_inputs=provided,
            )
        with agent_route_session(runtime_session_id, tenant_id):
            result = asyncio.run(self.execution.run(spec))
        route_projection = asyncio.run(
            self.routedeck.projection(build, runtime_session_id, tenant_id)
        )
        messages = self.execution.session_messages(
            tenant_id, runtime_session_id, build_hash
        )
        if result.status == "waiting" and result.final_response:
            return _projection(result, route_projection, messages)
        if result.status != "succeeded" or not result.final_response:
            raise RuntimeError("deployed_agent_run_failed")
        return _projection(result, route_projection, messages)

    def resolve_review(
        self,
        bundle: DeployableAgentBundle,
        runtime_session_id: str,
        review_id: str,
        accepted: bool,
        request_id: str,
    ) -> RuntimeProjection:
        build_hash, tenant_id = _runtime_identity(bundle)
        build = self._restore_binding(bundle, build_hash)
        pending = asyncio.run(
            self.routedeck.pending_review(build, runtime_session_id, tenant_id)
        )
        if pending is None or pending.review_id != review_id:
            raise RuntimeError("deployed_agent_review_unavailable")
        if not accepted:
            asyncio.run(self.routedeck.reject(
                build=build, tenant_id=tenant_id,
                session_id=runtime_session_id, review_id=review_id,
                request_id=request_id,
            ))
            waiting = self._review_waiting_run(
                tenant_id, runtime_session_id, build_hash
            )
            rejected = ApiCallResult(
                request_id, pending.operation_id, "failed", None, None,
                "review_rejected", False,
                "The requested action was not sent.", (),
            )
            completed = self.execution.complete_reviewed_run(
                tenant_id=tenant_id, run_id=waiting.run_id,
                api_result=rejected,
            )
            return _projection(
                completed,
                asyncio.run(self.routedeck.projection(build, runtime_session_id, tenant_id)),
                self.execution.session_messages(tenant_id, runtime_session_id, build_hash),
            )
        resolved = asyncio.run(self.routedeck.accept(
            build=build, tenant_id=tenant_id, session_id=runtime_session_id,
            review_id=review_id, request_id=request_id,
        ))
        if resolved.api_result is None:
            raise RuntimeError("deployed_agent_review_failed")
        self.routedeck.retain_result(
            tenant_id=tenant_id,
            build_hash=build_hash,
            result=resolved.api_result,
            session_id=runtime_session_id,
        )
        waiting = self._review_waiting_run(
            tenant_id, runtime_session_id, build_hash
        )
        completed = self.execution.complete_reviewed_run(
            tenant_id=tenant_id,
            run_id=waiting.run_id,
            api_result=resolved.api_result,
        )
        return _projection(
            completed,
            asyncio.run(self.routedeck.projection(build, runtime_session_id, tenant_id)),
            self.execution.session_messages(tenant_id, runtime_session_id, build_hash),
        )

    def _review_waiting_run(self, tenant_id: str, session_id: str, build_hash: str):
        value = self.execution.waiting_run(tenant_id, session_id, build_hash)
        if value is None or value.awaiting != "write_review":
            raise RuntimeError("deployed_agent_review_run_unavailable")
        return value

    def _restore_binding(self, bundle: DeployableAgentBundle, build_hash: str):
        organization_id = uuid.UUID(str(bundle.runtime_config.get("organization_id")))
        agent_id = uuid.UUID(str(bundle.runtime_config.get("agent_id")))
        build_id = uuid.UUID(str(bundle.runtime_config.get("build_id")))
        build = asyncio.run(
            self.builds.require_immutable_built(organization_id, agent_id, build_id)
        )
        if build.runtime_build_hash != build_hash:
            raise ValueError("deployment_durable_build_binding_mismatch")
        self.bindings.bind(build)
        self.bindings.get(build_hash)
        return build


def _runtime_identity(bundle: DeployableAgentBundle) -> tuple[str, str]:
    build_hash = bundle.runtime_config.get("runtime_build_hash")
    tenant_id = bundle.runtime_config.get("organization_id")
    if not isinstance(build_hash, str) or len(build_hash) != 64:
        raise ValueError("deployment_runtime_build_required")
    if not isinstance(tenant_id, str) or not tenant_id:
        raise ValueError("deployment_owner_required")
    if bundle.content_hash != build_hash:
        raise ValueError("deployment_content_hash_invalid")
    return build_hash, tenant_id


def _opaque(value: str) -> str:
    import hashlib
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def _selected_operation(
    text: str, candidates: tuple[str, ...], missing: tuple[str, ...]
) -> str | None:
    if missing:
        return candidates[0] if len(candidates) == 1 else None
    normalized = text.strip()
    if normalized in candidates:
        return normalized
    user_terms = set(_words(normalized)) - _CHOICE_FILLER
    matches: set[str] = set()
    for candidate in candidates:
        subject = set(_operation_subject(candidate))
        if subject and subject.issubset(user_terms):
            matches.add(candidate)
    return next(iter(matches)) if len(matches) == 1 else None


_OPERATION_VERBS = frozenset({
    "get", "list", "read", "fetch", "retrieve", "search", "find", "create",
    "post", "put", "patch", "update", "delete", "remove",
})
_CHOICE_FILLER = frozenset({
    "use", "choose", "select", "the", "operation", "please", "i", "want",
    "would", "like", "me", "for",
})


def _words(value: str) -> tuple[str, ...]:
    expanded = re.sub(r"(?<=[a-z0-9])(?=[A-Z])", " ", value)
    return tuple(re.findall(r"[a-z0-9]+", expanded.casefold()))


def _operation_subject(operation_id: str) -> tuple[str, ...]:
    values = list(_words(operation_id))
    while values and values[0] in _OPERATION_VERBS:
        values.pop(0)
    if len(values) > 1 and values[-1] == "id":
        values.pop()
    return tuple(values)


def _projection(
    result,
    route_projection: dict[str, object],
    messages: tuple[dict[str, str], ...],
) -> RuntimeProjection:
    surfaces = _surfaces(route_projection, result)
    actions = route_projection.get("suggested_actions", ())
    if not isinstance(actions, list):
        raise RuntimeError("deployed_agent_routedeck_actions_invalid")
    return RuntimeProjection(
        revision=len(messages),
        messages=messages,
        surfaces=surfaces,
        suggested_actions=tuple(dict(item) for item in actions if isinstance(item, dict)),
    )


def _surfaces(route_projection: dict[str, object], result) -> tuple[dict[str, object], ...]:
    raw = route_projection.get("surfaces")
    if not isinstance(raw, dict):
        raise RuntimeError("deployed_agent_routedeck_surfaces_invalid")
    values: list[dict[str, object]] = []
    for slot, entry in raw.items():
        entries = entry if isinstance(entry, list) else ([] if entry is None else [entry])
        for item in entries:
            if not isinstance(item, dict):
                raise RuntimeError("deployed_agent_routedeck_surface_invalid")
            value = dict(item)
            value["slot"] = str(slot)
            values.append(value)
    clarification = _clarification(result)
    for value in values:
        component = value.get("component")
        if component == "agent_runtime.clarification":
            value["props"] = clarification
        elif component == "agent_runtime.write_review":
            value["props"] = _public_surface_props(value.get("props"))
        elif component == "agent_runtime.toolrouter_status":
            value["props"] = _router_status(result, clarification)
    return tuple(values)


def _public_surface_props(raw: object) -> dict[str, object]:
    """Convert RouteDeck's typed public values into product surface props."""
    if not isinstance(raw, list):
        raise RuntimeError("deployed_agent_surface_props_invalid")
    values: dict[str, object] = {}
    for item in raw:
        if not isinstance(item, dict):
            raise RuntimeError("deployed_agent_surface_prop_invalid")
        name = item.get("name")
        if (
            not isinstance(name, str)
            or not name
            or name in values
        ):
            raise RuntimeError("deployed_agent_surface_prop_invalid")
        values[name] = item.get("value")
    return values


def _clarification(result) -> dict[str, object]:
    if (
        result is None
        or result.status != "waiting"
        or result.awaiting == "write_review"
    ):
        return {"state": "idle", "question": "", "candidate_operation_ids": [], "missing_input_names": []}
    candidates, missing = clarification_context(result.events)
    return {
        "state": "needs_input" if missing else "needs_operation_choice",
        "question": result.final_response,
        "candidate_operation_ids": list(candidates),
        "missing_input_names": list(missing),
    }


def _router_status(result, clarification: dict[str, object]) -> dict[str, object]:
    if result is None:
        state = "idle"
    elif result.status == "waiting":
        state = "waiting"
    elif result.status == "succeeded":
        state = "completed"
    else:
        state = "failed"
    resolution = ""
    if clarification["state"] == "needs_input":
        resolution = "input_required"
    elif clarification["state"] == "needs_operation_choice":
        resolution = "operation_choice_required"
    return {"state": state, "event_count": len(result.events) if result is not None else 0, "last_resolution": resolution}


__all__ = ["CorpusDeployedAgentRuntimePort"]
