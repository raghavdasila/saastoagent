from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path


@dataclass(frozen=True)
class BuilderSourceBinding:
    source_id: str
    source_revision_id: str
    curation_id: str
    inventory_fingerprint: str
    included_operation_ids: tuple[str, ...]
    artifact_dir: Path
    document_path: Path
    document_hash: str
    profile_id: str
    base_url: str
    authentication_method: str
    credential_name: str | None
    credential_reference_id: uuid.UUID | None
    credential_version: int | None


@dataclass(frozen=True)
class BuilderInputSnapshot:
    build_id: uuid.UUID
    build_request_id: uuid.UUID
    organization_id: uuid.UUID
    agent_id: uuid.UUID
    agent_version: int
    design_revision_id: uuid.UUID
    input_fingerprint: str
    name: str
    goal: str
    instructions: str
    features: tuple[str, ...]
    behaviors: tuple[str, ...]
    policies: tuple[str, ...]
    capabilities: tuple[str, ...]
    tools: tuple[str, ...]
    source_bindings: tuple[BuilderSourceBinding, ...]


@dataclass(frozen=True)
class RuntimeBuildArtifact:
    runtime_build_hash: str
    model: str
    model_digest: str
    allowed_operation_ids: tuple[str, ...]
    navgraph_hash: str
    compiled_navgraph: dict[str, object]
    frontend_contract: dict[str, object]


@dataclass(frozen=True)
class BuilderRecord:
    id: uuid.UUID
    organization_id: uuid.UUID
    agent_id: uuid.UUID
    build_request_id: uuid.UUID
    design_revision_id: uuid.UUID
    agent_version: int
    status: str
    runtime_lifecycle: str
    runtime_build_hash: str | None
    model: str | None
    model_digest: str | None
    source_bindings: tuple[dict[str, object], ...]
    allowed_operation_ids: tuple[str, ...]
    navgraph_hash: str | None
    compiled_navgraph: dict[str, object]
    frontend_contract: dict[str, object]
    failure_code: str | None
    failure_message: str | None
    created_at: datetime
    updated_at: datetime
    attempt_number: int = 1
