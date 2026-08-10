from __future__ import annotations

import hashlib
import json
import secrets
import uuid
from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Literal, Mapping

from pydantic import BaseModel, ConfigDict, Field, ValidationError

from corpus.integrations.api_execution._snapshot.contract_revision import openapi_document_hash
from corpus.integrations.api_execution.routed import (
    RoutedApiExecutionAdapter,
    RoutedApiExecutionError,
    RoutedApiExecutionOutcome,
    RoutedApiExecutionTarget,
)

from ...repository import LocalSourceRepository
from .connection_checks import MEDUSA_EFFECTIVE_CONTRACT_HASH
from .route_plans import ApiRoutePlanConflict, ApiRoutePlanRecord, ApiRoutePlanService


ApiRoutedSafety = Literal["read", "write"]
ApiRoutedDelivery = Literal["not_sent", "response_received", "possibly_sent"]


class ApiRoutedExecutionError(RuntimeError):
    pass


class ApiRoutedExecutionConflict(ApiRoutedExecutionError):
    pass


class ApiRoutedTraceRecord(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    event: str
    occurred_at: datetime
    safe_details: dict[str, str | int | bool | None]


class ApiRoutedExecutionClaim(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    schema_version: int = 1
    claim_id: str = Field(min_length=16, max_length=16)
    request_id: str = Field(min_length=16, max_length=128)
    boot_id: str = Field(min_length=1, max_length=128)
    owner_id: uuid.UUID
    conversation_id: str = Field(min_length=16, max_length=64)
    route_session_id: str = Field(min_length=1, max_length=256)
    plan_id: str = Field(min_length=16, max_length=16)
    plan_record_id: str = Field(min_length=16, max_length=16)
    plan_fingerprint: str = Field(pattern=r"^[0-9a-f]{64}$")
    source_id: str = Field(min_length=16, max_length=16)
    source_revision_id: str = Field(min_length=16, max_length=16)
    operation_id: str = Field(min_length=1, max_length=256)
    method: str = Field(pattern=r"^(GET|HEAD|OPTIONS|POST|PUT|PATCH|DELETE)$")
    path_template: str = Field(min_length=1, max_length=2_000)
    safety: ApiRoutedSafety
    created_at: datetime


class ApiRoutedExecutionResult(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    schema_version: int = 1
    result_id: str = Field(min_length=16, max_length=16)
    claim_id: str = Field(min_length=16, max_length=16)
    request_id: str = Field(min_length=16, max_length=128)
    owner_id: uuid.UUID
    conversation_id: str = Field(min_length=16, max_length=64)
    route_session_id: str = Field(min_length=1, max_length=256)
    plan_id: str = Field(min_length=16, max_length=16)
    plan_record_id: str = Field(min_length=16, max_length=16)
    plan_fingerprint: str = Field(pattern=r"^[0-9a-f]{64}$")
    source_id: str = Field(min_length=16, max_length=16)
    source_revision_id: str = Field(min_length=16, max_length=16)
    operation_id: str = Field(min_length=1, max_length=256)
    method: str
    path_template: str
    safety: ApiRoutedSafety
    status: Literal["succeeded", "failed", "outcome_unknown"]
    delivery: ApiRoutedDelivery
    status_code: int | None = None
    response_media_type: str | None = None
    response_byte_count: int = Field(ge=0)
    response_body_sha256: str | None = Field(default=None, pattern=r"^[0-9a-f]{64}$")
    error_code: str | None = None
    public_message: str | None = None
    validation_issue_count: int = Field(ge=0)
    validation_phases: tuple[str, ...]
    outcome_verified: bool | None = None
    http_call_count: int | None = Field(default=None, ge=0, le=1)
    started_at: datetime
    finished_at: datetime
    traces: tuple[ApiRoutedTraceRecord, ...]


class ApiRoutedExecutionView(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    result_id: str
    plan_id: str
    source_id: str
    source_revision_id: str
    operation_id: str
    method: str
    path_template: str
    safety: ApiRoutedSafety
    status: Literal["succeeded", "failed", "outcome_unknown"]
    delivery: ApiRoutedDelivery
    status_code: int | None
    response_media_type: str | None
    response_byte_count: int
    response_body_sha256: str | None
    error_code: str | None
    public_message: str | None
    validation_issue_count: int
    validation_phases: tuple[str, ...]
    outcome_verified: bool | None
    http_call_count: int | None
    started_at: datetime
    finished_at: datetime
    traces: tuple[ApiRoutedTraceRecord, ...]


@dataclass(frozen=True)
class _PreparedRoutedExecution:
    claim: ApiRoutedExecutionClaim
    profile: Any
    document: Mapping[str, Any]
    path: Mapping[str, Any]
    query: Mapping[str, Any]
    header: Mapping[str, Any]
    cookie: Mapping[str, Any]


@dataclass(frozen=True)
class ApiRoutedExecutionService:
    sources: LocalSourceRepository
    plans: ApiRoutePlanService
    records: "ApiRoutedExecutionRepository"
    execution: RoutedApiExecutionAdapter

    def require_variant(
        self,
        *,
        owner_id: uuid.UUID,
        conversation_id: str,
        route_session_id: str,
        plan_id: str,
        expected_safety: ApiRoutedSafety,
    ) -> ApiRoutePlanRecord:
        location = self.plans.locate(owner_id=owner_id, plan_id=plan_id)
        with self.sources.locked_revision(
            owner_key=str(owner_id),
            source_id=location.source_id,
            revision_id=location.source_revision_id,
            require_current=True,
        ) as (source, revision_dir):
            record, _context = self.plans.require_execution_locked(
                owner_id=owner_id,
                conversation_id=conversation_id,
                route_session_id=route_session_id,
                plan_id=plan_id,
                source=source,
                revision_dir=revision_dir,
            )
            _selected_step(record, expected_safety)
            claim_path, _ = _paths(revision_dir, plan_id)
            if claim_path.exists():
                raise ApiRoutedExecutionConflict("This route plan was already consumed.")
            return record

    async def execute(
        self,
        *,
        owner_id: uuid.UUID,
        conversation_id: str,
        route_session_id: str,
        plan_id: str,
        expected_safety: ApiRoutedSafety,
        request_id: str,
        approved_write: bool,
    ) -> ApiRoutedExecutionView:
        prepared, replay = self._prepare_claim(
            owner_id=owner_id,
            conversation_id=conversation_id,
            route_session_id=route_session_id,
            plan_id=plan_id,
            expected_safety=expected_safety,
            request_id=request_id,
        )
        if replay is not None:
            return _view(replay)
        claim = prepared.claim
        if expected_safety == "write" and not approved_write:
            outcome = None
            result = _failed_before_http(
                claim,
                "write_approval_required",
                "This API write requires explicit owner review.",
            )
        else:
            try:
                profile = prepared.profile
                outcome = await self.execution.execute(
                    RoutedApiExecutionTarget(
                        execution_id=claim.claim_id,
                        owner_id=owner_id,
                        connection_profile_id=profile.id,
                        base_url=profile.base_url,
                        authentication_method=profile.authentication_method.value,
                        credential_name=profile.credential_name,
                        credential_reference_id=profile.credential_reference_id,
                        credential_version=profile.credential_version,
                        document_hash=MEDUSA_EFFECTIVE_CONTRACT_HASH,
                        document=prepared.document,
                        operation_id=claim.operation_id,
                        path=prepared.path,
                        query=prepared.query,
                        header=prepared.header,
                        cookie=prepared.cookie,
                        approved_write=approved_write,
                    )
                )
                result = _result_from_outcome(claim, outcome)
            except (RoutedApiExecutionError, ValueError):
                result = _failed_before_http(
                    claim,
                    "routed_api_execution_unavailable",
                    "The routed API operation could not be executed.",
                )
        persisted = self.records.complete(owner_key=str(owner_id), result=result)
        return _view(persisted)

    def current(
        self, *, owner_id: uuid.UUID, plan_id: str
    ) -> ApiRoutedExecutionView | None:
        location = self.plans.locate(owner_id=owner_id, plan_id=plan_id)
        result = self.records.current(
            owner_key=str(owner_id),
            source_id=location.source_id,
            source_revision_id=location.source_revision_id,
            plan_id=plan_id,
        )
        return _view(result) if result is not None else None

    def _prepare_claim(
        self,
        *,
        owner_id: uuid.UUID,
        conversation_id: str,
        route_session_id: str,
        plan_id: str,
        expected_safety: ApiRoutedSafety,
        request_id: str,
    ) -> tuple[_PreparedRoutedExecution, ApiRoutedExecutionResult | None]:
        location = self.plans.locate(owner_id=owner_id, plan_id=plan_id)
        with self.sources.locked_revision(
            owner_key=str(owner_id),
            source_id=location.source_id,
            revision_id=location.source_revision_id,
            require_current=True,
        ) as (source, revision_dir):
            record, context = self.plans.require_execution_locked(
                owner_id=owner_id,
                conversation_id=conversation_id,
                route_session_id=route_session_id,
                plan_id=plan_id,
                source=source,
                revision_dir=revision_dir,
            )
            step = _selected_step(record, expected_safety)
            content_path = revision_dir / "i" / source.revision.original_filename
            try:
                content = content_path.read_bytes()
                document = json.loads(content)
            except (OSError, json.JSONDecodeError) as error:
                raise ApiRoutedExecutionError(
                    "The approved API definition is unavailable."
                ) from error
            if (
                hashlib.sha256(content).hexdigest() != source.revision.content_sha256
                or not isinstance(document, Mapping)
                or openapi_document_hash(document) != MEDUSA_EFFECTIVE_CONTRACT_HASH
                or record.document_sha256 != MEDUSA_EFFECTIVE_CONTRACT_HASH
            ):
                raise ApiRoutedExecutionConflict(
                    "The selected API version no longer matches its approved identity."
                )
            path, query, header, cookie = _execution_inputs(
                record=record,
                document=document,
                operation_id=step.selected_operation_id or "",
                method=step.method or "",
                path_template=step.path_template or "",
            )
            claim = ApiRoutedExecutionClaim(
                claim_id=secrets.token_urlsafe(12),
                request_id=request_id,
                boot_id=self.records.boot_id,
                owner_id=owner_id,
                conversation_id=conversation_id,
                route_session_id=route_session_id,
                plan_id=record.plan_id,
                plan_record_id=record.record_id,
                plan_fingerprint=record.plan_fingerprint,
                source_id=record.source_id,
                source_revision_id=record.source_revision_id,
                operation_id=step.selected_operation_id or "",
                method=step.method or "",
                path_template=step.path_template or "",
                safety=expected_safety,
                created_at=datetime.now(UTC),
            )
            existing, replay = self.records.begin_locked(
                revision_dir=revision_dir, claim=claim
            )
            prepared = _PreparedRoutedExecution(
                claim=existing,
                profile=context["profile"],
                document=document,
                path=path,
                query=query,
                header=header,
                cookie=cookie,
            )
            return prepared, replay


@dataclass(frozen=True)
class ApiRoutedExecutionRepository:
    sources: LocalSourceRepository
    boot_id: str = field(default_factory=lambda: secrets.token_urlsafe(18))

    def begin(
        self,
        *,
        owner_key: str,
        claim: ApiRoutedExecutionClaim,
    ) -> tuple[ApiRoutedExecutionClaim, ApiRoutedExecutionResult | None]:
        if claim.boot_id != self.boot_id:
            raise ApiRoutedExecutionError("The execution claim belongs to another runtime boot.")
        with self.sources.locked_revision(
            owner_key=owner_key,
            source_id=claim.source_id,
            revision_id=claim.source_revision_id,
            require_current=True,
        ) as (_, revision_dir):
            return self.begin_locked(revision_dir=revision_dir, claim=claim)

    def begin_locked(
        self,
        *,
        revision_dir: Path,
        claim: ApiRoutedExecutionClaim,
    ) -> tuple[ApiRoutedExecutionClaim, ApiRoutedExecutionResult | None]:
        if claim.boot_id != self.boot_id:
            raise ApiRoutedExecutionError("The execution claim belongs to another runtime boot.")
        claim_path, result_path = _paths(revision_dir, claim.plan_id)
        existing = _read_claim(claim_path)
        if existing is None:
            _write_create_only(claim_path, claim)
            return claim, None
        if existing.request_id != claim.request_id:
            raise ApiRoutedExecutionConflict(
                "This route plan was already consumed by another execution request."
            )
        result = _read_result(result_path)
        if result is not None:
            _require_result_matches(existing, result)
            return existing, result
        if existing.boot_id == self.boot_id:
            raise ApiRoutedExecutionConflict(
                "This route-plan execution is already in progress."
            )
        recovered = _interrupted_result(existing)
        _write_create_only(result_path, recovered)
        return existing, recovered

    def complete(
        self,
        *,
        owner_key: str,
        result: ApiRoutedExecutionResult,
    ) -> ApiRoutedExecutionResult:
        with self.sources.locked_revision(
            owner_key=owner_key,
            source_id=result.source_id,
            revision_id=result.source_revision_id,
        ) as (_, revision_dir):
            claim_path, result_path = _paths(revision_dir, result.plan_id)
            claim = _read_claim(claim_path)
            if claim is None:
                raise ApiRoutedExecutionError("The execution claim is unavailable.")
            _require_result_matches(claim, result)
            if result_path.exists():
                raise ApiRoutedExecutionConflict(
                    "This route-plan execution already has a result."
                )
            _write_create_only(result_path, result)
        return result

    def current(
        self,
        *,
        owner_key: str,
        source_id: str,
        source_revision_id: str,
        plan_id: str,
    ) -> ApiRoutedExecutionResult | None:
        with self.sources.locked_revision(
            owner_key=owner_key,
            source_id=source_id,
            revision_id=source_revision_id,
        ) as (_, revision_dir):
            claim_path, result_path = _paths(revision_dir, plan_id)
            claim = _read_claim(claim_path)
            result = _read_result(result_path)
            if result is not None:
                if claim is None:
                    raise ApiRoutedExecutionError("The execution result is inconsistent.")
                _require_result_matches(claim, result)
            return result


def _paths(revision_dir: Path, plan_id: str) -> tuple[Path, Path]:
    root = revision_dir / "routed-api-executions"
    return root / "claims" / f"{plan_id}.json", root / "results" / f"{plan_id}.json"


def _read_claim(path: Path) -> ApiRoutedExecutionClaim | None:
    if not path.is_file():
        return None
    try:
        return ApiRoutedExecutionClaim.model_validate_json(path.read_text(encoding="utf-8"))
    except (OSError, ValidationError) as error:
        raise ApiRoutedExecutionError("The execution claim is unavailable.") from error


def _read_result(path: Path) -> ApiRoutedExecutionResult | None:
    if not path.is_file():
        return None
    try:
        return ApiRoutedExecutionResult.model_validate_json(path.read_text(encoding="utf-8"))
    except (OSError, ValidationError) as error:
        raise ApiRoutedExecutionError("The execution result is unavailable.") from error


def _write_create_only(path: Path, model: BaseModel) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    try:
        with path.open("x", encoding="utf-8") as handle:
            handle.write(model.model_dump_json(indent=2))
    except FileExistsError as error:
        raise ApiRoutedExecutionConflict("The execution record already exists.") from error
    except OSError as error:
        raise ApiRoutedExecutionError("The execution record could not be persisted.") from error


def _require_result_matches(
    claim: ApiRoutedExecutionClaim, result: ApiRoutedExecutionResult
) -> None:
    facts = (
        result.claim_id == claim.claim_id,
        result.request_id == claim.request_id,
        result.owner_id == claim.owner_id,
        result.conversation_id == claim.conversation_id,
        result.route_session_id == claim.route_session_id,
        result.plan_id == claim.plan_id,
        result.plan_record_id == claim.plan_record_id,
        result.plan_fingerprint == claim.plan_fingerprint,
        result.source_id == claim.source_id,
        result.source_revision_id == claim.source_revision_id,
        result.operation_id == claim.operation_id,
        result.method == claim.method,
        result.path_template == claim.path_template,
        result.safety == claim.safety,
    )
    if not all(facts):
        raise ApiRoutedExecutionError("The execution result is inconsistent.")


def _interrupted_result(claim: ApiRoutedExecutionClaim) -> ApiRoutedExecutionResult:
    now = datetime.now(UTC)
    return ApiRoutedExecutionResult(
        result_id=secrets.token_urlsafe(12),
        **claim.model_dump(
            include={
                "claim_id",
                "request_id",
                "owner_id",
                "conversation_id",
                "route_session_id",
                "plan_id",
                "plan_record_id",
                "plan_fingerprint",
                "source_id",
                "source_revision_id",
                "operation_id",
                "method",
                "path_template",
                "safety",
            }
        ),
        status="outcome_unknown" if claim.safety == "write" else "failed",
        delivery="possibly_sent",
        response_byte_count=0,
        error_code="execution_interrupted",
        public_message=(
            "The API write may have been sent before recovery, so its outcome is unknown."
            if claim.safety == "write"
            else "The API read was interrupted and was not retried."
        ),
        validation_issue_count=0,
        validation_phases=(),
        http_call_count=None,
        started_at=claim.created_at,
        finished_at=now,
        traces=(),
    )


def _selected_step(
    record: ApiRoutePlanRecord, expected_safety: ApiRoutedSafety
):
    if record.state != "ready" or len(record.steps) != 1:
        raise ApiRoutedExecutionConflict(
            "Only one fully resolved API operation can be executed in this phase."
        )
    step = record.steps[0]
    if (
        not step.selected_operation_id
        or not step.method
        or not step.path_template
        or step.http_safety != expected_safety
        or step.selected_operation_id not in record.included_operation_ids
    ):
        raise ApiRoutedExecutionConflict(
            "The selected route plan does not match this execution action."
        )
    return step


def _execution_inputs(
    *,
    record: ApiRoutePlanRecord,
    document: Mapping[str, Any],
    operation_id: str,
    method: str,
    path_template: str,
) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any], dict[str, Any]]:
    try:
        path_item = document["paths"][path_template]
        operation = path_item[method.lower()]
    except (KeyError, TypeError) as error:
        raise ApiRoutedExecutionConflict(
            "The selected operation is missing from the approved contract."
        ) from error
    if not isinstance(operation, Mapping) or operation.get("operationId") != operation_id:
        raise ApiRoutedExecutionConflict(
            "The selected operation no longer matches the approved contract."
        )
    request_body = operation.get("requestBody") or {}
    if isinstance(request_body, Mapping) and request_body.get("required"):
        raise ApiRoutedExecutionConflict(
            "Required API request bodies are not supported in this phase."
        )
    managed = {(item.location, item.name.casefold()) for item in record.managed_parameters}
    by_name: dict[str, list[str]] = {}
    required: set[tuple[str, str]] = set()
    for raw in [*(path_item.get("parameters") or ()), *(operation.get("parameters") or ())]:
        value = _resolve_parameter(document, raw)
        if not isinstance(value, Mapping):
            raise ApiRoutedExecutionConflict("The selected operation has an invalid parameter.")
        name = str(value.get("name", ""))
        location = str(value.get("in", ""))
        if not name or location not in {"path", "query", "header", "cookie"}:
            continue
        if (location, name.casefold()) in managed:
            continue
        by_name.setdefault(name, []).append(location)
        if value.get("required"):
            required.add((location, name))
    outputs: dict[str, dict[str, Any]] = {
        "path": {},
        "query": {},
        "header": {},
        "cookie": {},
    }
    for item in record.input_provenance:
        locations = by_name.get(item.name, [])
        if len(locations) != 1:
            raise ApiRoutedExecutionConflict(
                "A route-plan input does not map uniquely to the selected operation."
            )
        outputs[locations[0]][item.name] = item.value
    missing = [
        name for location, name in sorted(required) if name not in outputs[location]
    ]
    if missing:
        raise ApiRoutedExecutionConflict(
            "The selected route plan is missing a required operation input."
        )
    return outputs["path"], outputs["query"], outputs["header"], outputs["cookie"]


def _resolve_parameter(document: Mapping[str, Any], value: Any) -> Any:
    if not isinstance(value, Mapping) or "$ref" not in value:
        return value
    reference = value.get("$ref")
    if not isinstance(reference, str) or not reference.startswith("#/"):
        raise ApiRoutedExecutionConflict("Only local operation parameter references are supported.")
    selected: Any = document
    for raw_part in reference[2:].split("/"):
        part = raw_part.replace("~1", "/").replace("~0", "~")
        if not isinstance(selected, Mapping) or part not in selected:
            raise ApiRoutedExecutionConflict("The operation parameter reference is unavailable.")
        selected = selected[part]
    return selected


def _result_from_outcome(
    claim: ApiRoutedExecutionClaim,
    outcome: RoutedApiExecutionOutcome,
) -> ApiRoutedExecutionResult:
    status = outcome.status
    if status not in {"succeeded", "failed", "outcome_unknown"}:
        status = "failed"
    return ApiRoutedExecutionResult(
        result_id=secrets.token_urlsafe(12),
        **claim.model_dump(
            include={
                "claim_id",
                "request_id",
                "owner_id",
                "conversation_id",
                "route_session_id",
                "plan_id",
                "plan_record_id",
                "plan_fingerprint",
                "source_id",
                "source_revision_id",
                "operation_id",
                "method",
                "path_template",
                "safety",
            }
        ),
        status=status,
        delivery=outcome.delivery,
        status_code=outcome.status_code,
        response_media_type=outcome.response_media_type,
        response_byte_count=outcome.response_byte_count,
        response_body_sha256=outcome.response_body_sha256,
        error_code=outcome.error_code,
        public_message=outcome.public_message,
        validation_issue_count=outcome.validation_issue_count,
        validation_phases=outcome.validation_phases,
        outcome_verified=outcome.outcome_verified,
        http_call_count=outcome.http_call_count,
        started_at=datetime.fromisoformat(outcome.started_at),
        finished_at=datetime.fromisoformat(outcome.finished_at),
        traces=tuple(
            ApiRoutedTraceRecord(
                event=item.event,
                occurred_at=datetime.fromisoformat(item.occurred_at),
                safe_details=dict(item.safe_details),
            )
            for item in outcome.traces
        ),
    )


def _failed_before_http(
    claim: ApiRoutedExecutionClaim, code: str, message: str
) -> ApiRoutedExecutionResult:
    now = datetime.now(UTC)
    return ApiRoutedExecutionResult(
        result_id=secrets.token_urlsafe(12),
        **claim.model_dump(
            include={
                "claim_id",
                "request_id",
                "owner_id",
                "conversation_id",
                "route_session_id",
                "plan_id",
                "plan_record_id",
                "plan_fingerprint",
                "source_id",
                "source_revision_id",
                "operation_id",
                "method",
                "path_template",
                "safety",
            }
        ),
        status="failed",
        delivery="not_sent",
        response_byte_count=0,
        error_code=code,
        public_message=message,
        validation_issue_count=0,
        validation_phases=(),
        http_call_count=0,
        started_at=now,
        finished_at=now,
        traces=(),
    )


def _view(result: ApiRoutedExecutionResult) -> ApiRoutedExecutionView:
    return ApiRoutedExecutionView(
        **result.model_dump(
            include={
                "result_id",
                "plan_id",
                "source_id",
                "source_revision_id",
                "operation_id",
                "method",
                "path_template",
                "safety",
                "status",
                "delivery",
                "status_code",
                "response_media_type",
                "response_byte_count",
                "response_body_sha256",
                "error_code",
                "public_message",
                "validation_issue_count",
                "validation_phases",
                "outcome_verified",
                "http_call_count",
                "started_at",
                "finished_at",
                "traces",
            }
        )
    )


__all__ = [
    "ApiRoutedDelivery",
    "ApiRoutedExecutionClaim",
    "ApiRoutedExecutionConflict",
    "ApiRoutedExecutionError",
    "ApiRoutedExecutionRepository",
    "ApiRoutedExecutionResult",
    "ApiRoutedExecutionService",
    "ApiRoutedExecutionView",
    "ApiRoutedSafety",
    "ApiRoutedTraceRecord",
]
