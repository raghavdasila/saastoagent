from __future__ import annotations

from dataclasses import dataclass
from typing import Any
import uuid

from backend.core.models import User
from backend.core.schemas import EntryGraphState, EntryGraphTurnRequest, EntryGraphTurnResponse
from backend.services.route_deck import build_runtime_snapshot

from .graph_executor import entry_graph_executor
from .graph_runtime import EntryEventSink, EntryRuntimeState, EntryTurnRuntime, state_dump, state_payload
from .graph_spec import GRAPH_VERSION, build_graph_manifest
from .runtime_store import EntryRuntimeStore
from .ui_actions import persistent_entry_actions


@dataclass
class EntryTurnResult:
    payload: EntryGraphTurnResponse
    session_id: uuid.UUID


def _request_input_payload(stage_id: str, body: EntryGraphTurnRequest) -> dict[str, Any]:
    user_input = body.user_input
    if stage_id == "password" and user_input:
        user_input = "********"
    return {
        "initial_intent": body.initial_intent,
        "selected_action_id": body.selected_action_id,
        "action_payload": _masked_action_payload(body.action_payload),
        "user_input": user_input,
    }


def _masked_action_payload(payload: dict[str, Any] | None) -> dict[str, Any] | None:
    if not payload:
        return payload
    masked = dict(payload)
    for key in ("credential_value", "password", "token", "api_key"):
        if masked.get(key):
            masked[key] = "********"
    return masked


def _resolved_state(
    *,
    session_state: dict[str, Any] | None,
    request_state: EntryGraphState | None,
) -> EntryGraphState | None:
    if session_state:
        return EntryGraphState.model_validate(session_state)
    return request_state


async def run_entry_turn(
    *,
    body: EntryGraphTurnRequest,
    current_user: User | None,
    db,
    session_id: uuid.UUID | None,
    event_sink: EntryEventSink | None = None,
) -> EntryTurnResult:
    store = EntryRuntimeStore(db)
    seed_state = body.state.model_dump(mode="json") if body.state else None
    session_record, _ = await store.ensure_session(
        session_id=session_id,
        current_user=current_user,
        initial_state=seed_state,
    )

    effective_state = _resolved_state(
        session_state=session_record.current_state,
        request_state=body.state,
    )
    graph_manifest = build_graph_manifest()
    current_node = effective_state.node if effective_state else "bootstrap"

    run_record = await store.start_run(
        session_record=session_record,
        current_user=current_user,
        graph_manifest=graph_manifest,
        request_input=_request_input_payload(current_node, body),
    )

    runtime = EntryTurnRuntime(
        db=db,
        store=store,
        session_record=session_record,
        run_record=run_record,
        graph_manifest=graph_manifest,
        event_sink=event_sink,
    )
    await runtime.emit(
        "run_started",
        {
            "type": "run_started",
            "turn_id": str(run_record.id),
            "run_id": str(run_record.id),
            "session_id": str(session_record.id),
            "graph_version": GRAPH_VERSION,
            "graph_manifest": graph_manifest,
            "status": run_record.status,
            "started_at": run_record.started_at.isoformat() if run_record.started_at else None,
            "metadata": run_record.metadata_ or {},
        },
    )
    runtime_state: EntryRuntimeState = {
        "node": effective_state.node if effective_state else "bootstrap",
        "intent": effective_state.intent if effective_state else None,
        "display_name": effective_state.display_name if effective_state else "",
        "email": effective_state.email if effective_state else "",
        "workspace_name": effective_state.workspace_name if effective_state else "",
        "workspace_slug": effective_state.workspace_slug if effective_state else "",
        "active_workspace_id": effective_state.active_workspace_id if effective_state else None,
        "active_connection_id": effective_state.active_connection_id if effective_state else None,
        "connection_draft": effective_state.connection_draft if effective_state else {},
        "entry_draft": effective_state.entry_draft if effective_state else {},
        "platform_question_context": effective_state.platform_question_context if effective_state else [],
        "canvas_artifacts": effective_state.canvas_artifacts if effective_state else [],
        "follow_up_context": effective_state.follow_up_context if effective_state else {},
        "user_input": body.user_input,
        "initial_intent": body.initial_intent,
        "selected_action_id": body.selected_action_id,
        "action_payload": body.action_payload,
        "current_user": current_user,
        "runtime": runtime,
        "messages": [],
        "session_payload": None,
        "workspaces": [],
        "available_actions": [],
        "persistent_actions": [],
        "ui_artifacts": [],
        "replace_path": None,
    }

    try:
        result = await entry_graph_executor.ainvoke(runtime_state)
        effective_user = result.get("current_user") or current_user
        persistent_actions = persistent_entry_actions(
            node=result.get("node"),
            current_user=effective_user,
            active_workspace_id=result.get("active_workspace_id"),
        )
        result["persistent_actions"] = persistent_actions
        final_state = state_dump(result)
        last_stage_id = runtime.executed_stage_ids[-1] if runtime.executed_stage_ids else None
        route_deck_snapshot = build_runtime_snapshot(
            current_node=result.get("node"),
            executed_nodes=runtime.executed_stage_ids,
            valid_actions=[
                *result.get("available_actions", []),
                *persistent_actions,
            ],
            diagnostics={
                "run_id": str(run_record.id),
                "session_id": str(session_record.id),
                "graph_version": GRAPH_VERSION,
            },
        )

        await store.persist_session_state(
            session_record,
            state=final_state,
            current_user=effective_user,
            last_stage_id=last_stage_id,
            last_run_id=run_record.id,
        )
        await store.complete_run(
            run_record,
            status="completed",
            final_state=final_state,
        )
        await db.commit()

        payload = EntryGraphTurnResponse(
            state=state_payload(result),
            session_id=session_record.id,
            run_id=run_record.id,
            graph_version=GRAPH_VERSION,
            graph_manifest=graph_manifest,
            messages=result.get("messages", []),
            session=result.get("session_payload"),
            workspaces=result.get("workspaces", []),
            available_actions=result.get("available_actions", []),
            persistent_actions=persistent_actions,
            ui_artifacts=result.get("ui_artifacts", []),
            route_deck_snapshot=route_deck_snapshot,
            replace_path=result.get("replace_path"),
        )
        await runtime.emit(
            "entry_turn_result",
            payload.model_dump(mode="json", by_alias=True),
        )
        await runtime.emit(
            "run_completed",
            {
                "type": "run_completed",
                "turn_id": str(run_record.id),
                "run_id": str(run_record.id),
                "session_id": str(session_record.id),
                "graph_version": GRAPH_VERSION,
                "status": run_record.status,
                "started_at": run_record.started_at.isoformat() if run_record.started_at else None,
                "completed_at": run_record.completed_at.isoformat() if run_record.completed_at else None,
                "metadata": run_record.metadata_ or {},
            },
        )

        return EntryTurnResult(
            session_id=session_record.id,
            payload=payload,
        )
    except Exception as exc:
        await store.complete_run(
            run_record,
            status="failed",
            final_state=session_record.current_state,
            metadata={"error": str(exc)},
        )
        await db.commit()
        await runtime.emit(
            "run_completed",
            {
                "type": "run_completed",
                "turn_id": str(run_record.id),
                "run_id": str(run_record.id),
                "session_id": str(session_record.id),
                "graph_version": GRAPH_VERSION,
                "status": run_record.status,
                "started_at": run_record.started_at.isoformat() if run_record.started_at else None,
                "completed_at": run_record.completed_at.isoformat() if run_record.completed_at else None,
                "metadata": run_record.metadata_ or {},
            },
        )
        raise
