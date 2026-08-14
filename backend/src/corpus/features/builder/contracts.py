from __future__ import annotations

import uuid
from typing import Protocol

from routedeck_core.contracts.navigation import NodeRef

from .domain import BuilderRecord
from .ports import BuilderUnavailable
from .schemas import AgentBuildCollectionView

BUILDER_HOME_REF = NodeRef(id="builder.home")


class BuilderRuntimeReader(Protocol):
    """Stable build-read capability consumed by downstream product features."""

    async def list(
        self, organization_id: uuid.UUID, agent_id: uuid.UUID
    ) -> AgentBuildCollectionView: ...

    async def require_immutable_built(
        self,
        organization_id: uuid.UUID,
        agent_id: uuid.UUID,
        build_id: uuid.UUID,
    ) -> BuilderRecord: ...

    async def require_running(
        self,
        organization_id: uuid.UUID,
        agent_id: uuid.UUID,
        build_id: uuid.UUID,
    ) -> BuilderRecord: ...


__all__ = ["BUILDER_HOME_REF", "BuilderRuntimeReader", "BuilderUnavailable"]
