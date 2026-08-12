from __future__ import annotations

import uuid
from dataclasses import dataclass
from typing import Protocol


class SourceOwnerScopeGateway(Protocol):
    async def organization_id_for_route(
        self, route_session_id: str
    ) -> uuid.UUID: ...

    async def conversation_id_for_route(self, route_session_id: str) -> str: ...


@dataclass(frozen=True)
class SourceDependencyReferences:
    attached_agent_ids: tuple[uuid.UUID, ...] = ()
    build_ids: tuple[uuid.UUID, ...] = ()
    design_revision_ids: tuple[uuid.UUID, ...] = ()


class SourceDependencyGateway(Protocol):
    async def inspect_source_dependencies(
        self, organization_id: uuid.UUID, source_id: str
    ) -> SourceDependencyReferences: ...


__all__ = [
    "SourceDependencyGateway",
    "SourceDependencyReferences",
    "SourceOwnerScopeGateway",
]
