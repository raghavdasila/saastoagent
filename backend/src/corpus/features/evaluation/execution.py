from __future__ import annotations

import uuid

from corpus.jobs.repository import SqlAlchemyDurableJobRepository

from .ports import EvaluationConflict, EvaluationRepository, EvaluationUnavailable
from .service import EvaluationService


class EvaluationRunProcessor:
    """Execute one queued Evaluation attempt against its exact persisted lineage."""

    def __init__(
        self,
        jobs: SqlAlchemyDurableJobRepository,
        evaluations: EvaluationRepository,
        service: EvaluationService,
    ) -> None:
        self.jobs = jobs
        self.evaluations = evaluations
        self.service = service

    async def process(self, job_id: uuid.UUID) -> dict[str, object]:
        job = await self.jobs.mark_running(job_id=job_id)
        attempt_id: uuid.UUID | None = None
        try:
            if job.job_type != "evaluation.run_case":
                raise ValueError("The durable job type is not owned by Evaluation execution.")
            agent_id = uuid.UUID(str(job.payload.get("agent_id", "")))
            case_id = uuid.UUID(str(job.payload.get("case_id", "")))
            case_revision = int(job.payload.get("case_revision", 0))
            attempt_id = uuid.UUID(str(job.payload.get("attempt_id", "")))
            if case_revision < 1:
                raise ValueError("The queued Evaluation case revision is invalid.")
            _evaluation_set, case, attempt = await self.evaluations.get_run_attempt(
                job.owner_id, agent_id, attempt_id
            )
            if (
                attempt.case_id != case_id
                or attempt.case_revision != case_revision
                or attempt.build_id != case.build_id
            ):
                raise EvaluationConflict(
                    "The queued Evaluation attempt changed its exact lineage."
                )
            await self.evaluations.mark_run_attempt_running(
                job.owner_id, attempt.id, job.id
            )
            stored = await self.service.execute_case(
                job.owner_id,
                agent_id,
                case_id,
                expected_case_revision=case_revision,
            )
            await self.evaluations.mark_run_attempt_succeeded(
                job.owner_id, attempt.id, stored.runtime_evaluation_run_id
            )
            result: dict[str, object] = {
                "attempt_id": str(attempt.id),
                "agent_id": str(agent_id),
                "case_id": str(case_id),
                "case_revision": case_revision,
                "build_id": str(case.build_id),
                "runtime_evaluation_run_id": stored.runtime_evaluation_run_id,
                "status": stored.status,
            }
            await self.jobs.mark_succeeded(job_id=job.id, result=result)
            return result
        except Exception as error:
            public_message = _public_failure(error)
            if attempt_id is not None:
                try:
                    await self.evaluations.mark_run_attempt_failed(
                        job.owner_id,
                        attempt_id,
                        code="evaluation_run_failed",
                        message=public_message,
                    )
                except (EvaluationConflict, EvaluationUnavailable):
                    pass
            await self.jobs.mark_failed(
                job_id=job.id,
                error_code="evaluation_run_failed",
                error_message=public_message,
            )
            raise


def _public_failure(error: Exception) -> str:
    if isinstance(error, (EvaluationConflict, EvaluationUnavailable, ValueError)):
        message = str(error).strip()
        if message:
            return message[:500]
    return "The queued evaluation run failed."


__all__ = ["EvaluationRunProcessor"]
