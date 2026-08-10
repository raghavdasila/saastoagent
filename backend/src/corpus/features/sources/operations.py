from __future__ import annotations

import asyncio
from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any

from pydantic import ValidationError
from routedeck_core.contracts.failures import (
    FailureKind,
    FailureSafeDetails,
    RouteDeckFailure,
)
from routedeck_core.contracts.operations import DeliveryPhase, OperationOutcome
from routedeck_core.contracts.effects import (
    EntityBindingEffect,
    EntityKindEffects,
    PublicSurfaceEffect,
    SessionEffects,
)
from routedeck_core.contracts.projection import (
    FrozenJson,
    FrozenJsonObject,
    PublicEntityHandle,
    PublicValue,
)
from pydantic import SecretStr
from routedeck_core.ports.executor import ExecutionContext

from corpus.app.source_adapters import SourceOwnerScopeUnavailable

from corpus.shared.private_forms import EncryptedPrivateFormReader, PrivateFormError

from .connectors.api.connections import (
    ApiConnectionConflict,
    ApiConnectionError,
    ApiConnectionPrivateForm,
    ApiConnectionService,
)
from .connectors.api.connection_checks import (
    ApiConnectionCheckConflict,
    ApiConnectionCheckError,
    ApiConnectionCheckService,
)
from .connectors.api.graph import ApiGraphPresenter
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
from .connectors.api.route_plans import ApiRoutePlanConflict
from .connectors.api.contract_revisions import (
    ApiContractRevisionConflict,
    ApiContractRevisionError,
    ApiContractRevisionService,
    proposal_public_ref,
)
from .declarations import (
    API_CONNECTION_FORM_ID,
    INSPECT_CURRENT_API,
    RETRY_PROCESSING,
    SAVE_API_CONNECTION,
    SAVE_API_OPERATION_CURATION,
    SELECT_GRAPH_STAGE,
    APPROVE_CONTRACT_REVISION,
    PROPOSE_CONTRACT_REVISION,
    PREPARE_ROUTED_API_TEST,
    TEST_API_CONNECTION,
    TEST_ROUTED_API_READ,
    TEST_ROUTED_API_WRITE,
)
from .ports import SourceOwnerScopeGateway
from .repository import SourceNotFound, SourceNotReady, SourceRepositoryError
from .schemas import (
    ApproveContractRevisionArguments,
    GraphStageArguments,
    ProposeContractRevisionArguments,
    RetrySourceArguments,
    SaveApiOperationCurationArguments,
    TestApiConnectionArguments,
    ExecuteRoutedApiArguments,
    save_api_operation_curation_arguments,
)
from .service import SourceService, one_current_ready_api_source


class SourcesNavigationHandler:
    def __init__(self, operation_id: str) -> None:
        self.operation_id = operation_id

    async def __call__(self, arguments, context) -> OperationOutcome:
        del context
        if arguments:
            raise ValueError(f"{self.operation_id} accepts no arguments")
        return _success("opened")


class OpenApiRoutePlanHandler:
    async def __call__(self, arguments, context) -> OperationOutcome:
        del context
        if arguments:
            raise ValueError(f"{PREPARE_ROUTED_API_TEST.id} accepts no arguments")
        return _success(
            "opened",
            effects=SessionEffects(
                surface_updates=(
                    PublicSurfaceEffect(
                        surface_id="sources.api_operation_test",
                        values=(PublicValue(name="open", value=FrozenJson(True)),),
                    ),
                ),
            ),
        )


@dataclass(frozen=True)
class InspectCurrentApiHandler:
    graph: ApiGraphPresenter
    curations: ApiOperationCurationService
    connection_checks: object
    owner_scope: SourceOwnerScopeGateway

    async def __call__(
        self,
        arguments: Mapping[str, Any],
        context: ExecutionContext,
    ) -> OperationOutcome:
        if arguments:
            return _failure(
                context,
                INSPECT_CURRENT_API.id,
                "invalid_api_architecture_inspection",
                "API architecture inspection does not accept user-supplied identities.",
                FailureKind.CONTRACT,
            )
        try:
            owner_id = await self.owner_scope.organization_id_for_route(
                context.session_id
            )
            source = one_current_ready_api_source(self.curations.sources, owner_id)
            graph = await asyncio.to_thread(
                self.graph.inspect,
                owner_key=str(owner_id),
                source_id=source.source_id,
            )
            curation = await asyncio.to_thread(
                self.curations.inspect,
                owner_id=owner_id,
                source_id=source.source_id,
                source_revision_id=source.revision.revision_id,
            )
            profiles = await asyncio.to_thread(
                self.connection_checks.profiles.list_exact,
                owner_key=str(owner_id),
                source_id=source.source_id,
                revision_id=source.revision.revision_id,
            )
        except (SourceNotFound, SourceNotReady, ApiOperationCurationConflict) as error:
            return _failure(
                context,
                INSPECT_CURRENT_API.id,
                "api_architecture_selection_required",
                str(error),
                FailureKind.STATE_CONFLICT,
            )
        except SourceOwnerScopeUnavailable as error:
            return _failure(
                context,
                INSPECT_CURRENT_API.id,
                "authentication_required",
                str(error),
                FailureKind.STATE_CONFLICT,
            )
        except (ApiOperationCurationError, ApiConnectionError, SourceRepositoryError):
            return _failure(
                context,
                INSPECT_CURRENT_API.id,
                "api_architecture_unavailable",
                "The current API architecture could not be inspected.",
                FailureKind.PERSISTENCE,
            )
        return OperationOutcome(
            outcome="inspected",
            delivery_phase=DeliveryPhase.RESPONSE_RECEIVED,
            observation=FrozenJsonObject({
                "source_id": source.source_id,
                "source_revision_id": source.revision.revision_id,
                "revision_kind": str(
                    source.revision.summary.get("revision_kind", "processed_api")
                ),
                "semantic_groups": [
                    {
                        "label": group.label,
                        "operation_ids": list(
                            graph.operation_ids_for_group(group)
                        ),
                    }
                    for group in graph.semantic_groups
                ],
                "operations": [
                    {
                        "operation_id": item.operation_id,
                        "method": item.method,
                        "path_template": item.path_template,
                    }
                    for item in curation.operations
                ],
                "saved_profile_count": len(profiles),
                "current_included_operation_ids": (
                    []
                    if curation.current is None
                    else list(curation.current.included_operation_ids)
                ),
            }),
        )


@dataclass(frozen=True)
class RoutedApiExecutionHandler:
    service: ApiRoutedExecutionService
    owner_scope: SourceOwnerScopeGateway
    expected_safety: str

    async def __call__(
        self,
        arguments: Mapping[str, Any],
        context: ExecutionContext,
    ) -> OperationOutcome:
        operation = (
            TEST_ROUTED_API_READ
            if self.expected_safety == "read"
            else TEST_ROUTED_API_WRITE
        )
        try:
            payload = ExecuteRoutedApiArguments.model_validate(dict(arguments))
            owner_id = await self.owner_scope.organization_id_for_route(context.session_id)
            location = await asyncio.to_thread(
                self.service.plans.locate,
                owner_id=owner_id,
                plan_id=payload.plan_id,
            )
            result = await self.service.execute(
                owner_id=owner_id,
                conversation_id=location.conversation_id,
                route_session_id=context.session_id,
                plan_id=payload.plan_id,
                expected_safety=self.expected_safety,  # type: ignore[arg-type]
                request_id=context.request_id,
                approved_write=self.expected_safety == "write",
            )
        except ValidationError:
            return _failure(
                context,
                operation.id,
                "routed_api_plan_invalid",
                "Select one current ready API route plan.",
                FailureKind.CONTRACT,
            )
        except (ApiRoutedExecutionConflict, ApiRoutePlanConflict, SourceNotFound, SourceNotReady) as error:
            return _failure(
                context,
                operation.id,
                "routed_api_plan_stale",
                str(error),
                FailureKind.STATE_CONFLICT,
            )
        except SourceOwnerScopeUnavailable as error:
            return _failure(
                context,
                operation.id,
                "authentication_required",
                str(error),
                FailureKind.STATE_CONFLICT,
            )
        except (ApiRoutedExecutionError, SourceRepositoryError):
            return _failure(
                context,
                operation.id,
                "routed_api_execution_unavailable",
                "The routed API operation is unavailable.",
                FailureKind.PERSISTENCE,
            )
        delivery = {
            "not_sent": DeliveryPhase.NOT_SENT,
            "possibly_sent": DeliveryPhase.POSSIBLY_SENT,
            "response_received": DeliveryPhase.RESPONSE_RECEIVED,
        }[result.delivery]
        if result.status == "succeeded":
            return OperationOutcome(
                outcome="observed",
                delivery_phase=delivery,
            )
        unknown = result.status == "outcome_unknown"
        return OperationOutcome(
            delivery_phase=delivery,
            failure=RouteDeckFailure(
                kind=(
                    FailureKind.EXTERNAL_OUTCOME_UNKNOWN
                    if unknown
                    else FailureKind.BUSINESS
                ),
                code=(
                    "external_outcome_unknown"
                    if unknown
                    else result.error_code or "routed_api_execution_failed"
                ),
                phase="sources_routed_api_execution",
                correlation_id=context.attempt_id,
                operation_id=operation.id,
                request_id=context.request_id,
                public_message=(
                    "The external write outcome is uncertain. Do not submit it again; prepare a new plan after verifying the external state."
                    if unknown
                    else result.public_message or "The routed API operation failed."
                ),
                recovery_directive=(
                    "Verify the external system before preparing a new route plan. Never retry this plan."
                    if unknown
                    else None
                ),
                safe_details=FailureSafeDetails(
                    provider="api",
                    provider_code=result.error_code,
                    http_status=result.status_code,
                    delivery_phase=delivery.value,
                ),
            ),
        )


@dataclass(frozen=True)
class GraphStageSelectionHandler:
    presenter: ApiGraphPresenter
    owner_scope: SourceOwnerScopeGateway

    async def __call__(
        self,
        arguments: Mapping[str, Any],
        context: ExecutionContext,
    ) -> OperationOutcome:
        try:
            payload = GraphStageArguments.model_validate(dict(arguments))
            organization_id = await self.owner_scope.organization_id_for_route(
                context.session_id
            )
            await asyncio.to_thread(
                self.presenter.inspect_stage,
                owner_key=str(organization_id),
                source_id=payload.source_id,
                revision_id=payload.revision_id,
                stage_id=payload.stage_id,
            )
        except ValidationError as error:
            return _failure(
                context,
                SELECT_GRAPH_STAGE.id,
                "invalid_graph_stage_selection",
                str(error),
                FailureKind.CONTRACT,
            )
        except (SourceNotFound, SourceNotReady) as error:
            return _failure(
                context,
                SELECT_GRAPH_STAGE.id,
                "graph_stage_unavailable",
                str(error),
                FailureKind.BUSINESS,
            )
        except SourceOwnerScopeUnavailable as error:
            return _failure(
                context,
                SELECT_GRAPH_STAGE.id,
                "authentication_required",
                str(error),
                FailureKind.STATE_CONFLICT,
            )
        except Exception:
            return _failure(
                context,
                SELECT_GRAPH_STAGE.id,
                "graph_stage_inspection_unavailable",
                "The recorded graph stage could not be inspected.",
                FailureKind.PERSISTENCE,
            )
        return _success("selected")


@dataclass(frozen=True)
class RetrySourceProcessingHandler:
    service: SourceService
    owner_scope: SourceOwnerScopeGateway

    async def __call__(
        self,
        arguments: Mapping[str, Any],
        context: ExecutionContext,
    ) -> OperationOutcome:
        try:
            payload = RetrySourceArguments.model_validate(dict(arguments))
            organization_id = await self.owner_scope.organization_id_for_route(
                context.session_id
            )
            await self.service.retry_processing(
                owner_id=organization_id,
                source_id=payload.source_id,
            )
        except (ValidationError, ValueError) as error:
            return _failure(
                context,
                RETRY_PROCESSING.id,
                "invalid_source_retry",
                str(error),
                FailureKind.CONTRACT,
            )
        except SourceNotFound as error:
            return _failure(
                context,
                RETRY_PROCESSING.id,
                "source_unavailable",
                str(error),
                FailureKind.BUSINESS,
            )
        except (SourceNotReady, SourceRepositoryError) as error:
            return _failure(
                context,
                RETRY_PROCESSING.id,
                "source_retry_conflict",
                str(error),
                FailureKind.STATE_CONFLICT,
            )
        except SourceOwnerScopeUnavailable as error:
            return _failure(
                context,
                RETRY_PROCESSING.id,
                "authentication_required",
                str(error),
                FailureKind.STATE_CONFLICT,
            )
        except Exception:
            return _failure(
                context,
                RETRY_PROCESSING.id,
                "source_retry_unavailable",
                "Source processing retry is unavailable.",
                FailureKind.PERSISTENCE,
            )
        return _success("queued")


@dataclass(frozen=True)
class SaveApiConnectionHandler:
    service: ApiConnectionService
    owner_scope: SourceOwnerScopeGateway
    private_forms: EncryptedPrivateFormReader

    async def __call__(
        self,
        arguments: Mapping[str, Any],
        context: ExecutionContext,
    ) -> OperationOutcome:
        if arguments:
            return _failure(
                context,
                SAVE_API_CONNECTION.id,
                "invalid_api_connection_save",
                "Connection values must be submitted through the protected form.",
                FailureKind.CONTRACT,
            )
        try:
            owner_id = await self.owner_scope.organization_id_for_route(
                context.session_id
            )
            value = await self.private_forms.load(
                context.session_id,
                API_CONNECTION_FORM_ID,
                ApiConnectionPrivateForm,
            )
            await self.service.save(owner_id=owner_id, value=value)
        except PrivateFormError as error:
            return _failure(
                context,
                SAVE_API_CONNECTION.id,
                error.code,
                error.public_message,
                FailureKind.CONTRACT,
            )
        except ApiConnectionConflict as error:
            return _failure(
                context,
                SAVE_API_CONNECTION.id,
                "api_connection_conflict",
                str(error),
                FailureKind.STATE_CONFLICT,
            )
        except (SourceNotFound, SourceNotReady) as error:
            return _failure(
                context,
                SAVE_API_CONNECTION.id,
                "api_source_unavailable",
                str(error),
                FailureKind.BUSINESS,
            )
        except SourceOwnerScopeUnavailable as error:
            return _failure(
                context,
                SAVE_API_CONNECTION.id,
                "authentication_required",
                str(error),
                FailureKind.STATE_CONFLICT,
            )
        except ApiConnectionError:
            return _failure(
                context,
                SAVE_API_CONNECTION.id,
                "api_connection_persistence_failed",
                "The API connection profile could not be saved.",
                FailureKind.PERSISTENCE,
            )
        except Exception:
            return _failure(
                context,
                SAVE_API_CONNECTION.id,
                "api_connection_save_unavailable",
                "The API connection profile could not be saved.",
                FailureKind.PERSISTENCE,
            )
        return OperationOutcome(
            outcome="saved",
            delivery_phase=DeliveryPhase.RESPONSE_RECEIVED,
            effects=SessionEffects(
                remove_private_form_ids=(API_CONNECTION_FORM_ID,)
            ),
        )


@dataclass(frozen=True)
class TestApiConnectionHandler:
    service: ApiConnectionCheckService
    owner_scope: SourceOwnerScopeGateway

    async def __call__(
        self,
        arguments: Mapping[str, Any],
        context: ExecutionContext,
    ) -> OperationOutcome:
        try:
            payload = TestApiConnectionArguments.model_validate(dict(arguments))
            owner_id = await self.owner_scope.organization_id_for_route(
                context.session_id
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
                        "Connection checking requires one exact saved profile; select it in Source Hub."
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
            record = await self.service.execute(
                owner_id=owner_id,
                source_id=source_id,
                source_revision_id=source_revision_id,
                connection_profile_id=connection_profile_id,
                operation_id=payload.operation_id,
            )
        except ValidationError:
            return _failure(
                context,
                TEST_API_CONNECTION.id,
                "invalid_api_connection_check",
                "Select one ready API revision, saved profile and safe check operation.",
                FailureKind.CONTRACT,
            )
        except (ApiConnectionCheckConflict, ApiConnectionError, SourceNotFound, SourceNotReady) as error:
            return _failure(
                context,
                TEST_API_CONNECTION.id,
                "api_connection_check_selection_stale",
                str(error),
                FailureKind.STATE_CONFLICT,
            )
        except SourceOwnerScopeUnavailable as error:
            return _failure(
                context,
                TEST_API_CONNECTION.id,
                "authentication_required",
                str(error),
                FailureKind.STATE_CONFLICT,
            )
        except (ApiConnectionCheckError, SourceRepositoryError):
            return _failure(
                context,
                TEST_API_CONNECTION.id,
                "api_connection_check_unavailable",
                "The safe API connection check is unavailable.",
                FailureKind.PERSISTENCE,
            )
        if record.status != "succeeded":
            phase = (
                DeliveryPhase.RESPONSE_RECEIVED
                if record.http_call_count == 1
                else DeliveryPhase.NOT_SENT
            )
            return OperationOutcome(
                delivery_phase=phase,
                failure=RouteDeckFailure(
                    kind=FailureKind.BUSINESS,
                    code="api_connection_check_failed",
                    phase="sources_service",
                    correlation_id=context.attempt_id,
                    operation_id=TEST_API_CONNECTION.id,
                    request_id=context.request_id,
                    public_message=(
                        record.public_message
                        or "The API connection check failed. Review the saved profile before trying again."
                    ),
                    safe_details=FailureSafeDetails(delivery_phase=phase.value),
                ),
            )
        return _success("checked")


@dataclass(frozen=True)
class SaveApiOperationCurationHandler:
    service: ApiOperationCurationService
    owner_scope: SourceOwnerScopeGateway

    async def __call__(
        self,
        arguments: Mapping[str, Any],
        context: ExecutionContext,
    ) -> OperationOutcome:
        try:
            payload = save_api_operation_curation_arguments(
                arguments,
                context.source,
            )
            owner_id = await self.owner_scope.organization_id_for_route(
                context.session_id
            )
            if payload.source_id is None:
                source = one_current_ready_api_source(self.service.sources, owner_id)
                view = await asyncio.to_thread(
                    self.service.inspect,
                    owner_id=owner_id,
                    source_id=source.source_id,
                    source_revision_id=source.revision.revision_id,
                )
                discovered = tuple(item.operation_id for item in view.operations)
                included = tuple(payload.included_operation_ids)
                included_set = set(included)
                unknown = included_set - set(discovered)
                if unknown:
                    raise ApiOperationCurationConflict(
                        "The requested operation selection is not in the current inspected API architecture."
                    )
                excluded = (
                    tuple(payload.excluded_operation_ids)
                    if payload.excluded_operation_ids is not None
                    else tuple(item for item in discovered if item not in included_set)
                )
                save_arguments = {
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
                assert payload.source_revision_id is not None
                assert payload.inventory_fingerprint is not None
                assert payload.excluded_operation_ids is not None
                save_arguments = {
                    "source_id": payload.source_id,
                    "source_revision_id": payload.source_revision_id,
                    "inventory_fingerprint": payload.inventory_fingerprint,
                    "included_operation_ids": payload.included_operation_ids,
                    "excluded_operation_ids": payload.excluded_operation_ids,
                    "expected_current_curation_id": payload.expected_current_curation_id,
                }
            await asyncio.to_thread(
                self.service.save,
                owner_id=owner_id,
                **save_arguments,
            )
        except ValidationError:
            return _failure(
                context,
                SAVE_API_OPERATION_CURATION.id,
                "invalid_api_operation_curation",
                "Review and classify every operation in the current discovered inventory.",
                FailureKind.CONTRACT,
            )
        except (ApiOperationCurationConflict, SourceNotFound, SourceNotReady) as error:
            return _failure(
                context,
                SAVE_API_OPERATION_CURATION.id,
                "api_operation_curation_stale",
                str(error),
                FailureKind.STATE_CONFLICT,
            )
        except SourceOwnerScopeUnavailable as error:
            return _failure(
                context,
                SAVE_API_OPERATION_CURATION.id,
                "authentication_required",
                str(error),
                FailureKind.STATE_CONFLICT,
            )
        except (ApiOperationCurationError, SourceRepositoryError):
            return _failure(
                context,
                SAVE_API_OPERATION_CURATION.id,
                "api_operation_curation_unavailable",
                "The API operation curation could not be saved.",
                FailureKind.PERSISTENCE,
            )
        return _success("saved")


@dataclass(frozen=True)
class ProposeContractRevisionHandler:
    service: ApiContractRevisionService
    owner_scope: SourceOwnerScopeGateway

    async def __call__(
        self,
        arguments: Mapping[str, Any],
        context: ExecutionContext,
    ) -> OperationOutcome:
        try:
            payload = ProposeContractRevisionArguments.model_validate(dict(arguments))
            owner_id = await self.owner_scope.organization_id_for_route(
                context.session_id
            )
            if payload.source_id is None:
                source = one_current_ready_api_source(self.service.repository, owner_id)
                source_id = source.source_id
                revision_id = source.revision.revision_id
            else:
                assert payload.revision_id is not None
                source_id = payload.source_id
                revision_id = payload.revision_id
            proposal = await asyncio.to_thread(
                self.service.propose,
                owner_id=owner_id,
                source_id=source_id,
                parent_revision_id=revision_id,
            )
        except ValidationError as error:
            return _failure(
                context,
                PROPOSE_CONTRACT_REVISION.id,
                "invalid_contract_revision_proposal",
                str(error),
                FailureKind.CONTRACT,
            )
        except (ApiContractRevisionConflict, SourceNotReady) as error:
            return _failure(
                context,
                PROPOSE_CONTRACT_REVISION.id,
                "contract_revision_conflict",
                str(error),
                FailureKind.STATE_CONFLICT,
            )
        except SourceNotFound as error:
            return _failure(
                context,
                PROPOSE_CONTRACT_REVISION.id,
                "source_unavailable",
                str(error),
                FailureKind.BUSINESS,
            )
        except SourceOwnerScopeUnavailable as error:
            return _failure(
                context,
                PROPOSE_CONTRACT_REVISION.id,
                "authentication_required",
                str(error),
                FailureKind.STATE_CONFLICT,
            )
        except (ApiContractRevisionError, SourceRepositoryError):
            return _failure(
                context,
                PROPOSE_CONTRACT_REVISION.id,
                "contract_revision_proposal_unavailable",
                "The reviewed contract proposal could not be prepared.",
                FailureKind.PERSISTENCE,
            )
        proposal_ref = proposal_public_ref(proposal.proposal_id)
        shared_impact = max(item.impact_count for item in proposal.patches)
        effects = SessionEffects(
            replace_entities=(
                EntityKindEffects(
                    entity_kind="contract_revision_proposal",
                    bindings=(
                        EntityBindingEffect(
                            public=PublicEntityHandle(
                                entity_kind="contract_revision_proposal",
                                handle=proposal_ref,
                                values=(
                                    PublicValue(
                                        name="final_hash",
                                        value=FrozenJson(proposal.final_canonical_sha256),
                                    ),
                                    PublicValue(
                                        name="shared_schema_impact_count",
                                        value=FrozenJson(shared_impact),
                                    ),
                                ),
                            ),
                            private_id=SecretStr(
                                f"{proposal.source_id}|{proposal.proposal_id}"
                            ),
                            allowed_operation_ids=(APPROVE_CONTRACT_REVISION.id,),
                        ),
                    ),
                ),
            ),
            surface_updates=(
                PublicSurfaceEffect(
                    surface_id="sources.contract_revision_proposal",
                    values=(
                        PublicValue(
                            name="source_id", value=FrozenJson(proposal.source_id)
                        ),
                        PublicValue(
                            name="proposal_ref", value=FrozenJson(proposal_ref)
                        ),
                    ),
                ),
            ),
        )
        return _success(
            "proposed",
            effects=effects,
            observation={
                "proposal_state": "proposal_prepared",
                "review_staged": False,
                "next_owner_decision": "request_owner_review",
            },
        )


@dataclass(frozen=True)
class ApproveContractRevisionHandler:
    service: ApiContractRevisionService
    owner_scope: SourceOwnerScopeGateway

    async def __call__(
        self,
        arguments: Mapping[str, Any],
        context: ExecutionContext,
    ) -> OperationOutcome:
        try:
            ApproveContractRevisionArguments.model_validate(dict(arguments))
            private_identity = context.private_entity_id("proposal_ref")
            source_id, separator, proposal_id = private_identity.partition("|")
            if not separator or len(source_id) != 16 or len(proposal_id) != 16:
                raise ValueError("The exact contract proposal binding is invalid.")
            owner_id = await self.owner_scope.organization_id_for_route(
                context.session_id
            )
            await asyncio.to_thread(
                self.service.approve,
                owner_id=owner_id,
                source_id=source_id,
                proposal_id=proposal_id,
            )
        except (ValidationError, ValueError, KeyError) as error:
            return _failure(
                context,
                APPROVE_CONTRACT_REVISION.id,
                "invalid_contract_revision_selection",
                str(error),
                FailureKind.CONTRACT,
            )
        except (ApiContractRevisionConflict, SourceNotReady) as error:
            return _failure(
                context,
                APPROVE_CONTRACT_REVISION.id,
                "contract_revision_stale",
                str(error),
                FailureKind.STATE_CONFLICT,
            )
        except SourceNotFound as error:
            return _failure(
                context,
                APPROVE_CONTRACT_REVISION.id,
                "contract_revision_unavailable",
                str(error),
                FailureKind.BUSINESS,
            )
        except SourceOwnerScopeUnavailable as error:
            return _failure(
                context,
                APPROVE_CONTRACT_REVISION.id,
                "authentication_required",
                str(error),
                FailureKind.STATE_CONFLICT,
            )
        except (ApiContractRevisionError, SourceRepositoryError):
            return _failure(
                context,
                APPROVE_CONTRACT_REVISION.id,
                "contract_revision_approval_unavailable",
                "The reviewed contract revision could not be created.",
                FailureKind.PERSISTENCE,
            )
        return _success(
            "approved",
            effects=SessionEffects(
                replace_entities=(
                    EntityKindEffects(entity_kind="contract_revision_proposal"),
                ),
                surface_updates=(
                    PublicSurfaceEffect(
                        surface_id="sources.contract_revision_proposal"
                    ),
                    PublicSurfaceEffect(
                        surface_id="sources.contract_revision_review"
                    ),
                ),
            ),
        )


def _success(
    outcome: str,
    *,
    effects: SessionEffects | None = None,
    observation: Mapping[str, Any] | None = None,
) -> OperationOutcome:
    return OperationOutcome(
        outcome=outcome,
        delivery_phase=DeliveryPhase.RESPONSE_RECEIVED,
        effects=effects or SessionEffects(),
        observation=FrozenJsonObject(observation or {}),
    )


def _failure(context, operation_id, code, message, kind) -> OperationOutcome:
    return OperationOutcome(
        delivery_phase=DeliveryPhase.NOT_SENT,
        failure=RouteDeckFailure(
            kind=kind,
            code=code,
            phase="sources_service",
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
    "ApproveContractRevisionHandler",
    "GraphStageSelectionHandler",
    "InspectCurrentApiHandler",
    "OpenApiRoutePlanHandler",
    "RoutedApiExecutionHandler",
    "ProposeContractRevisionHandler",
    "RetrySourceProcessingHandler",
    "SaveApiConnectionHandler",
    "SaveApiOperationCurationHandler",
    "TestApiConnectionHandler",
    "SourcesNavigationHandler",
]
