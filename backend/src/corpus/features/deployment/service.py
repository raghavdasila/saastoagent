from __future__ import annotations

import asyncio
import hashlib
import json

from corpus.jobs import DurableJobEnqueueError, DurableJobPort
from corpus.integrations.agent_delivery import DeployableBundleSpec, NeutralAgentDeliveryAdapter

from .ports import DeploymentConflict, DeploymentUnavailable


class DeploymentService:
    def __init__(
        self, repository, channels, builds, eligibility,
        delivery: NeutralAgentDeliveryAdapter, bindings,
        jobs: DurableJobPort | None = None,
    ) -> None:
        self.repository = repository
        self.channels = channels
        self.builds = builds
        self.eligibility = eligibility
        self.delivery = delivery
        self.bindings = bindings
        self.jobs = jobs

    async def _preflight(self, organization_id, agent_id, *, channel_id, build_id):
        channel = await self.channels.repository.get(organization_id, agent_id, channel_id)
        if channel.status != "ready" or not channel.runtime_channel_id:
            raise DeploymentConflict("The selected channel is not ready.")
        build = await self.builds.require_running(organization_id, agent_id, build_id)
        eligible = await self.eligibility.require_eligible(
            organization_id, agent_id, build_id
        )
        if build.runtime_build_hash != eligible.runtime_build_hash:
            raise DeploymentConflict("Eligibility does not match the exact selected build.")
        if build.navgraph_hash is None or not build.compiled_navgraph or not build.frontend_contract:
            raise DeploymentConflict("The selected build has no immutable RouteDeck application contract.")
        surface_contract_hash = hashlib.sha256(
            json.dumps(build.frontend_contract, sort_keys=True, separators=(",", ":")).encode("utf-8")
        ).hexdigest()
        return channel, build, eligible, surface_contract_hash

    async def queue_deploy(
        self, organization_id, agent_id, *, channel_id, build_id,
        retry_of_deployment_id=None,
    ):
        if self.jobs is None:
            raise DeploymentUnavailable("The deployment queue is unavailable.")
        channel, build, eligible, _surface_contract_hash = await self._preflight(
            organization_id, agent_id, channel_id=channel_id, build_id=build_id
        )
        record = await self.repository.reserve(
            organization_id, agent_id, channel_id=channel.id, build_id=build.id,
            eligibility_id=eligible.eligibility_id,
            bundle_hash=build.runtime_build_hash,
            retry_of_deployment_id=retry_of_deployment_id,
        )
        try:
            job = await self.jobs.enqueue(
                owner_id=organization_id,
                job_type="deployment.publish",
                payload={
                    "agent_id": str(agent_id),
                    "deployment_id": str(record.id),
                    "channel_id": str(channel.id),
                    "build_id": str(build.id),
                    "eligibility_id": str(eligible.eligibility_id),
                    "bundle_hash": build.runtime_build_hash,
                },
                max_attempts=1,
            )
            return await self.repository.link_job(
                organization_id, record.id, job.id
            )
        except Exception as error:
            await self.repository.complete(
                organization_id, record.id, runtime_deployment_id=None,
                status="failed", failure_code="queue_enqueue_failed",
                failure_message="The deployment could not be queued.",
            )
            if isinstance(error, DurableJobEnqueueError):
                raise DeploymentUnavailable(
                    "The deployment could not be queued."
                ) from error
            raise

    async def execute_deployment(
        self, organization_id, agent_id, deployment_id, *,
        expected_channel_id, expected_build_id, expected_eligibility_id,
        expected_bundle_hash,
    ):
        record = await self.repository.get(
            organization_id, agent_id, deployment_id
        )
        if (
            record.channel_id != expected_channel_id
            or record.build_id != expected_build_id
            or record.eligibility_id != expected_eligibility_id
            or record.bundle_hash != expected_bundle_hash
            or record.status != "running"
        ):
            raise DeploymentConflict(
                "The queued deployment changed its exact immutable lineage."
            )
        channel, build, eligible, surface_contract_hash = await self._preflight(
            organization_id,
            agent_id,
            channel_id=record.channel_id,
            build_id=record.build_id,
        )
        if (
            eligible.eligibility_id != record.eligibility_id
            or build.runtime_build_hash != record.bundle_hash
        ):
            raise DeploymentConflict(
                "The queued deployment eligibility or build identity changed."
            )
        self.bindings.bind(build)
        spec = DeployableBundleSpec(
            bundle_id=str(record.id), name=channel.name, version=str(build.agent_version),
            content_hash=build.runtime_build_hash,
            routedeck_app_hash=build.navgraph_hash,
            surface_contract_hash=surface_contract_hash,
            eligibility_hash=eligible.eligibility_hash,
            runtime_kind="corpus-agent-execution-v1",
            runtime_config={
                "runtime_build_hash": build.runtime_build_hash,
                "organization_id": str(organization_id),
                "agent_id": str(agent_id),
                "build_id": str(build.id),
                "model": build.model or "pinned",
                "navgraph_hash": build.navgraph_hash,
                "surface_contract_hash": surface_contract_hash,
            },
        )
        try:
            result = await asyncio.to_thread(
                self.delivery.request_deployment, channel.runtime_channel_id, spec
            )
        except Exception as error:
            await self.repository.complete(
                organization_id, record.id, runtime_deployment_id=None,
                status="failed", failure_code=type(error).__name__,
                failure_message="Deployment verification failed.",
            )
            raise DeploymentUnavailable("Deployment verification failed.") from error
        saved = await self.repository.complete(
            organization_id, record.id,
            runtime_deployment_id=result.deployment_id,
            status=result.status,
            failure_code=result.failure_code,
            failure_message=result.failure_message,
        )
        if result.status == "ready":
            await self.channels.repository.set_active(organization_id, channel.id, saved.id)
        return saved

    async def queue_current(self, organization_id, agent_id):
        channels = tuple(
            value
            for value in await self.channels.list(organization_id, agent_id)
            if value.status == "ready" and value.runtime_lifecycle == "running"
        )
        builds = tuple(
            value
            for value in (await self.builds.list(organization_id, agent_id)).builds
            if value.status == "ready"
        )
        if len(channels) != 1 or len(builds) != 1:
            raise DeploymentConflict(
                "Deployment requires one exact ready channel and one exact ready build."
            )
        return await self.queue_deploy(
            organization_id,
            agent_id,
            channel_id=channels[0].id,
            build_id=builds[0].id,
        )

    async def retry_deployment(
        self, organization_id, agent_id, deployment_id,
    ):
        failed = await self.repository.get(
            organization_id, agent_id, deployment_id
        )
        if failed.status != "failed":
            raise DeploymentConflict(
                "Only an exact failed deployment can be retried."
            )
        return await self.queue_deploy(
            organization_id,
            agent_id,
            channel_id=failed.channel_id,
            build_id=failed.build_id,
            retry_of_deployment_id=failed.id,
        )

    async def rollback(self, organization_id, agent_id, *, channel_id, deployment_id):
        channel = await self.channels.repository.get(organization_id, agent_id, channel_id)
        target = await self.repository.get(organization_id, agent_id, deployment_id)
        if target.channel_id != channel.id or target.status != "ready" or not target.runtime_deployment_id:
            raise DeploymentConflict("Rollback requires a ready deployment from this channel.")
        if not channel.runtime_channel_id:
            raise DeploymentConflict("The selected channel is not ready.")
        await asyncio.to_thread(
            self.delivery.rollback, channel.runtime_channel_id, target.runtime_deployment_id
        )
        await self.channels.repository.set_active(organization_id, channel.id, target.id)
        return target

    async def rollback_current(self, organization_id, agent_id):
        channels = tuple(
            value
            for value in await self.channels.list(organization_id, agent_id)
            if value.status == "ready"
        )
        if len(channels) != 1:
            raise DeploymentConflict(
                "Rollback requires one exact ready hosted Web channel."
            )
        channel = channels[0]
        candidates = tuple(
            value
            for value in await self.list(organization_id, agent_id)
            if value.channel_id == channel.id
            and value.status == "ready"
            and value.id != channel.active_deployment_id
        )
        if len(candidates) != 1:
            raise DeploymentConflict(
                "Rollback requires one exact earlier ready deployment."
            )
        return await self.rollback(
            organization_id,
            agent_id,
            channel_id=channel.id,
            deployment_id=candidates[0].id,
        )

    async def list(self, organization_id, agent_id):
        return await self.repository.list(organization_id, agent_id)

    async def prepare_public(self, channel):
        if channel.active_deployment_id is None:
            raise DeploymentConflict("This public Agent has no active deployment.")
        deployment = await self.repository.get(
            channel.organization_id, channel.agent_id, channel.active_deployment_id
        )
        if deployment.status != "ready" or deployment.channel_id != channel.id:
            raise DeploymentConflict("The active deployment is unavailable.")
        build = await self.builds.require_immutable_built(
            channel.organization_id, channel.agent_id, deployment.build_id
        )
        if build.runtime_build_hash != deployment.bundle_hash:
            raise DeploymentConflict("The active deployment build identity is inconsistent.")
        self.bindings.bind(build)
        return deployment


__all__ = ["DeploymentService"]
