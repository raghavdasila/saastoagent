import uuid

from routedeck_core.contracts.projection import FrozenJsonObject
from routedeck_core.supervision.guards import ProviderInvocationContext, ProviderResult

from .overview import AgentProductOverviewService
from .ports import AgentOwnerScopeGateway


class SelectedAgentProvider:
    async def __call__(self, context: ProviderInvocationContext) -> ProviderResult:
        del context
        return ProviderResult(values=FrozenJsonObject({}))


class PendingSourceProvider:
    async def __call__(self, context: ProviderInvocationContext) -> ProviderResult:
        active_surface_id = context.session.current.node_id
        if active_surface_id not in {"agents.home", "agents.create"}:
            return ProviderResult(values=FrozenJsonObject({}))
        selected = next(
            (
                surface
                for surface in context.session.public_state.surface_state
                if surface.surface_id == active_surface_id
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


class SelectedAgentOverviewProvider:
    def __init__(
        self,
        service: AgentProductOverviewService | None,
        owner_scope: AgentOwnerScopeGateway,
    ) -> None:
        self.service = service
        self.owner_scope = owner_scope

    async def __call__(self, context: ProviderInvocationContext) -> ProviderResult:
        bindings = tuple(
            binding
            for binding in context.session.private_state.entity_bindings
            if binding.entity_kind == "agent"
        )
        if not bindings:
            return ProviderResult(values=FrozenJsonObject({}))
        if len(bindings) != 1:
            raise RuntimeError("One exact selected Agent is required for its overview.")
        if self.service is None:
            raise RuntimeError("The selected-Agent overview service is not configured.")
        organization_id = await self.owner_scope.organization_id_for_route(
            context.session.session_id
        )
        value = await self.service.get(
            organization_id,
            uuid.UUID(bindings[0].private_id.get_secret_value()),
        )
        return ProviderResult(values=FrozenJsonObject(value.model_dump(mode="json")))


__all__ = ["PendingSourceProvider", "SelectedAgentOverviewProvider", "SelectedAgentProvider"]
