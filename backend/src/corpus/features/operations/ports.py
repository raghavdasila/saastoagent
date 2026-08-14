from __future__ import annotations

import uuid
from typing import Protocol

from corpus.shared.agent_delivery import InteractionProjection

from .domain import OperationsLineage


class OperationsUnavailable(RuntimeError):
    pass


class OperationsLineageGateway(Protocol):
    async def resolve(self, organization_id: uuid.UUID, runtime_deployment_id: str, request_id: str) -> OperationsLineage | None: ...


class OperationsDeliveryPort(Protocol):
    def interactions(self) -> tuple[InteractionProjection, ...]: ...

    def interaction(self, interaction_id: str) -> InteractionProjection: ...


class OperationsEvaluationPort(Protocol):
    async def promoted_operations_case_id(
        self, organization_id: uuid.UUID, interaction_id: str
    ) -> uuid.UUID | None: ...

    async def create_case_from_operations(self, *args, **kwargs): ...
