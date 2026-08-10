import uuid
from dataclasses import dataclass

from pydantic import ValidationError
from routedeck_core.contracts.failures import FailureKind, FailureSafeDetails, RouteDeckFailure
from routedeck_core.contracts.operations import DeliveryPhase, OperationOutcome
from routedeck_core.ports.executor import ExecutionContext

from .declarations import CREATE_CHANNEL, SET_CHANNEL_ENABLED
from .ports import ChannelConflict, ChannelUnavailable
from .schemas import CreateChannelArguments, SetChannelEnabledArguments


@dataclass(frozen=True)
class CreateChannelHandler:
    service: object
    owner_scope: object

    async def __call__(self, arguments, context: ExecutionContext) -> OperationOutcome:
        try:
            payload = CreateChannelArguments.model_validate(dict(arguments))
            organization_id = await self.owner_scope.organization_id_for_route(context.session_id)
            agent_id = uuid.UUID(context.private_entity_id("agent_ref"))
            await self.service.create(
                organization_id, agent_id, name=payload.name, slug=payload.slug
            )
        except (ValidationError, ValueError, KeyError) as error:
            return _failure(context, "invalid_channel", str(error), FailureKind.CONTRACT)
        except ChannelConflict as error:
            return _failure(context, "channel_conflict", str(error), FailureKind.STATE_CONFLICT)
        except ChannelUnavailable as error:
            return _failure(context, "channel_unavailable", str(error), FailureKind.BUSINESS)
        return OperationOutcome(outcome="created", delivery_phase=DeliveryPhase.RESPONSE_RECEIVED)


@dataclass(frozen=True)
class SetChannelEnabledHandler:
    service: object
    owner_scope: object

    async def __call__(self, arguments, context: ExecutionContext) -> OperationOutcome:
        try:
            payload = SetChannelEnabledArguments.model_validate(dict(arguments))
            organization_id = await self.owner_scope.organization_id_for_route(context.session_id)
            agent_id = uuid.UUID(context.private_entity_id("agent_ref"))
            if payload.channel_id is None:
                await self.service.set_current_enabled(
                    organization_id,
                    agent_id,
                    enabled=payload.enabled,
                )
            else:
                await self.service.set_enabled(
                    organization_id, agent_id, payload.channel_id, enabled=payload.enabled
                )
        except (ValidationError, ValueError, KeyError) as error:
            return _failure(
                context, "invalid_channel_availability", str(error), FailureKind.CONTRACT,
                operation=SET_CHANNEL_ENABLED,
            )
        except ChannelConflict as error:
            return _failure(
                context, "channel_conflict", str(error), FailureKind.STATE_CONFLICT,
                operation=SET_CHANNEL_ENABLED,
            )
        except ChannelUnavailable as error:
            return _failure(
                context, "channel_unavailable", str(error), FailureKind.BUSINESS,
                operation=SET_CHANNEL_ENABLED,
            )
        return OperationOutcome(
            outcome="availability_set", delivery_phase=DeliveryPhase.RESPONSE_RECEIVED
        )


def _failure(context, code, message, kind, *, operation=CREATE_CHANNEL):
    return OperationOutcome(delivery_phase=DeliveryPhase.NOT_SENT, failure=RouteDeckFailure(
        kind=kind, code=code, phase="channel_service", correlation_id=context.attempt_id,
        operation_id=operation.id, request_id=context.request_id,
        public_message=message,
        safe_details=FailureSafeDetails(delivery_phase=DeliveryPhase.NOT_SENT.value),
    ))


__all__ = ["CreateChannelHandler", "SetChannelEnabledHandler"]
