from __future__ import annotations

from typing import Any

from routedeck_core import RouteDeckSurfaceRegistry

from backend.core.schemas import CorpusContextLens, CorpusGraphState, CorpusSurface, SaaSAgentRead
from backend.services.corpus.corpus_surface_catalog import CorpusSurfaceCatalog, CorpusSurfaceSpec


class CorpusSurfaceRegistry(RouteDeckSurfaceRegistry):
    """Adapts Corpus surface descriptors to RouteDeck surface mechanics."""

    Surface = CorpusSurface

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
        state: CorpusGraphState,
        lens: CorpusContextLens,
        saas_agents: list[SaaSAgentRead],
        context: str,
        presentation_state: dict[str, Any],
        node_by_id: dict[str, Any],
    ) -> CorpusSurface:
        spec = self._catalog.frame_spec(state=state, lens=lens, saas_agents=saas_agents, context=context)
        return self.build_surface_from_spec(
            spec=spec,
            variant=self.surface_variant_for_node(
                node_id=state.node,
                presentation_state=presentation_state,
                surface_name="main",
                default=spec.variant,
                node_by_id=node_by_id,
            ),
            label=spec.label or lens.working_on,
            props=spec.resolve_props(state=state, lens=lens, saas_agents=saas_agents),
        )

    def active_surfaces(
        self,
        *,
        state: CorpusGraphState,
        lens: CorpusContextLens,
        saas_agents: list[SaaSAgentRead],
        context: str,
    ) -> list[CorpusSurface]:
        return self.surfaces_from_specs(
            self._catalog.active_specs(state=state, lens=lens, saas_agents=saas_agents, context=context),
            state=state,
            lens=lens,
            saas_agents=saas_agents,
        )

    def review_surface_props(
        self,
        *,
        state: CorpusGraphState,
        lens: CorpusContextLens,
        saas_agents: list[SaaSAgentRead],
    ) -> dict[str, Any]:
        return self._catalog.review_props(
            lens=lens,
            saas_agents=saas_agents,
            graph_context=state.graph_context,
        )

    def surface_props_for_spec(
        self,
        spec: CorpusSurfaceSpec,
        **context: Any,
    ) -> dict[str, Any]:
        state = context.get("state")
        lens = context.get("lens")
        saas_agents = context.get("saas_agents") or []
        if not isinstance(state, CorpusGraphState) or not isinstance(lens, CorpusContextLens):
            return dict(super().surface_props_for_spec(spec, **context))
        return {
            "title": lens.working_on,
            "node_id": state.node,
            "saas_agents": [agent.model_dump(mode="json") for agent in saas_agents],
            "lens": lens.model_dump(mode="json"),
            **spec.resolve_props(state=state, lens=lens, saas_agents=saas_agents),
            **state.graph_context,
            "router_index": state.graph_context.get("router_index") or self._catalog.router_index_from_lens(lens),
        }

    def surface_label_for_spec(
        self,
        spec: CorpusSurfaceSpec,
        **context: Any,
    ) -> str | None:
        lens = context.get("lens")
        return spec.label or (lens.working_on if isinstance(lens, CorpusContextLens) else None)
