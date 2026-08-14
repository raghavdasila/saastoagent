from __future__ import annotations

import uuid
import hashlib
import json

from corpus.shared.agent_execution import EligibilityProjection
from corpus.jobs import DurableJobLifecyclePort

from .ports import EvaluationGenerationGateway, EvaluationRepository


class EvaluationGenerationProcessor:
    """Generate exact-build draft cases through the real ToolRouter factory."""

    def __init__(
        self,
        jobs: DurableJobLifecyclePort,
        evaluations: EvaluationRepository,
        generation: EvaluationGenerationGateway,
    ) -> None:
        self.jobs = jobs
        self.evaluations = evaluations
        self.generation = generation

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
            build = await self.generation.get_build(job.owner_id, agent_id, build_id)
            if evaluation_set.build_id != build.id or build.status != "ready":
                raise ValueError("The exact immutable build is unavailable for generation.")
            await self.evaluations.mark_generation_running(
                job.owner_id, evaluation_set.id
            )
            accepted = 0
            expected = 0
            source_summaries: list[dict[str, object]] = []
            for index, binding in enumerate(build.source_bindings):
                result = self.generation.generate(
                    binding=binding,
                    evalset_id=f"{evaluation_set.id.hex}-{index}",
                    categories=categories,
                )
                if result.status != "ready" or not result.cases:
                    raise ValueError(
                        "ToolRouter did not produce accepted cases for the exact build."
                    )
                for task in result.cases:
                    if not task.query or not task.task_id or len(task.expected_operation_ids) != 1:
                        raise ValueError("A generated evaluation case is incomplete.")
                    await self.evaluations.add_generated_case(
                        job.owner_id,
                        evaluation_set,
                        task_id=task.task_id,
                        title=_title(task.query),
                        message=task.query,
                        category=task.category,
                        difficulty=_difficulty(task.category),
                        expected_operation_ids=task.expected_operation_ids,
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
                "generation_fingerprint": _stable_hash(source_summaries),
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


def _stable_hash(value: object) -> str:
    encoded = json.dumps(value, sort_keys=True, ensure_ascii=True).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


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
