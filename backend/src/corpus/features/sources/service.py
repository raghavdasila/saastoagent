from __future__ import annotations

from collections.abc import Iterable, Mapping
import uuid
from typing import Any

from corpus.jobs import (
    DurableJobEnqueueError,
    DurableJobPort,
)

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
        jobs: DurableJobPort,
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
        self.jobs = jobs

    async def create_source(
        self,
        *,
        owner_id: uuid.UUID,
        connector_key: str,
        display_name: str,
        upload: SourceUpload,
    ) -> SourceView:
        connector = self._connector(connector_key)
        validated = connector.validate_upload(upload)
        prepared = self.repository.begin_source(
            owner_key=str(owner_id),
            connector_key=connector_key,
            display_name=display_name,
            original_filename=validated.filename,
            content=validated.content,
            description_filename=validated.description_filename,
            description_content=validated.description_content,
        )
        try:
            job = await self.jobs.enqueue(
                owner_id=owner_id,
                job_type="sources.process_api_revision",
                payload={
                    "source_id": prepared.source.source_id,
                    "revision_id": prepared.revision.revision_id,
                },
                max_attempts=3,
            )
        except DurableJobEnqueueError as error:
            self.repository.attach_job(
                owner_key=str(owner_id),
                source_id=prepared.source.source_id,
                revision_id=prepared.revision.revision_id,
                job_id=str(error.job_id),
            )
            self.repository.mark_failed(
                owner_key=str(owner_id),
                source_id=prepared.source.source_id,
                revision_id=prepared.revision.revision_id,
                failure_code="queue_unavailable",
                failure_message="Source processing could not be queued.",
            )
            raise
        return self.repository.attach_job(
            owner_key=str(owner_id),
            source_id=prepared.source.source_id,
            revision_id=prepared.revision.revision_id,
            job_id=str(job.id),
        )

    async def retry_processing(
        self, *, owner_id: uuid.UUID, source_id: str
    ) -> SourceView:
        owner_key = str(owner_id)
        source = self.repository.get(owner_key=owner_key, source_id=source_id)
        if source.revision.state is not SourceState.FAILED:
            raise SourceNotReady("Only failed source processing can be retried.")
        if source.revision.job_id is None:
            raise SourceNotReady("The failed source has no durable job to retry.")
        self.repository.mark_queued_for_retry(
            owner_key=owner_key,
            source_id=source_id,
            revision_id=source.revision.revision_id,
        )
        try:
            await self.jobs.retry(
                owner_id=owner_id,
                job_id=uuid.UUID(source.revision.job_id),
            )
        except Exception:
            self.repository.mark_failed(
                owner_key=owner_key,
                source_id=source_id,
                revision_id=source.revision.revision_id,
                failure_code="retry_unavailable",
                failure_message="Source processing retry could not be queued.",
            )
            raise
        return self.repository.get(owner_key=owner_key, source_id=source_id)

    def list_sources(self, *, owner_key: str) -> tuple[SourceView, ...]:
        return self.repository.list(owner_key=owner_key)

    def get_source(
        self,
        *,
        owner_key: str,
        source_id: str,
        revision_id: str | None = None,
    ) -> SourceView:
        if revision_id is None:
            return self.repository.get(owner_key=owner_key, source_id=source_id)
        return self.repository.get_revision(
            owner_key=owner_key,
            source_id=source_id,
            revision_id=revision_id,
        )

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


def one_current_ready_api_source(
    repository: LocalSourceRepository,
    owner_id: uuid.UUID,
) -> SourceView:
    """Resolve chat context only when one current ready API Source is unambiguous."""

    matches = tuple(
        source
        for source in repository.list(owner_key=str(owner_id))
        if source.connector_key == "api"
        and source.revision.state is SourceState.READY
    )
    if len(matches) != 1:
        raise SourceNotReady(
            "This action requires one exact current ready API Source; choose the API you mean."
        )
    return matches[0]


class SourceJobProcessor:
    """Feature-owned execution for one durable Source processing job."""

    def __init__(self, repository, job_repository, *, connectors) -> None:
        self.repository = repository
        self.job_repository = job_repository
        self.connectors = {connector.key: connector for connector in connectors}

    async def process(self, job_id: uuid.UUID) -> dict[str, object]:
        job = await self.job_repository.mark_running(job_id=job_id)
        payload = job.payload
        owner_key = str(job.owner_id)
        source_id = str(payload.get("source_id", ""))
        revision_id = str(payload.get("revision_id", ""))
        try:
            if job.job_type != "sources.process_api_revision":
                raise ValueError("The durable job type is not owned by Sources.")
            source = self.repository.get(
                owner_key=owner_key, source_id=source_id
            )
            if source.revision.revision_id != revision_id:
                raise ValueError("The source revision no longer matches its job.")
            self.repository.mark_running(
                owner_key=owner_key,
                source_id=source_id,
                revision_id=revision_id,
            )
            connector = self.connectors[source.connector_key]
            input_path = self.repository.input_path(
                owner_key=owner_key, source_id=source_id
            )
            artifact_dir = self.repository.artifact_dir(
                owner_key=owner_key, source_id=source_id
            )
            summary = connector.ingest(
                input_path=input_path,
                artifact_dir=artifact_dir,
            )
            self.repository.mark_ready(
                owner_key=owner_key,
                source_id=source_id,
                revision_id=revision_id,
                summary=summary,
            )
            await self.job_repository.mark_succeeded(
                job_id=job_id,
                result={
                    "source_id": source_id,
                    "revision_id": revision_id,
                    "summary": summary,
                },
            )
            return dict(summary)
        except Exception as error:
            message = str(error) or type(error).__name__
            try:
                current = self.repository.get(
                    owner_key=owner_key, source_id=source_id
                )
                if current.revision.state in {
                    SourceState.QUEUED,
                    SourceState.RUNNING,
                }:
                    self.repository.mark_failed(
                        owner_key=owner_key,
                        source_id=source_id,
                        revision_id=revision_id,
                        failure_code="source_processing_failed",
                        failure_message=message[:500],
                    )
            finally:
                await self.job_repository.mark_failed(
                    job_id=job_id,
                    error_code="source_processing_failed",
                    error_message=message[:500],
                )
            raise


__all__ = ["SourceJobProcessor", "SourceService", "one_current_ready_api_source"]
