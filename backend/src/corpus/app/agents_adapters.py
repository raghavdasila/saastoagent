from __future__ import annotations

import uuid
from dataclasses import dataclass

from corpus.auth.service import AuthService, SessionUnavailable
from corpus.features.agents.ports import (
    AgentOwnerScopeGateway,
    AgentOwnerScopeUnavailable,
)


@dataclass(frozen=True)
class AuthAgentOwnerScopeGateway(AgentOwnerScopeGateway):
    auth: AuthService

    async def organization_id_for_route(
        self,
        route_session_id: str,
    ) -> uuid.UUID:
        try:
            return await self.auth.organization_id_for_route(route_session_id)
        except SessionUnavailable as error:
            raise AgentOwnerScopeUnavailable(
                "The authenticated owner Workspace is unavailable."
            ) from error

    async def organization_id_for_access_token(
        self,
        access_token: str,
    ) -> uuid.UUID:
        try:
            principal = await self.auth.resolve_access_token(access_token)
        except SessionUnavailable as error:
            raise AgentOwnerScopeUnavailable(
                "Authentication is required."
            ) from error
        if principal.organization_id is None:
            raise AgentOwnerScopeUnavailable("Authentication is required.")
        return principal.organization_id


__all__ = ["AuthAgentOwnerScopeGateway"]
