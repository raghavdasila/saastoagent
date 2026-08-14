from __future__ import annotations

import uuid

from routedeck_core.contracts.projection import FrozenJsonObject
from routedeck_core.supervision.guards import ProviderInvocationContext, ProviderResult

from corpus.auth.contracts import AgentOwnerScopeGateway

from .ports import DesignerUnavailable
from .service import DesignerService


class CurrentDesignProvider:
    def __init__(
        self,
        service: DesignerService,
        owner_scope: AgentOwnerScopeGateway,
    ) -> None:
        self.service = service
        self.owner_scope = owner_scope

    async def __call__(self, context: ProviderInvocationContext) -> ProviderResult:
        values = context.request.arguments.to_dict()
        handle = values.get("agent_ref")
        if not isinstance(handle, str) or not handle:
            raise DesignerUnavailable("The selected Agent is unavailable.")
        binding = next(
            (
                item
                for item in context.session.private_state.entity_bindings
                if item.entity_kind == "agent" and item.public_handle == handle
            ),
            None,
        )
        if binding is None:
            raise DesignerUnavailable("The selected Agent is unavailable.")
        organization_id = await self.owner_scope.organization_id_for_route(
            context.session.session_id
        )
        design = await self.service.get(
            organization_id,
            uuid.UUID(binding.private_id),
        )
        return ProviderResult(values=FrozenJsonObject({
            "current_revision_id": str(design.current_revision_id),
            "accepted_revision_id": (
                str(design.accepted_revision_id)
                if design.accepted_revision_id is not None
                else None
            ),
        }))


__all__ = ["CurrentDesignProvider"]
