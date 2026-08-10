from __future__ import annotations

import hashlib
import json
import secrets
import uuid
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, ValidationError

from ...models import SourceState, SourceView
from ...repository import LocalSourceRepository, SourceNotReady


class ApiOperationCurationError(RuntimeError):
    pass


class ApiOperationCurationConflict(ApiOperationCurationError):
    pass


class ApiOperationInventoryItem(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    operation_id: str = Field(min_length=1, max_length=256)
    graph_node_id: str = Field(min_length=1, max_length=512)
    method: str = Field(min_length=1, max_length=16)
    path_template: str = Field(min_length=1, max_length=2_048)
    operation_class: str = Field(min_length=1, max_length=64)


class ApiOperationCurationRecord(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    schema_version: int = 1
    id: str = Field(min_length=16, max_length=16)
    source_id: str = Field(min_length=16, max_length=16)
    source_revision_id: str = Field(min_length=16, max_length=16)
    artifact_revision_id: str = Field(min_length=16, max_length=16)
    inventory_fingerprint: str = Field(pattern=r"^[0-9a-f]{64}$")
    included_operation_ids: tuple[str, ...]
    excluded_operation_ids: tuple[str, ...]
    selected_by_owner_id: uuid.UUID
    selected_at: datetime
    previous_curation_id: str | None = Field(default=None, min_length=16, max_length=16)


class ApiOperationCurationView(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    source_id: str = Field(min_length=16, max_length=16)
    source_revision_id: str = Field(min_length=16, max_length=16)
    artifact_revision_id: str = Field(min_length=16, max_length=16)
    inventory_fingerprint: str = Field(pattern=r"^[0-9a-f]{64}$")
    operations: tuple[ApiOperationInventoryItem, ...]
    current: ApiOperationCurationRecord | None
    history: tuple[ApiOperationCurationRecord, ...]


class _ApiOperationCurationIndex(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    schema_version: int = 1
    current_curation_id: str | None = Field(default=None, min_length=16, max_length=16)
    record_ids: tuple[str, ...] = ()


@dataclass(frozen=True)
class ApiOperationCurationService:
    sources: LocalSourceRepository

    def inspect(
        self,
        *,
        owner_id: uuid.UUID,
        source_id: str,
        source_revision_id: str,
    ) -> ApiOperationCurationView:
        with self.sources.locked_revision(
            owner_key=str(owner_id),
            source_id=source_id,
            revision_id=source_revision_id,
        ) as (source, revision_dir):
            return self.inspect_locked(
                owner_id=owner_id,
                source=source,
                revision_dir=revision_dir,
            )

    def inspect_locked(
        self,
        *,
        owner_id: uuid.UUID,
        source: SourceView,
        revision_dir: Path,
    ) -> ApiOperationCurationView:
        """Inspect exact curation while the caller holds the Source revision lock."""

        inventory = _inventory(source, revision_dir)
        fingerprint = _inventory_fingerprint(source, inventory)
        index, history = _load_history(
            revision_dir,
            owner_id=owner_id,
            source=source,
            inventory=inventory,
            inventory_fingerprint=fingerprint,
        )
        current = _current_record(index, history)
        return ApiOperationCurationView(
            source_id=source.source_id,
            source_revision_id=source.revision.revision_id,
            artifact_revision_id=_artifact_revision_id(source),
            inventory_fingerprint=fingerprint,
            operations=inventory,
            current=current,
            history=history,
        )

    def require_current_selection(
        self,
        *,
        owner_id: uuid.UUID,
        source_id: str,
        source_revision_id: str,
        inventory_fingerprint: str,
        included_operation_ids: tuple[str, ...],
        excluded_operation_ids: tuple[str, ...],
        expected_current_curation_id: str | None,
    ) -> ApiOperationCurationView:
        with self.sources.locked_revision(
            owner_key=str(owner_id),
            source_id=source_id,
            revision_id=source_revision_id,
            require_current=True,
        ) as (source, revision_dir):
            return _validate_selection(
                owner_id=owner_id,
                source=source,
                revision_dir=revision_dir,
                inventory_fingerprint=inventory_fingerprint,
                included_operation_ids=included_operation_ids,
                excluded_operation_ids=excluded_operation_ids,
                expected_current_curation_id=expected_current_curation_id,
            )

    def save(
        self,
        *,
        owner_id: uuid.UUID,
        source_id: str,
        source_revision_id: str,
        inventory_fingerprint: str,
        included_operation_ids: tuple[str, ...],
        excluded_operation_ids: tuple[str, ...],
        expected_current_curation_id: str | None,
    ) -> ApiOperationCurationRecord:
        with self.sources.locked_revision(
            owner_key=str(owner_id),
            source_id=source_id,
            revision_id=source_revision_id,
            require_current=True,
        ) as (source, revision_dir):
            view = _validate_selection(
                owner_id=owner_id,
                source=source,
                revision_dir=revision_dir,
                inventory_fingerprint=inventory_fingerprint,
                included_operation_ids=included_operation_ids,
                excluded_operation_ids=excluded_operation_ids,
                expected_current_curation_id=expected_current_curation_id,
            )
            if not view.operations:
                raise ApiOperationCurationConflict(
                    "No discovered API operations are available to curate."
                )
            order = {item.operation_id: index for index, item in enumerate(view.operations)}
            included = tuple(sorted(included_operation_ids, key=order.__getitem__))
            excluded = tuple(sorted(excluded_operation_ids, key=order.__getitem__))
            record = ApiOperationCurationRecord(
                id=secrets.token_urlsafe(12),
                source_id=source_id,
                source_revision_id=source_revision_id,
                artifact_revision_id=view.artifact_revision_id,
                inventory_fingerprint=view.inventory_fingerprint,
                included_operation_ids=included,
                excluded_operation_ids=excluded,
                selected_by_owner_id=owner_id,
                selected_at=datetime.now(UTC),
                previous_curation_id=(view.current.id if view.current is not None else None),
            )
            root = _curation_root(revision_dir)
            record_path = root / "records" / f"{record.id}.json"
            if record_path.exists():
                raise ApiOperationCurationConflict(
                    "The operation curation identity already exists."
                )
            _write_model_atomic(record_path, record)
            index = _ApiOperationCurationIndex(
                current_curation_id=record.id,
                record_ids=(*tuple(item.id for item in view.history), record.id),
            )
            _write_model_atomic(root / "index.json", index)
            return record


def _validate_selection(
    *,
    owner_id: uuid.UUID,
    source: SourceView,
    revision_dir: Path,
    inventory_fingerprint: str,
    included_operation_ids: tuple[str, ...],
    excluded_operation_ids: tuple[str, ...],
    expected_current_curation_id: str | None,
) -> ApiOperationCurationView:
    inventory = _inventory(source, revision_dir)
    current_fingerprint = _inventory_fingerprint(source, inventory)
    if inventory_fingerprint != current_fingerprint:
        raise ApiOperationCurationConflict(
            "The discovered operation inventory changed. Refresh it before saving."
        )
    index, history = _load_history(
        revision_dir,
        owner_id=owner_id,
        source=source,
        inventory=inventory,
        inventory_fingerprint=current_fingerprint,
    )
    current = _current_record(index, history)
    observed_current_id = current.id if current is not None else None
    if expected_current_curation_id != observed_current_id:
        raise ApiOperationCurationConflict(
            "The operation curation changed. Refresh it before saving again."
        )
    if len(set(included_operation_ids)) != len(included_operation_ids) or len(
        set(excluded_operation_ids)
    ) != len(excluded_operation_ids):
        raise ApiOperationCurationConflict(
            "The operation selection contains a duplicate operation ID."
        )
    included = set(included_operation_ids)
    excluded = set(excluded_operation_ids)
    if included & excluded:
        raise ApiOperationCurationConflict(
            "An operation cannot be both included and excluded."
        )
    discovered = {item.operation_id for item in inventory}
    unknown = (included | excluded) - discovered
    if unknown:
        raise ApiOperationCurationConflict(
            "The operation selection contains an unknown discovered operation."
        )
    if included | excluded != discovered:
        raise ApiOperationCurationConflict(
            "The operation selection must explicitly classify every discovered operation."
        )
    return ApiOperationCurationView(
        source_id=source.source_id,
        source_revision_id=source.revision.revision_id,
        artifact_revision_id=_artifact_revision_id(source),
        inventory_fingerprint=current_fingerprint,
        operations=inventory,
        current=current,
        history=history,
    )


def _inventory(
    source: SourceView,
    revision_dir: Path,
) -> tuple[ApiOperationInventoryItem, ...]:
    if source.connector_key != "api" or source.revision.state is not SourceState.READY:
        raise SourceNotReady("The selected API Source revision is not ready.")
    artifact_revision_id = _artifact_revision_id(source)
    source_dir = revision_dir.parent.parent
    path = source_dir / "r" / artifact_revision_id / "a" / "graph" / "semantic_graph.json"
    try:
        document = json.loads(path.read_text(encoding="utf-8"))
        raw_nodes = document["nodes"]
    except (OSError, UnicodeDecodeError, json.JSONDecodeError, KeyError, TypeError) as error:
        raise ApiOperationCurationError(
            "The discovered API operation inventory is unavailable."
        ) from error
    if not isinstance(raw_nodes, list) or len(raw_nodes) > 10_000:
        raise ApiOperationCurationError(
            "The discovered API operation inventory is invalid."
        )
    values: list[ApiOperationInventoryItem] = []
    for raw in raw_nodes:
        if not isinstance(raw, dict) or raw.get("node_type") != "api_operation":
            continue
        facets = raw.get("facets")
        if not isinstance(facets, dict):
            raise ApiOperationCurationError(
                "The discovered API operation inventory is invalid."
            )
        try:
            values.append(
                ApiOperationInventoryItem(
                    operation_id=_required(facets.get("operation_id")),
                    graph_node_id=_required(raw.get("id")),
                    method=_required(facets.get("method")).upper(),
                    path_template=_required(facets.get("path")),
                    operation_class=_required(facets.get("operation_class")),
                )
            )
        except (ValueError, ValidationError) as error:
            raise ApiOperationCurationError(
                "The discovered API operation inventory is invalid."
            ) from error
    values.sort(key=lambda item: (item.operation_id, item.method, item.path_template))
    operation_ids = [item.operation_id for item in values]
    if len(operation_ids) != len(set(operation_ids)):
        raise ApiOperationCurationError(
            "The discovered API operation inventory contains duplicate operation IDs."
        )
    return tuple(values)


def _inventory_fingerprint(
    source: SourceView,
    inventory: tuple[ApiOperationInventoryItem, ...],
) -> str:
    value = {
        "source_id": source.source_id,
        "source_revision_id": source.revision.revision_id,
        "artifact_revision_id": _artifact_revision_id(source),
        "operations": [item.model_dump(mode="json") for item in inventory],
    }
    encoded = json.dumps(value, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def _load_history(
    revision_dir: Path,
    *,
    owner_id: uuid.UUID,
    source: SourceView,
    inventory: tuple[ApiOperationInventoryItem, ...],
    inventory_fingerprint: str,
) -> tuple[_ApiOperationCurationIndex, tuple[ApiOperationCurationRecord, ...]]:
    root = _curation_root(revision_dir)
    index_path = root / "index.json"
    if not index_path.exists():
        return _ApiOperationCurationIndex(), ()
    try:
        index = _ApiOperationCurationIndex.model_validate_json(
            index_path.read_text(encoding="utf-8")
        )
        if len(index.record_ids) != len(set(index.record_ids)):
            raise ValueError("duplicate record identity")
        history = tuple(
            ApiOperationCurationRecord.model_validate_json(
                (root / "records" / f"{record_id}.json").read_text(encoding="utf-8")
            )
            for record_id in index.record_ids
        )
    except (OSError, ValidationError, ValueError) as error:
        raise ApiOperationCurationError(
            "The saved API operation curation is unavailable."
        ) from error
    if tuple(item.id for item in history) != index.record_ids:
        raise ApiOperationCurationError(
            "The saved API operation curation is inconsistent."
        )
    expected_operations = {item.operation_id for item in inventory}
    previous_id: str | None = None
    for record in history:
        included = record.included_operation_ids
        excluded = record.excluded_operation_ids
        if (
            record.source_id != source.source_id
            or record.source_revision_id != source.revision.revision_id
            or record.artifact_revision_id != _artifact_revision_id(source)
            or record.inventory_fingerprint != inventory_fingerprint
            or record.selected_by_owner_id != owner_id
            or record.previous_curation_id != previous_id
            or len(included) != len(set(included))
            or len(excluded) != len(set(excluded))
            or set(included) & set(excluded)
            or set(included) | set(excluded) != expected_operations
        ):
            raise ApiOperationCurationError(
                "The saved API operation curation is inconsistent."
            )
        previous_id = record.id
    return index, history


def _current_record(
    index: _ApiOperationCurationIndex,
    history: tuple[ApiOperationCurationRecord, ...],
) -> ApiOperationCurationRecord | None:
    if index.current_curation_id is None:
        if history:
            raise ApiOperationCurationError(
                "The saved API operation curation is inconsistent."
            )
        return None
    if not history or history[-1].id != index.current_curation_id:
        raise ApiOperationCurationError(
            "The saved API operation curation is inconsistent."
        )
    return history[-1]


def _artifact_revision_id(source: SourceView) -> str:
    return source.revision.artifact_revision_id or source.revision.revision_id


def _curation_root(revision_dir: Path) -> Path:
    return revision_dir / "operation-curation"


def _required(value: Any) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError("required string")
    return value


def _write_model_atomic(path: Path, model: BaseModel) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    try:
        temporary.write_text(model.model_dump_json(indent=2), encoding="utf-8")
        temporary.replace(path)
    except OSError as error:
        raise ApiOperationCurationError(
            "The API operation curation could not be persisted."
        ) from error


__all__ = [
    "ApiOperationCurationConflict",
    "ApiOperationCurationError",
    "ApiOperationCurationRecord",
    "ApiOperationCurationService",
    "ApiOperationCurationView",
    "ApiOperationInventoryItem",
]
