from __future__ import annotations

import uuid

from corpus.features.agents.service import AgentService

from .domain import BuilderInputSnapshot
from .ports import BuilderConflict, BuilderInputGateway, BuilderRepository, BuilderRuntimeGateway, BuilderUnavailable
from .schemas import AgentBuildCollectionView, AgentBuildView, BuilderSourceBindingView


class BuilderService:
    def __init__(self, repository: BuilderRepository, inputs: BuilderInputGateway, runtime: BuilderRuntimeGateway, agents: AgentService) -> None:
        self.repository, self.inputs, self.runtime, self.agents = repository, inputs, runtime, agents

    async def list(self, organization_id: uuid.UUID, agent_id: uuid.UUID) -> AgentBuildCollectionView:
        await self.agents.get(organization_id, agent_id)
        return AgentBuildCollectionView(agent_id=agent_id, builds=tuple(_view(item) for item in await self.repository.get_for_agent(organization_id, agent_id)))

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
        return _view(await self.repository.set_runtime_lifecycle(
            organization_id, agent_id, build_id, lifecycle="running"
        ))

    async def stop(self, organization_id: uuid.UUID, agent_id: uuid.UUID, *, build_id: uuid.UUID) -> AgentBuildView:
        value = await self.repository.get(organization_id, agent_id, build_id)
        if value.status != "ready" or value.runtime_build_hash is None:
            raise BuilderUnavailable("The selected Agent build is not ready.")
        if value.runtime_lifecycle == "removed":
            raise BuilderConflict("The selected draft Agent runtime was removed.")
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
        if value.runtime_lifecycle == "running":
            raise BuilderConflict("Stop the draft Agent runtime before removing it.")
        return _view(await self.repository.set_runtime_lifecycle(
            organization_id, agent_id, build_id, lifecycle="removed"
        ))

    async def assemble(self, organization_id: uuid.UUID, agent_id: uuid.UUID, *, build_request_id: uuid.UUID) -> AgentBuildView:
        record = await self.repository.begin(organization_id, agent_id, build_request_id=build_request_id)
        if record.status == "ready":
            return _view(record)
        try:
            snapshot = await self.inputs.snapshot(organization_id, record)
            artifact = await self.runtime.assemble(snapshot)
            if set(artifact.allowed_operation_ids) != {
                operation for binding in snapshot.source_bindings for operation in binding.included_operation_ids
            }:
                raise BuilderConflict("The runtime build did not preserve the exact accepted operation selection.")
            await self.agents.record_build_lineage(
                organization_id, agent_id, build_id=record.id,
                expected_agent_version=snapshot.agent_version,
                source_references=tuple((item.source_id, item.source_revision_id) for item in snapshot.source_bindings),
            )
            bindings = tuple(_binding_json(item) for item in snapshot.source_bindings)
            return _view(await self.repository.complete(organization_id, record.id, artifact=artifact, source_bindings=bindings))
        except Exception as error:
            if isinstance(error, (BuilderUnavailable, BuilderConflict)):
                code, message = type(error).__name__.lower(), str(error)
            else:
                code, message = "builder_dependency_failed", "The Agent build could not be assembled."
            await self.repository.fail(organization_id, record.id, code=code, message=message)
            if isinstance(error, (BuilderUnavailable, BuilderConflict)):
                raise
            raise BuilderUnavailable(message) from error

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
        allowed_operation_ids=value.allowed_operation_ids, failure_code=value.failure_code,
        navgraph_hash=value.navgraph_hash, compiled_navgraph=value.compiled_navgraph,
        frontend_contract=value.frontend_contract,
        failure_message=value.failure_message, created_at=value.created_at, updated_at=value.updated_at,
        attempt_number=value.attempt_number,
    )


__all__ = ["BuilderService"]
