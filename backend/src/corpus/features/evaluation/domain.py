from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True)
class EvaluationSetRecord:
    id: uuid.UUID
    organization_id: uuid.UUID
    agent_id: uuid.UUID
    build_id: uuid.UUID
    name: str
    generation_job_id: uuid.UUID | None
    generation_status: str
    generation_failure_code: str | None
    generation_failure_message: str | None
    generation_summary: dict[str, object] | None
    created_at: datetime
    updated_at: datetime


@dataclass(frozen=True)
class EvaluationCaseRecord:
    id: uuid.UUID
    organization_id: uuid.UUID
    evaluation_set_id: uuid.UUID
    build_id: uuid.UUID
    runtime_case_id: str | None
    generation_task_id: str | None
    source_kind: str
    source_record_id: str
    title: str
    message: str
    category: str
    difficulty: str
    expected_operation_ids: tuple[str, ...]
    required_response_fields: tuple[str, ...]
    require_write_verification: bool
    mandatory: bool
    current_revision: int
    removed_at: datetime | None
    created_at: datetime


@dataclass(frozen=True)
class EvaluationRunRecord:
    id: uuid.UUID
    organization_id: uuid.UUID
    case_id: uuid.UUID
    build_id: uuid.UUID
    runtime_evaluation_run_id: str
    status: str
    deterministic_pass: bool
    review_pass: bool
    case_revision: int
    reasons: tuple[str, ...]
    created_at: datetime


@dataclass(frozen=True)
class EvaluationRunAttemptRecord:
    id: uuid.UUID
    organization_id: uuid.UUID
    agent_id: uuid.UUID
    evaluation_set_id: uuid.UUID
    case_id: uuid.UUID
    build_id: uuid.UUID
    case_revision: int
    job_id: uuid.UUID | None
    retry_of_attempt_id: uuid.UUID | None
    status: str
    failure_code: str | None
    failure_message: str | None
    runtime_evaluation_run_id: str | None
    created_at: datetime
    updated_at: datetime
    completed_at: datetime | None


@dataclass(frozen=True)
class EligibilityRecord:
    id: uuid.UUID
    organization_id: uuid.UUID
    agent_id: uuid.UUID
    build_id: uuid.UUID
    runtime_build_hash: str
    eligible: bool
    supporting_evaluation_run_ids: tuple[str, ...]
    reasons: tuple[str, ...]
    created_at: datetime
