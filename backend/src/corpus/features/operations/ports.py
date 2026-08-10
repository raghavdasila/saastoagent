from __future__ import annotations

import uuid
from typing import Protocol

from .domain import OperationsLineage


class OperationsUnavailable(RuntimeError):
    pass


class OperationsLineageGateway(Protocol):
    async def resolve(self, organization_id: uuid.UUID, runtime_deployment_id: str, request_id: str) -> OperationsLineage | None: ...

