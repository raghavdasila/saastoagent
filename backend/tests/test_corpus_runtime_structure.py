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
    assert "def validated_payload" in request_source
    assert "def review_state_for_operation" in request_source
    for forbidden in [
        "def _validated_operation_payload",
        "def _validated_route_open_node_args",
        "def _validated_route_switch_surface_args",
        "def _sanitize_operation_args",
    ]:
        assert forbidden not in runtime_source
