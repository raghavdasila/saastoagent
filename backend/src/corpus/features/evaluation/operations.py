import uuid
from dataclasses import dataclass

from pydantic import ValidationError
from routedeck_core.contracts.failures import FailureKind, FailureSafeDetails, RouteDeckFailure
from routedeck_core.contracts.operations import DeliveryPhase, OperationOutcome
from routedeck_core.ports.executor import ExecutionContext

from corpus.features.agents.ports import AgentOwnerScopeGateway, AgentOwnerScopeUnavailable

from .declarations import (
    CREATE_CASE,
    DELETE_CASE,
    EDIT_CASE,
    GENERATE_SET,
    RETRY_CASE_RUN,
    RETRY_GENERATION,
    RUN_CASE,
)
from .ports import EvaluationConflict, EvaluationUnavailable
from .schemas import (
    CreateEvaluationCaseArguments,
    DeleteEvaluationCaseArguments,
    EditEvaluationCaseArguments,
    GenerateEvaluationSetArguments,
    RetryEvaluationRunArguments,
    RetryEvaluationGenerationArguments,
    RunEvaluationCaseArguments,
)
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
                await self.service.queue_current_case(owner, agent_id)
            else:
                await self.service.queue_case(owner, agent_id, payload.case_id)
        except (ValidationError, ValueError, KeyError) as error:
            return _failure(context, RUN_CASE.id, "invalid_evaluation_run", str(error), FailureKind.CONTRACT)
        except (EvaluationUnavailable, AgentOwnerScopeUnavailable) as error:
            return _failure(context, RUN_CASE.id, "evaluation_unavailable", str(error), FailureKind.STATE_CONFLICT)
        except EvaluationConflict as error:
            return _failure(context, RUN_CASE.id, "evaluation_conflict", str(error), FailureKind.BUSINESS)
        except Exception:
            return _failure(context, RUN_CASE.id, "evaluation_failed", "The evaluation run failed.", FailureKind.PROVIDER_PROTOCOL)
        return OperationOutcome(outcome="queued", delivery_phase=DeliveryPhase.RESPONSE_RECEIVED)


@dataclass(frozen=True)
class RetryCaseRunHandler:
    service: EvaluationService
    owner_scope: AgentOwnerScopeGateway

    async def __call__(self, arguments, context: ExecutionContext) -> OperationOutcome:
        try:
            payload = RetryEvaluationRunArguments.model_validate(dict(arguments))
            owner = await self.owner_scope.organization_id_for_route(context.session_id)
            agent_id = uuid.UUID(context.private_entity_id("agent_ref"))
            await self.service.retry_case_run(owner, agent_id, payload.attempt_id)
        except (ValidationError, ValueError, KeyError) as error:
            return _failure(context, RETRY_CASE_RUN.id, "invalid_evaluation_retry", str(error), FailureKind.CONTRACT)
        except (EvaluationUnavailable, AgentOwnerScopeUnavailable) as error:
            return _failure(context, RETRY_CASE_RUN.id, "evaluation_unavailable", str(error), FailureKind.STATE_CONFLICT)
        except EvaluationConflict as error:
            return _failure(context, RETRY_CASE_RUN.id, "evaluation_conflict", str(error), FailureKind.BUSINESS)
        return OperationOutcome(outcome="queued", delivery_phase=DeliveryPhase.RESPONSE_RECEIVED)


@dataclass(frozen=True)
class GenerateSetHandler:
    service: EvaluationService
    owner_scope: AgentOwnerScopeGateway

    async def __call__(self, arguments, context: ExecutionContext) -> OperationOutcome:
        try:
            payload = GenerateEvaluationSetArguments.model_validate(dict(arguments))
            owner = await self.owner_scope.organization_id_for_route(context.session_id)
            agent_id = uuid.UUID(context.private_entity_id("agent_ref"))
            await self.service.generate_set(
                owner, agent_id, build_id=payload.build_id,
                set_name=payload.set_name, categories=payload.categories,
            )
        except (ValidationError, ValueError, KeyError) as error:
            return _failure(context, GENERATE_SET.id, "invalid_evaluation_generation", str(error), FailureKind.CONTRACT)
        except (EvaluationUnavailable, AgentOwnerScopeUnavailable) as error:
            return _failure(context, GENERATE_SET.id, "evaluation_unavailable", str(error), FailureKind.STATE_CONFLICT)
        except EvaluationConflict as error:
            return _failure(context, GENERATE_SET.id, "evaluation_conflict", str(error), FailureKind.BUSINESS)
        return OperationOutcome(
            outcome="queued", delivery_phase=DeliveryPhase.RESPONSE_RECEIVED
        )


@dataclass(frozen=True)
class RetryGenerationHandler:
    service: EvaluationService
    owner_scope: AgentOwnerScopeGateway

    async def __call__(self, arguments, context: ExecutionContext) -> OperationOutcome:
        try:
            payload = RetryEvaluationGenerationArguments.model_validate(dict(arguments))
            owner = await self.owner_scope.organization_id_for_route(context.session_id)
            agent_id = uuid.UUID(context.private_entity_id("agent_ref"))
            await self.service.retry_generation(owner, agent_id, payload.evaluation_set_id)
        except (ValidationError, ValueError, KeyError) as error:
            return _failure(context, RETRY_GENERATION.id, "invalid_evaluation_retry", str(error), FailureKind.CONTRACT)
        except (EvaluationUnavailable, AgentOwnerScopeUnavailable) as error:
            return _failure(context, RETRY_GENERATION.id, "evaluation_unavailable", str(error), FailureKind.STATE_CONFLICT)
        except EvaluationConflict as error:
            return _failure(context, RETRY_GENERATION.id, "evaluation_conflict", str(error), FailureKind.BUSINESS)
        return OperationOutcome(
            outcome="queued", delivery_phase=DeliveryPhase.RESPONSE_RECEIVED
        )


@dataclass(frozen=True)
class EditCaseHandler:
    service: EvaluationService
    owner_scope: AgentOwnerScopeGateway

    async def __call__(self, arguments, context: ExecutionContext) -> OperationOutcome:
        try:
            payload = EditEvaluationCaseArguments.model_validate(dict(arguments))
            owner = await self.owner_scope.organization_id_for_route(context.session_id)
            agent_id = uuid.UUID(context.private_entity_id("agent_ref"))
            await self.service.edit_case(
                owner, agent_id, case_id=payload.case_id,
                expected_revision=payload.expected_revision,
                title=payload.title, category=payload.category,
                difficulty=payload.difficulty, mandatory=payload.mandatory,
            )
        except (ValidationError, ValueError, KeyError) as error:
            return _failure(context, EDIT_CASE.id, "invalid_evaluation_edit", str(error), FailureKind.CONTRACT)
        except (EvaluationUnavailable, AgentOwnerScopeUnavailable) as error:
            return _failure(context, EDIT_CASE.id, "evaluation_unavailable", str(error), FailureKind.STATE_CONFLICT)
        except EvaluationConflict as error:
            return _failure(context, EDIT_CASE.id, "evaluation_conflict", str(error), FailureKind.BUSINESS)
        return OperationOutcome(
            outcome="edited", delivery_phase=DeliveryPhase.RESPONSE_RECEIVED
        )


@dataclass(frozen=True)
class DeleteCaseHandler:
    service: EvaluationService
    owner_scope: AgentOwnerScopeGateway

    async def __call__(self, arguments, context: ExecutionContext) -> OperationOutcome:
        try:
            payload = DeleteEvaluationCaseArguments.model_validate(dict(arguments))
            owner = await self.owner_scope.organization_id_for_route(context.session_id)
            agent_id = uuid.UUID(context.private_entity_id("agent_ref"))
            await self.service.remove_case(
                owner, agent_id, case_id=payload.case_id,
                expected_revision=payload.expected_revision,
            )
        except (ValidationError, ValueError, KeyError) as error:
            return _failure(context, DELETE_CASE.id, "invalid_evaluation_delete", str(error), FailureKind.CONTRACT)
        except (EvaluationUnavailable, AgentOwnerScopeUnavailable) as error:
            return _failure(context, DELETE_CASE.id, "evaluation_unavailable", str(error), FailureKind.STATE_CONFLICT)
        except EvaluationConflict as error:
            return _failure(context, DELETE_CASE.id, "evaluation_conflict", str(error), FailureKind.BUSINESS)
        return OperationOutcome(
            outcome="removed", delivery_phase=DeliveryPhase.RESPONSE_RECEIVED
        )


def _failure(context, operation_id, code, message, kind):
    return OperationOutcome(delivery_phase=DeliveryPhase.NOT_SENT, failure=RouteDeckFailure(
        kind=kind, code=code, phase="evaluation_service", correlation_id=context.attempt_id,
        operation_id=operation_id, request_id=context.request_id,
        public_message=message,
        safe_details=FailureSafeDetails(delivery_phase=DeliveryPhase.NOT_SENT.value),
    ))
