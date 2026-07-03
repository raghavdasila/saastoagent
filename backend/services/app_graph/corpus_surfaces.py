from __future__ import annotations

from typing import Any

from routedeck_core import RouteDeckSurface, RouteDeckSurfaceRegistry

from backend.core.schemas import AppGraphContextLens, AppGraphState, SaaSAgentRead
from backend.services.app_graph.corpus_surface_catalog import CorpusSurfaceCatalog, CorpusSurfaceSpec


class CorpusSurfaceRegistry(RouteDeckSurfaceRegistry):
    """Adapts Corpus surface descriptors to RouteDeck surface mechanics."""

    def __init__(self, catalog: CorpusSurfaceCatalog | None = None) -> None:
        self._catalog = catalog or CorpusSurfaceCatalog()
        super().__init__(
            active_components_by_node=self._catalog.active_components_by_node,
            default_surface_ids_by_node=self._catalog.default_surface_ids_by_node,
            surface_hosted_operations_by_node=self._catalog.surface_hosted_operations_by_node,
            operation_review_surface_prefix=self._catalog.operation_review_surface_prefix,
        )

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
        spec = self._catalog.frame_spec(state=state, lens=lens, saas_agents=saas_agents, context=context)
        return self._build_surface(
            spec=spec,
            state=state,
            lens=lens,
            saas_agents=saas_agents,
            variant=self.surface_variant(state, presentation_state, "main", spec.variant, node_by_id),
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
        surfaces = [
            self._build_active_surface(spec=spec, state=state, lens=lens, saas_agents=saas_agents)
            for spec in self._catalog.active_specs(state=state, lens=lens, saas_agents=saas_agents, context=context)
        ]
        review_surface = self.review_surface(state=state, lens=lens, saas_agents=saas_agents)
        return [review_surface, *surfaces] if review_surface else surfaces

    def default_surface_id(self, state: AppGraphState) -> str | None:
        return self.default_surface_id_for(state.node, pending_operation_id=state.pending_operation_id)

    def review_surface(
        self,
        *,
        state: AppGraphState,
        lens: AppGraphContextLens,
        saas_agents: list[SaaSAgentRead],
    ) -> RouteDeckSurface | None:
        if not state.pending_operation_id:
            return None
        return self.operation_review_surface(
            node_id=state.node,
            operation_id=state.pending_operation_id,
            operation_args=state.pending_operation_args,
            component="CorpusOperationReviewSurface",
            props=self._catalog.review_props(
                lens=lens,
                saas_agents=saas_agents,
                graph_context=state.graph_context,
            ),
        )

    def surface_variant(
        self,
        state: AppGraphState,
        presentation_state: dict[str, Any],
        surface_name: str,
        default: str,
        node_by_id: dict[str, Any],
    ) -> str:
        return self.surface_variant_for_node(
            node_id=state.node,
            presentation_state=presentation_state,
            surface_name=surface_name,
            default=default,
            node_by_id=node_by_id,
        )

    def store_surface_intent(
        self,
        *,
        state: AppGraphState,
        surface_intent: Any,
        node_by_id: dict[str, Any],
        presentation_state: dict[str, Any],
    ) -> bool:
        return self.store_surface_intent_for_node(
            node_id=state.node,
            surface_intent=surface_intent,
            node_by_id=node_by_id,
            presentation_state=presentation_state,
        )

    def _build_active_surface(
        self,
        *,
        spec: CorpusSurfaceSpec,
        state: AppGraphState,
        lens: AppGraphContextLens,
        saas_agents: list[SaaSAgentRead],
    ) -> RouteDeckSurface:
        props = {
            "title": lens.working_on,
            "node_id": state.node,
            "saas_agents": [agent.model_dump(mode="json") for agent in saas_agents],
            "lens": lens.model_dump(mode="json"),
            **spec.resolve_props(state=state, lens=lens, saas_agents=saas_agents),
            **state.graph_context,
            "router_index": state.graph_context.get("router_index") or self._catalog.router_index_from_lens(lens),
        }
        return self._build_surface(spec=spec, state=state, lens=lens, saas_agents=saas_agents, props=props)

    def _build_surface(
        self,
        *,
        spec: CorpusSurfaceSpec,
        state: AppGraphState,
        lens: AppGraphContextLens,
        saas_agents: list[SaaSAgentRead],
        variant: str | None = None,
        props: dict[str, Any] | None = None,
    ) -> RouteDeckSurface:
        return self.build_surface(
            name=spec.name,
            surface_id=spec.surface_id,
            component=spec.component,
            variant=variant or spec.variant,
            role=spec.role,
            slot=spec.slot,
            surface_kind=spec.surface_kind,
            label=spec.label or lens.working_on,
            props=props if props is not None else spec.resolve_props(state=state, lens=lens, saas_agents=saas_agents),
            lifecycle=spec.lifecycle,
        )
