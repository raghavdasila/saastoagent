from __future__ import annotations

import uuid
from typing import Protocol

from dataclasses import dataclass

from .domain import (
    AgentBuildLineageRecord,
    AgentDependencySnapshot,
    AgentRecord,
    AgentSourceAttachmentRecord,
)


class AgentNotFound(RuntimeError):
    pass


class AgentNameConflict(RuntimeError):
    pass


class AgentVersionConflict(RuntimeError):
    pass


class AgentLifecycleConflict(RuntimeError):
    pass


class AgentDependencyConflict(RuntimeError):
    pass


class AgentOwnerScopeUnavailable(RuntimeError):
    pass


class AgentSourceAttachmentConflict(RuntimeError):
    pass


class AgentSourceAttachmentUnavailable(RuntimeError):
    pass


class AgentBuildLineageConflict(RuntimeError):
    pass


class AgentBuildLineageUnavailable(RuntimeError):
    pass


@dataclass(frozen=True)
class AttachableSource:
    source_id: str
    source_revision_id: str
    display_name: str


class AgentSourceGateway(Protocol):
    async def ready_inventory(
        self,
        organization_id: uuid.UUID,
    ) -> tuple[AttachableSource, ...]: ...

    async def ready_current(
        self,
        organization_id: uuid.UUID,
        source_id: str,
    ) -> AttachableSource: ...

    async def exact_revision(
        self,
        organization_id: uuid.UUID,
        source_id: str,
        source_revision_id: str,
    ) -> AttachableSource: ...


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

    async def inspect_dependencies(
        self,
        organization_id: uuid.UUID,
        agent_id: uuid.UUID,
    ) -> AgentDependencySnapshot: ...

    async def archive(
        self,
        organization_id: uuid.UUID,
        agent_id: uuid.UUID,
    ) -> AgentRecord: ...

    async def delete(
        self,
        organization_id: uuid.UUID,
        agent_id: uuid.UUID,
    ) -> None: ...

    async def list_source_attachments(
        self,
        organization_id: uuid.UUID,
        agent_id: uuid.UUID,
    ) -> tuple[AgentSourceAttachmentRecord, ...]: ...

    async def attach_source(
        self,
        organization_id: uuid.UUID,
        agent_id: uuid.UUID,
        source: AttachableSource,
    ) -> AgentSourceAttachmentRecord: ...

    async def detach_source(
        self,
        organization_id: uuid.UUID,
        agent_id: uuid.UUID,
        source_id: str,
    ) -> None: ...

    async def get_source_attachment(
        self,
        organization_id: uuid.UUID,
        agent_id: uuid.UUID,
        source_id: str,
    ) -> AgentSourceAttachmentRecord: ...

    async def record_build_lineage(
        self,
        organization_id: uuid.UUID,
        agent_id: uuid.UUID,
        *,
        build_id: uuid.UUID,
        expected_agent_version: int,
        source_references: tuple[tuple[str, str], ...],
    ) -> AgentBuildLineageRecord: ...

    async def list_build_lineages(
        self,
        organization_id: uuid.UUID,
        agent_id: uuid.UUID,
    ) -> tuple[AgentBuildLineageRecord, ...]: ...


__all__ = [
    "AgentNameConflict",
    "AgentBuildLineageConflict",
    "AgentBuildLineageUnavailable",
    "AgentDependencyConflict",
    "AgentLifecycleConflict",
    "AgentNotFound",
    "AgentOwnerScopeGateway",
    "AgentOwnerScopeUnavailable",
    "AgentRepository",
    "AgentSourceAttachmentConflict",
    "AgentSourceAttachmentUnavailable",
    "AgentSourceGateway",
    "AgentVersionConflict",
    "AttachableSource",
]
