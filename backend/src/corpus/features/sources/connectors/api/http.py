from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, File, Form, Request, UploadFile
from routedeck_fastapi import SameOriginMutationPolicy

from corpus.auth.config import AuthSettings

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


def create_api_source_router(
    *,
    service: SourceService,
    auth_service: OwnerSessionResolver,
    auth_settings: AuthSettings,
    mutation_policy: SameOriginMutationPolicy,
    max_upload_bytes: int,
) -> APIRouter:
    if max_upload_bytes <= 0:
        raise ValueError("API source upload limit must be positive.")
    router = APIRouter(prefix="/api/sources", tags=["owner-api-sources"])

    @router.post("/api", status_code=201)
    async def upload_api_source(
        request: Request,
        name: Annotated[str, Form(min_length=1, max_length=128)],
        file: Annotated[UploadFile, File()],
    ):
        authorize_mutation(request, mutation_policy)
        current_owner = await owner_key(request, auth_service, auth_settings)
        content = await file.read(max_upload_bytes + 1)
        await file.close()
        if len(content) > max_upload_bytes:
            raise SourceHttpProblem(
                413,
                "api_collection_too_large",
                "The API collection exceeds the configured upload limit.",
            )
        try:
            result = await call_source_service(
                service.create_source,
                owner_key=current_owner,
                connector_key="api",
                display_name=name,
                upload=SourceUpload(
                    filename=file.filename or "",
                    content_type=(
                        file.content_type or "application/octet-stream"
                    ),
                    content=content,
                ),
            )
        except SourceUploadError as error:
            raise SourceHttpProblem(
                400,
                "invalid_api_collection_upload",
                str(error),
            ) from error
        return source_response(result, status_code=201)

    return router


__all__ = ["create_api_source_router"]
