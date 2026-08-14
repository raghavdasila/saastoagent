from __future__ import annotations

import uuid

from fastapi import APIRouter, Request
from fastapi.encoders import jsonable_encoder
from fastapi.responses import JSONResponse

from corpus.shared.http import CorpusHttpProblem as AgentsHttpProblem
from corpus.auth.contracts import AgentOwnerScopeGateway

from .ports import DesignerUnavailable
from .service import DesignerService


def create_designer_router(service: DesignerService, owner_scope: AgentOwnerScopeGateway) -> APIRouter:
    router = APIRouter(prefix="/api/agents", tags=["agent-designer"])

    @router.get("/{agent_id}/design")
    async def get_design(agent_id: uuid.UUID, request: Request):
        authorization = request.headers.get("Authorization", "")
        scheme, separator, token = authorization.partition(" ")
        if separator != " " or scheme.casefold() != "bearer" or not token:
            raise AgentsHttpProblem(401, "authentication_required", "Authentication is required.")
        organization_id = await owner_scope.organization_id_for_access_token(token)
        try:
            result = await service.get(organization_id, agent_id)
        except DesignerUnavailable:
            result = None
        return JSONResponse(content=jsonable_encoder(result), headers={"Cache-Control": "private, no-store"})

    return router


__all__ = ["create_designer_router"]
