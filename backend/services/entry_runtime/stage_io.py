from __future__ import annotations

from typing import Any, Awaitable, Callable

from backend.core.schemas import EntryActionCard, EntryGraphMessage, EntryGraphSession, EntryUIArtifact, WorkspaceRead
from backend.services.route_deck import build_runtime_snapshot, is_action_allowed_for_node, recover_from_invalid_action

from .graph_runtime import EntryRuntimeState, merge_messages
from .graph_spec import get_node_spec

StageHandler = Callable[[EntryRuntimeState], Awaitable[dict[str, Any]]]


def _masked_input(stage_id: str, value: str | None) -> str | None:
    if not value:
        return value
    if stage_id == "password":
        return "********"
    return value


def _stage_input_payload(stage_id: str, state: EntryRuntimeState) -> dict[str, Any]:
    return {
        "current_node": state.get("node"),
        "intent": state.get("intent"),
        "selected_action_id": state.get("selected_action_id"),
        "action_payload": _masked_action_payload(state.get("action_payload")),
        "user_input": _masked_input(stage_id, state.get("user_input")),
    }


def _masked_action_payload(payload: dict[str, Any] | None) -> dict[str, Any] | None:
    if not payload:
        return payload
    masked = dict(payload)
    for key in ("credential_value", "password", "token", "api_key"):
        if masked.get(key):
            masked[key] = "********"
    return masked


def _stage_output_payload(updates: dict[str, Any]) -> dict[str, Any]:
    payload: dict[str, Any] = {}

    if "node" in updates:
        payload["next_node"] = updates.get("node")
    if updates.get("messages"):
        payload["messages"] = [
            message.model_dump(mode="json") for message in updates["messages"]
        ]
    if updates.get("workspaces"):
        payload["workspaces"] = [
            workspace.model_dump(mode="json") for workspace in updates["workspaces"]
        ]
    if updates.get("available_actions"):
        payload["available_actions"] = [
            action.model_dump(mode="json") for action in updates["available_actions"]
        ]
    if updates.get("persistent_actions"):
        payload["persistent_actions"] = [
            action.model_dump(mode="json") for action in updates["persistent_actions"]
        ]
    if updates.get("replace_path"):
        payload["replace_path"] = updates.get("replace_path")
    if updates.get("active_workspace_id"):
        payload["active_workspace_id"] = str(updates.get("active_workspace_id"))
    if updates.get("active_connection_id"):
        payload["active_connection_id"] = str(updates.get("active_connection_id"))
    if updates.get("connection_draft"):
        payload["connection_draft"] = updates.get("connection_draft")
    if updates.get("entry_draft"):
        payload["entry_draft"] = updates.get("entry_draft")
    if updates.get("platform_question_context"):
        payload["platform_question_context"] = updates.get("platform_question_context")
    if updates.get("canvas_artifacts"):
        payload["canvas_artifacts"] = updates.get("canvas_artifacts")
    if updates.get("follow_up_context"):
        payload["follow_up_context"] = updates.get("follow_up_context")
    if updates.get("ui_artifacts"):
        payload["ui_artifacts"] = [
            artifact.model_dump(mode="json") for artifact in updates["ui_artifacts"]
            if isinstance(artifact, EntryUIArtifact)
        ]
    if updates.get("route_deck_snapshot"):
        payload["route_deck_snapshot"] = updates.get("route_deck_snapshot")

    session_payload = updates.get("session_payload")
    if isinstance(session_payload, EntryGraphSession):
        payload["session"] = {
            "user": session_payload.user.model_dump(mode="json"),
            "token_type": session_payload.token_type,
        }

    return payload


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
        input_payload=_stage_input_payload(stage_id, state),
    )
    runtime.executed_stage_ids.append(stage_id)
    await runtime.emit(
        "stage_started",
        {
            "type": "stage_started",
            "turn_id": str(runtime.run_record.id),
            "run_id": str(runtime.run_record.id),
            "session_id": str(runtime.session_record.id),
            "stage_id": stage_record.stage_id,
            "parent_stage_id": stage_record.parent_stage_id,
            "depends_on": stage_record.depends_on or [],
            "sequence": stage_record.sequence,
            "lane": stage_record.lane,
            "status": stage_record.status,
            "started_at": stage_record.started_at.isoformat() if stage_record.started_at else None,
            "input": stage_record.input_payload,
        },
    )

    try:
        selected_action_id = state.get("selected_action_id")
        if selected_action_id:
            await runtime.store.record_artifact(
                run_record=runtime.run_record,
                session_record=runtime.session_record,
                stage_id=stage_id,
                artifact_type="selected_action",
                name=selected_action_id,
                payload={"action_id": selected_action_id},
            )
        action_payload = _masked_action_payload(state.get("action_payload"))
        if action_payload:
            await runtime.store.record_artifact(
                run_record=runtime.run_record,
                session_record=runtime.session_record,
                stage_id=stage_id,
                artifact_type="action_payload",
                name=selected_action_id or "payload",
                payload=action_payload,
            )

        selected_action_id = state.get("selected_action_id")
        if selected_action_id and not is_action_allowed_for_node(stage_id, selected_action_id):
            recovery_message, recovery_actions = recover_from_invalid_action(stage_id, selected_action_id)
            updates = {
                "messages": merge_messages(state, recovery_message),
                "available_actions": recovery_actions,
                "route_deck_snapshot": build_runtime_snapshot(
                    current_node=stage_id,
                    executed_nodes=runtime.executed_stage_ids,
                    valid_actions=recovery_actions,
                    diagnostics={
                        "invalid_action_id": selected_action_id,
                        "recovery": "route_deck_invalid_action",
                    },
                ),
            }
        else:
            updates = await handler(state)
        messages = updates.get("messages", [])
        for message in messages:
            if isinstance(message, EntryGraphMessage):
                output_sequence = runtime.next_output_sequence()
                await runtime.store.record_output(
                    run_record=runtime.run_record,
                    session_record=runtime.session_record,
                    stage_id=stage_id,
                    sequence=output_sequence,
                    lane=node_spec.lane.value,
                    content=message.content,
                )
                await runtime.emit(
                    "message_delta",
                    {
                        "content": message.content,
                        "stage_id": stage_id,
                        "lane": node_spec.lane.value,
                        "sequence": output_sequence,
                    },
                )

        actions = updates.get("available_actions", [])
        normalized_actions: list[EntryActionCard] = []
        for action in actions:
            if isinstance(action, EntryActionCard):
                normalized_actions.append(action)

        if normalized_actions:
            await runtime.store.record_artifact(
                run_record=runtime.run_record,
                session_record=runtime.session_record,
                stage_id=stage_id,
                artifact_type="available_actions",
                name="entry_actions",
                payload={
                    "actions": [action.model_dump(mode="json") for action in normalized_actions]
                },
            )

        ui_artifacts = updates.get("ui_artifacts", [])
        normalized_ui_artifacts: list[EntryUIArtifact] = []
        for artifact in ui_artifacts:
            if isinstance(artifact, EntryUIArtifact):
                normalized_ui_artifacts.append(artifact)

        if normalized_ui_artifacts:
            await runtime.store.record_artifact(
                run_record=runtime.run_record,
                session_record=runtime.session_record,
                stage_id=stage_id,
                artifact_type="ui_artifacts",
                name="entry_ui_artifacts",
                payload={
                    "artifacts": [
                        artifact.model_dump(mode="json") for artifact in normalized_ui_artifacts
                    ]
                },
            )

        session_payload = updates.get("session_payload")
        if isinstance(session_payload, EntryGraphSession):
            await runtime.store.record_artifact(
                run_record=runtime.run_record,
                session_record=runtime.session_record,
                stage_id=stage_id,
                artifact_type="auth_session",
                name="issued_user",
                payload={"user": session_payload.user.model_dump(mode="json")},
            )

        output_payload = _stage_output_payload(updates)
        await runtime.store.complete_stage(
            stage_record,
            output_payload=output_payload,
        )
        await runtime.emit(
            "stage_completed",
            {
                "type": "stage_completed",
                "turn_id": str(runtime.run_record.id),
                "run_id": str(runtime.run_record.id),
                "session_id": str(runtime.session_record.id),
                "stage_id": stage_record.stage_id,
                "parent_stage_id": stage_record.parent_stage_id,
                "sequence": stage_record.sequence,
                "lane": stage_record.lane,
                "status": stage_record.status,
                "started_at": stage_record.started_at.isoformat() if stage_record.started_at else None,
                "completed_at": stage_record.completed_at.isoformat() if stage_record.completed_at else None,
                "duration_ms": stage_record.duration_ms,
                "output": output_payload,
                "error": stage_record.error,
            },
        )
        return updates
    except Exception as exc:
        await runtime.store.complete_stage(
            stage_record,
            status="failed",
            output_payload={"error": str(exc)},
            error=str(exc),
        )
        await runtime.emit(
            "stage_completed",
            {
                "type": "stage_completed",
                "turn_id": str(runtime.run_record.id),
                "run_id": str(runtime.run_record.id),
                "session_id": str(runtime.session_record.id),
                "stage_id": stage_record.stage_id,
                "parent_stage_id": stage_record.parent_stage_id,
                "sequence": stage_record.sequence,
                "lane": stage_record.lane,
                "status": stage_record.status,
                "started_at": stage_record.started_at.isoformat() if stage_record.started_at else None,
                "completed_at": stage_record.completed_at.isoformat() if stage_record.completed_at else None,
                "duration_ms": stage_record.duration_ms,
                "output": stage_record.output_payload,
                "error": stage_record.error,
            },
        )
        raise
