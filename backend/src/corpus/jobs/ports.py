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


__all__ = ["DurableJobPort"]
