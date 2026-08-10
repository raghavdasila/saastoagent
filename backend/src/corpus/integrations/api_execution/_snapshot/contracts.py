from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import StrEnum
from types import MappingProxyType
from typing import Any, Mapping


CONTRACT_VERSION = 1


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def frozen_mapping(value: Mapping[str, Any] | None = None) -> Mapping[str, Any]:
    return MappingProxyType(dict(value or {}))


class ExecutionStatus(StrEnum):
    PENDING = "pending"
    LEASED = "leased"
    EXECUTING = "executing"
    SUCCEEDED = "succeeded"
    FAILED = "failed"
    OUTCOME_UNKNOWN = "outcome_unknown"
    CANCELLED = "cancelled"


class SafetyClass(StrEnum):
    READ = "read"
    WRITE = "write"
    DESTRUCTIVE = "destructive"
    FINANCIAL = "financial"


@dataclass(frozen=True)
class NetworkPolicy:
    allow_http: bool = False
    allow_private_networks: bool = False
    allowed_private_cidrs: tuple[str, ...] = ()
    connect_timeout_seconds: float = 5.0
    read_timeout_seconds: float = 30.0
    write_timeout_seconds: float = 30.0
    pool_timeout_seconds: float = 5.0
    max_request_bytes: int = 2 * 1024 * 1024
    max_response_bytes: int = 8 * 1024 * 1024


@dataclass(frozen=True)
class ConnectionRevision:
    connection_id: str
    revision: int
    tenant_id: str
    base_url: str
    openapi_document_hash: str
    auth_plugin_id: str = "none"
    credential_ref: str | None = None
    network_policy: NetworkPolicy = field(default_factory=NetworkPolicy)


@dataclass(frozen=True)
class ParameterContract:
    name: str
    location: str
    required: bool = False
    managed_by_auth: bool = False


@dataclass(frozen=True)
class OperationContract:
    operation_id: str
    method: str
    path_template: str
    safety_class: SafetyClass
    parameters: tuple[ParameterContract, ...] = ()
    request_media_type: str | None = None
    response_media_types: tuple[str, ...] = ("application/json",)
    idempotent: bool = False


@dataclass(frozen=True)
class CapabilityEnvelope:
    execution_id: str
    tenant_id: str
    connection_id: str
    connection_revision: int
    openapi_document_hash: str
    operation_id: str
    expires_at: datetime
    approval_token: str | None = None


@dataclass(frozen=True)
class ExecutionInputs:
    path: Mapping[str, Any] = field(default_factory=frozen_mapping)
    query: Mapping[str, Any] = field(default_factory=frozen_mapping)
    header: Mapping[str, Any] = field(default_factory=frozen_mapping)
    cookie: Mapping[str, Any] = field(default_factory=frozen_mapping)
    body: Any = None

    def __post_init__(self) -> None:
        object.__setattr__(self, "path", frozen_mapping(self.path))
        object.__setattr__(self, "query", frozen_mapping(self.query))
        object.__setattr__(self, "header", frozen_mapping(self.header))
        object.__setattr__(self, "cookie", frozen_mapping(self.cookie))


@dataclass(frozen=True)
class ExecutionRequest:
    envelope: CapabilityEnvelope
    connection: ConnectionRevision
    operation: OperationContract
    inputs: ExecutionInputs = field(default_factory=ExecutionInputs)
    idempotency_key: str | None = None
    outcome_verifier_id: str | None = None
    contract_version: int = CONTRACT_VERSION


@dataclass(frozen=True)
class ValidationIssue:
    phase: str
    message: str


@dataclass(frozen=True)
class ExecutionResult:
    execution_id: str
    status: ExecutionStatus
    started_at: datetime
    finished_at: datetime
    attempt: int
    status_code: int | None = None
    response_media_type: str | None = None
    response_body: Any = None
    response_bytes: bytes | None = None
    validation_issues: tuple[ValidationIssue, ...] = ()
    error_code: str | None = None
    public_message: str | None = None
    outcome_verified: bool | None = None


@dataclass(frozen=True)
class TraceEvent:
    execution_id: str
    tenant_id: str
    connection_id: str
    operation_id: str
    event: str
    occurred_at: datetime
    safe_details: Mapping[str, Any] = field(default_factory=frozen_mapping)

    def __post_init__(self) -> None:
        object.__setattr__(self, "safe_details", frozen_mapping(self.safe_details))
