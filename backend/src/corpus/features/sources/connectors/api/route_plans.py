from __future__ import annotations

import hashlib
import json
import re
import secrets
import uuid
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any, Literal, Mapping

from pydantic import BaseModel, ConfigDict, Field, ValidationError

from ...contracts import SourceRetrievalResult
from ...models import SourceState, SourceView
from ...repository import LocalSourceRepository, SourceNotReady
from .connections import (
    ApiAuthenticationMethod,
    ApiConnectionProfile,
    ApiConnectionProfileRepository,
)
from .connection_checks import MEDUSA_EFFECTIVE_CONTRACT_HASH
from .engine import ApiSourceEngine, SourceManagedParameter
from .operation_curation import ApiOperationCurationService, ApiOperationInventoryItem


ApiRoutePlanState = Literal[
    "ready",
    "needs_input",
    "needs_operation_choice",
    "not_routable",
]


class ApiRoutePlanError(RuntimeError):
    pass


class ApiRoutePlanConflict(ApiRoutePlanError):
    pass


class ApiRoutePlanRankedOperation(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    operation_id: str
    operation_label: str
    endpoint_id: str
    score: float


class ApiRoutePlanStep(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    query: str
    ranked_operations: tuple[ApiRoutePlanRankedOperation, ...]
    selected_operation_id: str | None = None
    method: str | None = None
    path_template: str | None = None
    http_safety: Literal["read", "write"] | None = None


class ApiRoutePlanInputProvenance(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    name: str
    value: str | int | float | bool
    source: Literal["current_request", "user_clarification"]


class ApiRoutePlanOperationChoice(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    operation_id: str
    source: Literal["user_clarification"] = "user_clarification"


class ApiRoutePlanManagedParameter(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    name: str = Field(min_length=1, max_length=128)
    location: Literal["header"] = "header"
    authentication_method: Literal["api_key"] = "api_key"
    source: Literal["managed_by_profile"] = "managed_by_profile"


class ApiRoutePlanRecord(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    schema_version: int = 1
    plan_id: str = Field(min_length=16, max_length=16)
    record_id: str = Field(min_length=16, max_length=16)
    previous_record_id: str | None = Field(default=None, min_length=16, max_length=16)
    owner_id: uuid.UUID
    conversation_id: str = Field(min_length=16, max_length=64)
    route_session_id: str = Field(min_length=1, max_length=256)
    source_id: str = Field(min_length=16, max_length=16)
    source_revision_id: str = Field(min_length=16, max_length=16)
    artifact_revision_id: str = Field(min_length=16, max_length=16)
    document_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    profile_id: str = Field(min_length=16, max_length=16)
    credential_reference_id: uuid.UUID | None = None
    credential_version: int | None = Field(default=None, ge=1)
    curation_id: str = Field(min_length=16, max_length=16)
    inventory_fingerprint: str = Field(pattern=r"^[0-9a-f]{64}$")
    included_operation_ids: tuple[str, ...]
    allowed_endpoint_ids: tuple[str, ...]
    subset_fingerprint: str = Field(pattern=r"^[0-9a-f]{64}$")
    request_text: str = Field(min_length=1, max_length=4_000)
    request_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    state: ApiRoutePlanState
    steps: tuple[ApiRoutePlanStep, ...]
    missing_inputs: tuple[str, ...] = ()
    input_provenance: tuple[ApiRoutePlanInputProvenance, ...] = ()
    managed_parameters: tuple[ApiRoutePlanManagedParameter, ...] = ()
    operation_choice: ApiRoutePlanOperationChoice | None = None
    clarification_prompt: str | None = Field(default=None, max_length=512)
    created_at: datetime
    expires_at: datetime
    plan_fingerprint: str = Field(pattern=r"^[0-9a-f]{64}$")
    api_call_count: int = Field(default=0, ge=0, le=0)
    router_decision: str
    router_evidence: tuple[dict[str, Any], ...] = ()


class ApiRoutePlanView(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    plan_id: str
    record_id: str
    previous_record_id: str | None
    source_id: str
    source_revision_id: str
    profile_id: str
    curation_id: str
    inventory_fingerprint: str
    subset_fingerprint: str
    request_text: str
    state: ApiRoutePlanState
    steps: tuple[ApiRoutePlanStep, ...]
    missing_inputs: tuple[str, ...]
    input_provenance: tuple[ApiRoutePlanInputProvenance, ...]
    managed_parameters: tuple[ApiRoutePlanManagedParameter, ...]
    operation_choice: ApiRoutePlanOperationChoice | None
    clarification_prompt: str | None
    created_at: datetime
    expires_at: datetime
    plan_fingerprint: str
    api_call_count: int = 0


class _ApiRoutePlanPointer(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    schema_version: int = 1
    conversation_id: str
    route_session_id: str
    plan_id: str
    current_record_id: str


class _ApiRoutePlanOwnerIndex(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    schema_version: int = 1
    plan_id: str = Field(min_length=16, max_length=16)
    source_id: str = Field(min_length=16, max_length=16)
    source_revision_id: str = Field(min_length=16, max_length=16)
    conversation_id: str = Field(min_length=16, max_length=64)
    route_session_id: str = Field(min_length=1, max_length=256)
    current_record_id: str = Field(min_length=16, max_length=16)


@dataclass(frozen=True)
class ApiRoutePlanService:
    sources: LocalSourceRepository
    curations: ApiOperationCurationService
    profiles: ApiConnectionProfileRepository
    engine: ApiSourceEngine
    ttl: timedelta = timedelta(minutes=30)

    def locate(self, *, owner_id: uuid.UUID, plan_id: str) -> _ApiRoutePlanOwnerIndex:
        path = self.sources.owner_route_plan_index_path(
            owner_key=str(owner_id), plan_id=plan_id
        )
        try:
            value = _ApiRoutePlanOwnerIndex.model_validate_json(
                path.read_text(encoding="utf-8")
            )
        except FileNotFoundError as error:
            raise ApiRoutePlanConflict(
                "This route plan predates executable plan indexing. Prepare a new plan."
            ) from error
        except (OSError, ValidationError) as error:
            raise ApiRoutePlanError("The route plan index is unavailable.") from error
        if value.plan_id != plan_id:
            raise ApiRoutePlanError("The route plan index is inconsistent.")
        return value

    def require_execution_locked(
        self,
        *,
        owner_id: uuid.UUID,
        conversation_id: str,
        route_session_id: str,
        plan_id: str,
        source: SourceView,
        revision_dir: Path,
    ) -> tuple[ApiRoutePlanRecord, dict[str, Any]]:
        pointer = _read_pointer(revision_dir, conversation_id)
        if pointer is None:
            raise ApiRoutePlanConflict("The route plan is unavailable in this conversation.")
        index_path = self.sources.owner_route_plan_index_path(
            owner_key=str(owner_id), plan_id=plan_id
        )
        try:
            index = _ApiRoutePlanOwnerIndex.model_validate_json(
                index_path.read_text(encoding="utf-8")
            )
        except FileNotFoundError as error:
            raise ApiRoutePlanConflict(
                "This route plan predates executable plan indexing. Prepare a new plan."
            ) from error
        except (OSError, ValidationError) as error:
            raise ApiRoutePlanError("The route plan index is unavailable.") from error
        facts = (
            pointer.plan_id == plan_id,
            pointer.route_session_id == route_session_id,
            index.plan_id == plan_id,
            index.source_id == source.source_id,
            index.source_revision_id == source.revision.revision_id,
            index.conversation_id == conversation_id,
            index.route_session_id == route_session_id,
            index.current_record_id == pointer.current_record_id,
        )
        if not all(facts):
            raise ApiRoutePlanConflict("The route plan changed. Prepare a new plan.")
        record = _load_pointer_record(revision_dir, pointer)
        if record.owner_id != owner_id or record.plan_id != plan_id:
            raise ApiRoutePlanError("The saved route plan is unavailable.")
        if record.expires_at <= datetime.now(UTC):
            raise ApiRoutePlanConflict("The route plan expired.")
        context = self._context_locked(
            owner_id=owner_id,
            source=source,
            revision_dir=revision_dir,
            profile_id=record.profile_id,
            curation_id=record.curation_id,
        )
        if not _context_matches_record(context, record):
            raise ApiRoutePlanConflict(
                "The selected revision, curation, or profile changed. Prepare a new plan."
            )
        return record, context

    def create(
        self,
        *,
        owner_id: uuid.UUID,
        conversation_id: str,
        route_session_id: str,
        source_id: str,
        source_revision_id: str,
        profile_id: str,
        curation_id: str,
        request_text: str,
        provided_inputs: Mapping[str, Any] | None = None,
    ) -> ApiRoutePlanView:
        normalized = _request_text(request_text)
        inputs = _safe_inputs(provided_inputs or {})
        with self.sources.locked_revision(
            owner_key=str(owner_id),
            source_id=source_id,
            revision_id=source_revision_id,
            require_current=True,
        ) as (source, revision_dir):
            context = self._context_locked(
                owner_id=owner_id,
                source=source,
                revision_dir=revision_dir,
                profile_id=profile_id,
                curation_id=curation_id,
            )
            pointer = _read_pointer(revision_dir, conversation_id)
            if pointer is not None:
                existing = _load_pointer_record(revision_dir, pointer)
                if (
                    existing.expires_at > datetime.now(UTC)
                    and pointer.route_session_id == route_session_id
                ):
                    raise ApiRoutePlanConflict(
                        "A route plan is already active for this conversation and Source revision."
                    )
            return self._route_locked(
                owner_id=owner_id,
                conversation_id=conversation_id,
                route_session_id=route_session_id,
                source=source,
                revision_dir=revision_dir,
                context=context,
                request_text=normalized,
                inputs=inputs,
                provenance_source="current_request",
                provenance_updates=frozenset(inputs),
                plan_id=secrets.token_urlsafe(12),
                previous=None,
                operation_choice=None,
            )

    def clarify(
        self,
        *,
        owner_id: uuid.UUID,
        conversation_id: str,
        route_session_id: str,
        source_id: str,
        source_revision_id: str,
        plan_id: str,
        expected_record_id: str,
        answers: Mapping[str, Any],
    ) -> ApiRoutePlanView:
        provided = _safe_inputs(answers)
        if not provided:
            raise ApiRoutePlanConflict("A clarification answer is required.")
        with self.sources.locked_revision(
            owner_key=str(owner_id),
            source_id=source_id,
            revision_id=source_revision_id,
            require_current=True,
        ) as (source, revision_dir):
            previous = _current_record(
                revision_dir,
                conversation_id=conversation_id,
                route_session_id=route_session_id,
            )
            if (
                previous.owner_id != owner_id
                or previous.plan_id != plan_id
                or previous.record_id != expected_record_id
                or previous.source_id != source_id
                or previous.source_revision_id != source_revision_id
            ):
                raise ApiRoutePlanConflict(
                    "The route plan changed. Refresh it before answering."
                )
            if previous.expires_at <= datetime.now(UTC):
                raise ApiRoutePlanConflict("The route plan expired.")
            if previous.state not in {"needs_input", "needs_operation_choice"}:
                raise ApiRoutePlanConflict("The route plan is not waiting for clarification.")
            context = self._context_locked(
                owner_id=owner_id,
                source=source,
                revision_dir=revision_dir,
                profile_id=previous.profile_id,
                curation_id=previous.curation_id,
            )
            if not _context_matches_record(context, previous):
                raise ApiRoutePlanConflict(
                    "The selected revision, curation, or profile changed. Start a new plan."
                )
            inputs = {item.name: item.value for item in previous.input_provenance}
            operation_choice = previous.operation_choice
            if previous.state == "needs_operation_choice":
                if set(provided) != {"operation_id"}:
                    raise ApiRoutePlanConflict("Choose exactly one listed operation.")
                operation_id = provided["operation_id"]
                candidates = {
                    ranked.operation_id
                    for step in previous.steps
                    for ranked in step.ranked_operations
                }
                if not isinstance(operation_id, str) or operation_id not in candidates:
                    raise ApiRoutePlanConflict("Choose exactly one listed operation.")
                if operation_id not in context["endpoint_map"]:
                    raise ApiRoutePlanConflict("The chosen operation is no longer available.")
                operation_choice = ApiRoutePlanOperationChoice(
                    operation_id=operation_id
                )
                provenance_updates: frozenset[str] = frozenset()
            else:
                inputs.update(provided)
                provenance_updates = frozenset(provided)
            return self._route_locked(
                owner_id=owner_id,
                conversation_id=conversation_id,
                route_session_id=route_session_id,
                source=source,
                revision_dir=revision_dir,
                context=context,
                request_text=previous.request_text,
                inputs=inputs,
                provenance_source="user_clarification",
                provenance_updates=provenance_updates,
                plan_id=previous.plan_id,
                previous=previous,
                operation_choice=operation_choice,
            )

    def current(
        self,
        *,
        owner_id: uuid.UUID,
        conversation_id: str,
        route_session_id: str,
        source_id: str,
        source_revision_id: str,
    ) -> ApiRoutePlanView | None:
        with self.sources.locked_revision(
            owner_key=str(owner_id),
            source_id=source_id,
            revision_id=source_revision_id,
            require_current=True,
        ) as (source, revision_dir):
            pointer = _read_pointer(revision_dir, conversation_id)
            if pointer is None:
                return None
            pointed = _load_pointer_record(revision_dir, pointer)
            if (
                pointer.route_session_id != route_session_id
                or pointed.expires_at <= datetime.now(UTC)
            ):
                return None
            record = _current_record(
                revision_dir,
                conversation_id=conversation_id,
                route_session_id=route_session_id,
            )
            if record.owner_id != owner_id:
                raise ApiRoutePlanError("The saved route plan is unavailable.")
            context = self._context_locked(
                owner_id=owner_id,
                source=source,
                revision_dir=revision_dir,
                profile_id=record.profile_id,
                curation_id=record.curation_id,
            )
            if not _context_matches_record(context, record):
                raise ApiRoutePlanConflict(
                    "The selected revision, curation, or profile changed. Start a new plan."
                )
            if record.expires_at <= datetime.now(UTC):
                raise ApiRoutePlanConflict("The route plan expired.")
            return _view(record)

    def _context_locked(
        self,
        *,
        owner_id: uuid.UUID,
        source: SourceView,
        revision_dir: Path,
        profile_id: str,
        curation_id: str,
    ) -> dict[str, Any]:
        if source.connector_key != "api" or source.revision.state is not SourceState.READY:
            raise SourceNotReady("The selected API Source revision is not ready.")
        if (
            source.revision.summary.get("revision_kind") != "reviewed_api_contract"
            or source.revision.summary.get("final_canonical_sha256")
            != MEDUSA_EFFECTIVE_CONTRACT_HASH
        ):
            raise ApiRoutePlanConflict(
                "The selected API Source revision is not the approved effective contract."
            )
        curation = self.curations.inspect_locked(
            owner_id=owner_id,
            source=source,
            revision_dir=revision_dir,
        )
        if curation.current is None or curation.current.id != curation_id:
            raise ApiRoutePlanConflict("The selected operation curation is no longer current.")
        if not curation.current.included_operation_ids:
            raise ApiRoutePlanConflict("The current operation curation includes no operations.")
        profile = self.profiles.get_exact_locked(
            source_id=source.source_id,
            revision_id=source.revision.revision_id,
            profile_id=profile_id,
            revision_dir=revision_dir,
        )
        managed_parameters = _managed_parameters(profile)
        endpoint_map, graph_sha256 = _endpoint_map(source, revision_dir, curation.operations)
        allowed_endpoint_ids = tuple(
            endpoint_map[operation_id][0]
            for operation_id in curation.current.included_operation_ids
        )
        artifact_revision_id = source.revision.artifact_revision_id or source.revision.revision_id
        subset_fingerprint = _hash(
            {
                "source_id": source.source_id,
                "source_revision_id": source.revision.revision_id,
                "artifact_revision_id": artifact_revision_id,
                "graph_sha256": graph_sha256,
                "curation_id": curation.current.id,
                "inventory_fingerprint": curation.inventory_fingerprint,
                "included_operation_ids": list(curation.current.included_operation_ids),
                "allowed_endpoint_ids": list(allowed_endpoint_ids),
            }
        )
        return {
            "profile": profile,
            "managed_parameters": managed_parameters,
            "curation": curation.current,
            "inventory_fingerprint": curation.inventory_fingerprint,
            "endpoint_map": endpoint_map,
            "allowed_endpoint_ids": allowed_endpoint_ids,
            "artifact_revision_id": artifact_revision_id,
            "artifact_dir": revision_dir.parent.parent / "r" / artifact_revision_id / "a",
            "subset_fingerprint": subset_fingerprint,
        }

    def _route_locked(
        self,
        *,
        owner_id: uuid.UUID,
        conversation_id: str,
        route_session_id: str,
        source: SourceView,
        revision_dir: Path,
        context: dict[str, Any],
        request_text: str,
        inputs: dict[str, str | int | float | bool],
        provenance_source: Literal["current_request", "user_clarification"],
        provenance_updates: frozenset[str],
        plan_id: str,
        previous: ApiRoutePlanRecord | None,
        operation_choice: ApiRoutePlanOperationChoice | None,
    ) -> ApiRoutePlanView:
        retrieval_endpoint_ids = context["allowed_endpoint_ids"]
        if operation_choice is not None:
            selected = context["endpoint_map"].get(operation_choice.operation_id)
            if selected is None or selected[0] not in retrieval_endpoint_ids:
                raise ApiRoutePlanConflict("The chosen operation is no longer available.")
            retrieval_endpoint_ids = (selected[0],)
        result = self.engine.retrieve(
            artifact_dir=context["artifact_dir"],
            query=request_text,
            top_k=5,
            trace_mode="bounded",
            provided_params=inputs,
            allowed_endpoint_ids=retrieval_endpoint_ids,
            managed_parameters=tuple(
                SourceManagedParameter(name=value.name, location=value.location)
                for value in context["managed_parameters"]
            ),
        )
        state = _state(result)
        steps = _steps(result, context["endpoint_map"], retrieval_endpoint_ids)
        now = datetime.now(UTC)
        provenance_by_name = (
            {item.name: item for item in previous.input_provenance}
            if previous is not None
            else {}
        )
        for name, value in inputs.items():
            prior = provenance_by_name.get(name)
            provenance_by_name[name] = ApiRoutePlanInputProvenance(
                name=name,
                value=value,
                source=(
                    provenance_source
                    if name in provenance_updates or prior is None
                    else prior.source
                ),
            )
        profile = context["profile"]
        curation = context["curation"]
        payload = {
            "plan_id": plan_id,
            "record_id": secrets.token_urlsafe(12),
            "previous_record_id": previous.record_id if previous is not None else None,
            "owner_id": owner_id,
            "conversation_id": conversation_id,
            "route_session_id": route_session_id,
            "source_id": source.source_id,
            "source_revision_id": source.revision.revision_id,
            "artifact_revision_id": context["artifact_revision_id"],
            "document_sha256": MEDUSA_EFFECTIVE_CONTRACT_HASH,
            "profile_id": profile.id,
            "credential_reference_id": profile.credential_reference_id,
            "credential_version": profile.credential_version,
            "curation_id": curation.id,
            "inventory_fingerprint": context["inventory_fingerprint"],
            "included_operation_ids": curation.included_operation_ids,
            "allowed_endpoint_ids": context["allowed_endpoint_ids"],
            "subset_fingerprint": context["subset_fingerprint"],
            "request_text": request_text,
            "request_sha256": hashlib.sha256(request_text.encode("utf-8")).hexdigest(),
            "state": state,
            "steps": steps,
            "missing_inputs": tuple(result.missing_inputs),
            "input_provenance": tuple(
                provenance_by_name[name] for name in sorted(provenance_by_name)
            ),
            "managed_parameters": context["managed_parameters"],
            "operation_choice": operation_choice,
            "clarification_prompt": _clarification_prompt(state, result),
            "created_at": now,
            "expires_at": now + self.ttl,
            "api_call_count": 0,
            "router_decision": result.decision_type,
            "router_evidence": tuple(
                _safe_router_evidence(step.trace) for step in result.steps
            ),
        }
        payload["plan_fingerprint"] = "0" * 64
        draft = ApiRoutePlanRecord.model_validate(payload)
        record = draft.model_copy(
            update={"plan_fingerprint": _record_fingerprint(draft)}
        )
        _write_record_and_pointer(
            revision_dir,
            record,
            owner_index_path=self.sources.owner_route_plan_index_path(
                owner_key=str(owner_id), plan_id=record.plan_id
            ),
        )
        return _view(record)


def _endpoint_map(
    source: SourceView,
    revision_dir: Path,
    inventory: tuple[ApiOperationInventoryItem, ...],
) -> tuple[dict[str, tuple[str, ApiOperationInventoryItem, str]], str]:
    artifact_revision_id = source.revision.artifact_revision_id or source.revision.revision_id
    path = revision_dir.parent.parent / "r" / artifact_revision_id / "a" / "graph" / "semantic_graph.json"
    try:
        raw = path.read_bytes()
        document = json.loads(raw)
        rows = document["nodes"]
    except (OSError, UnicodeDecodeError, json.JSONDecodeError, KeyError, TypeError) as error:
        raise ApiRoutePlanError("The ToolRouter operation index is unavailable.") from error
    by_graph_id = {item.graph_node_id: item for item in inventory}
    values: dict[str, tuple[str, ApiOperationInventoryItem, str]] = {}
    for row in rows:
        if not isinstance(row, dict) or row.get("id") not in by_graph_id:
            continue
        endpoint_id = row.get("endpoint_id")
        label = row.get("label")
        item = by_graph_id[str(row["id"])]
        if (
            not isinstance(endpoint_id, str)
            or not endpoint_id
            or not isinstance(label, str)
            or not label.strip()
        ):
            raise ApiRoutePlanError("The ToolRouter operation index is invalid.")
        if item.operation_id in values:
            raise ApiRoutePlanError("The ToolRouter operation index is invalid.")
        values[item.operation_id] = (endpoint_id, item, label.strip())
    if set(values) != {item.operation_id for item in inventory}:
        raise ApiRoutePlanError("The ToolRouter operation index is incomplete.")
    return values, hashlib.sha256(raw).hexdigest()


def _steps(
    result: SourceRetrievalResult,
    endpoint_map: dict[str, tuple[str, ApiOperationInventoryItem, str]],
    allowed_endpoint_ids: tuple[str, ...],
) -> tuple[ApiRoutePlanStep, ...]:
    by_endpoint = {
        value[0]: (operation_id, value[1], value[2])
        for operation_id, value in endpoint_map.items()
    }
    allowed = set(allowed_endpoint_ids)
    values: list[ApiRoutePlanStep] = []
    for step in result.steps:
        ranked: list[ApiRoutePlanRankedOperation] = []
        for item in step.ranked_items:
            if item.item_id not in allowed or item.item_id not in by_endpoint:
                raise ApiRoutePlanError("ToolRouter returned an operation outside the accepted curation.")
            operation_id, _inventory, operation_label = by_endpoint[item.item_id]
            ranked.append(
                ApiRoutePlanRankedOperation(
                    operation_id=operation_id,
                    operation_label=operation_label,
                    endpoint_id=item.item_id,
                    score=item.score,
                )
            )
        selected_operation_id = (
            ranked[0].operation_id
            if ranked and result.decision_type != "ASK_DISAMBIGUATE"
            else None
        )
        inventory = (
            by_endpoint[ranked[0].endpoint_id][1]
            if selected_operation_id is not None
            else None
        )
        values.append(
            ApiRoutePlanStep(
                query=step.query,
                ranked_operations=tuple(ranked),
                selected_operation_id=selected_operation_id,
                method=inventory.method if inventory else None,
                path_template=inventory.path_template if inventory else None,
                http_safety=(
                    _http_safety(inventory.method) if inventory is not None else None
                ),
            )
        )
    return tuple(values)


def _state(result: SourceRetrievalResult) -> ApiRoutePlanState:
    if result.decision_type == "ROUTE":
        if result.missing_inputs or not result.steps or any(not step.ranked_items for step in result.steps):
            return "needs_input"
        return "ready"
    if result.decision_type == "ASK_PARAM":
        return "needs_input"
    if result.decision_type == "ASK_DISAMBIGUATE":
        return "needs_operation_choice"
    if result.decision_type in {"NO_TOOL", "ABSTAIN"}:
        return "not_routable"
    raise ApiRoutePlanError("ToolRouter returned an unsupported planning result.")


def _clarification_prompt(
    state: ApiRoutePlanState,
    result: SourceRetrievalResult,
) -> str | None:
    if state == "needs_input":
        name = result.missing_inputs[0] if result.missing_inputs else None
        return f"What should Corpus use for {name}?" if name else "What required value should Corpus use?"
    if state == "needs_operation_choice":
        return "Which of these included operations did you mean?"
    return None


def _http_safety(method: str) -> Literal["read", "write"]:
    return "read" if method.upper() in {"GET", "HEAD", "OPTIONS"} else "write"


def _safe_inputs(values: Mapping[str, Any]) -> dict[str, str | int | float | bool]:
    if len(values) > 50:
        raise ApiRoutePlanConflict("Too many route-plan inputs were provided.")
    safe: dict[str, str | int | float | bool] = {}
    for raw_name, value in values.items():
        name = str(raw_name).strip()
        if not name or len(name) > 128 or _sensitive_name(name):
            raise ApiRoutePlanConflict("A route-plan input name is invalid.")
        if not isinstance(value, (str, int, float, bool)) or isinstance(value, str) and len(value) > 2_000:
            raise ApiRoutePlanConflict("A route-plan input value is invalid.")
        if isinstance(value, str) and _secret_like_value(value):
            raise ApiRoutePlanConflict("A route-plan input value is invalid.")
        safe[name] = value
    return safe


def _safe_router_evidence(value: Mapping[str, Any]) -> dict[str, Any]:
    def clean(item: Any, *, depth: int = 0) -> Any:
        if depth > 6:
            raise ApiRoutePlanError("ToolRouter route evidence is too deeply nested.")
        if item is None or isinstance(item, (bool, int, float)):
            return item
        if isinstance(item, str):
            if len(item) > 4_000 or _secret_like_value(item):
                raise ApiRoutePlanError("ToolRouter route evidence is too large.")
            return item
        if isinstance(item, Mapping):
            if len(item) > 200:
                raise ApiRoutePlanError("ToolRouter route evidence is too large.")
            output: dict[str, Any] = {}
            for raw_key, nested in item.items():
                key = str(raw_key)
                if _sensitive_name(key) or key.casefold() in {"request_body", "response_body"}:
                    raise ApiRoutePlanError("ToolRouter route evidence contains a forbidden field.")
                output[key] = clean(nested, depth=depth + 1)
            return output
        if isinstance(item, (list, tuple)):
            if len(item) > 500:
                raise ApiRoutePlanError("ToolRouter route evidence is too large.")
            return [clean(nested, depth=depth + 1) for nested in item]
        raise ApiRoutePlanError("ToolRouter route evidence is invalid.")

    return clean(value)


def _request_text(value: str) -> str:
    normalized = " ".join(value.split())
    if not normalized or len(normalized) > 4_000 or _secret_like_value(normalized):
        raise ApiRoutePlanConflict("A route-planning request is required.")
    return normalized


def _sensitive_name(value: str) -> bool:
    normalized = re.sub(r"([a-z0-9])([A-Z])", r"\1_\2", value).casefold()
    collapsed = re.sub(r"[^a-z0-9]", "", normalized)
    fragments = (
        "authorization",
        "bearer",
        "cookie",
        "credential",
        "password",
        "passwd",
        "secret",
        "token",
        "apikey",
        "privatekey",
        "publishablekey",
        "accesskey",
        "clientkey",
    )
    return any(fragment in collapsed for fragment in fragments) or "header" in {
        token for token in re.split(r"[^a-z0-9]+", normalized) if token
    }


def _secret_like_value(value: str) -> bool:
    stripped = value.strip()
    return bool(
        re.search(r"(?i)\bbearer\s+[a-z0-9._~+/=-]{8,}", stripped)
        or "-----BEGIN PRIVATE KEY-----" in stripped
        or re.fullmatch(r"eyJ[a-zA-Z0-9_-]{8,}\.[a-zA-Z0-9_-]{8,}\.[a-zA-Z0-9_-]{8,}", stripped)
        or re.search(
            r"(?i)\b(?:authorization|cookie|client[_ -]?secret|access[_ -]?token|"
            r"refresh[_ -]?token|x[_ -]?api[_ -]?key|x[_ -]?publishable[_ -]?api[_ -]?key)"
            r"\s*[:=]\s*\S+",
            stripped,
        )
    )


def _context_matches_record(context: dict[str, Any], record: ApiRoutePlanRecord) -> bool:
    profile = context["profile"]
    curation = context["curation"]
    return (
        profile.id == record.profile_id
        and profile.credential_reference_id == record.credential_reference_id
        and profile.credential_version == record.credential_version
        and curation.id == record.curation_id
        and curation.included_operation_ids == record.included_operation_ids
        and context["inventory_fingerprint"] == record.inventory_fingerprint
        and context["allowed_endpoint_ids"] == record.allowed_endpoint_ids
        and context["subset_fingerprint"] == record.subset_fingerprint
        and context["managed_parameters"] == record.managed_parameters
    )


def _managed_parameters(
    profile: ApiConnectionProfile,
) -> tuple[ApiRoutePlanManagedParameter, ...]:
    if profile.authentication_method is not ApiAuthenticationMethod.API_KEY:
        return ()
    name = (profile.credential_name or "").strip()
    if not name or profile.credential_reference_id is None or profile.credential_version is None:
        raise ApiRoutePlanConflict(
            "The selected connection profile has no usable managed authentication."
        )
    return (ApiRoutePlanManagedParameter(name=name),)


def _root(revision_dir: Path) -> Path:
    return revision_dir / "api-route-plans"


def _pointer_path(revision_dir: Path, conversation_id: str) -> Path:
    key = hashlib.sha256(conversation_id.encode("utf-8")).hexdigest()
    return _root(revision_dir) / "conversations" / f"{key}.json"


def _read_pointer(revision_dir: Path, conversation_id: str) -> _ApiRoutePlanPointer | None:
    path = _pointer_path(revision_dir, conversation_id)
    if not path.exists():
        return None
    try:
        pointer = _ApiRoutePlanPointer.model_validate_json(path.read_text(encoding="utf-8"))
    except (OSError, ValidationError) as error:
        raise ApiRoutePlanError("The saved route plan is unavailable.") from error
    if pointer.conversation_id != conversation_id:
        raise ApiRoutePlanError("The saved route plan is inconsistent.")
    return pointer


def _current_record(
    revision_dir: Path,
    *,
    conversation_id: str,
    route_session_id: str,
) -> ApiRoutePlanRecord:
    pointer = _read_pointer(revision_dir, conversation_id)
    if pointer is None or pointer.route_session_id != route_session_id:
        raise ApiRoutePlanConflict("The route plan is unavailable in this conversation.")
    record = _load_record(revision_dir, pointer.current_record_id)
    if (
        record.record_id != pointer.current_record_id
        or record.plan_id != pointer.plan_id
        or record.conversation_id != pointer.conversation_id
        or record.route_session_id != pointer.route_session_id
    ):
        raise ApiRoutePlanError("The saved route plan is inconsistent.")
    current = record
    seen = {record.record_id}
    while current.previous_record_id is not None:
        if len(seen) > 100:
            raise ApiRoutePlanError("The saved route plan is inconsistent.")
        previous = _load_record(revision_dir, current.previous_record_id)
        if (
            previous.record_id in seen
            or previous.plan_id != record.plan_id
            or previous.owner_id != record.owner_id
            or previous.conversation_id != record.conversation_id
            or previous.route_session_id != record.route_session_id
            or previous.source_id != record.source_id
            or previous.source_revision_id != record.source_revision_id
            or previous.created_at > current.created_at
        ):
            raise ApiRoutePlanError("The saved route plan is inconsistent.")
        seen.add(previous.record_id)
        current = previous
    return record


def _load_pointer_record(
    revision_dir: Path, pointer: _ApiRoutePlanPointer
) -> ApiRoutePlanRecord:
    record = _load_record(revision_dir, pointer.current_record_id)
    if (
        record.record_id != pointer.current_record_id
        or record.plan_id != pointer.plan_id
        or record.conversation_id != pointer.conversation_id
        or record.route_session_id != pointer.route_session_id
    ):
        raise ApiRoutePlanError("The saved route plan is inconsistent.")
    return record


def _load_record(revision_dir: Path, record_id: str) -> ApiRoutePlanRecord:
    try:
        record = ApiRoutePlanRecord.model_validate_json(
            (_root(revision_dir) / "records" / f"{record_id}.json").read_text(
                encoding="utf-8"
            )
        )
    except (OSError, ValidationError) as error:
        raise ApiRoutePlanError("The saved route plan is unavailable.") from error
    if record.record_id != record_id or record.plan_fingerprint != _record_fingerprint(record):
        raise ApiRoutePlanError("The saved route plan is inconsistent.")
    return record


def _write_record_and_pointer(
    revision_dir: Path,
    record: ApiRoutePlanRecord,
    *,
    owner_index_path: Path,
) -> None:
    root = _root(revision_dir)
    record_path = root / "records" / f"{record.record_id}.json"
    if record_path.exists():
        raise ApiRoutePlanConflict("The route-plan record identity already exists.")
    _write_atomic(record_path, record)
    _write_atomic(
        owner_index_path,
        _ApiRoutePlanOwnerIndex(
            plan_id=record.plan_id,
            source_id=record.source_id,
            source_revision_id=record.source_revision_id,
            conversation_id=record.conversation_id,
            route_session_id=record.route_session_id,
            current_record_id=record.record_id,
        ),
    )
    _write_atomic(
        _pointer_path(revision_dir, record.conversation_id),
        _ApiRoutePlanPointer(
            conversation_id=record.conversation_id,
            route_session_id=record.route_session_id,
            plan_id=record.plan_id,
            current_record_id=record.record_id,
        ),
    )


def _write_atomic(path: Path, model: BaseModel) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    try:
        temporary.write_text(model.model_dump_json(indent=2), encoding="utf-8")
        temporary.replace(path)
    except OSError as error:
        raise ApiRoutePlanError("The route plan could not be persisted.") from error


def _view(record: ApiRoutePlanRecord) -> ApiRoutePlanView:
    return ApiRoutePlanView(
        **record.model_dump(
            include={
                "plan_id", "record_id", "previous_record_id", "source_id",
                "source_revision_id", "profile_id", "curation_id",
                "inventory_fingerprint", "subset_fingerprint", "request_text",
                "state", "steps", "missing_inputs", "input_provenance",
                "managed_parameters", "operation_choice",
                "clarification_prompt", "created_at", "expires_at",
                "plan_fingerprint", "api_call_count",
            }
        )
    )


def _hash(value: Any) -> str:
    encoded = json.dumps(value, sort_keys=True, separators=(",", ":"), default=str).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def _record_fingerprint(record: ApiRoutePlanRecord) -> str:
    return _hash(
        {
            key: value
            for key, value in record.model_dump(mode="json").items()
            if key != "plan_fingerprint"
        }
    )


__all__ = [
    "ApiRoutePlanConflict",
    "ApiRoutePlanError",
    "ApiRoutePlanManagedParameter",
    "ApiRoutePlanOperationChoice",
    "ApiRoutePlanRecord",
    "ApiRoutePlanService",
    "ApiRoutePlanState",
    "ApiRoutePlanView",
]
