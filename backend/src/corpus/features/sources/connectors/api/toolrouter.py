from __future__ import annotations

from dataclasses import asdict
from pathlib import Path
from typing import Any, Mapping

from corpus.integrations.toolrouter import (
    EvalsetRequest,
    IngestRequest,
    RetrievalRequest,
    ToolRouterAdapter,
    ToolRouterArtifactError,
    ToolRouterDependencyError,
    ToolRouterInputError,
    ToolRouterIntegrationError,
)

from ...contracts import (
    SourceEvalsetResult,
    SourceRankedItem,
    SourceRetrievalResult,
    SourceRetrievalStep,
    SourceTraceMode,
)
from ...errors import (
    SourceArtifactError,
    SourceDependencyError,
    SourceInputError,
    SourceIntegrationError,
)


class ToolRouterApiSourceEngine:
    """Translate between the API connector engine port and ToolRouter."""

    def __init__(self, adapter: ToolRouterAdapter) -> None:
        self.adapter = adapter

    def ingest(
        self,
        *,
        input_path: Path,
        artifact_dir: Path,
    ) -> dict[str, object]:
        try:
            result = self.adapter.ingest(
                IngestRequest(source_path=input_path, artifact_dir=artifact_dir)
            )
        except ToolRouterIntegrationError as error:
            raise _source_error(error) from error
        values = asdict(result)
        values.pop("artifact_dir", None)
        return values

    def retrieve(
        self,
        *,
        artifact_dir: Path,
        query: str,
        top_k: int,
        trace_mode: SourceTraceMode,
        provided_params: Mapping[str, Any] | None,
    ) -> SourceRetrievalResult:
        try:
            result = self.adapter.retrieve(
                RetrievalRequest(
                    artifact_dir=artifact_dir,
                    query=query,
                    top_k=top_k,
                    trace_mode=trace_mode,
                    provided_params=provided_params,
                )
            )
        except ToolRouterIntegrationError as error:
            raise _source_error(error) from error
        return SourceRetrievalResult(
            query=result.query,
            decision_type=result.decision_type,
            decision_reason=result.decision_reason,
            decomposed=result.decomposed,
            steps=tuple(
                SourceRetrievalStep(
                    query=step.query,
                    ranked_items=tuple(
                        SourceRankedItem(
                            item_id=item.endpoint_id,
                            item_kind="api_operation",
                            score=item.score,
                        )
                        for item in step.ranked_endpoints
                    ),
                    trace=dict(step.trace),
                )
                for step in result.steps
            ),
            missing_inputs=tuple(result.missing_params),
            ambiguity=(
                dict(result.ambiguity) if result.ambiguity is not None else None
            ),
            decision_evidence=dict(result.decision_evidence),
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
        try:
            result = self.adapter.generate_evalset(
                EvalsetRequest(
                    artifact_dir=artifact_dir,
                    evalset_id=evalset_id,
                    categories=categories,
                    tasks_per_category=tasks_per_category,
                    max_generation_attempts=max_generation_attempts,
                    max_review_attempts=max_review_attempts,
                )
            )
        except ToolRouterIntegrationError as error:
            raise _source_error(error) from error
        return SourceEvalsetResult(
            evalset_id=result.evalset_id,
            status=result.status,
            completed_count=result.completed_count,
            expected_count=result.expected_count,
            accepted_count=result.accepted_count,
            quarantined_count=result.quarantined_count,
            terminal_status_counts=dict(result.terminal_status_counts),
            offline_tokens=result.offline_tokens,
            generator_model=result.generator_model,
            generator_model_digest=result.generator_model_digest,
            reviewer_model=result.reviewer_model,
            reviewer_model_digest=result.reviewer_model_digest,
            accepted_tasks=tuple(dict(task) for task in result.accepted_tasks),
            summary=dict(result.summary),
        )


def _source_error(error: ToolRouterIntegrationError) -> SourceIntegrationError:
    if isinstance(error, ToolRouterInputError):
        return SourceInputError(str(error))
    if isinstance(error, ToolRouterDependencyError):
        return SourceDependencyError(str(error))
    if isinstance(error, ToolRouterArtifactError):
        return SourceArtifactError(str(error))
    return SourceIntegrationError(str(error))


__all__ = ["ToolRouterApiSourceEngine"]
