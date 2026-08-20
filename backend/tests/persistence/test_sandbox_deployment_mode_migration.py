from __future__ import annotations

import sqlite3
from pathlib import Path

import pytest

from corpus.persistence.migrations import upgrade_database


@pytest.mark.asyncio
async def test_existing_delivery_ids_and_activation_survive_mode_migration(
    tmp_path: Path,
) -> None:
    database_path = tmp_path / "corpus.sqlite3"
    database_url = f"sqlite+aiosqlite:///{database_path.as_posix()}"
    await upgrade_database(database_url, "0019_builder_assembly_lifecycle")
    owner_id = "1" * 32
    agent_id = "2" * 32
    channel_id = "3" * 32
    deployment_id = "4" * 32
    build_id = "5" * 32
    eligibility_id = "6" * 32
    timestamp = "2026-08-19 00:00:00"
    with sqlite3.connect(database_path) as connection:
        connection.execute("PRAGMA foreign_keys = OFF")
        connection.execute(
            """INSERT INTO agent_channels
               (id, organization_id, agent_id, runtime_channel_id, name, slug,
                status, enabled, active_deployment_id, failure_code,
                failure_message, created_at, updated_at)
               VALUES (?, ?, ?, ?, ?, ?, 'ready', 1, ?, NULL, NULL, ?, ?)""",
            (
                channel_id, owner_id, agent_id, "runtime-channel", "Web", "web",
                deployment_id, timestamp, timestamp,
            ),
        )
        connection.execute(
            """INSERT INTO agent_deployments
               (id, organization_id, agent_id, channel_id, build_id,
                eligibility_id, runtime_deployment_id, status, bundle_hash,
                failure_code, failure_message, created_at, updated_at, job_id,
                retry_of_deployment_id, active_channel_id)
               VALUES (?, ?, ?, ?, ?, ?, ?, 'ready', ?, NULL, NULL, ?, ?,
                       NULL, NULL, ?)""",
            (
                deployment_id, owner_id, agent_id, channel_id, build_id,
                eligibility_id, "runtime-deployment", "a" * 64, timestamp,
                timestamp, channel_id,
            ),
        )
        connection.commit()

    await upgrade_database(database_url, "0020_sandbox_deployment_mode")

    with sqlite3.connect(database_path) as connection:
        deployment = connection.execute(
            """SELECT id, target_id, mode, channel_id, eligibility_id,
                      active_target_id
               FROM agent_deployments WHERE id = ?""",
            (deployment_id,),
        ).fetchone()
        target = connection.execute(
            """SELECT id, mode, channel_id, active_deployment_id
               FROM agent_deployment_targets WHERE id = ?""",
            (channel_id,),
        ).fetchone()
        channel = connection.execute(
            "SELECT id, active_deployment_id FROM agent_channels WHERE id = ?",
            (channel_id,),
        ).fetchone()

    assert deployment == (
        deployment_id, channel_id, "delivery", channel_id, eligibility_id,
        channel_id,
    )
    assert target == (channel_id, "delivery", channel_id, deployment_id)
    assert channel == (channel_id, deployment_id)
