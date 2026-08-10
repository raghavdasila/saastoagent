from __future__ import annotations

import uuid
from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError

from corpus.persistence import CorpusDatabase

from .domain import ChannelRecord
from .models import AgentChannel
from .ports import ChannelConflict, ChannelUnavailable


class SqlAlchemyChannelRepository:
    def __init__(self, database: CorpusDatabase) -> None:
        self.database = database

    async def reserve(self, organization_id, agent_id, *, name: str, slug: str) -> ChannelRecord:
        now = datetime.now(UTC)
        value = AgentChannel(
            id=uuid.uuid4(), organization_id=organization_id, agent_id=agent_id,
            runtime_channel_id=None, name=name, slug=slug, status="creating", enabled=False,
            active_deployment_id=None, failure_code=None, failure_message=None,
            created_at=now, updated_at=now,
        )
        try:
            async with self.database.session() as session:
                async with session.begin():
                    session.add(value)
                    await session.flush()
        except IntegrityError as error:
            raise ChannelConflict("That hosted Web address is already in use.") from error
        return _record(value)

    async def complete(self, organization_id, channel_id, *, runtime_channel_id: str) -> ChannelRecord:
        async with self.database.session() as session:
            async with session.begin():
                value = await _locked(session, organization_id, channel_id)
                if value.status != "creating":
                    raise ChannelConflict("This channel creation is no longer pending.")
                value.runtime_channel_id = runtime_channel_id
                value.status = "ready"
                value.enabled = True
                value.updated_at = datetime.now(UTC)
                await session.flush()
                return _record(value)

    async def fail(self, organization_id, channel_id, *, code: str, message: str) -> ChannelRecord:
        async with self.database.session() as session:
            async with session.begin():
                value = await _locked(session, organization_id, channel_id)
                value.status = "failed"
                value.failure_code = code[:80]
                value.failure_message = message[:500]
                value.updated_at = datetime.now(UTC)
                await session.flush()
                return _record(value)

    async def set_active(self, organization_id, channel_id, deployment_id) -> ChannelRecord:
        async with self.database.session() as session:
            async with session.begin():
                value = await _locked(session, organization_id, channel_id)
                if value.status != "ready":
                    raise ChannelConflict("The channel is not ready for activation.")
                value.active_deployment_id = deployment_id
                value.updated_at = datetime.now(UTC)
                await session.flush()
                return _record(value)

    async def set_enabled(
        self, organization_id, agent_id, channel_id, *, enabled: bool
    ) -> ChannelRecord:
        async with self.database.session() as session:
            async with session.begin():
                value = await _locked(session, organization_id, channel_id)
                if value.agent_id != agent_id or value.status != "ready" or not value.runtime_channel_id:
                    raise ChannelUnavailable("The selected channel is unavailable.")
                value.enabled = enabled
                value.updated_at = datetime.now(UTC)
                await session.flush()
                return _record(value)

    async def list(self, organization_id, agent_id) -> tuple[ChannelRecord, ...]:
        async with self.database.session() as session:
            values = tuple((await session.scalars(select(AgentChannel).where(
                AgentChannel.organization_id == organization_id,
                AgentChannel.agent_id == agent_id,
            ).order_by(AgentChannel.created_at.desc()))).all())
        return tuple(_record(value) for value in values)

    async def get(self, organization_id, agent_id, channel_id) -> ChannelRecord:
        async with self.database.session() as session:
            value = await session.scalar(select(AgentChannel).where(
                AgentChannel.organization_id == organization_id,
                AgentChannel.agent_id == agent_id,
                AgentChannel.id == channel_id,
            ))
        if value is None:
            raise ChannelUnavailable("The selected channel is unavailable.")
        return _record(value)

    async def get_public(self, slug: str) -> ChannelRecord:
        async with self.database.session() as session:
            value = await session.scalar(select(AgentChannel).where(
                AgentChannel.slug == slug, AgentChannel.status == "ready",
            ))
        if value is None:
            raise ChannelUnavailable("This public Agent is unavailable.")
        return _record(value)


async def _locked(session, organization_id, channel_id):
    value = await session.scalar(select(AgentChannel).where(
        AgentChannel.organization_id == organization_id,
        AgentChannel.id == channel_id,
    ).with_for_update())
    if value is None:
        raise ChannelUnavailable("The selected channel is unavailable.")
    return value


def _record(value) -> ChannelRecord:
    return ChannelRecord(
        value.id, value.organization_id, value.agent_id, value.runtime_channel_id,
        value.name, value.slug, value.status, value.enabled, value.active_deployment_id,
        value.failure_code, value.failure_message, value.created_at, value.updated_at,
    )


__all__ = ["SqlAlchemyChannelRepository"]
