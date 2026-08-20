from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True)
class DeploymentRecord:
    id: uuid.UUID
    organization_id: uuid.UUID
    agent_id: uuid.UUID
    channel_id: uuid.UUID | None
    build_id: uuid.UUID
    eligibility_id: uuid.UUID | None
    runtime_deployment_id: str | None
    status: str
    bundle_hash: str
    failure_code: str | None
    failure_message: str | None
    created_at: datetime
    updated_at: datetime
    job_id: uuid.UUID | None = None
    retry_of_deployment_id: uuid.UUID | None = None
    target_id: uuid.UUID | None = None
    mode: str = "delivery"
    request_key: str | None = None


@dataclass(frozen=True)
class DeploymentTargetRecord:
    id: uuid.UUID
    organization_id: uuid.UUID
    agent_id: uuid.UUID
    mode: str
    channel_id: uuid.UUID | None
    active_deployment_id: uuid.UUID | None
    created_at: datetime


@dataclass(frozen=True)
class EligibleBuild:
    eligibility_id: uuid.UUID
    runtime_build_hash: str
    eligibility_hash: str


__all__ = ["DeploymentRecord", "DeploymentTargetRecord", "EligibleBuild"]
