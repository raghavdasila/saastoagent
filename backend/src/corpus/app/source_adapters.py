from __future__ import annotations

import uuid
from dataclasses import dataclass

from corpus.auth.service import AuthService, SessionUnavailable


class SourceOwnerScopeUnavailable(RuntimeError):
    pass


@dataclass(frozen=True)
class AuthSourceOwnerScopeGateway:
    auth: AuthService

    async def organization_id_for_route(
        self, route_session_id: str
    ) -> uuid.UUID:
        try:
            return await self.auth.organization_id_for_route(route_session_id)
        except SessionUnavailable as error:
            raise SourceOwnerScopeUnavailable(
                "The owner Workspace is unavailable."
            ) from error


__all__ = ["AuthSourceOwnerScopeGateway", "SourceOwnerScopeUnavailable"]
