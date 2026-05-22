from __future__ import annotations

import uuid
from types import SimpleNamespace

from backend.services.app_graph import (
    ACTION_TARGETS,
    APP_GRAPH_GROUPS,
    APP_GRAPH_VERSION,
    NODE_HANDLERS,
    build_app_graph_manifest,
    corpus_graph_runtime,
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


def test_app_graph_connection_activation_is_user_configured_not_target_preset():
    action = next(action for action in ACTION_SPECS if action.id == AppActionIds.CONNECTION_ACTIVATE)
    field_by_key = {field.key: field for field in action.fields}

    assert "api_target" not in field_by_key
    assert field_by_key["name"].placeholder == "Production API"
    assert field_by_key["base_url"].placeholder == "https://api.example.com"
    assert field_by_key["spec_url"].placeholder == "https://api.example.com/openapi.json"
    assert field_by_key["spec_url"].required is False
    assert field_by_key["raw_spec"].field_type == "textarea"
    assert field_by_key["auth_type"].default == "none"


def test_product_runtime_has_no_medusa_presets_or_defaults():
    root = Path(__file__).parents[2]
    product_paths = [
        root / "backend" / "services" / "app_graph" / "manifest.py",
        root / "backend" / "services" / "saas_agent_route_deck.py",
        root / "backend" / "services" / "route_deck" / "catalog.py",
        root / "frontend" / "src" / "components" / "appGraph" / "AppGraphShell.tsx",
        root / "frontend" / "src" / "components" / "appGraph" / "corpusRouteDeckClient.ts",
        root / "frontend" / "src" / "components" / "appGraph" / "corpusOperations.tsx",
        root / "frontend" / "src" / "components" / "appGraph" / "corpusSurfaces.tsx",
        root / "frontend" / "src" / "components" / "appGraph" / "CorpusRouteDeckDiagnostics.tsx",
        root / "frontend" / "src" / "components" / "saasAgent" / "ConnectSetupView.tsx",
    ]
    for path in product_paths:
        source = path.read_text(encoding="utf-8").lower()
        assert "medusa" not in source, path


def test_app_graph_product_shell_hides_internal_route_deck_copy():
    app_graph_path = Path(__file__).parents[2] / "frontend" / "src" / "components" / "appGraph"
    source = (app_graph_path / "AppGraphShell.tsx").read_text(encoding="utf-8")
    diagnostics_source = (app_graph_path / "CorpusRouteDeckDiagnostics.tsx").read_text(encoding="utf-8")
    product_source = source

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

    assert "RouteDeck navgraph diagnostics" in diagnostics_source


def test_product_shell_uses_corpus_and_routedeck_contracts_not_legacy_app_graph_endpoints():
    app_graph_path = Path(__file__).parents[2] / "frontend" / "src" / "components" / "appGraph"
    shell_source = (app_graph_path / "AppGraphShell.tsx").read_text(encoding="utf-8")
    client_source = (app_graph_path / "corpusRouteDeckClient.ts").read_text(encoding="utf-8")
    product_source = shell_source + "\n" + client_source

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
    surface_path = Path(__file__).parents[2] / "frontend" / "src" / "components" / "appGraph" / "corpusSurfaces.tsx"
    source = surface_path.read_text(encoding="utf-8")
    auth_surface_source = source.split("export function AuthSurfaceCard", 1)[1].split("export function Fact", 1)[0]

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


def test_material_workbench_proposal_surface_has_real_card_boundary():
    shell_path = Path(__file__).parents[2] / "frontend" / "src" / "components" / "appGraph" / "AppGraphShell.tsx"
    source = shell_path.read_text(encoding="utf-8")
    proposal_source = source.split("function ProposalPanel", 1)[1].split("function QuickActionChips", 1)[0]

    assert 'data-testid="corpus-proposal-surface"' in proposal_source
    assert "border border-border" in proposal_source
    assert "bg-card" in proposal_source
    assert "dark:bg-muted" in proposal_source


def test_connection_setup_surface_renders_real_api_forms():
    surface_path = Path(__file__).parents[2] / "frontend" / "src" / "components" / "appGraph" / "corpusSurfaces.tsx"
    source = surface_path.read_text(encoding="utf-8")
    connection_source = source.split("export function ConnectionSetupSurface", 1)[1].split("export function ActiveSurfacePanel", 1)[0]

    assert 'data-testid="connection-setup-surface"' in connection_source
    assert "connection.preview" in connection_source
    assert "connection.activate" in connection_source
    assert "Save and activate API" in connection_source
    assert "OperationForm" in connection_source


def test_builder_surface_exposes_owner_approval_controls():
    shell_path = Path(__file__).parents[2] / "frontend" / "src" / "components" / "appGraph" / "AppGraphShell.tsx"
    source = shell_path.read_text(encoding="utf-8")

    assert "PendingApprovalsCard" in source
    assert "/approvals/pending" in source
    assert "/approve" in source
    assert "/cancel" in source
    assert 'data-testid="pending-approvals-card"' in source


def test_deployed_chat_subscribes_to_public_session_events():
    page_path = Path(__file__).parents[2] / "frontend" / "src" / "pages" / "DeployedAgentChatPage.tsx"
    source = page_path.read_text(encoding="utf-8")

    assert "useDeployedSessionEvents" in source
    assert "/sessions/${sessionId}/events" in source
    assert "appendPublicAssistantMessage" in source


def test_docker_e2e_harness_is_first_class_and_uses_external_artifacts():
    frontend_path = Path(__file__).parents[2] / "frontend"
    package_source = (frontend_path / "package.json").read_text(encoding="utf-8")
    harness_path = frontend_path / "scripts" / "e2e-docker.mjs"
    fixture_path = frontend_path / "scripts" / "mock-storefront-api.mjs"

    harness_source = harness_path.read_text(encoding="utf-8")
    fixture_source = fixture_path.read_text(encoding="utf-8")

    assert '"e2e:docker": "node scripts/e2e-docker.mjs"' in package_source
    assert "SAASTOAGENT_E2E_ARTIFACT_DIR" in harness_source
    assert "os.tmpdir()" in harness_source
    assert "http://localhost:3007" in harness_source
    assert "host.docker.internal:9109" in harness_source
    assert "Sandbox Hoodie" in harness_source
    assert "forbiddenPublicLeaks" in harness_source
    assert "Sandbox Hoodie" in fixture_source
    assert "/openapi.json" in fixture_source


def test_agent_route_without_node_uses_agent_home_state_not_home():
    app_graph_path = Path(__file__).parents[2] / "frontend" / "src" / "components" / "appGraph"
    shell_source = (app_graph_path / "AppGraphShell.tsx").read_text(encoding="utf-8")
    client_source = (app_graph_path / "corpusRouteDeckClient.ts").read_text(encoding="utf-8")
    corpus_state_path_source = client_source.split("function corpusStatePath", 1)[1].split("function createSaaStoAgentRouteDeckStore", 1)[0]
    turn_source = shell_source.split("const turn = useMutation", 1)[1].split("const hasStreamingCorpusMessage", 1)[0]

    assert "saasAgentId ? 'agent_home'" in corpus_state_path_source
    assert "currentGraphState?.node === 'home' && saasAgentId" in turn_source
    assert "params.set('node_id', streamNodeId)" in turn_source


def test_routedeck_location_sync_does_not_trigger_browser_navigation():
    client_path = Path(__file__).parents[2] / "frontend" / "src" / "components" / "appGraph" / "corpusRouteDeckClient.ts"
    source = client_path.read_text(encoding="utf-8")
    sync_source = source.split("function syncBrowserPathWithoutNavigation", 1)[1]

    assert "window.history.replaceState" in sync_source
    assert "PopStateEvent" not in sync_source
    assert "window.dispatchEvent" not in sync_source


def test_surface_opening_prompt_for_connection_is_deterministic_not_a_choice_question():
    action = next(action for action in ACTION_SPECS if action.id == AppActionIds.CONNECTION_CONFIGURE)
    content = corpus_graph_runtime._deterministic_surface_prompt(action)

    assert "Connection setup is open" in content
    assert "what would you like" not in content.lower()
    assert "which would you like" not in content.lower()


def test_api_setup_request_routes_to_connection_surface_when_agent_is_active():
    action = next(action for action in ACTION_SPECS if action.id == AppActionIds.CONNECTION_CONFIGURE)
    state = AppGraphState(node="agent_home", active_saas_agent_id=uuid.uuid4())
    projection = SimpleNamespace(legal_operations=[action])

    decision = corpus_graph_runtime._deterministic_turn_plan(
        user_input="let me setup the api",
        state=state,
        projection=projection,
    )

    assert decision is not None
    assert decision["intent"] == "open_surface"
    assert decision["operation_id"] == AppActionIds.CONNECTION_CONFIGURE
    assert "Connection setup is open" in decision["message"]
    assert "what would you like" not in decision["message"].lower()


def test_saas_agent_list_is_dispatchable_surface_and_open_is_bound_only():
    list_action = next(action for action in ACTION_SPECS if action.id == AppActionIds.SAAS_AGENT_LIST)
    open_action = next(action for action in ACTION_SPECS if action.id == AppActionIds.SAAS_AGENT_OPEN)
    list_operation = corpus_graph_runtime._operation_for_action(list_action)
    open_operation = corpus_graph_runtime._operation_for_action(open_action)

    assert ACTION_TARGETS[AppActionIds.SAAS_AGENT_LIST] == "saas_agent_select"
    assert list_action.invocation_kind == "surface"
    assert list_operation.invocation_kind == "surface"
    assert list_operation.can_dispatch_now is True
    assert open_action.invocation_kind == "entity_selector"
    assert open_operation.invocation_kind == "entity_selector"
    assert open_operation.required_args == ["saas_agent_id"]
    assert open_operation.missing_args == ["saas_agent_id"]
    assert open_operation.can_dispatch_now is False


def test_saas_agent_select_node_uses_list_surface():
    assert corpus_graph_runtime._active_surface_component_for_node("saas_agent_select") == "SaaSAgentListSurface"


def test_saas_agent_open_is_selector_not_one_click_dispatch_without_agent_id():
    action = next(action for action in ACTION_SPECS if action.id == AppActionIds.SAAS_AGENT_OPEN)
    operation = corpus_graph_runtime._operation_for_action(action)

    assert action.invocation_kind == "entity_selector"
    assert operation.invocation_kind == "entity_selector"
    assert operation.required_args == ["saas_agent_id"]
    assert operation.missing_args == ["saas_agent_id"]
    assert operation.can_dispatch_now is False


def test_material_workbench_only_one_click_dispatches_ready_operations():
    app_graph_path = Path(__file__).parents[2] / "frontend" / "src" / "components" / "appGraph"
    source = (app_graph_path / "AppGraphShell.tsx").read_text(encoding="utf-8")
    operations_source = (app_graph_path / "corpusOperations.tsx").read_text(encoding="utf-8")
    quick_actions_source = operations_source.split("function corpusQuickActions", 1)[1].split("function operationToQuickAction", 1)[0]
    quick_action_handler_source = source.split("const handleQuickAction", 1)[1].split("const handleRailSelect", 1)[0]
    dashboard_markup_source = source.split("if (surface.component === 'CorpusDashboardSurface')", 1)[1].split("return (", 1)[1].split("return (", 1)[0]

    assert "operation.can_dispatch_now" in quick_actions_source
    assert "operation.invocation_kind" in quick_actions_source
    assert "operation.can_dispatch_now === false" in quick_action_handler_source
    assert "saas_agent_id: agent.id" in source
    assert "onOpenSaaSAgent" in source
    assert "onOpenSaaSAgent(agent)" in dashboard_markup_source


def test_surface_opening_state_comes_from_routedeck_hook():
    app_graph_path = Path(__file__).parents[2] / "frontend" / "src" / "components" / "appGraph"
    shell_source = (app_graph_path / "AppGraphShell.tsx").read_text(encoding="utf-8")
    routedeck_provider_source = (
        Path(__file__).parents[3] / "routedeck" / "react" / "src" / "RouteDeckProvider.tsx"
    ).read_text(encoding="utf-8")

    assert "useRouteDeckSurfaceOpening" in routedeck_provider_source
    assert "useRouteDeckSurfaceOpening()" in shell_source
    assert "activeSurfaceOpening" in shell_source
    assert "'Opening surface'" in shell_source
    assert "Opening ${activeSurfaceOpening.label}" in shell_source


def test_material_workbench_dashboard_limits_agents_and_routes_to_list_surface():
    shell_path = Path(__file__).parents[2] / "frontend" / "src" / "components" / "appGraph" / "AppGraphShell.tsx"
    source = shell_path.read_text(encoding="utf-8")
    frame_source = source.split("function FrameSurfacePanel", 1)[1].split("function ProposalPanel", 1)[0]
    dashboard_source = source.split("if (surface.component === 'CorpusDashboardSurface')", 1)[1].split("return (", 1)[1].split("return (", 1)[0]

    assert "saasAgents.slice(0, 2)" in dashboard_source
    assert "saas_agent.list" in frame_source
    assert "List agents" in dashboard_source
    assert "agent_count" in frame_source


def test_material_workbench_agent_list_surface_binds_agent_open_operation():
    shell_path = Path(__file__).parents[2] / "frontend" / "src" / "components" / "appGraph" / "AppGraphShell.tsx"
    surface_path = Path(__file__).parents[2] / "frontend" / "src" / "components" / "appGraph" / "corpusSurfaces.tsx"
    source = shell_path.read_text(encoding="utf-8") + "\n" + surface_path.read_text(encoding="utf-8")

    assert "SaaSAgentListSurface" in source
    list_surface_source = source.split("export function SaaSAgentListSurface", 1)[1].split("export function AuthSurfaceCard", 1)[0]
    assert 'data-testid="saas-agent-list-surface"' in list_surface_source
    assert "search" in list_surface_source
    assert "filteredAgents" in list_surface_source
    assert "operation_id: 'saas_agent.open'" in list_surface_source
    assert "saas_agent_id: agent.id" in list_surface_source


def test_auto_operation_stream_emits_done_after_operation_completed():
    runtime_path = Path(__file__).parents[1] / "services" / "app_graph" / "runtime.py"
    source = runtime_path.read_text(encoding="utf-8")
    auto_operation_source = source.split('if operation.execution_mode == "auto":', 1)[1].split("proposal = CorpusProposal", 1)[0]

    assert '"event_type": "operation_completed"' in auto_operation_source
    assert '"event_type": "corpus_done"' in auto_operation_source
    assert '"status": "committed"' in auto_operation_source


def test_material_workbench_proposal_waits_for_input_without_spinner_status():
    shell_path = Path(__file__).parents[2] / "frontend" / "src" / "components" / "appGraph" / "AppGraphShell.tsx"
    source = shell_path.read_text(encoding="utf-8")
    visible_status_source = source.split("const visibleStatus", 1)[1].split("const composerPlaceholder", 1)[0]
    quick_action_source = source.split("const handleQuickAction", 1)[1].split("const handleRailSelect", 1)[0]
    status_pill_source = source.split("function StatusPill", 1)[1].split("function AgentConversation", 1)[0]

    assert "pendingProposal" in visible_status_source
    assert "'Waiting for input'" in visible_status_source
    assert "setCorpusStatus('Preparing proposal')" not in quick_action_source
    assert "'Waiting for input'" not in status_pill_source.split("includes(status)", 1)[0]


def test_material_tokens_share_primary_and_secondary_across_themes():
    css_path = Path(__file__).parents[2] / "frontend" / "src" / "index.css"
    source = css_path.read_text(encoding="utf-8")
    root_source = source.split(":root {", 1)[1].split("}", 1)[0]
    dark_source = source.split(".dark {", 1)[1].split("}", 1)[0]

    assert "--primary: 213 61% 41%;" in root_source
    assert "--primary: 213 61% 41%;" in dark_source
    assert "--secondary: 29 65% 38%;" in root_source
    assert "--secondary: 29 65% 38%;" in dark_source
    assert "--secondary: 220 9% 24%;" not in dark_source


def test_product_diagnostics_are_read_only():
    diagnostics_path = Path(__file__).parents[2] / "frontend" / "src" / "components" / "appGraph" / "CorpusRouteDeckDiagnostics.tsx"
    diagnostics_source = diagnostics_path.read_text(encoding="utf-8")

    assert "onActionSelect" not in diagnostics_source
    assert "executeOperation" not in diagnostics_source
    assert "onOperationSelect" not in diagnostics_source


def test_legacy_app_graph_routes_are_not_registered():
    from backend.main import app

    legacy_routes = [
        route for route in app.routes if getattr(route, "path", "").startswith("/api/app/graph")
    ]

    assert legacy_routes == []
