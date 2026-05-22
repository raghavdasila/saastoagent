from __future__ import annotations

from backend.core.schemas import AppGraphContextLens, AppGraphState
from backend.services.app_graph.corpus_operations import CorpusOperationPolicy
from backend.services.app_graph.corpus_surfaces import CorpusSurfaceRegistry
from backend.services.app_graph.manifest import ACTION_SPECS, AppActionIds


def _action(action_id: str):
    return next(action for action in ACTION_SPECS if action.id == action_id)


def test_corpus_operation_policy_keeps_agent_list_surface_dispatchable():
    operation = CorpusOperationPolicy().operation_for_action(_action(AppActionIds.SAAS_AGENT_LIST))

    assert operation.id == "saas_agent.list"
    assert operation.invocation_kind == "surface"
    assert operation.can_dispatch_now is True
    assert operation.target_node == "saas_agent_select"


def test_corpus_operation_policy_keeps_agent_open_bound_only():
    operation = CorpusOperationPolicy().operation_for_action(_action(AppActionIds.SAAS_AGENT_OPEN))

    assert operation.id == "saas_agent.open"
    assert operation.invocation_kind == "entity_selector"
    assert operation.required_args == ["saas_agent_id"]
    assert operation.missing_args == ["saas_agent_id"]
    assert operation.can_dispatch_now is False


def test_corpus_surface_registry_maps_product_nodes_to_surfaces():
    registry = CorpusSurfaceRegistry()

    assert registry.active_surface_component_for_node("auth_sign_in") == "CorpusAuthSurface"
    assert registry.active_surface_component_for_node("saas_agent_select") == "SaaSAgentListSurface"
    assert registry.active_surface_component_for_node("connection_configure") == "ConnectionSetupSurface"


def test_corpus_surface_registry_builds_connection_surface_prompt():
    registry = CorpusSurfaceRegistry()
    operation = CorpusOperationPolicy().operation_for_action(_action(AppActionIds.CONNECTION_CONFIGURE))

    assert registry.deterministic_surface_prompt(operation).startswith("Connection setup is open.")


def test_corpus_surface_registry_builds_active_surface_with_lens_and_agents():
    registry = CorpusSurfaceRegistry()
    state = AppGraphState(node="saas_agent_select")
    lens = AppGraphContextLens(current_node="saas_agent_select", working_on="Select SaaS Agent")

    surface = registry.active_surface(state=state, lens=lens, saas_agents=[], context="saas_agent_select")

    assert surface is not None
    assert surface.name == "active"
    assert surface.component == "SaaSAgentListSurface"
    assert surface.props["lens"]["working_on"] == "Select SaaS Agent"
