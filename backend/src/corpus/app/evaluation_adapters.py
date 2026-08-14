from __future__ import annotations

import uuid
from pathlib import Path
from typing import Mapping

from corpus.features.builder.ports import BuilderRepository
from corpus.features.evaluation.ports import (
    EvaluationGeneratedBatch,
    EvaluationGeneratedCase,
    EvaluationGenerationBuild,
)
from corpus.features.sources.connectors.api.engine import ApiSourceEngine
from corpus.integrations.toolrouter.engine.openapi_loader import read_normalized_bundle


class CorpusEvaluationGenerationGateway:
    """Compose Builder lineage and ToolRouter case generation for Evaluation."""

    def __init__(self, builds: BuilderRepository, engine: ApiSourceEngine) -> None:
        self.builds = builds
        self.engine = engine

    async def get_build(
        self,
        organization_id: uuid.UUID,
        agent_id: uuid.UUID,
        build_id: uuid.UUID,
    ) -> EvaluationGenerationBuild:
        value = await self.builds.get(organization_id, agent_id, build_id)
        return EvaluationGenerationBuild(
            id=value.id,
            status=value.status,
            runtime_build_hash=value.runtime_build_hash,
            source_bindings=tuple(dict(item) for item in value.source_bindings),
        )

    def generate(
        self,
        *,
        binding: Mapping[str, object],
        evalset_id: str,
        categories: tuple[str, ...],
    ) -> EvaluationGeneratedBatch:
        artifact_dir = Path(str(binding["artifact_dir"]))
        operation_ids = tuple(map(str, binding["included_operation_ids"]))
        endpoint_by_operation = _endpoint_map(artifact_dir, operation_ids)
        result = self.engine.generate_evalset(
            artifact_dir=artifact_dir,
            evalset_id=evalset_id,
            categories=categories,
            tasks_per_category=1,
            max_generation_attempts=2,
            max_review_attempts=2,
            allowed_endpoint_ids=tuple(
                endpoint_by_operation[value] for value in operation_ids
            ),
        )
        operation_by_endpoint = {
            endpoint: operation for operation, endpoint in endpoint_by_operation.items()
        }
        cases: list[EvaluationGeneratedCase] = []
        for task in result.accepted_tasks:
            endpoint_sequence = tuple(
                map(str, task.get("expected_endpoint_sequence", ()))
            )
            if (
                len(endpoint_sequence) != 1
                or endpoint_sequence[0] not in operation_by_endpoint
            ):
                raise ValueError(
                    "A generated case escaped the exact curated operation subset."
                )
            metadata = task.get("evalset")
            cases.append(EvaluationGeneratedCase(
                task_id=str(task.get("id", "")).strip(),
                query=str(task.get("query", "")).strip(),
                category=(
                    str(metadata.get("query_category", "routing"))
                    if isinstance(metadata, dict)
                    else "routing"
                ),
                expected_operation_ids=(
                    operation_by_endpoint[endpoint_sequence[0]],
                ),
            ))
        return EvaluationGeneratedBatch(
            status=result.status,
            accepted_count=result.accepted_count,
            expected_count=result.expected_count,
            generator_model=result.generator_model,
            generator_model_digest=result.generator_model_digest,
            reviewer_model=result.reviewer_model,
            reviewer_model_digest=result.reviewer_model_digest,
            cases=tuple(cases),
        )


def _endpoint_map(
    artifact_dir: Path, operation_ids: tuple[str, ...]
) -> dict[str, str]:
    bundle = read_normalized_bundle(artifact_dir / "normalized")
    matches = {
        operation: tuple(
            endpoint.id
            for endpoint in bundle.endpoints
            if endpoint.operation_id == operation
        )
        for operation in operation_ids
    }
    if not matches or any(len(values) != 1 for values in matches.values()):
        raise ValueError(
            "Every curated build operation must resolve to one exact ToolRouter endpoint."
        )
    return {operation: values[0] for operation, values in matches.items()}


__all__ = ["CorpusEvaluationGenerationGateway"]
