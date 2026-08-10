from __future__ import annotations

from pathlib import Path

import pytest
from sqlalchemy import inspect

from corpus.persistence import CorpusDatabase
from corpus.persistence.migrations import upgrade_database


@pytest.mark.asyncio
async def test_shared_infrastructure_migration_creates_exact_tables(
    tmp_path: Path,
) -> None:
    database_url = f"sqlite+aiosqlite:///{(tmp_path / 'corpus.sqlite3').as_posix()}"
    await upgrade_database(database_url)
    database = CorpusDatabase(database_url)
    try:
        async with database.engine.connect() as connection:
            schema = await connection.run_sync(
                lambda sync: {
                    table: {column["name"] for column in inspect(sync).get_columns(table)}
                    for table in (
                        "durable_jobs",
                        "durable_job_events",
                        "credential_references",
                    )
                }
            )
        assert schema["durable_jobs"] == {
            "id",
            "owner_id",
            "job_type",
            "state",
            "payload",
            "attempt_count",
            "max_attempts",
            "error_code",
            "error_message",
            "result",
            "created_at",
            "updated_at",
            "started_at",
            "completed_at",
        }
        assert schema["durable_job_events"] == {
            "id",
            "job_id",
            "event_type",
            "state",
            "details",
            "created_at",
        }
        assert schema["credential_references"] == {
            "id",
            "owner_id",
            "label",
            "kind",
            "version",
            "ciphertext",
            "created_at",
            "updated_at",
        }
        await database.verify_revision("0012_builder_navgraph")
    finally:
        await database.close()
