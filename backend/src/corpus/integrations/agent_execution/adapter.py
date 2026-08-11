from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any, Mapping

from agent_execution_runtime import (
    AgentBuild,
    AgentExecutionService,
    BuildLimits,
    ConnectionBinding,
    RunCommand,
)
from agent_execution_runtime.ports import ApiExecutorPort, ModelPort, RouterPort, RuntimeStore

from .contracts import (
    ImmutableBuildProjection,
    ImmutableBuildSpec,
    SandboxEventProjection,
    SandboxRunProjection,
    SandboxRunSpec,
)


_EVENT_FIELDS: dict[str, frozenset[str]] = {
    "model.decision": frozenset({"action"}),
    "router.decision": frozenset({"candidates", "missing_params"}),
    "api.started": frozenset({"call_id", "execution_id", "operation_id", "connection_id"}),
    "api.result": frozenset(
        {
            "call_id",
            "execution_id",
            "operation_id",
            "connection_id",
            "status",
            "http_status",
            "error_code",
            "public_message",
            "validation_issues",
            "outcome_verified",
            "response_summary",
        }
    ),
    "api.verification_started": frozenset(
        {"source_execution_id", "execution_id", "operation_id"}
    ),
    "api.verification_result": frozenset(
        {
            "source_execution_id",
            "execution_id",
            "operation_id",
            "status",
            "http_status",
            "error_code",
            "public_message",
            "validation_issues",
        }
    ),
    "run.waiting": frozenset({"status"}),
    "run.completed": frozenset({"status", "response"}),
    "run.cancelled": frozenset({"status"}),
    "run.failed": frozenset({"error_code", "elapsed_ms"}),
}


@dataclass(frozen=True)
class NeutralAgentExecutionAdapter:
    """Corpus boundary over the neutral runtime's public domain services.

    Corpus supplies the durable RuntimeStore and every external port. The
    standalone proof repository, proof UI, local credential map, and SQLite
    adapter are intentionally not imported here.
    """

    store: RuntimeStore
    model: ModelPort
    router: RouterPort
    executor: ApiExecutorPort

    def assemble(self, spec: ImmutableBuildSpec) -> ImmutableBuildProjection:
        build = AgentBuild(
            build_id=spec.build_id,
            version=spec.version,
            name=spec.name,
            instructions=spec.instructions,
            model=spec.model,
            model_digest=spec.model_digest,
            source_path=spec.source_path,
            source_hash=spec.source_hash,
            allowed_operations=spec.allowed_operations,
            preauthorized_write_operations=spec.preauthorized_write_operations,
            connections=tuple(
                ConnectionBinding(
                    connection_id=item.connection_id,
                    revision=item.revision,
                    base_url=item.base_url,
                    openapi_path=item.openapi_path,
                    openapi_hash=item.openapi_hash,
                    auth_plugin_id=item.auth_plugin_id,
                    credential_ref=item.credential_ref,
                    operation_ids=item.operation_ids,
                )
                for item in spec.connections
            ),
            limits=BuildLimits(
                max_turns=spec.max_turns,
                max_api_calls=spec.max_api_calls,
                max_parallel_calls=spec.max_parallel_calls,
                max_response_bytes=spec.max_response_bytes,
                max_elapsed_seconds=spec.max_elapsed_seconds,
            ),
        )
        _validate_build(build)
        self.store.save_build(build)
        persisted = self.store.get_build(build.content_hash)
        if persisted.content_hash != build.content_hash:
            raise RuntimeError("neutral_build_persistence_mismatch")
        return _build_projection(persisted)

    def load_build(self, content_hash: str) -> ImmutableBuildProjection:
        return _build_projection(self.store.get_build(content_hash))

    async def run(self, spec: SandboxRunSpec) -> SandboxRunProjection:
        service = AgentExecutionService(
            store=self.store,
            model=self.model,
            router=self.router,
            executor=self.executor,
        )
        projection = await service.execute(
            RunCommand(
                command=spec.command,
                tenant_id=spec.tenant_id,
                session_id=spec.session_id,
                build_hash=spec.build_hash,
                message=spec.message,
                run_id=spec.run_id,
                selected_operation_id=spec.selected_operation_id,
                selected_operations=dict(spec.selected_operations or {}),
                provided_inputs=dict(spec.provided_inputs or {}),
            )
        )
        return _run_projection(projection)

    def load_run(self, tenant_id: str, run_id: str) -> SandboxRunProjection:
        run = self.store.get_run(tenant_id, run_id)
        events = self.store.events(tenant_id, run_id)
        return _run_projection(type("Projection", (), {"run": run, "events": events})())

    def waiting_run(
        self, tenant_id: str, session_id: str, build_hash: str
    ) -> SandboxRunProjection | None:
        matches = tuple(
            run
            for run in self.store.list_runs(tenant_id)
            if run.session_id == session_id
            and run.build_hash == build_hash
            and run.status.value == "waiting"
        )
        if len(matches) > 1:
            raise RuntimeError("multiple_waiting_runs_for_session")
        if not matches:
            return None
        return self.load_run(tenant_id, matches[0].run_id)

    def session_messages(
        self, tenant_id: str, session_id: str, build_hash: str
    ) -> tuple[dict[str, str], ...]:
        """Project the exact durable conversation for one runtime session.

        Conversation truth remains in the neutral execution store. Corpus does
        not create a parallel delivery transcript or infer messages from
        Operations summaries.
        """
        runs = sorted(
            (
                run
                for run in self.store.list_runs(tenant_id)
                if run.session_id == session_id and run.build_hash == build_hash
            ),
            key=lambda run: (run.created_at, run.run_id),
        )
        messages: list[dict[str, str]] = []
        for run in runs:
            events = self.store.events(tenant_id, run.run_id)
            for index, event in enumerate(events):
                data = dict(event.safe_data)
                if event.kind == "user.message":
                    content = data.get("message")
                    if not isinstance(content, str) or not content.strip():
                        raise RuntimeError("runtime_conversation_user_message_invalid")
                    messages.append({"role": "user", "content": content})
                elif event.kind == "run.waiting":
                    messages.append(
                        {
                            "role": "assistant",
                            "content": _clarification_question(events[: index + 1]),
                        }
                    )
                elif event.kind == "run.completed":
                    content = data.get("response", run.final_response)
                    if not isinstance(content, str) or not content.strip():
                        raise RuntimeError("runtime_conversation_response_invalid")
                    messages.append({"role": "assistant", "content": content})
        return tuple(messages)


def _validate_build(build: AgentBuild) -> None:
    if not build.allowed_operations:
        raise ValueError("neutral_build_operations_required")
    if len(set(build.allowed_operations)) != len(build.allowed_operations):
        raise ValueError("neutral_build_operations_duplicate")
    if not build.connections:
        raise ValueError("neutral_build_connections_required")
    declared = {
        operation_id
        for connection in build.connections
        for operation_id in connection.operation_ids
    }
    if set(build.allowed_operations) != declared:
        raise ValueError("neutral_build_connection_operations_mismatch")
    if not set(build.preauthorized_write_operations).issubset(build.allowed_operations):
        raise ValueError("neutral_build_write_authorization_invalid")


def _build_projection(build: AgentBuild) -> ImmutableBuildProjection:
    return ImmutableBuildProjection(
        build_id=build.build_id,
        version=build.version,
        content_hash=build.content_hash,
        source_hash=build.source_hash,
        operation_ids=build.allowed_operations,
        preauthorized_write_operation_ids=build.preauthorized_write_operations,
    )


def _run_projection(value: Any) -> SandboxRunProjection:
    user_message_index = 0
    projected_events: list[SandboxEventProjection] = []
    for event in value.events:
        if event.kind == "user.message":
            user_message_index += 1
        projected_events.append(_safe_event(event, user_message_index=user_message_index))
    events = tuple(projected_events)
    waiting = value.run.status.value == "waiting"
    return SandboxRunProjection(
        run_id=value.run.run_id,
        build_hash=value.run.build_hash,
        status=value.run.status.value,
        awaiting=value.run.awaiting,
        final_response=(
            _clarification_question(value.events)
            if waiting
            else value.run.final_response
        ),
        api_call_count=sum(
            event.kind in {"api.result", "api.verification_result"}
            for event in value.events
        ),
        events=events,
    )


def _safe_event(event: Any, *, user_message_index: int) -> SandboxEventProjection:
    allowed = _EVENT_FIELDS.get(event.kind, frozenset())
    data = {
        key: _safe_value(value)
        for key, value in dict(event.safe_data).items()
        if key in allowed
    }
    public_kind = {
        "user.message": (
            "run.requested" if user_message_index <= 1 else "clarification.user_answer"
        ),
        "run.waiting": "run.needs_input",
        "run.failed": "run.failed",
    }.get(event.kind, event.kind if event.kind in _EVENT_FIELDS else "run.progress")
    if event.kind == "router.decision":
        decision = str(dict(event.safe_data).get("decision_type", ""))
        data["resolution"] = {
            "ASK_DISAMBIGUATE": "operation_choice_required",
            "ASK_PARAM": "input_required",
            "ROUTE": "operation_resolved",
            "NO_TOOL": "not_routable",
            "ABSTAIN": "not_routable",
        }.get(decision, "routing_checked")
    if event.kind == "user.message" and user_message_index > 1:
        data["source"] = "user"
    return SandboxEventProjection(
        sequence=event.sequence,
        kind=public_kind,
        occurred_at=event.occurred_at,
        safe_data=data,
    )


def _clarification_question(events: Any) -> str:
    decisions = [event for event in events if event.kind == "router.decision"]
    if not decisions:
        return "I need one more detail before I can continue. What should I use?"
    data = dict(decisions[-1].safe_data)
    missing = tuple(
        str(item) for item in data.get("missing_params", ()) if str(item).strip()
    )
    candidates = tuple(
        str(item.get("operation_id"))
        for item in data.get("candidates", ())
        if isinstance(item, Mapping) and item.get("operation_id")
    )
    if missing:
        names = ", ".join(missing)
        return f"What value should I use for {names}?"
    if len(candidates) > 1:
        labels = tuple(_operation_label(value) for value in candidates)
        return "Should I use " + " or ".join(labels) + "?"
    return "I need one more detail before I can continue. What should I use?"


def _operation_label(operation_id: str) -> str:
    expanded = re.sub(r"(?<=[a-z0-9])(?=[A-Z])", " ", operation_id)
    words = re.findall(r"[A-Za-z0-9]+", expanded)
    while words and words[0].casefold() in {
        "get", "list", "read", "fetch", "retrieve", "search", "find", "create",
        "post", "put", "patch", "update", "delete", "remove",
    }:
        words.pop(0)
    if len(words) > 1 and words[-1].casefold() == "id":
        words.pop()
    return " ".join(word.casefold() for word in words) or "the requested action"


def _safe_value(value: Any) -> Any:
    if value is None or isinstance(value, (bool, int, float, str)):
        return value
    if isinstance(value, (tuple, list)):
        return [_safe_value(item) for item in value]
    if isinstance(value, Mapping):
        return {str(key): _safe_value(item) for key, item in value.items()}
    return str(type(value).__name__)


__all__ = ["NeutralAgentExecutionAdapter"]
