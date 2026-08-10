from __future__ import annotations

import uuid
from datetime import UTC, datetime

from sqlalchemy import select

from corpus.persistence import CorpusDatabase

from .domain import DeploymentRecord
from .models import AgentDeployment
from .ports import DeploymentConflict, DeploymentUnavailable


class SqlAlchemyDeploymentRepository:
    def __init__(self, database: CorpusDatabase) -> None:
        self.database = database

    async def reserve(self, organization_id, agent_id, *, channel_id, build_id, eligibility_id, bundle_hash):
        now = datetime.now(UTC)
        value = AgentDeployment(
            id=uuid.uuid4(), organization_id=organization_id, agent_id=agent_id,
            channel_id=channel_id, build_id=build_id, eligibility_id=eligibility_id,
            runtime_deployment_id=None, status="verifying", bundle_hash=bundle_hash,
            failure_code=None, failure_message=None, created_at=now, updated_at=now,
        )
        async with self.database.session() as session:
            async with session.begin():
                session.add(value)
                await session.flush()
        return _record(value)

    async def complete(self, organization_id, deployment_id, *, runtime_deployment_id, status, failure_code=None, failure_message=None):
        async with self.database.session() as session:
            async with session.begin():
                value = await _locked(session, organization_id, deployment_id)
                if value.status != "verifying":
                    raise DeploymentConflict("This deployment request is no longer verifying.")
                value.runtime_deployment_id = runtime_deployment_id
                value.status = status
                value.failure_code = failure_code
                value.failure_message = failure_message
                value.updated_at = datetime.now(UTC)
                await session.flush()
                return _record(value)

    async def list(self, organization_id, agent_id):
        async with self.database.session() as session:
            values = tuple((await session.scalars(select(AgentDeployment).where(
                AgentDeployment.organization_id == organization_id,
                AgentDeployment.agent_id == agent_id,
            ).order_by(AgentDeployment.created_at.desc()))).all())
        return tuple(_record(value) for value in values)

    async def get(self, organization_id, agent_id, deployment_id):
        async with self.database.session() as session:
            value = await session.scalar(select(AgentDeployment).where(
                AgentDeployment.organization_id == organization_id,
                AgentDeployment.agent_id == agent_id,
                AgentDeployment.id == deployment_id,
            ))
        if value is None:
            raise DeploymentUnavailable("The selected deployment is unavailable.")
        return _record(value)


async def _locked(session, organization_id, deployment_id):
    value = await session.scalar(select(AgentDeployment).where(
        AgentDeployment.organization_id == organization_id,
        AgentDeployment.id == deployment_id,
    ).with_for_update())
    if value is None:
        raise DeploymentUnavailable("The selected deployment is unavailable.")
    return value


def _record(value):
    return DeploymentRecord(
        value.id, value.organization_id, value.agent_id, value.channel_id,
        value.build_id, value.eligibility_id, value.runtime_deployment_id,
        value.status, value.bundle_hash, value.failure_code, value.failure_message,
        value.created_at, value.updated_at,
    )


__all__ = ["SqlAlchemyDeploymentRepository"]
