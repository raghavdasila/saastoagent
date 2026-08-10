from __future__ import annotations

import uuid
from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError

from corpus.features.agents.domain import AgentLifecycle
from corpus.features.agents.models import Agent
from corpus.persistence import CorpusDatabase

from .domain import AgentDesignRecord, BuildRequestRecord, DesignerInputSnapshot, DesignRevisionRecord
from .models import AgentBuildRequest, AgentDesign, AgentDesignRevision
from .ports import DesignerConflict, DesignerUnavailable


class SqlAlchemyDesignerRepository:
    def __init__(self, database: CorpusDatabase) -> None:
        self.database = database

    async def get(self, organization_id, agent_id):
        async with self.database.session() as session:
            design = await session.scalar(select(AgentDesign).where(
                AgentDesign.organization_id == organization_id,
                AgentDesign.agent_id == agent_id,
            ))
            if design is None:
                raise DesignerUnavailable("No Agent design exists for the selected Agent.")
            revisions = tuple((await session.scalars(
                select(AgentDesignRevision)
                .where(AgentDesignRevision.design_id == design.id)
                .order_by(AgentDesignRevision.revision)
            )).all())
            build = await session.scalar(select(AgentBuildRequest).where(
                AgentBuildRequest.organization_id == organization_id,
                AgentBuildRequest.agent_id == agent_id,
            ).order_by(AgentBuildRequest.created_at.desc()))
        return _design_record(design), tuple(_revision_record(item) for item in revisions), _build_record(build) if build else None

    async def propose(self, organization_id, snapshot, *, content, input_fingerprint):
        now = datetime.now(UTC)
        async with self.database.session() as session:
            async with session.begin():
                agent = await _locked_agent(session, organization_id, snapshot.agent_id)
                if agent.current_version != snapshot.agent_version:
                    raise DesignerConflict("The Agent changed before the design proposal was saved.")
                design = await session.scalar(select(AgentDesign).where(
                    AgentDesign.organization_id == organization_id,
                    AgentDesign.agent_id == snapshot.agent_id,
                ).with_for_update())
                revision_id = uuid.uuid4()
                if design is None:
                    design = AgentDesign(
                        organization_id=organization_id,
                        agent_id=snapshot.agent_id,
                        current_revision_id=revision_id,
                        current_revision=1,
                        accepted_revision_id=None,
                        created_at=now,
                        updated_at=now,
                    )
                    session.add(design)
                    await session.flush()
                    number = 1
                else:
                    number = design.current_revision + 1
                    design.current_revision_id = revision_id
                    design.current_revision = number
                    design.updated_at = now
                revision = AgentDesignRevision(
                    id=revision_id,
                    design_id=design.id,
                    revision=number,
                    agent_version=snapshot.agent_version,
                    input_fingerprint=input_fingerprint,
                    content=content,
                    source_inputs=[_source_json(item) for item in snapshot.sources],
                    created_at=now,
                )
                session.add(revision)
                await session.flush()
        return _design_record(design), _revision_record(revision)

    async def customize(self, organization_id, agent_id, *, expected_revision_id, content):
        now = datetime.now(UTC)
        async with self.database.session() as session:
            async with session.begin():
                await _locked_agent(session, organization_id, agent_id)
                design = await _locked_design(session, organization_id, agent_id)
                if design.current_revision_id != expected_revision_id:
                    raise DesignerConflict("The design changed after this edit was opened.")
                prior = await session.get(AgentDesignRevision, expected_revision_id)
                if prior is None or prior.design_id != design.id:
                    raise DesignerUnavailable("The selected design revision is unavailable.")
                revision = AgentDesignRevision(
                    design_id=design.id,
                    revision=design.current_revision + 1,
                    agent_version=prior.agent_version,
                    input_fingerprint=prior.input_fingerprint,
                    content=content,
                    source_inputs=prior.source_inputs,
                    created_at=now,
                )
                session.add(revision)
                await session.flush()
                design.current_revision_id = revision.id
                design.current_revision = revision.revision
                design.updated_at = now
                await session.flush()
        return _design_record(design), _revision_record(revision)

    async def accept(self, organization_id, agent_id, *, expected_revision_id):
        async with self.database.session() as session:
            async with session.begin():
                await _locked_agent(session, organization_id, agent_id)
                design = await _locked_design(session, organization_id, agent_id)
                if design.current_revision_id != expected_revision_id:
                    raise DesignerConflict("The proposed design changed before review acceptance.")
                design.accepted_revision_id = expected_revision_id
                design.updated_at = datetime.now(UTC)
                await session.flush()
        return _design_record(design)

    async def request_build(self, organization_id, agent_id, *, accepted_revision_id):
        now = datetime.now(UTC)
        try:
            async with self.database.session() as session:
                async with session.begin():
                    await _locked_agent(session, organization_id, agent_id)
                    design = await _locked_design(session, organization_id, agent_id)
                    if design.accepted_revision_id != accepted_revision_id:
                        raise DesignerConflict("A build can be requested only for the exact accepted design revision.")
                    request = AgentBuildRequest(
                        organization_id=organization_id,
                        agent_id=agent_id,
                        design_revision_id=accepted_revision_id,
                        status="pending",
                        created_at=now,
                    )
                    session.add(request)
                    await session.flush()
        except IntegrityError as error:
            raise DesignerConflict("This accepted design already has a build request.") from error
        return _build_record(request)


async def _locked_agent(session, organization_id, agent_id):
    agent = await session.scalar(select(Agent).where(
        Agent.organization_id == organization_id,
        Agent.id == agent_id,
        Agent.lifecycle == AgentLifecycle.ACTIVE,
    ).with_for_update())
    if agent is None:
        raise DesignerUnavailable("The selected Agent is unavailable.")
    return agent


async def _locked_design(session, organization_id, agent_id):
    design = await session.scalar(select(AgentDesign).where(
        AgentDesign.organization_id == organization_id,
        AgentDesign.agent_id == agent_id,
    ).with_for_update())
    if design is None:
        raise DesignerUnavailable("No Agent design exists for the selected Agent.")
    return design


def _design_record(value):
    return AgentDesignRecord(value.id, value.organization_id, value.agent_id, value.current_revision_id, value.current_revision, value.accepted_revision_id, value.created_at, value.updated_at)


def _revision_record(value):
    return DesignRevisionRecord(value.id, value.design_id, value.revision, value.agent_version, value.input_fingerprint, dict(value.content), tuple(dict(item) for item in value.source_inputs), value.created_at)


def _build_record(value):
    return BuildRequestRecord(value.id, value.organization_id, value.agent_id, value.design_revision_id, value.status, value.created_at)


def _source_json(value):
    return {
        "source_id": value.source_id,
        "source_revision_id": value.source_revision_id,
        "curation_id": value.curation_id,
        "inventory_fingerprint": value.inventory_fingerprint,
        "included_operation_ids": list(value.included_operation_ids),
        "semantic_groups": [
            {
                "label": group.label,
                "operation_ids": list(group.operation_ids),
            }
            for group in value.semantic_groups
        ],
    }
