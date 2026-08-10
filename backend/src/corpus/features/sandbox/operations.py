import uuid
from dataclasses import dataclass

from pydantic import ValidationError
from routedeck_core.contracts.failures import FailureKind, FailureSafeDetails, RouteDeckFailure
from routedeck_core.contracts.operations import DeliveryPhase, OperationOutcome
from routedeck_core.contracts.projection import FrozenJsonObject
from routedeck_core.ports.executor import ExecutionContext

from corpus.features.agents.ports import AgentOwnerScopeGateway, AgentOwnerScopeUnavailable
from corpus.features.builder.ports import BuilderUnavailable

from .declarations import RESUME_SANDBOX, START_SANDBOX
from .ports import SandboxConflict, SandboxUnavailable
from .schemas import ResumeSandboxArguments, StartSandboxArguments
from .service import SandboxService


@dataclass(frozen=True)
class StartSandboxHandler:
    service: SandboxService
    owner_scope: AgentOwnerScopeGateway

    async def __call__(self, arguments, context: ExecutionContext) -> OperationOutcome:
        try:
            payload = StartSandboxArguments.model_validate(dict(arguments))
            organization_id = await self.owner_scope.organization_id_for_route(context.session_id)
            agent_id = uuid.UUID(context.private_entity_id("agent_ref"))
            if payload.build_id is None:
                result = await self.service.start_current(
                    organization_id,
                    agent_id,
                    message=payload.message,
                )
            else:
                result = await self.service.start(
                    organization_id,
                    agent_id,
                    build_id=payload.build_id,
                    message=payload.message,
                )
        except (ValidationError, ValueError, KeyError) as error:
            return _failure(context, "invalid_sandbox_request", str(error), FailureKind.CONTRACT)
        except (SandboxUnavailable, BuilderUnavailable) as error:
            return _failure(context, "sandbox_unavailable", str(error), FailureKind.BUSINESS)
        except SandboxConflict as error:
            return _failure(context, "sandbox_conflict", str(error), FailureKind.STATE_CONFLICT)
        except AgentOwnerScopeUnavailable as error:
            return _failure(context, "authentication_required", str(error), FailureKind.STATE_CONFLICT)
        observation = FrozenJsonObject(sandbox_tool_observation(result))
        return OperationOutcome(
            outcome="started",
            delivery_phase=DeliveryPhase.RESPONSE_RECEIVED,
            observation=observation,
            public_observation=observation,
        )


@dataclass(frozen=True)
class ResumeSandboxHandler:
    service: SandboxService
    owner_scope: AgentOwnerScopeGateway

    async def __call__(self, arguments, context: ExecutionContext) -> OperationOutcome:
        try:
            payload = ResumeSandboxArguments.model_validate(dict(arguments))
            organization_id = await self.owner_scope.organization_id_for_route(context.session_id)
            agent_id = uuid.UUID(context.private_entity_id("agent_ref"))
            if payload.run_id is None:
                result = await self.service.resume_current(
                    organization_id,
                    agent_id,
                    message=payload.message,
                    selected_operation_id=payload.selected_operation_id,
                    answers=payload.answers,
                )
            else:
                result = await self.service.resume(
                    organization_id,
                    agent_id,
                    run_id=payload.run_id,
                    message=payload.message,
                    selected_operation_id=payload.selected_operation_id,
                    answers=payload.answers,
                )
        except (ValidationError, ValueError, KeyError) as error:
            return _failure_for(RESUME_SANDBOX.id, context, "invalid_sandbox_clarification", str(error), FailureKind.CONTRACT)
        except (SandboxUnavailable, BuilderUnavailable) as error:
            return _failure_for(RESUME_SANDBOX.id, context, "sandbox_unavailable", str(error), FailureKind.BUSINESS)
        except SandboxConflict as error:
            return _failure_for(RESUME_SANDBOX.id, context, "sandbox_conflict", str(error), FailureKind.STATE_CONFLICT)
        except AgentOwnerScopeUnavailable as error:
            return _failure_for(RESUME_SANDBOX.id, context, "authentication_required", str(error), FailureKind.STATE_CONFLICT)
        observation = FrozenJsonObject(sandbox_tool_observation(result))
        return OperationOutcome(
            outcome="resumed",
            delivery_phase=DeliveryPhase.RESPONSE_RECEIVED,
            observation=observation,
            public_observation=observation,
        )


def sandbox_tool_observation(run) -> dict[str, object]:
    clarification = None
    if run.clarification is not None:
        clarification = {
            "question": run.clarification.question,
            "candidate_choices": [
                {"operation_id": item.operation_id, "label": item.label}
                for item in run.clarification.candidate_choices
            ],
            "missing_input_names": list(run.clarification.missing_input_names),
        }
    return {
        "status": run.status,
        "final_response": run.final_response,
        "api_call_count": run.api_call_count,
        "clarification": clarification,
    }


def _failure(context, code, message, kind):
    return _failure_for(START_SANDBOX.id, context, code, message, kind)


def _failure_for(operation_id, context, code, message, kind):
    return OperationOutcome(delivery_phase=DeliveryPhase.NOT_SENT, failure=RouteDeckFailure(
        kind=kind, code=code, phase="sandbox_service", correlation_id=context.attempt_id,
        operation_id=operation_id, request_id=context.request_id, public_message=message,
        safe_details=FailureSafeDetails(delivery_phase=DeliveryPhase.NOT_SENT.value),
    ))
