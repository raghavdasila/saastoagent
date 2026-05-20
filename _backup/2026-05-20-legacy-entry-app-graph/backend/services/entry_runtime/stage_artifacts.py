from __future__ import annotations

from typing import Any

from backend.core.schemas import EntryActionCard, EntryGraphSession, EntryUIArtifact

from .graph_runtime import EntryTurnRuntime
from .stage_security import mask_action_payload


async def record_action_inputs(
    *,
    runtime: EntryTurnRuntime,
    stage_id: str,
    selected_action_id: str | None,
    action_payload: dict[str, Any] | None,
) -> None:
    if selected_action_id:
        await runtime.store.record_artifact(
            run_record=runtime.run_record,
            session_record=runtime.session_record,
            stage_id=stage_id,
            artifact_type="selected_action",
            name=selected_action_id,
            payload={"action_id": selected_action_id},
        )

    masked_payload = mask_action_payload(action_payload)
    if masked_payload:
        await runtime.store.record_artifact(
            run_record=runtime.run_record,
            session_record=runtime.session_record,
            stage_id=stage_id,
            artifact_type="action_payload",
            name=selected_action_id or "payload",
            payload=masked_payload,
        )


async def record_available_actions(
    *,
    runtime: EntryTurnRuntime,
    stage_id: str,
    actions: list[Any],
) -> None:
    normalized = [action for action in actions if isinstance(action, EntryActionCard)]
    if not normalized:
        return
    await runtime.store.record_artifact(
        run_record=runtime.run_record,
        session_record=runtime.session_record,
        stage_id=stage_id,
        artifact_type="available_actions",
        name="entry_actions",
        payload={"actions": [action.model_dump(mode="json") for action in normalized]},
    )


async def record_ui_artifacts(
    *,
    runtime: EntryTurnRuntime,
    stage_id: str,
    ui_artifacts: list[Any],
) -> None:
    normalized = [artifact for artifact in ui_artifacts if isinstance(artifact, EntryUIArtifact)]
    if not normalized:
        return
    await runtime.store.record_artifact(
        run_record=runtime.run_record,
        session_record=runtime.session_record,
        stage_id=stage_id,
        artifact_type="ui_artifacts",
        name="entry_ui_artifacts",
        payload={
            "artifacts": [
                artifact.model_dump(mode="json") for artifact in normalized
            ]
        },
    )


async def record_session_payload(
    *,
    runtime: EntryTurnRuntime,
    stage_id: str,
    session_payload: Any,
) -> None:
    if not isinstance(session_payload, EntryGraphSession):
        return
    await runtime.store.record_artifact(
        run_record=runtime.run_record,
        session_record=runtime.session_record,
        stage_id=stage_id,
        artifact_type="auth_session",
        name="issued_user",
        payload={"user": session_payload.user.model_dump(mode="json")},
    )
