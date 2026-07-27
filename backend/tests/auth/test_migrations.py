from __future__ import annotations

from pathlib import Path

import pytest

from corpus.auth.database import AuthDatabase, MigrationRevisionError
from corpus.auth.migrations import upgrade_database


@pytest.mark.asyncio
async def test_alembic_upgrade_reaches_expected_revision_and_startup_check_passes(
    tmp_path: Path,
) -> None:
    database_url = f"sqlite+aiosqlite:///{(tmp_path / 'auth.sqlite3').as_posix()}"
    await upgrade_database(database_url)
    database = AuthDatabase(database_url)
    try:
        await database.verify_revision("0001_owner_auth")
        with pytest.raises(MigrationRevisionError):
            await database.verify_revision("future_revision")
    finally:
        await database.close()
