from __future__ import annotations

import uuid
from datetime import datetime
from typing import Literal

from routedeck_core.contracts.interactions import OperationSource

from pydantic import BaseModel, ConfigDict, Field


class EvaluationCaseView(BaseModel):
    model_config = ConfigDict(extra="forbid")
    id: uuid.UUID
    title: str
    message: str
    source_kind: str
    category: str
    difficulty: str
    mandatory: bool
    expected_operation_ids: tuple[str, ...]
    current_revision: int
    removed: bool
    runnable: bool
    latest_status: str | None = None
    latest_run_attempt: "EvaluationRunAttemptView | None" = None


class EvaluationRunAttemptView(BaseModel):
    model_config = ConfigDict(extra="forbid")
    id: uuid.UUID
    status: Literal["queued", "running", "succeeded", "failed"]
    failure_code: str | None
    failure_message: str | None
    retry_of_attempt_id: uuid.UUID | None
    created_at: datetime
    updated_at: datetime


class EvaluationSetView(BaseModel):
    model_config = ConfigDict(extra="forbid")
    id: uuid.UUID
    agent_id: uuid.UUID
    build_id: uuid.UUID
    name: str
    generation_job_id: uuid.UUID | None
    generation_status: str
    generation_failure_code: str | None
    generation_failure_message: str | None
    generation_summary: dict[str, object] | None
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
    case_origin: Literal["generated", "sandbox", "operations"] | None = None


def run_evaluation_case_arguments(
    arguments: dict[str, object],
    source: OperationSource,
) -> RunEvaluationCaseArguments:
    payload = RunEvaluationCaseArguments.model_validate(arguments)
    if source is OperationSource.SURFACE:
        if payload.case_id is None or payload.case_origin is not None:
            raise ValueError("Surface evaluation requires one exact case selection.")
        return payload
    if payload.case_id is not None:
        payload = payload.model_copy(update={"case_id": None})
    return payload


class RetryEvaluationRunArguments(BaseModel):
    model_config = ConfigDict(extra="forbid")
    agent_ref: str = Field(min_length=1, max_length=64)
    attempt_id: uuid.UUID


class GenerateEvaluationSetArguments(BaseModel):
    model_config = ConfigDict(extra="forbid")
    agent_ref: str = Field(min_length=1, max_length=64)
    build_id: uuid.UUID | None = None
    set_name: str = Field(default="Generated coverage", min_length=1, max_length=160)
    categories: tuple[Literal["paraphrase", "non_exact_wording", "low_lexical_overlap", "typo_or_noisy", "verbose_or_indirect"], ...] = ("paraphrase",)


class EditEvaluationCaseArguments(BaseModel):
    model_config = ConfigDict(extra="forbid")
    agent_ref: str = Field(min_length=1, max_length=64)
    case_id: uuid.UUID
    expected_revision: int = Field(ge=1)
    title: str = Field(min_length=1, max_length=160)
    category: str = Field(min_length=1, max_length=80)
    difficulty: Literal["easy", "medium", "hard"]
    mandatory: bool


class DeleteEvaluationCaseArguments(BaseModel):
    model_config = ConfigDict(extra="forbid")
    agent_ref: str = Field(min_length=1, max_length=64)
    case_id: uuid.UUID
    expected_revision: int = Field(ge=1)


class RetryEvaluationGenerationArguments(BaseModel):
    model_config = ConfigDict(extra="forbid")
    agent_ref: str = Field(min_length=1, max_length=64)
    evaluation_set_id: uuid.UUID
