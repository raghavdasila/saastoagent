from __future__ import annotations

from dataclasses import dataclass
import uuid

from routedeck_core.contracts.failures import FailureKind, RouteDeckFailure
from routedeck_core.supervision.guards import GuardDecision, GuardInvocationContext

from .ports import AgentNotFound, AgentOwnerScopeGateway, AgentOwnerScopeUnavailable
from .service import AgentService


@dataclass(frozen=True)
class ArchiveCurrentGuard:
    service: AgentService
    owner_scope: AgentOwnerScopeGateway

    async def __call__(self, context: GuardInvocationContext) -> GuardDecision:
        resolved = _agent_id(context)
        if resolved is None:
            return GuardDecision.blocked(
                _failure(context, "agent_selection_stale", "Select the exact active Agent again before continuing.")
            )
        try:
            organization_id = await self.owner_scope.organization_id_for_route(
                context.session.session_id
            )
            await self.service.get(organization_id, resolved)
        except (AgentNotFound, AgentOwnerScopeUnavailable) as error:
            return GuardDecision.blocked(
                _failure(context, "agent_unavailable", str(error))
            )
        return GuardDecision.allowed_result()


@dataclass(frozen=True)
class DeleteDependenciesGuard:
    service: AgentService
    owner_scope: AgentOwnerScopeGateway

    async def __call__(self, context: GuardInvocationContext) -> GuardDecision:
        resolved = _agent_id(context)
        if resolved is None:
            return GuardDecision.blocked(
                _failure(context, "agent_selection_stale", "Select the exact active Agent again before continuing.")
            )
        try:
            organization_id = await self.owner_scope.organization_id_for_route(
                context.session.session_id
            )
            dependencies = await self.service.inspect_dependencies(
                organization_id,
                resolved,
            )
        except (AgentNotFound, AgentOwnerScopeUnavailable) as error:
            return GuardDecision.blocked(
                _failure(context, "agent_unavailable", str(error))
            )
        if dependencies.blocks_delete:
            count = len(dependencies.source_attachments)
            noun = "Source attachment" if count == 1 else "Source attachments"
            return GuardDecision.blocked(
                _failure(
                    context,
                    "agent_dependency_conflict",
                    f"Delete is blocked by {count} {noun}. The Agent and every dependency remain unchanged.",
                )
            )
        return GuardDecision.allowed_result()


def _agent_id(context: GuardInvocationContext) -> uuid.UUID | None:
    matches = tuple(
        item
        for item in context.resolved_entities
        if item.argument_name == "agent_ref" and item.entity_kind == "agent"
    )
    if len(matches) != 1:
        return None
    try:
        return uuid.UUID(matches[0].private_id.get_secret_value())
    except ValueError:
        return None


def _failure(
    context: GuardInvocationContext,
    code: str,
    message: str,
) -> RouteDeckFailure:
    return RouteDeckFailure(
        kind=FailureKind.GUARD,
        code=code,
        phase="agents_lifecycle_guard",
        correlation_id=context.attempt_id,
        operation_id=context.request.operation_id,
        request_id=context.request.request_id,
        public_message=message,
    )


__all__ = ["ArchiveCurrentGuard", "DeleteDependenciesGuard"]
