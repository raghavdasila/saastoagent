from __future__ import annotations

from collections.abc import Callable, Mapping
from dataclasses import dataclass, field
from typing import Any

from backend.core.schemas import AppGraphContextLens, AppGraphState, SaaSAgentRead
from backend.services.app_graph.manifest import AppActionIds, AppNodeIds

SurfacePropsFactory = Callable[[AppGraphState, AppGraphContextLens, list[SaaSAgentRead]], dict[str, Any]]


@dataclass(frozen=True)
class CorpusSurfaceSpec:
    component: str
    variant: str
    surface_id: str | None = None
    name: str = "active"
    role: str = "active"
    slot: str | None = "active"
    surface_kind: str = "embedded"
    label: str | None = None
    props: Mapping[str, Any] = field(default_factory=dict)
    props_factory: SurfacePropsFactory | None = None
    lifecycle: str = "ephemeral"

    def resolve_props(
        self,
        *,
        state: AppGraphState,
        lens: AppGraphContextLens,
        saas_agents: list[SaaSAgentRead],
    ) -> dict[str, Any]:
        resolved = dict(self.props)
        if self.props_factory:
            resolved.update(self.props_factory(state, lens, saas_agents))
        return resolved


class CorpusSurfaceCatalog:
    """Product-owned Corpus surface descriptors and node mappings."""

    operation_review_surface_prefix = "operation_review."
    planning_entity_limit = 25

    active_components_by_node = {
        AppNodeIds.AUTH_SIGN_IN: "CorpusAuthSurface",
        AppNodeIds.AUTH_REGISTER: "CorpusAuthSurface",
        AppNodeIds.SAAS_AGENT_SELECT: "SaaSAgentListSurface",
        AppNodeIds.INSTRUCTIONS: "InstructionsSurface",
        AppNodeIds.CONNECTION_CONFIGURE: "ConnectionSetupSurface",
        AppNodeIds.SCHEMA_PREVIEW: "SchemaPreviewSurface",
        AppNodeIds.CATALOG: "CatalogSurface",
        AppNodeIds.CATALOG_ACTIVATION: "CatalogSurface",
        AppNodeIds.ENTITIES: "EntitiesSurface",
        AppNodeIds.ACTIONS: "ActionsSurface",
        AppNodeIds.EXECUTION_PLANNING: "ExecutionSurface",
        AppNodeIds.NEEDS_INPUT: "ExecutionSurface",
        AppNodeIds.APPROVAL_REQUIRED: "ExecutionSurface",
        AppNodeIds.RESULT_REVIEW: "ExecutionSurface",
        AppNodeIds.KNOWLEDGE: "KnowledgeSurface",
        AppNodeIds.MEMORY: "MemorySurface",
        AppNodeIds.LEARNING: "LearningSurface",
        AppNodeIds.LEARNING_POLICY_CANDIDATE: "LearningPolicyCandidateSurface",
        AppNodeIds.LEARNING_EXECUTION_TRACE: "LearningExecutionTraceSurface",
        AppNodeIds.LEARNING_ACTIVE_POLICY: "LearningPolicyCandidateSurface",
        AppNodeIds.QA: "QASurface",
        AppNodeIds.RECOVERY: "RecoverySurface",
    }

    default_surface_ids_by_node = {
        AppNodeIds.LEARNING: "learning.policy_gaps",
        AppNodeIds.LEARNING_POLICY_CANDIDATE: "learning.policy_candidate.review",
        AppNodeIds.LEARNING_EXECUTION_TRACE: "learning.execution_trace.review",
        AppNodeIds.LEARNING_ACTIVE_POLICY: "learning.active_policy.review",
    }

    surface_hosted_operations_by_node = {
        AppNodeIds.AGENT_HOME: {AppActionIds.DEPLOYMENT_SAVE},
        AppNodeIds.INSTRUCTIONS: {AppActionIds.INSTRUCTIONS_SAVE},
        AppNodeIds.CONNECTION_CONFIGURE: {AppActionIds.CONNECTION_PREVIEW, AppActionIds.CONNECTION_ACTIVATE},
        AppNodeIds.SCHEMA_PREVIEW: {AppActionIds.CONNECTION_ACTIVATE},
        AppNodeIds.EXECUTION_PLANNING: {AppActionIds.EXECUTION_PLAN},
        AppNodeIds.NEEDS_INPUT: {AppActionIds.EXECUTION_INPUT},
        AppNodeIds.APPROVAL_REQUIRED: {AppActionIds.APPROVAL_APPROVE, AppActionIds.APPROVAL_REJECT},
        AppNodeIds.KNOWLEDGE: {AppActionIds.KNOWLEDGE_GENERATE},
        AppNodeIds.MEMORY: {AppActionIds.MEMORY_SAVE},
        AppNodeIds.LEARNING: {AppActionIds.LEARNING_APPROVE, AppActionIds.LEARNING_REJECT},
        AppNodeIds.LEARNING_POLICY_CANDIDATE: {AppActionIds.LEARNING_APPROVE, AppActionIds.LEARNING_REJECT},
        AppNodeIds.QA: {AppActionIds.QA_RUN},
    }

    def __init__(self) -> None:
        self._active_spec_builders = {
            AppNodeIds.LEARNING: self._learning_specs,
            AppNodeIds.LEARNING_POLICY_CANDIDATE: self._policy_candidate_specs,
            AppNodeIds.LEARNING_EXECUTION_TRACE: self._execution_trace_specs,
            AppNodeIds.LEARNING_ACTIVE_POLICY: self._active_policy_specs,
            AppNodeIds.SAAS_AGENT_SELECT: self._saas_agent_select_specs,
        }

    def frame_spec(
        self,
        *,
        state: AppGraphState,
        lens: AppGraphContextLens,
        saas_agents: list[SaaSAgentRead],
        context: str,
    ) -> CorpusSurfaceSpec:
        if context == "lounge":
            return CorpusSurfaceSpec(
                name="main",
                component="CorpusLoungeSurface",
                variant="lounge",
                role="frame",
                slot=None,
                props={
                    "title": "Explore SaaStoAgent",
                    "subtitle": "Ask about the platform and let Corpus guide the next step when you are ready.",
                },
                lifecycle="stable",
            )

        if state.node == AppNodeIds.HOME:
            return CorpusSurfaceSpec(
                name="main",
                component="CorpusDashboardSurface",
                variant="dashboard",
                role="frame",
                slot=None,
                props={
                    "title": "Dashboard",
                    "saas_agents": [agent.model_dump(mode="json") for agent in saas_agents[:2]],
                    "agent_count": len(saas_agents),
                    "working_on": lens.working_on,
                },
                lifecycle="stable",
            )

        return CorpusSurfaceSpec(
            name="main",
            component="CorpusNodeFrame",
            variant=state.node,
            role="frame",
            slot=None,
            props={
                "title": lens.working_on,
                "node_id": state.node,
                "selected_saas_agent_name": lens.selected_saas_agent_name,
                "working_on": lens.working_on,
            },
            lifecycle="stable",
        )

    def active_specs(
        self,
        *,
        state: AppGraphState,
        lens: AppGraphContextLens,
        saas_agents: list[SaaSAgentRead],
        context: str,
    ) -> list[CorpusSurfaceSpec]:
        builder = self._active_spec_builders.get(state.node)
        if builder:
            return builder(state, lens, saas_agents)
        return self._default_active_specs(state, lens, saas_agents)

    def review_props(
        self,
        *,
        lens: AppGraphContextLens,
        saas_agents: list[SaaSAgentRead],
        graph_context: Mapping[str, Any],
    ) -> dict[str, Any]:
        return {
            "saas_agents": [agent.model_dump(mode="json") for agent in saas_agents],
            "lens": lens.model_dump(mode="json"),
            **graph_context,
        }

    def router_index_from_lens(self, lens: AppGraphContextLens) -> dict[str, Any] | None:
        if not lens.router_index_status:
            return None
        return {
            "status": lens.router_index_status,
            "router_version": lens.router_version,
            "document_count": lens.router_documents_count,
            "endpoint_count": lens.router_endpoint_count,
        }

    def _learning_specs(
        self,
        state: AppGraphState,
        lens: AppGraphContextLens,
        saas_agents: list[SaaSAgentRead],
    ) -> list[CorpusSurfaceSpec]:
        return [
            CorpusSurfaceSpec(
                component="LearningSurface",
                surface_id="learning.policy_gaps",
                variant="policy_gaps",
                surface_kind="peer",
                label="Policy gaps",
                props={
                    "filter": "policy_gaps",
                    "planning_description": "Review policy proposals that need an owner decision.",
                },
            ),
            CorpusSurfaceSpec(
                component="LearningSurface",
                surface_id="learning.failed_executions",
                variant="failed_executions",
                surface_kind="peer",
                label="Failed executions",
                props={
                    "filter": "failed_executions",
                    "planning_description": "Review failed execution patterns and the learning candidates generated from them.",
                },
            ),
            CorpusSurfaceSpec(
                component="LearningSurface",
                surface_id="learning.active_policies",
                variant="active_policies",
                surface_kind="peer",
                label="Active policies",
                props={
                    "filter": "active_policies",
                    "planning_description": "Inspect the approved policies that are currently active for this agent.",
                },
            ),
            CorpusSurfaceSpec(
                component="LearningSurface",
                surface_id="learning.rejected",
                variant="rejected",
                surface_kind="peer",
                label="Rejected",
                props={
                    "filter": "rejected",
                    "planning_description": "Review learning items that were previously rejected.",
                },
            ),
        ]

    def _policy_candidate_specs(
        self,
        state: AppGraphState,
        lens: AppGraphContextLens,
        saas_agents: list[SaaSAgentRead],
    ) -> list[CorpusSurfaceSpec]:
        return [
            CorpusSurfaceSpec(
                component="LearningPolicyCandidateSurface",
                surface_id="learning.policy_candidate.review",
                variant="policy_candidate_review",
                surface_kind="detail",
                label="Policy candidate",
                props={"candidate_id": state.route_params.get("candidate_id")},
            )
        ]

    def _execution_trace_specs(
        self,
        state: AppGraphState,
        lens: AppGraphContextLens,
        saas_agents: list[SaaSAgentRead],
    ) -> list[CorpusSurfaceSpec]:
        return [
            CorpusSurfaceSpec(
                component="LearningExecutionTraceSurface",
                surface_id="learning.execution_trace.review",
                variant="execution_trace_review",
                surface_kind="detail",
                label="Execution trace",
                props={"trace_id": state.route_params.get("trace_id")},
            )
        ]

    def _active_policy_specs(
        self,
        state: AppGraphState,
        lens: AppGraphContextLens,
        saas_agents: list[SaaSAgentRead],
    ) -> list[CorpusSurfaceSpec]:
        return [
            CorpusSurfaceSpec(
                component="LearningPolicyCandidateSurface",
                surface_id="learning.active_policy.review",
                variant="active_policy_review",
                surface_kind="detail",
                label="Active policy",
                props={"candidate_id": state.route_params.get("candidate_id"), "readonly": True},
            )
        ]

    def _saas_agent_select_specs(
        self,
        state: AppGraphState,
        lens: AppGraphContextLens,
        saas_agents: list[SaaSAgentRead],
    ) -> list[CorpusSurfaceSpec]:
        return [
            CorpusSurfaceSpec(
                component="SaaSAgentListSurface",
                surface_id="saas_agent_select.active",
                variant="saas_agent_select",
                label=lens.working_on,
                props={
                    "planning_description": "Shows the selectable SaaS Agents currently visible in the list.",
                    "planning_entities": self.saas_agent_planning_entities(saas_agents),
                    "planning_entity_count": len(saas_agents),
                    "planning_entities_truncated": len(saas_agents) > self.planning_entity_limit,
                },
            )
        ]

    def _default_active_specs(
        self,
        state: AppGraphState,
        lens: AppGraphContextLens,
        saas_agents: list[SaaSAgentRead],
    ) -> list[CorpusSurfaceSpec]:
        component = self.active_components_by_node.get(state.node)
        if component is None:
            return []
        return [
            CorpusSurfaceSpec(
                component=component,
                surface_id=f"{state.node}.active",
                variant=state.node,
                label=lens.working_on,
            )
        ]

    def saas_agent_planning_entities(self, saas_agents: list[SaaSAgentRead]) -> list[dict[str, Any]]:
        return [
            {
                "entity_type": "saas_agent",
                "id": str(agent.id),
                "label": agent.name,
                "slug": agent.slug,
                "description": agent.slug,
                "operation_id": AppActionIds.SAAS_AGENT_OPEN,
                "args": {"saas_agent_id": str(agent.id)},
            }
            for agent in saas_agents[: self.planning_entity_limit]
        ]
