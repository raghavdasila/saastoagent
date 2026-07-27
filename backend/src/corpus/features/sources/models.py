from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from enum import Enum
from pathlib import Path

from pydantic import BaseModel, ConfigDict, Field


def utc_now() -> datetime:
    return datetime.now(UTC)


class SourceState(str, Enum):
    PROCESSING = "processing"
    READY = "ready"
    FAILED = "failed"


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


class SourceRevisionRecord(BaseModel):
    model_config = ConfigDict(frozen=True)

    schema_version: int = 1
    revision_id: str = Field(min_length=1)
    source_id: str = Field(min_length=1)
    original_filename: str = Field(min_length=1)
    content_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    state: SourceState
    created_at: datetime
    updated_at: datetime
    summary: dict[str, object] = Field(default_factory=dict)
    failure_code: str | None = None
    failure_message: str | None = None


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
    "PreparedSource",
    "SourceRecord",
    "SourceRevisionRecord",
    "SourceState",
    "SourceView",
    "utc_now",
]

