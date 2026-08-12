from __future__ import annotations

import uuid
from collections.abc import Mapping
from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator
from routedeck_core.contracts.operations import OperationSource

from .domain import (
    AgentDependencySnapshot,
    AgentBuildLineageRecord,
    AgentLifecycle,
    AgentRecord,
    AgentProductOverview,
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


class OpenAgentChoiceForSourceArguments(BaseModel):
    model_config = ConfigDict(extra="forbid")
    source_id: str = Field(min_length=16, max_length=16)
    source_revision_id: str = Field(min_length=16, max_length=16)


class OpenAgentCreationArguments(BaseModel):
    model_config = ConfigDict(extra="forbid")
    source_id: str | None = Field(default=None, min_length=16, max_length=16)
    source_revision_id: str | None = Field(default=None, min_length=16, max_length=16)

    @model_validator(mode="after")
    def _complete_source_identity(self) -> "OpenAgentCreationArguments":
        if (self.source_id is None) != (self.source_revision_id is None):
            raise ValueError("Source and API version must be supplied together.")
        return self


class AttachSourceArguments(BaseModel):
    model_config = ConfigDict(extra="forbid")
    agent_ref: str = Field(min_length=1, max_length=64)
    source_id: str | None = Field(
        default=None,
        min_length=16,
        max_length=16,
        description=(
            "Surface-selected Source identity. Agent calls omit this value and use the exact "
            "current pending Source resolved by Corpus."
        ),
    )
    source_revision_id: str | None = Field(
        default=None,
        min_length=16,
        max_length=16,
        description=(
            "Surface-selected API version. Agent calls omit this value and use the exact current "
            "pending API version resolved by Corpus."
        ),
    )

    @model_validator(mode="after")
    def _revision_requires_source(self) -> "AttachSourceArguments":
        if self.source_revision_id is not None and self.source_id is None:
            raise ValueError("An exact API version requires its Source.")
        return self


def attach_source_arguments(
    arguments: Mapping[str, Any],
    source: OperationSource,
) -> AttachSourceArguments:
    values = dict(arguments)
    if source is OperationSource.AGENT:
        # Source identity is server-owned for an agent call. The agent selects
        # the bound Agent; the exact pending Source/revision comes from the
        # current RouteDeck provider context (or the service's unique eligible
        # Source rule), never from model-restated historical identifiers.
        values = {
            key: values[key]
            for key in ("agent_ref",)
            if key in values
        }
    return AttachSourceArguments.model_validate(values)


class DetachSourceArguments(BaseModel):
    model_config = ConfigDict(extra="forbid")
    agent_ref: str = Field(min_length=1, max_length=64)
    source_id: str = Field(min_length=16, max_length=16)


class OpenAttachedSourceArguments(BaseModel):
    model_config = ConfigDict(extra="forbid")
    agent_ref: str = Field(min_length=1, max_length=64)
    source_id: str | None = Field(default=None, min_length=16, max_length=16)
    return_to: Literal["agent", "builder"] = "agent"
    target_stage: Literal["graph", "operations", "connection", "agent"] = "graph"


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


class AgentProductOverviewView(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")
    agent_id: uuid.UUID
    agent_version: int = Field(ge=1)
    source_count: int = Field(ge=0)
    design_status: Literal["missing", "draft", "accepted"]
    design_revision: int | None = Field(default=None, ge=1)
    build_status: str | None
    build_runtime_lifecycle: str | None
    evaluation_status: str | None
    evaluation_case_count: int = Field(ge=0)
    evaluation_eligible: bool | None
    delivery_status: Literal["none", "channel_only", "deploying", "live", "disabled", "failed"]
    hosted_path: str | None
    operations_count: int = Field(ge=0)
    next_step: str

    @classmethod
    def from_model(cls, value: AgentProductOverview) -> "AgentProductOverviewView":
        return cls.model_validate(value, from_attributes=True)


__all__ = [
    "AgentListView",
    "AgentProductOverviewView",
    "AgentBuildLineageListView",
    "AgentBuildLineageView",
    "AgentBuildSourceReferenceView",
    "AgentDependencySourceView",
    "AgentDependencyView",
    "AgentSourceAttachmentListView",
    "AgentSourceAttachmentView",
    "AgentView",
    "AttachSourceArguments",
    "attach_source_arguments",
    "DetachSourceArguments",
    "AgentLifecycleArguments",
    "CreateAgentArguments",
    "OpenAgentChoiceForSourceArguments",
    "OpenAgentCreationArguments",
    "OpenBuildSourceReferenceArguments",
    "OpenAttachedSourceArguments",
    "UpdateAgentArguments",
    "SelectAgentArguments",
]
