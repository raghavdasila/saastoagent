import uuid

from fastapi import APIRouter, Request
from fastapi.encoders import jsonable_encoder
from fastapi.responses import JSONResponse

from corpus.features.agents.http import AgentsHttpProblem
from corpus.features.agents.ports import AgentOwnerScopeGateway, AgentOwnerScopeUnavailable

from .service import SandboxService


def create_sandbox_router(service: SandboxService, owner_scope: AgentOwnerScopeGateway) -> APIRouter:
    router = APIRouter(prefix="/api/agents", tags=["agent-sandbox"])

    @router.get("/{agent_id}/sandbox")
    async def list_runs(agent_id: uuid.UUID, request: Request):
        authorization = request.headers.get("Authorization", "")
        scheme, separator, token = authorization.partition(" ")
        if separator != " " or scheme.casefold() != "bearer" or not token:
            raise AgentsHttpProblem(401, "authentication_required", "Authentication is required.")
        try:
            organization_id = await owner_scope.organization_id_for_access_token(token)
            result = await service.list(organization_id, agent_id)
        except AgentOwnerScopeUnavailable as error:
            raise AgentsHttpProblem(401, "authentication_required", str(error)) from error
        return JSONResponse(content=jsonable_encoder(result), headers={"Cache-Control": "private, no-store"})

    return router


__all__ = ["create_sandbox_router"]
