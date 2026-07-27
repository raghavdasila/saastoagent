from __future__ import annotations

import hashlib
from datetime import UTC, datetime, timedelta

from sqlalchemy import select

from .database import AuthDatabase
from .models import AuthRateLimit


class RateLimitExceeded(RuntimeError):
    pass


class AuthRateLimiter:
    def __init__(self, database: AuthDatabase) -> None:
        self.database = database

    async def consume(
        self,
        *,
        scope: str,
        subject: str,
        limit: int,
        window: timedelta,
        now: datetime | None = None,
    ) -> None:
        current = now or datetime.now(UTC)
        window_seconds = int(window.total_seconds())
        if limit < 1 or window_seconds < 1:
            raise ValueError("Rate-limit bounds must be positive.")
        epoch = int(current.timestamp())
        window_start = datetime.fromtimestamp(
            epoch - (epoch % window_seconds),
            tz=UTC,
        )
        subject_hash = hashlib.sha256(subject.encode("utf-8")).hexdigest()
        async with self.database.session() as session:
            async with session.begin():
                bucket = await session.scalar(
                    select(AuthRateLimit).where(
                        AuthRateLimit.scope == scope,
                        AuthRateLimit.subject_hash == subject_hash,
                        AuthRateLimit.window_start == window_start,
                    )
                )
                if bucket is None:
                    session.add(
                        AuthRateLimit(
                            scope=scope,
                            subject_hash=subject_hash,
                            window_start=window_start,
                            request_count=1,
                        )
                    )
                    return
                if bucket.request_count >= limit:
                    raise RateLimitExceeded("Too many authentication attempts.")
                bucket.request_count += 1


__all__ = ["AuthRateLimiter", "RateLimitExceeded"]
