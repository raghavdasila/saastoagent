from __future__ import annotations

import uuid
from pydantic import BaseModel, ConfigDict, Field


class OperationsEventView(BaseModel):
    model_config = ConfigDict(extra="forbid")
    sequence: int
    kind: str
    safe_data: dict[str, object]


class OperationsInteractionView(BaseModel):
    model_config = ConfigDict(extra="forbid")
    interaction_id: str
    agent_id: uuid.UUID
    build_id: uuid.UUID
    deployment_id: uuid.UUID
    session_id: str
    input_summary: str
    output_summary: str
    status: str
    evaluation_case_id: uuid.UUID | None
    events: tuple[OperationsEventView, ...]


class OperationsCollectionView(BaseModel):
    model_config = ConfigDict(extra="forbid")
    interactions: tuple[OperationsInteractionView, ...]


class PromoteInteractionArguments(BaseModel):
    model_config = ConfigDict(extra="forbid")
    interaction_id: str | None = Field(default=None, min_length=1, max_length=80)
    set_name: str = Field(min_length=1, max_length=160)
    title: str = Field(min_length=1, max_length=160)
    category: str = Field(min_length=1, max_length=80)
    difficulty: str = Field(pattern="^(easy|medium|hard)$")
    mandatory: bool = True
