from __future__ import annotations

from dataclasses import dataclass
import re
import uuid
from typing import Protocol
from fastapi import Request

from routedeck_core.contracts.operations import ContextProvider
from routedeck_core.contracts.projection import FrozenJsonObject


OWNER_CONTEXT_PROVIDER = ContextProvider(
    id="corpus.owner_context",
    description=(
        "Authenticated Corpus owner and organization context for this "
        "RouteDeck session."
    ),
    output_schema=FrozenJsonObject(
        {
            "type": "object",
            "properties": {
                "display_name": {"type": ["string", "null"]},
                "organization_name": {"type": "string"},
                "organization_slug": {"type": "string"},
                "role": {"type": "string", "enum": ["owner", "admin", "member"]},
                "is_verified": {"type": "boolean"},
            },
            "required": [
                "display_name",
                "organization_name",
                "organization_slug",
                "role",
                "is_verified",
            ],
            "additionalProperties": False,
        }
    ),
)


@dataclass(frozen=True)
class OwnerRouteContext:
    display_name: str | None
    organization_name: str
    organization_slug: str
    role: str
    is_verified: bool


class AgentOwnerScopeUnavailable(RuntimeError):
    pass


class AgentOwnerScopeGateway(Protocol):
    async def organization_id_for_route(
        self, route_session_id: str
    ) -> uuid.UUID: ...


class ConversationUnavailable(RuntimeError):
    pass


class SessionUnavailable(RuntimeError):
    pass


class BearerCredentialError(ValueError):
    pass


_PUBLIC_CONVERSATION_ID = re.compile(r"^[A-Za-z0-9_-]{16,64}$")


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
    if not _PUBLIC_CONVERSATION_ID.fullmatch(value):
        raise ValueError("X-Corpus-Conversation-ID is invalid.")
    return value


__all__ = [
    "OWNER_CONTEXT_PROVIDER",
    "AgentOwnerScopeGateway",
    "AgentOwnerScopeUnavailable",
    "BearerCredentialError",
    "ConversationUnavailable",
    "OwnerRouteContext",
    "SessionUnavailable",
    "bearer_token",
    "conversation_id",
]
