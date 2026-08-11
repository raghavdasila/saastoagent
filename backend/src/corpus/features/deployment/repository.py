from __future__ import annotations

import uuid
from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError

from corpus.persistence import CorpusDatabase

from .domain import DeploymentRecord
from .models import AgentDeployment
from .ports import DeploymentConflict, DeploymentUnavailable


class SqlAlchemyDeploymentRepository:
    def __init__(self, database: CorpusDatabase) -> None:
        self.database = database

    async def reserve(
        self, organization_id, agent_id, *, channel_id, build_id,
        eligibility_id, bundle_hash, retry_of_deployment_id=None,
    ):
        now = datetime.now(UTC)
        value = AgentDeployment(
            id=uuid.uuid4(), organization_id=organization_id, agent_id=agent_id,
            channel_id=channel_id, build_id=build_id, eligibility_id=eligibility_id,
            runtime_deployment_id=None, job_id=None,
            retry_of_deployment_id=retry_of_deployment_id,
            active_channel_id=channel_id, status="queued", bundle_hash=bundle_hash,
            failure_code=None, failure_message=None, created_at=now, updated_at=now,
        )
        async with self.database.session() as session:
            async with session.begin():
                if retry_of_deployment_id is not None:
                    retry = await session.scalar(select(AgentDeployment).where(
                        AgentDeployment.id == retry_of_deployment_id,
                        AgentDeployment.organization_id == organization_id,
                        AgentDeployment.agent_id == agent_id,
                        AgentDeployment.channel_id == channel_id,
                        AgentDeployment.build_id == build_id,
                    ).with_for_update())
                    if retry is None or retry.status != "failed":
                        raise DeploymentConflict(
                            "Only the exact failed deployment can be retried."
                        )
                session.add(value)
                try:
                    await session.flush()
                except IntegrityError as error:
                    raise DeploymentConflict(
                        "That channel already has an active deployment attempt."
                    ) from error
        return _record(value)

    async def link_job(self, organization_id, deployment_id, job_id):
        async with self.database.session() as session:
            async with session.begin():
                value = await _locked(session, organization_id, deployment_id)
                if value.job_id == job_id and value.status in {"queued", "running"}:
                    return _record(value)
                if value.status != "queued":
                    raise DeploymentConflict(
                        "This deployment attempt is no longer queued."
                    )
                if value.job_id is not None and value.job_id != job_id:
                    raise DeploymentConflict(
                        "This deployment attempt is linked to another job."
                    )
                value.job_id = job_id
                value.updated_at = datetime.now(UTC)
                await session.flush()
                return _record(value)

    async def mark_running(self, organization_id, deployment_id, job_id):
        async with self.database.session() as session:
            async with session.begin():
                value = await _locked(session, organization_id, deployment_id)
                if value.status == "running" and value.job_id == job_id:
                    return _record(value)
                if (
                    value.status != "queued"
                    or value.job_id not in {None, job_id}
                ):
                    raise DeploymentConflict(
                        "This deployment attempt changed before the worker started."
                    )
                value.job_id = job_id
                value.status = "running"
                value.updated_at = datetime.now(UTC)
                await session.flush()
                return _record(value)

    async def complete(self, organization_id, deployment_id, *, runtime_deployment_id, status, failure_code=None, failure_message=None):
        async with self.database.session() as session:
            async with session.begin():
                value = await _locked(session, organization_id, deployment_id)
                if value.status == status and value.runtime_deployment_id == runtime_deployment_id:
                    return _record(value)
                if value.status not in {"queued", "running"}:
                    raise DeploymentConflict("This deployment request is no longer active.")
                value.runtime_deployment_id = runtime_deployment_id
                value.status = status
                value.failure_code = failure_code
                value.failure_message = failure_message
                value.active_channel_id = None
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
        value.created_at, value.updated_at, value.job_id,
        value.retry_of_deployment_id,
    )


__all__ = ["SqlAlchemyDeploymentRepository"]
