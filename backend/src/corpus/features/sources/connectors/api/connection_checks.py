from __future__ import annotations

import secrets
import uuid
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Mapping

from pydantic import BaseModel, ConfigDict, Field, ValidationError

from corpus.credentials import CredentialVaultPort
from corpus.shared.api_execution import (
    RedactedApiExecution,
    SafeApiExecutionError,
    SafeApiExecutionPort,
    SafeApiExecutionTarget,
    SafeApiTraceRecord,
)

from ...models import SourceState
from ...repository import LocalSourceRepository, SourceNotReady, SourceRepositoryError
from .connections import (
    ApiAuthenticationMethod,
    ApiConnectionError,
    ApiConnectionProfile,
    ApiConnectionProfileRepository,
)
from .reviewed_revision import ReviewedApiRevisionMismatch, load_reviewed_document


SAFE_API_OPERATIONS: Mapping[str, tuple[str, str]] = {
    "GetProductTypes": ("GET", "/store/product-types"),
    "GetProductTags": ("GET", "/store/product-tags"),
}


class ApiConnectionCheckRecord(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    schema_version: int = 1
    id: str = Field(min_length=16, max_length=16)
    execution_id: str = Field(min_length=16, max_length=16)
    source_id: str = Field(min_length=16, max_length=16)
    source_revision_id: str = Field(min_length=16, max_length=16)
    connection_profile_id: str = Field(min_length=16, max_length=16)
    credential_reference_id: uuid.UUID | None = None
    credential_version: int | None = Field(default=None, ge=1)
    operation_id: str
    method: str
    path_template: str
    effective_contract_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    status: str
    status_code: int | None = None
    error_code: str | None = None
    public_message: str | None = None
    validation_issue_count: int = Field(ge=0)
    validation_phases: tuple[str, ...]
    http_call_count: int = Field(ge=0, le=1)
    started_at: datetime
    finished_at: datetime
    traces: tuple[SafeApiTraceRecord, ...]


class ApiConnectionCheckError(RuntimeError):
    pass


class ApiConnectionCheckConflict(ApiConnectionCheckError):
    pass


@dataclass(frozen=True)
class PreparedApiConnectionCheck:
    owner_id: uuid.UUID
    source_id: str
    source_revision_id: str
    profile: ApiConnectionProfile
    operation_id: str
    method: str
    path_template: str
    document: Mapping[str, Any]
    document_hash: str


@dataclass(frozen=True)
class ApiConnectionCheckRepository:
    sources: LocalSourceRepository

    def append(
        self, *, owner_key: str, record: ApiConnectionCheckRecord
    ) -> ApiConnectionCheckRecord:
        with self.sources.locked_revision(
            owner_key=owner_key,
            source_id=record.source_id,
            revision_id=record.source_revision_id,
        ) as (_, revision_dir):
            path = revision_dir / "connection-checks" / f"{record.id}.json"
            if path.exists():
                raise ApiConnectionCheckConflict(
                    "The API connection check identity already exists."
                )
            temporary = path.with_suffix(".json.tmp")
            try:
                path.parent.mkdir(parents=True, exist_ok=True)
                temporary.write_text(record.model_dump_json(indent=2), encoding="utf-8")
                temporary.replace(path)
            except OSError as error:
                raise ApiConnectionCheckError(
                    "The API connection check result could not be persisted."
                ) from error
        return record

    def list(
        self, *, owner_key: str, source_id: str, revision_id: str
    ) -> tuple[ApiConnectionCheckRecord, ...]:
        with self.sources.locked_revision(
            owner_key=owner_key,
            source_id=source_id,
            revision_id=revision_id,
        ) as (_, revision_dir):
            root = revision_dir / "connection-checks"
            if not root.is_dir():
                return ()
            values: list[ApiConnectionCheckRecord] = []
            try:
                for path in root.glob("*.json"):
                    values.append(
                        ApiConnectionCheckRecord.model_validate_json(
                            path.read_text(encoding="utf-8")
                        )
                    )
            except (OSError, ValidationError) as error:
                raise ApiConnectionCheckError(
                    "The API connection check results are unavailable."
                ) from error
            return tuple(sorted(values, key=lambda item: (item.started_at, item.id)))


@dataclass(frozen=True)
class ApiConnectionCheckService:
    sources: LocalSourceRepository
    profiles: ApiConnectionProfileRepository
    records: ApiConnectionCheckRepository
    credentials: CredentialVaultPort
    execution: SafeApiExecutionPort

    def require_executable(
        self,
        *,
        owner_id: uuid.UUID,
        source_id: str,
        source_revision_id: str,
        connection_profile_id: str,
        operation_id: str,
    ) -> PreparedApiConnectionCheck:
        owner_key = str(owner_id)
        source = self.sources.get_revision(
            owner_key=owner_key,
            source_id=source_id,
            revision_id=source_revision_id,
        )
        if source.connector_key != "api" or source.revision.state is not SourceState.READY:
            raise SourceNotReady("The selected API Source revision is not ready.")
        profile = self.profiles.get_exact(
            owner_key=owner_key,
            source_id=source_id,
            revision_id=source_revision_id,
            profile_id=connection_profile_id,
        )
        if (
            profile.source_id != source_id
            or profile.revision_id != source_revision_id
        ):
            raise ApiConnectionCheckConflict(
                "The selected API connection profile belongs to another Source revision."
            )
        operation = SAFE_API_OPERATIONS.get(operation_id)
        if operation is None:
            raise ApiConnectionCheckConflict(
                "The selected API operation is not approved for a safe connection check."
            )
        with self.sources.locked_revision(
            owner_key=owner_key,
            source_id=source_id,
            revision_id=source_revision_id,
        ) as (locked_source, revision_dir):
            if locked_source.revision != source.revision:
                raise ApiConnectionCheckConflict(
                    "The selected API Source revision changed before the check began."
                )
            try:
                document, document_hash = load_reviewed_document(
                    locked_source, revision_dir, owner_key=owner_key
                )
            except ReviewedApiRevisionMismatch as error:
                raise ApiConnectionCheckConflict(str(error)) from error
        method, path_template = operation
        return PreparedApiConnectionCheck(
            owner_id=owner_id,
            source_id=source_id,
            source_revision_id=source_revision_id,
            profile=profile,
            operation_id=operation_id,
            method=method,
            path_template=path_template,
            document=document,
            document_hash=document_hash,
        )

    async def execute(
        self,
        *,
        owner_id: uuid.UUID,
        source_id: str,
        source_revision_id: str,
        connection_profile_id: str,
        operation_id: str,
    ) -> ApiConnectionCheckRecord:
        prepared = self.require_executable(
            owner_id=owner_id,
            source_id=source_id,
            source_revision_id=source_revision_id,
            connection_profile_id=connection_profile_id,
            operation_id=operation_id,
        )
        check_id = secrets.token_urlsafe(12)
        execution_id = secrets.token_urlsafe(12)
        profile = prepared.profile
        if profile.authentication_method is not ApiAuthenticationMethod.NONE:
            if (
                profile.credential_reference_id is None
                or profile.credential_version is None
            ):
                redacted = _failed_before_http(
                    "credential_reference_missing",
                    "The selected API credential is unavailable.",
                )
                return self._persist(prepared, check_id, execution_id, redacted)
            try:
                metadata = await self.credentials.metadata(
                    owner_id=owner_id,
                    credential_id=profile.credential_reference_id,
                )
            except Exception:
                redacted = _failed_before_http(
                    "credential_unavailable",
                    "The selected API credential is unavailable.",
                )
                return self._persist(prepared, check_id, execution_id, redacted)
            if (
                metadata.id != profile.credential_reference_id
                or metadata.owner_id != owner_id
                or metadata.version != profile.credential_version
            ):
                redacted = _failed_before_http(
                    "credential_version_mismatch",
                    "The selected API credential changed before the check began.",
                )
                return self._persist(prepared, check_id, execution_id, redacted)
        elif (
            profile.credential_reference_id is not None
            or profile.credential_version is not None
        ):
            redacted = _failed_before_http(
                "credential_reference_unexpected",
                "The selected unauthenticated profile is invalid.",
            )
            return self._persist(prepared, check_id, execution_id, redacted)
        try:
            redacted = await self.execution.execute_redacted(
                SafeApiExecutionTarget(
                    execution_id=execution_id,
                    owner_id=owner_id,
                    source_id=source_id,
                    source_revision_id=source_revision_id,
                    connection_profile_id=connection_profile_id,
                    base_url=profile.base_url,
                    authentication_method=profile.authentication_method.value,
                    credential_name=profile.credential_name,
                    credential_reference_id=profile.credential_reference_id,
                    credential_version=profile.credential_version,
                    document_hash=prepared.document_hash,
                    document=prepared.document,
                    operation_id=operation_id,
                )
            )
        except (SafeApiExecutionError, ValueError):
            redacted = _failed_before_http(
                "safe_api_check_unavailable",
                "The safe API connection check is unavailable.",
            )
        return self._persist(prepared, check_id, execution_id, redacted)

    def list(
        self, *, owner_id: uuid.UUID, source_id: str, source_revision_id: str
    ) -> tuple[ApiConnectionCheckRecord, ...]:
        self.require_revision(
            owner_id=owner_id,
            source_id=source_id,
            source_revision_id=source_revision_id,
        )
        return self.records.list(
            owner_key=str(owner_id),
            source_id=source_id,
            revision_id=source_revision_id,
        )

    def require_revision(
        self, *, owner_id: uuid.UUID, source_id: str, source_revision_id: str
    ) -> None:
        source = self.sources.get_revision(
            owner_key=str(owner_id),
            source_id=source_id,
            revision_id=source_revision_id,
        )
        if source.connector_key != "api":
            raise SourceNotReady("The selected source is not an API source.")

    def _persist(
        self,
        prepared: PreparedApiConnectionCheck,
        check_id: str,
        execution_id: str,
        redacted: RedactedApiExecution,
    ) -> ApiConnectionCheckRecord:
        profile = prepared.profile
        return self.records.append(
            owner_key=str(prepared.owner_id),
            record=ApiConnectionCheckRecord(
                id=check_id,
                execution_id=execution_id,
                source_id=prepared.source_id,
                source_revision_id=prepared.source_revision_id,
                connection_profile_id=profile.id,
                credential_reference_id=profile.credential_reference_id,
                credential_version=profile.credential_version,
                operation_id=prepared.operation_id,
                method=prepared.method,
                path_template=prepared.path_template,
                effective_contract_sha256=prepared.document_hash,
                status=redacted.status,
                status_code=redacted.status_code,
                error_code=redacted.error_code,
                public_message=redacted.public_message,
                validation_issue_count=redacted.validation_issue_count,
                validation_phases=redacted.validation_phases,
                http_call_count=redacted.http_call_count,
                started_at=redacted.started_at,
                finished_at=redacted.finished_at,
                traces=redacted.traces,
            ),
        )


def _failed_before_http(code: str, message: str) -> RedactedApiExecution:
    now = datetime.now(UTC).isoformat()
    return RedactedApiExecution(
        status="failed",
        error_code=code,
        public_message=message,
        validation_issue_count=0,
        validation_phases=(),
        http_call_count=0,
        started_at=now,
        finished_at=now,
        traces=(),
    )


__all__ = [
    "ApiConnectionCheckConflict",
    "ApiConnectionCheckError",
    "ApiConnectionCheckRecord",
    "ApiConnectionCheckRepository",
    "ApiConnectionCheckService",
    "PreparedApiConnectionCheck",
]
