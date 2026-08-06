from __future__ import annotations

from dataclasses import asdict
from typing import Protocol

from routedeck_core.contracts.projection import FrozenJsonObject
from routedeck_core.supervision.guards import ProviderInvocationContext, ProviderResult

from .contracts import OWNER_CONTEXT_PROVIDER, OwnerRouteContext


class OwnerContextResolver(Protocol):
    async def owner_context_for_route(
        self,
        route_session_id: str,
    ) -> OwnerRouteContext: ...


class OwnerContextProvider:
    def __init__(self, resolver: OwnerContextResolver) -> None:
        self._resolver = resolver

    async def __call__(self, context: ProviderInvocationContext) -> ProviderResult:
        owner = await self._resolver.owner_context_for_route(
            context.session.session_id
        )
        return ProviderResult(values=FrozenJsonObject(asdict(owner)))


__all__ = [
    "OWNER_CONTEXT_PROVIDER",
    "OwnerContextProvider",
    "OwnerContextResolver",
]
