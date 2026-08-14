from __future__ import annotations

import uuid

from corpus.jobs import DurableJobEnqueueError, DurableJobPort

from .domain import BuilderInputSnapshot
from .ports import (
    BuilderConflict,
    BuilderAgentGateway,
    BuilderInputGateway,
    BuilderRepository,
    BuilderRuntimeGateway,
    BuilderUnavailable,
    InitialEvaluationSetScheduler,
)
from .schemas import AgentBuildCollectionView, AgentBuildView, BuilderSourceBindingView


class BuilderService:
    def __init__(self, repository: BuilderRepository, inputs: BuilderInputGateway, runtime: BuilderRuntimeGateway, agents: BuilderAgentGateway) -> None:
        self.repository, self.inputs, self.runtime, self.agents = repository, inputs, runtime, agents
        self._initial_evaluations: InitialEvaluationSetScheduler | None = None
        self._assembly_jobs: DurableJobPort | None = None

    def bind_assembly_jobs(self, jobs: DurableJobPort) -> None:
        if self._assembly_jobs is not None:
            raise RuntimeError("The Builder assembly queue is already bound.")
        self._assembly_jobs = jobs

    def bind_initial_evaluation_scheduler(
        self, scheduler: InitialEvaluationSetScheduler
    ) -> None:
        if self._initial_evaluations is not None:
            raise RuntimeError("The initial evaluation scheduler is already bound.")
        self._initial_evaluations = scheduler

    async def list(self, organization_id: uuid.UUID, agent_id: uuid.UUID) -> AgentBuildCollectionView:
        await self.agents.get(organization_id, agent_id)
        return AgentBuildCollectionView(agent_id=agent_id, builds=tuple(_view(item) for item in await self.repository.get_for_agent(organization_id, agent_id)))

    async def current_build_id(
        self,
        organization_id: uuid.UUID,
        agent_id: uuid.UUID,
    ) -> uuid.UUID:
        build_request_id = await self.inputs.current_build_request_id(
            organization_id,
            agent_id,
        )
        values = tuple(
            value
            for value in await self.repository.get_for_agent(
                organization_id,
                agent_id,
            )
            if value.build_request_id == build_request_id
        )
        if not values:
            raise BuilderUnavailable(
                "The selected Agent does not have one exact current build."
            )
        latest_attempt = max(value.attempt_number for value in values)
        current = tuple(
            value for value in values if value.attempt_number == latest_attempt
        )
        if len(current) != 1:
            raise BuilderUnavailable(
                "The selected Agent does not have one exact current build."
            )
        return current[0].id

    async def require_immutable_built(self, organization_id: uuid.UUID, agent_id: uuid.UUID, build_id: uuid.UUID):
        value = await self.repository.get(organization_id, agent_id, build_id)
        if value.status != "ready" or value.runtime_build_hash is None:
            raise BuilderUnavailable("The selected Agent build is not ready.")
        try:
            await self.runtime.validate_immutable_build(value.runtime_build_hash)
        except Exception as error:
            if isinstance(error, BuilderUnavailable):
                raise
            raise BuilderUnavailable("The exact immutable Agent build is unavailable.") from error
        return value

    async def require_running(self, organization_id: uuid.UUID, agent_id: uuid.UUID, build_id: uuid.UUID):
        value = await self.require_immutable_built(organization_id, agent_id, build_id)
        if value.runtime_lifecycle != "running":
            raise BuilderUnavailable("Run the exact draft Agent build before using Sandbox or Evaluation.")
        return value

    async def run(self, organization_id: uuid.UUID, agent_id: uuid.UUID, *, build_id: uuid.UUID) -> AgentBuildView:
        value = await self.require_immutable_built(organization_id, agent_id, build_id)
        if value.runtime_lifecycle == "removed":
            raise BuilderConflict("The selected draft Agent runtime was removed.")
        if value.runtime_lifecycle == "running":
            raise BuilderConflict("The selected draft Agent runtime is already running.")
        if value.runtime_lifecycle not in {"stopped", "paused"}:
            raise BuilderConflict("The selected draft Agent runtime cannot be started or resumed from its current state.")
        return _view(await self.repository.set_runtime_lifecycle(
            organization_id, agent_id, build_id, lifecycle="running"
        ))

    async def pause(self, organization_id: uuid.UUID, agent_id: uuid.UUID, *, build_id: uuid.UUID) -> AgentBuildView:
        value = await self.require_immutable_built(organization_id, agent_id, build_id)
        if value.runtime_lifecycle != "running":
            raise BuilderConflict("Only a running draft Agent runtime can be paused.")
        return _view(await self.repository.set_runtime_lifecycle(
            organization_id, agent_id, build_id, lifecycle="paused"
        ))

    async def stop(self, organization_id: uuid.UUID, agent_id: uuid.UUID, *, build_id: uuid.UUID) -> AgentBuildView:
        value = await self.repository.get(organization_id, agent_id, build_id)
        if value.status != "ready" or value.runtime_build_hash is None:
            raise BuilderUnavailable("The selected Agent build is not ready.")
        if value.runtime_lifecycle == "removed":
            raise BuilderConflict("The selected draft Agent runtime was removed.")
        if value.runtime_lifecycle not in {"running", "paused"}:
            raise BuilderConflict("Only a running or paused draft Agent runtime can be stopped.")
        return _view(await self.repository.set_runtime_lifecycle(
            organization_id, agent_id, build_id, lifecycle="stopped"
        ))

    async def remove_runtime(
        self,
        organization_id: uuid.UUID,
        agent_id: uuid.UUID,
        *,
        build_id: uuid.UUID,
    ) -> AgentBuildView:
        value = await self.repository.get(organization_id, agent_id, build_id)
        if value.status != "ready" or value.runtime_build_hash is None:
            raise BuilderUnavailable("The selected Agent build is not ready.")
        if value.runtime_lifecycle != "stopped":
            raise BuilderConflict("Only a stopped draft Agent runtime can be removed.")
        return _view(await self.repository.set_runtime_lifecycle(
            organization_id, agent_id, build_id, lifecycle="removed"
        ))

    async def assemble(self, organization_id: uuid.UUID, agent_id: uuid.UUID, *, build_request_id: uuid.UUID) -> AgentBuildView:
        if self._assembly_jobs is None:
            raise BuilderUnavailable("The Agent build queue is unavailable.")
        record = await self.repository.begin(organization_id, agent_id, build_request_id=build_request_id)
        if record.status == "ready":
            return _view(record)
        try:
            job = await self._assembly_jobs.enqueue(
                owner_id=organization_id,
                job_type="builder.assemble",
                payload={
                    "agent_id": str(agent_id),
                    "build_id": str(record.id),
                    "build_request_id": str(record.build_request_id),
                    "design_revision_id": str(record.design_revision_id),
                    "attempt_number": record.attempt_number,
                },
                max_attempts=1,
            )
            queued = await self.repository.link_job(
                organization_id, record.id, job.id
            )
        except Exception as error:
            await self.repository.fail(
                organization_id,
                record.id,
                code="builder_queue_failed",
                message="The Agent build could not be queued.",
            )
            if isinstance(error, DurableJobEnqueueError):
                raise BuilderUnavailable("The Agent build could not be queued.") from error
            raise
        return _view(queued)

    async def execute_assembly(
        self,
        organization_id: uuid.UUID,
        agent_id: uuid.UUID,
        *,
        build_id: uuid.UUID,
        expected_build_request_id: uuid.UUID,
        expected_design_revision_id: uuid.UUID,
        expected_attempt_number: int,
    ) -> AgentBuildView:
        record = await self.repository.get(organization_id, agent_id, build_id)
        if (
            record.status != "running"
            or record.build_request_id != expected_build_request_id
            or record.design_revision_id != expected_design_revision_id
            or record.attempt_number != expected_attempt_number
        ):
            raise BuilderConflict("The queued build attempt changed its exact immutable lineage.")
        snapshot = await self.inputs.snapshot(organization_id, record)
        artifact = await self.runtime.assemble(snapshot)
        if set(artifact.allowed_operation_ids) != {
            operation for binding in snapshot.source_bindings for operation in binding.included_operation_ids
        }:
            raise BuilderConflict("The runtime build did not preserve the exact accepted operation selection.")
        await self.agents.record_build_lineage(
            organization_id,
            agent_id,
            build_id=record.id,
            expected_agent_version=snapshot.agent_version,
            source_references=tuple(
                (item.source_id, item.source_revision_id)
                for item in snapshot.source_bindings
            ),
        )
        completed = await self.repository.complete(
            organization_id,
            record.id,
            artifact=artifact,
            source_bindings=tuple(_binding_json(item) for item in snapshot.source_bindings),
        )
        if self._initial_evaluations is None:
            raise BuilderUnavailable(
                "Automatic evaluation-set generation is unavailable for this build."
            )
        await self._initial_evaluations.schedule_initial_set(
            organization_id, agent_id, build_id=completed.id
        )
        return _view(completed)

    async def assemble_current(
        self,
        organization_id: uuid.UUID,
        agent_id: uuid.UUID,
    ) -> AgentBuildView:
        build_request_id = await self.inputs.current_build_request_id(
            organization_id,
            agent_id,
        )
        return await self.assemble(
            organization_id,
            agent_id,
            build_request_id=build_request_id,
        )


def _binding_json(value):
    return {
        "source_id": value.source_id, "source_revision_id": value.source_revision_id,
        "curation_id": value.curation_id, "inventory_fingerprint": value.inventory_fingerprint,
        "included_operation_ids": list(value.included_operation_ids), "artifact_dir": str(value.artifact_dir),
        "document_path": str(value.document_path), "document_hash": value.document_hash,
        "profile_id": value.profile_id, "base_url": value.base_url,
        "authentication_method": value.authentication_method, "credential_name": value.credential_name,
        "credential_reference_id": str(value.credential_reference_id) if value.credential_reference_id else None,
        "credential_version": value.credential_version,
    }


def _view(value):
    return AgentBuildView(
        id=value.id, agent_id=value.agent_id, build_request_id=value.build_request_id,
        design_revision_id=value.design_revision_id, agent_version=value.agent_version,
        status=value.status, runtime_lifecycle=value.runtime_lifecycle, runtime_build_hash=value.runtime_build_hash, model=value.model,
        model_digest=value.model_digest,
        source_bindings=tuple(BuilderSourceBindingView(
            source_id=str(item["source_id"]), source_revision_id=str(item["source_revision_id"]),
            curation_id=str(item["curation_id"]), inventory_fingerprint=str(item["inventory_fingerprint"]),
            included_operation_ids=tuple(map(str, item["included_operation_ids"])), profile_id=str(item["profile_id"]),
            credential_reference_id=(uuid.UUID(str(item["credential_reference_id"])) if item.get("credential_reference_id") else None),
            credential_version=(int(item["credential_version"]) if item.get("credential_version") is not None else None),
        ) for item in value.source_bindings),
        allowed_operation_ids=value.allowed_operation_ids, job_id=value.job_id,
        failure_code=value.failure_code,
        navgraph_hash=value.navgraph_hash, compiled_navgraph=value.compiled_navgraph,
        frontend_contract=value.frontend_contract,
        failure_message=value.failure_message, created_at=value.created_at, updated_at=value.updated_at,
        attempt_number=value.attempt_number,
    )


__all__ = ["BuilderService"]
