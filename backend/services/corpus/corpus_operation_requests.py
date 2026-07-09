from __future__ import annotations

from typing import Any

from fastapi import HTTPException, status

from backend.core.schemas import CorpusGraphState
from backend.services.corpus.corpus_routedeck_navigation import CorpusRouteDeckNavigation
from backend.services.corpus.corpus_surfaces import CorpusSurfaceRegistry
from routedeck_core import (
    RouteDeckOperation,
    RouteDeckOperationRequestPolicy,
    RouteDeckProjection,
    RouteDeckRouteActionIds,
)


class CorpusOperationRequests(RouteDeckOperationRequestPolicy):
    """Corpus route action IDs wired into RouteDeck operation requests."""

    def __init__(
        self,
        *,
        navigation: CorpusRouteDeckNavigation,
        surface_registry: CorpusSurfaceRegistry,
        route_actions: RouteDeckRouteActionIds,
    ) -> None:
        super().__init__(
            navigation=navigation,
            surface_registry=surface_registry,
            route_actions=route_actions,
        )

    def validated_payload(
        self,
        *,
        state: CorpusGraphState,
        operation: RouteDeckOperation,
        args: dict[str, Any] | None,
        projection: RouteDeckProjection,
    ) -> dict[str, Any]:
        try:
            return super().validated_payload(
                state=state,
                operation=operation,
                args=args,
                projection=projection,
            )
        except ValueError as exc:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc

    def review_state_for_operation(
        self,
        *,
        state: CorpusGraphState,
        operation: RouteDeckOperation,
        args: dict[str, Any],
    ) -> CorpusGraphState:
        return super().review_state_for_operation(state=state, operation=operation, args=args)
