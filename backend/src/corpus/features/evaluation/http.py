import uuid

from fastapi import APIRouter, Request
from fastapi.encoders import jsonable_encoder
from fastapi.responses import JSONResponse

from corpus.shared.http import CorpusHttpProblem as AgentsHttpProblem
from corpus.auth.contracts import AgentOwnerScopeGateway, AgentOwnerScopeUnavailable

from .service import EvaluationService
from .schemas import SandboxEvaluationRunCreate
from .ports import EvaluationConflict, EvaluationUnavailable


def create_evaluation_router(service: EvaluationService, owner_scope: AgentOwnerScopeGateway) -> APIRouter:
    router = APIRouter(prefix="/api/agents", tags=["agent-evaluation"])

    @router.get("/{agent_id}/evaluations")
    async def list_evaluations(agent_id: uuid.UUID, request: Request):
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

    @router.post("/{agent_id}/evaluations/sandbox-runs", status_code=202)
    async def run_set(agent_id: uuid.UUID, body: SandboxEvaluationRunCreate, request: Request):
        organization_id = await _owner(request, owner_scope)
        try:
            result = await service.queue_set_against_sandbox(
                organization_id,
                agent_id,
                body.evaluation_set_id,
                sandbox_deployment_id=body.sandbox_deployment_id,
            )
        except EvaluationConflict as error:
            raise AgentsHttpProblem(409, "evaluation_conflict", str(error)) from error
        except EvaluationUnavailable as error:
            raise AgentsHttpProblem(503, "evaluation_unavailable", str(error)) from error
        return JSONResponse(status_code=202, content=jsonable_encoder(result), headers={"Cache-Control": "private, no-store"})

    @router.post("/{agent_id}/evaluations/attempts/{attempt_id}/retry", status_code=202)
    async def retry_attempt(agent_id: uuid.UUID, attempt_id: uuid.UUID, request: Request):
        organization_id = await _owner(request, owner_scope)
        try:
            result = await service.retry_case_run(
                organization_id, agent_id, attempt_id
            )
        except EvaluationConflict as error:
            raise AgentsHttpProblem(409, "evaluation_conflict", str(error)) from error
        except EvaluationUnavailable as error:
            raise AgentsHttpProblem(503, "evaluation_unavailable", str(error)) from error
        return JSONResponse(status_code=202, content=jsonable_encoder(result), headers={"Cache-Control": "private, no-store"})

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

__all__ = ["create_evaluation_router"]
