import uuid

from fastapi import APIRouter, Request
from fastapi.encoders import jsonable_encoder
from fastapi.responses import JSONResponse

from corpus.shared.http import CorpusHttpProblem as AgentsHttpProblem
from corpus.auth.contracts import AgentOwnerScopeGateway, AgentOwnerScopeUnavailable

from .service import SandboxService
from .deployment_service import SandboxDeploymentService
from .deployment_schemas import (
    PlaygroundMessageCreate,
    PlaygroundReviewResolution,
    SandboxDeploymentCreate,
    SandboxDeploymentRetry,
)
from corpus.features.deployment.contracts import DeploymentConflict, DeploymentUnavailable
from agent_delivery_runtime.domain import DeliveryError, new_id


def create_sandbox_router(
    legacy_service: SandboxService,
    service: SandboxDeploymentService,
    owner_scope: AgentOwnerScopeGateway,
) -> APIRouter:
    router = APIRouter(prefix="/api/agents", tags=["agent-sandbox"])

    @router.get("/{agent_id}/sandbox")
    async def list_sandbox(agent_id: uuid.UUID, request: Request):
        organization_id = await _owner(request, owner_scope)
        try:
            result = await service.list(organization_id, agent_id)
        except (DeploymentConflict, DeploymentUnavailable, DeliveryError) as error:
            raise _problem(error)
        return JSONResponse(content=jsonable_encoder(result), headers={"Cache-Control": "private, no-store"})

    @router.get("/{agent_id}/sandbox/legacy")
    async def list_legacy_runs(agent_id: uuid.UUID, request: Request):
        organization_id = await _owner(request, owner_scope)
        result = await legacy_service.list(organization_id, agent_id)
        return JSONResponse(content=jsonable_encoder(result), headers={"Cache-Control": "private, no-store"})

    @router.post("/{agent_id}/sandbox/deployments", status_code=201)
    async def deploy(agent_id: uuid.UUID, body: SandboxDeploymentCreate, request: Request):
        organization_id = await _owner(request, owner_scope)
        try:
            result = await service.deploy(
                organization_id, agent_id,
                build_id=body.build_id, request_key=body.request_key,
            )
        except (DeploymentConflict, DeploymentUnavailable, DeliveryError) as error:
            raise _problem(error)
        return JSONResponse(status_code=201, content=jsonable_encoder(result), headers={"Cache-Control": "private, no-store"})

    @router.post("/{agent_id}/sandbox/deployments/{deployment_id}/retry", status_code=201)
    async def retry(agent_id: uuid.UUID, deployment_id: uuid.UUID, body: SandboxDeploymentRetry, request: Request):
        organization_id = await _owner(request, owner_scope)
        try:
            result = await service.retry(
                organization_id, agent_id, deployment_id,
                request_key=body.request_key,
            )
        except (DeploymentConflict, DeploymentUnavailable, DeliveryError) as error:
            raise _problem(error)
        return JSONResponse(status_code=201, content=jsonable_encoder(result), headers={"Cache-Control": "private, no-store"})

    @router.post("/{agent_id}/sandbox/sessions", status_code=201)
    async def create_session(agent_id: uuid.UUID, request: Request):
        organization_id = await _owner(request, owner_scope)
        try:
            result = await service.create_session(organization_id, agent_id)
        except (DeploymentConflict, DeploymentUnavailable, DeliveryError) as error:
            raise _problem(error)
        return JSONResponse(status_code=201, content=jsonable_encoder(result), headers={"Cache-Control": "private, no-store"})

    @router.get("/{agent_id}/sandbox/sessions/{session_id}")
    async def read_session(agent_id: uuid.UUID, session_id: str, request: Request):
        organization_id = await _owner(request, owner_scope)
        try:
            result = await service.session(organization_id, agent_id, session_id)
        except (DeploymentConflict, DeploymentUnavailable, DeliveryError) as error:
            raise _problem(error)
        return JSONResponse(content=jsonable_encoder(result), headers={"Cache-Control": "private, no-store"})

    @router.post("/{agent_id}/sandbox/sessions/{session_id}/messages")
    async def send_message(agent_id: uuid.UUID, session_id: str, body: PlaygroundMessageCreate, request: Request):
        organization_id = await _owner(request, owner_scope)
        try:
            result = await service.send_message(
                organization_id, agent_id, session_id,
                text=body.text, request_id=body.request_id or new_id("req"),
            )
        except (DeploymentConflict, DeploymentUnavailable, DeliveryError) as error:
            raise _problem(error)
        return JSONResponse(content=jsonable_encoder(result), headers={"Cache-Control": "private, no-store"})

    @router.post("/{agent_id}/sandbox/sessions/{session_id}/reviews")
    async def resolve_review(agent_id: uuid.UUID, session_id: str, body: PlaygroundReviewResolution, request: Request):
        organization_id = await _owner(request, owner_scope)
        try:
            result = await service.resolve_review(
                organization_id, agent_id, session_id,
                review_id=body.review_id, accepted=body.accepted,
                request_id=body.request_id or new_id("req"),
            )
        except (DeploymentConflict, DeploymentUnavailable, DeliveryError) as error:
            raise _problem(error)
        return JSONResponse(content=jsonable_encoder(result), headers={"Cache-Control": "private, no-store"})

    @router.get("/{agent_id}/sandbox/sessions/{session_id}/diagnostics")
    async def diagnostics(agent_id: uuid.UUID, session_id: str, request: Request):
        organization_id = await _owner(request, owner_scope)
        try:
            result = await service.diagnostics(organization_id, agent_id, session_id)
        except (DeploymentConflict, DeploymentUnavailable, DeliveryError) as error:
            raise _problem(error)
        return JSONResponse(content=jsonable_encoder(result), headers={"Cache-Control": "private, no-store"})

    return router


async def _owner(request: Request, owner_scope: AgentOwnerScopeGateway):
    authorization = request.headers.get("Authorization", "")
    scheme, separator, token = authorization.partition(" ")
    if separator != " " or scheme.casefold() != "bearer" or not token:
        raise AgentsHttpProblem(401, "authentication_required", "Authentication is required.")
    try:
        return await owner_scope.organization_id_for_access_token(token)
    except AgentOwnerScopeUnavailable as error:
        raise AgentsHttpProblem(401, "authentication_required", str(error)) from error


def _problem(error: Exception) -> AgentsHttpProblem:
    if isinstance(error, DeploymentConflict):
        return AgentsHttpProblem(409, "sandbox_conflict", str(error))
    if isinstance(error, DeliveryError):
        return AgentsHttpProblem(error.status_code, error.code, str(error))
    return AgentsHttpProblem(503, "sandbox_unavailable", str(error))


__all__ = ["create_sandbox_router"]
