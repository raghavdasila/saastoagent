from __future__ import annotations

import asyncio
import uuid

from huey import SqliteHuey

from .generation import EvaluationGenerationProcessor


def register_evaluation_generation_task(
    huey: SqliteHuey,
    processor: EvaluationGenerationProcessor,
):
    @huey.task(retries=0)
    def generate_build_evaluation_set(job_id: str) -> dict[str, object]:
        return asyncio.run(processor.process(uuid.UUID(job_id)))

    return generate_build_evaluation_set


__all__ = ["register_evaluation_generation_task"]
