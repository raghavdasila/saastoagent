from __future__ import annotations

from collections.abc import Mapping
from dataclasses import asdict
from typing import Any, Protocol

from routedeck_core.app import FeatureBindings
from routedeck_core.contracts.operations import DeliveryPhase, OperationOutcome
from routedeck_core.ports.executor import ExecutionContext
from routedeck_core.contracts.projection import FrozenJsonObject
from routedeck_core.supervision.guards import ProviderInvocationContext, ProviderResult

from .declarations import (
    AUTHENTICATION_COMPLETED,
    OPEN_FORGOT_PASSWORD,
    OPEN_REGISTRATION,
    OPEN_RESET_PASSWORD,
    OPEN_SIGN_IN,
    OPEN_SOURCES,
    OPEN_VERIFY_EMAIL,
    OWNER_CONTEXT_PROVIDER,
    RETURN_TO_LOUNGE,
)


class OwnerContextResolver(Protocol):
    async def owner_context_for_route(self, route_session_id: str): ...


class OwnerContextProvider:
    def __init__(self, resolver: OwnerContextResolver) -> None:
        self._resolver = resolver

    async def __call__(self, context: ProviderInvocationContext) -> ProviderResult:
        owner = await self._resolver.owner_context_for_route(
            context.session.session_id
        )
        return ProviderResult(values=FrozenJsonObject(asdict(owner)))


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


def create_workspace_bindings(
    owner_context_resolver: OwnerContextResolver,
) -> FeatureBindings:
    return FeatureBindings(
        handlers={
            operation.ref: NavigationHandler(operation.id)
            for operation in (
                OPEN_SIGN_IN,
                OPEN_REGISTRATION,
                OPEN_FORGOT_PASSWORD,
                OPEN_RESET_PASSWORD,
                OPEN_VERIFY_EMAIL,
                RETURN_TO_LOUNGE,
                AUTHENTICATION_COMPLETED,
                OPEN_SOURCES,
            )
        },
        providers={
            OWNER_CONTEXT_PROVIDER.ref: OwnerContextProvider(
                owner_context_resolver
            )
        },
        guards={},
    )


__all__ = ["OwnerContextResolver", "create_workspace_bindings"]
