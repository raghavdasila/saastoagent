from __future__ import annotations

from backend.services.route_deck import (
    build_route_deck_manifest,
    build_runtime_snapshot,
    is_action_allowed_for_node,
    recover_from_invalid_action,
    validate_route_deck_manifest,
)


def test_ROUTE_DECK_manifest_is_valid_and_complete():
    assert validate_route_deck_manifest() == []

    manifest = build_route_deck_manifest()
    node_ids = {node.id for node in manifest.nodes}
    action_ids = {action.id for action in manifest.actions}

    assert {"intent", "display_name", "email", "password", "setup_intro", "operator_ready"} <= node_ids
    assert {"intent.sign_in", "intent.register", "setup.rest.configure"} <= action_ids
    assert manifest.policies["sensitive"]["masked_payload_keys"]


def test_ROUTE_DECK_action_scope_blocks_invalid_auth_dead_ends():
    assert is_action_allowed_for_node("intent", "intent.register")
    assert is_action_allowed_for_node("display_name", "display_name.skip")
    assert not is_action_allowed_for_node("email", "intent.register")

    message, actions = recover_from_invalid_action("email", "intent.register")
    assert "not available" in message
    assert actions == []


def test_ROUTE_DECK_runtime_snapshot_exposes_debuggable_flow_state():
    snapshot = build_runtime_snapshot(
        current_node="setup_intro",
        executed_nodes=["bootstrap", "intent", "setup_intro"],
    )

    assert snapshot["current_node"] == "setup_intro"
    assert "connection_confirm" in snapshot["reachable_nodes"]
    assert any(action["id"] == "setup.rest.configure" for action in snapshot["valid_actions"])
    assert snapshot["executed_nodes"] == ["bootstrap", "intent", "setup_intro"]
