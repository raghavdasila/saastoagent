from __future__ import annotations

import uuid
from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class EvaluationCaseView(BaseModel):
    model_config = ConfigDict(extra="forbid")
    id: uuid.UUID
    title: str
    category: str
    difficulty: str
    mandatory: bool
    expected_operation_ids: tuple[str, ...]
    latest_status: str | None = None


class EvaluationSetView(BaseModel):
    model_config = ConfigDict(extra="forbid")
    id: uuid.UUID
    agent_id: uuid.UUID
    build_id: uuid.UUID
    name: str
    cases: tuple[EvaluationCaseView, ...]
    eligible: bool | None
    eligibility_reasons: tuple[str, ...]
    created_at: datetime


class EvaluationCollectionView(BaseModel):
    model_config = ConfigDict(extra="forbid")
    agent_id: uuid.UUID
    evaluation_sets: tuple[EvaluationSetView, ...]


class CreateEvaluationCaseArguments(BaseModel):
    model_config = ConfigDict(extra="forbid")
    agent_ref: str = Field(min_length=1, max_length=64)
    build_id: uuid.UUID | None = None
    sandbox_run_id: uuid.UUID | None = None
    set_name: str = Field(min_length=1, max_length=160)
    title: str = Field(min_length=1, max_length=160)
    category: str = Field(min_length=1, max_length=80)
    difficulty: Literal["easy", "medium", "hard"]
    mandatory: bool = True


class RunEvaluationCaseArguments(BaseModel):
    model_config = ConfigDict(extra="forbid")
    agent_ref: str = Field(min_length=1, max_length=64)
    case_id: uuid.UUID | None = None
