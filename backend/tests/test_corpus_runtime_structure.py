from __future__ import annotations

from pathlib import Path


BACKEND_ROOT = Path(__file__).parents[1]
APP_GRAPH_ROOT = BACKEND_ROOT / "services" / "app_graph"


def test_corpus_runtime_uses_explicit_action_dispatcher_not_reflection_handlers():
    runtime_source = (APP_GRAPH_ROOT / "runtime.py").read_text(encoding="utf-8")

    assert "RouteDeckActionDispatcher" in runtime_source
    assert "build_corpus_action_dispatcher" in runtime_source
    assert "getattr(self, f\"_handle_" not in runtime_source


def test_corpus_business_handlers_live_in_domain_modules_not_runtime():
    runtime_source = (APP_GRAPH_ROOT / "runtime.py").read_text(encoding="utf-8")
    handlers_root = APP_GRAPH_ROOT / "corpus_handlers"

    assert handlers_root.exists()
    for module_name in [
        "agent.py",
        "connection.py",
        "execution.py",
        "content.py",
        "learning.py",
        "navigation.py",
        "registry.py",
    ]:
        assert (handlers_root / module_name).exists()

    forbidden_runtime_handlers = [
        "_handle_saas_agent_create",
        "_handle_connection_activate",
        "_handle_execution_plan",
        "_handle_deployment_save",
        "_handle_instructions_save",
        "_handle_memory_save",
        "_handle_learning_approve",
    ]
    for handler_name in forbidden_runtime_handlers:
        assert handler_name not in runtime_source


def test_operation_request_plumbing_lives_outside_runtime():
    runtime_source = (APP_GRAPH_ROOT / "runtime.py").read_text(encoding="utf-8")
    request_source = (APP_GRAPH_ROOT / "corpus_operation_requests.py").read_text(encoding="utf-8")

    assert "CorpusOperationRequests" in runtime_source
    assert "RouteDeckOperationRequestPolicy" in request_source
    assert "RouteDeckRouteActionIds" in request_source
    for forbidden in [
        "def _validated_operation_payload",
        "def _validated_route_open_node_args",
        "def _validated_route_switch_surface_args",
        "def _sanitize_operation_args",
    ]:
        assert forbidden not in runtime_source
        assert forbidden not in request_source


def test_corpus_navigation_configures_routedeck_controller_not_duplicate_navigation_logic():
    navigation_source = (APP_GRAPH_ROOT / "corpus_routedeck_navigation.py").read_text(encoding="utf-8")

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
