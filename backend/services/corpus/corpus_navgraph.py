from __future__ import annotations

from typing import Any

from routedeck_core import RouteDeckManifest, RouteDeckProjection

from backend.core.schemas import CorpusContextLens, CorpusGraphState
from backend.services.corpus.introspection import build_graph_introspection


class CorpusNavgraphDiagnostics:
    """Builds read-only RouteDeck navgraph diagnostics for the Corpus app."""

    def introspection(
        self,
        *,
        manifest: RouteDeckManifest,
        state: CorpusGraphState,
        lens: CorpusContextLens,
        projection: RouteDeckProjection,
        valid_actions: list[dict[str, Any]],
        blocked_actions: list[dict[str, Any]],
        guard_explanations: list[dict[str, Any]],
        diagnostics: dict[str, Any],
    ) -> dict[str, Any]:
        return build_graph_introspection(
            manifest,
            state=state,
            lens=lens,
            projection=projection,
            valid_actions=valid_actions,
            blocked_actions=blocked_actions,
            guard_explanations=guard_explanations,
            diagnostics={**diagnostics, "navgraph": True},
        )
