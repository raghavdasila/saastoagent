from __future__ import annotations

import uuid
from typing import Protocol

from routedeck_core.contracts.navigation import NodeRef

from corpus.features.agents.contracts import (
    OPEN_AGENT_SANDBOX,
    OPEN_ATTACHED_SOURCE,
    RETURN_TO_AGENT_HUB,
)

from .declarations import (
    ASSEMBLE_BUILD,
    DELETE_BUILD,
    PAUSE_BUILD,
    RUN_BUILD,
    STOP_BUILD,
)
from .domain import BuilderRecord
from .ports import BuilderUnavailable
from .schemas import AgentBuildCollectionView

BUILDER_HOME_REF = NodeRef(id="builder.home")
BUILDER_AGENT_BOUND_OPERATION_IDS = tuple(
    operation.id
    for operation in (
        RETURN_TO_AGENT_HUB,
        ASSEMBLE_BUILD,
        OPEN_ATTACHED_SOURCE,
        RUN_BUILD,
        PAUSE_BUILD,
        STOP_BUILD,
        DELETE_BUILD,
        OPEN_AGENT_SANDBOX,
    )
)


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


__all__ = [
    "BUILDER_AGENT_BOUND_OPERATION_IDS",
    "BUILDER_HOME_REF",
    "BuilderRuntimeReader",
    "BuilderUnavailable",
]
