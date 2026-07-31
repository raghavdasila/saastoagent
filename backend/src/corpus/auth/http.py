from __future__ import annotations

from datetime import timedelta

from fastapi import APIRouter, Request
from fastapi.encoders import jsonable_encoder
from fastapi.responses import JSONResponse, Response
from pydantic import BaseModel
from routedeck_fastapi import SameOriginMutationPolicy
from routedeck_fastapi.security import RouteDeckMutationRejected

from .schemas import AnonymousPrincipalView, RefreshRequest
from .rate_limits import AuthRateLimiter, RateLimitExceeded
from .security import hash_opaque_token
from .selector import BearerCredentialError, bearer_token
from .service import AuthService, SessionUnavailable


class AuthProblem(BaseModel):
    code: str
    message: str


class AuthHttpProblem(RuntimeError):
    def __init__(self, status_code: int, code: str, message: str) -> None:
        super().__init__(message)
        self.status_code = status_code
        self.code = code
        self.message = message


async def auth_problem_response(_request: Request, error: AuthHttpProblem):
    return JSONResponse(
        status_code=error.status_code,
        content=AuthProblem(code=error.code, message=error.message).model_dump(),
        headers={"Cache-Control": "no-store"},
    )


def create_auth_router(
    *,
    service: AuthService,
    limiter: AuthRateLimiter,
    trusted_proxies: tuple[str, ...],
    mutation_policy: SameOriginMutationPolicy,
) -> APIRouter:
    router = APIRouter(prefix="/api/auth", tags=["owner-auth"])

    @router.post("/anonymous", status_code=201)
    async def anonymous(request: Request):
        _authorize(request, mutation_policy)
        await _limit(
            limiter,
            scope="anonymous-ip",
            subject=_client_ip(request, trusted_proxies),
            limit=20,
            window=timedelta(hours=1),
        )
        return _json(await service.issue_anonymous(), status_code=201)

    @router.post("/refresh")
    async def refresh(payload: RefreshRequest, request: Request):
        _authorize(request, mutation_policy)
        await _limit(
            limiter,
            scope="refresh-token",
            subject=hash_opaque_token(payload.refresh_token),
            limit=10,
            window=timedelta(minutes=15),
        )
        try:
            tokens = await service.refresh(payload.refresh_token)
        except SessionUnavailable as error:
            raise _unauthorized("The refresh token is invalid or expired.") from error
        return _json(tokens)

    @router.get("/session")
    async def current_session(request: Request):
        current = await _current_principal(request, service)
        return _json(
            current.owner
            if current.owner is not None
            else AnonymousPrincipalView()
        )

    @router.post("/sign-out", status_code=204)
    async def sign_out(request: Request):
        _authorize(request, mutation_policy)
        token = _required_bearer(request)
        try:
            await service.sign_out(token)
        except SessionUnavailable as error:
            raise _unauthorized() from error
        return Response(status_code=204, headers={"Cache-Control": "no-store"})

    return router


async def _current_principal(request: Request, service: AuthService):
    token = _required_bearer(request)
    try:
        return await service.resolve_access_token(token)
    except SessionUnavailable as error:
        raise _unauthorized() from error


def _required_bearer(request: Request) -> str:
    try:
        return bearer_token(request)
    except BearerCredentialError as error:
        raise _unauthorized(str(error)) from error


def _unauthorized(
    message: str = "Authorization bearer credentials are invalid or expired.",
) -> AuthHttpProblem:
    return AuthHttpProblem(401, "authentication_required", message)


def _authorize(request: Request, policy: SameOriginMutationPolicy) -> None:
    try:
        policy.authorize(request)
    except RouteDeckMutationRejected as error:
        raise AuthHttpProblem(
            403,
            "mutation_origin_rejected",
            "The mutation request origin is not authorized.",
        ) from error


async def _limit(limiter: AuthRateLimiter, **values) -> None:
    try:
        await limiter.consume(**values)
    except RateLimitExceeded as error:
        raise AuthHttpProblem(
            429,
            "rate_limit_exceeded",
            "Too many authentication attempts. Try again later.",
        ) from error


def _client_ip(request: Request, trusted_proxies: tuple[str, ...]) -> str:
    peer = request.client.host if request.client is not None else "unknown"
    if peer in trusted_proxies:
        forwarded = request.headers.get("x-forwarded-for")
        if forwarded:
            return forwarded.split(",", 1)[0].strip()
    return peer


def _json(value, *, status_code: int = 200) -> JSONResponse:
    return JSONResponse(
        status_code=status_code,
        content=jsonable_encoder(value),
        headers={"Cache-Control": "no-store"},
    )


__all__ = [
    "AuthHttpProblem",
    "AuthProblem",
    "auth_problem_response",
    "create_auth_router",
]
