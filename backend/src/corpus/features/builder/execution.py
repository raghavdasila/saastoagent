from __future__ import annotations

import uuid

from corpus.jobs import DurableJobLifecyclePort

from .ports import BuilderConflict, BuilderUnavailable
from .service import BuilderService


class BuilderAssemblyProcessor:
    """Materialize one exact queued build attempt in the durable worker."""

    def __init__(self, jobs: DurableJobLifecyclePort, service: BuilderService) -> None:
        self.jobs = jobs
        self.service = service

    async def process(self, job_id: uuid.UUID) -> dict[str, object]:
        job = await self.jobs.mark_running(job_id=job_id)
        build_id: uuid.UUID | None = None
        try:
            if job.job_type != "builder.assemble":
                raise ValueError("The durable job type is not owned by Builder assembly.")
            agent_id = uuid.UUID(str(job.payload.get("agent_id", "")))
            build_id = uuid.UUID(str(job.payload.get("build_id", "")))
            build_request_id = uuid.UUID(str(job.payload.get("build_request_id", "")))
            design_revision_id = uuid.UUID(str(job.payload.get("design_revision_id", "")))
            attempt_number = int(job.payload.get("attempt_number", 0))
            if attempt_number < 1:
                raise ValueError("The queued build attempt number is invalid.")
            await self.service.repository.mark_running(job.owner_id, build_id, job.id)
            completed = await self.service.execute_assembly(
                job.owner_id,
                agent_id,
                build_id=build_id,
                expected_build_request_id=build_request_id,
                expected_design_revision_id=design_revision_id,
                expected_attempt_number=attempt_number,
            )
            result: dict[str, object] = {
                "agent_id": str(agent_id),
                "build_id": str(completed.id),
                "build_request_id": str(completed.build_request_id),
                "design_revision_id": str(completed.design_revision_id),
                "attempt_number": completed.attempt_number,
                "runtime_build_hash": completed.runtime_build_hash,
                "status": completed.status,
            }
            await self.jobs.mark_succeeded(job_id=job.id, result=result)
            return result
        except Exception as error:
            message = _public_failure(error)
            if build_id is not None:
                try:
                    await self.service.repository.fail(
                        job.owner_id,
                        build_id,
                        code="builder_assembly_failed",
                        message=message,
                    )
                except (BuilderConflict, BuilderUnavailable):
                    pass
            await self.jobs.mark_failed(
                job_id=job.id,
                error_code="builder_assembly_failed",
                error_message=message,
            )
            raise


def _public_failure(error: Exception) -> str:
    if isinstance(error, (BuilderConflict, BuilderUnavailable, ValueError)):
        value = str(error).strip()
        if value:
            return value[:500]
    return "The queued Agent build failed."


__all__ = ["BuilderAssemblyProcessor"]
