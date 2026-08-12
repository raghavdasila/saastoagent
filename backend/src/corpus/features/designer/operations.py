from __future__ import annotations

import uuid
from dataclasses import dataclass

from pydantic import ValidationError
from routedeck_core.contracts.failures import FailureKind, FailureSafeDetails, RouteDeckFailure
from routedeck_core.contracts.operations import DeliveryPhase, OperationOutcome
from routedeck_core.ports.executor import ExecutionContext

from corpus.features.agents.ports import AgentOwnerScopeGateway, AgentOwnerScopeUnavailable

from .declarations import APPROVE_DESIGN, CUSTOMIZE_DESIGN, GENERATE_FEATURE, PROPOSE_DESIGN, REQUEST_BUILD
from .ports import DesignerConflict, DesignerUnavailable
from .schemas import CustomizeDesignArguments, DesignerAgentArguments, GenerateFeatureArguments, RequestBuildArguments, ReviewDesignArguments
from .service import DesignerService


@dataclass(frozen=True)
class DesignerHandler:
    service: DesignerService
    owner_scope: AgentOwnerScopeGateway
    operation_id: str

    async def __call__(self, arguments, context: ExecutionContext) -> OperationOutcome:
        try:
            organization_id = await self.owner_scope.organization_id_for_route(context.session_id)
            agent_id = uuid.UUID(context.private_entity_id("agent_ref"))
            if self.operation_id == PROPOSE_DESIGN.id:
                DesignerAgentArguments.model_validate(dict(arguments))
                await self.service.propose(organization_id, agent_id)
                outcome = "proposed"
            elif self.operation_id == GENERATE_FEATURE.id:
                payload = GenerateFeatureArguments.model_validate(dict(arguments))
                current = payload.expected_revision_id
                if current is None:
                    current = (await self.service.get(organization_id, agent_id)).current_revision_id
                await self.service.generate_feature(
                    organization_id,
                    agent_id,
                    expected_revision_id=current,
                    description=payload.description,
                )
                outcome = "generated"
            elif self.operation_id == CUSTOMIZE_DESIGN.id:
                payload = CustomizeDesignArguments.model_validate(dict(arguments))
                current = payload.expected_revision_id
                if current is None:
                    current = (await self.service.get(organization_id, agent_id)).current_revision_id
                await self.service.customize(organization_id, agent_id, expected_revision_id=current, content=payload.content)
                outcome = "customized"
            elif self.operation_id == APPROVE_DESIGN.id:
                payload = ReviewDesignArguments.model_validate(dict(arguments))
                current = payload.expected_revision_id
                if current is None:
                    current = (await self.service.get(organization_id, agent_id)).current_revision_id
                await self.service.accept(organization_id, agent_id, expected_revision_id=current)
                outcome = "accepted"
            elif self.operation_id == REQUEST_BUILD.id:
                payload = RequestBuildArguments.model_validate(dict(arguments))
                accepted = payload.accepted_revision_id
                if accepted is None:
                    accepted = (await self.service.get(organization_id, agent_id)).accepted_revision_id
                if accepted is None:
                    raise DesignerConflict("The selected Agent has no accepted design.")
                await self.service.request_build(organization_id, agent_id, accepted_revision_id=accepted)
                outcome = "requested"
            else:
                raise ValueError("Unsupported Designer operation.")
        except (ValidationError, ValueError, KeyError) as error:
            return _failure(context, self.operation_id, "invalid_designer_request", str(error), FailureKind.CONTRACT)
        except DesignerUnavailable as error:
            return _failure(context, self.operation_id, "designer_unavailable", str(error), FailureKind.BUSINESS)
        except DesignerConflict as error:
            return _failure(context, self.operation_id, "designer_conflict", str(error), FailureKind.STATE_CONFLICT)
        except AgentOwnerScopeUnavailable as error:
            return _failure(context, self.operation_id, "authentication_required", str(error), FailureKind.STATE_CONFLICT)
        return OperationOutcome(outcome=outcome, delivery_phase=DeliveryPhase.RESPONSE_RECEIVED)


def _failure(context, operation_id, code, message, kind):
    return OperationOutcome(
        delivery_phase=DeliveryPhase.NOT_SENT,
        failure=RouteDeckFailure(
            kind=kind,
            code=code,
            phase="designer_service",
            correlation_id=context.attempt_id,
            operation_id=operation_id,
            request_id=context.request_id,
            public_message=message,
            safe_details=FailureSafeDetails(delivery_phase=DeliveryPhase.NOT_SENT.value),
        ),
    )
