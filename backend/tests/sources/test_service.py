from __future__ import annotations

import uuid
from datetime import UTC, datetime
from pathlib import Path

import pytest

from corpus.features.sources import LocalSourceRepository, SourceService, SourceState
from corpus.features.sources.connectors.api import ApiSourceConnector, SourceUpload
from corpus.app.toolrouter_source_adapter import ToolRouterApiSourceEngine
from corpus.integrations.toolrouter import ToolRouterAdapter, ToolRouterSettings
from corpus.jobs import DurableJobRecord, DurableJobState
from backend.tests.integrations.toolrouter.conftest import (
    KeywordEmbeddingProvider,
    write_openapi_fixture,
)


class RecordingJobs:
    def __init__(self) -> None:
        self.job_id = uuid.uuid4()
        self.enqueued: list[dict[str, object]] = []
        self.retried: list[uuid.UUID] = []

    async def enqueue(self, **kwargs) -> DurableJobRecord:
        self.enqueued.append(kwargs)
        return self._record(DurableJobState.QUEUED)

    async def retry(self, **kwargs) -> DurableJobRecord:
        self.retried.append(kwargs["job_id"])
        return self._record(DurableJobState.QUEUED)

    async def status(self, **kwargs) -> DurableJobRecord:
        return self._record(DurableJobState.QUEUED)

    def _record(self, state: DurableJobState) -> DurableJobRecord:
        now = datetime.now(UTC)
        return DurableJobRecord(
            id=self.job_id,
            owner_id=uuid.UUID("00000000-0000-0000-0000-000000000001"),
            job_type="sources.process_api_revision",
            state=state,
            payload={},
            attempt_count=0,
            max_attempts=3,
            error_code=None,
            error_message=None,
            result=None,
            created_at=now,
            updated_at=now,
            started_at=None,
            completed_at=None,
        )


def _service(tmp_path: Path) -> tuple[SourceService, RecordingJobs]:
    jobs = RecordingJobs()
    service = SourceService(
        LocalSourceRepository(tmp_path / "sources"),
        connectors=(
            ApiSourceConnector(
                ToolRouterApiSourceEngine(
                    ToolRouterAdapter(
                        ToolRouterSettings(),
                        embedding_provider=KeywordEmbeddingProvider(),
                    )
                ),
                max_upload_bytes=20 * 1024 * 1024,
            ),
        ),
        jobs=jobs,
    )
    return service, jobs


@pytest.mark.asyncio
async def test_service_accepts_revision_before_explicit_processing_job(
    tmp_path: Path,
) -> None:
    service, jobs = _service(tmp_path)
    source_file = write_openapi_fixture(tmp_path / "widgets.json")
    owner_id = uuid.UUID("00000000-0000-0000-0000-000000000001")

    created = await service.create_source(
        owner_id=owner_id,
        connector_key="api",
        display_name="Widget API",
        upload=SourceUpload(
            filename="widgets.json",
            content_type="application/json",
            content=source_file.read_bytes(),
            description_filename="widgets.md",
            description_content_type="text/markdown",
            description_content=b"# Widget API\nOwner notes.",
        ),
    )

    assert created.revision.state is SourceState.ACCEPTED
    assert created.revision.job_id is None
    assert created.revision.description_filename == "widgets.md"
    assert jobs.enqueued == []

    queued = await service.process_source(owner_id=owner_id, source_id=created.source_id)

    assert queued.revision.state is SourceState.QUEUED
    assert queued.revision.job_id == str(jobs.job_id)
    assert jobs.enqueued[0]["payload"] == {
        "source_id": created.source_id,
        "revision_id": created.revision.revision_id,
    }
    assert service.list_sources(owner_key=str(owner_id)) == (queued,)
    assert service.list_sources(
        owner_key="00000000-0000-0000-0000-000000000002"
    ) == ()


@pytest.mark.asyncio
async def test_service_retries_only_the_failed_linked_job(tmp_path: Path) -> None:
    service, jobs = _service(tmp_path)
    source_file = write_openapi_fixture(tmp_path / "widgets.json")
    owner_id = uuid.UUID("00000000-0000-0000-0000-000000000001")
    created = await service.create_source(
        owner_id=owner_id,
        connector_key="api",
        display_name="Widget API",
        upload=SourceUpload(
            filename="widgets.json",
            content_type="application/json",
            content=source_file.read_bytes(),
        ),
    )
    queued = await service.process_source(owner_id=owner_id, source_id=created.source_id)
    service.repository.mark_failed(
        owner_key=str(owner_id),
        source_id=created.source_id,
        revision_id=queued.revision.revision_id,
        failure_code="source_processing_failed",
        failure_message="ToolRouter rejected the definition.",
    )

    retried = await service.retry_processing(
        owner_id=owner_id, source_id=created.source_id
    )

    assert retried.revision.state is SourceState.QUEUED
    assert jobs.retried == [jobs.job_id]
