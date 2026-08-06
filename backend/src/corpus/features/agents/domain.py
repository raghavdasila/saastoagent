from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import datetime
from enum import Enum


class AgentLifecycle(str, Enum):
    ACTIVE = "active"
    ARCHIVED = "archived"


@dataclass(frozen=True)
class AgentRecord:
    id: uuid.UUID
    organization_id: uuid.UUID
    name: str
    description: str
    instructions: str
    lifecycle: AgentLifecycle
    current_version: int
    created_at: datetime
    updated_at: datetime


__all__ = ["AgentLifecycle", "AgentRecord"]
