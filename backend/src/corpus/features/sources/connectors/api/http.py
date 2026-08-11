from __future__ import annotations

from typing import Annotated, Any, Mapping
from uuid import UUID

from fastapi import APIRouter, Body, File, Form, Query, Request, UploadFile
from pydantic import BaseModel, ConfigDict, Field
from routedeck_fastapi import SameOriginMutationPolicy

from corpus.auth.config import AuthSettings
from corpus.auth.selector import bearer_token, conversation_id
from corpus.auth.service import ConversationUnavailable, SessionUnavailable

from ...http_common import (
    OwnerSessionResolver,
    SourceHttpProblem,
    authorize_mutation,
    call_source_service,
    owner_key,
    source_response,
)
from ...service import SourceService
from ..base import SourceUpload
from .intake import SourceUploadError
from .connections import ApiConnectionError, ApiConnectionProfileRepository
from .graph import ApiGraphPresenter
from .contract_revisions import (
    ApiContractRevisionConflict,
    ApiContractRevisionService,
)
from .connection_checks import ApiConnectionCheckError, ApiConnectionCheckService
from .operation_curation import ApiOperationCurationError, ApiOperationCurationService
from .route_plans import ApiRoutePlanConflict, ApiRoutePlanError, ApiRoutePlanService
from .routed_executions import (
    ApiRoutedExecutionConflict,
    ApiRoutedExecutionError,
    ApiRoutedExecutionService,
)
from .staged_attachments import (
    ApiStagedAttachmentError,
    ApiStagedAttachmentService,
)
from .staged_descriptions import (
    ApiStagedDescriptionError,
    ApiStagedDescriptionService,
)


class CreateApiRoutePlanRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    source_revision_id: str = Field(min_length=16, max_length=16)
    profile_id: str = Field(min_length=16, max_length=16)
    curation_id: str = Field(min_length=16, max_length=16)
    request_text: str = Field(min_length=1, max_length=4_000)
    provided_inputs: Mapping[str, Any] = Field(default_factory=dict)


class ClarifyApiRoutePlanRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    source_revision_id: str = Field(min_length=16, max_length=16)
    expected_record_id: str = Field(min_length=16, max_length=16)
    answers: Mapping[str, Any]


def create_api_source_router(
    *,
    service: SourceService,
    auth_service: OwnerSessionResolver,
    auth_settings: AuthSettings,
    mutation_policy: SameOriginMutationPolicy,
    max_upload_bytes: int,
    graph_presenter: ApiGraphPresenter,
    connection_profiles: ApiConnectionProfileRepository,
    contract_revision_service: ApiContractRevisionService,
    connection_check_service: ApiConnectionCheckService,
    operation_curation_service: ApiOperationCurationService,
    route_plan_service: ApiRoutePlanService,
    routed_execution_service: ApiRoutedExecutionService | None = None,
    staged_attachment_service: ApiStagedAttachmentService | None = None,
    staged_description_service: ApiStagedDescriptionService | None = None,
) -> APIRouter:
    if max_upload_bytes <= 0:
        raise ValueError("API source upload limit must be positive.")
    router = APIRouter(prefix="/api/sources", tags=["owner-api-sources"])

    @router.post("/api/attachments", status_code=201)
    async def stage_api_definition(
        request: Request,
        name: Annotated[str, Form(min_length=1, max_length=128)],
        file: Annotated[UploadFile, File()],
        description: Annotated[UploadFile | None, File()] = None,
    ):
        if staged_attachment_service is None:
            raise SourceHttpProblem(
                500,
                "staged_api_definition_unavailable",
                "API definition staging is unavailable.",
            )
        authorize_mutation(request, mutation_policy)
        current_owner, selected = await _planning_session(
            request, auth_service, auth_settings
        )
        content = await file.read(max_upload_bytes + 1)
        description_content: bytes | None = None
        description_filename: str | None = None
        description_content_type: str | None = None
        if description is not None:
            description_content = await description.read(
                min(max_upload_bytes, 1024 * 1024) + 1
            )
            description_filename = description.filename or ""
            description_content_type = (
                description.content_type or "application/octet-stream"
            )
            await description.close()
        await file.close()
        if len(content) > max_upload_bytes:
            raise SourceHttpProblem(
                413,
                "api_collection_too_large",
                "The API collection exceeds the configured upload limit.",
            )
        try:
            result = await call_source_service(
                staged_attachment_service.stage,
                owner_key=current_owner,
                conversation_id=selected.public_id,
                route_session_id=selected.route_session_id,
                display_name=name,
                upload=SourceUpload(
                    filename=file.filename or "",
                    content_type=(
                        file.content_type or "application/octet-stream"
                    ),
                    content=content,
                    description_filename=description_filename,
                    description_content_type=description_content_type,
                    description_content=description_content,
                ),
            )
        except SourceUploadError as error:
            raise SourceHttpProblem(
                400,
                "invalid_api_collection_upload",
                str(error),
            ) from error
        except ApiStagedAttachmentError as error:
            raise SourceHttpProblem(
                500,
                "staged_api_definition_unavailable",
                "The API definition could not be staged.",
            ) from error
        return source_response(result, status_code=201)

    @router.get("/api/attachments/current")
    async def current_staged_api_definition(request: Request):
        if staged_attachment_service is None:
            raise SourceHttpProblem(
                500,
                "staged_api_definition_unavailable",
                "The attached API definition is unavailable.",
            )
        current_owner, selected = await _planning_session(
            request, auth_service, auth_settings
        )
        try:
            result = await call_source_service(
                staged_attachment_service.current,
                owner_key=current_owner,
                conversation_id=selected.public_id,
                route_session_id=selected.route_session_id,
            )
        except ApiStagedAttachmentError as error:
            raise SourceHttpProblem(
                500,
                "staged_api_definition_unavailable",
                "The attached API definition is unavailable.",
            ) from error
        return source_response(result)

    @router.post("/api/description-attachments", status_code=201)
    async def stage_api_description(
        request: Request,
        file: Annotated[UploadFile, File()],
    ):
        if staged_description_service is None:
            raise SourceHttpProblem(
                500,
                "staged_api_description_unavailable",
                "API description staging is unavailable.",
            )
        authorize_mutation(request, mutation_policy)
        current_owner, selected = await _planning_session(
            request, auth_service, auth_settings
        )
        content = await file.read(1024 * 1024 + 1)
        filename = file.filename or ""
        await file.close()
        try:
            result = await call_source_service(
                staged_description_service.stage,
                owner_key=current_owner,
                conversation_id=selected.public_id,
                route_session_id=selected.route_session_id,
                filename=filename,
                content=content,
            )
        except ValueError as error:
            raise SourceHttpProblem(
                400,
                "invalid_api_description_upload",
                str(error),
            ) from error
        except ApiStagedDescriptionError as error:
            raise SourceHttpProblem(
                500,
                "staged_api_description_unavailable",
                "The API description could not be staged.",
            ) from error
        return source_response(result, status_code=201)

    @router.get("/api/description-attachments/current")
    async def current_staged_api_description(request: Request):
        if staged_description_service is None:
            raise SourceHttpProblem(
                500,
                "staged_api_description_unavailable",
                "The attached API description is unavailable.",
            )
        current_owner, selected = await _planning_session(
            request, auth_service, auth_settings
        )
        try:
            result = await call_source_service(
                staged_description_service.current,
                owner_key=current_owner,
                conversation_id=selected.public_id,
                route_session_id=selected.route_session_id,
            )
        except ApiStagedDescriptionError as error:
            raise SourceHttpProblem(
                500,
                "staged_api_description_unavailable",
                "The attached API description is unavailable.",
            ) from error
        return source_response(result)

    @router.get("/{source_id}/graph")
    async def inspect_api_graph(source_id: str, request: Request):
        current_owner = await owner_key(request, auth_service, auth_settings)
        result = await call_source_service(
            graph_presenter.inspect,
            owner_key=current_owner,
            source_id=source_id,
        )
        return source_response(result)

    @router.get("/{source_id}/connections")
    async def list_api_connections(source_id: str, request: Request):
        current_owner = await owner_key(request, auth_service, auth_settings)
        try:
            result = await call_source_service(
                connection_profiles.list,
                owner_key=current_owner,
                source_id=source_id,
            )
        except ApiConnectionError as error:
            raise SourceHttpProblem(
                500,
                "api_connection_profiles_unavailable",
                "The API connection profiles are unavailable.",
            ) from error
        return source_response(result)

    @router.get("/{source_id}/contract-revisions")
    async def list_api_contract_revisions(source_id: str, request: Request):
        current_owner = await owner_key(request, auth_service, auth_settings)
        try:
            result = await call_source_service(
                contract_revision_service.list,
                owner_id=UUID(current_owner),
                source_id=source_id,
            )
        except ApiContractRevisionConflict as error:
            raise SourceHttpProblem(
                409,
                "contract_revision_conflict",
                str(error),
            ) from error
        return source_response(result)

    @router.get("/{source_id}/connection-checks")
    async def list_api_connection_checks(
        source_id: str,
        request: Request,
        revision_id: Annotated[str, Query(min_length=16, max_length=16)],
    ):
        current_owner = await owner_key(request, auth_service, auth_settings)
        try:
            result = await call_source_service(
                connection_check_service.list,
                owner_id=UUID(current_owner),
                source_id=source_id,
                source_revision_id=revision_id,
            )
        except ApiConnectionCheckError as error:
            raise SourceHttpProblem(
                500,
                "api_connection_checks_unavailable",
                "The API connection check history is unavailable.",
            ) from error
        return source_response(result)

    @router.get("/{source_id}/operation-curation")
    async def inspect_api_operation_curation(
        source_id: str,
        request: Request,
        revision_id: Annotated[str, Query(min_length=16, max_length=16)],
    ):
        current_owner = await owner_key(request, auth_service, auth_settings)
        try:
            result = await call_source_service(
                operation_curation_service.inspect,
                owner_id=UUID(current_owner),
                source_id=source_id,
                source_revision_id=revision_id,
            )
        except ApiOperationCurationError as error:
            raise SourceHttpProblem(
                500,
                "api_operation_curation_unavailable",
                "The API operation curation is unavailable.",
            ) from error
        return source_response(result)

    @router.post("/{source_id}/route-plans", status_code=201)
    async def create_api_route_plan(
        source_id: str,
        request: Request,
        body: Annotated[CreateApiRoutePlanRequest, Body()],
    ):
        authorize_mutation(request, mutation_policy)
        current_owner, selected = await _planning_session(
            request, auth_service, auth_settings
        )
        try:
            result = await call_source_service(
                route_plan_service.create,
                owner_id=UUID(current_owner),
                conversation_id=selected.public_id,
                route_session_id=selected.route_session_id,
                source_id=source_id,
                source_revision_id=body.source_revision_id,
                profile_id=body.profile_id,
                curation_id=body.curation_id,
                request_text=body.request_text,
                provided_inputs=body.provided_inputs,
            )
        except ApiRoutePlanConflict as error:
            raise SourceHttpProblem(409, "api_route_plan_conflict", str(error)) from error
        except ApiRoutePlanError as error:
            raise SourceHttpProblem(
                500,
                "api_route_plan_unavailable",
                "The API route plan is unavailable.",
            ) from error
        return source_response(result, status_code=201)

    @router.get("/{source_id}/route-plans/current")
    async def current_api_route_plan(
        source_id: str,
        request: Request,
        revision_id: Annotated[str, Query(min_length=16, max_length=16)],
    ):
        current_owner, selected = await _planning_session(
            request, auth_service, auth_settings
        )
        try:
            result = await call_source_service(
                route_plan_service.current,
                owner_id=UUID(current_owner),
                conversation_id=selected.public_id,
                route_session_id=selected.route_session_id,
                source_id=source_id,
                source_revision_id=revision_id,
            )
        except ApiRoutePlanConflict as error:
            raise SourceHttpProblem(409, "api_route_plan_conflict", str(error)) from error
        except ApiRoutePlanError as error:
            raise SourceHttpProblem(
                500,
                "api_route_plan_unavailable",
                "The API route plan is unavailable.",
            ) from error
        return source_response(result)

    @router.get("/{source_id}/route-plans/{plan_id}")
    async def inspect_api_route_plan(
        source_id: str,
        plan_id: str,
        request: Request,
        revision_id: Annotated[str, Query(min_length=16, max_length=16)],
    ):
        current_owner, selected = await _planning_session(
            request, auth_service, auth_settings
        )
        try:
            result = await call_source_service(
                route_plan_service.current,
                owner_id=UUID(current_owner),
                conversation_id=selected.public_id,
                route_session_id=selected.route_session_id,
                source_id=source_id,
                source_revision_id=revision_id,
            )
            if result is None or result.plan_id != plan_id:
                raise SourceHttpProblem(
                    404, "api_route_plan_not_found", "The API route plan is unavailable."
                )
        except ApiRoutePlanConflict as error:
            raise SourceHttpProblem(409, "api_route_plan_conflict", str(error)) from error
        except ApiRoutePlanError as error:
            raise SourceHttpProblem(
                500,
                "api_route_plan_unavailable",
                "The API route plan is unavailable.",
            ) from error
        return source_response(result)

    @router.post("/{source_id}/route-plans/{plan_id}/clarifications")
    async def clarify_api_route_plan(
        source_id: str,
        plan_id: str,
        request: Request,
        body: Annotated[ClarifyApiRoutePlanRequest, Body()],
    ):
        authorize_mutation(request, mutation_policy)
        current_owner, selected = await _planning_session(
            request, auth_service, auth_settings
        )
        try:
            result = await call_source_service(
                route_plan_service.clarify,
                owner_id=UUID(current_owner),
                conversation_id=selected.public_id,
                route_session_id=selected.route_session_id,
                source_id=source_id,
                source_revision_id=body.source_revision_id,
                plan_id=plan_id,
                expected_record_id=body.expected_record_id,
                answers=body.answers,
            )
        except ApiRoutePlanConflict as error:
            raise SourceHttpProblem(409, "api_route_plan_conflict", str(error)) from error
        except ApiRoutePlanError as error:
            raise SourceHttpProblem(
                500,
                "api_route_plan_unavailable",
                "The API route plan is unavailable.",
            ) from error
        return source_response(result)

    @router.get("/{source_id}/route-plans/{plan_id}/execution")
    async def current_routed_api_execution(
        source_id: str,
        plan_id: str,
        request: Request,
    ):
        current_owner, selected = await _planning_session(
            request, auth_service, auth_settings
        )
        if routed_execution_service is None:
            raise SourceHttpProblem(
                500,
                "routed_api_execution_unavailable",
                "The routed API execution is unavailable.",
            )
        try:
            location = await call_source_service(
                route_plan_service.locate,
                owner_id=UUID(current_owner),
                plan_id=plan_id,
            )
            if (
                location.source_id != source_id
                or location.conversation_id != selected.public_id
                or location.route_session_id != selected.route_session_id
            ):
                raise SourceHttpProblem(
                    404,
                    "routed_api_execution_not_found",
                    "The routed API execution is unavailable.",
                )
            result = await call_source_service(
                routed_execution_service.current,
                owner_id=UUID(current_owner),
                plan_id=plan_id,
            )
        except ApiRoutedExecutionConflict as error:
            raise SourceHttpProblem(
                409, "routed_api_execution_conflict", str(error)
            ) from error
        except (ApiRoutedExecutionError, ApiRoutePlanError) as error:
            raise SourceHttpProblem(
                500,
                "routed_api_execution_unavailable",
                "The routed API execution is unavailable.",
            ) from error
        return source_response(result)

    return router


async def _planning_session(request, auth_service, auth_settings):
    current_owner = await owner_key(request, auth_service, auth_settings)
    try:
        selected = await auth_service.resolve_conversation(
            access_token=bearer_token(request),
            conversation_id=conversation_id(request),
            touch=True,
        )
    except (ConversationUnavailable, SessionUnavailable) as error:
        raise SourceHttpProblem(
            404,
            "conversation_not_found",
            "The selected conversation is unavailable.",
        ) from error
    return current_owner, selected


__all__ = [
    "ClarifyApiRoutePlanRequest",
    "CreateApiRoutePlanRequest",
    "create_api_source_router",
]
