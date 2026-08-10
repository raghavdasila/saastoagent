from __future__ import annotations

import asyncio
from dataclasses import dataclass

from routedeck_core.contracts.failures import FailureKind, RouteDeckFailure
from routedeck_core.supervision.guards import GuardDecision, GuardInvocationContext

from corpus.app.source_adapters import SourceOwnerScopeUnavailable

from .connectors.api.contract_revisions import (
    ApiContractRevisionConflict,
    ApiContractRevisionService,
)
from .connectors.api.connection_checks import (
    ApiConnectionCheckConflict,
    ApiConnectionCheckError,
    ApiConnectionCheckService,
)
from .connectors.api.connections import ApiConnectionError
from .connectors.api.operation_curation import (
    ApiOperationCurationConflict,
    ApiOperationCurationError,
    ApiOperationCurationService,
)
from .connectors.api.routed_executions import (
    ApiRoutedExecutionConflict,
    ApiRoutedExecutionError,
    ApiRoutedExecutionService,
)
from .connectors.api.route_plans import ApiRoutePlanConflict, ApiRoutePlanError
from .schemas import (
    ExecuteRoutedApiArguments,
    SaveApiOperationCurationArguments,
    TestApiConnectionArguments,
    save_api_operation_curation_arguments,
)
from pydantic import ValidationError
from .ports import SourceOwnerScopeGateway
from .repository import SourceNotFound, SourceNotReady, SourceRepositoryError
from .service import one_current_ready_api_source


@dataclass(frozen=True)
class ContractRevisionCurrentGuard:
    service: ApiContractRevisionService
    owner_scope: SourceOwnerScopeGateway

    async def __call__(self, context: GuardInvocationContext) -> GuardDecision:
        identity = contract_proposal_private_identity(context)
        if identity is None:
            return GuardDecision.blocked(
                _failure(
                    context,
                    "contract_revision_selection_stale",
                    "Reload the exact contract proposal before continuing.",
                )
            )
        source_id, proposal_id = identity
        try:
            owner_id = await self.owner_scope.organization_id_for_route(
                context.session.session_id
            )
            await asyncio.to_thread(
                self.service.require_pending_current,
                owner_id=owner_id,
                source_id=source_id,
                proposal_id=proposal_id,
            )
        except (ApiContractRevisionConflict, SourceNotFound, SourceNotReady) as error:
            return GuardDecision.blocked(
                _failure(context, "contract_revision_stale", str(error))
            )
        except SourceRepositoryError:
            return GuardDecision.blocked(
                _failure(
                    context,
                    "contract_revision_unavailable",
                    "The reviewed API update is unavailable.",
                )
            )
        return GuardDecision.allowed_result()


@dataclass(frozen=True)
class ApiConnectionCheckCurrentGuard:
    service: ApiConnectionCheckService
    owner_scope: SourceOwnerScopeGateway

    async def __call__(self, context: GuardInvocationContext) -> GuardDecision:
        try:
            payload = TestApiConnectionArguments.model_validate(
                dict(context.request.arguments)
            )
            owner_id = await self.owner_scope.organization_id_for_route(
                context.session.session_id
            )
            if payload.source_id is None:
                source = one_current_ready_api_source(self.service.sources, owner_id)
                profiles = await asyncio.to_thread(
                    self.service.profiles.list_exact,
                    owner_key=str(owner_id),
                    source_id=source.source_id,
                    revision_id=source.revision.revision_id,
                )
                if len(profiles) != 1:
                    raise ApiConnectionCheckConflict(
                        "Connection checking requires one exact saved profile; choose the connection you mean."
                    )
                source_id = source.source_id
                source_revision_id = source.revision.revision_id
                connection_profile_id = profiles[0].id
            else:
                assert payload.source_revision_id is not None
                assert payload.connection_profile_id is not None
                source_id = payload.source_id
                source_revision_id = payload.source_revision_id
                connection_profile_id = payload.connection_profile_id
            await asyncio.to_thread(
                self.service.require_executable,
                owner_id=owner_id,
                source_id=source_id,
                source_revision_id=source_revision_id,
                connection_profile_id=connection_profile_id,
                operation_id=payload.operation_id,
            )
        except ValidationError:
            return GuardDecision.blocked(
                _failure(
                    context,
                    "api_connection_check_selection_invalid",
                    "Select one ready API revision, saved profile and safe check operation.",
                    phase="sources_api_connection_check_guard",
                )
            )
        except (ApiConnectionCheckConflict, ApiConnectionError, SourceNotFound, SourceNotReady) as error:
            return GuardDecision.blocked(
                _failure(
                    context,
                    "api_connection_check_selection_stale",
                    str(error),
                    phase="sources_api_connection_check_guard",
                )
            )
        except (ApiConnectionCheckError, SourceRepositoryError):
            return GuardDecision.blocked(
                _failure(
                    context,
                    "api_connection_check_unavailable",
                    "The safe API connection check is unavailable.",
                    phase="sources_api_connection_check_guard",
                )
            )
        return GuardDecision.allowed_result()


@dataclass(frozen=True)
class ApiOperationCurationCurrentGuard:
    service: ApiOperationCurationService
    owner_scope: SourceOwnerScopeGateway

    async def __call__(self, context: GuardInvocationContext) -> GuardDecision:
        try:
            payload = save_api_operation_curation_arguments(
                context.request.arguments,
                context.request.source,
            )
            owner_id = await self.owner_scope.organization_id_for_route(
                context.session.session_id
            )
            if payload.source_id is None:
                source = one_current_ready_api_source(self.service.sources, owner_id)
                view = await asyncio.to_thread(
                    self.service.inspect,
                    owner_id=owner_id,
                    source_id=source.source_id,
                    source_revision_id=source.revision.revision_id,
                )
                included = tuple(payload.included_operation_ids)
                included_set = set(included)
                discovered = tuple(item.operation_id for item in view.operations)
                if included_set - set(discovered):
                    raise ApiOperationCurationConflict(
                        "The requested operation selection is not in the current inspected API architecture."
                    )
                excluded = (
                    tuple(payload.excluded_operation_ids)
                    if payload.excluded_operation_ids is not None
                    else tuple(item for item in discovered if item not in included_set)
                )
                selection = {
                    "source_id": source.source_id,
                    "source_revision_id": source.revision.revision_id,
                    "inventory_fingerprint": view.inventory_fingerprint,
                    "included_operation_ids": included,
                    "excluded_operation_ids": excluded,
                    "expected_current_curation_id": (
                        view.current.id if view.current is not None else None
                    ),
                }
            else:
                selection = payload.model_dump()
            await asyncio.to_thread(
                self.service.require_current_selection,
                owner_id=owner_id,
                **selection,
            )
        except ValidationError:
            return GuardDecision.blocked(
                _failure(
                    context,
                    "api_operation_curation_selection_invalid",
                    "Review and classify every operation in the current discovered inventory.",
                    phase="sources_api_operation_curation_guard",
                )
            )
        except (ApiOperationCurationConflict, SourceNotFound, SourceNotReady) as error:
            return GuardDecision.blocked(
                _failure(
                    context,
                    "api_operation_curation_selection_stale",
                    str(error),
                    phase="sources_api_operation_curation_guard",
                )
            )
        except (ApiOperationCurationError, SourceRepositoryError):
            return GuardDecision.blocked(
                _failure(
                    context,
                    "api_operation_curation_unavailable",
                    "The discovered API operation inventory is unavailable.",
                    phase="sources_api_operation_curation_guard",
                )
            )
        return GuardDecision.allowed_result()


@dataclass(frozen=True)
class RoutedApiExecutionCurrentGuard:
    service: ApiRoutedExecutionService
    owner_scope: SourceOwnerScopeGateway
    expected_safety: str

    async def __call__(self, context: GuardInvocationContext) -> GuardDecision:
        try:
            payload = ExecuteRoutedApiArguments.model_validate(
                dict(context.request.arguments)
            )
            owner_id = await self.owner_scope.organization_id_for_route(
                context.session.session_id
            )
            location = await asyncio.to_thread(
                self.service.plans.locate,
                owner_id=owner_id,
                plan_id=payload.plan_id,
            )
            await asyncio.to_thread(
                self.service.require_variant,
                owner_id=owner_id,
                conversation_id=location.conversation_id,
                route_session_id=context.session.session_id,
                plan_id=payload.plan_id,
                expected_safety=self.expected_safety,
            )
        except ValidationError:
            return GuardDecision.blocked(
                _failure(
                    context,
                    "routed_api_plan_invalid",
                    "Select one current ready API route plan.",
                    phase="sources_routed_api_execution_guard",
                )
            )
        except (
            ApiRoutedExecutionConflict,
            ApiRoutePlanConflict,
            SourceNotFound,
            SourceNotReady,
        ) as error:
            return GuardDecision.blocked(
                _failure(
                    context,
                    "routed_api_plan_stale",
                    str(error),
                    phase="sources_routed_api_execution_guard",
                )
            )
        except SourceOwnerScopeUnavailable as error:
            return GuardDecision.blocked(
                _failure(
                    context,
                    "authentication_required",
                    str(error),
                    phase="sources_routed_api_execution_guard",
                )
            )
        except (
            ApiRoutedExecutionError,
            ApiRoutePlanError,
            SourceRepositoryError,
        ):
            return GuardDecision.blocked(
                _failure(
                    context,
                    "routed_api_execution_unavailable",
                    "The routed API operation is unavailable.",
                    phase="sources_routed_api_execution_guard",
                )
            )
        return GuardDecision.allowed_result()


def contract_proposal_private_identity(
    context: GuardInvocationContext,
) -> tuple[str, str] | None:
    matches = tuple(
        item
        for item in context.resolved_entities
        if item.argument_name == "proposal_ref"
        and item.entity_kind == "contract_revision_proposal"
    )
    if len(matches) != 1:
        return None
    value = matches[0].private_id.get_secret_value()
    source_id, separator, proposal_id = value.partition("|")
    if not separator or len(source_id) != 16 or len(proposal_id) != 16:
        return None
    return source_id, proposal_id


def _failure(
    context: GuardInvocationContext,
    code: str,
    message: str,
    *,
    phase: str = "sources_contract_revision_guard",
) -> RouteDeckFailure:
    return RouteDeckFailure(
        kind=FailureKind.GUARD,
        code=code,
        phase=phase,
        correlation_id=context.attempt_id,
        operation_id=context.request.operation_id,
        request_id=context.request.request_id,
        public_message=message,
    )


__all__ = [
    "ApiConnectionCheckCurrentGuard",
    "ApiOperationCurationCurrentGuard",
    "ContractRevisionCurrentGuard",
    "RoutedApiExecutionCurrentGuard",
    "contract_proposal_private_identity",
]
