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


@dataclass(frozen=True)
class AgentProductOverview:
    agent_id: uuid.UUID
    agent_version: int
    source_count: int
    design_status: str
    design_revision: int | None
    build_status: str | None
    build_runtime_lifecycle: str | None
    evaluation_status: str | None
    evaluation_case_count: int
    evaluation_eligible: bool | None
    delivery_status: str
    hosted_path: str | None
    operations_count: int
    next_step: str


__all__ = [
    "AgentDependencySnapshot",
    "AgentBuildLineageRecord",
    "AgentBuildSourceReferenceRecord",
    "AgentLifecycle",
    "AgentProductOverview",
    "AgentRecord",
    "AgentSourceAttachmentRecord",
]
