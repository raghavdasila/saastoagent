from __future__ import annotations

import uuid
from dataclasses import dataclass

from corpus.auth.service import AuthService, SessionUnavailable
from corpus.features.agents.service import AgentService
from corpus.features.workspace.models import (
    WorkspaceOverview,
    WorkspaceSectionState,
)
from corpus.features.workspace.ports import (
    WorkspaceOverviewGateway,
    WorkspaceOverviewUnavailable,
)


@dataclass(frozen=True)
class CorpusWorkspaceOverviewGateway(WorkspaceOverviewGateway):
    auth: AuthService
    agents: AgentService

    async def overview_for_route(
        self,
        route_session_id: str,
    ) -> WorkspaceOverview:
        try:
            organization_id = await self.auth.organization_id_for_route(
                route_session_id
            )
        except SessionUnavailable as error:
            raise WorkspaceOverviewUnavailable(
                "The authenticated Workspace is unavailable."
            ) from error
        return await self._overview(organization_id)

    async def overview_for_access_token(
        self,
        access_token: str,
    ) -> WorkspaceOverview:
        try:
            principal = await self.auth.resolve_access_token(access_token)
        except SessionUnavailable as error:
            raise WorkspaceOverviewUnavailable(
                "Authentication is required."
            ) from error
        if principal.organization_id is None:
            raise WorkspaceOverviewUnavailable("Authentication is required.")
        return await self._overview(principal.organization_id)

    async def _overview(self, organization_id: uuid.UUID) -> WorkspaceOverview:
        agent_count = len((await self.agents.list(organization_id)).agents)
        return WorkspaceOverview(
            agent_count=agent_count,
            agents=WorkspaceSectionState(
                status="empty" if agent_count == 0 else "available",
                message=(
                    "No agents have been created in this Workspace."
                    if agent_count == 0
                    else f"{agent_count} active agent"
                    f"{'s' if agent_count != 1 else ''} in this Workspace."
                ),
            ),
            sources=WorkspaceSectionState(
                status="unavailable",
                message=(
                    "Sources overview is not connected to Workspace in this core slice."
                ),
            ),
            recent_activity=WorkspaceSectionState(
                status="unavailable",
                message=(
                    "Recent activity is not recorded by this core Workspace slice."
                ),
            ),
        )


__all__ = ["CorpusWorkspaceOverviewGateway"]
