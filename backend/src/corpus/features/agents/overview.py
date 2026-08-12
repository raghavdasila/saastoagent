from __future__ import annotations

import uuid

from .ports import AgentProductOverviewGateway
from .schemas import AgentProductOverviewView


class AgentProductOverviewService:
    def __init__(self, gateway: AgentProductOverviewGateway) -> None:
        self.gateway = gateway

    async def get(
        self,
        organization_id: uuid.UUID,
        agent_id: uuid.UUID,
    ) -> AgentProductOverviewView:
        return AgentProductOverviewView.from_model(
            await self.gateway.overview(organization_id, agent_id)
        )


__all__ = ["AgentProductOverviewService"]
