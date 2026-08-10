from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True)
class ChannelRecord:
    id: uuid.UUID
    organization_id: uuid.UUID
    agent_id: uuid.UUID
    runtime_channel_id: str | None
    name: str
    slug: str
    status: str
    enabled: bool
    active_deployment_id: uuid.UUID | None
    failure_code: str | None
    failure_message: str | None
    created_at: datetime
    updated_at: datetime


__all__ = ["ChannelRecord"]
