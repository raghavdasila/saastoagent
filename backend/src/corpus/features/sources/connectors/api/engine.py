from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Literal, Mapping, Protocol

from ...contracts import (
    SourceEvalsetResult,
    SourceRetrievalResult,
    SourceTraceMode,
)


@dataclass(frozen=True)
class SourceManagedParameter:
    name: str
    location: Literal["header", "path", "query", "body"]


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
        allowed_endpoint_ids: tuple[str, ...] | None = None,
        managed_parameters: tuple[SourceManagedParameter, ...] = (),
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
        allowed_endpoint_ids: tuple[str, ...] | None = None,
    ) -> SourceEvalsetResult: ...


__all__ = ["ApiSourceEngine", "SourceManagedParameter"]
