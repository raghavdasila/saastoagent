from __future__ import annotations

import uuid
from dataclasses import dataclass


@dataclass(frozen=True)
class OperationsLineage:
    agent_id: uuid.UUID
    build_id: uuid.UUID
    deployment_id: uuid.UUID
    runtime_run_id: str
    safe_events: tuple[dict[str, object], ...]

