from __future__ import annotations

from typing import Any

from fastapi import HTTPException, status

from backend.core.schemas import AppGraphState
from backend.services.app_graph.corpus_routedeck_navigation import CorpusRouteDeckNavigation
from backend.services.app_graph.corpus_surfaces import CorpusSurfaceRegistry
from backend.services.app_graph.manifest import AppActionIds
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
    ) -> None:
        super().__init__(
            navigation=navigation,
            surface_registry=surface_registry,
            route_actions=RouteDeckRouteActionIds(
                open_node=AppActionIds.ROUTE_OPEN_NODE,
                switch_surface=AppActionIds.ROUTE_SWITCH_SURFACE,
                back=AppActionIds.ROUTE_BACK,
                forward=AppActionIds.ROUTE_FORWARD,
                cancel=AppActionIds.ROUTE_CANCEL,
            ),
        )

    def validated_payload(
        self,
        *,
        state: AppGraphState,
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
        state: AppGraphState,
        operation: RouteDeckOperation,
        args: dict[str, Any],
    ) -> AppGraphState:
        return super().review_state_for_operation(state=state, operation=operation, args=args)
