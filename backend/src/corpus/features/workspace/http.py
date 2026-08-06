from __future__ import annotations

from fastapi import APIRouter, Request
from fastapi.encoders import jsonable_encoder
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from .ports import WorkspaceOverviewUnavailable
from .service import WorkspaceService


class WorkspaceHttpProblem(RuntimeError):
    def __init__(self, status_code: int, code: str, message: str) -> None:
        super().__init__(message)
        self.status_code = status_code
        self.code = code
        self.message = message


class WorkspaceProblemView(BaseModel):
    code: str
    message: str


async def workspace_problem_response(_request: Request, error: WorkspaceHttpProblem):
    return JSONResponse(
        status_code=error.status_code,
        content=WorkspaceProblemView(
            code=error.code,
            message=error.message,
        ).model_dump(),
        headers={"Cache-Control": "no-store"},
    )


def create_workspace_router(service: WorkspaceService) -> APIRouter:
    router = APIRouter(prefix="/api/workspace", tags=["workspace"])

    @router.get("/overview")
    async def overview(request: Request):
        token = _bearer_token(request)
        try:
            value = await service.for_access_token(token)
        except WorkspaceOverviewUnavailable as error:
            raise WorkspaceHttpProblem(
                401,
                "authentication_required",
                str(error),
            ) from error
        return JSONResponse(
            content=jsonable_encoder(value),
            headers={"Cache-Control": "private, no-store"},
        )

    return router


def _bearer_token(request: Request) -> str:
    authorization = request.headers.get("Authorization", "")
    scheme, separator, token = authorization.partition(" ")
    if separator != " " or scheme.casefold() != "bearer" or not token:
        raise WorkspaceHttpProblem(
            401,
            "authentication_required",
            "Authentication is required.",
        )
    return token


__all__ = [
    "WorkspaceHttpProblem",
    "create_workspace_router",
    "workspace_problem_response",
]
