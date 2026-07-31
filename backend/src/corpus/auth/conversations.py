from __future__ import annotations

import inspect
import secrets
from collections.abc import Awaitable, Callable
from datetime import UTC
from typing import Literal

from fastapi import APIRouter, Request
from fastapi.encoders import jsonable_encoder
from fastapi.responses import JSONResponse
from routedeck_core import RouteDeckRuntime
from routedeck_core.ports import SessionStoreError
from routedeck_core.ports.session_store import SessionStoreErrorCode
from routedeck_fastapi import SameOriginMutationPolicy
from routedeck_fastapi.security import RouteDeckMutationRejected

from .http import AuthHttpProblem
from .models import CorpusConversation
from .schemas import ActiveConversationRunView, ConversationView
from .selector import BearerCredentialError, bearer_token
from .service import (
    AuthService,
    ConversationLimitReached,
    ConversationUnavailable,
    SessionUnavailable,
)


RuntimeProvider = Callable[[Request], RouteDeckRuntime | Awaitable[RouteDeckRuntime]]


class ConversationBackingSessionUnavailable(RuntimeError):
    pass


def create_conversation_router(
    *,
    service: AuthService,
    mutation_policy: SameOriginMutationPolicy,
    runtime_provider: RuntimeProvider,
) -> APIRouter:
    router = APIRouter(prefix="/api/conversations", tags=["conversations"])

    @router.get("")
    async def list_conversations(request: Request):
        token = _required_bearer(request)
        try:
            conversations = await service.list_conversations(token)
        except SessionUnavailable as error:
            raise _unauthorized() from error
        runtime = await _runtime(runtime_provider, request)
        summaries = []
        for conversation in conversations:
            try:
                summaries.append(await _summary(runtime, conversation))
            except ConversationBackingSessionUnavailable:
                await service.release_conversation(conversation.public_id)
        return _response({"conversations": summaries})

    @router.post("", status_code=201)
    async def create_conversation(request: Request):
        _authorize_mutation(request, mutation_policy)
        token = _required_bearer(request)
        runtime = await _runtime(runtime_provider, request)
        route_session_id = secrets.token_urlsafe(32)
        try:
            conversation = await service.reserve_conversation(
                access_token=token,
                route_session_id=route_session_id,
            )
        except SessionUnavailable as error:
            raise _unauthorized() from error
        except ConversationLimitReached as error:
            raise AuthHttpProblem(
                409,
                "conversation_limit_reached",
                str(error),
            ) from error
        try:
            await runtime.provision_session(
                session_id=route_session_id,
                request_id=secrets.token_urlsafe(24),
            )
        except Exception:
            await service.release_conversation(conversation.public_id)
            raise
        return _response(await _summary(runtime, conversation), status_code=201)

    @router.get("/{public_id}")
    async def get_conversation(public_id: str, request: Request):
        if not public_id or len(public_id) > 64:
            raise AuthHttpProblem(
                404,
                "conversation_not_found",
                "The requested conversation is unavailable.",
            )
        token = _required_bearer(request)
        try:
            conversation = await service.resolve_conversation(
                access_token=token,
                conversation_id=public_id,
            )
        except SessionUnavailable as error:
            raise _unauthorized() from error
        except ConversationUnavailable as error:
            raise AuthHttpProblem(
                404,
                "conversation_not_found",
                "The requested conversation is unavailable.",
            ) from error
        runtime = await _runtime(runtime_provider, request)
        try:
            summary = await _summary(runtime, conversation)
        except ConversationBackingSessionUnavailable as error:
            await service.release_conversation(conversation.public_id)
            raise AuthHttpProblem(
                404,
                "conversation_not_found",
                "The requested conversation is unavailable.",
            ) from error
        return _response(summary)

    return router


async def _summary(
    runtime: RouteDeckRuntime,
    conversation: CorpusConversation,
) -> ConversationView:
    try:
        snapshot = await runtime.services.store.load(conversation.route_session_id)
    except SessionStoreError as error:
        if error.code not in {
            SessionStoreErrorCode.SESSION_NOT_FOUND,
            SessionStoreErrorCode.SESSION_EXPIRED,
        }:
            raise
        raise ConversationBackingSessionUnavailable from error
    active_run = None
    interaction = snapshot.state.interaction
    if interaction.phase.value == "active" and interaction.request_id is not None:
        run = await runtime.conversation_runs.get(
            conversation.route_session_id,
            interaction.request_id,
        )
        status: Literal["running", "completed", "interrupted"] = (
            "completed"
            if run.stage.value == "completed"
            else "interrupted"
            if run.stage.value == "interrupted"
            else "running"
        )
        active_run = ActiveConversationRunView(
            request_id=run.request_id,
            status=status,
            stage=run.stage.value,
            cursor=run.cursor,
        )
    return ConversationView(
        id=conversation.public_id,
        current_node_id=snapshot.state.current.node_id,
        session_version=snapshot.session_version,
        updated_at=(
            conversation.updated_at.replace(tzinfo=UTC)
            if conversation.updated_at.tzinfo is None
            else conversation.updated_at.astimezone(UTC)
        ),
        active_run=active_run,
    )


async def _runtime(
    provider: RuntimeProvider,
    request: Request,
) -> RouteDeckRuntime:
    runtime = provider(request)
    if inspect.isawaitable(runtime):
        runtime = await runtime
    if not isinstance(runtime, RouteDeckRuntime):
        raise AuthHttpProblem(
            503,
            "conversation_runtime_unavailable",
            "Conversation runtime is unavailable.",
        )
    return runtime


def _required_bearer(request: Request) -> str:
    try:
        return bearer_token(request)
    except BearerCredentialError as error:
        raise _unauthorized(str(error)) from error


def _authorize_mutation(
    request: Request,
    policy: SameOriginMutationPolicy,
) -> None:
    try:
        policy.authorize(request)
    except RouteDeckMutationRejected as error:
        raise AuthHttpProblem(
            403,
            "mutation_origin_rejected",
            "The mutation request origin is not authorized.",
        ) from error


def _unauthorized(
    message: str = "Authorization bearer credentials are invalid or expired.",
) -> AuthHttpProblem:
    return AuthHttpProblem(401, "authentication_required", message)


def _response(value, *, status_code: int = 200) -> JSONResponse:
    return JSONResponse(
        status_code=status_code,
        content=jsonable_encoder(value),
        headers={"Cache-Control": "no-store"},
    )


__all__ = ["create_conversation_router"]
