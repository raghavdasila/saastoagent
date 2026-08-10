from __future__ import annotations

import uuid
from datetime import UTC, datetime
from typing import Any, Mapping

from sqlalchemy import select

from corpus.persistence import CorpusDatabase

from .domain import DurableJobRecord, DurableJobState
from .models import DurableJob, DurableJobEvent


class DurableJobNotFound(LookupError):
    pass


class DurableJobStateConflict(RuntimeError):
    pass


class SqlAlchemyDurableJobRepository:
    def __init__(self, database: CorpusDatabase) -> None:
        self.database = database

    async def create(
        self,
        *,
        owner_id: uuid.UUID,
        job_type: str,
        payload: Mapping[str, Any],
        max_attempts: int,
    ) -> DurableJobRecord:
        if not job_type.strip():
            raise ValueError("job_type cannot be empty")
        if max_attempts < 1:
            raise ValueError("max_attempts must be at least one")
        now = datetime.now(UTC)
        job = DurableJob(
            owner_id=owner_id,
            job_type=job_type,
            state=DurableJobState.QUEUED,
            payload=dict(payload),
            attempt_count=0,
            max_attempts=max_attempts,
            created_at=now,
            updated_at=now,
        )
        async with self.database.session() as session:
            async with session.begin():
                session.add(job)
                await session.flush()
                session.add(_event(job.id, "enqueued", DurableJobState.QUEUED, now))
        return _record(job)

    async def get(
        self, *, owner_id: uuid.UUID, job_id: uuid.UUID
    ) -> DurableJobRecord:
        async with self.database.session() as session:
            job = await session.scalar(
                select(DurableJob).where(
                    DurableJob.id == job_id, DurableJob.owner_id == owner_id
                )
            )
        if job is None:
            raise DurableJobNotFound("The requested job does not exist.")
        return _record(job)

    async def mark_running(self, *, job_id: uuid.UUID) -> DurableJobRecord:
        async with self.database.session() as session:
            async with session.begin():
                job = await self._locked(session, job_id)
                if job.state != DurableJobState.QUEUED:
                    raise DurableJobStateConflict("Only a queued job can start.")
                now = datetime.now(UTC)
                job.state = DurableJobState.RUNNING
                job.attempt_count += 1
                job.started_at = now
                job.completed_at = None
                job.updated_at = now
                session.add(_event(job.id, "started", job.state, now))
        return _record(job)

    async def mark_succeeded(
        self, *, job_id: uuid.UUID, result: Mapping[str, Any]
    ) -> DurableJobRecord:
        async with self.database.session() as session:
            async with session.begin():
                job = await self._locked(session, job_id)
                if job.state != DurableJobState.RUNNING:
                    raise DurableJobStateConflict("Only a running job can succeed.")
                now = datetime.now(UTC)
                job.state = DurableJobState.SUCCEEDED
                job.result = dict(result)
                job.error_code = None
                job.error_message = None
                job.updated_at = now
                job.completed_at = now
                session.add(_event(job.id, "succeeded", job.state, now))
        return _record(job)

    async def mark_failed(
        self,
        *,
        job_id: uuid.UUID,
        error_code: str,
        error_message: str,
    ) -> DurableJobRecord:
        async with self.database.session() as session:
            async with session.begin():
                job = await self._locked(session, job_id)
                if job.state not in {DurableJobState.QUEUED, DurableJobState.RUNNING}:
                    raise DurableJobStateConflict(
                        "Only a queued or running job can fail."
                    )
                now = datetime.now(UTC)
                job.state = DurableJobState.FAILED
                job.error_code = error_code
                job.error_message = error_message
                job.updated_at = now
                job.completed_at = now
                session.add(
                    _event(
                        job.id,
                        "failed",
                        job.state,
                        now,
                        {"error_code": error_code},
                    )
                )
        return _record(job)

    async def prepare_retry(
        self, *, owner_id: uuid.UUID, job_id: uuid.UUID
    ) -> DurableJobRecord:
        async with self.database.session() as session:
            async with session.begin():
                job = await session.scalar(
                    select(DurableJob)
                    .where(DurableJob.id == job_id, DurableJob.owner_id == owner_id)
                    .with_for_update()
                )
                if job is None:
                    raise DurableJobNotFound("The requested job does not exist.")
                if job.state != DurableJobState.FAILED:
                    raise DurableJobStateConflict("Only a failed job can be retried.")
                if job.attempt_count >= job.max_attempts:
                    raise DurableJobStateConflict("This job has no retry attempts left.")
                now = datetime.now(UTC)
                job.state = DurableJobState.QUEUED
                job.error_code = None
                job.error_message = None
                job.result = None
                job.updated_at = now
                job.completed_at = None
                session.add(_event(job.id, "retry_requested", job.state, now))
        return _record(job)

    async def _locked(self, session, job_id: uuid.UUID) -> DurableJob:
        job = await session.scalar(
            select(DurableJob).where(DurableJob.id == job_id).with_for_update()
        )
        if job is None:
            raise DurableJobNotFound("The requested job does not exist.")
        return job


def _event(
    job_id: uuid.UUID,
    event_type: str,
    state: DurableJobState,
    created_at: datetime,
    details: Mapping[str, Any] | None = None,
) -> DurableJobEvent:
    return DurableJobEvent(
        job_id=job_id,
        event_type=event_type,
        state=state,
        details=dict(details or {}),
        created_at=created_at,
    )


def _record(job: DurableJob) -> DurableJobRecord:
    return DurableJobRecord(
        id=job.id,
        owner_id=job.owner_id,
        job_type=job.job_type,
        state=job.state,
        payload=dict(job.payload),
        attempt_count=job.attempt_count,
        max_attempts=job.max_attempts,
        error_code=job.error_code,
        error_message=job.error_message,
        result=dict(job.result) if job.result is not None else None,
        created_at=job.created_at,
        updated_at=job.updated_at,
        started_at=job.started_at,
        completed_at=job.completed_at,
    )


__all__ = [
    "DurableJobNotFound",
    "DurableJobStateConflict",
    "SqlAlchemyDurableJobRepository",
]
