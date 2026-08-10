from __future__ import annotations

import asyncio
import uuid

from huey import SqliteHuey

from .service import SourceJobProcessor


def register_source_processing_task(
    huey: SqliteHuey,
    processor: SourceJobProcessor,
):
    """Register the real feature-owned Huey task on one Corpus queue."""

    @huey.task(retries=0)
    def process_source_revision(job_id: str) -> dict[str, object]:
        return asyncio.run(processor.process(uuid.UUID(job_id)))

    return process_source_revision


__all__ = ["register_source_processing_task"]
