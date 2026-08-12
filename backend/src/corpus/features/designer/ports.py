from __future__ import annotations

import uuid
from typing import Protocol

from .domain import AgentDesignRecord, BuildRequestRecord, DesignerGeneratedFeature, DesignerInputSnapshot, DesignRevisionRecord


class DesignerUnavailable(RuntimeError):
    pass


class DesignerConflict(RuntimeError):
    pass


class DesignerInputGateway(Protocol):
    async def snapshot(self, organization_id: uuid.UUID, agent_id: uuid.UUID) -> DesignerInputSnapshot: ...


class DesignerGenerationGateway(Protocol):
    async def generate(
        self,
        snapshot: DesignerInputSnapshot,
        current_content: dict[str, object],
        description: str,
    ) -> DesignerGeneratedFeature: ...


class DesignerRepository(Protocol):
    async def get(self, organization_id: uuid.UUID, agent_id: uuid.UUID) -> tuple[AgentDesignRecord, tuple[DesignRevisionRecord, ...], BuildRequestRecord | None]: ...
    async def propose(self, organization_id: uuid.UUID, snapshot: DesignerInputSnapshot, *, content: dict[str, object], input_fingerprint: str) -> tuple[AgentDesignRecord, DesignRevisionRecord]: ...
    async def customize(self, organization_id: uuid.UUID, agent_id: uuid.UUID, *, expected_revision_id: uuid.UUID, content: dict[str, object]) -> tuple[AgentDesignRecord, DesignRevisionRecord]: ...
    async def accept(self, organization_id: uuid.UUID, agent_id: uuid.UUID, *, expected_revision_id: uuid.UUID) -> AgentDesignRecord: ...
    async def request_build(self, organization_id: uuid.UUID, agent_id: uuid.UUID, *, accepted_revision_id: uuid.UUID) -> BuildRequestRecord: ...
