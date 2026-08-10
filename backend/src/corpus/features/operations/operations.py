from dataclasses import dataclass

from pydantic import ValidationError
from routedeck_core.contracts.failures import FailureKind, FailureSafeDetails, RouteDeckFailure
from routedeck_core.contracts.operations import DeliveryPhase, OperationOutcome
from routedeck_core.ports.executor import ExecutionContext

from corpus.features.agents.ports import AgentOwnerScopeGateway, AgentOwnerScopeUnavailable

from .declarations import PROMOTE_INTERACTION
from .ports import OperationsUnavailable
from .schemas import PromoteInteractionArguments
from .service import OperationsService


@dataclass(frozen=True)
class PromoteInteractionHandler:
    service: OperationsService
    owner_scope: AgentOwnerScopeGateway

    async def __call__(self, arguments, context: ExecutionContext) -> OperationOutcome:
        try:
            payload = PromoteInteractionArguments.model_validate(dict(arguments))
            owner = await self.owner_scope.organization_id_for_route(context.session_id)
            values = payload.model_dump(exclude={"interaction_id"})
            if payload.interaction_id is None:
                await self.service.promote_current(owner, **values)
            else:
                await self.service.promote(
                    owner,
                    interaction_id=payload.interaction_id,
                    **values,
                )
        except (ValidationError, ValueError, KeyError) as error:
            return _failure(context, "invalid_operations_promotion", str(error), FailureKind.CONTRACT)
        except (OperationsUnavailable, AgentOwnerScopeUnavailable) as error:
            return _failure(context, "operations_unavailable", str(error), FailureKind.STATE_CONFLICT)
        return OperationOutcome(outcome="promoted", delivery_phase=DeliveryPhase.RESPONSE_RECEIVED)


def _failure(context, code, message, kind):
    return OperationOutcome(delivery_phase=DeliveryPhase.NOT_SENT, failure=RouteDeckFailure(
        kind=kind, code=code, phase="operations_service",
        correlation_id=context.attempt_id, operation_id=PROMOTE_INTERACTION.id,
        request_id=context.request_id, public_message=message,
        safe_details=FailureSafeDetails(delivery_phase=DeliveryPhase.NOT_SENT.value),
    ))
