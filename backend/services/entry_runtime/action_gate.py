from __future__ import annotations

from typing import Any

from backend.services.route_deck import (
    build_runtime_snapshot,
    is_action_allowed_for_node,
    recover_from_invalid_action,
)

from .graph_runtime import EntryRuntimeState, merge_messages


def selected_action_id(state: EntryRuntimeState) -> str | None:
    value = state.get("selected_action_id")
    return value.strip() if isinstance(value, str) and value.strip() else None


def route_action_error(stage_id: str, state: EntryRuntimeState) -> dict[str, Any] | None:
    action_id = selected_action_id(state)
    if not action_id or is_action_allowed_for_node(stage_id, action_id):
        return None

    message, actions = recover_from_invalid_action(stage_id, action_id)
    return {
        "stage_id": stage_id,
        "invalid_action_id": action_id,
        "message": message,
        "actions": actions,
    }


def recovery_updates_from_route_error(
    state: EntryRuntimeState,
    *,
    stage_id: str,
    route_error: dict[str, Any],
) -> dict[str, Any]:
    actions = route_error.get("actions") or []
    action_id = str(route_error.get("invalid_action_id") or "")
    return {
        "messages": merge_messages(state, str(route_error.get("message") or "")),
        "available_actions": actions,
        "route_deck_snapshot": build_runtime_snapshot(
            current_node=stage_id,
            executed_nodes=state["runtime"].executed_stage_ids,
            valid_actions=actions,
            diagnostics={
                "invalid_action_id": action_id,
                "recovery": "route_deck_invalid_action",
                "validated_by": "route_action",
            },
        ),
    }
