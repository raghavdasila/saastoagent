from __future__ import annotations

from typing import Any

from routedeck_core import RouteDeckSurface

from backend.core.schemas import AppGraphContextLens, AppGraphState, SaaSAgentRead
from backend.services.app_graph.manifest import AppActionIds, AppNodeIds


class CorpusSurfaceRegistry:
    """Owns SaaStoAgent surface names, variants, and review-surface mapping."""

    _OPERATION_REVIEW_SURFACE_PREFIX = "operation_review."
    _PLANNING_ENTITY_LIMIT = 25
    _SURFACE_HOSTED_OPERATIONS_BY_NODE = {
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

    def frame_surface(
        self,
        *,
        state: AppGraphState,
        lens: AppGraphContextLens,
        saas_agents: list[SaaSAgentRead],
        context: str,
        presentation_state: dict[str, Any],
        node_by_id: dict[str, Any],
    ) -> RouteDeckSurface:
        if context == "lounge":
            return RouteDeckSurface(
                name="main",
                component="CorpusLoungeSurface",
                variant=self.surface_variant(state, presentation_state, "main", "lounge", node_by_id),
                role="frame",
                props={
                    "title": "Explore SaaStoAgent",
                    "subtitle": "Ask about the platform and let Corpus guide the next step when you are ready.",
                },
                lifecycle="stable",
            )
        if state.node == AppNodeIds.HOME:
            return RouteDeckSurface(
                name="main",
                component="CorpusDashboardSurface",
                variant=self.surface_variant(state, presentation_state, "main", "dashboard", node_by_id),
                role="frame",
                props={
                    "title": "Dashboard",
                    "saas_agents": [agent.model_dump(mode="json") for agent in saas_agents[:2]],
                    "agent_count": len(saas_agents),
                    "working_on": lens.working_on,
                },
                lifecycle="stable",
            )
        return RouteDeckSurface(
            name="main",
            component="CorpusNodeFrame",
            variant=self.surface_variant(state, presentation_state, "main", state.node, node_by_id),
            role="frame",
            props={
                "title": lens.working_on,
                "node_id": state.node,
                "selected_saas_agent_name": lens.selected_saas_agent_name,
                "working_on": lens.working_on,
            },
            lifecycle="stable",
        )

    def active_surface(
        self,
        *,
        state: AppGraphState,
        lens: AppGraphContextLens,
        saas_agents: list[SaaSAgentRead],
        context: str,
    ) -> RouteDeckSurface | None:
        surfaces = self.active_surfaces(state=state, lens=lens, saas_agents=saas_agents, context=context)
        return surfaces[0] if surfaces else None

    def active_surfaces(
        self,
        *,
        state: AppGraphState,
        lens: AppGraphContextLens,
        saas_agents: list[SaaSAgentRead],
        context: str,
    ) -> list[RouteDeckSurface]:
        review_surface = self.review_surface(
            state=state,
            lens=lens,
            saas_agents=saas_agents,
        )
        surfaces: list[RouteDeckSurface]
        if state.node == AppNodeIds.LEARNING:
            surfaces = [
                self._surface(
                    state=state,
                    lens=lens,
                    saas_agents=saas_agents,
                    component="LearningSurface",
                    surface_id="learning.policy_gaps",
                    variant="policy_gaps",
                    kind="peer",
                    label="Policy gaps",
                    props={
                        "filter": "policy_gaps",
                        "planning_description": "Review policy proposals that need an owner decision.",
                    },
                ),
                self._surface(
                    state=state,
                    lens=lens,
                    saas_agents=saas_agents,
                    component="LearningSurface",
                    surface_id="learning.failed_executions",
                    variant="failed_executions",
                    kind="peer",
                    label="Failed executions",
                    props={
                        "filter": "failed_executions",
                        "planning_description": "Review failed execution patterns and the learning candidates generated from them.",
                    },
                ),
                self._surface(
                    state=state,
                    lens=lens,
                    saas_agents=saas_agents,
                    component="LearningSurface",
                    surface_id="learning.active_policies",
                    variant="active_policies",
                    kind="peer",
                    label="Active policies",
                    props={
                        "filter": "active_policies",
                        "planning_description": "Inspect the approved policies that are currently active for this agent.",
                    },
                ),
                self._surface(
                    state=state,
                    lens=lens,
                    saas_agents=saas_agents,
                    component="LearningSurface",
                    surface_id="learning.rejected",
                    variant="rejected",
                    kind="peer",
                    label="Rejected",
                    props={
                        "filter": "rejected",
                        "planning_description": "Review learning items that were previously rejected.",
                    },
                ),
            ]
        elif state.node == AppNodeIds.LEARNING_POLICY_CANDIDATE:
            surfaces = [
                self._surface(
                    state=state,
                    lens=lens,
                    saas_agents=saas_agents,
                    component="LearningPolicyCandidateSurface",
                    surface_id="learning.policy_candidate.review",
                    variant="policy_candidate_review",
                    kind="detail",
                    label="Policy candidate",
                    props={"candidate_id": state.route_params.get("candidate_id")},
                )
            ]
        elif state.node == AppNodeIds.LEARNING_EXECUTION_TRACE:
            surfaces = [
                self._surface(
                    state=state,
                    lens=lens,
                    saas_agents=saas_agents,
                    component="LearningExecutionTraceSurface",
                    surface_id="learning.execution_trace.review",
                    variant="execution_trace_review",
                    kind="detail",
                    label="Execution trace",
                    props={"trace_id": state.route_params.get("trace_id")},
                )
            ]
        elif state.node == AppNodeIds.LEARNING_ACTIVE_POLICY:
            surfaces = [
                self._surface(
                    state=state,
                    lens=lens,
                    saas_agents=saas_agents,
                    component="LearningPolicyCandidateSurface",
                    surface_id="learning.active_policy.review",
                    variant="active_policy_review",
                    kind="detail",
                    label="Active policy",
                    props={"candidate_id": state.route_params.get("candidate_id"), "readonly": True},
                )
            ]
        elif state.node == AppNodeIds.SAAS_AGENT_SELECT:
            surfaces = [
                self._surface(
                    state=state,
                    lens=lens,
                    saas_agents=saas_agents,
                    component="SaaSAgentListSurface",
                    surface_id="saas_agent_select.active",
                    variant="saas_agent_select",
                    kind="embedded",
                    label=lens.working_on,
                    props={
                        "planning_description": "Shows the selectable SaaS Agents currently visible in the list.",
                        "planning_entities": self._saas_agent_planning_entities(saas_agents),
                        "planning_entity_count": len(saas_agents),
                        "planning_entities_truncated": len(saas_agents) > self._PLANNING_ENTITY_LIMIT,
                    },
                )
            ]
        else:
            component = self.active_surface_component_for_node(state.node)
            if component is None:
                surfaces = []
            else:
                surfaces = [self._surface(
                    state=state,
                    lens=lens,
                    saas_agents=saas_agents,
                    component=component,
                    surface_id=f"{state.node}.active",
                    variant=state.node,
                    kind="embedded",
                    label=lens.working_on,
                )]
        return [review_surface, *surfaces] if review_surface else surfaces

    def _surface(
        self,
        *,
        state: AppGraphState,
        lens: AppGraphContextLens,
        saas_agents: list[SaaSAgentRead],
        component: str,
        surface_id: str,
        variant: str,
        kind: str,
        label: str,
        props: dict[str, Any] | None = None,
    ) -> RouteDeckSurface:
        return RouteDeckSurface(
            name="active",
            surface_id=surface_id,
            component=component,
            variant=variant,
            role="active",
            slot="active",
            surface_kind=kind,
            label=label,
            props={
                "title": lens.working_on,
                "node_id": state.node,
                "saas_agents": [agent.model_dump(mode="json") for agent in saas_agents],
                "lens": lens.model_dump(mode="json"),
                **(props or {}),
                **state.graph_context,
            },
        )

    def _saas_agent_planning_entities(self, saas_agents: list[SaaSAgentRead]) -> list[dict[str, Any]]:
        entities: list[dict[str, Any]] = []
        for agent in saas_agents[: self._PLANNING_ENTITY_LIMIT]:
            entities.append(
                {
                    "entity_type": "saas_agent",
                    "id": str(agent.id),
                    "label": agent.name,
                    "slug": agent.slug,
                    "description": agent.slug,
                    "operation_id": AppActionIds.SAAS_AGENT_OPEN,
                    "args": {"saas_agent_id": str(agent.id)},
                }
            )
        return entities

    def active_surface_component_for_node(self, node_id: str | None) -> str | None:
        active_components = {
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
        return active_components.get(node_id or "")

    def operation_review_surface_id(self, operation_id: str) -> str:
        return f"operation_review.{operation_id}"

    def operation_id_from_surface_id(self, surface_id: str | None) -> str | None:
        if not surface_id or not surface_id.startswith(self._OPERATION_REVIEW_SURFACE_PREFIX):
            return None
        operation_id = surface_id.removeprefix(self._OPERATION_REVIEW_SURFACE_PREFIX).strip()
        return operation_id or None

    def is_surface_hosted_operation(self, *, node_id: str | None, operation_id: str) -> bool:
        if not node_id:
            return False
        return operation_id in self._SURFACE_HOSTED_OPERATIONS_BY_NODE.get(node_id, set())

    def default_surface_id(self, state: AppGraphState) -> str | None:
        if state.pending_operation_id:
            return self.operation_review_surface_id(state.pending_operation_id)
        if state.node == AppNodeIds.LEARNING:
            return "learning.policy_gaps"
        if state.node == AppNodeIds.LEARNING_POLICY_CANDIDATE:
            return "learning.policy_candidate.review"
        if state.node == AppNodeIds.LEARNING_EXECUTION_TRACE:
            return "learning.execution_trace.review"
        if state.node == AppNodeIds.LEARNING_ACTIVE_POLICY:
            return "learning.active_policy.review"
        component = self.active_surface_component_for_node(state.node)
        if component is None:
            return None
        return f"{state.node}.active"

    def review_surface(
        self,
        *,
        state: AppGraphState,
        lens: AppGraphContextLens,
        saas_agents: list[SaaSAgentRead],
    ) -> RouteDeckSurface | None:
        if not state.pending_operation_id:
            return None
        return RouteDeckSurface(
            name="review",
            surface_id=self.operation_review_surface_id(state.pending_operation_id),
            component="CorpusOperationReviewSurface",
            variant="operation_review",
            role="active",
            slot="active",
            surface_kind="peer",
            label="Review next step",
            props={
                "title": "Review next step",
                "node_id": state.node,
                "saas_agents": [agent.model_dump(mode="json") for agent in saas_agents],
                "lens": lens.model_dump(mode="json"),
                "operation_id": state.pending_operation_id,
                "operation_args": state.pending_operation_args,
                **state.graph_context,
            },
        )

    def surface_variant(
        self,
        state: AppGraphState,
        presentation_state: dict[str, Any],
        surface_name: str,
        default: str,
        node_by_id: dict[str, Any],
    ) -> str:
        variants = presentation_state.get("surface_variants")
        requested = variants.get(surface_name) if isinstance(variants, dict) else None
        if not isinstance(requested, str):
            return default
        node = node_by_id.get(state.node)
        allowed = node.allowed_surfaces.get(surface_name) if node else None
        return requested if not allowed or requested in allowed else default

    def store_surface_intent(
        self,
        *,
        state: AppGraphState,
        surface_intent: Any,
        node_by_id: dict[str, Any],
        presentation_state: dict[str, Any],
    ) -> bool:
        if not isinstance(surface_intent, dict):
            return False
        node = node_by_id.get(state.node)
        if node is None:
            return False
        accepted: dict[str, str] = {}
        for surface_name, variant in surface_intent.items():
            if not isinstance(surface_name, str) or not isinstance(variant, str):
                continue
            allowed = node.allowed_surfaces.get(surface_name)
            if allowed and variant not in allowed:
                continue
            accepted[surface_name] = variant
        if not accepted:
            return False
        variants = dict(presentation_state.get("surface_variants") or {})
        variants.update(accepted)
        presentation_state["surface_variants"] = variants
        return True
