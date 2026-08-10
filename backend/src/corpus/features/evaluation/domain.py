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
    created_at: datetime
    updated_at: datetime


@dataclass(frozen=True)
class EvaluationCaseRecord:
    id: uuid.UUID
    organization_id: uuid.UUID
    evaluation_set_id: uuid.UUID
    build_id: uuid.UUID
    runtime_case_id: str
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
    reasons: tuple[str, ...]
    created_at: datetime


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

