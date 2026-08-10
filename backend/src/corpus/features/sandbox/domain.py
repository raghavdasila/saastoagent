from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True)
class RuntimeSandboxRun:
    runtime_run_id: str
    status: str
    awaiting: str | None
    final_response: str | None
    api_call_count: int
    safe_events: tuple[dict[str, object], ...]
    routedeck_projection: dict[str, object]


@dataclass(frozen=True)
class SandboxRecord:
    id: uuid.UUID
    organization_id: uuid.UUID
    agent_id: uuid.UUID
    build_id: uuid.UUID
    runtime_build_hash: str
    runtime_session_id: str
    runtime_run_id: str
    status: str
    awaiting: str | None
    final_response: str | None
    api_call_count: int
    safe_events: tuple[dict[str, object], ...]
    routedeck_projection: dict[str, object]
    failure_code: str | None
    created_at: datetime
    updated_at: datetime
    message: str = ""
