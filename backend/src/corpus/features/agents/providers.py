from routedeck_core.contracts.projection import FrozenJsonObject
from routedeck_core.supervision.guards import ProviderInvocationContext, ProviderResult


class SelectedAgentProvider:
    async def __call__(self, context: ProviderInvocationContext) -> ProviderResult:
        del context
        return ProviderResult(values=FrozenJsonObject({}))


class PendingSourceProvider:
    async def __call__(self, context: ProviderInvocationContext) -> ProviderResult:
        selected = next(
            (
                surface
                for surface in context.session.public_state.surface_state
                if surface.surface_id in {"agents.home", "agents.create"}
                and any(value.name == "pending_source_id" for value in surface.values)
            ),
            None,
        )
        if selected is None:
            return ProviderResult(values=FrozenJsonObject({}))
        values = {item.name: item.value.to_python() for item in selected.values}
        source_id = values.get("pending_source_id")
        revision_id = values.get("pending_source_revision_id")
        display_name = values.get("pending_source_display_name")
        if not isinstance(source_id, str) or not isinstance(revision_id, str):
            return ProviderResult(values=FrozenJsonObject({}))
        result: dict[str, str] = {
            "source_id": source_id,
            "source_revision_id": revision_id,
        }
        if isinstance(display_name, str) and display_name:
            result["display_name"] = display_name
        return ProviderResult(values=FrozenJsonObject(result))


__all__ = ["PendingSourceProvider", "SelectedAgentProvider"]
