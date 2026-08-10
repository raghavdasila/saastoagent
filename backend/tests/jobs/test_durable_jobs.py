from __future__ import annotations

import uuid
from datetime import UTC, datetime
from pathlib import Path

import pytest
from huey import SqliteHuey
from sqlalchemy import func, select

from corpus.auth.models import Organization
from corpus.jobs import (
    DurableJobEnqueueError,
    DurableJobNotFound,
    DurableJobState,
    DurableJobStateConflict,
    HueyDurableJobPort,
    SqlAlchemyDurableJobRepository,
)
from corpus.jobs.models import DurableJobEvent
from corpus.persistence import CorpusDatabase


async def _database(tmp_path: Path) -> tuple[CorpusDatabase, uuid.UUID, uuid.UUID]:
    database = CorpusDatabase(
        f"sqlite+aiosqlite:///{(tmp_path / 'corpus.sqlite3').as_posix()}"
    )
    await database.create_schema_for_tests()
    first = uuid.uuid4()
    second = uuid.uuid4()
    async with database.session() as session:
        async with session.begin():
            session.add_all(
                (
                    Organization(
                        id=first,
                        name="First",
                        slug=f"first-{first}",
                        created_at=datetime.now(UTC),
                    ),
                    Organization(
                        id=second,
                        name="Second",
                        slug=f"second-{second}",
                        created_at=datetime.now(UTC),
                    ),
                )
            )
    return database, first, second


def _queue(tmp_path: Path):
    huey = SqliteHuey(
        "corpus-test",
        filename=str(tmp_path / "huey.sqlite3"),
        immediate=False,
        results=True,
    )

    @huey.task(retries=0)
    def execute(job_id: str) -> str:
        return job_id

    return huey, execute


@pytest.mark.asyncio
async def test_huey_port_persists_before_enqueue_and_is_owner_scoped(
    tmp_path: Path,
) -> None:
    database, owner_id, other_owner = await _database(tmp_path)
    huey, task = _queue(tmp_path)
    repository = SqlAlchemyDurableJobRepository(database)
    port = HueyDurableJobPort(repository, huey, task)
    try:
        job = await port.enqueue(
            owner_id=owner_id,
            job_type="source.process",
            payload={"source_id": "source-1"},
            max_attempts=2,
        )

        assert job.state == DurableJobState.QUEUED
        assert job.attempt_count == 0
        assert job.payload == {"source_id": "source-1"}
        assert [pending.id for pending in huey.pending()] == [
            f"corpus-job:{job.id}:attempt:1"
        ]
        with pytest.raises(DurableJobNotFound):
            await port.status(owner_id=other_owner, job_id=job.id)
    finally:
        await database.close()


@pytest.mark.asyncio
async def test_failed_job_has_explicit_retry_state_and_lifecycle_records(
    tmp_path: Path,
) -> None:
    database, owner_id, _ = await _database(tmp_path)
    huey, task = _queue(tmp_path)
    repository = SqlAlchemyDurableJobRepository(database)
    port = HueyDurableJobPort(repository, huey, task)
    try:
        job = await port.enqueue(
            owner_id=owner_id,
            job_type="source.process",
            payload={"revision_id": "revision-1"},
            max_attempts=2,
        )
        running = await repository.mark_running(job_id=job.id)
        assert running.attempt_count == 1
        failed = await repository.mark_failed(
            job_id=job.id,
            error_code="processing_failed",
            error_message="Processing failed safely.",
        )
        assert failed.state == DurableJobState.FAILED
        retried = await port.retry(owner_id=owner_id, job_id=job.id)
        assert retried.state == DurableJobState.QUEUED
        assert retried.error_code is None

        await repository.mark_running(job_id=job.id)
        await repository.mark_failed(
            job_id=job.id,
            error_code="processing_failed",
            error_message="Processing failed safely.",
        )
        with pytest.raises(DurableJobStateConflict, match="no retry attempts"):
            await port.retry(owner_id=owner_id, job_id=job.id)

        async with database.session() as session:
            event_count = await session.scalar(
                select(func.count(DurableJobEvent.id)).where(
                    DurableJobEvent.job_id == job.id
                )
            )
        assert event_count == 6
    finally:
        await database.close()


@pytest.mark.asyncio
async def test_queue_rejection_is_persisted_as_failure_without_fallback(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    database, owner_id, _ = await _database(tmp_path)
    huey, task = _queue(tmp_path)
    repository = SqlAlchemyDurableJobRepository(database)
    port = HueyDurableJobPort(repository, huey, task)

    def reject(_task):
        raise OSError("queue is unavailable")

    monkeypatch.setattr(huey, "enqueue", reject)
    try:
        with pytest.raises(DurableJobEnqueueError, match="rejected"):
            await port.enqueue(
                owner_id=owner_id,
                job_type="source.process",
                payload={"source_id": "source-1"},
            )
        async with database.session() as session:
            failed = await session.scalar(
                select(func.count()).select_from(DurableJobEvent).where(
                    DurableJobEvent.event_type == "failed"
                )
            )
        assert failed == 1
    finally:
        await database.close()
