from __future__ import annotations

import hashlib
import re
import secrets
from pathlib import Path

from pydantic import ValidationError

from .models import (
    PreparedSource,
    SourceRecord,
    SourceRevisionRecord,
    SourceState,
    SourceView,
    utc_now,
)


class SourceRepositoryError(RuntimeError):
    pass


class SourceNotFound(SourceRepositoryError):
    pass


class SourceNotReady(SourceRepositoryError):
    pass


class LocalSourceRepository:
    def __init__(self, root: Path) -> None:
        self.root = root.resolve()

    def begin_source(
        self,
        *,
        owner_key: str,
        connector_key: str,
        display_name: str,
        original_filename: str,
        content: bytes,
    ) -> PreparedSource:
        if not owner_key.strip() or not connector_key.strip() or not display_name.strip():
            raise ValueError("Owner, connector, and source display name are required.")
        if Path(original_filename).name != original_filename or any(
            separator in original_filename for separator in ("/", "\\")
        ):
            raise ValueError("Source input must use a plain filename.")
        # 96 bits keeps owner-facing IDs opaque and collision-resistant while
        # leaving room for nested connector artifacts on Windows.
        source_id = secrets.token_urlsafe(12)
        revision_id = secrets.token_urlsafe(12)
        now = utc_now()
        source = SourceRecord(
            source_id=source_id,
            owner_key=owner_key,
            connector_key=connector_key,
            display_name=display_name.strip(),
            current_revision_id=revision_id,
            created_at=now,
            updated_at=now,
        )
        revision = SourceRevisionRecord(
            revision_id=revision_id,
            source_id=source_id,
            original_filename=original_filename,
            content_sha256=hashlib.sha256(content).hexdigest(),
            state=SourceState.PROCESSING,
            created_at=now,
            updated_at=now,
        )
        source_dir = self._source_dir(owner_key, source_id)
        revision_dir = source_dir / "r" / revision_id
        input_path = revision_dir / "i" / original_filename
        artifact_dir = revision_dir / "a"
        if source_dir.exists():
            raise SourceRepositoryError(
                f"The generated source ID already exists: {source_id}"
            )
        input_path.parent.mkdir(parents=True, exist_ok=False)
        artifact_dir.mkdir(parents=True, exist_ok=False)
        _write_bytes_atomic(input_path, content)
        _write_model_atomic(source_dir / "source.json", source)
        _write_model_atomic(revision_dir / "revision.json", revision)
        return PreparedSource(
            source=source,
            revision=revision,
            input_path=input_path,
            artifact_dir=artifact_dir,
        )

    def list(self, *, owner_key: str) -> tuple[SourceView, ...]:
        owner_dir = self._owner_dir(owner_key)
        if not owner_dir.is_dir():
            return ()
        values: list[SourceView] = []
        for manifest in owner_dir.glob("*/source.json"):
            source = self._read_source(manifest)
            if source.owner_key != owner_key:
                raise SourceRepositoryError(
                    f"Source owner metadata disagrees at {manifest}"
                )
            values.append(self._view(source))
        return tuple(
            sorted(values, key=lambda value: (value.created_at, value.source_id))
        )

    def get(self, *, owner_key: str, source_id: str) -> SourceView:
        manifest = self._source_dir(owner_key, source_id) / "source.json"
        if not manifest.is_file():
            raise SourceNotFound("The requested source does not exist.")
        source = self._read_source(manifest)
        if source.owner_key != owner_key:
            raise SourceNotFound("The requested source does not exist.")
        return self._view(source)

    def artifact_dir(self, *, owner_key: str, source_id: str) -> Path:
        view = self.get(owner_key=owner_key, source_id=source_id)
        return (
            self._source_dir(owner_key, source_id)
            / "r"
            / view.revision.revision_id
            / "a"
        )

    def mark_ready(
        self,
        *,
        owner_key: str,
        source_id: str,
        revision_id: str,
        summary: dict[str, object],
    ) -> SourceView:
        return self._transition(
            owner_key=owner_key,
            source_id=source_id,
            revision_id=revision_id,
            state=SourceState.READY,
            summary=summary,
            failure_code=None,
            failure_message=None,
        )

    def mark_failed(
        self,
        *,
        owner_key: str,
        source_id: str,
        revision_id: str,
        failure_code: str,
        failure_message: str,
    ) -> SourceView:
        if not failure_code.strip() or not failure_message.strip():
            raise ValueError("Failed source revisions require a code and message.")
        return self._transition(
            owner_key=owner_key,
            source_id=source_id,
            revision_id=revision_id,
            state=SourceState.FAILED,
            summary={},
            failure_code=failure_code,
            failure_message=failure_message,
        )

    def _transition(
        self,
        *,
        owner_key: str,
        source_id: str,
        revision_id: str,
        state: SourceState,
        summary: dict[str, object],
        failure_code: str | None,
        failure_message: str | None,
    ) -> SourceView:
        source_view = self.get(owner_key=owner_key, source_id=source_id)
        if source_view.revision.revision_id != revision_id:
            raise SourceNotFound("The requested source revision does not exist.")
        if source_view.revision.state is not SourceState.PROCESSING:
            raise SourceRepositoryError(
                "Only a processing source revision may transition."
            )
        now = utc_now()
        updated_revision = source_view.revision.model_copy(
            update={
                "state": state,
                "updated_at": now,
                "summary": dict(summary),
                "failure_code": failure_code,
                "failure_message": failure_message,
            }
        )
        source_manifest = self._source_dir(owner_key, source_id) / "source.json"
        source = self._read_source(source_manifest).model_copy(
            update={"updated_at": now}
        )
        revision_manifest = (
            source_manifest.parent
            / "r"
            / revision_id
            / "revision.json"
        )
        _write_model_atomic(revision_manifest, updated_revision)
        _write_model_atomic(source_manifest, source)
        return SourceView(
            source_id=source.source_id,
            connector_key=source.connector_key,
            display_name=source.display_name,
            created_at=source.created_at,
            updated_at=source.updated_at,
            revision=updated_revision,
        )

    def _view(self, source: SourceRecord) -> SourceView:
        revision_path = (
            self._source_dir(source.owner_key, source.source_id)
            / "r"
            / source.current_revision_id
            / "revision.json"
        )
        if not revision_path.is_file():
            raise SourceRepositoryError(
                f"The current source revision is missing: {revision_path}"
            )
        try:
            revision = SourceRevisionRecord.model_validate_json(
                revision_path.read_text(encoding="utf-8")
            )
        except (OSError, ValidationError) as error:
            raise SourceRepositoryError(
                f"The source revision metadata is invalid: {error}"
            ) from error
        return SourceView(
            source_id=source.source_id,
            connector_key=source.connector_key,
            display_name=source.display_name,
            created_at=source.created_at,
            updated_at=source.updated_at,
            revision=revision,
        )

    def _read_source(self, path: Path) -> SourceRecord:
        try:
            return SourceRecord.model_validate_json(path.read_text(encoding="utf-8"))
        except (OSError, ValidationError) as error:
            raise SourceRepositoryError(
                f"The source metadata is invalid: {error}"
            ) from error

    def _owner_dir(self, owner_key: str) -> Path:
        if not owner_key.strip():
            raise ValueError("Owner key cannot be empty.")
        opaque = hashlib.sha256(owner_key.encode("utf-8")).hexdigest()[:16]
        return self.root / opaque

    def _source_dir(self, owner_key: str, source_id: str) -> Path:
        if not re.fullmatch(r"[A-Za-z0-9_-]{16}", source_id):
            raise SourceNotFound("The requested source does not exist.")
        return self._owner_dir(owner_key) / source_id


def _write_model_atomic(path: Path, model) -> None:
    _write_text_atomic(path, model.model_dump_json(indent=2))


def _write_text_atomic(path: Path, value: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(value, encoding="utf-8")
    temporary.replace(path)


def _write_bytes_atomic(path: Path, value: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_bytes(value)
    temporary.replace(path)


__all__ = [
    "LocalSourceRepository",
    "SourceNotFound",
    "SourceNotReady",
    "SourceRepositoryError",
]
