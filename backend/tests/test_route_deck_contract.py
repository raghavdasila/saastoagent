from __future__ import annotations

from backend.services.route_deck import (
    RouteDeckActionIds,
    build_route_deck_manifest,
    build_runtime_snapshot,
    is_action_allowed_for_node,
    recover_from_invalid_action,
    validate_route_deck_manifest,
)
from backend.services.entry_runtime.graph_executor import ENTRY_GRAPH_GROUPS, NODE_HANDLERS
from backend.services.entry_runtime.route_conditions import (
    EDGE_CONDITION_RESOLVERS,
    assert_route_deck_transition,
    missing_route_deck_condition_resolvers,
)
from routedeck_langgraph import validate_langgraph_contract
from backend.services.entry_runtime.stage_auth import display_name_node, email_node, password_node
from backend.services.entry_runtime import stage_workspace
from backend.core.config import settings
from backend.services.entry_runtime.ui_actions import (
    connection_confirm_actions,
    setup_intro_actions,
    standard_workspace_actions,
)
from backend.core.schemas import WorkspaceRead


def test_ROUTE_DECK_manifest_is_valid_and_complete():
    assert validate_route_deck_manifest() == []

    manifest = build_route_deck_manifest()
    node_ids = {node.id for node in manifest.nodes}
    action_ids = {action.id for action in manifest.actions}

    assert {"intent", "display_name", "email", "password", "setup_intro", "operator_ready"} <= node_ids
    assert {"intent.sign_in", "intent.register", "setup.rest.configure"} <= action_ids
    assert manifest.policies["sensitive"]["masked_payload_keys"]


def test_ROUTE_DECK_workspace_creation_copy_matches_product_contract():
    manifest = build_route_deck_manifest()
    text = " ".join(
        str(value)
        for node in manifest.nodes
        for value in (
            node.label,
            node.description,
            node.prompt_placeholder,
            node.expected_input,
            node.recovery_prompt,
        )
        if value
    )
    text += " " + " ".join(edge.explanation or "" for edge in manifest.edges)

    assert "saas job" not in text.lower()
    assert "operator should own" not in text.lower()
    assert "workspace job" not in text.lower()
    assert "workspace name" in text.lower()


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


def test_ROUTE_DECK_edges_have_executable_langgraph_resolvers():
    manifest = build_route_deck_manifest()
    grouped_nodes = set().union(*ENTRY_GRAPH_GROUPS.values())

    assert grouped_nodes == {node.id for node in manifest.nodes}
    assert missing_route_deck_condition_resolvers() == []
    assert validate_langgraph_contract(
        manifest,
        NODE_HANDLERS,
        EDGE_CONDITION_RESOLVERS,
        groups=ENTRY_GRAPH_GROUPS,
    ) == []

    for edge in manifest.edges:
        state = {"node": edge.to_stage}
        transition = assert_route_deck_transition(
            from_stage=edge.from_stage,
            to_stage=edge.to_stage,
            state=state,
        )
        assert transition["source"] == "route_deck"


def test_ROUTE_DECK_action_scope_blocks_invalid_auth_dead_ends():
    assert is_action_allowed_for_node("intent", "intent.register")
    assert is_action_allowed_for_node("display_name", "display_name.skip")
    assert is_action_allowed_for_node("email", "intent.register")
    assert is_action_allowed_for_node("password", "nav.back")
    assert is_action_allowed_for_node("password", "nav.cancel")
    assert is_action_allowed_for_node("workspace_select", "nav.back")
    assert is_action_allowed_for_node("workspace_select", "nav.cancel")
    assert is_action_allowed_for_node("workspace_job", "nav.back")
    assert is_action_allowed_for_node("workspace_job", "nav.cancel")
    assert is_action_allowed_for_node("workspace_confirm", "nav.back")
    assert is_action_allowed_for_node("workspace_confirm", "nav.cancel")

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


def test_auth_passive_resume_returns_to_assisted_intent_without_validating_empty_input(monkeypatch):
    import asyncio

    monkeypatch.setattr(settings, "openai_api_key", "", raising=False)

    email_result = asyncio.run(email_node(_auth_state("email", intent="login")))
    display_result = asyncio.run(display_name_node(_auth_state("display_name", intent="register")))
    password_result = asyncio.run(password_node(_auth_state("password", intent="login")))

    assert email_result["node"] == "intent"
    assert email_result["intent"] is None
    assert email_result["email"] == ""
    assert "valid email" not in email_result["messages"][-1].content
    assert "give me the email" not in email_result["messages"][-1].content.lower()

    assert display_result["node"] == "intent"
    assert display_result["display_name"] == ""
    assert "display name" not in display_result["messages"][-1].content.lower()

    assert password_result["node"] == "intent"
    assert "password" not in password_result["messages"][-1].content.lower()


def test_typed_non_llm_nodes_expose_recovery_navigation():
    manifest = build_route_deck_manifest()
    node_by_id = {node.id: node for node in manifest.nodes}

    for node_id in ("display_name", "email", "password", "workspace_select", "workspace_job", "workspace_confirm", "setup_intro", "connection_confirm"):
        assert RouteDeckActionIds.NAV_BACK in node_by_id[node_id].allowed_actions
        assert RouteDeckActionIds.NAV_CANCEL in node_by_id[node_id].allowed_actions


def _workspace_state(node: str, *, action_id: str | None = None):
    return {
        "node": node,
        "current_user": type("UserStub", (), {"id": "user-1"})(),
        "selected_action_id": action_id,
        "workspace_name": "Billing Workspace",
        "workspace_slug": "billing-workspace",
        "messages": [],
    }


def _workspace(name: str = "Existing Workspace") -> WorkspaceRead:
    from datetime import datetime
    from uuid import uuid4

    return WorkspaceRead(
        id=uuid4(),
        name=name,
        slug="existing-workspace",
        created_by=uuid4(),
        created_at=datetime.utcnow(),
        role="owner",
    )


def test_workspace_recovery_actions_are_executable(monkeypatch):
    import asyncio

    async def fake_list_workspaces(_state, _user_id):
        return [_workspace()]

    monkeypatch.setattr(stage_workspace, "list_workspaces", fake_list_workspaces)

    select_result = asyncio.run(
        stage_workspace.workspace_select_node(
            _workspace_state("workspace_select", action_id=RouteDeckActionIds.NAV_CANCEL)
        )
    )
    job_result = asyncio.run(
        stage_workspace.workspace_job_node(
            _workspace_state("workspace_job", action_id=RouteDeckActionIds.NAV_BACK)
        )
    )
    confirm_back_result = asyncio.run(
        stage_workspace.workspace_confirm_node(
            _workspace_state("workspace_confirm", action_id=RouteDeckActionIds.NAV_BACK)
        )
    )
    confirm_cancel_result = asyncio.run(
        stage_workspace.workspace_confirm_node(
            _workspace_state("workspace_confirm", action_id=RouteDeckActionIds.NAV_CANCEL)
        )
    )

    assert select_result["node"] == "intent"
    assert select_result["workspace_name"] == ""
    assert job_result["node"] == "intent"
    assert job_result["workspace_slug"] == ""
    assert confirm_back_result["node"] == "workspace_select"
    assert {action.id for action in confirm_back_result["available_actions"]} >= {"workspace_select.open:1"}
    assert confirm_cancel_result["node"] == "intent"
    assert confirm_cancel_result["workspace_name"] == ""
