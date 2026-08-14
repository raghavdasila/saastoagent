from __future__ import annotations

import uuid
from dataclasses import dataclass
from typing import Mapping, Protocol

from corpus.shared.agent_execution import (
    EligibilityProjection,
    EvaluationCaseProjection,
    EvaluationRunProjection,
)

from .domain import (
    EvaluationCaseRecord,
    EvaluationRunAttemptRecord,
    EvaluationRunRecord,
    EvaluationSetRecord,
    EligibilityRecord,
)


class EvaluationUnavailable(RuntimeError):
    pass


class EvaluationConflict(RuntimeError):
    pass


@dataclass(frozen=True)
class EvaluationGenerationBuild:
    id: uuid.UUID
    status: str
    runtime_build_hash: str | None
    source_bindings: tuple[Mapping[str, object], ...]


@dataclass(frozen=True)
class EvaluationGeneratedCase:
    task_id: str
    query: str
    category: str
    expected_operation_ids: tuple[str, ...]


@dataclass(frozen=True)
class EvaluationGeneratedBatch:
    status: str
    accepted_count: int
    expected_count: int
    generator_model: str
    generator_model_digest: str
    reviewer_model: str
    reviewer_model_digest: str
    cases: tuple[EvaluationGeneratedCase, ...]


class EvaluationGenerationGateway(Protocol):
    """Application-composed access to one immutable build and case generator."""

    async def get_build(
        self,
        organization_id: uuid.UUID,
        agent_id: uuid.UUID,
        build_id: uuid.UUID,
    ) -> EvaluationGenerationBuild: ...

    def generate(
        self,
        *,
        binding: Mapping[str, object],
        evalset_id: str,
        categories: tuple[str, ...],
    ) -> EvaluationGeneratedBatch: ...


class EvaluationRuntimeGateway(Protocol):
    def promote(self, *, tenant_id: str, run_id: str, message: str, expected_operation_ids: tuple[str, ...], required_response_fields: tuple[str, ...], require_write_verification: bool) -> EvaluationCaseProjection: ...
    def evaluate(self, tenant_id: str, runtime_case_id: str) -> EvaluationRunProjection: ...
    def eligibility(self, runtime_build_hash: str, runtime_case_ids: tuple[str, ...]) -> EligibilityProjection: ...


class EvaluationRepository(Protocol):
    async def create_set(self, organization_id: uuid.UUID, agent_id: uuid.UUID, build_id: uuid.UUID, name: str) -> EvaluationSetRecord: ...
    async def get_set(self, organization_id: uuid.UUID, agent_id: uuid.UUID, evaluation_set_id: uuid.UUID) -> EvaluationSetRecord: ...
    async def list_sets(self, organization_id: uuid.UUID, agent_id: uuid.UUID) -> tuple[EvaluationSetRecord, ...]: ...
    async def add_case(self, organization_id: uuid.UUID, evaluation_set: EvaluationSetRecord, *, runtime: EvaluationCaseProjection, source_kind: str, source_record_id: str, title: str, message: str, category: str, difficulty: str, expected_operation_ids: tuple[str, ...], required_response_fields: tuple[str, ...], require_write_verification: bool, mandatory: bool) -> EvaluationCaseRecord: ...
    async def add_generated_case(self, organization_id: uuid.UUID, evaluation_set: EvaluationSetRecord, *, task_id: str, title: str, message: str, category: str, difficulty: str, expected_operation_ids: tuple[str, ...], mandatory: bool) -> EvaluationCaseRecord: ...
    async def set_generation_job(self, organization_id: uuid.UUID, evaluation_set_id: uuid.UUID, job_id: uuid.UUID) -> EvaluationSetRecord: ...
    async def mark_generation_running(self, organization_id: uuid.UUID, evaluation_set_id: uuid.UUID) -> EvaluationSetRecord: ...
    async def mark_generation_ready(self, organization_id: uuid.UUID, evaluation_set_id: uuid.UUID, summary: dict[str, object]) -> EvaluationSetRecord: ...
    async def mark_generation_failed(self, organization_id: uuid.UUID, evaluation_set_id: uuid.UUID, *, code: str, message: str) -> EvaluationSetRecord: ...
    async def edit_case(self, organization_id: uuid.UUID, agent_id: uuid.UUID, case_id: uuid.UUID, *, expected_revision: int, title: str, category: str, difficulty: str, mandatory: bool) -> EvaluationCaseRecord: ...
    async def remove_case(self, organization_id: uuid.UUID, agent_id: uuid.UUID, case_id: uuid.UUID, *, expected_revision: int) -> EvaluationCaseRecord: ...
    async def link_generated_run(self, organization_id: uuid.UUID, case_id: uuid.UUID, sandbox_run_id: uuid.UUID) -> EvaluationCaseRecord: ...
    async def bind_generated_runtime(self, organization_id: uuid.UUID, case_id: uuid.UUID, runtime: EvaluationCaseProjection) -> EvaluationCaseRecord: ...
    async def get_case(self, organization_id: uuid.UUID, agent_id: uuid.UUID, case_id: uuid.UUID) -> tuple[EvaluationSetRecord, EvaluationCaseRecord]: ...
    async def cases(self, organization_id: uuid.UUID, evaluation_set_id: uuid.UUID) -> tuple[EvaluationCaseRecord, ...]: ...
    async def cases_by_source(self, organization_id: uuid.UUID, *, source_kind: str, source_record_id: str) -> tuple[EvaluationCaseRecord, ...]: ...
    async def add_run(self, organization_id: uuid.UUID, case: EvaluationCaseRecord, runtime: EvaluationRunProjection) -> EvaluationRunRecord: ...
    async def runs(self, organization_id: uuid.UUID, evaluation_set_id: uuid.UUID) -> tuple[EvaluationRunRecord, ...]: ...
    async def create_run_attempt(self, organization_id: uuid.UUID, agent_id: uuid.UUID, case_id: uuid.UUID, *, retry_of_attempt_id: uuid.UUID | None = None) -> EvaluationRunAttemptRecord: ...
    async def link_run_attempt_job(self, organization_id: uuid.UUID, attempt_id: uuid.UUID, job_id: uuid.UUID) -> EvaluationRunAttemptRecord: ...
    async def get_run_attempt(self, organization_id: uuid.UUID, agent_id: uuid.UUID, attempt_id: uuid.UUID) -> tuple[EvaluationSetRecord, EvaluationCaseRecord, EvaluationRunAttemptRecord]: ...
    async def mark_run_attempt_running(self, organization_id: uuid.UUID, attempt_id: uuid.UUID, job_id: uuid.UUID) -> EvaluationRunAttemptRecord: ...
    async def mark_run_attempt_succeeded(self, organization_id: uuid.UUID, attempt_id: uuid.UUID, runtime_evaluation_run_id: str) -> EvaluationRunAttemptRecord: ...
    async def mark_run_attempt_failed(self, organization_id: uuid.UUID, attempt_id: uuid.UUID, *, code: str, message: str) -> EvaluationRunAttemptRecord: ...
    async def run_attempts(self, organization_id: uuid.UUID, evaluation_set_id: uuid.UUID) -> tuple[EvaluationRunAttemptRecord, ...]: ...
    async def add_eligibility(self, organization_id: uuid.UUID, agent_id: uuid.UUID, build_id: uuid.UUID, runtime_build_hash: str, runtime: EligibilityProjection) -> EligibilityRecord: ...
    async def latest_eligibility(self, organization_id: uuid.UUID, agent_id: uuid.UUID, build_id: uuid.UUID) -> EligibilityRecord | None: ...
