from __future__ import annotations

import asyncio
import uuid

from huey import SqliteHuey

from .execution import BuilderAssemblyProcessor


def register_builder_assembly_task(huey: SqliteHuey, processor: BuilderAssemblyProcessor):
    @huey.task(retries=0)
    def assemble_agent_build(job_id: str) -> dict[str, object]:
        return asyncio.run(processor.process(uuid.UUID(job_id)))

    return assemble_agent_build


__all__ = ["register_builder_assembly_task"]
