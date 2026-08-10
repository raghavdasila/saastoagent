from __future__ import annotations

from typing import Any, Literal

from fastapi import APIRouter, Request
from pydantic import BaseModel, Field
from routedeck_fastapi import SameOriginMutationPolicy

from corpus.auth.config import AuthSettings
from .http_common import (
    OwnerSessionResolver,
    SourceHttpProblem,
    authorize_mutation,
    call_source_service,
    owner_key,
    source_problem_response,
    source_response,
)
from .service import SourceService


class RetrievalBody(BaseModel):
    query: str = Field(min_length=1, max_length=4_000)
    top_k: int = Field(default=5, ge=1, le=25)
    trace_mode: Literal["bounded", "full"] = "bounded"
    provided_params: dict[str, Any] | None = None


class EvalsetBody(BaseModel):
    evalset_id: str = Field(
        min_length=1,
        max_length=80,
        pattern=r"^[A-Za-z0-9][A-Za-z0-9._-]*$",
    )
    categories: tuple[str, ...] = ("paraphrase",)
    tasks_per_category: int = Field(default=1, ge=1, le=10)
    max_generation_attempts: int = Field(default=2, ge=1, le=10)
    max_review_attempts: int = Field(default=2, ge=1, le=10)


def create_sources_router(
    *,
    service: SourceService,
    auth_service: OwnerSessionResolver,
    auth_settings: AuthSettings,
    mutation_policy: SameOriginMutationPolicy,
) -> APIRouter:
    router = APIRouter(prefix="/api/sources", tags=["owner-sources"])

    @router.get("")
    async def list_sources(request: Request):
        current_owner = await owner_key(request, auth_service, auth_settings)
        result = await call_source_service(
            service.list_sources,
            owner_key=current_owner,
        )
        return source_response(result)

    @router.get("/{source_id}")
    async def get_source(source_id: str, request: Request, revision_id: str | None = None):
        current_owner = await owner_key(request, auth_service, auth_settings)
        result = await call_source_service(
            service.get_source,
            owner_key=current_owner,
            source_id=source_id,
            revision_id=revision_id,
        )
        return source_response(result)

    @router.post("/{source_id}/retrieve")
    async def retrieve(source_id: str, body: RetrievalBody, request: Request):
        authorize_mutation(request, mutation_policy)
        current_owner = await owner_key(request, auth_service, auth_settings)
        result = await call_source_service(
            service.retrieve,
            owner_key=current_owner,
            source_id=source_id,
            query=body.query,
            top_k=body.top_k,
            trace_mode=body.trace_mode,
            provided_params=body.provided_params,
        )
        return source_response(result)

    @router.post("/{source_id}/evalsets")
    async def generate_evalset(
        source_id: str,
        body: EvalsetBody,
        request: Request,
    ):
        authorize_mutation(request, mutation_policy)
        current_owner = await owner_key(request, auth_service, auth_settings)
        result = await call_source_service(
            service.generate_evalset,
            owner_key=current_owner,
            source_id=source_id,
            evalset_id=body.evalset_id,
            categories=body.categories,
            tasks_per_category=body.tasks_per_category,
            max_generation_attempts=body.max_generation_attempts,
            max_review_attempts=body.max_review_attempts,
        )
        return source_response(result)

    return router


__all__ = [
    "SourceHttpProblem",
    "create_sources_router",
    "source_problem_response",
]
