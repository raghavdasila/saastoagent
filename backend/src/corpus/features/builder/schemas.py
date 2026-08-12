from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field
from routedeck_core.contracts.operations import OperationSource


class AssembleBuildArguments(BaseModel):
    model_config = ConfigDict(extra="forbid")
    agent_ref: str = Field(min_length=1, max_length=64)
    build_request_id: uuid.UUID | None = None


class BuildRuntimeLifecycleArguments(BaseModel):
    model_config = ConfigDict(extra="forbid")
    agent_ref: str = Field(min_length=1, max_length=64)
    build_id: uuid.UUID | None = Field(
        default=None,
        description=(
            "Surface-selected immutable build identity. Agent calls omit this value and "
            "use the exact current build resolved by Corpus for the selected Agent."
        ),
    )


def build_runtime_lifecycle_arguments(
    arguments: dict[str, object],
    source: OperationSource,
) -> BuildRuntimeLifecycleArguments:
    values = dict(arguments)
    if source is OperationSource.AGENT:
        values = {key: values[key] for key in ("agent_ref",) if key in values}
    payload = BuildRuntimeLifecycleArguments.model_validate(values)
    if source is OperationSource.SURFACE and payload.build_id is None:
        raise ValueError("A surface build lifecycle action requires the selected build.")
    return payload


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
    runtime_lifecycle: str
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
    attempt_number: int = Field(default=1, ge=1)
    job_id: uuid.UUID | None = None


class AgentBuildCollectionView(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")
    agent_id: uuid.UUID
    builds: tuple[AgentBuildView, ...]
