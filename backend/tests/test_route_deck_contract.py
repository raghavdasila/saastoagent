from __future__ import annotations

from backend.services.route_deck import (
    RouteDeckActionIds,
    build_route_deck_manifest,
    build_runtime_snapshot,
    is_action_allowed_for_node,
    recover_from_invalid_action,
    validate_route_deck_manifest,
)
from backend.services.entry_runtime.graph_executor import NODE_HANDLERS
from backend.services.entry_runtime.stage_auth import display_name_node, email_node, password_node
from backend.services.entry_runtime.ui_actions import (
    connection_confirm_actions,
    setup_intro_actions,
    standard_workspace_actions,
)


def test_ROUTE_DECK_manifest_is_valid_and_complete():
    assert validate_route_deck_manifest() == []

    manifest = build_route_deck_manifest()
    node_ids = {node.id for node in manifest.nodes}
    action_ids = {action.id for action in manifest.actions}

    assert {"intent", "display_name", "email", "password", "setup_intro", "operator_ready"} <= node_ids
    assert {"intent.sign_in", "intent.register", "setup.rest.configure"} <= action_ids
    assert manifest.policies["sensitive"]["masked_payload_keys"]


def test_ROUTE_DECK_manifest_matches_executable_entry_runtime():
    manifest = build_route_deck_manifest()
    runtime_nodes = set(NODE_HANDLERS.keys())

    assert {node.id for node in manifest.nodes} == runtime_nodes
    assert all(edge.from_stage in runtime_nodes and edge.to_stage in runtime_nodes for edge in manifest.edges)

    action_ids = {action.id for action in manifest.actions}
    for node in manifest.nodes:
        for action_id in node.allowed_actions:
            if action_id.endswith("*"):
                assert action_id in action_ids
            else:
                assert is_action_allowed_for_node(node.id, action_id)

    for node, actions in {
        "operator_ready": standard_workspace_actions(),
        "setup_intro": setup_intro_actions(),
        "connection_confirm": connection_confirm_actions({"name": "Example API"}),
    }.items():
        assert all(is_action_allowed_for_node(node, action.id) for action in actions)


def test_ROUTE_DECK_action_scope_blocks_invalid_auth_dead_ends():
    assert is_action_allowed_for_node("intent", "intent.register")
    assert is_action_allowed_for_node("display_name", "display_name.skip")
    assert is_action_allowed_for_node("email", "intent.register")
    assert is_action_allowed_for_node("password", "nav.back")
    assert is_action_allowed_for_node("password", "nav.cancel")

    message, actions = recover_from_invalid_action("email", "setup.rest.configure")
    assert "not available" in message
    assert all(is_action_allowed_for_node("email", action.id) for action in actions)


def test_ROUTE_DECK_runtime_snapshot_exposes_debuggable_flow_state():
    snapshot = build_runtime_snapshot(
        current_node="setup_intro",
        executed_nodes=["bootstrap", "intent", "setup_intro"],
    )

    assert snapshot["current_node"] == "setup_intro"
    assert "connection_confirm" in snapshot["reachable_nodes"]
    assert any(action["id"] == "setup.rest.configure" for action in snapshot["valid_actions"])
    assert snapshot["executed_nodes"] == ["bootstrap", "intent", "setup_intro"]


def _auth_state(node: str, *, intent: str | None = None, action_id: str | None = None):
    return {
        "node": node,
        "intent": intent,
        "display_name": "Draft Name",
        "email": "draft@example.com",
        "selected_action_id": action_id,
        "messages": [],
    }


def test_auth_cancel_clears_transient_fields_and_returns_to_intent():
    import asyncio

    result = asyncio.run(
        email_node(
            _auth_state(
                "email",
                intent="login",
                action_id=RouteDeckActionIds.NAV_CANCEL,
            )
        )
    )

    assert result["node"] == "intent"
    assert result["intent"] is None
    assert result["display_name"] == ""
    assert result["email"] == ""
    assert {action.id for action in result["available_actions"]} >= {
        RouteDeckActionIds.INTENT_SIGN_IN,
        RouteDeckActionIds.INTENT_REGISTER,
    }


def test_auth_back_and_switch_actions_are_executable():
    import asyncio

    back_result = asyncio.run(
        password_node(
            _auth_state(
                "password",
                intent="login",
                action_id=RouteDeckActionIds.NAV_BACK,
            )
        )
    )
    register_result = asyncio.run(
        email_node(
            _auth_state(
                "email",
                intent="login",
                action_id=RouteDeckActionIds.INTENT_REGISTER,
            )
        )
    )
    login_result = asyncio.run(
        display_name_node(
            _auth_state(
                "display_name",
                intent="register",
                action_id=RouteDeckActionIds.INTENT_SIGN_IN,
            )
        )
    )

    assert back_result["node"] == "email"
    assert back_result["email"] == ""
    assert register_result["node"] == "display_name"
    assert register_result["intent"] == "register"
    assert login_result["node"] == "email"
    assert login_result["intent"] == "login"
