from __future__ import annotations

from collections import defaultdict, deque
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone


@dataclass(frozen=True)
class RateLimitResult:
    allowed: bool
    remaining: int
    reset_seconds: int


class AnonymousChatRateLimiter:
    def __init__(self) -> None:
        self._hits: dict[str, deque[datetime]] = defaultdict(deque)

    def check(self, key: str, *, limit: int, window_seconds: int) -> RateLimitResult:
        if limit <= 0:
            return RateLimitResult(allowed=True, remaining=limit, reset_seconds=0)

        now = datetime.now(timezone.utc)
        window = timedelta(seconds=window_seconds)
        hits = self._hits[key]

        while hits and now - hits[0] >= window:
            hits.popleft()

        if len(hits) >= limit:
            reset_at = hits[0] + window
            reset_seconds = max(1, int((reset_at - now).total_seconds()))
            return RateLimitResult(allowed=False, remaining=0, reset_seconds=reset_seconds)

        hits.append(now)
        return RateLimitResult(
            allowed=True,
            remaining=max(0, limit - len(hits)),
            reset_seconds=window_seconds,
        )


anonymous_chat_rate_limiter = AnonymousChatRateLimiter()
