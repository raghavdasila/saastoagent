from __future__ import annotations

from collections.abc import Callable, Mapping
from dataclasses import dataclass, field
from typing import Any

from backend.core.schemas import CorpusContextLens, CorpusGraphState, SaaSAgentRead
from backend.services.corpus.manifest import CorpusActionIds, CorpusNodeIds

SurfacePropsFactory = Callable[[CorpusGraphState, CorpusContextLens, list[SaaSAgentRead]], dict[str, Any]]


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
        state: CorpusGraphState,
        lens: CorpusContextLens,
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
        CorpusNodeIds.AUTH_SIGN_IN: "CorpusAuthSurface",
        CorpusNodeIds.AUTH_REGISTER: "CorpusAuthSurface",
        CorpusNodeIds.SAAS_AGENT_SELECT: "SaaSAgentListSurface",
        CorpusNodeIds.INSTRUCTIONS: "InstructionsSurface",
        CorpusNodeIds.CONNECTION_CONFIGURE: "ConnectionSetupSurface",
        CorpusNodeIds.SCHEMA_PREVIEW: "SchemaPreviewSurface",
        CorpusNodeIds.CATALOG: "CatalogSurface",
        CorpusNodeIds.CATALOG_ACTIVATION: "CatalogSurface",
        CorpusNodeIds.ENTITIES: "EntitiesSurface",
        CorpusNodeIds.ACTIONS: "ActionsSurface",
        CorpusNodeIds.EXECUTION_PLANNING: "ExecutionSurface",
        CorpusNodeIds.NEEDS_INPUT: "ExecutionSurface",
        CorpusNodeIds.APPROVAL_REQUIRED: "ExecutionSurface",
        CorpusNodeIds.RESULT_REVIEW: "ExecutionSurface",
        CorpusNodeIds.KNOWLEDGE: "KnowledgeSurface",
        CorpusNodeIds.MEMORY: "MemorySurface",
        CorpusNodeIds.LEARNING: "LearningSurface",
        CorpusNodeIds.LEARNING_POLICY_CANDIDATE: "LearningPolicyCandidateSurface",
        CorpusNodeIds.LEARNING_EXECUTION_TRACE: "LearningExecutionTraceSurface",
        CorpusNodeIds.LEARNING_ACTIVE_POLICY: "LearningPolicyCandidateSurface",
        CorpusNodeIds.QA: "QASurface",
        CorpusNodeIds.RECOVERY: "RecoverySurface",
    }

    default_surface_ids_by_node = {
        CorpusNodeIds.LEARNING: "learning.policy_gaps",
        CorpusNodeIds.LEARNING_POLICY_CANDIDATE: "learning.policy_candidate.review",
        CorpusNodeIds.LEARNING_EXECUTION_TRACE: "learning.execution_trace.review",
        CorpusNodeIds.LEARNING_ACTIVE_POLICY: "learning.active_policy.review",
    }

    surface_hosted_operations_by_node = {
        CorpusNodeIds.AGENT_HOME: {CorpusActionIds.DEPLOYMENT_SAVE},
        CorpusNodeIds.INSTRUCTIONS: {CorpusActionIds.INSTRUCTIONS_SAVE},
        CorpusNodeIds.CONNECTION_CONFIGURE: {CorpusActionIds.CONNECTION_PREVIEW, CorpusActionIds.CONNECTION_ACTIVATE},
        CorpusNodeIds.SCHEMA_PREVIEW: {CorpusActionIds.CONNECTION_ACTIVATE},
        CorpusNodeIds.EXECUTION_PLANNING: {CorpusActionIds.EXECUTION_PLAN},
        CorpusNodeIds.NEEDS_INPUT: {CorpusActionIds.EXECUTION_INPUT},
        CorpusNodeIds.APPROVAL_REQUIRED: {CorpusActionIds.APPROVAL_APPROVE, CorpusActionIds.APPROVAL_REJECT},
        CorpusNodeIds.KNOWLEDGE: {CorpusActionIds.KNOWLEDGE_GENERATE},
        CorpusNodeIds.MEMORY: {CorpusActionIds.MEMORY_SAVE},
        CorpusNodeIds.LEARNING: {CorpusActionIds.LEARNING_APPROVE, CorpusActionIds.LEARNING_REJECT},
        CorpusNodeIds.LEARNING_POLICY_CANDIDATE: {CorpusActionIds.LEARNING_APPROVE, CorpusActionIds.LEARNING_REJECT},
        CorpusNodeIds.QA: {CorpusActionIds.QA_RUN},
    }

    def __init__(self) -> None:
        self._active_spec_builders = {
            CorpusNodeIds.LEARNING: self._learning_specs,
            CorpusNodeIds.LEARNING_POLICY_CANDIDATE: self._policy_candidate_specs,
            CorpusNodeIds.LEARNING_EXECUTION_TRACE: self._execution_trace_specs,
            CorpusNodeIds.LEARNING_ACTIVE_POLICY: self._active_policy_specs,
            CorpusNodeIds.SAAS_AGENT_SELECT: self._saas_agent_select_specs,
        }

    def frame_spec(
        self,
        *,
        state: CorpusGraphState,
        lens: CorpusContextLens,
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

        if state.node == CorpusNodeIds.HOME:
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
        state: CorpusGraphState,
        lens: CorpusContextLens,
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
        lens: CorpusContextLens,
        saas_agents: list[SaaSAgentRead],
        graph_context: Mapping[str, Any],
    ) -> dict[str, Any]:
        return {
            "saas_agents": [agent.model_dump(mode="json") for agent in saas_agents],
            "lens": lens.model_dump(mode="json"),
            **graph_context,
        }

    def router_index_from_lens(self, lens: CorpusContextLens) -> dict[str, Any] | None:
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
        state: CorpusGraphState,
        lens: CorpusContextLens,
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
        state: CorpusGraphState,
        lens: CorpusContextLens,
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
        state: CorpusGraphState,
        lens: CorpusContextLens,
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
        state: CorpusGraphState,
        lens: CorpusContextLens,
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
        state: CorpusGraphState,
        lens: CorpusContextLens,
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
        state: CorpusGraphState,
        lens: CorpusContextLens,
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
                "operation_id": CorpusActionIds.SAAS_AGENT_OPEN,
                "args": {"saas_agent_id": str(agent.id)},
            }
            for agent in saas_agents[: self.planning_entity_limit]
        ]
