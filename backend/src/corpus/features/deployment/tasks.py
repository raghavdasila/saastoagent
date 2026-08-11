from __future__ import annotations

import asyncio
import uuid

from huey import SqliteHuey

from .execution import DeploymentProcessor


def register_deployment_task(huey: SqliteHuey, processor: DeploymentProcessor):
    @huey.task(retries=0)
    def publish_agent_build(job_id: str) -> dict[str, object]:
        return asyncio.run(processor.process(uuid.UUID(job_id)))

    return publish_agent_build


__all__ = ["register_deployment_task"]
