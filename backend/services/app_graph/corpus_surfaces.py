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
        component = self.active_surface_component_for_node(state.node)
        if component is None:
            return None
        return RouteDeckSurface(
            name="active",
            component=component,
            variant=state.node,
            role="active",
            props={
                "title": lens.working_on,
                "node_id": state.node,
                "saas_agents": [agent.model_dump(mode="json") for agent in saas_agents],
                "lens": lens.model_dump(mode="json"),
                **state.graph_context,
            },
        )

    def active_surface_component_for_node(self, node_id: str | None) -> str | None:
        active_components = {
            AppNodeIds.AUTH_SIGN_IN: "CorpusAuthSurface",
            AppNodeIds.AUTH_REGISTER: "CorpusAuthSurface",
            AppNodeIds.SAAS_AGENT_SELECT: "SaaSAgentListSurface",
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
            AppNodeIds.QA: "QASurface",
            AppNodeIds.RECOVERY: "RecoverySurface",
        }
        return active_components.get(node_id or "")

    def expected_active_surface_for_operation(self, operation: RouteDeckOperation) -> dict[str, Any] | None:
        component = self.active_surface_component_for_node(operation.target_node)
        if component is None:
            return None
        return {
            "name": "active",
            "component": component,
            "variant": operation.target_node,
            "role": "active",
        }

    def surface_prompt_payload(
        self,
        *,
        operation: RouteDeckOperation,
        response: Any,
        decision_message: str,
        expected_active_surface: dict[str, Any] | None,
    ) -> dict[str, Any] | None:
        if expected_active_surface is None:
            return None
        content = self.deterministic_surface_prompt(operation)
        if not content:
            content = decision_message.strip()
        if not content and response.messages:
            content = str(response.messages[0].content or "").strip()
        if not content:
            return None
        return {
            "operation_id": operation.id,
            "target_node": operation.target_node,
            "expected_active_surface": expected_active_surface,
            "content": content,
        }

    def deterministic_surface_prompt(self, operation: RouteDeckOperation) -> str:
        prompts = {
            AppActionIds.CONNECTION_CONFIGURE: (
                "Connection setup is open. Enter the API name, base URL, OpenAPI schema URL, and auth details, "
                "then preview or save and activate the connection."
            ),
            AppActionIds.SAAS_AGENT_CREATE: "The SaaS Agent creation form is open. Enter a name and slug to continue.",
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
