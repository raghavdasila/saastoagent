from __future__ import annotations

import uuid
from pathlib import Path

from corpus.features.builder.ports import BuilderRepository
from corpus.features.sources.connectors.api.toolrouter import ToolRouterApiSourceEngine
from corpus.integrations.agent_execution import EligibilityProjection
from corpus.integrations.toolrouter.engine.ladder_llm import stable_hash
from corpus.integrations.toolrouter.engine.openapi_loader import read_normalized_bundle
from corpus.jobs.repository import SqlAlchemyDurableJobRepository

from .ports import EvaluationRepository


class EvaluationGenerationProcessor:
    """Generate exact-build draft cases through the real ToolRouter factory."""

    def __init__(
        self,
        jobs: SqlAlchemyDurableJobRepository,
        evaluations: EvaluationRepository,
        builds: BuilderRepository,
        engine: ToolRouterApiSourceEngine,
    ) -> None:
        self.jobs = jobs
        self.evaluations = evaluations
        self.builds = builds
        self.engine = engine

    async def process(self, job_id: uuid.UUID) -> dict[str, object]:
        job = await self.jobs.mark_running(job_id=job_id)
        payload = job.payload
        evaluation_set_id = uuid.UUID(str(payload.get("evaluation_set_id", "")))
        agent_id = uuid.UUID(str(payload.get("agent_id", "")))
        build_id = uuid.UUID(str(payload.get("build_id", "")))
        categories = tuple(map(str, payload.get("categories", ())))
        try:
            if job.job_type != "evaluation.generate_build_evalset":
                raise ValueError("The durable job type is not owned by Evaluation.")
            evaluation_set = await self.evaluations.get_set(
                job.owner_id, agent_id, evaluation_set_id
            )
            build = await self.builds.get(job.owner_id, agent_id, build_id)
            if evaluation_set.build_id != build.id or build.status != "ready":
                raise ValueError("The exact immutable build is unavailable for generation.")
            await self.evaluations.mark_generation_running(
                job.owner_id, evaluation_set.id
            )
            accepted = 0
            expected = 0
            source_summaries: list[dict[str, object]] = []
            for index, binding in enumerate(build.source_bindings):
                artifact_dir = Path(str(binding["artifact_dir"]))
                operation_ids = tuple(map(str, binding["included_operation_ids"]))
                endpoint_by_operation = _endpoint_map(artifact_dir, operation_ids)
                result = self.engine.generate_evalset(
                    artifact_dir=artifact_dir,
                    evalset_id=f"{evaluation_set.id.hex}-{index}",
                    categories=categories,
                    tasks_per_category=1,
                    max_generation_attempts=2,
                    max_review_attempts=2,
                    allowed_endpoint_ids=tuple(
                        endpoint_by_operation[value] for value in operation_ids
                    ),
                )
                if result.status != "ready" or not result.accepted_tasks:
                    raise ValueError(
                        "ToolRouter did not produce accepted cases for the exact build."
                    )
                operation_by_endpoint = {
                    endpoint: operation
                    for operation, endpoint in endpoint_by_operation.items()
                }
                for task in result.accepted_tasks:
                    endpoint_sequence = tuple(
                        map(str, task.get("expected_endpoint_sequence", ()))
                    )
                    if len(endpoint_sequence) != 1 or endpoint_sequence[0] not in operation_by_endpoint:
                        raise ValueError(
                            "A generated case escaped the exact curated operation subset."
                        )
                    query = str(task.get("query", "")).strip()
                    task_id = str(task.get("id", "")).strip()
                    if not query or not task_id:
                        raise ValueError("A generated evaluation case is incomplete.")
                    metadata = task.get("evalset")
                    category = (
                        str(metadata.get("query_category", "routing"))
                        if isinstance(metadata, dict)
                        else "routing"
                    )
                    await self.evaluations.add_generated_case(
                        job.owner_id,
                        evaluation_set,
                        task_id=task_id,
                        title=_title(query),
                        message=query,
                        category=category,
                        difficulty=_difficulty(category),
                        expected_operation_ids=(
                            operation_by_endpoint[endpoint_sequence[0]],
                        ),
                        # Generated coverage begins as an owner-visible draft. A generated
                        # query can legitimately expose a routing weakness; it must not
                        # silently become a deployment gate before the owner marks it
                        # required. Owner-recorded Sandbox cases retain the required
                        # baseline role.
                        mandatory=False,
                    )
                accepted += result.accepted_count
                expected += result.expected_count
                source_summaries.append({
                    "source_id": str(binding["source_id"]),
                    "source_revision_id": str(binding["source_revision_id"]),
                    "curation_id": str(binding["curation_id"]),
                    "accepted_count": result.accepted_count,
                    "expected_count": result.expected_count,
                    "generator_model": result.generator_model,
                    "generator_model_digest": result.generator_model_digest,
                    "reviewer_model": result.reviewer_model,
                    "reviewer_model_digest": result.reviewer_model_digest,
                })
            summary: dict[str, object] = {
                "build_id": str(build.id),
                "runtime_build_hash": str(build.runtime_build_hash),
                "accepted_count": accepted,
                "expected_count": expected,
                "source_count": len(source_summaries),
                "generation_fingerprint": stable_hash(source_summaries),
                "sources": source_summaries,
            }
            await self.evaluations.add_eligibility(
                job.owner_id,
                agent_id,
                build.id,
                build.runtime_build_hash,
                EligibilityProjection(
                    build.runtime_build_hash,
                    False,
                    (),
                    ("generated_evaluation_cases_pending",),
                ),
            )
            await self.evaluations.mark_generation_ready(
                job.owner_id, evaluation_set.id, summary
            )
            await self.jobs.mark_succeeded(job_id=job_id, result=summary)
            return summary
        except Exception as error:
            message = (str(error) or type(error).__name__)[:500]
            try:
                await self.evaluations.mark_generation_failed(
                    job.owner_id,
                    evaluation_set_id,
                    code="evaluation_generation_failed",
                    message=message,
                )
            finally:
                await self.jobs.mark_failed(
                    job_id=job_id,
                    error_code="evaluation_generation_failed",
                    error_message=message,
                )
            raise


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


def _difficulty(category: str) -> str:
    if category in {"typo_or_noisy", "low_lexical_overlap"}:
        return "hard"
    if category in {"verbose_or_indirect", "non_exact_wording"}:
        return "medium"
    return "easy"


def _title(query: str) -> str:
    value = " ".join(query.split())
    return value if len(value) <= 160 else f"{value[:157]}..."


__all__ = ["EvaluationGenerationProcessor"]
