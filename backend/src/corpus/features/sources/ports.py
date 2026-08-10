from __future__ import annotations

import uuid
from typing import Protocol


class SourceOwnerScopeGateway(Protocol):
    async def organization_id_for_route(
        self, route_session_id: str
    ) -> uuid.UUID: ...


__all__ = ["SourceOwnerScopeGateway"]
