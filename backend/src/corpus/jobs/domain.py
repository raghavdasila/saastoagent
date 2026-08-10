from __future__ import annotations

import enum
import uuid
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Mapping


class DurableJobState(str, enum.Enum):
    QUEUED = "queued"
    RUNNING = "running"
    SUCCEEDED = "succeeded"
    FAILED = "failed"


@dataclass(frozen=True)
class DurableJobRecord:
    id: uuid.UUID
    owner_id: uuid.UUID
    job_type: str
    state: DurableJobState
    payload: Mapping[str, Any]
    attempt_count: int
    max_attempts: int
    error_code: str | None
    error_message: str | None
    result: Mapping[str, Any] | None
    created_at: datetime
    updated_at: datetime
    started_at: datetime | None
    completed_at: datetime | None


__all__ = ["DurableJobRecord", "DurableJobState"]
