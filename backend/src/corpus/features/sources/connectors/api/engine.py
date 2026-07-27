from __future__ import annotations

from pathlib import Path
from typing import Any, Mapping, Protocol

from ...contracts import (
    SourceEvalsetResult,
    SourceRetrievalResult,
    SourceTraceMode,
)


class ApiSourceEngine(Protocol):
    """Replaceable parser/retrieval/evalset engine used by the API connector."""

    def ingest(
        self,
        *,
        input_path: Path,
        artifact_dir: Path,
    ) -> dict[str, object]: ...

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


__all__ = ["ApiSourceEngine"]
