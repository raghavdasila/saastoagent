from __future__ import annotations

from .ports import WorkspaceOverviewGateway
from .schemas import WorkspaceOverviewView


class WorkspaceService:
    def __init__(self, overview: WorkspaceOverviewGateway) -> None:
        self.overview = overview

    async def for_route(self, route_session_id: str) -> WorkspaceOverviewView:
        return WorkspaceOverviewView.from_model(
            await self.overview.overview_for_route(route_session_id)
        )

    async def for_access_token(self, access_token: str) -> WorkspaceOverviewView:
        return WorkspaceOverviewView.from_model(
            await self.overview.overview_for_access_token(access_token)
        )


__all__ = ["WorkspaceService"]
