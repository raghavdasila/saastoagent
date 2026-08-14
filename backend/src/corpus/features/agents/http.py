from __future__ import annotations

import uuid

from fastapi import APIRouter, Request
from fastapi.encoders import jsonable_encoder
from fastapi.responses import JSONResponse
from corpus.auth.contracts import AgentOwnerScopeGateway, AgentOwnerScopeUnavailable
from corpus.shared.http import CorpusHttpProblem

from .ports import (
    AgentNotFound,
    AgentSourceAttachmentUnavailable,
)
from .service import AgentService
from .overview import AgentProductOverviewService


def create_agents_router(
    service: AgentService,
    owner_scope: AgentOwnerScopeGateway,
    overview_service: AgentProductOverviewService | None = None,
) -> APIRouter:
    router = APIRouter(prefix="/api/agents", tags=["agents"])

    @router.get("")
    async def list_agents(request: Request):
        organization_id = await _organization_id(request, owner_scope)
        return _json(await service.list(organization_id))

    @router.get("/{agent_id}")
    async def get_agent(agent_id: uuid.UUID, request: Request):
        organization_id = await _organization_id(request, owner_scope)
        try:
            result = await service.get(organization_id, agent_id)
        except AgentNotFound as error:
            raise CorpusHttpProblem(404, "agent_unavailable", str(error)) from error
        return _json(result)

    @router.get("/{agent_id}/sources")
    async def list_agent_sources(agent_id: uuid.UUID, request: Request):
        organization_id = await _organization_id(request, owner_scope)
        try:
            result = await service.list_source_attachments(organization_id, agent_id)
        except AgentNotFound as error:
            raise CorpusHttpProblem(404, "agent_unavailable", str(error)) from error
        except AgentSourceAttachmentUnavailable as error:
            raise CorpusHttpProblem(
                409,
                "source_attachment_unavailable",
                str(error),
            ) from error
        return _json(result)

    @router.get("/{agent_id}/dependencies")
    async def inspect_agent_dependencies(agent_id: uuid.UUID, request: Request):
        organization_id = await _organization_id(request, owner_scope)
        try:
            result = await service.inspect_dependencies(organization_id, agent_id)
        except AgentNotFound as error:
            raise CorpusHttpProblem(404, "agent_unavailable", str(error)) from error
        return _json(result)

    @router.get("/{agent_id}/builds")
    async def list_agent_builds(agent_id: uuid.UUID, request: Request):
        organization_id = await _organization_id(request, owner_scope)
        try:
            result = await service.list_build_lineages(organization_id, agent_id)
        except AgentNotFound as error:
            raise CorpusHttpProblem(404, "agent_unavailable", str(error)) from error
        return _json(result)

    @router.get("/{agent_id}/product-overview")
    async def get_agent_product_overview(agent_id: uuid.UUID, request: Request):
        if overview_service is None:
            raise CorpusHttpProblem(
                503,
                "agent_overview_unavailable",
                "The selected-Agent product overview is unavailable.",
            )
        organization_id = await _organization_id(request, owner_scope)
        try:
            result = await overview_service.get(organization_id, agent_id)
        except AgentNotFound as error:
            raise CorpusHttpProblem(404, "agent_unavailable", str(error)) from error
        return _json(result)

    return router


async def _organization_id(
    request: Request,
    owner_scope: AgentOwnerScopeGateway,
) -> uuid.UUID:
    authorization = request.headers.get("Authorization", "")
    scheme, separator, token = authorization.partition(" ")
    if separator != " " or scheme.casefold() != "bearer" or not token:
        raise CorpusHttpProblem(401, "authentication_required", "Authentication is required.")
    try:
        return await owner_scope.organization_id_for_access_token(token)
    except AgentOwnerScopeUnavailable as error:
        raise CorpusHttpProblem(401, "authentication_required", str(error)) from error


def _json(value) -> JSONResponse:
    return JSONResponse(
        content=jsonable_encoder(value),
        headers={"Cache-Control": "private, no-store"},
    )


__all__ = [
    "create_agents_router",
]
