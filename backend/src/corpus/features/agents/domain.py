from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import datetime
from enum import Enum


class AgentLifecycle(str, Enum):
    ACTIVE = "active"
    ARCHIVED = "archived"


@dataclass(frozen=True)
class AgentRecord:
    id: uuid.UUID
    organization_id: uuid.UUID
    name: str
    description: str
    instructions: str
    lifecycle: AgentLifecycle
    current_version: int
    created_at: datetime
    updated_at: datetime


@dataclass(frozen=True)
class AgentSourceAttachmentRecord:
    id: uuid.UUID
    organization_id: uuid.UUID
    agent_id: uuid.UUID
    source_id: str
    source_revision_id: str
    attached_at: datetime


@dataclass(frozen=True)
class AgentBuildSourceReferenceRecord:
    id: uuid.UUID
    build_lineage_id: uuid.UUID
    source_id: str
    source_revision_id: str


@dataclass(frozen=True)
class AgentBuildLineageRecord:
    id: uuid.UUID
    organization_id: uuid.UUID
    agent_id: uuid.UUID
    build_id: uuid.UUID
    agent_version: int
    created_at: datetime
    source_references: tuple[AgentBuildSourceReferenceRecord, ...]


@dataclass(frozen=True)
class AgentDependencySnapshot:
    agent_id: uuid.UUID
    source_attachments: tuple[AgentSourceAttachmentRecord, ...]
    build_lineages: tuple[AgentBuildLineageRecord, ...] = ()

    @property
    def blocks_delete(self) -> bool:
        return bool(self.source_attachments or self.build_lineages)


__all__ = [
    "AgentDependencySnapshot",
    "AgentBuildLineageRecord",
    "AgentBuildSourceReferenceRecord",
    "AgentLifecycle",
    "AgentRecord",
    "AgentSourceAttachmentRecord",
]
