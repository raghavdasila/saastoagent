from __future__ import annotations

from backend.core.schemas import CorpusContextLens, CorpusGraphState, CorpusSurface
from backend.services.corpus.corpus_operations import CorpusOperationPolicy
from backend.services.corpus.corpus_surfaces import CorpusSurfaceRegistry
from backend.services.corpus.manifest import ACTION_SPECS, CorpusActionIds


def _action(action_id: str):
    return next(action for action in ACTION_SPECS if action.id == action_id)


def test_corpus_operation_policy_keeps_agent_list_surface_dispatchable():
    operation = CorpusOperationPolicy().operation_for_action(_action(CorpusActionIds.SAAS_AGENT_LIST))

    assert operation.id == "saas_agent.list"
    assert operation.invocation_kind == "surface"
    assert operation.can_dispatch_now is True
    assert operation.target_node == "saas_agent_select"


def test_corpus_operation_policy_keeps_agent_open_bound_only():
    operation = CorpusOperationPolicy().operation_for_action(_action(CorpusActionIds.SAAS_AGENT_OPEN))

    assert operation.id == "saas_agent.open"
    assert operation.invocation_kind == "entity_selector"
    assert operation.required_args == ["saas_agent_id"]
    assert operation.missing_args == ["saas_agent_id"]
    assert operation.can_dispatch_now is False


def test_corpus_operation_policy_keeps_learning_open_directly_dispatchable():
    operation = CorpusOperationPolicy().operation_for_action(_action(CorpusActionIds.LEARNING_OPEN))

    assert operation.id == "learning.open"
    assert operation.invocation_kind == "direct"
    assert operation.execution_mode == "auto"
    assert operation.can_dispatch_now is True
    assert operation.target_node == "learning"


def test_corpus_operation_policy_keeps_learning_review_actions_review_mode():
    operation = CorpusOperationPolicy().operation_for_action(_action(CorpusActionIds.LEARNING_APPROVE))

    assert operation.id == "learning.approve"
    assert operation.execution_mode == "review"


def test_corpus_surface_registry_maps_product_nodes_to_surfaces():
    registry = CorpusSurfaceRegistry()

    assert registry.active_surface_component_for_node("auth_sign_in") == "CorpusAuthSurface"
    assert registry.active_surface_component_for_node("saas_agent_select") == "SaaSAgentListSurface"
    assert registry.active_surface_component_for_node("connection_configure") == "ConnectionSetupSurface"


def test_corpus_surface_registry_configures_review_surface_prefix_for_routedeck():
    registry = CorpusSurfaceRegistry()
    state = CorpusGraphState(
        node="connection_configure",
        pending_operation_id=CorpusActionIds.CONNECTION_CONFIGURE,
    )

    assert (
        registry.default_surface_id_for(state.node, pending_operation_id=state.pending_operation_id)
        == "operation_review.navigate.connection_configure"
    )


def test_corpus_surface_registry_builds_active_surface_with_lens_and_agents():
    registry = CorpusSurfaceRegistry()
    state = CorpusGraphState(node="saas_agent_select")
    lens = CorpusContextLens(current_node="saas_agent_select", working_on="Select SaaS Agent")

    surfaces = registry.active_surfaces(state=state, lens=lens, saas_agents=[], context="saas_agent_select")

    surface = surfaces[0]
    assert isinstance(surface, CorpusSurface)
    assert surface.name == "active"
    assert surface.component == "SaaSAgentListSurface"
    assert surface.props["lens"]["working_on"] == "Select SaaS Agent"


def test_learning_projection_exposes_peer_surfaces_and_child_review_nodes():
    registry = CorpusSurfaceRegistry()
    state = CorpusGraphState(node="learning")
    lens = CorpusContextLens(current_node="learning", working_on="Learning")

    surfaces = registry.active_surfaces(state=state, lens=lens, saas_agents=[], context="learning")

    surface_ids = {surface.surface_id for surface in surfaces}
    assert "learning.policy_gaps" in surface_ids
    assert "learning.failed_executions" in surface_ids
    assert "learning.active_policies" in surface_ids
    assert all(surface.surface_kind == "peer" for surface in surfaces)


def test_learning_policy_candidate_detail_surface_uses_route_params():
    registry = CorpusSurfaceRegistry()
    state = CorpusGraphState(
        node="learning.policy_candidate",
        route_params={"candidate_id": "candidate_123"},
    )
    lens = CorpusContextLens(current_node="learning.policy_candidate", working_on="Policy Candidate")

    surfaces = registry.active_surfaces(state=state, lens=lens, saas_agents=[], context="learning.policy_candidate")

    assert len(surfaces) == 1
    assert surfaces[0].surface_id == "learning.policy_candidate.review"
    assert surfaces[0].surface_kind == "detail"
    assert surfaces[0].props["candidate_id"] == "candidate_123"
