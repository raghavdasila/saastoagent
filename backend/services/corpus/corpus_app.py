from __future__ import annotations

from backend.core.schemas import CorpusGraphState
from backend.services.corpus.corpus_operation_requests import CorpusOperationRequests
from backend.services.corpus.corpus_operations import CorpusOperationPolicy
from backend.services.corpus.corpus_routedeck_navigation import CorpusRouteDeckNavigation
from backend.services.corpus.corpus_routedeck_runtime import CorpusRouteDeckRuntime
from backend.services.corpus.corpus_surfaces import CorpusSurfaceRegistry
from backend.services.corpus.manifest import CORPUS_MANIFEST, CorpusActionIds, CorpusNodeIds
from routedeck_core import RouteDeckApp, RouteDeckRouteActionIds


corpus_route_deck_app = (
    RouteDeckApp(CorpusGraphState, runtime_base=CorpusRouteDeckRuntime, name="CorpusRouteDeckRuntime")
    .manifest(CORPUS_MANIFEST)
    .initial_node(CorpusNodeIds.HOME)
    .surfaces(CorpusSurfaceRegistry)
    .navigation(CorpusRouteDeckNavigation)
    .operation_policy(CorpusOperationPolicy)
    .operation_requests(CorpusOperationRequests)
    .route_actions(
        RouteDeckRouteActionIds(
            open_node=CorpusActionIds.ROUTE_OPEN_NODE,
            switch_surface=CorpusActionIds.ROUTE_SWITCH_SURFACE,
            back=CorpusActionIds.ROUTE_BACK,
            forward=CorpusActionIds.ROUTE_FORWARD,
            cancel=CorpusActionIds.ROUTE_CANCEL,
        )
    )
    .operation_review_component("CorpusOperationReviewSurface")
)

route_deck_runtime = corpus_route_deck_app.compile()
