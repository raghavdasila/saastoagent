from __future__ import annotations

from backend.services.app_graph import (
    ACTION_TARGETS,
    APP_GRAPH_GROUPS,
    APP_GRAPH_VERSION,
    NODE_HANDLERS,
    build_app_graph_manifest,
    validate_app_graph_manifest,
)
from backend.core.schemas import AppGraphState
from backend.services.app_graph.manifest import ACTION_SPECS, AppActionIds, route_action_to_card
from backend.services.app_graph.router import AppGraphTurnRouter
from routedeck_langgraph import validate_langgraph_contract
from pathlib import Path


def test_app_graph_manifest_is_valid_and_handler_complete():
    assert validate_app_graph_manifest() == []
    manifest = build_app_graph_manifest()

    assert manifest.version == APP_GRAPH_VERSION
    assert manifest.nodes[0].id == "home"
    assert {node.id for node in manifest.nodes} == set(NODE_HANDLERS)
    assert {
        "home",
        "agent_home",
        "connection_configure",
        "schema_preview",
        "catalog_activation",
        "catalog",
        "execution_planning",
        "approval_required",
        "knowledge",
        "memory",
        "learning",
        "qa",
        "recovery",
    } <= {node.id for node in manifest.nodes}


def test_app_graph_route_deck_matches_langgraph_contract():
    manifest = build_app_graph_manifest()
    assert validate_langgraph_contract(
        manifest,
        NODE_HANDLERS,
        {},
        groups=APP_GRAPH_GROUPS,
    ) == []

    node_ids = {node.id for node in manifest.nodes}
    action_ids = {action.id for action in manifest.actions}
    for edge in manifest.edges:
        assert edge.from_stage in node_ids
        assert edge.to_stage in node_ids
        if edge.action_id:
            assert edge.action_id in action_ids


def test_app_graph_actions_are_scoped_and_target_typed_nodes():
    manifest = build_app_graph_manifest()
    node_ids = {node.id for node in manifest.nodes}
    action_ids = {action.id for action in manifest.actions}

    assert set(ACTION_TARGETS) <= action_ids
    assert set(ACTION_TARGETS.values()) <= node_ids

    for action in manifest.actions:
        assert action.allowed_nodes, f"{action.id} must declare graph scope"
        assert ":" not in action.id, "App graph actions must be typed ids, not dynamic label commands"


def test_app_graph_free_text_policy_is_not_phrase_list_routing():
    manifest = build_app_graph_manifest()
    policy = manifest.policies["navigation"]
    assert policy["source_of_truth"] == "backend_app_graph"
    assert policy["no_frontend_workflow_authority"] is True

    action_ids = {action.id for action in manifest.actions}
    assert "approval.approve" in action_ids
    assert "approve:*" not in action_ids


def test_app_graph_router_disabled_clarifies_without_executing_text():
    import asyncio

    manifest = build_app_graph_manifest()
    actions = [
        route_action_to_card(action)
        for action in ACTION_SPECS
        if action.id in {AppActionIds.AUTH_SIGN_IN, AppActionIds.SAAS_AGENT_CREATE}
    ]
    router = AppGraphTurnRouter(provider="disabled")

    decision = asyncio.run(
        router.route(
            user_input="create a medusa storefront agent",
            state=AppGraphState(node="home"),
            actions=actions,
            manifest=manifest,
        )
    )

    assert decision.intent == "clarify"
    assert decision.action_id is None
    assert decision.confidence == 1.0
    assert "I'm SaaStoAgent" in (decision.clarification or "")
    assert "Sign in" not in (decision.clarification or "")
    assert "Create account" not in (decision.clarification or "")
    assert "Create SaaS Agent" not in (decision.clarification or "")
    assert router.action_needs_clarification(decision, actions) == decision.clarification
    assert "not available" not in (decision.clarification or "").lower()


def test_app_graph_router_requires_structured_slots_before_action():
    action = next(action for action in ACTION_SPECS if action.id == AppActionIds.SAAS_AGENT_CREATE)
    card = route_action_to_card(action)
    router = AppGraphTurnRouter(provider="disabled")

    missing = router.action_needs_clarification(
        decision=router._coerce_decision(
            '{"intent":"action","action_id":"saas_agent.create","slots":{},"confidence":0.99}',
            [card],
            provider="test",
        ),
        actions=[card],
    )

    assert missing is not None
    assert "Name" in missing
    assert "Slug" in missing


def test_app_graph_connection_options_include_medusa_targets():
    action = next(action for action in ACTION_SPECS if action.id == AppActionIds.CONNECTION_ACTIVATE)
    target_field = next(field for field in action.fields if field.key == "api_target")
    option_values = {option["value"] for option in target_field.options or []}

    assert {"medusa_storefront", "medusa_admin", "custom_api"} <= option_values


def test_app_graph_product_shell_hides_internal_route_deck_copy():
    shell_path = Path(__file__).parents[2] / "frontend" / "src" / "components" / "appGraph" / "AppGraphShell.tsx"
    source = shell_path.read_text(encoding="utf-8")
    product_source = source.split("function DiagnosticsPanel", 1)[0]

    forbidden_visible_copy = [
        "SaaStoAgent RouteDeck",
        "Central graph chat",
        "Message the app graph",
        "typed action",
        "visible RouteDeck actions",
        "node:",
        "reachable:",
    ]
    for text in forbidden_visible_copy:
        assert text not in product_source

    assert "RouteDeck diagnostics" in source
