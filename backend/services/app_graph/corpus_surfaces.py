from __future__ import annotations

from typing import Any

from routedeck_core import RouteDeckOperation, RouteDeckSurface

from backend.core.schemas import AppGraphContextLens, AppGraphState, SaaSAgentRead
from backend.services.app_graph.manifest import AppActionIds, AppNodeIds


class CorpusSurfaceRegistry:
    """Owns SaaStoAgent surface names, variants, and deterministic surface copy."""

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
        if state.node == AppNodeIds.LEARNING:
            return [
                self._surface(
                    state=state,
                    lens=lens,
                    saas_agents=saas_agents,
                    component="LearningSurface",
                    surface_id="learning.policy_gaps",
                    variant="policy_gaps",
                    kind="peer",
                    label="Policy gaps",
                    props={"filter": "policy_gaps"},
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
                    props={"filter": "failed_executions"},
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
                    props={"filter": "active_policies"},
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
                    props={"filter": "rejected"},
                ),
            ]
        if state.node == AppNodeIds.LEARNING_POLICY_CANDIDATE:
            return [
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
        if state.node == AppNodeIds.LEARNING_EXECUTION_TRACE:
            return [
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
        if state.node == AppNodeIds.LEARNING_ACTIVE_POLICY:
            return [
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
        component = self.active_surface_component_for_node(state.node)
        if component is None:
            return []
        return [self._surface(
            state=state,
            lens=lens,
            saas_agents=saas_agents,
            component=component,
            surface_id=f"{state.node}.active",
            variant=state.node,
            kind="embedded",
            label=lens.working_on,
        )]

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

    def deterministic_open_message(self, operation: RouteDeckOperation) -> str:
        prompts = {
            AppActionIds.CONNECTION_CONFIGURE: (
                "Connection setup is open. Enter the API name, base URL, OpenAPI schema URL, and auth details, "
                "then preview or save and activate the connection."
            ),
            AppActionIds.SAAS_AGENT_CREATE: "The SaaS Agent creation form is open. Enter a name and slug to continue.",
            AppActionIds.INSTRUCTIONS_OPEN: "Instructions are open. Update the agent prompt and operating guidance, then save changes.",
            AppActionIds.KNOWLEDGE_OPEN: "Knowledge is open. Add documents or review generated catalog context for this agent.",
            AppActionIds.MEMORY_OPEN: "Memory is open. Add durable facts or instructions for this SaaS Agent.",
            AppActionIds.LEARNING_OPEN: "Learning is open. Review sandbox learning candidates before applying them.",
            AppActionIds.QA_OPEN: "QA is open. Run scenarios to validate this agent configuration.",
            AppActionIds.EXECUTION_OPEN: "Execution planning is open. Describe the API task you want to run.",
        }
        return prompts.get(operation.id, "")

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
