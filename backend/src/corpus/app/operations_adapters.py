from __future__ import annotations

import uuid

from sqlalchemy import select

from corpus.features.deployment.models import AgentDeployment
from corpus.features.operations.domain import OperationsLineage
from corpus.integrations.agent_execution import NeutralAgentExecutionAdapter
from corpus.persistence import CorpusDatabase


class CorpusOperationsLineageGateway:
    def __init__(self, database: CorpusDatabase, execution: NeutralAgentExecutionAdapter) -> None:
        self.database, self.execution = database, execution

    async def resolve(self, organization_id: uuid.UUID, runtime_deployment_id: str, request_id: str):
        async with self.database.session() as session:
            deployment = await session.scalar(select(AgentDeployment).where(
                AgentDeployment.organization_id == organization_id,
                AgentDeployment.runtime_deployment_id == runtime_deployment_id,
            ))
        if deployment is None:
            return None
        try:
            run = self.execution.load_run(str(organization_id), request_id)
        except KeyError:
            return None
        if run.build_hash != deployment.bundle_hash:
            return None
        return OperationsLineage(
            agent_id=deployment.agent_id, build_id=deployment.build_id,
            deployment_id=deployment.id, runtime_run_id=run.run_id,
            safe_events=tuple({
                "sequence": item.sequence, "kind": item.kind,
                "safe_data": dict(item.safe_data),
            } for item in run.events),
        )


__all__ = ["CorpusOperationsLineageGateway"]
