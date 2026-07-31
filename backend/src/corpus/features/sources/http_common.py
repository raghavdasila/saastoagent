from __future__ import annotations

from typing import Protocol

from fastapi import Request
from fastapi.concurrency import run_in_threadpool
from fastapi.encoders import jsonable_encoder
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from routedeck_fastapi import SameOriginMutationPolicy
from routedeck_fastapi.security import RouteDeckMutationRejected

from corpus.auth.config import AuthSettings
from corpus.auth.service import SessionUnavailable

from .errors import (
    SourceArtifactError,
    SourceDependencyError,
    SourceInputError,
    SourceIntegrationError,
)
from .repository import SourceNotFound, SourceNotReady, SourceRepositoryError


class OwnerSessionResolver(Protocol):
    async def resolve_access_token(self, access_token: str): ...


class SourceProblem(BaseModel):
    code: str
    message: str


class SourceHttpProblem(RuntimeError):
    def __init__(self, status_code: int, code: str, message: str) -> None:
        super().__init__(message)
        self.status_code = status_code
        self.code = code
        self.message = message


async def source_problem_response(_request: Request, error: SourceHttpProblem):
    return JSONResponse(
        status_code=error.status_code,
        content=SourceProblem(code=error.code, message=error.message).model_dump(),
        headers={"Cache-Control": "no-store"},
    )


async def owner_key(
    request: Request,
    service: OwnerSessionResolver,
    settings: AuthSettings,
) -> str:
    del settings
    authorization = request.headers.get("authorization")
    if authorization is None:
        raise unauthorized()
    scheme, separator, auth_token = authorization.partition(" ")
    if (
        not separator
        or scheme.casefold() != "bearer"
        or not auth_token
        or auth_token != auth_token.strip()
        or " " in auth_token
        or len(auth_token) > 512
    ):
        raise unauthorized()
    try:
        current = await service.resolve_access_token(auth_token)
    except SessionUnavailable as error:
        raise unauthorized() from error
    if current.user_id is None:
        raise unauthorized()
    return str(current.user_id)


def authorize_mutation(
    request: Request,
    policy: SameOriginMutationPolicy,
) -> None:
    try:
        policy.authorize(request)
    except RouteDeckMutationRejected as error:
        raise SourceHttpProblem(
            403,
            "mutation_origin_rejected",
            "The mutation request origin is not authorized.",
        ) from error


async def call_source_service(function, **kwargs):
    try:
        return await run_in_threadpool(function, **kwargs)
    except SourceNotFound as error:
        raise SourceHttpProblem(
            404,
            "source_not_found",
            "The requested source does not exist.",
        ) from error
    except SourceNotReady as error:
        raise SourceHttpProblem(409, "source_not_ready", str(error)) from error
    except SourceInputError as error:
        raise SourceHttpProblem(422, "invalid_source_input", str(error)) from error
    except SourceDependencyError as error:
        raise SourceHttpProblem(
            503,
            "source_dependency_unavailable",
            str(error),
        ) from error
    except SourceArtifactError as error:
        raise SourceHttpProblem(
            500,
            "source_artifact_invalid",
            str(error),
        ) from error
    except SourceRepositoryError as error:
        raise SourceHttpProblem(
            500,
            "source_repository_failure",
            str(error),
        ) from error
    except SourceIntegrationError as error:
        raise SourceHttpProblem(
            500,
            "source_integration_failure",
            str(error),
        ) from error


def source_response(value, *, status_code: int = 200) -> JSONResponse:
    return JSONResponse(
        status_code=status_code,
        content=jsonable_encoder(value),
        headers={"Cache-Control": "no-store"},
    )


def unauthorized() -> SourceHttpProblem:
    return SourceHttpProblem(
        401,
        "authentication_required",
        "Authentication is required.",
    )


__all__ = [
    "OwnerSessionResolver",
    "SourceHttpProblem",
    "authorize_mutation",
    "call_source_service",
    "owner_key",
    "source_problem_response",
    "source_response",
]
