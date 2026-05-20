from __future__ import annotations

from typing import Any, Awaitable, Callable

from .action_gate import recovery_updates_from_route_error
from .graph_runtime import EntryRuntimeState
from .graph_spec import get_node_spec
from .stage_artifacts import (
    record_action_inputs,
    record_available_actions,
    record_session_payload,
    record_ui_artifacts,
)
from .stage_events import emit_stage_completed, emit_stage_started, record_and_stream_messages
from .stage_output import stage_output_payload
from .stage_security import stage_input_payload

StageHandler = Callable[[EntryRuntimeState], Awaitable[dict[str, Any]]]


async def execute_stage(
    stage_id: str,
    handler: StageHandler,
    state: EntryRuntimeState,
) -> dict[str, Any]:
    runtime = state["runtime"]
    node_spec = get_node_spec(stage_id)
    session_metadata = runtime.session_record.metadata_ or {}
    depends_on = [session_metadata["last_stage_id"]] if session_metadata.get("last_stage_id") else []

    stage_record = await runtime.store.start_stage(
        run_record=runtime.run_record,
        session_record=runtime.session_record,
        stage_id=stage_id,
        lane=node_spec.lane.value,
        sequence=runtime.next_stage_sequence(),
        parent_stage_id=node_spec.parent,
        depends_on=depends_on,
        input_payload=stage_input_payload(stage_id, state),
    )
    runtime.executed_stage_ids.append(stage_id)
    await emit_stage_started(runtime, stage_record)

    try:
        selected_action_id = state.get("selected_action_id")
        await record_action_inputs(
            runtime=runtime,
            stage_id=stage_id,
            selected_action_id=selected_action_id,
            action_payload=state.get("action_payload"),
        )

        route_error = state.get("route_error")
        if isinstance(route_error, dict):
            updates = recovery_updates_from_route_error(
                state,
                stage_id=stage_id,
                route_error=route_error,
            )
        else:
            updates = await handler(state)
        await record_and_stream_messages(
            runtime=runtime,
            node_spec=node_spec,
            stage_id=stage_id,
            messages=updates.get("messages", []),
            emit_deltas=not bool(updates.get("messages_already_streamed")),
        )
        await record_available_actions(
            runtime=runtime,
            stage_id=stage_id,
            actions=updates.get("available_actions", []),
        )
        await record_ui_artifacts(
            runtime=runtime,
            stage_id=stage_id,
            ui_artifacts=updates.get("ui_artifacts", []),
        )
        await record_session_payload(
            runtime=runtime,
            stage_id=stage_id,
            session_payload=updates.get("session_payload"),
        )

        output_payload = stage_output_payload(updates)
        await runtime.store.complete_stage(
            stage_record,
            output_payload=output_payload,
        )
        await emit_stage_completed(runtime, stage_record, output_payload=output_payload)
        return updates
    except Exception as exc:
        await runtime.store.complete_stage(
            stage_record,
            status="failed",
            output_payload={"error": str(exc)},
            error=str(exc),
        )
        await emit_stage_completed(runtime, stage_record)
        raise
