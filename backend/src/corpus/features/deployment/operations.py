import uuid
from dataclasses import dataclass

from pydantic import ValidationError
from routedeck_core.contracts.failures import FailureKind, FailureSafeDetails, RouteDeckFailure
from routedeck_core.contracts.operations import DeliveryPhase, OperationOutcome
from routedeck_core.ports.executor import ExecutionContext

from .declarations import DEPLOY_AGENT, RETRY_DEPLOYMENT, ROLLBACK_DEPLOYMENT
from .ports import DeploymentConflict, DeploymentUnavailable
from .schemas import DeployArguments, RetryDeploymentArguments, RollbackArguments


@dataclass(frozen=True)
class DeployHandler:
    service: object
    owner_scope: object

    async def __call__(self, arguments, context: ExecutionContext) -> OperationOutcome:
        return await _run(self, arguments, context, deploy=True)


@dataclass(frozen=True)
class RollbackHandler:
    service: object
    owner_scope: object

    async def __call__(self, arguments, context: ExecutionContext) -> OperationOutcome:
        return await _run(self, arguments, context, deploy=False)


@dataclass(frozen=True)
class RetryDeploymentHandler:
    service: object
    owner_scope: object

    async def __call__(self, arguments, context: ExecutionContext) -> OperationOutcome:
        try:
            payload = RetryDeploymentArguments.model_validate(dict(arguments))
            organization_id = await self.owner_scope.organization_id_for_route(
                context.session_id
            )
            agent_id = uuid.UUID(context.private_entity_id("agent_ref"))
            await self.service.retry_deployment(
                organization_id, agent_id, payload.deployment_id
            )
        except (ValidationError, ValueError, KeyError) as error:
            return _failure(context, RETRY_DEPLOYMENT, "invalid_deployment", str(error), FailureKind.CONTRACT)
        except DeploymentConflict as error:
            return _failure(context, RETRY_DEPLOYMENT, "deployment_conflict", str(error), FailureKind.STATE_CONFLICT)
        except DeploymentUnavailable as error:
            return _failure(context, RETRY_DEPLOYMENT, "deployment_unavailable", str(error), FailureKind.BUSINESS)
        return OperationOutcome(
            outcome="queued", delivery_phase=DeliveryPhase.RESPONSE_RECEIVED
        )


async def _run(handler, arguments, context, *, deploy: bool):
    operation = DEPLOY_AGENT if deploy else ROLLBACK_DEPLOYMENT
    try:
        payload = (DeployArguments if deploy else RollbackArguments).model_validate(dict(arguments))
        organization_id = await handler.owner_scope.organization_id_for_route(context.session_id)
        agent_id = uuid.UUID(context.private_entity_id("agent_ref"))
        if deploy:
            if payload.channel_id is None and payload.build_id is None:
                await handler.service.queue_current(organization_id, agent_id)
            elif payload.channel_id is None or payload.build_id is None:
                raise DeploymentConflict(
                    "Channel and build must be selected together."
                )
            else:
                await handler.service.queue_deploy(
                    organization_id, agent_id,
                    channel_id=payload.channel_id, build_id=payload.build_id,
                )
        else:
            if payload.channel_id is None and payload.deployment_id is None:
                await handler.service.rollback_current(organization_id, agent_id)
            elif payload.channel_id is None or payload.deployment_id is None:
                raise DeploymentConflict(
                    "Channel and rollback deployment must be selected together."
                )
            else:
                await handler.service.rollback(
                    organization_id, agent_id,
                    channel_id=payload.channel_id, deployment_id=payload.deployment_id,
                )
    except (ValidationError, ValueError, KeyError) as error:
        return _failure(context, operation, "invalid_deployment", str(error), FailureKind.CONTRACT)
    except DeploymentConflict as error:
        return _failure(context, operation, "deployment_conflict", str(error), FailureKind.STATE_CONFLICT)
    except DeploymentUnavailable as error:
        return _failure(context, operation, "deployment_unavailable", str(error), FailureKind.BUSINESS)
    return OperationOutcome(
        outcome="queued" if deploy else "rolled_back",
        delivery_phase=DeliveryPhase.RESPONSE_RECEIVED,
    )


def _failure(context, operation, code, message, kind):
    return OperationOutcome(delivery_phase=DeliveryPhase.NOT_SENT, failure=RouteDeckFailure(
        kind=kind, code=code, phase="deployment_service", correlation_id=context.attempt_id,
        operation_id=operation.id, request_id=context.request_id,
        public_message=message,
        safe_details=FailureSafeDetails(delivery_phase=DeliveryPhase.NOT_SENT.value),
    ))


__all__ = ["DeployHandler", "RetryDeploymentHandler", "RollbackHandler"]
