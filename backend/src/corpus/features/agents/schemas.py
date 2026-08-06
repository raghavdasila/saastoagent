from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from .domain import AgentLifecycle, AgentRecord


class CreateAgentArguments(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str = Field(min_length=1, max_length=120)
    description: str = Field(default="", max_length=500)
    instructions: str = Field(min_length=1, max_length=12_000)


class UpdateAgentArguments(CreateAgentArguments):
    agent_id: uuid.UUID
    expected_version: int = Field(ge=1)


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


__all__ = [
    "AgentListView",
    "AgentView",
    "CreateAgentArguments",
    "UpdateAgentArguments",
]
