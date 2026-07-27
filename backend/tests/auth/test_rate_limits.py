from __future__ import annotations

from datetime import UTC, datetime, timedelta
from pathlib import Path

import pytest

from corpus.auth.database import AuthDatabase
from corpus.auth.rate_limits import AuthRateLimiter, RateLimitExceeded


@pytest.mark.asyncio
async def test_rate_limit_is_database_backed_and_windowed(tmp_path: Path) -> None:
    database = AuthDatabase(
        f"sqlite+aiosqlite:///{(tmp_path / 'auth.sqlite3').as_posix()}"
    )
    await database.create_schema_for_tests()
    limiter = AuthRateLimiter(database)
    now = datetime(2026, 7, 22, 10, 5, tzinfo=UTC)
    try:
        await limiter.consume(
            scope="sign-in-email",
            subject="owner@example.com",
            limit=2,
            window=timedelta(minutes=15),
            now=now,
        )
        await limiter.consume(
            scope="sign-in-email",
            subject="owner@example.com",
            limit=2,
            window=timedelta(minutes=15),
            now=now,
        )
        with pytest.raises(RateLimitExceeded):
            await limiter.consume(
                scope="sign-in-email",
                subject="owner@example.com",
                limit=2,
                window=timedelta(minutes=15),
                now=now,
            )
        await limiter.consume(
            scope="sign-in-email",
            subject="owner@example.com",
            limit=2,
            window=timedelta(minutes=15),
            now=now + timedelta(minutes=15),
        )
    finally:
        await database.close()
