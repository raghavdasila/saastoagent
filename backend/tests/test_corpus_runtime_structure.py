from __future__ import annotations

from pathlib import Path


BACKEND_ROOT = Path(__file__).parents[1]
CORPUS_ROOT = BACKEND_ROOT / "corpus"
CORPUS_GRAPH_ROOT = CORPUS_ROOT / "graph"
CORPUS_SCHEMA_ROOT = CORPUS_ROOT / "schemas"
RETIRED_SERVICE_CORPUS_ROOT = BACKEND_ROOT / "services" / "corpus"
RETIRED_GRAPH_ROOT = BACKEND_ROOT / "services" / "app_graph"
ALLOWED_CORPUS_IMPLEMENTATION_FILES = {
    "__init__.py",
    "graph/__init__.py",
    "graph/app.py",
    "graph/definitions.py",
    "schemas/__init__.py",
    "schemas/graph.py",
}


def test_corpus_backend_package_is_a_vertical_slice_with_graph_and_product_schemas():
    implementation_files = {
        path.relative_to(CORPUS_ROOT).as_posix()
        for path in CORPUS_ROOT.rglob("*.py")
        if "__pycache__" not in path.parts
    }

    assert implementation_files == ALLOWED_CORPUS_IMPLEMENTATION_FILES
    assert CORPUS_GRAPH_ROOT.exists()
    assert CORPUS_SCHEMA_ROOT.exists()
    assert not RETIRED_SERVICE_CORPUS_ROOT.exists()


def test_corpus_app_builder_is_the_only_runtime_wiring_module():
    app_source = (CORPUS_GRAPH_ROOT / "app.py").read_text(encoding="utf-8")

    assert "from backend.corpus.graph.definitions import" in app_source
    for retired_module in [
        "business_logic",
        "corpus_context",
        "corpus_handlers",
        "corpus_navgraph",
        "corpus_operation_requests",
        "corpus_operations",
        "corpus_routedeck_navigation",
        "corpus_routedeck_runtime",
        "corpus_surface_catalog",
        "corpus_surfaces",
        "corpus_turn_planning",
        "manifest",
    ]:
        assert f"backend.corpus.graph.{retired_module}" not in app_source


def test_corpus_definitions_and_business_logic_are_intentionally_separate():
    definitions_source = (CORPUS_GRAPH_ROOT / "definitions.py").read_text(encoding="utf-8")
    app_source = (CORPUS_GRAPH_ROOT / "app.py").read_text(encoding="utf-8")

    assert "class CorpusNodeIds" in definitions_source
    assert "class CorpusActionIds" in definitions_source
    assert "CORPUS_MANIFEST" in definitions_source
    assert "class CorpusSurfaceCatalog" in definitions_source

    for handler_name in [
        "handle_saas_agent_create",
        "handle_connection_activate",
        "handle_execution_plan",
        "handle_instructions_save",
        "handle_learning_approve",
    ]:
        assert f"async def {handler_name}" in app_source
        assert handler_name not in definitions_source


def test_corpus_package_owns_routedeck_runtime_and_app_graph_package_is_retired():
    assert CORPUS_ROOT.exists()
    assert not RETIRED_GRAPH_ROOT.exists()

    init_source = (CORPUS_ROOT / "__init__.py").read_text(encoding="utf-8")
    graph_init_source = (CORPUS_GRAPH_ROOT / "__init__.py").read_text(encoding="utf-8")
    app_source = (CORPUS_GRAPH_ROOT / "app.py").read_text(encoding="utf-8")

    assert "from .graph import" not in init_source
    assert "from .app import CorpusRouteDeckRuntime, corpus_route_deck_app, route_deck_runtime" in graph_init_source
    assert "route_deck_runtime = corpus_route_deck_app.compile()" in app_source
    assert "from .runtime import CorpusGraphRuntime, corpus_graph_runtime" not in init_source
    assert '"CorpusGraphRuntime"' not in init_source
    assert '"corpus_graph_runtime"' not in init_source


def test_corpus_package_uses_corpus_named_graph_schema_and_manifest_contracts():
    schema_source = (CORPUS_SCHEMA_ROOT / "graph.py").read_text(encoding="utf-8")
    manifest_source = (CORPUS_GRAPH_ROOT / "definitions.py").read_text(encoding="utf-8")
    init_source = (CORPUS_ROOT / "__init__.py").read_text(encoding="utf-8")
    legacy_builder_name = "build_" + "app_graph_manifest"
    legacy_validator_name = "validate_" + "app_graph_manifest"
    legacy_manifest_name = "APP_" + "GRAPH_MANIFEST"

    assert "class CorpusGraphState(" in schema_source
    assert "class CorpusGraphRequest(" in schema_source
    assert "class CorpusContextLens(" in schema_source
    assert "def build_corpus_manifest(" in manifest_source
    assert "def validate_corpus_manifest(" in manifest_source
    assert "CORPUS_MANIFEST" in manifest_source
    assert legacy_builder_name not in manifest_source
    assert legacy_validator_name not in manifest_source
    assert legacy_manifest_name not in manifest_source
    assert legacy_builder_name not in init_source


def test_corpus_route_deck_app_declares_product_extensions_in_one_builder():
    app_source = (CORPUS_GRAPH_ROOT / "app.py").read_text(encoding="utf-8")

    assert "RouteDeckApp(CorpusGraphState, runtime_base=CorpusRouteDeckRuntime" in app_source
    assert ".manifest(CORPUS_MANIFEST)" in app_source
    assert ".initial_node(CorpusNodeIds.HOME)" in app_source
    assert ".surfaces(CorpusSurfaceRegistry)" in app_source
    assert ".navigation(CorpusRouteDeckNavigation)" in app_source
    assert ".operation_policy(CorpusOperationPolicy)" in app_source
    assert ".operation_requests(CorpusOperationRequests)" in app_source
    assert ".route_actions(" in app_source
    assert "RouteDeckRouteActionIds(" in app_source
    assert ".operation_review_component(\"CorpusOperationReviewSurface\")" in app_source
    assert ".projector(" not in app_source
    assert "CorpusRouteDeckStateProjector" not in app_source


def test_legacy_corpus_graph_runtime_module_is_retired():
    assert not (CORPUS_GRAPH_ROOT / "runtime.py").exists()


def test_corpus_runtime_uses_explicit_action_dispatcher_not_reflection_handlers():
    runtime_source = (CORPUS_GRAPH_ROOT / "app.py").read_text(encoding="utf-8")

    assert "build_corpus_action_dispatcher" in runtime_source
    assert "self._action_dispatcher" in runtime_source
    assert "getattr(self, f\"_handle_" not in runtime_source


def test_corpus_business_handlers_live_in_single_business_logic_module_not_runtime():
    runtime_source = (CORPUS_GRAPH_ROOT / "app.py").read_text(encoding="utf-8")
    app_source = (CORPUS_GRAPH_ROOT / "app.py").read_text(encoding="utf-8")
    handlers_root = CORPUS_GRAPH_ROOT / "corpus_handlers"

    assert not handlers_root.exists()
    for handler_name in [
        "handle_saas_agent_create",
        "handle_connection_activate",
        "handle_execution_plan",
        "handle_deployment_save",
        "handle_instructions_save",
        "handle_memory_save",
        "handle_learning_approve",
    ]:
        assert f"async def {handler_name}" in app_source

    assert "build_corpus_action_dispatcher(" in runtime_source


def test_operation_request_plumbing_lives_in_app_builder_module_without_old_split_file():
    app_source = (CORPUS_GRAPH_ROOT / "app.py").read_text(encoding="utf-8")

    assert not (CORPUS_GRAPH_ROOT / "corpus_operation_requests.py").exists()
    assert ".operation_requests(CorpusOperationRequests)" in app_source
    assert "class CorpusOperationRequests(RouteDeckOperationRequestPolicy)" in app_source
    assert "RouteDeckRouteActionIds" in app_source
    assert "route_actions: RouteDeckRouteActionIds" in app_source
    for forbidden in [
        "def _validated_operation_payload",
        "def _validated_route_open_node_args",
        "def _validated_route_switch_surface_args",
        "def _sanitize_operation_args",
    ]:
        assert forbidden not in app_source


def test_corpus_navigation_configures_routedeck_controller_not_duplicate_navigation_logic():
    navigation_source = (CORPUS_GRAPH_ROOT / "app.py").read_text(encoding="utf-8")

    assert "RouteDeckGraphNavigationController" in navigation_source
    assert "class CorpusRouteDeckNavigation(RouteDeckGraphNavigationController)" in navigation_source
    assert "def extra_history_params" in navigation_source
    assert "def apply_extra_history_params" in navigation_source
    assert "NAV_PARAM_SAAS_AGENT_ID" in navigation_source

    for forbidden in [
        "def active_surface_ids",
        "def legal_target_node_ids_from_projection",
        "def resolved_surface_id",
        "def history_params_for_state",
        "def current_location",
        "def apply_location",
        "def push_navigation",
        "def move_back",
        "def move_forward",
        "def open_node",
        "def switch_surface",
    ]:
        assert forbidden not in navigation_source


def test_corpus_surface_registry_does_not_rewrap_routedeck_surface_mechanics():
    surface_source = (CORPUS_GRAPH_ROOT / "app.py").read_text(encoding="utf-8")

    assert "class CorpusSurfaceRegistry(RouteDeckSurfaceRegistry)" in surface_source
    assert "def active_surfaces(" in surface_source
    for forbidden in [
        "def active_surface(",
        "def default_surface_id(",
        "def surface_variant(",
        "def store_surface_intent(",
        "def review_surface(",
        "return self.operation_review_surface(",
    ]:
        assert forbidden not in surface_source


def test_corpus_projection_assembly_uses_routedeck_navigation_projection_helper():
    runtime_source = (CORPUS_GRAPH_ROOT / "app.py").read_text(encoding="utf-8")
    routedeck_projector_source = (
        Path(__file__).parents[2] / ".." / "routedeck" / "routedeck_core" / "projector.py"
    ).resolve().read_text(encoding="utf-8")

    assert "def project_state(" in routedeck_projector_source
    assert "navigation=self.navigation_for_state(state)" in routedeck_projector_source
    assert "self._route_deck_projector.project_state(" in runtime_source
    assert '"back_stack": [location.model_dump' not in runtime_source
    assert '"forward_stack": [location.model_dump' not in runtime_source


def test_corpus_projection_assembly_uses_routedeck_review_surface_helper():
    app_source = (CORPUS_GRAPH_ROOT / "app.py").read_text(encoding="utf-8")
    runtime_source = (CORPUS_GRAPH_ROOT / "app.py").read_text(encoding="utf-8")
    routedeck_projector_source = (
        Path(__file__).parents[2] / ".." / "routedeck" / "routedeck_core" / "projector.py"
    ).resolve().read_text(encoding="utf-8")
    surface_source = (CORPUS_GRAPH_ROOT / "app.py").read_text(encoding="utf-8")

    assert "def surfaces_with_review(" in routedeck_projector_source
    assert "review_surface_props=" in runtime_source
    assert ".operation_review_component(\"CorpusOperationReviewSurface\")" in app_source
    assert "def review_surface(" not in surface_source
    assert "return self.operation_review_surface(" not in surface_source


def test_corpus_projection_assembly_passes_context_lens_to_routedeck_projection():
    runtime_source = (CORPUS_GRAPH_ROOT / "app.py").read_text(encoding="utf-8")

    assert "context_lens=lens" in runtime_source
    assert 'component="CorpusContextLens"' not in runtime_source
    assert "props=lens.model_dump" not in runtime_source


def test_corpus_turn_planning_reads_context_lens_from_projection_not_surface_props():
    turn_planning_source = (CORPUS_GRAPH_ROOT / "app.py").read_text(encoding="utf-8")
    lens_helper_source = turn_planning_source.split("def _lens_props", 1)[1].split("def _coerce_mapping", 1)[0]

    assert "projection.context_lens" in lens_helper_source
    assert "projection.surfaces" not in lens_helper_source
    assert "CorpusContextLens" not in lens_helper_source


def test_corpus_has_no_product_owned_route_deck_projector():
    runtime_source = (CORPUS_GRAPH_ROOT / "app.py").read_text(encoding="utf-8")
    app_source = (CORPUS_GRAPH_ROOT / "app.py").read_text(encoding="utf-8")

    assert not (CORPUS_GRAPH_ROOT / "corpus_routedeck_state.py").exists()
    assert "CorpusRouteDeckStateProjector" not in runtime_source
    assert "CorpusRouteDeckStateProjector" not in app_source
    assert ".projector(" not in app_source
    assert "self._route_deck_projector.project_state(" in runtime_source


def test_corpus_routedeck_runtime_extends_route_deck_runtime_base_not_wrapper():
    runtime_source = (CORPUS_GRAPH_ROOT / "app.py").read_text(encoding="utf-8")

    assert "RouteDeckRuntimeBase" in runtime_source
    assert "class CorpusRouteDeckRuntime(RouteDeckRuntimeBase[" in runtime_source
    assert "def __init__(self, runtime: CorpusGraphRuntime)" not in runtime_source
    assert "self._runtime = runtime" not in runtime_source


def test_corpus_routedeck_runtime_does_not_delegate_projection_lifecycle_to_corpus_graph_runtime():
    runtime_source = (CORPUS_GRAPH_ROOT / "app.py").read_text(encoding="utf-8")

    for forbidden in [
        ".corpus_state(",
        ".route_deck_projection(",
        ".diagnostics_snapshot(",
    ]:
        assert forbidden not in runtime_source


def test_corpus_routedeck_runtime_does_not_delegate_dispatch_lifecycle_to_corpus_graph_runtime():
    runtime_source = (CORPUS_GRAPH_ROOT / "app.py").read_text(encoding="utf-8")

    assert "async def dispatch(" not in runtime_source
    assert ".corpus_action(" not in runtime_source


def test_corpus_routedeck_runtime_does_not_reach_through_corpus_graph_private_runtime():
    runtime_source = (CORPUS_GRAPH_ROOT / "app.py").read_text(encoding="utf-8")

    assert "self._corpus_graph._" not in runtime_source


def test_corpus_routedeck_runtime_does_not_wrap_legacy_corpus_graph_runtime():
    runtime_source = (CORPUS_GRAPH_ROOT / "app.py").read_text(encoding="utf-8")

    assert "CorpusGraphRuntime" not in runtime_source
    assert "self._corpus_graph" not in runtime_source


def test_corpus_app_builder_declares_extension_components_instead_of_runtime_redeclarations():
    app_source = (CORPUS_GRAPH_ROOT / "app.py").read_text(encoding="utf-8")
    runtime_source = (CORPUS_GRAPH_ROOT / "app.py").read_text(encoding="utf-8")

    assert ".surfaces(CorpusSurfaceRegistry)" in app_source
    assert ".navigation(CorpusRouteDeckNavigation)" in app_source
    assert ".operation_policy(CorpusOperationPolicy)" in app_source
    assert ".operation_requests(CorpusOperationRequests)" in app_source
    assert ".manifest(CORPUS_MANIFEST)" in app_source
    assert ".route_actions(" in app_source
    assert "self.build_state_projector(" in runtime_source
    assert ".projector(" not in app_source
    for forbidden in [
        "SurfaceRegistry = CorpusSurfaceRegistry",
        "NavigationController = CorpusRouteDeckNavigation",
        "OperationPolicy = CorpusOperationPolicy",
        "OperationRequestPolicy = CorpusOperationRequests",
        "manifest = CORPUS_MANIFEST",
        "route_action_ids = RouteDeckRouteActionIds(",
        "self._surface_registry = CorpusSurfaceRegistry(",
        "self._navigation = CorpusRouteDeckNavigation(",
        "self._operation_policy = CorpusOperationPolicy(",
        "self._operation_requests = CorpusOperationRequests(",
        "operation_policy=self._operation_policy",
        "surface_registry=self._surface_registry",
        "manifest = build_corpus_manifest()",
    ]:
        assert forbidden not in runtime_source
    assert "CorpusRouteDeckStateProjector(" not in runtime_source


def test_corpus_routedeck_runtime_uses_routedeck_route_action_helpers():
    runtime_source = (CORPUS_GRAPH_ROOT / "app.py").read_text(encoding="utf-8")

    assert "self.route_actions_for_state(state)" in runtime_source
    assert "self.is_route_action_id(action_id)" in runtime_source
    assert "def _route_actions(" not in runtime_source


def test_corpus_routedeck_runtime_uses_routedeck_surface_intent_and_presentation_state_helpers():
    runtime_source = (CORPUS_GRAPH_ROOT / "app.py").read_text(encoding="utf-8")

    assert "self.surface_navigation_id_from_intent(surface_intent)" in runtime_source
    assert "self.surface_variant_intent_from_intent(surface_intent)" in runtime_source
    assert "self.store_surface_intent_for_state(turn_state, surface_variant_intent, context)" in runtime_source
    assert "self.stored_presentation_state_for_state(state, context)" in runtime_source
    assert "def presentation_state_key(" in runtime_source
    for forbidden in [
        "_presentation_state_by_key",
        "def _store_surface_intent(",
        "def _surface_navigation_id(",
        "def _surface_variant_intent(",
    ]:
        assert forbidden not in runtime_source


def test_corpus_routedeck_runtime_leaves_surface_query_location_encoding_to_routedeck():
    runtime_source = (CORPUS_GRAPH_ROOT / "app.py").read_text(encoding="utf-8")

    assert "def base_location_for_state(" in runtime_source
    assert '"replace_path": self.location_for_state(state, context)' in runtime_source
    for forbidden in [
        "from urllib.parse import urlencode",
        "def location_for_state(",
        "def _path_for_state(",
        "urlencode({'surface_id': surface_id})",
        "self._navigation.resolved_surface_id(state)",
    ]:
        assert forbidden not in runtime_source


def test_corpus_routes_use_routedeck_runtime_not_legacy_corpus_graph_runtime():
    route_source = (BACKEND_ROOT / "routes" / "corpus_graph.py").read_text(encoding="utf-8")

    assert "corpus_graph_runtime" not in route_source
    assert "route_deck_runtime.request_from_location(" in route_source
    assert "route_deck_runtime.stream_corpus_turn(" in route_source


def test_corpus_routedeck_runtime_stream_turn_uses_inherited_dispatch_path():
    runtime_source = (CORPUS_GRAPH_ROOT / "app.py").read_text(encoding="utf-8")

    assert "async def stream_corpus_turn(" in runtime_source
    assert "await self.dispatch(" in runtime_source
    assert ".stream_corpus_turn(" not in runtime_source


def test_corpus_routedeck_runtime_uses_routedeck_dispatch_events_not_local_store_event_builder():
    runtime_source = (CORPUS_GRAPH_ROOT / "app.py").read_text(encoding="utf-8")

    assert "def _operation_completed_event(" not in runtime_source
    assert ".events[0].model_dump(mode=\"json\")" in runtime_source
