from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any

from pydantic import ValidationError
from routedeck_core.contracts.failures import FailureKind, FailureSafeDetails, RouteDeckFailure
from routedeck_core.contracts.operations import DeliveryPhase, OperationOutcome
from routedeck_core.ports.executor import ExecutionContext

from .declarations import CREATE_AGENT, SAVE_AGENT_CHANGES
from .ports import (
    AgentNameConflict,
    AgentNotFound,
    AgentOwnerScopeGateway,
    AgentOwnerScopeUnavailable,
    AgentVersionConflict,
)
from .schemas import CreateAgentArguments, UpdateAgentArguments
from .service import AgentService


@dataclass(frozen=True)
class CreateAgentHandler:
    service: AgentService
    owner_scope: AgentOwnerScopeGateway

    async def __call__(
        self,
        arguments: Mapping[str, Any],
        context: ExecutionContext,
    ) -> OperationOutcome:
        try:
            payload = CreateAgentArguments.model_validate(dict(arguments))
            organization_id = await self.owner_scope.organization_id_for_route(
                context.session_id
            )
            await self.service.create(organization_id, payload)
        except (ValidationError, ValueError) as error:
            return _failure(context, CREATE_AGENT.id, "invalid_agent", str(error), FailureKind.CONTRACT)
        except AgentNameConflict as error:
            return _failure(context, CREATE_AGENT.id, "agent_name_conflict", str(error), FailureKind.BUSINESS)
        except AgentOwnerScopeUnavailable as error:
            return _failure(context, CREATE_AGENT.id, "authentication_required", str(error), FailureKind.STATE_CONFLICT)
        return _success("created")


@dataclass(frozen=True)
class SaveAgentChangesHandler:
    service: AgentService
    owner_scope: AgentOwnerScopeGateway

    async def __call__(
        self,
        arguments: Mapping[str, Any],
        context: ExecutionContext,
    ) -> OperationOutcome:
        try:
            payload = UpdateAgentArguments.model_validate(dict(arguments))
            organization_id = await self.owner_scope.organization_id_for_route(
                context.session_id
            )
            await self.service.update(organization_id, payload)
        except (ValidationError, ValueError) as error:
            return _failure(context, SAVE_AGENT_CHANGES.id, "invalid_agent", str(error), FailureKind.CONTRACT)
        except AgentNotFound as error:
            return _failure(context, SAVE_AGENT_CHANGES.id, "agent_unavailable", str(error), FailureKind.BUSINESS)
        except AgentNameConflict as error:
            return _failure(context, SAVE_AGENT_CHANGES.id, "agent_name_conflict", str(error), FailureKind.BUSINESS)
        except AgentVersionConflict as error:
            return _failure(context, SAVE_AGENT_CHANGES.id, "agent_version_conflict", str(error), FailureKind.STATE_CONFLICT)
        except AgentOwnerScopeUnavailable as error:
            return _failure(context, SAVE_AGENT_CHANGES.id, "authentication_required", str(error), FailureKind.STATE_CONFLICT)
        return _success("saved")


class AgentNavigationHandler:
    def __init__(self, operation_id: str) -> None:
        self.operation_id = operation_id

    async def __call__(self, arguments, context) -> OperationOutcome:
        del context
        if arguments:
            raise ValueError(f"{self.operation_id} accepts no arguments")
        return _success("opened")


def _success(outcome: str) -> OperationOutcome:
    return OperationOutcome(
        outcome=outcome,
        delivery_phase=DeliveryPhase.RESPONSE_RECEIVED,
    )


def _failure(context, operation_id, code, message, kind) -> OperationOutcome:
    return OperationOutcome(
        delivery_phase=DeliveryPhase.NOT_SENT,
        failure=RouteDeckFailure(
            kind=kind,
            code=code,
            phase="agents_service",
            correlation_id=context.attempt_id,
            operation_id=operation_id,
            request_id=context.request_id,
            public_message=message,
            safe_details=FailureSafeDetails(
                delivery_phase=DeliveryPhase.NOT_SENT.value
            ),
        ),
    )


__all__ = [
    "AgentNavigationHandler",
    "CreateAgentHandler",
    "SaveAgentChangesHandler",
]
