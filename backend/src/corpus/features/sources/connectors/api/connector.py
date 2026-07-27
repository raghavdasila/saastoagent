from __future__ import annotations

from pathlib import Path
from typing import Any, Mapping

from ...contracts import (
    SourceEvalsetResult,
    SourceRetrievalResult,
    SourceTraceMode,
)

from ..base import SourceUpload, ValidatedSourceUpload
from .engine import ApiSourceEngine
from .intake import validate_api_upload


class ApiSourceConnector:
    key = "api"

    def __init__(
        self,
        engine: ApiSourceEngine,
        *,
        max_upload_bytes: int,
    ) -> None:
        if max_upload_bytes <= 0:
            raise ValueError("API source max_upload_bytes must be positive.")
        self.engine = engine
        self.max_upload_bytes = max_upload_bytes

    def validate_upload(self, upload: SourceUpload) -> ValidatedSourceUpload:
        return validate_api_upload(
            upload,
            max_upload_bytes=self.max_upload_bytes,
        )

    def ingest(self, *, input_path: Path, artifact_dir: Path) -> dict[str, object]:
        return self.engine.ingest(
            input_path=input_path,
            artifact_dir=artifact_dir,
        )

    def retrieve(
        self,
        *,
        artifact_dir: Path,
        query: str,
        top_k: int,
        trace_mode: SourceTraceMode,
        provided_params: Mapping[str, Any] | None,
    ) -> SourceRetrievalResult:
        return self.engine.retrieve(
            artifact_dir=artifact_dir,
            query=query,
            top_k=top_k,
            trace_mode=trace_mode,
            provided_params=provided_params,
        )

    def generate_evalset(
        self,
        *,
        artifact_dir: Path,
        evalset_id: str,
        categories: tuple[str, ...],
        tasks_per_category: int,
        max_generation_attempts: int,
        max_review_attempts: int,
    ) -> SourceEvalsetResult:
        return self.engine.generate_evalset(
            artifact_dir=artifact_dir,
            evalset_id=evalset_id,
            categories=categories,
            tasks_per_category=tasks_per_category,
            max_generation_attempts=max_generation_attempts,
            max_review_attempts=max_review_attempts,
        )


__all__ = ["ApiSourceConnector"]
