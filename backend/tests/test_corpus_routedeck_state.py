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


def test_corpus_operation_policy_keeps_learning_open_directly_dispatchable():
    operation = CorpusOperationPolicy().operation_for_action(_action(AppActionIds.LEARNING_OPEN))

    assert operation.id == "learning.open"
    assert operation.invocation_kind == "direct"
    assert operation.execution_mode == "auto"
    assert operation.can_dispatch_now is True
    assert operation.target_node == "learning"


def test_corpus_operation_policy_keeps_learning_review_actions_review_mode():
    operation = CorpusOperationPolicy().operation_for_action(_action(AppActionIds.LEARNING_APPROVE))

    assert operation.id == "learning.approve"
    assert operation.execution_mode == "review"


def test_corpus_surface_registry_maps_product_nodes_to_surfaces():
    registry = CorpusSurfaceRegistry()

    assert registry.active_surface_component_for_node("auth_sign_in") == "CorpusAuthSurface"
    assert registry.active_surface_component_for_node("saas_agent_select") == "SaaSAgentListSurface"
    assert registry.active_surface_component_for_node("connection_configure") == "ConnectionSetupSurface"


def test_corpus_surface_registry_prefers_review_surface_for_pending_operation():
    registry = CorpusSurfaceRegistry()
    state = AppGraphState(
        node="connection_configure",
        pending_operation_id=AppActionIds.CONNECTION_CONFIGURE,
    )

    assert registry.default_surface_id(state) == "operation_review.navigate.connection_configure"


def test_corpus_surface_registry_builds_active_surface_with_lens_and_agents():
    registry = CorpusSurfaceRegistry()
    state = AppGraphState(node="saas_agent_select")
    lens = AppGraphContextLens(current_node="saas_agent_select", working_on="Select SaaS Agent")

    surface = registry.active_surface(state=state, lens=lens, saas_agents=[], context="saas_agent_select")

    assert surface is not None
    assert surface.name == "active"
    assert surface.component == "SaaSAgentListSurface"
    assert surface.props["lens"]["working_on"] == "Select SaaS Agent"


def test_learning_projection_exposes_peer_surfaces_and_child_review_nodes():
    registry = CorpusSurfaceRegistry()
    state = AppGraphState(node="learning")
    lens = AppGraphContextLens(current_node="learning", working_on="Learning")

    surfaces = registry.active_surfaces(state=state, lens=lens, saas_agents=[], context="learning")

    surface_ids = {surface.surface_id for surface in surfaces}
    assert "learning.policy_gaps" in surface_ids
    assert "learning.failed_executions" in surface_ids
    assert "learning.active_policies" in surface_ids
    assert all(surface.surface_kind == "peer" for surface in surfaces)


def test_learning_policy_candidate_detail_surface_uses_route_params():
    registry = CorpusSurfaceRegistry()
    state = AppGraphState(
        node="learning.policy_candidate",
        route_params={"candidate_id": "candidate_123"},
    )
    lens = AppGraphContextLens(current_node="learning.policy_candidate", working_on="Policy Candidate")

    surfaces = registry.active_surfaces(state=state, lens=lens, saas_agents=[], context="learning.policy_candidate")

    assert len(surfaces) == 1
    assert surfaces[0].surface_id == "learning.policy_candidate.review"
    assert surfaces[0].surface_kind == "detail"
    assert surfaces[0].props["candidate_id"] == "candidate_123"
