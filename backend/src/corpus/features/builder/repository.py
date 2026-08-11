from __future__ import annotations

import uuid
from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError

from corpus.features.designer.models import AgentBuildRequest, AgentDesign, AgentDesignRevision
from corpus.persistence import CorpusDatabase

from .domain import BuilderRecord, RuntimeBuildArtifact
from .models import AgentRunnableBuild
from .ports import BuilderConflict, BuilderUnavailable


class SqlAlchemyBuilderRepository:
    def __init__(self, database: CorpusDatabase) -> None:
        self.database = database

    async def begin(self, organization_id, agent_id, *, build_request_id):
        now = datetime.now(UTC)
        try:
            async with self.database.session() as session:
                async with session.begin():
                    request = await session.scalar(select(AgentBuildRequest).where(
                        AgentBuildRequest.id == build_request_id,
                        AgentBuildRequest.organization_id == organization_id,
                        AgentBuildRequest.agent_id == agent_id,
                    ).with_for_update())
                    if request is None:
                        raise BuilderUnavailable("The selected build request is unavailable.")
                    design = await session.scalar(select(AgentDesign).where(
                        AgentDesign.organization_id == organization_id,
                        AgentDesign.agent_id == agent_id,
                        AgentDesign.accepted_revision_id == request.design_revision_id,
                    ))
                    revision = await session.get(AgentDesignRevision, request.design_revision_id)
                    if design is None or revision is None or revision.design_id != design.id:
                        raise BuilderConflict("The build request no longer names the exact accepted design.")
                    existing = await session.scalar(select(AgentRunnableBuild).where(
                        AgentRunnableBuild.organization_id == organization_id,
                        AgentRunnableBuild.build_request_id == build_request_id,
                    ).order_by(AgentRunnableBuild.attempt_number.desc()))
                    if existing is not None and existing.status == "ready":
                        return _record(existing)
                    if existing is not None and existing.status == "assembling":
                        raise BuilderConflict("This build request already has an active build attempt.")
                    attempt_number = 1 if existing is None else existing.attempt_number + 1
                    value = AgentRunnableBuild(
                        id=uuid.uuid4(), organization_id=organization_id, agent_id=agent_id,
                        build_request_id=build_request_id, design_revision_id=request.design_revision_id,
                        agent_version=revision.agent_version, attempt_number=attempt_number,
                        status="assembling", runtime_lifecycle="stopped", runtime_build_hash=None,
                        model=None, model_digest=None, source_bindings=[], allowed_operation_ids=[],
                        navgraph_hash=None, compiled_navgraph={}, frontend_contract={},
                        failure_code=None, failure_message=None, created_at=now, updated_at=now,
                    )
                    request.status = "assembling"
                    session.add(value)
                    await session.flush()
                    return _record(value)
        except IntegrityError as error:
            raise BuilderConflict("This build request already has an active build attempt.") from error

    async def complete(self, organization_id, build_id, *, artifact, source_bindings):
        async with self.database.session() as session:
            async with session.begin():
                value = await _locked(session, organization_id, build_id)
                if value.status != "assembling":
                    raise BuilderConflict("The build attempt is no longer assembling.")
                value.status = "ready"
                value.runtime_lifecycle = "stopped"
                value.runtime_build_hash = artifact.runtime_build_hash
                value.model = artifact.model
                value.model_digest = artifact.model_digest
                value.source_bindings = list(source_bindings)
                value.allowed_operation_ids = list(artifact.allowed_operation_ids)
                value.navgraph_hash = artifact.navgraph_hash
                value.compiled_navgraph = artifact.compiled_navgraph
                value.frontend_contract = artifact.frontend_contract
                value.updated_at = datetime.now(UTC)
                request = await session.get(AgentBuildRequest, value.build_request_id)
                if request is None:
                    raise BuilderUnavailable("The selected build request is unavailable.")
                request.status = "ready"
                await session.flush()
                return _record(value)

    async def fail(self, organization_id, build_id, *, code, message):
        async with self.database.session() as session:
            async with session.begin():
                value = await _locked(session, organization_id, build_id)
                if value.status == "ready":
                    raise BuilderConflict("A ready build cannot be replaced by a failure.")
                value.status = "failed"
                value.failure_code = code[:80]
                value.failure_message = message[:500]
                value.updated_at = datetime.now(UTC)
                request = await session.get(AgentBuildRequest, value.build_request_id)
                if request is not None:
                    request.status = "failed"
                await session.flush()
                return _record(value)

    async def get_for_agent(self, organization_id, agent_id):
        async with self.database.session() as session:
            values = tuple((await session.scalars(select(AgentRunnableBuild).where(
                AgentRunnableBuild.organization_id == organization_id,
                AgentRunnableBuild.agent_id == agent_id,
            ).order_by(AgentRunnableBuild.created_at.desc()))).all())
        return tuple(_record(value) for value in values)

    async def get(self, organization_id, agent_id, build_id):
        async with self.database.session() as session:
            value = await session.scalar(select(AgentRunnableBuild).where(
                AgentRunnableBuild.organization_id == organization_id,
                AgentRunnableBuild.agent_id == agent_id,
                AgentRunnableBuild.id == build_id,
            ))
        if value is None:
            raise BuilderUnavailable("The selected Agent build is unavailable.")
        return _record(value)

    async def set_runtime_lifecycle(self, organization_id, agent_id, build_id, *, lifecycle):
        if lifecycle not in {"stopped", "running", "paused", "removed"}:
            raise BuilderConflict("The requested draft runtime lifecycle is invalid.")
        async with self.database.session() as session:
            async with session.begin():
                value = await _locked(session, organization_id, build_id)
                if value.agent_id != agent_id:
                    raise BuilderUnavailable("The selected Agent build is unavailable.")
                if value.status != "ready" or value.runtime_build_hash is None:
                    raise BuilderUnavailable("The selected Agent build is not assembled.")
                if value.runtime_lifecycle == "removed" and lifecycle != "removed":
                    raise BuilderConflict(
                        "A removed draft runtime cannot be started or stopped."
                    )
                if lifecycle == "removed" and value.runtime_lifecycle != "stopped":
                    raise BuilderConflict(
                        "Only a stopped draft Agent runtime can be removed."
                    )
                value.runtime_lifecycle = lifecycle
                value.updated_at = datetime.now(UTC)
                await session.flush()
                return _record(value)


async def _locked(session, organization_id, build_id):
    value = await session.scalar(select(AgentRunnableBuild).where(
        AgentRunnableBuild.organization_id == organization_id,
        AgentRunnableBuild.id == build_id,
    ).with_for_update())
    if value is None:
        raise BuilderUnavailable("The selected Agent build is unavailable.")
    return value


def _record(value):
    return BuilderRecord(
        value.id, value.organization_id, value.agent_id, value.build_request_id,
        value.design_revision_id, value.agent_version, value.status, value.runtime_lifecycle,
        value.runtime_build_hash, value.model, value.model_digest,
        tuple(dict(item) for item in value.source_bindings), tuple(value.allowed_operation_ids),
        value.navgraph_hash, dict(value.compiled_navgraph), dict(value.frontend_contract),
        value.failure_code, value.failure_message, value.created_at, value.updated_at,
        value.attempt_number,
    )


__all__ = ["SqlAlchemyBuilderRepository"]
