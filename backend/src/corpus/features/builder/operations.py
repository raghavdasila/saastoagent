import uuid
from dataclasses import dataclass

from pydantic import ValidationError
from routedeck_core.contracts.failures import FailureKind, FailureSafeDetails, RouteDeckFailure
from routedeck_core.contracts.operations import DeliveryPhase, OperationOutcome
from routedeck_core.ports.executor import ExecutionContext

from corpus.features.agents.ports import AgentOwnerScopeGateway, AgentOwnerScopeUnavailable

from .declarations import ASSEMBLE_BUILD, DELETE_BUILD, RUN_BUILD, STOP_BUILD
from .ports import BuilderConflict, BuilderUnavailable
from .schemas import AssembleBuildArguments
from .schemas import BuildRuntimeLifecycleArguments
from .service import BuilderService


@dataclass(frozen=True)
class AssembleBuildHandler:
    service: BuilderService
    owner_scope: AgentOwnerScopeGateway

    async def __call__(self, arguments, context: ExecutionContext) -> OperationOutcome:
        try:
            payload = AssembleBuildArguments.model_validate(dict(arguments))
            organization_id = await self.owner_scope.organization_id_for_route(context.session_id)
            agent_id = uuid.UUID(context.private_entity_id("agent_ref"))
            if payload.build_request_id is None:
                await self.service.assemble_current(organization_id, agent_id)
            else:
                await self.service.assemble(
                    organization_id,
                    agent_id,
                    build_request_id=payload.build_request_id,
                )
        except (ValidationError, ValueError, KeyError) as error:
            return _failure(context, "invalid_build_request", str(error), FailureKind.CONTRACT)
        except BuilderUnavailable as error:
            return _failure(context, "builder_unavailable", str(error), FailureKind.BUSINESS)
        except BuilderConflict as error:
            return _failure(context, "builder_conflict", str(error), FailureKind.STATE_CONFLICT)
        except AgentOwnerScopeUnavailable as error:
            return _failure(context, "authentication_required", str(error), FailureKind.STATE_CONFLICT)
        return OperationOutcome(outcome="assembled", delivery_phase=DeliveryPhase.RESPONSE_RECEIVED)


@dataclass(frozen=True)
class BuildRuntimeLifecycleHandler:
    service: BuilderService
    owner_scope: AgentOwnerScopeGateway
    operation: object
    action: str

    async def __call__(self, arguments, context: ExecutionContext) -> OperationOutcome:
        try:
            payload = BuildRuntimeLifecycleArguments.model_validate(dict(arguments))
            organization_id = await self.owner_scope.organization_id_for_route(context.session_id)
            agent_id = uuid.UUID(context.private_entity_id("agent_ref"))
            if self.action == "run":
                await self.service.run(
                    organization_id, agent_id, build_id=payload.build_id
                )
                outcome = "running"
            elif self.action == "stop":
                await self.service.stop(
                    organization_id, agent_id, build_id=payload.build_id
                )
                outcome = "stopped"
            elif self.action == "delete":
                await self.service.remove_runtime(
                    organization_id, agent_id, build_id=payload.build_id
                )
                outcome = "removed"
            else:
                raise RuntimeError("builder_runtime_action_invalid")
        except (ValidationError, ValueError, KeyError) as error:
            return _failure_for(
                context, self.operation, "invalid_build_runtime_request",
                str(error), FailureKind.CONTRACT,
            )
        except BuilderUnavailable as error:
            return _failure_for(
                context, self.operation, "builder_unavailable",
                str(error), FailureKind.BUSINESS,
            )
        except BuilderConflict as error:
            return _failure_for(
                context, self.operation, "builder_conflict",
                str(error), FailureKind.STATE_CONFLICT,
            )
        except AgentOwnerScopeUnavailable as error:
            return _failure_for(
                context, self.operation, "authentication_required",
                str(error), FailureKind.STATE_CONFLICT,
            )
        return OperationOutcome(
            outcome=outcome, delivery_phase=DeliveryPhase.RESPONSE_RECEIVED
        )


def _failure(context, code, message, kind):
    return _failure_for(context, ASSEMBLE_BUILD, code, message, kind)


def _failure_for(context, operation, code, message, kind):
    return OperationOutcome(delivery_phase=DeliveryPhase.NOT_SENT, failure=RouteDeckFailure(
        kind=kind, code=code, phase="builder_service", correlation_id=context.attempt_id,
        operation_id=operation.id, request_id=context.request_id, public_message=message,
        safe_details=FailureSafeDetails(delivery_phase=DeliveryPhase.NOT_SENT.value),
    ))


__all__ = ["AssembleBuildHandler", "BuildRuntimeLifecycleHandler"]
