from __future__ import annotations

import uuid

from corpus.jobs.repository import SqlAlchemyDurableJobRepository

from .ports import DeploymentConflict, DeploymentUnavailable
from .service import DeploymentService


class DeploymentProcessor:
    """Publish one reviewed queued deployment against exact persisted lineage."""

    def __init__(
        self,
        jobs: SqlAlchemyDurableJobRepository,
        deployments: object,
        service: DeploymentService,
    ) -> None:
        self.jobs = jobs
        self.deployments = deployments
        self.service = service

    async def process(self, job_id: uuid.UUID) -> dict[str, object]:
        job = await self.jobs.mark_running(job_id=job_id)
        deployment_id: uuid.UUID | None = None
        try:
            if job.job_type != "deployment.publish":
                raise ValueError("The durable job type is not owned by Deployment.")
            agent_id = uuid.UUID(str(job.payload.get("agent_id", "")))
            deployment_id = uuid.UUID(str(job.payload.get("deployment_id", "")))
            channel_id = uuid.UUID(str(job.payload.get("channel_id", "")))
            build_id = uuid.UUID(str(job.payload.get("build_id", "")))
            eligibility_id = uuid.UUID(str(job.payload.get("eligibility_id", "")))
            bundle_hash = str(job.payload.get("bundle_hash", ""))
            if len(bundle_hash) != 64:
                raise ValueError("The queued deployment build identity is invalid.")
            attempt = await self.deployments.mark_running(
                job.owner_id, deployment_id, job.id
            )
            if (
                attempt.agent_id != agent_id
                or attempt.channel_id != channel_id
                or attempt.build_id != build_id
                or attempt.eligibility_id != eligibility_id
                or attempt.bundle_hash != bundle_hash
            ):
                raise DeploymentConflict(
                    "The queued deployment changed its exact immutable lineage."
                )
            stored = await self.service.execute_deployment(
                job.owner_id,
                agent_id,
                deployment_id,
                expected_channel_id=channel_id,
                expected_build_id=build_id,
                expected_eligibility_id=eligibility_id,
                expected_bundle_hash=bundle_hash,
            )
            result: dict[str, object] = {
                "deployment_id": str(stored.id),
                "runtime_deployment_id": stored.runtime_deployment_id,
                "agent_id": str(agent_id),
                "channel_id": str(channel_id),
                "build_id": str(build_id),
                "status": stored.status,
            }
            if stored.status == "ready":
                await self.jobs.mark_succeeded(job_id=job.id, result=result)
            else:
                await self.jobs.mark_failed(
                    job_id=job.id,
                    error_code=stored.failure_code or "deployment_failed",
                    error_message=stored.failure_message or "The deployment failed.",
                )
            return result
        except Exception as error:
            public_message = _public_failure(error)
            if deployment_id is not None:
                try:
                    await self.deployments.complete(
                        job.owner_id,
                        deployment_id,
                        runtime_deployment_id=None,
                        status="failed",
                        failure_code="deployment_failed",
                        failure_message=public_message,
                    )
                except (DeploymentConflict, DeploymentUnavailable):
                    pass
            await self.jobs.mark_failed(
                job_id=job.id,
                error_code="deployment_failed",
                error_message=public_message,
            )
            raise


def _public_failure(error: Exception) -> str:
    if isinstance(error, (DeploymentConflict, DeploymentUnavailable, ValueError)):
        message = str(error).strip()
        if message:
            return message[:500]
    return "The queued deployment failed."


__all__ = ["DeploymentProcessor"]
