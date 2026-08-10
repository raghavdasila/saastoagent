import uuid

from fastapi import APIRouter, Request
from fastapi.encoders import jsonable_encoder
from fastapi.responses import JSONResponse

from corpus.features.agents.http import AgentsHttpProblem
from corpus.features.agents.ports import AgentOwnerScopeGateway

from .service import OperationsService


def create_operations_router(service: OperationsService, owner_scope: AgentOwnerScopeGateway) -> APIRouter:
    router = APIRouter(tags=["agent-operations"])

    @router.get("/api/agents/{agent_id}/operations")
    async def list_operations(agent_id: uuid.UUID, request: Request):
        authorization = request.headers.get("Authorization", "")
        scheme, separator, token = authorization.partition(" ")
        if separator != " " or scheme.casefold() != "bearer" or not token:
            raise AgentsHttpProblem(401, "authentication_required", "Authentication is required.")
        owner = await owner_scope.organization_id_for_access_token(token)
        return JSONResponse(
            content=jsonable_encoder(await service.list(owner, agent_id)),
            headers={"Cache-Control": "private, no-store"},
        )

    return router

__all__ = ["create_operations_router"]
