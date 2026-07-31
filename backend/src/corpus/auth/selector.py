from __future__ import annotations

import re
from dataclasses import dataclass

from fastapi import Request, Response
from routedeck_fastapi.contracts import RouteDeckHttpProblem

from .service import (
    AuthService,
    ConversationLimitReached,
    ConversationUnavailable,
    SessionUnavailable,
)


_PUBLIC_ID = re.compile(r"^[A-Za-z0-9_-]{16,64}$")


class BearerCredentialError(ValueError):
    pass


def bearer_token(request: Request) -> str:
    authorization = request.headers.get("authorization")
    if authorization is None:
        raise BearerCredentialError("Authorization bearer credentials are required.")
    scheme, separator, value = authorization.partition(" ")
    if (
        not separator
        or scheme.casefold() != "bearer"
        or not value
        or value != value.strip()
        or " " in value
        or len(value) > 512
    ):
        raise BearerCredentialError("Authorization bearer credentials are invalid.")
    return value


def conversation_id(request: Request) -> str:
    value = request.headers.get("x-corpus-conversation-id")
    if value is None:
        raise ValueError("X-Corpus-Conversation-ID is required.")
    if not _PUBLIC_ID.fullmatch(value):
        raise ValueError("X-Corpus-Conversation-ID is invalid.")
    return value


@dataclass(frozen=True)
class CorpusSessionSelector:
    service: AuthService

    async def selected_session_id(self, request: Request) -> str:
        try:
            access_token = bearer_token(request)
        except BearerCredentialError as error:
            raise _authentication_required(str(error)) from error
        try:
            public_id = conversation_id(request)
        except ValueError as error:
            raise RouteDeckHttpProblem(
                400,
                "conversation_selection_required",
                str(error),
            ) from error
        try:
            selected = await self.service.resolve_conversation(
                access_token=access_token,
                conversation_id=public_id,
                touch=True,
            )
        except SessionUnavailable as error:
            raise _authentication_required(
                "Authorization bearer credentials are invalid or expired."
            ) from error
        except ConversationUnavailable as error:
            raise RouteDeckHttpProblem(
                404,
                "conversation_not_found",
                "The selected conversation is unavailable.",
            ) from error
        return selected.route_session_id

    async def attach_created_session(
        self,
        request: Request,
        response: Response,
        session_id: str,
    ) -> None:
        try:
            access_token = bearer_token(request)
            conversation = await self.service.reserve_conversation(
                access_token=access_token,
                route_session_id=session_id,
            )
        except BearerCredentialError as error:
            raise _authentication_required(str(error)) from error
        except SessionUnavailable as error:
            raise _authentication_required(
                "Authorization bearer credentials are invalid or expired."
            ) from error
        except ConversationLimitReached as error:
            raise RouteDeckHttpProblem(
                409,
                "conversation_limit_reached",
                str(error),
            ) from error
        response.headers["X-Corpus-Conversation-ID"] = conversation.public_id


def _authentication_required(message: str) -> RouteDeckHttpProblem:
    return RouteDeckHttpProblem(
        401,
        "authentication_required",
        message,
    )


__all__ = [
    "BearerCredentialError",
    "CorpusSessionSelector",
    "bearer_token",
    "conversation_id",
]
