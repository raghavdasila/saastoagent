from __future__ import annotations

import json
import logging
from collections.abc import Awaitable, Callable
from datetime import timedelta
from urllib.parse import quote

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse, Response
from pydantic import BaseModel, EmailStr, Field, ValidationError
from routedeck_fastapi import SameOriginMutationPolicy
from routedeck_fastapi.security import RouteDeckMutationRejected

from .config import AuthSettings
from .mail import MailDeliveryUnavailable, OwnerMailDelivery
from .rate_limits import AuthRateLimiter, RateLimitExceeded
from .service import (
    AuthConflict,
    AuthService,
    GuestSessionUnavailable,
    InvalidAuthToken,
    InvalidCredentials,
    SessionUnavailable,
)


logger = logging.getLogger(__name__)


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


class RegisterRequest(BaseModel):
    email: EmailStr
    password: str
    display_name: str | None = Field(default=None, max_length=128)


class SignInRequest(BaseModel):
    email: EmailStr
    password: str


class EmailRequest(BaseModel):
    email: EmailStr


class TokenRequest(BaseModel):
    token: str = Field(min_length=1)


class ResetConfirmRequest(BaseModel):
    token: str = Field(min_length=1)
    new_password: str


def create_auth_router(
    *,
    service: AuthService,
    limiter: AuthRateLimiter,
    mail: OwnerMailDelivery,
    settings: AuthSettings,
    mutation_policy: SameOriginMutationPolicy,
    guest_cookie_name: str,
    route_session_exists: Callable[[Request, str], Awaitable[bool]],
    guest_cookie_path: str = "/",
    guest_cookie_secure: bool = False,
) -> APIRouter:
    router = APIRouter(prefix="/api/auth", tags=["owner-auth"])

    @router.post("/register", status_code=201)
    async def register(request: Request):
        _authorize(request, mutation_policy)
        body = await _body(request, RegisterRequest)
        await _limit(
            limiter,
            scope="registration-ip",
            subject=_client_ip(request, settings.trusted_proxies),
            limit=5,
            window=timedelta(hours=1),
        )
        guest_session = request.cookies.get(guest_cookie_name)
        if not guest_session or not await route_session_exists(request, guest_session):
            raise AuthHttpProblem(
                409,
                "guest_session_unavailable",
                "The guest Workspace session is unavailable.",
            )
        try:
            issued = await service.register(
                email=str(body.email),
                password=body.password,
                display_name=body.display_name,
                guest_route_session_id=guest_session,
            )
        except AuthConflict as error:
            raise AuthHttpProblem(
                409,
                "email_already_registered",
                "An owner with that email already exists.",
            ) from error
        except GuestSessionUnavailable as error:
            raise AuthHttpProblem(
                409,
                "guest_session_unavailable",
                "The guest Workspace session is unavailable.",
            ) from error
        except ValueError as error:
            raise AuthHttpProblem(400, "invalid_password", str(error)) from error
        return _owner_response(
            issued,
            status_code=201,
            settings=settings,
            guest_cookie_name=guest_cookie_name,
            guest_cookie_path=guest_cookie_path,
            guest_cookie_secure=guest_cookie_secure,
        )

    @router.post("/sign-in")
    async def sign_in(request: Request):
        _authorize(request, mutation_policy)
        body = await _body(request, SignInRequest)
        client_ip = _client_ip(request, settings.trusted_proxies)
        await _limit(
            limiter,
            scope="sign-in-ip",
            subject=client_ip,
            limit=20,
            window=timedelta(minutes=15),
        )
        await _limit(
            limiter,
            scope="sign-in-email",
            subject=str(body.email).lower(),
            limit=5,
            window=timedelta(minutes=15),
        )
        try:
            issued = await service.sign_in(
                email=str(body.email),
                password=body.password,
                guest_route_session_id=request.cookies.get(guest_cookie_name),
                current_auth_token=request.cookies.get(settings.auth_cookie_name),
            )
        except InvalidCredentials as error:
            raise AuthHttpProblem(
                401,
                "invalid_credentials",
                "Invalid email or password.",
            ) from error
        except GuestSessionUnavailable as error:
            raise AuthHttpProblem(
                409,
                "guest_session_unavailable",
                "The guest Workspace session is unavailable.",
            ) from error
        return _owner_response(
            issued,
            status_code=200,
            settings=settings,
            guest_cookie_name=guest_cookie_name,
            guest_cookie_path=guest_cookie_path,
            guest_cookie_secure=guest_cookie_secure,
        )

    @router.get("/session")
    async def session(request: Request):
        current = await _current_owner(request, service, settings, require_route=False)
        return JSONResponse(
            content=current.view.model_dump(mode="json"),
            headers={"Cache-Control": "no-store"},
        )

    @router.post("/sign-out", status_code=204)
    async def sign_out(request: Request):
        _authorize(request, mutation_policy)
        await service.sign_out(request.cookies.get(settings.auth_cookie_name))
        response = Response(status_code=204)
        _clear_all_cookies(
            response,
            settings,
            guest_cookie_name,
            guest_cookie_path,
            guest_cookie_secure,
        )
        return response

    @router.post("/verification-email", status_code=204)
    async def verification_email(request: Request):
        _authorize(request, mutation_policy)
        auth_token = _required_cookie(request, settings.auth_cookie_name)
        try:
            token = await service.request_verification(auth_token)
        except SessionUnavailable as error:
            raise _unauthorized() from error
        if token is None:
            return Response(status_code=204)
        await _limit(
            limiter,
            scope="verification-email",
            subject=token.recipient,
            limit=3,
            window=timedelta(hours=1),
        )
        await _limit(
            limiter,
            scope="verification-ip",
            subject=_client_ip(request, settings.trusted_proxies),
            limit=20,
            window=timedelta(hours=1),
        )
        link = f"{str(settings.public_frontend_url).rstrip('/')}/verify#token={quote(token.token)}"
        try:
            await mail.send_verification(token.recipient, link)
        except MailDeliveryUnavailable as error:
            raise AuthHttpProblem(
                503,
                "verification_delivery_unavailable",
                "Verification email delivery is unavailable.",
            ) from error
        return Response(status_code=204)

    @router.post("/verify", status_code=204)
    async def verify(request: Request):
        _authorize(request, mutation_policy)
        body = await _body(request, TokenRequest)
        try:
            await service.verify(body.token)
        except InvalidAuthToken as error:
            raise AuthHttpProblem(
                400,
                "invalid_verification_token",
                "The verification token is invalid or expired.",
            ) from error
        return Response(status_code=204)

    @router.post("/password-reset/request", status_code=202)
    async def password_reset_request(request: Request):
        _authorize(request, mutation_policy)
        body = await _body(request, EmailRequest)
        email = str(body.email).lower()
        await _limit(
            limiter,
            scope="password-reset-email",
            subject=email,
            limit=3,
            window=timedelta(hours=1),
        )
        await _limit(
            limiter,
            scope="password-reset-ip",
            subject=_client_ip(request, settings.trusted_proxies),
            limit=20,
            window=timedelta(hours=1),
        )
        token = await service.request_password_reset(email)
        if token is not None:
            link = f"{str(settings.public_frontend_url).rstrip('/')}/reset-password#token={quote(token.token)}"
            try:
                await mail.send_password_reset(token.recipient, link)
            except MailDeliveryUnavailable:
                logger.exception("Password reset email delivery failed")
        return Response(status_code=202)

    @router.post("/password-reset/confirm", status_code=204)
    async def password_reset_confirm(request: Request):
        _authorize(request, mutation_policy)
        body = await _body(request, ResetConfirmRequest)
        try:
            await service.confirm_password_reset(body.token, body.new_password)
        except InvalidAuthToken as error:
            raise AuthHttpProblem(
                400,
                "invalid_reset_token",
                "The reset token is invalid or expired.",
            ) from error
        except ValueError as error:
            raise AuthHttpProblem(400, "invalid_password", str(error)) from error
        response = Response(status_code=204)
        _clear_all_cookies(
            response,
            settings,
            guest_cookie_name,
            guest_cookie_path,
            guest_cookie_secure,
        )
        return response

    @router.post("/recover", status_code=204)
    async def recover(request: Request):
        _authorize(request, mutation_policy)
        await service.sign_out(request.cookies.get(settings.auth_cookie_name))
        response = Response(status_code=204)
        _clear_all_cookies(
            response,
            settings,
            guest_cookie_name,
            guest_cookie_path,
            guest_cookie_secure,
        )
        return response

    return router


async def _current_owner(request, service, settings, *, require_route):
    auth_token = _required_cookie(request, settings.auth_cookie_name)
    try:
        return await service.resolve_browser_session(
            auth_token=auth_token,
            owner_route_handle=request.cookies.get(settings.owner_route_cookie_name),
            require_route=require_route,
        )
    except SessionUnavailable as error:
        raise _unauthorized() from error


def _required_cookie(request: Request, name: str) -> str:
    value = request.cookies.get(name)
    if not value:
        raise _unauthorized()
    return value


def _unauthorized() -> AuthHttpProblem:
    return AuthHttpProblem(401, "authentication_required", "Authentication is required.")


def _authorize(request: Request, policy: SameOriginMutationPolicy) -> None:
    try:
        policy.authorize(request)
    except RouteDeckMutationRejected as error:
        raise AuthHttpProblem(
            403,
            "mutation_origin_rejected",
            "The mutation request origin is not authorized.",
        ) from error


async def _body(request: Request, model):
    try:
        if request.headers.get("content-type", "").partition(";")[0].lower() != "application/json":
            raise ValueError
        return model.model_validate(await request.json())
    except (ValueError, json.JSONDecodeError, ValidationError) as error:
        raise AuthHttpProblem(400, "invalid_request", "The request is invalid.") from error


async def _limit(limiter, **kwargs) -> None:
    try:
        await limiter.consume(**kwargs)
    except RateLimitExceeded as error:
        raise AuthHttpProblem(
            429,
            "rate_limit_exceeded",
            "Too many authentication attempts. Try again later.",
        ) from error


def _owner_response(
    issued,
    *,
    status_code,
    settings,
    guest_cookie_name,
    guest_cookie_path,
    guest_cookie_secure,
):
    response = JSONResponse(
        status_code=status_code,
        content=issued.view.model_dump(mode="json"),
        headers={"Cache-Control": "no-store"},
    )
    max_age = settings.absolute_session_days * 24 * 60 * 60
    for name, value in (
        (settings.auth_cookie_name, issued.auth_token),
        (settings.owner_route_cookie_name, issued.owner_route_handle),
    ):
        response.set_cookie(
            key=name,
            value=value,
            max_age=max_age,
            httponly=True,
            secure=settings.auth_cookie_secure,
            samesite="lax",
            path=settings.auth_cookie_path,
        )
    response.delete_cookie(
        guest_cookie_name,
        path=guest_cookie_path,
        secure=guest_cookie_secure,
        httponly=True,
        samesite="lax",
    )
    return response


def _clear_all_cookies(
    response,
    settings,
    guest_cookie_name,
    guest_cookie_path,
    guest_cookie_secure,
):
    for name in (settings.auth_cookie_name, settings.owner_route_cookie_name):
        response.delete_cookie(
            name,
            path=settings.auth_cookie_path,
            secure=settings.auth_cookie_secure,
            httponly=True,
            samesite="lax",
        )
    response.delete_cookie(
        guest_cookie_name,
        path=guest_cookie_path,
        secure=guest_cookie_secure,
        httponly=True,
        samesite="lax",
    )


def _client_ip(request: Request, trusted_proxies: tuple[str, ...]) -> str:
    peer = request.client.host if request.client is not None else "unknown"
    if peer in trusted_proxies:
        forwarded = request.headers.get("x-forwarded-for")
        if forwarded:
            return forwarded.split(",", 1)[0].strip()
    return peer


__all__ = [
    "AuthHttpProblem",
    "AuthProblem",
    "auth_problem_response",
    "create_auth_router",
]
