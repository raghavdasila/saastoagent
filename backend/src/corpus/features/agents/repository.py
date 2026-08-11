from __future__ import annotations

import uuid
from datetime import UTC, datetime

from sqlalchemy import and_, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from corpus.persistence import CorpusDatabase

from .domain import (
    AgentBuildLineageRecord,
    AgentBuildSourceReferenceRecord,
    AgentDependencySnapshot,
    AgentLifecycle,
    AgentRecord,
    AgentSourceAttachmentRecord,
)
from .models import (
    Agent,
    AgentBuildLineage,
    AgentBuildSourceReference,
    AgentSourceAttachment,
    AgentVersion,
)
from .ports import (
    AgentNameConflict,
    AgentBuildLineageConflict,
    AgentBuildLineageUnavailable,
    AgentDependencyConflict,
    AgentLifecycleConflict,
    AgentNotFound,
    AgentSourceAttachmentConflict,
    AgentSourceAttachmentUnavailable,
    AgentVersionConflict,
    AttachableSource,
)


class SqlAlchemyAgentRepository:
    def __init__(self, database: CorpusDatabase) -> None:
        self.database = database

    async def list(self, organization_id: uuid.UUID) -> tuple[AgentRecord, ...]:
        async with self.database.session() as session:
            rows = (
                await session.execute(
                    select(Agent, AgentVersion)
                    .join(
                        AgentVersion,
                        and_(
                            AgentVersion.agent_id == Agent.id,
                            AgentVersion.version == Agent.current_version,
                        ),
                    )
                    .where(
                        Agent.organization_id == organization_id,
                        Agent.lifecycle == AgentLifecycle.ACTIVE,
                    )
                    .order_by(Agent.updated_at.desc(), Agent.id)
                )
            ).all()
        return tuple(_record(agent, version) for agent, version in rows)

    async def get(
        self,
        organization_id: uuid.UUID,
        agent_id: uuid.UUID,
    ) -> AgentRecord:
        async with self.database.session() as session:
            row = (
                await session.execute(
                    select(Agent, AgentVersion)
                    .join(
                        AgentVersion,
                        and_(
                            AgentVersion.agent_id == Agent.id,
                            AgentVersion.version == Agent.current_version,
                        ),
                    )
                    .where(
                        Agent.organization_id == organization_id,
                        Agent.id == agent_id,
                        Agent.lifecycle == AgentLifecycle.ACTIVE,
                    )
                )
            ).one_or_none()
        if row is None:
            raise AgentNotFound("The selected agent is unavailable.")
        return _record(*row)

    async def create(
        self,
        organization_id: uuid.UUID,
        *,
        name: str,
        name_key: str,
        description: str,
        instructions: str,
    ) -> AgentRecord:
        now = datetime.now(UTC)
        agent = Agent(
            organization_id=organization_id,
            name=name,
            name_key=name_key,
            lifecycle=AgentLifecycle.ACTIVE,
            current_version=1,
            created_at=now,
            updated_at=now,
        )
        version = AgentVersion(
            agent=agent,
            version=1,
            name=name,
            description=description,
            instructions=instructions,
            created_at=now,
        )
        try:
            async with self.database.session() as session:
                async with session.begin():
                    session.add_all((agent, version))
                    await session.flush()
        except IntegrityError as error:
            raise AgentNameConflict(
                "An active agent with this name already exists."
            ) from error
        return _record(agent, version)

    async def update(
        self,
        organization_id: uuid.UUID,
        agent_id: uuid.UUID,
        *,
        expected_version: int,
        name: str,
        name_key: str,
        description: str,
        instructions: str,
    ) -> AgentRecord:
        now = datetime.now(UTC)
        try:
            async with self.database.session() as session:
                async with session.begin():
                    agent = await session.scalar(
                        select(Agent)
                        .where(
                            Agent.organization_id == organization_id,
                            Agent.id == agent_id,
                            Agent.lifecycle == AgentLifecycle.ACTIVE,
                        )
                        .with_for_update()
                    )
                    if agent is None:
                        raise AgentNotFound("The selected agent is unavailable.")
                    if agent.current_version != expected_version:
                        raise AgentVersionConflict(
                            "The agent changed after this edit was opened. Reload it and try again."
                        )
                    next_version = expected_version + 1
                    version = AgentVersion(
                        agent=agent,
                        version=next_version,
                        name=name,
                        description=description,
                        instructions=instructions,
                        created_at=now,
                    )
                    agent.name = name
                    agent.name_key = name_key
                    agent.current_version = next_version
                    agent.updated_at = now
                    session.add(version)
                    await session.flush()
        except IntegrityError as error:
            raise AgentNameConflict(
                "An active agent with this name already exists."
            ) from error
        return _record(agent, version)

    async def inspect_dependencies(
        self,
        organization_id: uuid.UUID,
        agent_id: uuid.UUID,
    ) -> AgentDependencySnapshot:
        async with self.database.session() as session:
            agent = await session.scalar(
                select(Agent.id).where(
                    Agent.organization_id == organization_id,
                    Agent.id == agent_id,
                    Agent.lifecycle == AgentLifecycle.ACTIVE,
                )
            )
            if agent is None:
                raise AgentNotFound("The selected agent is unavailable.")
            records = await _dependency_records(
                session,
                organization_id,
                agent_id,
            )
            build_lineages = await _build_lineage_records(
                session,
                organization_id,
                agent_id,
            )
        return AgentDependencySnapshot(
            agent_id=agent_id,
            source_attachments=records,
            build_lineages=build_lineages,
        )

    async def archive(
        self,
        organization_id: uuid.UUID,
        agent_id: uuid.UUID,
    ) -> AgentRecord:
        now = datetime.now(UTC)
        async with self.database.session() as session:
            async with session.begin():
                agent = await session.scalar(
                    select(Agent)
                    .where(
                        Agent.organization_id == organization_id,
                        Agent.id == agent_id,
                    )
                    .with_for_update()
                )
                if agent is None:
                    raise AgentNotFound("The selected agent is unavailable.")
                if agent.lifecycle is not AgentLifecycle.ACTIVE:
                    raise AgentLifecycleConflict(
                        "The selected agent is already archived. Reload the active inventory before retrying."
                    )
                version = await session.scalar(
                    select(AgentVersion).where(
                        AgentVersion.agent_id == agent.id,
                        AgentVersion.version == agent.current_version,
                    )
                )
                if version is None:
                    raise AgentLifecycleConflict(
                        "The selected agent configuration is unavailable."
                    )
                agent.lifecycle = AgentLifecycle.ARCHIVED
                agent.updated_at = now
                await session.flush()
        return _record(agent, version)

    async def delete(
        self,
        organization_id: uuid.UUID,
        agent_id: uuid.UUID,
    ) -> None:
        async with self.database.session() as session:
            async with session.begin():
                agent = await session.scalar(
                    select(Agent)
                    .where(
                        Agent.organization_id == organization_id,
                        Agent.id == agent_id,
                    )
                    .with_for_update()
                )
                if agent is None:
                    raise AgentNotFound("The selected agent is unavailable.")
                if agent.lifecycle is not AgentLifecycle.ACTIVE:
                    raise AgentLifecycleConflict(
                        "The selected agent is no longer active. Reload the inventory before retrying."
                    )
                dependencies = await _dependency_records(
                    session,
                    organization_id,
                    agent_id,
                )
                if dependencies:
                    raise AgentDependencyConflict(
                        _dependency_message(len(dependencies))
                    )
                build_lineages = await _build_lineage_records(
                    session,
                    organization_id,
                    agent_id,
                )
                if build_lineages:
                    raise AgentDependencyConflict(
                        _build_dependency_message(len(build_lineages))
                    )
                await session.delete(agent)
                await session.flush()

    async def list_source_attachments(
        self,
        organization_id: uuid.UUID,
        agent_id: uuid.UUID,
    ) -> tuple[AgentSourceAttachmentRecord, ...]:
        await self.get(organization_id, agent_id)
        async with self.database.session() as session:
            rows = (
                await session.scalars(
                    select(AgentSourceAttachment)
                    .where(
                        AgentSourceAttachment.organization_id == organization_id,
                        AgentSourceAttachment.agent_id == agent_id,
                    )
                    .order_by(AgentSourceAttachment.attached_at, AgentSourceAttachment.id)
                )
            ).all()
        return tuple(_attachment_record(row) for row in rows)

    async def attach_source(
        self,
        organization_id: uuid.UUID,
        agent_id: uuid.UUID,
        source: AttachableSource,
    ) -> AgentSourceAttachmentRecord:
        now = datetime.now(UTC)
        try:
            async with self.database.session() as session:
                async with session.begin():
                    agent = await session.scalar(
                        select(Agent)
                        .where(
                            Agent.organization_id == organization_id,
                            Agent.id == agent_id,
                            Agent.lifecycle == AgentLifecycle.ACTIVE,
                        )
                        .with_for_update()
                    )
                    if agent is None:
                        raise AgentNotFound("The selected agent is unavailable.")
                    row = await session.scalar(
                        select(AgentSourceAttachment)
                        .where(
                            AgentSourceAttachment.organization_id == organization_id,
                            AgentSourceAttachment.agent_id == agent_id,
                            AgentSourceAttachment.source_id == source.source_id,
                        )
                        .with_for_update()
                    )
                    if row is None:
                        row = AgentSourceAttachment(
                            organization_id=organization_id,
                            agent_id=agent_id,
                            source_id=source.source_id,
                            source_revision_id=source.source_revision_id,
                            attached_at=now,
                        )
                        session.add(row)
                    elif row.source_revision_id != source.source_revision_id:
                        row.source_revision_id = source.source_revision_id
                        row.attached_at = now
                    await session.flush()
        except IntegrityError as error:
            raise AgentSourceAttachmentConflict(
                "The Source attachment changed concurrently. Reload the Agent before trying again."
            ) from error
        return _attachment_record(row)

    async def get_source_attachment(
        self,
        organization_id: uuid.UUID,
        agent_id: uuid.UUID,
        source_id: str,
    ) -> AgentSourceAttachmentRecord:
        await self.get(organization_id, agent_id)
        async with self.database.session() as session:
            row = await session.scalar(
                select(AgentSourceAttachment).where(
                    AgentSourceAttachment.organization_id == organization_id,
                    AgentSourceAttachment.agent_id == agent_id,
                    AgentSourceAttachment.source_id == source_id,
                )
            )
        if row is None:
            raise AgentSourceAttachmentUnavailable(
                "The selected Source is not attached to this Agent."
            )
        return _attachment_record(row)

    async def detach_source(
        self,
        organization_id: uuid.UUID,
        agent_id: uuid.UUID,
        source_id: str,
    ) -> None:
        async with self.database.session() as session:
            async with session.begin():
                agent = await session.scalar(
                    select(Agent)
                    .where(
                        Agent.organization_id == organization_id,
                        Agent.id == agent_id,
                        Agent.lifecycle == AgentLifecycle.ACTIVE,
                    )
                    .with_for_update()
                )
                if agent is None:
                    raise AgentNotFound("The selected agent is unavailable.")
                row = await session.scalar(
                    select(AgentSourceAttachment)
                    .where(
                        AgentSourceAttachment.organization_id == organization_id,
                        AgentSourceAttachment.agent_id == agent_id,
                        AgentSourceAttachment.source_id == source_id,
                    )
                    .with_for_update()
                )
                if row is None:
                    raise AgentSourceAttachmentUnavailable(
                        "The selected Source is not attached to this Agent."
                    )
                await session.delete(row)
                await session.flush()

    async def record_build_lineage(
        self,
        organization_id: uuid.UUID,
        agent_id: uuid.UUID,
        *,
        build_id: uuid.UUID,
        expected_agent_version: int,
        source_references: tuple[tuple[str, str], ...],
    ) -> AgentBuildLineageRecord:
        if len({source_id for source_id, _ in source_references}) != len(source_references):
            raise AgentBuildLineageConflict("A build can reference each Source only once.")
        now = datetime.now(UTC)
        try:
            async with self.database.session() as session:
                async with session.begin():
                    agent = await session.scalar(
                        select(Agent)
                        .where(
                            Agent.organization_id == organization_id,
                            Agent.id == agent_id,
                            Agent.lifecycle == AgentLifecycle.ACTIVE,
                        )
                        .with_for_update()
                    )
                    if agent is None:
                        raise AgentNotFound("The selected agent is unavailable.")
                    exact_version = await session.scalar(
                        select(AgentVersion.id).where(
                            AgentVersion.agent_id == agent_id,
                            AgentVersion.version == expected_agent_version,
                        )
                    )
                    if exact_version is None:
                        raise AgentBuildLineageConflict(
                            "The exact accepted Agent configuration is unavailable for this build."
                        )
                    attachments = {
                        (row.source_id, row.source_revision_id)
                        for row in (
                            await session.scalars(
                                select(AgentSourceAttachment).where(
                                    AgentSourceAttachment.organization_id == organization_id,
                                    AgentSourceAttachment.agent_id == agent_id,
                                )
                            )
                        ).all()
                    }
                    if not set(source_references) <= attachments:
                        raise AgentBuildLineageConflict(
                            "A build Source reference must match an exact persisted Agent attachment."
                        )
                    lineage = AgentBuildLineage(
                        organization_id=organization_id,
                        agent_id=agent_id,
                        build_id=build_id,
                        agent_version=expected_agent_version,
                        created_at=now,
                    )
                    lineage.source_references = [
                        AgentBuildSourceReference(
                            source_id=source_id,
                            source_revision_id=source_revision_id,
                        )
                        for source_id, source_revision_id in source_references
                    ]
                    session.add(lineage)
                    await session.flush()
                    record = _build_lineage_record(lineage)
        except IntegrityError as error:
            raise AgentBuildLineageConflict(
                "This build identity already has immutable Source lineage."
            ) from error
        return record

    async def list_build_lineages(
        self,
        organization_id: uuid.UUID,
        agent_id: uuid.UUID,
    ) -> tuple[AgentBuildLineageRecord, ...]:
        await self.get(organization_id, agent_id)
        async with self.database.session() as session:
            return await _build_lineage_records(session, organization_id, agent_id)


def _record(agent: Agent, version: AgentVersion) -> AgentRecord:
    return AgentRecord(
        id=agent.id,
        organization_id=agent.organization_id,
        name=version.name,
        description=version.description,
        instructions=version.instructions,
        lifecycle=agent.lifecycle,
        current_version=agent.current_version,
        created_at=agent.created_at,
        updated_at=agent.updated_at,
    )


def _attachment_record(value: AgentSourceAttachment) -> AgentSourceAttachmentRecord:
    return AgentSourceAttachmentRecord(
        id=value.id,
        organization_id=value.organization_id,
        agent_id=value.agent_id,
        source_id=value.source_id,
        source_revision_id=value.source_revision_id,
        attached_at=value.attached_at,
    )


def _build_lineage_record(
    value: AgentBuildLineage,
    references: tuple[AgentBuildSourceReference, ...] | None = None,
) -> AgentBuildLineageRecord:
    rows = tuple(value.source_references) if references is None else references
    return AgentBuildLineageRecord(
        id=value.id,
        organization_id=value.organization_id,
        agent_id=value.agent_id,
        build_id=value.build_id,
        agent_version=value.agent_version,
        created_at=value.created_at,
        source_references=tuple(
            AgentBuildSourceReferenceRecord(
                id=row.id,
                build_lineage_id=value.id,
                source_id=row.source_id,
                source_revision_id=row.source_revision_id,
            )
            for row in rows
        ),
    )


async def _build_lineage_records(
    session: AsyncSession,
    organization_id: uuid.UUID,
    agent_id: uuid.UUID,
) -> tuple[AgentBuildLineageRecord, ...]:
    lineages = (
        await session.scalars(
            select(AgentBuildLineage)
            .where(
                AgentBuildLineage.organization_id == organization_id,
                AgentBuildLineage.agent_id == agent_id,
            )
            .order_by(AgentBuildLineage.created_at.desc(), AgentBuildLineage.id)
        )
    ).all()
    result: list[AgentBuildLineageRecord] = []
    for lineage in lineages:
        references = tuple(
            (
                await session.scalars(
                    select(AgentBuildSourceReference)
                    .where(AgentBuildSourceReference.build_lineage_id == lineage.id)
                    .order_by(AgentBuildSourceReference.source_id)
                )
            ).all()
        )
        result.append(_build_lineage_record(lineage, references))
    return tuple(result)


async def _dependency_records(
    session: AsyncSession,
    organization_id: uuid.UUID,
    agent_id: uuid.UUID,
) -> tuple[AgentSourceAttachmentRecord, ...]:
    rows = (
        await session.scalars(
            select(AgentSourceAttachment)
            .where(
                AgentSourceAttachment.organization_id == organization_id,
                AgentSourceAttachment.agent_id == agent_id,
            )
            .order_by(AgentSourceAttachment.attached_at, AgentSourceAttachment.id)
        )
    ).all()
    return tuple(_attachment_record(row) for row in rows)


def _dependency_message(source_attachment_count: int) -> str:
    noun = "Source attachment" if source_attachment_count == 1 else "Source attachments"
    return (
        f"Delete is blocked by {source_attachment_count} {noun}. "
        "The Agent and every dependency remain unchanged."
    )


def _build_dependency_message(build_count: int) -> str:
    noun = "historical build" if build_count == 1 else "historical builds"
    return (
        f"Delete is blocked by {build_count} {noun}. "
        "The Agent and every immutable build reference remain unchanged."
    )


__all__ = ["SqlAlchemyAgentRepository"]
