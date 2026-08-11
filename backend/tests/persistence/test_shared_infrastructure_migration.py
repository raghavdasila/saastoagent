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
                        "agent_deployments",
                    )
                }
            )
            deployment_constraints = await connection.run_sync(
                lambda sync: {
                    "unique": {
                        tuple(item["column_names"])
                        for item in inspect(sync).get_unique_constraints(
                            "agent_deployments"
                        )
                    },
                    "checks": {
                        item["name"]: item["sqltext"]
                        for item in inspect(sync).get_check_constraints(
                            "agent_deployments"
                        )
                    },
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
        assert {
            "job_id", "retry_of_deployment_id", "active_channel_id"
        } <= schema["agent_deployments"]
        assert ("job_id",) in deployment_constraints["unique"]
        assert (
            "organization_id", "active_channel_id"
        ) in deployment_constraints["unique"]
        assert "queued" in deployment_constraints["checks"][
            "ck_agent_deployment_status"
        ]
        assert "running" in deployment_constraints["checks"][
            "ck_agent_deployment_status"
        ]
        await database.verify_revision("0018_deployment_lifecycle")
    finally:
        await database.close()
