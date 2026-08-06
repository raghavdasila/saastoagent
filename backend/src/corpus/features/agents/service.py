from __future__ import annotations

import uuid

from .ports import AgentRepository
from .schemas import AgentListView, AgentView, CreateAgentArguments, UpdateAgentArguments


class AgentService:
    def __init__(self, repository: AgentRepository) -> None:
        self.repository = repository

    async def list(self, organization_id: uuid.UUID) -> AgentListView:
        records = await self.repository.list(organization_id)
        return AgentListView(agents=tuple(AgentView.from_record(item) for item in records))

    async def get(
        self,
        organization_id: uuid.UUID,
        agent_id: uuid.UUID,
    ) -> AgentView:
        return AgentView.from_record(
            await self.repository.get(organization_id, agent_id)
        )

    async def create(
        self,
        organization_id: uuid.UUID,
        arguments: CreateAgentArguments,
    ) -> AgentView:
        name = _normalized_name(arguments.name)
        return AgentView.from_record(
            await self.repository.create(
                organization_id,
                name=name,
                name_key=name.casefold(),
                description=arguments.description.strip(),
                instructions=arguments.instructions.strip(),
            )
        )

    async def update(
        self,
        organization_id: uuid.UUID,
        arguments: UpdateAgentArguments,
    ) -> AgentView:
        name = _normalized_name(arguments.name)
        return AgentView.from_record(
            await self.repository.update(
                organization_id,
                arguments.agent_id,
                expected_version=arguments.expected_version,
                name=name,
                name_key=name.casefold(),
                description=arguments.description.strip(),
                instructions=arguments.instructions.strip(),
            )
        )


def _normalized_name(value: str) -> str:
    normalized = " ".join(value.split())
    if not normalized:
        raise ValueError("Agent name cannot be blank.")
    return normalized


__all__ = ["AgentService"]
