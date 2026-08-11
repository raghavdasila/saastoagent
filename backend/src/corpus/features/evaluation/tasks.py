from __future__ import annotations

import asyncio
import uuid

from huey import SqliteHuey

from .execution import EvaluationRunProcessor
from .generation import EvaluationGenerationProcessor


def register_evaluation_generation_task(
    huey: SqliteHuey,
    processor: EvaluationGenerationProcessor,
):
    @huey.task(retries=0)
    def generate_build_evaluation_set(job_id: str) -> dict[str, object]:
        return asyncio.run(processor.process(uuid.UUID(job_id)))

    return generate_build_evaluation_set


def register_evaluation_run_task(
    huey: SqliteHuey,
    processor: EvaluationRunProcessor,
):
    @huey.task(retries=0)
    def run_evaluation_case(job_id: str) -> dict[str, object]:
        return asyncio.run(processor.process(uuid.UUID(job_id)))

    return run_evaluation_case


__all__ = [
    "register_evaluation_generation_task",
    "register_evaluation_run_task",
]
