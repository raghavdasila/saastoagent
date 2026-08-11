from routedeck_core.contracts.projection import FrozenJsonObject
from routedeck_core.supervision.guards import ProviderInvocationContext, ProviderResult


class ContractRevisionProposalProvider:
    async def __call__(self, context: ProviderInvocationContext) -> ProviderResult:
        del context
        return ProviderResult(values=FrozenJsonObject({}))


class SelectedApiSourceProvider:
    async def __call__(self, context: ProviderInvocationContext) -> ProviderResult:
        selected = next(
            (
                surface
                for surface in context.session.public_state.surface_state
                if surface.surface_id == "sources.api"
            ),
            None,
        )
        if selected is None:
            return ProviderResult(values=FrozenJsonObject({}))
        values = {item.name: item.value.to_python() for item in selected.values}
        source_id = values.get("selected_source_id")
        revision_id = values.get("selected_source_revision_id")
        if not isinstance(source_id, str) or not isinstance(revision_id, str):
            return ProviderResult(values=FrozenJsonObject({}))
        return ProviderResult(
            values=FrozenJsonObject(
                {
                    "source_id": source_id,
                    "source_revision_id": revision_id,
                }
            )
        )


def selected_api_source_identity(
    provider_values: FrozenJsonObject,
) -> tuple[str, str] | None:
    selected = provider_values.to_dict().get("sources.selected_api_source", {})
    if not isinstance(selected, dict):
        return None
    source_id = selected.get("source_id")
    revision_id = selected.get("source_revision_id")
    if not isinstance(source_id, str) or not isinstance(revision_id, str):
        return None
    return source_id, revision_id


__all__ = [
    "ContractRevisionProposalProvider",
    "SelectedApiSourceProvider",
    "selected_api_source_identity",
]
