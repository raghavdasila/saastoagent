from __future__ import annotations

import time
from contextlib import contextmanager
from typing import Any, Iterator


class RequestTiming:
    def __init__(self) -> None:
        self._started = time.perf_counter()
        self._spans: list[dict[str, Any]] = []

    @contextmanager
    def span(self, name: str, **metadata: Any) -> Iterator[None]:
        started = time.perf_counter()
        try:
            yield
        finally:
            ended = time.perf_counter()
            item: dict[str, Any] = {
                "name": name,
                "duration_ms": round((ended - started) * 1000, 2),
                "offset_ms": round((started - self._started) * 1000, 2),
            }
            if metadata:
                item["metadata"] = metadata
            self._spans.append(item)

    def mark(self, name: str, **metadata: Any) -> None:
        item: dict[str, Any] = {
            "name": name,
            "duration_ms": 0,
            "offset_ms": round((time.perf_counter() - self._started) * 1000, 2),
        }
        if metadata:
            item["metadata"] = metadata
        self._spans.append(item)

    def snapshot(self) -> dict[str, Any]:
        return {
            "total_ms": round((time.perf_counter() - self._started) * 1000, 2),
            "spans": list(self._spans),
        }
