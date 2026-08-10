from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping, Protocol

from ..contracts import (
    SourceEvalsetResult,
    SourceRetrievalResult,
    SourceTraceMode,
)


@dataclass(frozen=True)
class SourceUpload:
    filename: str
    content_type: str
    content: bytes
    description_filename: str | None = None
    description_content_type: str | None = None
    description_content: bytes | None = None


@dataclass(frozen=True)
class ValidatedSourceUpload:
    filename: str
    content_type: str
    content: bytes
    description_filename: str | None = None
    description_content_type: str | None = None
    description_content: bytes | None = None


class SourceConnector(Protocol):
    key: str

    def validate_upload(self, upload: SourceUpload) -> ValidatedSourceUpload: ...

    def ingest(self, *, input_path: Path, artifact_dir: Path) -> dict[str, object]: ...

    def retrieve(
        self,
        *,
        artifact_dir: Path,
        query: str,
        top_k: int,
        trace_mode: SourceTraceMode,
        provided_params: Mapping[str, Any] | None,
    ) -> SourceRetrievalResult: ...

    def generate_evalset(
        self,
        *,
        artifact_dir: Path,
        evalset_id: str,
        categories: tuple[str, ...],
        tasks_per_category: int,
        max_generation_attempts: int,
        max_review_attempts: int,
    ) -> SourceEvalsetResult: ...


__all__ = ["SourceConnector", "SourceUpload", "ValidatedSourceUpload"]
