import uuid
from dataclasses import dataclass

from pydantic import ValidationError
from routedeck_core.contracts.failures import FailureKind, FailureSafeDetails, RouteDeckFailure
from routedeck_core.contracts.operations import DeliveryPhase, OperationOutcome
from routedeck_core.ports.executor import ExecutionContext

from corpus.features.agents.ports import AgentOwnerScopeGateway, AgentOwnerScopeUnavailable

from .declarations import CREATE_CASE, RUN_CASE
from .ports import EvaluationConflict, EvaluationUnavailable
from .schemas import CreateEvaluationCaseArguments, RunEvaluationCaseArguments
from .service import EvaluationService


@dataclass(frozen=True)
class CreateCaseHandler:
    service: EvaluationService
    owner_scope: AgentOwnerScopeGateway

    async def __call__(self, arguments, context: ExecutionContext) -> OperationOutcome:
        try:
            payload = CreateEvaluationCaseArguments.model_validate(dict(arguments))
            owner = await self.owner_scope.organization_id_for_route(context.session_id)
            agent_id = uuid.UUID(context.private_entity_id("agent_ref"))
            if payload.build_id is None and payload.sandbox_run_id is None:
                await self.service.create_case_from_current_sandbox(
                    owner,
                    agent_id,
                    set_name=payload.set_name,
                    title=payload.title,
                    category=payload.category,
                    difficulty=payload.difficulty,
                    mandatory=payload.mandatory,
                )
            elif payload.build_id is None or payload.sandbox_run_id is None:
                raise EvaluationConflict(
                    "Build and Sandbox interaction must be selected together."
                )
            else:
                await self.service.create_case_from_sandbox(
                    owner, agent_id, build_id=payload.build_id,
                    sandbox_run_id=payload.sandbox_run_id, set_name=payload.set_name,
                    title=payload.title, category=payload.category,
                    difficulty=payload.difficulty,
                    mandatory=payload.mandatory,
                )
        except (ValidationError, ValueError, KeyError) as error:
            return _failure(context, CREATE_CASE.id, "invalid_evaluation_case", str(error), FailureKind.CONTRACT)
        except (EvaluationUnavailable, AgentOwnerScopeUnavailable) as error:
            return _failure(context, CREATE_CASE.id, "evaluation_unavailable", str(error), FailureKind.STATE_CONFLICT)
        except EvaluationConflict as error:
            return _failure(context, CREATE_CASE.id, "evaluation_conflict", str(error), FailureKind.BUSINESS)
        return OperationOutcome(outcome="created", delivery_phase=DeliveryPhase.RESPONSE_RECEIVED)


@dataclass(frozen=True)
class RunCaseHandler:
    service: EvaluationService
    owner_scope: AgentOwnerScopeGateway

    async def __call__(self, arguments, context: ExecutionContext) -> OperationOutcome:
        try:
            payload = RunEvaluationCaseArguments.model_validate(dict(arguments))
            owner = await self.owner_scope.organization_id_for_route(context.session_id)
            agent_id = uuid.UUID(context.private_entity_id("agent_ref"))
            if payload.case_id is None:
                await self.service.run_current_case(owner, agent_id)
            else:
                await self.service.run_case(owner, agent_id, payload.case_id)
        except (ValidationError, ValueError, KeyError) as error:
            return _failure(context, RUN_CASE.id, "invalid_evaluation_run", str(error), FailureKind.CONTRACT)
        except (EvaluationUnavailable, AgentOwnerScopeUnavailable) as error:
            return _failure(context, RUN_CASE.id, "evaluation_unavailable", str(error), FailureKind.STATE_CONFLICT)
        except EvaluationConflict as error:
            return _failure(context, RUN_CASE.id, "evaluation_conflict", str(error), FailureKind.BUSINESS)
        except Exception:
            return _failure(context, RUN_CASE.id, "evaluation_failed", "The evaluation run failed.", FailureKind.PROVIDER_PROTOCOL)
        return OperationOutcome(outcome="evaluated", delivery_phase=DeliveryPhase.RESPONSE_RECEIVED)


def _failure(context, operation_id, code, message, kind):
    return OperationOutcome(delivery_phase=DeliveryPhase.NOT_SENT, failure=RouteDeckFailure(
        kind=kind, code=code, phase="evaluation_service", correlation_id=context.attempt_id,
        operation_id=operation_id, request_id=context.request_id,
        public_message=message,
        safe_details=FailureSafeDetails(delivery_phase=DeliveryPhase.NOT_SENT.value),
    ))
