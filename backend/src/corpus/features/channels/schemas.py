from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class CreateChannelArguments(BaseModel):
    model_config = ConfigDict(extra="forbid")
    agent_ref: str = Field(min_length=1, max_length=64)
    name: str = Field(min_length=1, max_length=160)
    slug: str = Field(pattern=r"^[a-z0-9]+(?:-[a-z0-9]+)*$", max_length=120)


class SetChannelEnabledArguments(BaseModel):
    model_config = ConfigDict(extra="forbid")
    agent_ref: str = Field(min_length=1, max_length=64)
    channel_id: uuid.UUID | None = None
    enabled: bool


class ChannelView(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    agent_id: uuid.UUID
    name: str
    slug: str
    status: str
    enabled: bool
    active_deployment_id: uuid.UUID | None
    failure_code: str | None
    failure_message: str | None
    created_at: datetime


class ChannelCollectionView(BaseModel):
    agent_id: uuid.UUID
    channels: tuple[ChannelView, ...]


__all__ = [
    "ChannelCollectionView",
    "ChannelView",
    "CreateChannelArguments",
    "SetChannelEnabledArguments",
]
