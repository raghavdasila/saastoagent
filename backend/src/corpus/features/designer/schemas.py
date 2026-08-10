from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from .topology import DesignTopology


class DesignContent(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")
    goal: str = Field(max_length=500)
    instructions: str = Field(min_length=1, max_length=12_000)
    features: tuple[str, ...] = Field(max_length=64)
    behaviors: tuple[str, ...] = Field(max_length=64)
    policies: tuple[str, ...] = Field(max_length=64)
    capabilities: tuple[str, ...] = Field(max_length=64)
    tools: tuple[str, ...] = Field(max_length=512)


class DesignerAgentArguments(BaseModel):
    model_config = ConfigDict(extra="forbid")
    agent_ref: str = Field(min_length=1, max_length=64)


class CustomizeDesignArguments(DesignerAgentArguments):
    expected_revision_id: uuid.UUID | None = None
    content: DesignContent


class ReviewDesignArguments(DesignerAgentArguments):
    expected_revision_id: uuid.UUID | None = None


class RequestBuildArguments(DesignerAgentArguments):
    accepted_revision_id: uuid.UUID | None = None


class DesignRevisionView(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")
    id: uuid.UUID
    revision: int
    agent_version: int
    input_fingerprint: str
    content: DesignContent
    topology: DesignTopology
    source_inputs: tuple[dict[str, object], ...]
    created_at: datetime


class BuildRequestView(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")
    id: uuid.UUID
    design_revision_id: uuid.UUID
    status: str
    created_at: datetime


class AgentDesignView(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")
    agent_id: uuid.UUID
    current_revision_id: uuid.UUID
    accepted_revision_id: uuid.UUID | None
    revisions: tuple[DesignRevisionView, ...]
    build_request: BuildRequestView | None
