from __future__ import annotations

import hashlib
import json
import os
import secrets
import threading
from datetime import datetime
from pathlib import Path

from pydantic import BaseModel, ConfigDict, Field

from ...models import SourceDescriptionView, utc_now
from ...repository import LocalSourceRepository


class ApiStagedDescriptionError(RuntimeError):
    pass


class ApiStagedDescriptionUnavailable(ApiStagedDescriptionError):
    pass


class ApiStagedDescriptionView(BaseModel):
    model_config = ConfigDict(frozen=True)

    attachment_id: str = Field(min_length=16, max_length=16)
    filename: str = Field(min_length=1, max_length=255)
    content_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    staged_at: datetime
    state: str = Field(pattern=r"^(staged|saved)$")
    source_id: str | None = Field(default=None, min_length=16, max_length=16)
    description_id: str | None = None


class _ApiStagedDescriptionRecord(BaseModel):
    model_config = ConfigDict(frozen=True)

    attachment_id: str = Field(min_length=16, max_length=16)
    owner_key: str = Field(min_length=1)
    conversation_id: str = Field(min_length=16, max_length=64)
    route_session_id: str = Field(min_length=1, max_length=256)
    filename: str = Field(min_length=1, max_length=255)
    content_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    staged_at: datetime
    saved_source_id: str | None = Field(default=None, min_length=16, max_length=16)
    saved_description_id: str | None = None


class ApiStagedDescriptionRepository:
    """Conversation-bound Markdown bytes awaiting a supervised Source save."""

    def __init__(self, root: Path) -> None:
        self.root = root.resolve() / "_staged-api-descriptions"
        self._lock = threading.RLock()

    def stage(
        self,
        *,
        owner_key: str,
        conversation_id: str,
        route_session_id: str,
        filename: str,
        content: bytes,
    ) -> ApiStagedDescriptionView:
        _validate_markdown(filename, content)
        attachment_id = secrets.token_urlsafe(12)
        record = _ApiStagedDescriptionRecord(
            attachment_id=attachment_id,
            owner_key=owner_key,
            conversation_id=conversation_id,
            route_session_id=route_session_id,
            filename=filename,
            content_sha256=hashlib.sha256(content).hexdigest(),
            staged_at=utc_now(),
        )
        location = self._session_dir(owner_key, route_session_id)
        record_dir = location / "records" / attachment_id
        with self._lock:
            record_dir.mkdir(parents=True, exist_ok=False)
            _write_bytes_atomic(record_dir / "content.md", content)
            _write_json_atomic(record_dir / "record.json", record.model_dump(mode="json"))
            _write_json_atomic(location / "current.json", {"attachment_id": attachment_id})
        return _view(record)

    def current(
        self,
        *,
        owner_key: str,
        conversation_id: str | None,
        route_session_id: str,
    ) -> ApiStagedDescriptionView | None:
        with self._lock:
            record = self._read_current(owner_key, route_session_id, conversation_id)
            return None if record is None else _view(record)

    def save_current(
        self,
        *,
        owner_key: str,
        conversation_id: str | None,
        route_session_id: str,
        source_id: str,
        source_revision_id: str,
        sources: LocalSourceRepository,
    ) -> SourceDescriptionView:
        with self._lock:
            record = self._read_current(owner_key, route_session_id, conversation_id)
            if record is None:
                raise ApiStagedDescriptionUnavailable(
                    "Attach a Markdown API description to this conversation before saving it."
                )
            if record.saved_description_id is not None:
                raise ApiStagedDescriptionUnavailable(
                    "The current attached API description has already been saved."
                )
            record_dir = self._record_dir(owner_key, route_session_id, record.attachment_id)
            try:
                content = (record_dir / "content.md").read_bytes()
            except OSError as error:
                raise ApiStagedDescriptionError(
                    "The staged API description content is unavailable."
                ) from error
            if hashlib.sha256(content).hexdigest() != record.content_sha256:
                raise ApiStagedDescriptionError(
                    "The staged API description failed integrity validation."
                )
            saved = sources.save_description(
                owner_key=owner_key,
                source_id=source_id,
                expected_revision_id=source_revision_id,
                filename=record.filename,
                content=content,
            )
            next_record = record.model_copy(
                update={
                    "saved_source_id": source_id,
                    "saved_description_id": saved.description_id,
                }
            )
            _write_json_atomic(
                record_dir / "record.json", next_record.model_dump(mode="json")
            )
            return saved

    def _read_current(
        self,
        owner_key: str,
        route_session_id: str,
        conversation_id: str | None,
    ) -> _ApiStagedDescriptionRecord | None:
        location = self._session_dir(owner_key, route_session_id)
        pointer = location / "current.json"
        if not pointer.is_file():
            return None
        try:
            attachment_id = str(json.loads(pointer.read_text(encoding="utf-8"))["attachment_id"])
            record = _ApiStagedDescriptionRecord.model_validate_json(
                (self._record_dir(owner_key, route_session_id, attachment_id) / "record.json").read_text(
                    encoding="utf-8"
                )
            )
        except (OSError, KeyError, TypeError, ValueError) as error:
            raise ApiStagedDescriptionError(
                "The staged API description record is invalid."
            ) from error
        if (
            record.owner_key != owner_key
            or record.route_session_id != route_session_id
            or record.attachment_id != attachment_id
            or (conversation_id is not None and record.conversation_id != conversation_id)
        ):
            raise ApiStagedDescriptionError(
                "The staged API description binding is invalid."
            )
        return record

    def _session_dir(self, owner_key: str, route_session_id: str) -> Path:
        return self.root / _digest(owner_key) / _digest(route_session_id)

    def _record_dir(self, owner_key: str, route_session_id: str, attachment_id: str) -> Path:
        return self._session_dir(owner_key, route_session_id) / "records" / attachment_id


class ApiStagedDescriptionService:
    def __init__(
        self,
        *,
        repository: ApiStagedDescriptionRepository,
        sources: LocalSourceRepository,
    ) -> None:
        self.repository = repository
        self.sources = sources

    def stage(self, **kwargs) -> ApiStagedDescriptionView:
        return self.repository.stage(**kwargs)

    def current(self, **kwargs) -> ApiStagedDescriptionView | None:
        return self.repository.current(**kwargs)

    def save_current(
        self,
        *,
        owner_key: str,
        conversation_id: str | None,
        route_session_id: str,
        source_id: str,
        source_revision_id: str,
    ) -> SourceDescriptionView:
        return self.repository.save_current(
            owner_key=owner_key,
            conversation_id=conversation_id,
            route_session_id=route_session_id,
            source_id=source_id,
            source_revision_id=source_revision_id,
            sources=self.sources,
        )


def _validate_markdown(filename: str, content: bytes) -> None:
    if (
        not filename
        or Path(filename).name != filename
        or any(separator in filename for separator in ("/", "\\"))
        or Path(filename).suffix.casefold() not in {".md", ".markdown"}
    ):
        raise ValueError("The API description must use a plain Markdown filename.")
    if not content:
        raise ValueError("The API description is empty.")
    if len(content) > 1024 * 1024:
        raise ValueError("The API description exceeds the 1 MiB upload limit.")
    try:
        content.decode("utf-8")
    except UnicodeDecodeError as error:
        raise ValueError("The API description must be valid UTF-8 Markdown.") from error


def _view(record: _ApiStagedDescriptionRecord) -> ApiStagedDescriptionView:
    return ApiStagedDescriptionView(
        attachment_id=record.attachment_id,
        filename=record.filename,
        content_sha256=record.content_sha256,
        staged_at=record.staged_at,
        state="saved" if record.saved_description_id is not None else "staged",
        source_id=record.saved_source_id,
        description_id=record.saved_description_id,
    )


def _digest(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()[:24]


def _write_bytes_atomic(path: Path, content: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.{secrets.token_hex(8)}.tmp")
    try:
        temporary.write_bytes(content)
        os.replace(temporary, path)
    finally:
        temporary.unlink(missing_ok=True)


def _write_json_atomic(path: Path, value: object) -> None:
    content = json.dumps(value, sort_keys=True, separators=(",", ":")).encode("utf-8")
    _write_bytes_atomic(path, content)


__all__ = [
    "ApiStagedDescriptionError",
    "ApiStagedDescriptionRepository",
    "ApiStagedDescriptionService",
    "ApiStagedDescriptionUnavailable",
    "ApiStagedDescriptionView",
]
