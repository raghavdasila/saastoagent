from __future__ import annotations

import uuid
from typing import Any, Mapping

from huey import SqliteHuey

from .domain import DurableJobRecord
from .repository import SqlAlchemyDurableJobRepository


class DurableJobEnqueueError(RuntimeError):
    def __init__(self, message: str, *, job_id: uuid.UUID) -> None:
        super().__init__(message)
        self.job_id = job_id


class HueyDurableJobPort:
    """Persists Corpus job truth before submitting an opaque ID to Huey."""

    def __init__(
        self,
        repository: SqlAlchemyDurableJobRepository,
        huey: SqliteHuey,
        task: Any,
    ) -> None:
        self.repository = repository
        self.huey = huey
        self.task = task

    async def enqueue(
        self,
        *,
        owner_id: uuid.UUID,
        job_type: str,
        payload: Mapping[str, Any],
        max_attempts: int = 1,
    ) -> DurableJobRecord:
        job = await self.repository.create(
            owner_id=owner_id,
            job_type=job_type,
            payload=payload,
            max_attempts=max_attempts,
        )
        await self._submit_or_fail(job)
        return await self.repository.get(owner_id=owner_id, job_id=job.id)

    async def status(
        self, *, owner_id: uuid.UUID, job_id: uuid.UUID
    ) -> DurableJobRecord:
        return await self.repository.get(owner_id=owner_id, job_id=job_id)

    async def retry(
        self, *, owner_id: uuid.UUID, job_id: uuid.UUID
    ) -> DurableJobRecord:
        job = await self.repository.prepare_retry(owner_id=owner_id, job_id=job_id)
        await self._submit_or_fail(job)
        return await self.repository.get(owner_id=owner_id, job_id=job.id)

    async def _submit_or_fail(self, job: DurableJobRecord) -> None:
        try:
            task = self.task.s(str(job.id))
            task.id = f"corpus-job:{job.id}:attempt:{job.attempt_count + 1}"
            self.huey.enqueue(task)
        except Exception as error:
            await self.repository.mark_failed(
                job_id=job.id,
                error_code="queue_unavailable",
                error_message="The durable job queue rejected the request.",
            )
            raise DurableJobEnqueueError(
                "The durable job queue rejected the request.",
                job_id=job.id,
            ) from error


__all__ = ["DurableJobEnqueueError", "HueyDurableJobPort"]
