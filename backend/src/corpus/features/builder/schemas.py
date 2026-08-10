from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class AssembleBuildArguments(BaseModel):
    model_config = ConfigDict(extra="forbid")
    agent_ref: str = Field(min_length=1, max_length=64)
    build_request_id: uuid.UUID | None = None


class BuilderSourceBindingView(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")
    source_id: str
    source_revision_id: str
    curation_id: str
    inventory_fingerprint: str
    included_operation_ids: tuple[str, ...]
    profile_id: str
    credential_reference_id: uuid.UUID | None
    credential_version: int | None


class AgentBuildView(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")
    id: uuid.UUID
    agent_id: uuid.UUID
    build_request_id: uuid.UUID
    design_revision_id: uuid.UUID
    agent_version: int
    status: str
    runtime_build_hash: str | None
    model: str | None
    model_digest: str | None
    source_bindings: tuple[BuilderSourceBindingView, ...]
    allowed_operation_ids: tuple[str, ...]
    navgraph_hash: str | None
    compiled_navgraph: dict[str, object]
    frontend_contract: dict[str, object]
    failure_code: str | None
    failure_message: str | None
    created_at: datetime
    updated_at: datetime


class AgentBuildCollectionView(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")
    agent_id: uuid.UUID
    builds: tuple[AgentBuildView, ...]
