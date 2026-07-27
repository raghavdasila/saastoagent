from __future__ import annotations

from collections.abc import Iterable, Mapping
from typing import Any

from .contracts import (
    SourceEvalsetResult,
    SourceRetrievalResult,
    SourceTraceMode,
)

from .connectors.base import SourceConnector, SourceUpload
from .models import SourceState, SourceView
from .repository import LocalSourceRepository, SourceNotReady


class SourceService:
    def __init__(
        self,
        repository: LocalSourceRepository,
        *,
        connectors: Iterable[SourceConnector],
    ) -> None:
        indexed: dict[str, SourceConnector] = {}
        for connector in connectors:
            if connector.key in indexed:
                raise ValueError(
                    f"Duplicate source connector registration: {connector.key}"
                )
            indexed[connector.key] = connector
        if not indexed:
            raise ValueError("SourceService requires at least one connector.")
        self.repository = repository
        self.connectors = indexed

    def create_source(
        self,
        *,
        owner_key: str,
        connector_key: str,
        display_name: str,
        upload: SourceUpload,
    ) -> SourceView:
        connector = self._connector(connector_key)
        validated = connector.validate_upload(upload)
        prepared = self.repository.begin_source(
            owner_key=owner_key,
            connector_key=connector_key,
            display_name=display_name,
            original_filename=validated.filename,
            content=validated.content,
        )
        try:
            summary = connector.ingest(
                input_path=prepared.input_path,
                artifact_dir=prepared.artifact_dir,
            )
        except Exception as error:
            self.repository.mark_failed(
                owner_key=owner_key,
                source_id=prepared.source.source_id,
                revision_id=prepared.revision.revision_id,
                failure_code="source_processing_failed",
                failure_message=str(error) or type(error).__name__,
            )
            raise
        return self.repository.mark_ready(
            owner_key=owner_key,
            source_id=prepared.source.source_id,
            revision_id=prepared.revision.revision_id,
            summary=summary,
        )

    def list_sources(self, *, owner_key: str) -> tuple[SourceView, ...]:
        return self.repository.list(owner_key=owner_key)

    def get_source(self, *, owner_key: str, source_id: str) -> SourceView:
        return self.repository.get(owner_key=owner_key, source_id=source_id)

    def retrieve(
        self,
        *,
        owner_key: str,
        source_id: str,
        query: str,
        top_k: int,
        trace_mode: SourceTraceMode,
        provided_params: Mapping[str, Any] | None,
    ) -> SourceRetrievalResult:
        source, connector = self._ready_source(owner_key, source_id)
        return connector.retrieve(
            artifact_dir=self.repository.artifact_dir(
                owner_key=owner_key, source_id=source.source_id
            ),
            query=query,
            top_k=top_k,
            trace_mode=trace_mode,
            provided_params=provided_params,
        )

    def generate_evalset(
        self,
        *,
        owner_key: str,
        source_id: str,
        evalset_id: str,
        categories: tuple[str, ...],
        tasks_per_category: int,
        max_generation_attempts: int = 2,
        max_review_attempts: int = 2,
    ) -> SourceEvalsetResult:
        source, connector = self._ready_source(owner_key, source_id)
        return connector.generate_evalset(
            artifact_dir=self.repository.artifact_dir(
                owner_key=owner_key, source_id=source.source_id
            ),
            evalset_id=evalset_id,
            categories=categories,
            tasks_per_category=tasks_per_category,
            max_generation_attempts=max_generation_attempts,
            max_review_attempts=max_review_attempts,
        )

    def _ready_source(
        self, owner_key: str, source_id: str
    ) -> tuple[SourceView, SourceConnector]:
        source = self.repository.get(owner_key=owner_key, source_id=source_id)
        if source.revision.state is not SourceState.READY:
            raise SourceNotReady(
                f"Source revision is {source.revision.state.value}, not ready."
            )
        return source, self._connector(source.connector_key)

    def _connector(self, connector_key: str) -> SourceConnector:
        try:
            return self.connectors[connector_key]
        except KeyError as error:
            raise ValueError(
                f"Unknown source connector: {connector_key}"
            ) from error


__all__ = ["SourceService"]
