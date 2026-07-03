from __future__ import annotations

from typing import Any

from routedeck_core import RouteDeckManifest, RouteDeckProjection, RouteDeckStateProjector, RouteDeckSurface

from backend.core.models import User
from backend.core.schemas import AppGraphContextLens, AppGraphState, SaaSAgentRead
from backend.services.app_graph.corpus_navgraph import CorpusNavgraphDiagnostics
from backend.services.app_graph.corpus_operations import CorpusOperationPolicy
from backend.services.app_graph.corpus_surfaces import CorpusSurfaceRegistry
from backend.services.app_graph.manifest import APP_GRAPH_VERSION, CAPABILITY_RAIL_ITEMS


class CorpusRouteDeckStateProjector(RouteDeckStateProjector):
    """Projects Corpus app state into RouteDeck runtime state primitives."""

    def __init__(
        self,
        *,
        manifest: RouteDeckManifest,
        node_by_id: dict[str, Any],
        operation_policy: CorpusOperationPolicy | None = None,
        surface_registry: CorpusSurfaceRegistry | None = None,
        navgraph_diagnostics: CorpusNavgraphDiagnostics | None = None,
    ) -> None:
        operation_policy = operation_policy or CorpusOperationPolicy()
        surface_registry = surface_registry or CorpusSurfaceRegistry()
        super().__init__(
            manifest=manifest,
            operation_policy=operation_policy,
            surface_registry=surface_registry,
        )
        self.node_by_id = node_by_id
        self.navgraph_diagnostics = navgraph_diagnostics or CorpusNavgraphDiagnostics()

    def project(
        self,
        *,
        state: AppGraphState,
        user: User | None,
        lens: AppGraphContextLens,
        actions: list[Any],
        saas_agents: list[SaaSAgentRead],
        context: str,
        presentation_state: dict[str, Any],
        replace_path: str,
        projection_version: int,
        blocked_actions: list[dict[str, Any]],
        guard_explanations: list[dict[str, Any]],
    ) -> RouteDeckProjection:
        frame_surface = self.surface_registry.frame_surface(
            state=state,
            lens=lens,
            saas_agents=saas_agents,
            context=context,
            presentation_state=presentation_state,
            node_by_id=self.node_by_id,
        )
        active_surfaces = self.surface_registry.active_surfaces(
            state=state,
            lens=lens,
            saas_agents=saas_agents,
            context=context,
        )
        default_surface_by_node = self._default_surface_by_node(
            state=state,
            lens=lens,
            saas_agents=saas_agents,
            context=context,
        )
        current_surface_id = self.resolve_current_surface_id(
            active_surface_id=state.active_surface_id,
            pending_operation_id=state.pending_operation_id,
            default_surface_id=self.surface_registry.default_surface_id(state),
        )
        projection = super().project(
            current_node=state.node,
            current_context=context,
            actions=actions,
            surfaces=[
                frame_surface,
                RouteDeckSurface(
                    name="side",
                    component="CorpusContextLens",
                    variant="default",
                    role="frame",
                    props=lens.model_dump(mode="json"),
                    lifecycle="stable",
                ),
                *active_surfaces,
            ],
            navigation={
                "current": {
                    "node_id": state.node,
                    "surface_id": current_surface_id,
                    "params": state.route_params,
                },
                "back_stack": [location.model_dump(mode="json") for location in state.navigation_back_stack],
                "forward_stack": [location.model_dump(mode="json") for location in state.navigation_forward_stack],
            },
            presentation_state={"context": context, **presentation_state},
            projection_version=projection_version,
            diagnostics={
                **self.base_diagnostics(state),
                "capability_rail": CAPABILITY_RAIL_ITEMS,
                "node_hierarchy": self.node_hierarchy(default_surface_by_node=default_surface_by_node),
            },
        )
        introspection = self.navgraph_diagnostics.introspection(
            manifest=self.manifest,
            state=state,
            lens=lens,
            projection=projection,
            valid_actions=[action.model_dump(mode="json") for action in actions],
            blocked_actions=blocked_actions,
            guard_explanations=guard_explanations,
            diagnostics={**self.base_diagnostics(state), "replace_path": replace_path},
        )
        diagnostics = {**projection.diagnostics, "introspection": introspection}
        return projection.model_copy(update={"diagnostics": diagnostics})

    def base_diagnostics(self, state: AppGraphState) -> dict[str, Any]:
        return {
            "source": "corpus_graph",
            "graph_version": APP_GRAPH_VERSION,
            "selected_saas_agent_id": str(state.active_saas_agent_id) if state.active_saas_agent_id else None,
        }

    def _default_surface_by_node(
        self,
        *,
        state: AppGraphState,
        lens: AppGraphContextLens,
        saas_agents: list[SaaSAgentRead],
        context: str,
    ) -> dict[str, str]:
        defaults: dict[str, str] = {}
        for node in self.manifest.nodes:
            node_state = state.model_copy(
                update={
                    "node": node.id,
                    "active_surface_id": None,
                    "pending_operation_id": None,
                    "pending_operation_args": {},
                    "route_params": {},
                }
            )
            default_surface_id = self.surface_registry.default_surface_id(node_state)
            if default_surface_id:
                defaults[node.id] = default_surface_id
        return defaults
