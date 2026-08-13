from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping


@dataclass(frozen=True)
class BuildConnectionSpec:
    connection_id: str
    revision: int
    base_url: str
    openapi_path: str
    openapi_hash: str
    auth_plugin_id: str
    credential_ref: str | None
    operation_ids: tuple[str, ...]


@dataclass(frozen=True)
class ImmutableBuildSpec:
    build_id: str
    version: int
    name: str
    instructions: str
    model: str
    model_digest: str
    source_path: str
    source_hash: str
    allowed_operations: tuple[str, ...]
    preauthorized_write_operations: tuple[str, ...]
    connections: tuple[BuildConnectionSpec, ...]
    max_turns: int = 8
    max_api_calls: int = 8
    max_parallel_calls: int = 4
    max_response_bytes: int = 8 * 1024 * 1024
    max_elapsed_seconds: int = 120


@dataclass(frozen=True)
class ImmutableBuildProjection:
    build_id: str
    version: int
    content_hash: str
    source_hash: str
    operation_ids: tuple[str, ...]
    preauthorized_write_operation_ids: tuple[str, ...]


@dataclass(frozen=True)
class SandboxRunSpec:
    tenant_id: str
    session_id: str
    build_hash: str
    message: str
    run_id: str | None = None
    command: str = "start"
    selected_operation_id: str | None = None
    selected_operations: Mapping[str, str] | None = None
    provided_inputs: Mapping[str, Any] | None = None


@dataclass(frozen=True)
class SandboxEventProjection:
    sequence: int
    kind: str
    occurred_at: str
    safe_data: Mapping[str, Any]


@dataclass(frozen=True)
class SandboxRunProjection:
    run_id: str
    build_hash: str
    status: str
    awaiting: str | None
    final_response: str | None
    api_call_count: int
    events: tuple[SandboxEventProjection, ...]


@dataclass(frozen=True)
class ReviewedRunCompletion:
    run_id: str
    build_hash: str
    status: str
    final_response: str
    api_call_count: int
    events: tuple[SandboxEventProjection, ...]


@dataclass(frozen=True)
class EvaluationCaseSpec:
    tenant_id: str
    run_id: str
    message: str
    expected_operation_ids: tuple[str, ...]
    required_response_fields: tuple[str, ...] = ()
    require_write_verification: bool = False


@dataclass(frozen=True)
class EvaluationCaseProjection:
    case_id: str
    build_hash: str
    source_run_id: str
    expected_operation_ids: tuple[str, ...]
    source_evidence_hash: str
    source_event_count: int
    mandatory: bool


@dataclass(frozen=True)
class EvaluationRunProjection:
    evaluation_run_id: str
    case_id: str
    build_hash: str
    status: str
    deterministic_pass: bool
    review_pass: bool
    reasons: tuple[str, ...]
    created_at: str


@dataclass(frozen=True)
class EligibilityProjection:
    build_hash: str
    eligible: bool
    supporting_evaluation_run_ids: tuple[str, ...]
    reasons: tuple[str, ...]


__all__ = [
    "BuildConnectionSpec",
    "EligibilityProjection",
    "EvaluationCaseProjection",
    "EvaluationCaseSpec",
    "EvaluationRunProjection",
    "ImmutableBuildProjection",
    "ImmutableBuildSpec",
    "SandboxEventProjection",
    "SandboxRunProjection",
    "ReviewedRunCompletion",
    "SandboxRunSpec",
]
