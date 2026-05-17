import uuid
from datetime import datetime

from pydantic import BaseModel, Field


class SaaSAgentCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    slug: str = Field(..., min_length=1, max_length=255, pattern=r"^[a-z0-9][a-z0-9\-]*$")


class SaaSAgentRead(BaseModel):
    id: uuid.UUID
    name: str
    slug: str
    created_by: uuid.UUID
    created_at: datetime
    role: str | None = None

    model_config = {"from_attributes": True}


class SaaSAgentStats(BaseModel):
    connections_count: int = 0
    tools_count: int = 0
    learnings_count: int = 0
    active_learnings_count: int = 0
    systems_count: int = 0
    connections_with_learnings: int = 0
    tools_with_learnings: int = 0
    avg_confidence: float = 0.0
    maturity: float = 0.0
