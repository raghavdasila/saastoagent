from __future__ import annotations

from typing import Any

from backend.services.route_deck import build_route_deck_manifest

from .graph_runtime import EntryRuntimeState


def masked_payload_keys() -> set[str]:
    manifest = build_route_deck_manifest()
    policy = manifest.policies.get("sensitive", {})
    keys = policy.get("masked_payload_keys", [])
    return {str(key) for key in keys}


def mask_action_payload(payload: dict[str, Any] | None) -> dict[str, Any] | None:
    if not payload:
        return payload
    masked = dict(payload)
    for key in masked_payload_keys():
        if masked.get(key):
            masked[key] = "********"
    return masked


def mask_input(stage_id: str, value: str | None) -> str | None:
    if not value:
        return value
    if stage_id == "password":
        return "********"
    return value


def stage_input_payload(stage_id: str, state: EntryRuntimeState) -> dict[str, Any]:
    return {
        "current_node": state.get("node"),
        "intent": state.get("intent"),
        "selected_action_id": state.get("selected_action_id"),
        "action_payload": mask_action_payload(state.get("action_payload")),
        "user_input": mask_input(stage_id, state.get("user_input")),
    }
