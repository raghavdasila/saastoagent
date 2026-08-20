from __future__ import annotations

import sqlite3
import uuid
from pathlib import Path

import pytest
from sqlalchemy import inspect

from corpus.persistence import CorpusDatabase
from corpus.persistence.migrations import upgrade_database


@pytest.mark.asyncio
async def test_agent_source_attachment_head_has_exact_identity_only_schema(
    tmp_path: Path,
) -> None:
    database_url = f"sqlite+aiosqlite:///{(tmp_path / 'attachments.sqlite3').as_posix()}"
    await upgrade_database(database_url)
    database = CorpusDatabase(database_url)
    try:
        async with database.engine.connect() as connection:
            schema = await connection.run_sync(_attachment_schema)
            version_foreign_keys = await connection.run_sync(_agent_version_foreign_keys)
        assert schema == {
            "columns": {
                "id",
                "organization_id",
                "agent_id",
                "source_id",
                "source_revision_id",
                "attached_at",
            },
            "unique_constraints": {
                ("uq_agent_source_attachment", ("agent_id", "source_id"))
            },
            "foreign_keys": {
                (("organization_id",), "organizations", ("id",), "CASCADE"),
                (("agent_id",), "agents", ("id",), "RESTRICT"),
            },
            "indexes": {
                (
                    "ix_agent_source_attachments_owner_agent",
                    ("organization_id", "agent_id", "attached_at"),
                    False,
                )
            },
        }
        assert version_foreign_keys == {
            (("agent_id",), "agents", ("id",), "CASCADE")
        }
        await database.verify_revision("0020_sandbox_deployment_mode")
    finally:
        await database.close()


@pytest.mark.asyncio
async def test_0005_removes_display_copy_and_preserves_attachment_identity(
    tmp_path: Path,
) -> None:
    path = tmp_path / "forward.sqlite3"
    database_url = f"sqlite+aiosqlite:///{path.as_posix()}"
    await upgrade_database(database_url, "0004_agent_source_attachments")
    organization_id = uuid.uuid4().hex
    agent_id = uuid.uuid4().hex
    attachment_id = uuid.uuid4().hex
    with sqlite3.connect(path) as connection:
        connection.execute(
            "INSERT INTO organizations (id, name, slug, created_at) VALUES (?, ?, ?, ?)",
            (organization_id, "Migration Workspace", f"migration-{organization_id}", "2026-08-07 00:00:00"),
        )
        connection.execute(
            """INSERT INTO agents
            (id, organization_id, name, name_key, lifecycle, current_version, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                agent_id,
                organization_id,
                "Migration Agent",
                "migration agent",
                "ACTIVE",
                1,
                "2026-08-07 00:00:00",
                "2026-08-07 00:00:00",
            ),
        )
        connection.execute(
            """INSERT INTO agent_source_attachments
            (id, organization_id, agent_id, source_id, source_revision_id, source_display_name, attached_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)""",
            (
                attachment_id,
                organization_id,
                agent_id,
                "source-ready-001",
                "revision-ready01",
                "Stale copied label",
                "2026-08-07 00:00:00",
            ),
        )
        connection.commit()

    await upgrade_database(database_url)

    with sqlite3.connect(path) as connection:
        columns = {
            row[1]
            for row in connection.execute(
                "PRAGMA table_info(agent_source_attachments)"
            )
        }
        identity = connection.execute(
            "SELECT source_id, source_revision_id FROM agent_source_attachments WHERE id = ?",
            (attachment_id,),
        ).fetchone()
    assert "source_display_name" not in columns
    assert identity == ("source-ready-001", "revision-ready01")


def _attachment_schema(connection) -> dict[str, set[tuple] | set[str]]:
    inspector = inspect(connection)
    return {
        "columns": {
            column["name"]
            for column in inspector.get_columns("agent_source_attachments")
        },
        "unique_constraints": {
            (constraint["name"], tuple(constraint["column_names"]))
            for constraint in inspector.get_unique_constraints(
                "agent_source_attachments"
            )
        },
        "foreign_keys": {
            (
                tuple(foreign_key["constrained_columns"]),
                foreign_key["referred_table"],
                tuple(foreign_key["referred_columns"]),
                foreign_key["options"].get("ondelete"),
            )
            for foreign_key in inspector.get_foreign_keys(
                "agent_source_attachments"
            )
        },
        "indexes": {
            (
                index["name"],
                tuple(index["column_names"]),
                bool(index["unique"]),
            )
            for index in inspector.get_indexes("agent_source_attachments")
        },
    }


def _agent_version_foreign_keys(connection) -> set[tuple]:
    inspector = inspect(connection)
    return {
        (
            tuple(foreign_key["constrained_columns"]),
            foreign_key["referred_table"],
            tuple(foreign_key["referred_columns"]),
            foreign_key["options"].get("ondelete"),
        )
        for foreign_key in inspector.get_foreign_keys("agent_versions")
    }


@pytest.mark.asyncio
async def test_test_schema_matches_agent_history_and_dependency_delete_rules(
    tmp_path: Path,
) -> None:
    database = CorpusDatabase(
        f"sqlite+aiosqlite:///{(tmp_path / 'metadata.sqlite3').as_posix()}"
    )
    try:
        await database.create_schema_for_tests()
        async with database.engine.connect() as connection:
            attachment_schema = await connection.run_sync(_attachment_schema)
            version_foreign_keys = await connection.run_sync(_agent_version_foreign_keys)
        assert (
            ("agent_id",),
            "agents",
            ("id",),
            "RESTRICT",
        ) in attachment_schema["foreign_keys"]
        assert version_foreign_keys == {
            (("agent_id",), "agents", ("id",), "CASCADE")
        }
    finally:
        await database.close()


@pytest.mark.asyncio
async def test_0006_preserves_attachments_and_restricts_direct_agent_delete(
    tmp_path: Path,
) -> None:
    path = tmp_path / "restricted-delete.sqlite3"
    database_url = f"sqlite+aiosqlite:///{path.as_posix()}"
    await upgrade_database(database_url, "0005_remove_agent_attachment_display_name")
    organization_id = uuid.uuid4().hex
    agent_id = uuid.uuid4().hex
    attachment_id = uuid.uuid4().hex
    with sqlite3.connect(path) as connection:
        connection.execute("PRAGMA foreign_keys = ON")
        connection.execute(
            "INSERT INTO organizations (id, name, slug, created_at) VALUES (?, ?, ?, ?)",
            (organization_id, "Migration Workspace", f"migration-{organization_id}", "2026-08-07 00:00:00"),
        )
        connection.execute(
            """INSERT INTO agents
            (id, organization_id, name, name_key, lifecycle, current_version, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
            (agent_id, organization_id, "Migration Agent", "migration agent", "ACTIVE", 1, "2026-08-07 00:00:00", "2026-08-07 00:00:00"),
        )
        connection.execute(
            """INSERT INTO agent_source_attachments
            (id, organization_id, agent_id, source_id, source_revision_id, attached_at)
            VALUES (?, ?, ?, ?, ?, ?)""",
            (attachment_id, organization_id, agent_id, "source-ready-001", "revision-ready01", "2026-08-07 00:00:00"),
        )
        connection.commit()

    await upgrade_database(database_url)

    with sqlite3.connect(path) as connection:
        connection.execute("PRAGMA foreign_keys = ON")
        with pytest.raises(sqlite3.IntegrityError):
            connection.execute("DELETE FROM agents WHERE id = ?", (agent_id,))
        attachment = connection.execute(
            "SELECT source_id, source_revision_id FROM agent_source_attachments WHERE id = ?",
            (attachment_id,),
        ).fetchone()
    assert attachment == ("source-ready-001", "revision-ready01")
