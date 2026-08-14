import asyncio

from routedeck_core.contracts.projection import FrozenJsonObject
from routedeck_core.supervision.guards import ProviderInvocationContext, ProviderResult

from .ports import SourceOwnerScopeGateway
from .service import SourceService


class ContractRevisionProposalProvider:
    async def __call__(self, context: ProviderInvocationContext) -> ProviderResult:
        del context
        return ProviderResult(values=FrozenJsonObject({}))


class SelectedApiSourceProvider:
    def __init__(
        self,
        service: SourceService,
        owner_scope: SourceOwnerScopeGateway,
    ) -> None:
        self.service = service
        self.owner_scope = owner_scope

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
        organization_id = await self.owner_scope.organization_id_for_route(
            context.session.session_id
        )
        source = await asyncio.to_thread(
            self.service.get_source,
            owner_key=str(organization_id),
            source_id=source_id,
            revision_id=revision_id,
        )
        selected_context = {
            "source_id": source_id,
            "source_revision_id": revision_id,
            "display_name": source.display_name,
            "processing_state": source.revision.state.value,
        }
        for name in (
            "return_agent_ref",
            "agent_handoff_mode",
            "attached_source_revision_id",
            "return_context",
            "initial_workspace",
        ):
            value = values.get(name)
            if isinstance(value, str):
                selected_context[name] = value
        if "attached_source_revision_id" not in selected_context:
            matching_agents: list[tuple[str, str]] = []
            for entity in context.session.public_state.entity_handles:
                if entity.entity_kind != "agent":
                    continue
                entity_values = {
                    item.name: item.value.to_python() for item in entity.values
                }
                if entity_values.get("attached_source_id") != source_id:
                    continue
                attached_revision = entity_values.get("attached_source_revision_id")
                if isinstance(attached_revision, str):
                    matching_agents.append((entity.handle, attached_revision))
            if len(matching_agents) == 1:
                agent_ref, attached_revision = matching_agents[0]
                selected_context.update(
                    {
                        "return_agent_ref": agent_ref,
                        "agent_handoff_mode": "inspect",
                        "attached_source_revision_id": attached_revision,
                        "return_context": "agent",
                    }
                )
        attached_revision_id = selected_context.get("attached_source_revision_id")
        if isinstance(attached_revision_id, str):
            selected_context["attachment_update_available"] = (
                attached_revision_id != revision_id
            )
        return ProviderResult(values=FrozenJsonObject(selected_context))


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
