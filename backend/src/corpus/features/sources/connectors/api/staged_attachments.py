from __future__ import annotations

import hashlib
import json
import os
import secrets
import threading
from collections.abc import Callable
from datetime import datetime
from pathlib import Path

from pydantic import BaseModel, ConfigDict, Field

from ...models import SourceState, SourceView, utc_now
from ...repository import LocalSourceRepository
from ..base import SourceUpload, ValidatedSourceUpload
from .connector import ApiSourceConnector


class ApiStagedAttachmentError(RuntimeError):
    pass


class ApiStagedAttachmentUnavailable(ApiStagedAttachmentError):
    pass


class ApiStagedAttachmentView(BaseModel):
    model_config = ConfigDict(frozen=True)

    attachment_id: str = Field(min_length=16, max_length=16)
    display_name: str = Field(min_length=1, max_length=128)
    filename: str = Field(min_length=1)
    content_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    staged_at: datetime
    state: str = Field(pattern=r"^(staged|accepted)$")
    source_id: str | None = Field(default=None, min_length=16, max_length=16)
    source_revision_id: str | None = Field(default=None, min_length=16, max_length=16)


class _ApiStagedAttachmentRecord(BaseModel):
    model_config = ConfigDict(frozen=True)

    attachment_id: str = Field(min_length=16, max_length=16)
    owner_key: str = Field(min_length=1)
    conversation_id: str = Field(min_length=16, max_length=64)
    route_session_id: str = Field(min_length=1, max_length=256)
    display_name: str = Field(min_length=1, max_length=128)
    filename: str = Field(min_length=1)
    content_type: str
    content_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    description_filename: str | None = None
    description_content_type: str | None = None
    description_sha256: str | None = Field(default=None, pattern=r"^[0-9a-f]{64}$")
    staged_at: datetime
    accepted_source_id: str | None = Field(default=None, min_length=16, max_length=16)
    accepted_source_revision_id: str | None = Field(default=None, min_length=16, max_length=16)


class ApiStagedAttachmentRepository:
    """Durable, conversation-bound binary intake before any Source mutation."""

    def __init__(self, root: Path) -> None:
        self.root = (root.resolve() / "_staged-api-attachments")
        self._lock = threading.RLock()

    def stage(
        self,
        *,
        owner_key: str,
        conversation_id: str,
        route_session_id: str,
        display_name: str,
        upload: ValidatedSourceUpload,
    ) -> ApiStagedAttachmentView:
        attachment_id = secrets.token_urlsafe(12)
        staged_at = utc_now()
        record = _ApiStagedAttachmentRecord(
            attachment_id=attachment_id,
            owner_key=owner_key,
            conversation_id=conversation_id,
            route_session_id=route_session_id,
            display_name=display_name.strip(),
            filename=upload.filename,
            content_type=upload.content_type,
            content_sha256=hashlib.sha256(upload.content).hexdigest(),
            description_filename=upload.description_filename,
            description_content_type=upload.description_content_type,
            description_sha256=(
                hashlib.sha256(upload.description_content).hexdigest()
                if upload.description_content is not None
                else None
            ),
            staged_at=staged_at,
        )
        location = self._session_dir(owner_key, route_session_id)
        attachment_dir = location / "records" / attachment_id
        with self._lock:
            if attachment_dir.exists():
                raise ApiStagedAttachmentError("The staged attachment identity already exists.")
            attachment_dir.mkdir(parents=True, exist_ok=False)
            _write_bytes_atomic(attachment_dir / "definition", upload.content)
            if upload.description_content is not None:
                _write_bytes_atomic(attachment_dir / "description", upload.description_content)
            _write_json_atomic(attachment_dir / "record.json", record.model_dump(mode="json"))
            _write_json_atomic(location / "current.json", {"attachment_id": attachment_id})
        return _view(record)

    def current(
        self,
        *,
        owner_key: str,
        conversation_id: str,
        route_session_id: str,
    ) -> ApiStagedAttachmentView | None:
        with self._lock:
            record = self._read_current(owner_key, route_session_id, conversation_id)
            return None if record is None else _view(record)

    def accept_current(
        self,
        *,
        owner_key: str,
        conversation_id: str | None,
        route_session_id: str,
        accept: Callable[[str, SourceUpload], SourceView],
    ) -> SourceView:
        with self._lock:
            record = self._read_current(owner_key, route_session_id, conversation_id)
            if record is None:
                raise ApiStagedAttachmentUnavailable(
                    "Attach an API definition to this conversation before adding it."
                )
            if record.accepted_source_id is not None:
                raise ApiStagedAttachmentUnavailable(
                    "The current attached API definition has already been added."
                )
            attachment_dir = self._record_dir(owner_key, route_session_id, record.attachment_id)
            definition = _read_verified(
                attachment_dir / "definition", record.content_sha256, "API definition"
            )
            description = None
            if record.description_sha256 is not None:
                description = _read_verified(
                    attachment_dir / "description",
                    record.description_sha256,
                    "API description",
                )
            source = accept(
                record.display_name,
                SourceUpload(
                    filename=record.filename,
                    content_type=record.content_type,
                    content=definition,
                    description_filename=record.description_filename,
                    description_content_type=record.description_content_type,
                    description_content=description,
                ),
            )
            accepted = record.model_copy(
                update={
                    "accepted_source_id": source.source_id,
                    "accepted_source_revision_id": source.revision.revision_id,
                }
            )
            _write_json_atomic(
                attachment_dir / "record.json", accepted.model_dump(mode="json")
            )
            return source

    def accepted_source(
        self,
        *,
        owner_key: str,
        conversation_id: str | None,
        route_session_id: str,
    ) -> tuple[str, str]:
        with self._lock:
            record = self._read_current(owner_key, route_session_id, conversation_id)
            if (
                record is None
                or record.accepted_source_id is None
                or record.accepted_source_revision_id is None
            ):
                raise ApiStagedAttachmentUnavailable(
                    "Add the attached API definition before analyzing it."
                )
            return record.accepted_source_id, record.accepted_source_revision_id

    def _read_current(
        self, owner_key: str, route_session_id: str, conversation_id: str | None = None
    ) -> _ApiStagedAttachmentRecord | None:
        location = self._session_dir(owner_key, route_session_id)
        pointer = location / "current.json"
        if not pointer.is_file():
            return None
        try:
            attachment_id = str(json.loads(pointer.read_text(encoding="utf-8"))["attachment_id"])
            record = _ApiStagedAttachmentRecord.model_validate_json(
                (self._record_dir(owner_key, route_session_id, attachment_id) / "record.json").read_text(
                    encoding="utf-8"
                )
            )
        except (OSError, KeyError, TypeError, ValueError) as error:
            raise ApiStagedAttachmentError("The staged API attachment record is invalid.") from error
        if (
            record.owner_key != owner_key
            or (conversation_id is not None and record.conversation_id != conversation_id)
            or record.route_session_id != route_session_id
            or record.attachment_id != attachment_id
        ):
            raise ApiStagedAttachmentError("The staged API attachment binding is invalid.")
        return record

    def _session_dir(self, owner_key: str, route_session_id: str) -> Path:
        return self.root / _digest(owner_key) / _digest(route_session_id)

    def _record_dir(self, owner_key: str, route_session_id: str, attachment_id: str) -> Path:
        return self._session_dir(owner_key, route_session_id) / "records" / attachment_id


class ApiStagedAttachmentService:
    def __init__(
        self,
        *,
        repository: ApiStagedAttachmentRepository,
        sources: LocalSourceRepository,
        connector: ApiSourceConnector,
    ) -> None:
        self.repository = repository
        self.sources = sources
        self.connector = connector

    def stage(
        self,
        *,
        owner_key: str,
        conversation_id: str,
        route_session_id: str,
        display_name: str,
        upload: SourceUpload,
    ) -> ApiStagedAttachmentView:
        validated = self.connector.validate_upload(upload)
        return self.repository.stage(
            owner_key=owner_key,
            conversation_id=conversation_id,
            route_session_id=route_session_id,
            display_name=display_name,
            upload=validated,
        )

    def current(
        self, *, owner_key: str, conversation_id: str, route_session_id: str
    ) -> ApiStagedAttachmentView | None:
        return self.repository.current(
            owner_key=owner_key,
            conversation_id=conversation_id,
            route_session_id=route_session_id,
        )

    def accept_current(
        self,
        *,
        owner_key: str,
        route_session_id: str,
        conversation_id: str | None = None,
    ) -> SourceView:
        def accept(display_name: str, upload: SourceUpload) -> SourceView:
            validated = self.connector.validate_upload(upload)
            prepared = self.sources.begin_source(
                owner_key=owner_key,
                connector_key=self.connector.key,
                display_name=display_name,
                original_filename=validated.filename,
                content=validated.content,
                description_filename=validated.description_filename,
                description_content=validated.description_content,
                initial_state=SourceState.ACCEPTED,
            )
            return SourceView(
                source_id=prepared.source.source_id,
                connector_key=prepared.source.connector_key,
                display_name=prepared.source.display_name,
                created_at=prepared.source.created_at,
                updated_at=prepared.source.updated_at,
                revision=prepared.revision,
            )

        return self.repository.accept_current(
            owner_key=owner_key,
            conversation_id=conversation_id,
            route_session_id=route_session_id,
            accept=accept,
        )

    def accepted_source(
        self,
        *,
        owner_key: str,
        route_session_id: str,
        conversation_id: str | None = None,
    ) -> tuple[str, str]:
        return self.repository.accepted_source(
            owner_key=owner_key,
            conversation_id=conversation_id,
            route_session_id=route_session_id,
        )


def _view(record: _ApiStagedAttachmentRecord) -> ApiStagedAttachmentView:
    return ApiStagedAttachmentView(
        attachment_id=record.attachment_id,
        display_name=record.display_name,
        filename=record.filename,
        content_sha256=record.content_sha256,
        staged_at=record.staged_at,
        state="accepted" if record.accepted_source_id is not None else "staged",
        source_id=record.accepted_source_id,
        source_revision_id=record.accepted_source_revision_id,
    )


def _digest(value: str) -> str:
    # 96 bits keeps Windows paths bounded while the record still verifies the
    # complete owner and RouteDeck-session identities after lookup.
    return hashlib.sha256(value.encode("utf-8")).hexdigest()[:24]


def _read_verified(path: Path, expected_sha256: str, label: str) -> bytes:
    try:
        content = path.read_bytes()
    except OSError as error:
        raise ApiStagedAttachmentError(f"The staged {label} is unavailable.") from error
    if hashlib.sha256(content).hexdigest() != expected_sha256:
        raise ApiStagedAttachmentError(f"The staged {label} failed integrity validation.")
    return content


def _write_bytes_atomic(path: Path, content: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.{secrets.token_hex(8)}.tmp")
    try:
        temporary.write_bytes(content)
        os.replace(temporary, path)
    finally:
        temporary.unlink(missing_ok=True)


def _write_json_atomic(path: Path, value: object) -> None:
    _write_bytes_atomic(
        path,
        json.dumps(value, ensure_ascii=False, separators=(",", ":")).encode("utf-8"),
    )


__all__ = [
    "ApiStagedAttachmentError",
    "ApiStagedAttachmentRepository",
    "ApiStagedAttachmentService",
    "ApiStagedAttachmentUnavailable",
    "ApiStagedAttachmentView",
]
