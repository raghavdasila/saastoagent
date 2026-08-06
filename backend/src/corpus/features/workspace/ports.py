from __future__ import annotations

from typing import Protocol

from .models import WorkspaceOverview


class WorkspaceOverviewUnavailable(RuntimeError):
    pass


class WorkspaceOverviewGateway(Protocol):
    async def overview_for_route(
        self,
        route_session_id: str,
    ) -> WorkspaceOverview: ...

    async def overview_for_access_token(
        self,
        access_token: str,
    ) -> WorkspaceOverview: ...


__all__ = ["WorkspaceOverviewGateway", "WorkspaceOverviewUnavailable"]
