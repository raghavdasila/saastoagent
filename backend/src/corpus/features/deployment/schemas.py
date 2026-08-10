from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class DeployArguments(BaseModel):
    model_config = ConfigDict(extra="forbid")
    agent_ref: str = Field(min_length=1, max_length=64)
    channel_id: uuid.UUID | None = None
    build_id: uuid.UUID | None = None


class RollbackArguments(BaseModel):
    model_config = ConfigDict(extra="forbid")
    agent_ref: str = Field(min_length=1, max_length=64)
    channel_id: uuid.UUID | None = None
    deployment_id: uuid.UUID | None = None


class DeploymentView(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    agent_id: uuid.UUID
    channel_id: uuid.UUID
    build_id: uuid.UUID
    status: str
    bundle_hash: str
    failure_code: str | None
    failure_message: str | None
    created_at: datetime


class DeploymentCollectionView(BaseModel):
    agent_id: uuid.UUID
    deployments: tuple[DeploymentView, ...]


__all__ = ["DeployArguments", "DeploymentCollectionView", "DeploymentView", "RollbackArguments"]
