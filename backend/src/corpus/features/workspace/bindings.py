from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from routedeck_core.app import FeatureBindings
from routedeck_core.contracts.operations import DeliveryPhase, OperationOutcome
from routedeck_core.ports.executor import ExecutionContext
from routedeck_core.contracts.projection import FrozenJsonObject
from routedeck_core.supervision.guards import (
    ProviderInvocationContext,
    ProviderResult,
)

from .contracts import WORKSPACE_OVERVIEW_PROVIDER
from .declarations import OPEN_AGENTS, OPEN_SOURCES, OPEN_VERIFICATION
from .service import WorkspaceService


class NavigationHandler:
    def __init__(self, operation_id: str) -> None:
        self._operation_id = operation_id

    async def __call__(
        self,
        arguments: Mapping[str, Any],
        context: ExecutionContext,
    ) -> OperationOutcome:
        del context
        if arguments:
            raise ValueError(f"{self._operation_id} accepts no arguments")
        return OperationOutcome(
            outcome="opened",
            delivery_phase=DeliveryPhase.RESPONSE_RECEIVED,
        )


class WorkspaceOverviewProvider:
    def __init__(self, service: WorkspaceService) -> None:
        self.service = service

    async def __call__(
        self,
        context: ProviderInvocationContext,
    ) -> ProviderResult:
        value = await self.service.for_route(context.session.session_id)
        return ProviderResult(
            values=FrozenJsonObject(value.model_dump(mode="json"))
        )


def create_workspace_bindings(service: WorkspaceService) -> FeatureBindings:
    return FeatureBindings(
        handlers={
            operation.ref: NavigationHandler(operation.id)
            for operation in (OPEN_AGENTS, OPEN_SOURCES, OPEN_VERIFICATION)
        },
        providers={
            WORKSPACE_OVERVIEW_PROVIDER.ref: WorkspaceOverviewProvider(service)
        },
        guards={},
    )


__all__ = ["create_workspace_bindings"]
