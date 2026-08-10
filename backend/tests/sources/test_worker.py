from __future__ import annotations

import asyncio
import uuid
from datetime import UTC, datetime
from pathlib import Path

from huey import SqliteHuey

from corpus.auth.models import Organization
from corpus.features.sources import LocalSourceRepository, SourceJobProcessor, SourceState
from corpus.features.sources.tasks import register_source_processing_task
from corpus.jobs import DurableJobState, SqlAlchemyDurableJobRepository
from corpus.persistence import CorpusDatabase


class RecordingConnector:
    key = "api"

    def ingest(self, *, input_path: Path, artifact_dir: Path):
        assert input_path.read_text(encoding="utf-8") == "openapi: 3.0.3"
        artifact_dir.mkdir(parents=True, exist_ok=True)
        (artifact_dir / "graph.json").write_text("{}", encoding="utf-8")
        return {"endpoint_count": 1}


def test_feature_owned_huey_task_processes_the_linked_revision(tmp_path: Path) -> None:
    database = CorpusDatabase(
        f"sqlite+aiosqlite:///{(tmp_path / 'corpus.sqlite3').as_posix()}"
    )
    jobs = SqlAlchemyDurableJobRepository(database)
    sources = LocalSourceRepository(tmp_path / "sources")
    owner_id = uuid.uuid4()

    async def prepare():
        await database.create_schema_for_tests()
        async with database.session() as session:
            async with session.begin():
                session.add(
                    Organization(
                        id=owner_id,
                        name="Owner Workspace",
                        slug=f"owner-{owner_id.hex[:8]}",
                        created_at=datetime.now(UTC),
                    )
                )
        prepared = sources.begin_source(
            owner_key=str(owner_id),
            connector_key="api",
            display_name="Widgets",
            original_filename="widgets.yaml",
            content=b"openapi: 3.0.3",
        )
        job = await jobs.create(
            owner_id=owner_id,
            job_type="sources.process_api_revision",
            payload={
                "source_id": prepared.source.source_id,
                "revision_id": prepared.revision.revision_id,
            },
            max_attempts=3,
        )
        sources.attach_job(
            owner_key=str(owner_id),
            source_id=prepared.source.source_id,
            revision_id=prepared.revision.revision_id,
            job_id=str(job.id),
        )
        return prepared, job

    prepared, job = asyncio.run(prepare())
    huey = SqliteHuey(
        "source-worker-test",
        filename=str(tmp_path / "queue.sqlite3"),
        immediate=True,
    )
    task = register_source_processing_task(
        huey,
        SourceJobProcessor(sources, jobs, connectors=(RecordingConnector(),)),
    )

    result = task(str(job.id)).get(blocking=True)

    assert result == {"endpoint_count": 1}
    source = sources.get(
        owner_key=str(owner_id), source_id=prepared.source.source_id
    )
    assert source.revision.state is SourceState.READY
    persisted_job = asyncio.run(jobs.get(owner_id=owner_id, job_id=job.id))
    assert persisted_job.state is DurableJobState.SUCCEEDED
    assert persisted_job.result == {
        "source_id": prepared.source.source_id,
        "revision_id": prepared.revision.revision_id,
        "summary": {"endpoint_count": 1},
    }
    asyncio.run(database.close())
