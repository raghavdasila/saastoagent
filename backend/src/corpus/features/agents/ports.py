from __future__ import annotations

import uuid
from typing import Protocol

from .domain import AgentRecord


class AgentNotFound(RuntimeError):
    pass


class AgentNameConflict(RuntimeError):
    pass


class AgentVersionConflict(RuntimeError):
    pass


class AgentOwnerScopeUnavailable(RuntimeError):
    pass


class AgentOwnerScopeGateway(Protocol):
    async def organization_id_for_route(
        self,
        route_session_id: str,
    ) -> uuid.UUID: ...

    async def organization_id_for_access_token(
        self,
        access_token: str,
    ) -> uuid.UUID: ...


class AgentRepository(Protocol):
    async def list(self, organization_id: uuid.UUID) -> tuple[AgentRecord, ...]: ...

    async def get(
        self,
        organization_id: uuid.UUID,
        agent_id: uuid.UUID,
    ) -> AgentRecord: ...

    async def create(
        self,
        organization_id: uuid.UUID,
        *,
        name: str,
        name_key: str,
        description: str,
        instructions: str,
    ) -> AgentRecord: ...

    async def update(
        self,
        organization_id: uuid.UUID,
        agent_id: uuid.UUID,
        *,
        expected_version: int,
        name: str,
        name_key: str,
        description: str,
        instructions: str,
    ) -> AgentRecord: ...


__all__ = [
    "AgentNameConflict",
    "AgentNotFound",
    "AgentOwnerScopeGateway",
    "AgentOwnerScopeUnavailable",
    "AgentRepository",
    "AgentVersionConflict",
]
