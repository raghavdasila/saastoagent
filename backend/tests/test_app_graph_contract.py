from __future__ import annotations

from backend.services.corpus import (
    ACTION_TARGETS,
    CORPUS_GRAPH_GROUPS,
    CORPUS_GRAPH_VERSION,
    NODE_HANDLERS,
    build_corpus_manifest,
    validate_corpus_manifest,
)
from backend.services.corpus.corpus_operations import CorpusOperationPolicy
from backend.services.corpus.manifest import ACTION_SPECS, CorpusActionIds
from backend.services.corpus.corpus_surfaces import CorpusSurfaceRegistry
from routedeck_langgraph import validate_langgraph_contract
from pathlib import Path
from backend.core.schemas import ActionCatalogRead


def _operation_for_action(action):
    return CorpusOperationPolicy().operation_for_action(action)


def test_app_graph_manifest_is_valid_and_handler_complete():
    assert validate_corpus_manifest() == []
    manifest = build_corpus_manifest()

    assert manifest.version == CORPUS_GRAPH_VERSION
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
    manifest = build_corpus_manifest()
    assert validate_langgraph_contract(
        manifest,
        NODE_HANDLERS,
        {},
        groups=CORPUS_GRAPH_GROUPS,
    ) == []

    node_ids = {node.id for node in manifest.nodes}
    action_ids = {action.id for action in manifest.actions}
    for edge in manifest.edges:
        assert edge.from_stage in node_ids
        assert edge.to_stage in node_ids
        if edge.action_id:
            assert edge.action_id in action_ids


def test_app_graph_manifest_edges_are_semantic_topology_not_global_actions():
    manifest = build_corpus_manifest()
    edges = {(edge.from_stage, edge.to_stage, edge.action_id) for edge in manifest.edges}

    assert len(manifest.edges) < len(manifest.nodes) * 2
    assert ("home", "auth_register", CorpusActionIds.AUTH_REGISTER) in edges
    assert ("agent_home", "connection_configure", CorpusActionIds.CONNECTION_CONFIGURE) in edges
    assert ("connection_configure", "schema_preview", CorpusActionIds.CONNECTION_PREVIEW) in edges
    assert ("schema_preview", "catalog_activation", CorpusActionIds.CONNECTION_ACTIVATE) in edges
    assert ("catalog_activation", "catalog", None) in edges
    assert ("qa", "home", CorpusActionIds.HOME) not in edges
    assert ("memory", "agent_home", CorpusActionIds.AGENT_HOME) not in edges


def test_app_graph_actions_are_scoped_and_target_typed_nodes():
    manifest = build_corpus_manifest()
    node_ids = {node.id for node in manifest.nodes}
    action_ids = {action.id for action in manifest.actions}

    assert set(ACTION_TARGETS) <= action_ids
    assert set(ACTION_TARGETS.values()) <= node_ids

    for action in manifest.actions:
        assert action.allowed_nodes, f"{action.id} must declare graph scope"
        assert ":" not in action.id, "App graph actions must be typed ids, not dynamic label commands"


def test_app_graph_free_text_policy_is_not_phrase_list_routing():
    manifest = build_corpus_manifest()
    policy = manifest.policies["navigation"]
    assert policy["source_of_truth"] == "backend_corpus_graph"
    assert policy["no_frontend_workflow_authority"] is True

    action_ids = {action.id for action in manifest.actions}
    assert "approval.approve" in action_ids
    assert "approve:*" not in action_ids


def test_corpus_runtime_has_no_phrase_routing_helpers():
    runtime_path = Path(__file__).parents[2] / "backend" / "services" / "corpus" / "corpus_routedeck_runtime.py"
    source = runtime_path.read_text(encoding="utf-8")

    forbidden = [
        "_deterministic_turn_plan",
        "_deterministic_surface_open_plan",
        "_deterministic_surface_switch_plan",
        "_projection_current_surface_id",
        "_projection_surfaces",
        "_match_surface_from_request",
        "_normalized_turn_text",
        "_turn_tokens",
        "_looks_like_api_setup_request",
        "_looks_like_agent_list_request",
        "_surface_match_phrases",
        "deterministic_open_message",
    ]
    for text in forbidden:
        assert text not in source, text


def test_app_graph_connection_activation_is_user_configured_not_target_preset():
    action = next(action for action in ACTION_SPECS if action.id == CorpusActionIds.CONNECTION_ACTIVATE)
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
        root / "backend" / "services" / "corpus" / "manifest.py",
        root / "backend" / "services" / "saas_agent_route_deck.py",
        root / "backend" / "services" / "route_deck" / "catalog.py",
        root / "frontend" / "src" / "components" / "corpus" / "CorpusShell.tsx",
        root / "frontend" / "src" / "components" / "corpus" / "corpusActiveSurfaces.tsx",
        root / "frontend" / "src" / "components" / "corpus" / "corpusFrameSurfaces.tsx",
        root / "frontend" / "src" / "components" / "corpus" / "corpusRouteDeckClient.ts",
        root / "frontend" / "src" / "components" / "corpus" / "corpusOperations.tsx",
        root / "frontend" / "src" / "components" / "corpus" / "corpusSurfaces.tsx",
        root / "frontend" / "src" / "components" / "corpus" / "CorpusRouteDeckDiagnostics.tsx",
        root / "frontend" / "src" / "components" / "saasAgent" / "ConnectSetupView.tsx",
    ]
    for path in product_paths:
        source = path.read_text(encoding="utf-8").lower()
        assert "medusa" not in source, path


def test_app_graph_product_shell_hides_internal_route_deck_copy():
    app_graph_path = Path(__file__).parents[2] / "frontend" / "src" / "components" / "corpus"
    source = (app_graph_path / "CorpusShell.tsx").read_text(encoding="utf-8")
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
    app_graph_path = Path(__file__).parents[2] / "frontend" / "src" / "components" / "corpus"
    shell_source = (app_graph_path / "CorpusShell.tsx").read_text(encoding="utf-8")
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
        "syncBrowserPathWithoutNavigation",
    ]
    for text in forbidden:
        assert text not in product_source


def test_corpus_state_and_action_routes_use_routedeck_runtime_boundary():
    route_path = Path(__file__).parents[1] / "routes" / "corpus_graph.py"
    source = route_path.read_text(encoding="utf-8")
    state_route = source.split('async def get_corpus_state(', 1)[1].split('@router.get("/api/corpus/stream")', 1)[0]
    action_route = source.split('async def corpus_action(', 1)[1].split('@router.get("/api/diagnostics/stream")', 1)[0]

    assert "route_deck_runtime.snapshot(" in state_route
    assert "route_deck_runtime.dispatch(" in action_route
    assert "corpus_graph_runtime.corpus_state(" not in state_route
    assert "corpus_graph_runtime.corpus_action(" not in action_route
    assert "_corpus_state_response_from_routedeck_state" in state_route
    assert "_corpus_action_response_from_routedeck_result" in action_route


def test_app_graph_backend_exports_only_corpus_routedeck_runtime_name():
    root = Path(__file__).parents[1]
    app_graph_paths = list((root / "services" / "corpus").glob("*.py"))
    test_paths = [
        path
        for path in (root / "tests").glob("test_*routedeck*.py")
        if path.name != "test_toolrouter_adapter.py"
    ]
    old_runtime_name = "SaaStoAgent" + "RouteDeck" + "Adapter"
    old_module_name = "routedeck_" + "adapter"

    assert not (root / "services" / "corpus" / f"{old_module_name}.py").exists()
    for path in [*app_graph_paths, *test_paths]:
        source = path.read_text(encoding="utf-8")
        assert old_runtime_name not in source, path
        assert old_module_name not in source, path
    assert not (root / "tests" / f"test_{old_module_name}_contract.py").exists()


def test_auth_surface_completion_does_not_force_page_reload():
    surface_path = Path(__file__).parents[2] / "frontend" / "src" / "components" / "corpus" / "corpusSurfaces.tsx"
    source = surface_path.read_text(encoding="utf-8")
    auth_surface_source = source.split("export function AuthSurfaceCard", 1)[1].split("export function Fact", 1)[0]

    assert "window.location.assign" not in auth_surface_source
    assert "window.location.reload" not in auth_surface_source


def test_material_workbench_renders_corpus_chips_and_auth_identity_without_raw_ids():
    shell_path = Path(__file__).parents[2] / "frontend" / "src" / "components" / "corpus" / "CorpusShell.tsx"
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
    shell_path = Path(__file__).parents[2] / "frontend" / "src" / "components" / "corpus" / "CorpusShell.tsx"
    source = shell_path.read_text(encoding="utf-8")
    rail_source = source.split("function CapabilityRail", 1)[1].split("function CapabilityStatusIcon", 1)[0]

    assert "Workflow switcher" in rail_source
    assert "Workflow switcher:" in source
    assert 'data-testid="rail-node-notice"' in source
    assert "disabled={!operation || active}" not in rail_source
    assert "onSelect(item, action, status)" in rail_source


def test_material_workbench_review_surface_is_route_deck_hosted():
    app_graph_path = Path(__file__).parents[2] / "frontend" / "src" / "components" / "corpus"
    shell_source = (app_graph_path / "CorpusShell.tsx").read_text(encoding="utf-8")
    active_surface_source = (app_graph_path / "corpusActiveSurfaces.tsx").read_text(encoding="utf-8")
    surface_source = (app_graph_path / "corpusSurfaces.tsx").read_text(encoding="utf-8")
    catalog_source = (app_graph_path / "corpusRouteDeckCatalog.ts").read_text(encoding="utf-8")

    assert "function ProposalPanel" not in shell_source
    assert "pendingProposal" not in shell_source
    assert "RouteDeckSurfaceHost" in active_surface_source
    assert "CorpusOperationReviewSurface" in catalog_source
    assert 'data-testid="corpus-operation-review-surface"' in surface_source


def test_connection_setup_surface_renders_real_api_forms():
    surface_path = Path(__file__).parents[2] / "frontend" / "src" / "components" / "corpus" / "corpusSurfaces.tsx"
    source = surface_path.read_text(encoding="utf-8")
    connection_source = source.split("export function ConnectionSetupSurface", 1)[1].split("export function ActiveSurfacePanel", 1)[0]

    assert 'data-testid="connection-setup-surface"' in connection_source
    assert "connection.preview" in connection_source
    assert "connection.activate" in connection_source
    assert "Save and activate API" in connection_source
    assert "OperationForm" in connection_source


def test_builder_surface_exposes_owner_approval_controls():
    shell_path = Path(__file__).parents[2] / "frontend" / "src" / "components" / "corpus" / "CorpusShell.tsx"
    source = shell_path.read_text(encoding="utf-8")
    pending_card_source = source.split("function PendingApprovalsCard", 1)[1].split("function ", 1)[0]

    assert "PendingApprovalsCard" in source
    assert "/approvals/pending" in source
    assert "/approve" in source
    assert "/cancel" in source
    assert 'data-testid="pending-approvals-card"' in source
    assert "enabled: enabled && Boolean(saasAgentId)" in pending_card_source
    assert "refetchInterval: enabled ? 2000 : false" in pending_card_source
    assert "refetchInterval: 2000" not in pending_card_source


def test_deployed_chat_subscribes_to_public_session_events():
    page_path = Path(__file__).parents[2] / "frontend" / "src" / "pages" / "DeployedAgentChatPage.tsx"
    source = page_path.read_text(encoding="utf-8")

    assert "useDeployedSessionEvents" in source
    assert "/sessions/${sessionId}/events" in source
    assert "appendPublicAssistantMessage" in source


def test_deployed_chat_collapses_raw_json_payloads_without_hiding_builder_diagnostics():
    frontend_root = Path(__file__).parents[2] / "frontend" / "src"
    page_source = (frontend_root / "pages" / "DeployedAgentChatPage.tsx").read_text(encoding="utf-8")
    message_source = (frontend_root / "components" / "agent" / "MessageBubble.tsx").read_text(encoding="utf-8")
    json_source = (frontend_root / "components" / "agent" / "CollapsibleJsonMessage.tsx").read_text(encoding="utf-8")
    diagnostics_source = (
        frontend_root / "components" / "corpus" / "CorpusRouteDeckDiagnostics.tsx"
    ).read_text(encoding="utf-8")

    assert "collapseJsonPayloads" in page_source
    assert "CollapsibleJsonMessage" in message_source
    assert 'data-testid="assistant-json-payload"' in json_source
    assert "<details" in json_source
    assert "open={false}" in json_source
    assert "JSON.stringify(parsed, null, 2)" in json_source
    assert "Raw RouteDeck navgraph JSON" in diagnostics_source


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
    app_graph_path = Path(__file__).parents[2] / "frontend" / "src" / "components" / "corpus"
    shell_source = (app_graph_path / "CorpusShell.tsx").read_text(encoding="utf-8")
    client_source = (app_graph_path / "corpusRouteDeckClient.ts").read_text(encoding="utf-8")
    corpus_state_path_source = client_source.split("function corpusStatePath", 1)[1].split("function createSaaStoAgentRouteDeckStore", 1)[0]
    turn_source = shell_source.split("const turn = useMutation", 1)[1].split("const hasStreamingCorpusMessage", 1)[0]

    assert "saasAgentId ? corpusNodeIds.agentHome" in corpus_state_path_source
    assert "currentGraphState?.node === corpusNodeIds.home && saasAgentId" in turn_source
    assert "params.set('node_id', streamNodeId)" in turn_source


def test_routedeck_location_sync_does_not_trigger_browser_navigation():
    client_path = Path(__file__).parents[2] / "frontend" / "src" / "components" / "corpus" / "corpusRouteDeckClient.ts"
    source = client_path.read_text(encoding="utf-8")

    assert "createCorpusRouteCodec" in source
    assert "corpusPathFromRouteDeckState" in source
    assert "window.history.replaceState" not in source
    assert "window.dispatchEvent" not in source


def test_connection_configure_operation_is_exposed_as_surface_context():
    action = next(action for action in ACTION_SPECS if action.id == CorpusActionIds.CONNECTION_CONFIGURE)
    operation = _operation_for_action(action)

    assert ACTION_TARGETS[CorpusActionIds.CONNECTION_CONFIGURE] == "connection_configure"
    assert operation.can_dispatch_now is True
    assert operation.target_node == "connection_configure"


def test_deployment_publish_is_product_operation_available_from_agent_context():
    action = next(action for action in ACTION_SPECS if action.id == CorpusActionIds.DEPLOYMENT_SAVE)
    operation = _operation_for_action(action)

    field_keys = {field.key for field in action.fields}
    assert ACTION_TARGETS[CorpusActionIds.DEPLOYMENT_SAVE] == "agent_home"
    assert action.label == "Save deployment"
    assert action.category == "deployment"
    assert operation.execution_mode == "review"
    assert operation.invocation_kind == "form"
    assert operation.target_node == "agent_home"
    assert {"enabled", "visitor_auth_mode", "execution_mode", "default_write_policy", "welcome_message"} <= field_keys


def test_router_prompt_uses_planning_context_not_raw_projection():
    runtime_path = Path(__file__).parents[2] / "backend" / "services" / "corpus" / "corpus_routedeck_runtime.py"
    source = runtime_path.read_text(encoding="utf-8")

    assert '"planning_context"' in source
    assert "build_corpus_turn_planning_context" in source
    assert "normalize_corpus_turn_plan" in source
    assert "Use only operation ids present in planning_context.legal_operations." in source
    assert "Use \"reply_now\" only for informational answers that do not change the current workspace." in source
    assert "return a legal typed operation or surface_intent instead" in source
    assert "Do not claim that a workspace surface is being opened" in source


def test_saas_agent_list_is_dispatchable_surface_and_open_is_bound_only():
    list_action = next(action for action in ACTION_SPECS if action.id == CorpusActionIds.SAAS_AGENT_LIST)
    open_action = next(action for action in ACTION_SPECS if action.id == CorpusActionIds.SAAS_AGENT_OPEN)
    list_operation = _operation_for_action(list_action)
    open_operation = _operation_for_action(open_action)

    assert ACTION_TARGETS[CorpusActionIds.SAAS_AGENT_LIST] == "saas_agent_select"
    assert list_action.invocation_kind == "surface"
    assert list_operation.invocation_kind == "surface"
    assert list_operation.can_dispatch_now is True
    assert open_action.invocation_kind == "entity_selector"
    assert open_operation.invocation_kind == "entity_selector"
    assert open_operation.required_args == ["saas_agent_id"]
    assert open_operation.missing_args == ["saas_agent_id"]
    assert open_operation.can_dispatch_now is False


def test_saas_agent_select_node_uses_list_surface():
    assert CorpusSurfaceRegistry().active_surface_component_for_node("saas_agent_select") == "SaaSAgentListSurface"


def test_saas_agent_open_is_selector_not_one_click_dispatch_without_agent_id():
    action = next(action for action in ACTION_SPECS if action.id == CorpusActionIds.SAAS_AGENT_OPEN)
    operation = _operation_for_action(action)

    assert action.invocation_kind == "entity_selector"
    assert operation.invocation_kind == "entity_selector"
    assert operation.required_args == ["saas_agent_id"]
    assert operation.missing_args == ["saas_agent_id"]
    assert operation.can_dispatch_now is False


def test_material_workbench_only_one_click_dispatches_ready_operations():
    app_graph_path = Path(__file__).parents[2] / "frontend" / "src" / "components" / "corpus"
    shell_source = (app_graph_path / "CorpusShell.tsx").read_text(encoding="utf-8")
    frame_source = (app_graph_path / "corpusFrameSurfaces.tsx").read_text(encoding="utf-8")
    source = shell_source + "\n" + frame_source
    operations_source = (app_graph_path / "corpusOperations.tsx").read_text(encoding="utf-8")
    quick_actions_source = operations_source.split("function corpusQuickActions", 1)[1].split("function operationToQuickAction", 1)[0]
    quick_action_handler_source = shell_source.split("const handleQuickAction", 1)[1].split("const handleRailSelect", 1)[0]

    assert "operation.can_dispatch_now" in quick_actions_source
    assert "operation.invocation_kind" in quick_actions_source
    assert "operation.can_dispatch_now === false" in quick_action_handler_source
    assert "saas_agent_id: agent.id" in source
    assert "onOpenSaaSAgent" in source
    assert "onOpenSaaSAgent(agent)" in frame_source


def test_node_navigation_uses_routedeck_controls_with_dirty_surface_prompt_bridge():
    app_graph_path = Path(__file__).parents[2] / "frontend" / "src" / "components" / "corpus"
    shell_source = (app_graph_path / "CorpusShell.tsx").read_text(encoding="utf-8")
    routedeck_provider_source = (
        Path(__file__).parents[3] / "routedeck" / "react" / "src" / "RouteDeckProvider.tsx"
    ).read_text(encoding="utf-8")

    assert "useRouteDeckSurfaceOpening" in routedeck_provider_source
    assert "useRouteDeckSurfaceOpening()" not in shell_source
    assert "Save changes before leaving this surface?" in shell_source
    assert "Save and continue" in shell_source
    assert "Continue without saving" in shell_source
    assert "Stay here" in shell_source
    assert "routeDeckStore.back()" in shell_source
    assert "routeDeckStore.forward()" in shell_source
    assert "routeDeckStore.cancel()" in shell_source


def test_capability_rail_is_projected_by_routedeck_not_hardcoded_in_frontend():
    app_graph_path = Path(__file__).parents[2] / "frontend" / "src" / "components" / "corpus"
    shell_source = (app_graph_path / "CorpusShell.tsx").read_text(encoding="utf-8")

    assert "projection.diagnostics?.capability_rail" in shell_source
    assert "function capabilityItems()" not in shell_source
    assert "nodes: ['connection_configure', 'schema_preview']" not in shell_source


def test_builder_surfaces_do_not_use_zustand_as_agent_source_of_truth():
    root = Path(__file__).parents[2] / "frontend" / "src" / "components"
    surface_paths = [
        root / "agent" / "AdminPanel.tsx",
        root / "agent" / "AgentChat.tsx",
        root / "agent" / "AttachmentsPanel.tsx",
        root / "agent" / "LearningPanel.tsx",
        root / "saasAgent" / "ActionsCanvas.tsx",
        root / "saasAgent" / "AgentChatStub.tsx",
        root / "saasAgent" / "ConnectSetupView.tsx",
        root / "saasAgent" / "EntitiesCanvas.tsx",
    ]

    for path in surface_paths:
        source = path.read_text(encoding="utf-8")
        assert "state.saasAgentId" not in source, path
        assert "storage.getSaaSAgentId" not in source, path


def test_learning_detail_navigation_uses_app_owned_routedeck_operations():
    frontend_root = Path(__file__).parents[2] / "frontend" / "src"
    learning_source = (frontend_root / "components" / "agent" / "LearningPanel.tsx").read_text(encoding="utf-8")
    catalog_source = (frontend_root / "components" / "corpus" / "corpusRouteDeckCatalog.ts").read_text(encoding="utf-8")

    assert "learningPolicyCandidateOpen" in catalog_source
    assert "learningActivePolicyOpen" in catalog_source
    assert "routeDeckStore.dispatch" in learning_source
    assert "corpusOperationIds.learningPolicyCandidateOpen" in learning_source
    assert "corpusOperationIds.learningActivePolicyOpen" in learning_source
    assert "corpusOperationIds.learningApprove" in learning_source
    assert "corpusOperationIds.learningReject" in learning_source
    assert "/agent/learnings/${id}/${action}" not in learning_source
    assert "agentApi.post<AgentLearningCandidate>" not in learning_source
    assert "routeDeckStore.openNode" not in learning_source


def test_instructions_save_is_app_graph_owned():
    root = Path(__file__).parents[2]
    app_graph_path = root / "frontend" / "src" / "components" / "corpus"
    manifest_source = (root / "backend" / "services" / "corpus" / "manifest.py").read_text(encoding="utf-8")
    runtime_source = (root / "backend" / "services" / "corpus" / "corpus_routedeck_runtime.py").read_text(encoding="utf-8")
    content_handler_source = (root / "backend" / "services" / "corpus" / "corpus_handlers" / "content.py").read_text(encoding="utf-8")
    catalog_source = (app_graph_path / "corpusRouteDeckCatalog.ts").read_text(encoding="utf-8")
    surface_source = (app_graph_path / "corpusSurfaces.tsx").read_text(encoding="utf-8")

    assert 'INSTRUCTIONS_SAVE = "instructions.save"' in manifest_source
    assert "async def instructions_save" in content_handler_source
    assert "_handle_instructions_save" not in runtime_source
    assert "corpusOperationIds.instructionsSave" in surface_source
    assert "routeDeckStore.dispatch" in surface_source
    assert "api.put<SaaSAgent>(`/saas-agents/${saasAgentId}/instructions`" not in surface_source
    assert "instructionsSave: 'instructions.save'" in catalog_source


def test_product_workbench_does_not_expose_routedeck_copy():
    app_graph_path = Path(__file__).parents[2] / "frontend" / "src" / "components" / "corpus"
    shell_source = (app_graph_path / "CorpusShell.tsx").read_text(encoding="utf-8")

    assert "active RouteDeck node" not in shell_source
    assert "RouteDeck Nodes" not in shell_source
    assert "RouteDeck node switcher" not in shell_source


def test_routedeck_debugger_does_not_label_navgraph_edges_with_actions():
    routedeck_root = Path(__file__).parents[3] / "routedeck" / "react" / "src"
    debugger_source = (routedeck_root / "RouteDeckDebugger.tsx").read_text(encoding="utf-8")
    routing_source = (routedeck_root / "routeDeckDebuggerRouting.ts").read_text(encoding="utf-8")

    assert "return edge.action_id || edge.condition || edge.type" not in debugger_source
    assert "edge.action_id || edge.condition || edge.type || 'edge'" not in debugger_source
    assert "edge.action_id || edge.condition || edge.type || 'edge'" not in routing_source


def test_corpus_workbench_derives_agent_context_from_routedeck_state():
    app_graph_path = Path(__file__).parents[2] / "frontend" / "src" / "components" / "corpus"
    shell_source = (app_graph_path / "CorpusShell.tsx").read_text(encoding="utf-8")
    client_source = (app_graph_path / "corpusRouteDeckClient.ts").read_text(encoding="utf-8")

    assert "function activeSaaSAgentIdFromRouteDeckState" in client_source
    assert "activeSaaSAgentIdFromRouteDeckState(routeDeckState)" in shell_source
    assert "state) => state.saasAgentId" not in shell_source
    assert "state) => state.setMirroredSaaSAgentId" in shell_source


def test_corpus_api_uses_explicit_saas_agent_context_not_storage_header():
    frontend_root = Path(__file__).parents[2] / "frontend" / "src"
    api_source = (frontend_root / "lib" / "api.ts").read_text(encoding="utf-8")
    builder_files = [
        frontend_root / "components" / "agent" / "AdminPanel.tsx",
        frontend_root / "components" / "agent" / "AgentChat.tsx",
        frontend_root / "components" / "agent" / "AttachmentsPanel.tsx",
        frontend_root / "components" / "agent" / "LearningPanel.tsx",
        frontend_root / "components" / "corpus" / "CorpusShell.tsx",
        frontend_root / "components" / "saasAgent" / "ActionsCanvas.tsx",
        frontend_root / "components" / "saasAgent" / "ConnectSetupView.tsx",
        frontend_root / "components" / "saasAgent" / "EntitiesCanvas.tsx",
    ]

    assert "storage.getSaaSAgentId" not in api_source
    assert "withSaaSAgent" in api_source
    for path in builder_files:
        source = path.read_text(encoding="utf-8")
        if "/saas-agents/${saasAgentId}" in source:
            assert "api.withSaaSAgent(saasAgentId)" in source, path


def test_zustand_store_is_named_as_ui_state_not_routedeck_state():
    frontend_root = Path(__file__).parents[2] / "frontend" / "src"
    store_path = frontend_root / "stores" / "saasAgentUiStore.ts"
    store_source = store_path.read_text(encoding="utf-8")

    assert store_path.exists()
    assert "interface SaaSAgentUiState" in store_source
    assert "mirroredSaaSAgentId" in store_source
    assert "setMirroredSaaSAgentId" in store_source
    assert "useSaaSAgentUiStore" in store_source

    for path in frontend_root.rglob("*.tsx"):
        source = path.read_text(encoding="utf-8")
        assert "@/stores/saasAgentStore" not in source, path
        assert "useSaaSAgentStore" not in source, path


def test_corpus_routedeck_ids_are_read_from_catalog():
    app_graph_path = Path(__file__).parents[2] / "frontend" / "src" / "components" / "corpus"
    catalog_source = (app_graph_path / "corpusRouteDeckCatalog.ts").read_text(encoding="utf-8")
    shell_source = (app_graph_path / "CorpusShell.tsx").read_text(encoding="utf-8")
    active_surface_source = (app_graph_path / "corpusActiveSurfaces.tsx").read_text(encoding="utf-8")
    frame_source = (app_graph_path / "corpusFrameSurfaces.tsx").read_text(encoding="utf-8")
    surface_source = (app_graph_path / "corpusSurfaces.tsx").read_text(encoding="utf-8")
    product_source = shell_source + "\n" + active_surface_source + "\n" + frame_source + "\n" + surface_source

    assert "corpusOperationIds" in catalog_source
    assert "corpusSurfaceComponents" in catalog_source
    assert "corpusNodeIds" in catalog_source
    assert "corpusOperationIds.openSaaSAgent" in product_source
    assert "corpusOperationIds.listSaaSAgents" in frame_source
    assert "corpusSurfaceComponents.entities" in active_surface_source
    assert "operation_id: 'saas_agent.open'" not in product_source


def test_material_workbench_dashboard_limits_agents_and_routes_to_list_surface():
    frame_path = Path(__file__).parents[2] / "frontend" / "src" / "components" / "corpus" / "corpusFrameSurfaces.tsx"
    frame_source = frame_path.read_text(encoding="utf-8")

    assert "saasAgents.slice(0, 2)" in frame_source
    assert "corpusOperationIds.listSaaSAgents" in frame_source
    assert "List agents" in frame_source
    assert "agent_count" in frame_source


def test_material_workbench_agent_list_surface_binds_agent_open_operation():
    shell_path = Path(__file__).parents[2] / "frontend" / "src" / "components" / "corpus" / "CorpusShell.tsx"
    surface_path = Path(__file__).parents[2] / "frontend" / "src" / "components" / "corpus" / "corpusSurfaces.tsx"
    source = shell_path.read_text(encoding="utf-8") + "\n" + surface_path.read_text(encoding="utf-8")

    assert "SaaSAgentListSurface" in source
    list_surface_source = source.split("export function SaaSAgentListSurface", 1)[1].split("export function AuthSurfaceCard", 1)[0]
    assert 'data-testid="saas-agent-list-surface"' in list_surface_source
    assert "search" in list_surface_source
    assert "filteredAgents" in list_surface_source
    assert "operation_id: corpusOperationIds.openSaaSAgent" in list_surface_source
    assert "saas_agent_id: agent.id" in list_surface_source


def test_auto_operation_stream_emits_done_after_operation_completed():
    runtime_path = Path(__file__).parents[1] / "services" / "corpus" / "corpus_routedeck_runtime.py"
    source = runtime_path.read_text(encoding="utf-8")

    assert '.events[0].model_dump(mode="json")' in source
    assert '"event_type": "corpus_done"' in source
    assert 'done_status = "review" if response.state.pending_operation_id == operation.id else "committed"' in source


def test_material_workbench_review_surface_uses_route_deck_active_surface_state():
    app_graph_path = Path(__file__).parents[2] / "frontend" / "src" / "components" / "corpus"
    shell_source = (app_graph_path / "CorpusShell.tsx").read_text(encoding="utf-8")
    active_surface_source = (app_graph_path / "corpusActiveSurfaces.tsx").read_text(encoding="utf-8")
    surface_source = (app_graph_path / "corpusSurfaces.tsx").read_text(encoding="utf-8")
    quick_action_source = shell_source.split("const handleQuickAction", 1)[1].split("const handleRailSelect", 1)[0]
    review_open_source = shell_source.split("const openReviewSurface", 1)[1].split("useEffect(() => {", 1)[0]
    conversation_source = shell_source.split("function AgentConversation", 1)[1].split("function QuickActionChips", 1)[0]

    assert "pendingProposal" not in shell_source
    assert "setCorpusStatus('Preparing proposal')" not in quick_action_source
    assert "pendingProposal ? (" not in conversation_source
    assert "activeSurfacePanel" in conversation_source
    assert "RouteDeckSurfaceHost" in active_surface_source
    assert 'data-testid="corpus-operation-review-surface"' in surface_source
    assert "operation_id: 'route.open_node'" not in review_open_source
    assert "pending_operation_id" not in review_open_source


def test_frontend_reads_context_lens_from_projection_not_side_surface_props():
    surface_path = Path(__file__).parents[2] / "frontend" / "src" / "components" / "corpus" / "corpusSurfaces.tsx"
    source = surface_path.read_text(encoding="utf-8")
    helper_source = source.split("export function contextLensFromProjection", 1)[1].split(
        "export function activeSurfaceFromProjection",
        1,
    )[0]

    assert "projection.context_lens" in helper_source
    assert "projection.surfaces.side" not in helper_source
    assert "sideSurface" not in helper_source


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
    diagnostics_path = Path(__file__).parents[2] / "frontend" / "src" / "components" / "corpus" / "CorpusRouteDeckDiagnostics.tsx"
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


def test_catalog_schema_includes_router_index_readiness():
    assert "router_index" in ActionCatalogRead.model_fields


def test_catalog_surface_contract_includes_request_matching_without_router_copy():
    backend_surface_path = Path(__file__).parents[1] / "services" / "corpus" / "corpus_surfaces.py"
    backend_surface_catalog_path = Path(__file__).parents[1] / "services" / "corpus" / "corpus_surface_catalog.py"
    activation_path = Path(__file__).parents[1] / "services" / "discovery" / "activation.py"
    frontend_active_surface_path = Path(__file__).parents[2] / "frontend" / "src" / "components" / "corpus" / "corpusActiveSurfaces.tsx"
    frontend_surface_path = Path(__file__).parents[2] / "frontend" / "src" / "components" / "corpus" / "corpusSurfaces.tsx"
    shell_path = Path(__file__).parents[2] / "frontend" / "src" / "components" / "corpus" / "CorpusShell.tsx"
    runtime_path = Path(__file__).parents[1] / "services" / "corpus" / "corpus_routedeck_runtime.py"
    internal_source = (
        backend_surface_path.read_text(encoding="utf-8")
        + "\n"
        + backend_surface_catalog_path.read_text(encoding="utf-8")
        + "\n"
        + runtime_path.read_text(encoding="utf-8")
    )
    product_visible_source = (
        activation_path.read_text(encoding="utf-8")
        + "\n"
        + frontend_active_surface_path.read_text(encoding="utf-8")
        + "\n"
        + frontend_surface_path.read_text(encoding="utf-8")
        + "\n"
        + shell_path.read_text(encoding="utf-8")
    )

    assert "router_index" in internal_source
    assert "router_documents_count" in internal_source
    assert "API references" in product_visible_source
    assert "Request matching" in product_visible_source
    assert "request matching" in product_visible_source
    assert "Router docs" not in product_visible_source
    assert "Router index:" not in product_visible_source
    assert "fusion router index" not in product_visible_source
    assert "Fusion router index" not in product_visible_source
    assert "move through the graph" not in product_visible_source
