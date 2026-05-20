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


def test_app_graph_manifest_edges_are_semantic_topology_not_global_actions():
    manifest = build_app_graph_manifest()
    edges = {(edge.from_stage, edge.to_stage, edge.action_id) for edge in manifest.edges}

    assert len(manifest.edges) < len(manifest.nodes) * 2
    assert ("home", "auth_register", AppActionIds.AUTH_REGISTER) in edges
    assert ("agent_home", "connection_configure", AppActionIds.CONNECTION_CONFIGURE) in edges
    assert ("connection_configure", "schema_preview", AppActionIds.CONNECTION_PREVIEW) in edges
    assert ("schema_preview", "catalog_activation", AppActionIds.CONNECTION_ACTIVATE) in edges
    assert ("catalog_activation", "catalog", None) in edges
    assert ("qa", "home", AppActionIds.HOME) not in edges
    assert ("memory", "agent_home", AppActionIds.AGENT_HOME) not in edges


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


def test_product_shell_uses_corpus_and_routedeck_contracts_not_legacy_app_graph_endpoints():
    shell_path = Path(__file__).parents[2] / "frontend" / "src" / "components" / "appGraph" / "AppGraphShell.tsx"
    source = shell_path.read_text(encoding="utf-8")
    product_source = source.split("function DiagnosticsPanel", 1)[0]

    assert "/corpus/state" in product_source
    assert "/corpus/stream" in product_source
    assert "/corpus/action" in product_source

    forbidden = [
        "/app/graph/snapshot",
        "/app/graph/action",
        "/routedeck/projection",
        "useRouteDeckOperations",
        "RouteDeckOperationDock",
        "available_actions",
        "persistent_actions",
        "function WorkSurface",
        "projection.diagnostics?.graph_state",
        "projection.diagnostics?.replace_path",
    ]
    for text in forbidden:
        assert text not in product_source


def test_auth_surface_completion_does_not_force_page_reload():
    shell_path = Path(__file__).parents[2] / "frontend" / "src" / "components" / "appGraph" / "AppGraphShell.tsx"
    source = shell_path.read_text(encoding="utf-8")
    auth_surface_source = source.split("function AuthSurfaceCard", 1)[1].split("function ContextPanel", 1)[0]

    assert "window.location.assign" not in auth_surface_source
    assert "window.location.reload" not in auth_surface_source


def test_material_workbench_renders_corpus_chips_and_auth_identity_without_raw_ids():
    shell_path = Path(__file__).parents[2] / "frontend" / "src" / "components" / "appGraph" / "AppGraphShell.tsx"
    source = shell_path.read_text(encoding="utf-8")
    conversation_source = source.split("function AgentConversation", 1)[1].split("function QuickActionChips", 1)[0]
    quick_action_source = source.split("function QuickActionChips", 1)[1].split("function CapabilityRail", 1)[0]

    assert 'data-testid="corpus-quick-actions"' in quick_action_source
    assert "latestAssistantMessageId" in conversation_source
    assert "message.id === latestAssistantMessageId" in conversation_source
    assert 'data-testid="auth-user-pill"' in source
    assert 'data-testid="capability-rail"' in source
    assert "operation.id}</span>" not in quick_action_source
    assert "{operation.id}" not in quick_action_source


def test_material_workbench_rail_is_node_switcher_not_disabled_action_dock():
    shell_path = Path(__file__).parents[2] / "frontend" / "src" / "components" / "appGraph" / "AppGraphShell.tsx"
    source = shell_path.read_text(encoding="utf-8")
    rail_source = source.split("function CapabilityRail", 1)[1].split("function CapabilityStatusIcon", 1)[0]

    assert "RouteDeck node switcher" in rail_source
    assert "Node switcher:" in source
    assert 'data-testid="rail-node-notice"' in source
    assert "disabled={!operation || active}" not in rail_source
    assert "onSelect(item, action, status)" in rail_source


def test_product_diagnostics_are_read_only():
    shell_path = Path(__file__).parents[2] / "frontend" / "src" / "components" / "appGraph" / "AppGraphShell.tsx"
    source = shell_path.read_text(encoding="utf-8")
    diagnostics_source = source.split("function DiagnosticsPanel", 1)[1]

    assert "onActionSelect" not in diagnostics_source
    assert "executeOperation" not in diagnostics_source
    assert "onOperationSelect" not in diagnostics_source


def test_legacy_app_graph_routes_are_not_registered():
    from backend.main import app

    legacy_routes = [
        route for route in app.routes if getattr(route, "path", "").startswith("/api/app/graph")
    ]

    assert legacy_routes == []
