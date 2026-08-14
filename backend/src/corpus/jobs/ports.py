from __future__ import annotations

import uuid
from typing import Any, Mapping, Protocol

from .domain import DurableJobRecord


class DurableJobPort(Protocol):
    """Owner-scoped durable scheduling boundary used by Corpus features."""

    async def enqueue(
        self,
        *,
        owner_id: uuid.UUID,
        job_type: str,
        payload: Mapping[str, Any],
        max_attempts: int = 1,
    ) -> DurableJobRecord: ...


class DurableJobLifecyclePort(Protocol):
    """Worker-side lifecycle boundary without a concrete persistence dependency."""

    async def mark_running(self, *, job_id: uuid.UUID) -> DurableJobRecord: ...

    async def mark_succeeded(
        self, *, job_id: uuid.UUID, result: Mapping[str, Any]
    ) -> DurableJobRecord: ...

    async def mark_failed(
        self,
        *,
        job_id: uuid.UUID,
        error_code: str,
        error_message: str,
    ) -> DurableJobRecord: ...

    async def status(
        self,
        *,
        owner_id: uuid.UUID,
        job_id: uuid.UUID,
    ) -> DurableJobRecord: ...

    async def retry(
        self,
        *,
        owner_id: uuid.UUID,
        job_id: uuid.UUID,
    ) -> DurableJobRecord: ...


__all__ = ["DurableJobLifecyclePort", "DurableJobPort"]
