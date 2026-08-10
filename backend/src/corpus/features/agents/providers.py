from routedeck_core.contracts.projection import FrozenJsonObject
from routedeck_core.supervision.guards import ProviderInvocationContext, ProviderResult


class SelectedAgentProvider:
    async def __call__(self, context: ProviderInvocationContext) -> ProviderResult:
        del context
        return ProviderResult(values=FrozenJsonObject({}))


__all__ = ["SelectedAgentProvider"]
