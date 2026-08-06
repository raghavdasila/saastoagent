from __future__ import annotations

import uuid
from datetime import UTC, datetime

from sqlalchemy import and_, select
from sqlalchemy.exc import IntegrityError

from corpus.persistence import CorpusDatabase

from .domain import AgentLifecycle, AgentRecord
from .models import Agent, AgentVersion
from .ports import AgentNameConflict, AgentNotFound, AgentVersionConflict


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


__all__ = ["SqlAlchemyAgentRepository"]
