from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from .domain import (
    AgentDependencySnapshot,
    AgentBuildLineageRecord,
    AgentLifecycle,
    AgentRecord,
    AgentSourceAttachmentRecord,
)


class CreateAgentArguments(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str = Field(min_length=1, max_length=120)
    description: str = Field(default="", max_length=500)
    instructions: str = Field(min_length=1, max_length=12_000)


class UpdateAgentArguments(CreateAgentArguments):
    agent_id: uuid.UUID
    expected_version: int = Field(ge=1)


class SelectAgentArguments(BaseModel):
    model_config = ConfigDict(extra="forbid")
    agent_id: uuid.UUID


class AttachSourceArguments(BaseModel):
    model_config = ConfigDict(extra="forbid")
    agent_ref: str = Field(min_length=1, max_length=64)
    source_id: str | None = Field(default=None, min_length=16, max_length=16)


class OpenAttachedSourceArguments(BaseModel):
    model_config = ConfigDict(extra="forbid")
    agent_ref: str = Field(min_length=1, max_length=64)
    source_id: str | None = Field(default=None, min_length=16, max_length=16)


class AgentLifecycleArguments(BaseModel):
    model_config = ConfigDict(extra="forbid")
    agent_ref: str = Field(min_length=1, max_length=64)


class OpenBuildSourceReferenceArguments(AgentLifecycleArguments):
    build_id: uuid.UUID
    source_id: str = Field(min_length=16, max_length=16)
    source_revision_id: str = Field(min_length=16, max_length=16)


class AgentSourceAttachmentView(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")
    source_id: str
    source_revision_id: str
    display_name: str
    attached_at: datetime

    @classmethod
    def from_record(
        cls,
        value: AgentSourceAttachmentRecord,
        *,
        display_name: str,
    ) -> "AgentSourceAttachmentView":
        return cls(
            source_id=value.source_id,
            source_revision_id=value.source_revision_id,
            display_name=display_name,
            attached_at=value.attached_at,
        )


class AgentView(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    id: uuid.UUID
    name: str
    description: str
    instructions: str
    lifecycle: AgentLifecycle
    current_version: int
    created_at: datetime
    updated_at: datetime

    @classmethod
    def from_record(cls, value: AgentRecord) -> AgentView:
        return cls.model_validate(
            {
                "id": value.id,
                "name": value.name,
                "description": value.description,
                "instructions": value.instructions,
                "lifecycle": value.lifecycle,
                "current_version": value.current_version,
                "created_at": value.created_at,
                "updated_at": value.updated_at,
            }
        )


class AgentListView(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    agents: tuple[AgentView, ...]


class AgentSourceAttachmentListView(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")
    attachments: tuple[AgentSourceAttachmentView, ...]


class AgentDependencySourceView(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")
    source_id: str
    source_revision_id: str


class AgentDependencyView(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")
    agent_id: uuid.UUID
    source_attachments: tuple[AgentDependencySourceView, ...]
    build_ids: tuple[uuid.UUID, ...] = ()
    blocks_delete: bool

    @classmethod
    def from_snapshot(cls, value: AgentDependencySnapshot) -> "AgentDependencyView":
        return cls(
            agent_id=value.agent_id,
            source_attachments=tuple(
                AgentDependencySourceView(
                    source_id=item.source_id,
                    source_revision_id=item.source_revision_id,
                )
                for item in value.source_attachments
            ),
            build_ids=tuple(item.build_id for item in value.build_lineages),
            blocks_delete=value.blocks_delete,
        )


class AgentBuildSourceReferenceView(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")
    source_id: str
    source_revision_id: str
    display_name: str | None
    available: bool


class AgentBuildLineageView(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")
    build_id: uuid.UUID
    agent_id: uuid.UUID
    agent_version: int
    created_at: datetime
    source_references: tuple[AgentBuildSourceReferenceView, ...]


class AgentBuildLineageListView(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")
    builds: tuple[AgentBuildLineageView, ...]


__all__ = [
    "AgentListView",
    "AgentBuildLineageListView",
    "AgentBuildLineageView",
    "AgentBuildSourceReferenceView",
    "AgentDependencySourceView",
    "AgentDependencyView",
    "AgentSourceAttachmentListView",
    "AgentSourceAttachmentView",
    "AgentView",
    "AttachSourceArguments",
    "AgentLifecycleArguments",
    "CreateAgentArguments",
    "OpenBuildSourceReferenceArguments",
    "OpenAttachedSourceArguments",
    "UpdateAgentArguments",
    "SelectAgentArguments",
]
