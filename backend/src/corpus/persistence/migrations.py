from __future__ import annotations

import asyncio
from pathlib import Path

from alembic import command
from alembic.config import Config


_BACKEND_ROOT = Path(__file__).resolve().parents[3]


async def upgrade_database(database_url: str, revision: str = "head") -> None:
    await asyncio.to_thread(_upgrade_sync, database_url, revision)


def _upgrade_sync(database_url: str, revision: str) -> None:
    config = Config(str(_BACKEND_ROOT / "alembic.ini"))
    config.set_main_option("script_location", str(_BACKEND_ROOT / "migrations"))
    config.set_main_option("sqlalchemy.url", _sync_url(database_url))
    command.upgrade(config, revision)


def _sync_url(database_url: str) -> str:
    return database_url.replace("sqlite+aiosqlite://", "sqlite://", 1)


if __name__ == "__main__":
    from .config import CorpusDatabaseSettings

    asyncio.run(upgrade_database(CorpusDatabaseSettings.from_env().url))


__all__ = ["upgrade_database"]
