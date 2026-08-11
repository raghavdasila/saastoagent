from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from enum import Enum
from pathlib import Path

from pydantic import BaseModel, ConfigDict, Field


def utc_now() -> datetime:
    return datetime.now(UTC)


class SourceState(str, Enum):
    ACCEPTED = "accepted"
    QUEUED = "queued"
    RUNNING = "running"
    READY = "ready"
    FAILED = "failed"


class ContractRevisionProposalState(str, Enum):
    PENDING = "pending"
    APPROVED = "approved"


class ContractPatchRecord(BaseModel):
    model_config = ConfigDict(frozen=True)

    patch_id: str = Field(pattern=r"^[0-9a-f]{16}$")
    kind: str = Field(min_length=1)
    schema_pointer: str = Field(min_length=1)
    field_name: str | None = None
    evidence_count: int = Field(ge=1)
    impact_count: int = Field(ge=1)


class ContractRevisionProposalRecord(BaseModel):
    model_config = ConfigDict(frozen=True)

    schema_version: int = 1
    proposal_id: str = Field(min_length=16, max_length=16)
    source_id: str = Field(min_length=16, max_length=16)
    parent_revision_id: str = Field(min_length=16, max_length=16)
    state: ContractRevisionProposalState
    source_raw_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    source_canonical_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    repair_manifest_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    repaired_parent_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    final_canonical_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    patches: tuple[ContractPatchRecord, ...] = Field(min_length=1)
    local_medusa_version: str = Field(min_length=1)
    local_package_json_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    local_package_lock_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    evidence_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    proposed_at: datetime
    approved_by_owner_id: str | None = None
    approved_at: datetime | None = None
    approved_revision_id: str | None = Field(default=None, min_length=16, max_length=16)


class SourceRecord(BaseModel):
    model_config = ConfigDict(frozen=True)

    schema_version: int = 1
    source_id: str = Field(min_length=1)
    owner_key: str = Field(min_length=1)
    connector_key: str = Field(min_length=1)
    display_name: str = Field(min_length=1)
    current_revision_id: str = Field(min_length=1)
    created_at: datetime
    updated_at: datetime
    current_description_id: str | None = Field(default=None, min_length=16, max_length=16)
    contract_revision_proposals: tuple[ContractRevisionProposalRecord, ...] = ()


class SourceDescriptionRecord(BaseModel):
    model_config = ConfigDict(frozen=True)

    description_id: str = Field(min_length=16, max_length=16)
    source_id: str = Field(min_length=16, max_length=16)
    filename: str = Field(min_length=1, max_length=255)
    content_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    created_at: datetime


class SourceDescriptionView(BaseModel):
    model_config = ConfigDict(frozen=True)

    description_id: str = Field(min_length=1)
    source_id: str = Field(min_length=16, max_length=16)
    filename: str = Field(min_length=1, max_length=255)
    content_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    content: str
    created_at: datetime


class SourceRevisionRecord(BaseModel):
    model_config = ConfigDict(frozen=True)

    schema_version: int = 1
    revision_id: str = Field(min_length=1)
    source_id: str = Field(min_length=1)
    original_filename: str = Field(min_length=1)
    content_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    description_filename: str | None = None
    description_sha256: str | None = Field(
        default=None, pattern=r"^[0-9a-f]{64}$"
    )
    job_id: str | None = None
    state: SourceState
    created_at: datetime
    updated_at: datetime
    summary: dict[str, object] = Field(default_factory=dict)
    failure_code: str | None = None
    failure_message: str | None = None
    parent_revision_id: str | None = Field(default=None, min_length=16, max_length=16)
    artifact_revision_id: str | None = Field(default=None, min_length=16, max_length=16)


class SourceView(BaseModel):
    model_config = ConfigDict(frozen=True)

    source_id: str
    connector_key: str
    display_name: str
    created_at: datetime
    updated_at: datetime
    revision: SourceRevisionRecord


@dataclass(frozen=True)
class PreparedSource:
    source: SourceRecord
    revision: SourceRevisionRecord
    input_path: Path
    artifact_dir: Path


__all__ = [
    "ContractPatchRecord",
    "ContractRevisionProposalRecord",
    "ContractRevisionProposalState",
    "PreparedSource",
    "SourceDescriptionRecord",
    "SourceDescriptionView",
    "SourceRecord",
    "SourceRevisionRecord",
    "SourceState",
    "SourceView",
    "utc_now",
]
