from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class SandboxDeploymentCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")
    build_id: uuid.UUID
    request_key: str = Field(min_length=1, max_length=160)


class SandboxDeploymentRetry(BaseModel):
    model_config = ConfigDict(extra="forbid")
    request_key: str = Field(min_length=1, max_length=160)


class PlaygroundMessageCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")
    text: str = Field(min_length=1, max_length=16_000)
    request_id: str | None = Field(default=None, min_length=1, max_length=160)


class PlaygroundReviewResolution(BaseModel):
    model_config = ConfigDict(extra="forbid")
    review_id: str = Field(min_length=1, max_length=160)
    accepted: bool
    request_id: str | None = Field(default=None, min_length=1, max_length=160)


class SandboxDeploymentView(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")
    id: uuid.UUID
    target_id: uuid.UUID
    agent_id: uuid.UUID
    build_id: uuid.UUID
    mode: str
    status: str
    request_key: str | None
    runtime_deployment_id: str | None
    failure_code: str | None
    failure_message: str | None
    created_at: datetime
    updated_at: datetime


class PlaygroundSessionView(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")
    session_id: str
    target_id: uuid.UUID
    deployment_id: uuid.UUID
    runtime_deployment_id: str
    build_id: uuid.UUID
    purpose: str
    created_at: str
    projection: dict[str, object] | None = None


class SandboxDeploymentCollectionView(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")
    agent_id: uuid.UUID
    target_id: uuid.UUID | None
    active_deployment_id: uuid.UUID | None
    deployments: tuple[SandboxDeploymentView, ...]
    playground_sessions: tuple[PlaygroundSessionView, ...]


class PlaygroundInteractionView(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")
    session: PlaygroundSessionView
    projection: dict[str, object]
    interaction_id: str | None = None


class SandboxDiagnosticsView(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")
    session: PlaygroundSessionView
    projection: dict[str, object]
    interactions: tuple[dict[str, object], ...]


__all__ = [
    "PlaygroundInteractionView",
    "PlaygroundMessageCreate",
    "PlaygroundReviewResolution",
    "PlaygroundSessionView",
    "SandboxDeploymentCollectionView",
    "SandboxDeploymentCreate",
    "SandboxDeploymentRetry",
    "SandboxDeploymentView",
    "SandboxDiagnosticsView",
]
