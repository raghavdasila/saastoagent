from __future__ import annotations

import uuid
from dataclasses import dataclass
from typing import Any, Literal, Mapping, Protocol

from pydantic import BaseModel, ConfigDict, Field


class SafeApiExecutionError(RuntimeError):
    pass


@dataclass(frozen=True)
class SafeApiExecutionTarget:
    execution_id: str
    owner_id: uuid.UUID
    source_id: str
    source_revision_id: str
    connection_profile_id: str
    base_url: str
    authentication_method: str
    credential_name: str | None
    credential_reference_id: uuid.UUID | None
    credential_version: int | None
    document_hash: str
    document: Mapping[str, Any]
    operation_id: str


class SafeApiTraceRecord(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    event: str
    occurred_at: str
    safe_details: dict[str, str | int | bool | None]


class RedactedApiExecution(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    status: str
    status_code: int | None = None
    error_code: str | None = None
    public_message: str | None = None
    validation_issue_count: int = Field(ge=0)
    validation_phases: tuple[str, ...]
    http_call_count: int = Field(ge=0, le=1)
    started_at: str
    finished_at: str
    traces: tuple[SafeApiTraceRecord, ...]


class SafeApiExecutionPort(Protocol):
    async def execute_redacted(
        self, target: SafeApiExecutionTarget
    ) -> RedactedApiExecution: ...


RoutedDelivery = Literal["not_sent", "response_received", "possibly_sent"]


class RoutedApiExecutionError(RuntimeError):
    pass


@dataclass(frozen=True)
class RoutedApiExecutionTarget:
    execution_id: str
    owner_id: uuid.UUID
    connection_profile_id: str
    base_url: str
    authentication_method: str
    credential_name: str | None
    credential_reference_id: uuid.UUID | None
    credential_version: int | None
    document_hash: str
    document: Mapping[str, Any]
    operation_id: str
    path: Mapping[str, Any] | None = None
    query: Mapping[str, Any] | None = None
    header: Mapping[str, Any] | None = None
    cookie: Mapping[str, Any] | None = None
    body: Any = None
    approved_write: bool = False

    def __post_init__(self) -> None:
        for name in ("path", "query", "header", "cookie"):
            object.__setattr__(self, name, dict(getattr(self, name) or {}))


@dataclass(frozen=True)
class RoutedApiTraceRecord:
    event: str
    occurred_at: str
    safe_details: Mapping[str, str | int | bool | None]


@dataclass(frozen=True)
class RoutedApiExecutionOutcome:
    status: str
    delivery: RoutedDelivery
    status_code: int | None
    response_media_type: str | None
    response_byte_count: int
    response_body_sha256: str | None
    error_code: str | None
    public_message: str | None
    validation_issue_count: int
    validation_phases: tuple[str, ...]
    outcome_verified: bool | None
    http_call_count: int
    started_at: str
    finished_at: str
    traces: tuple[RoutedApiTraceRecord, ...]


class RoutedApiExecutionPort(Protocol):
    async def execute(
        self, target: RoutedApiExecutionTarget
    ) -> RoutedApiExecutionOutcome: ...


__all__ = [
    "RedactedApiExecution",
    "RoutedApiExecutionError",
    "RoutedApiExecutionOutcome",
    "RoutedApiExecutionPort",
    "RoutedApiExecutionTarget",
    "RoutedApiTraceRecord",
    "SafeApiExecutionError",
    "SafeApiExecutionPort",
    "SafeApiExecutionTarget",
    "SafeApiTraceRecord",
]
