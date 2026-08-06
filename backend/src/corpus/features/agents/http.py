from __future__ import annotations

import uuid

from fastapi import APIRouter, Request
from fastapi.encoders import jsonable_encoder
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from .ports import AgentNotFound, AgentOwnerScopeGateway, AgentOwnerScopeUnavailable
from .service import AgentService


class AgentsHttpProblem(RuntimeError):
    def __init__(self, status_code: int, code: str, message: str) -> None:
        super().__init__(message)
        self.status_code = status_code
        self.code = code
        self.message = message


class AgentsProblemView(BaseModel):
    code: str
    message: str


async def agents_problem_response(_request: Request, error: AgentsHttpProblem):
    return JSONResponse(
        status_code=error.status_code,
        content=AgentsProblemView(code=error.code, message=error.message).model_dump(),
        headers={"Cache-Control": "no-store"},
    )


def create_agents_router(
    service: AgentService,
    owner_scope: AgentOwnerScopeGateway,
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
            raise AgentsHttpProblem(404, "agent_unavailable", str(error)) from error
        return _json(result)

    return router


async def _organization_id(
    request: Request,
    owner_scope: AgentOwnerScopeGateway,
) -> uuid.UUID:
    authorization = request.headers.get("Authorization", "")
    scheme, separator, token = authorization.partition(" ")
    if separator != " " or scheme.casefold() != "bearer" or not token:
        raise AgentsHttpProblem(401, "authentication_required", "Authentication is required.")
    try:
        return await owner_scope.organization_id_for_access_token(token)
    except AgentOwnerScopeUnavailable as error:
        raise AgentsHttpProblem(401, "authentication_required", str(error)) from error


def _json(value) -> JSONResponse:
    return JSONResponse(
        content=jsonable_encoder(value),
        headers={"Cache-Control": "private, no-store"},
    )


__all__ = [
    "AgentsHttpProblem",
    "agents_problem_response",
    "create_agents_router",
]
