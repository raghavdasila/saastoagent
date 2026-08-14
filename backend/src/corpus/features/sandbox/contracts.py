from __future__ import annotations

import uuid
from typing import Protocol

from routedeck_core.contracts.navigation import NodeRef

from .ports import SandboxRunFailed
from .schemas import SandboxRunCollectionView, SandboxRunView

SANDBOX_HOME_REF = NodeRef(id="sandbox.home")


class SandboxRuntimeReader(Protocol):
    """Stable Sandbox capability consumed by Evaluation."""

    async def list(
        self, organization_id: uuid.UUID, agent_id: uuid.UUID
    ) -> SandboxRunCollectionView: ...

    async def start(
        self,
        organization_id: uuid.UUID,
        agent_id: uuid.UUID,
        *,
        build_id: uuid.UUID,
        message: str,
    ) -> SandboxRunView: ...


__all__ = ["SANDBOX_HOME_REF", "SandboxRunFailed", "SandboxRuntimeReader"]
