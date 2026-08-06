from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from datetime import timedelta
from typing import Any, Protocol


class LoungeAccountError(RuntimeError):
    pass


class LoungeAccountConflict(LoungeAccountError):
    pass


class LoungeInvalidCredentials(LoungeAccountError):
    pass


class LoungeConversationUnavailable(LoungeAccountError):
    pass


class LoungeSessionUnavailable(LoungeAccountError):
    pass


class LoungeInvalidAuthToken(LoungeAccountError):
    pass


class LoungeRateLimitExceeded(RuntimeError):
    pass


class LoungeMailDeliveryUnavailable(RuntimeError):
    pass


class LoungeMailRecipientRejected(RuntimeError):
    pass


@dataclass(frozen=True)
class LoungeOperationRequest:
    client_ip: str
    current_access_token: str | None
    selected_conversation_id: str | None


@dataclass(frozen=True)
class LoungeIssuedOwnerSession:
    credential_payload: Mapping[str, Any]


@dataclass(frozen=True)
class LoungeEmailToken:
    recipient: str
    token: str


@dataclass(frozen=True)
class LoungeVerificationDeliveryContext:
    recipient: str
    already_verified: bool


class LoungeAccountGateway(Protocol):
    async def register(
        self,
        *,
        email: str,
        password: str,
        display_name: str | None,
        anonymous_access_token: str,
        conversation_id: str,
        route_session_id: str,
    ) -> LoungeIssuedOwnerSession: ...

    async def sign_in(
        self,
        *,
        email: str,
        password: str,
        anonymous_access_token: str,
        conversation_id: str,
        route_session_id: str,
    ) -> LoungeIssuedOwnerSession: ...

    async def request_password_reset(
        self,
        email: str,
    ) -> LoungeEmailToken | None: ...

    async def confirm_password_reset(
        self,
        token: str,
        new_password: str,
    ) -> None: ...

    async def verification_delivery_context_for_route(
        self,
        route_session_id: str,
    ) -> LoungeVerificationDeliveryContext: ...

    async def request_verification_for_route(
        self,
        route_session_id: str,
    ) -> LoungeEmailToken | None: ...

    async def verify(self, token: str) -> None: ...


class LoungeRateLimiter(Protocol):
    async def consume(
        self,
        *,
        scope: str,
        subject: str,
        limit: int,
        window: timedelta,
    ) -> None: ...


class LoungeMailDelivery(Protocol):
    @property
    def known_unavailable(self) -> bool: ...

    async def send_password_reset(self, recipient: str, link: str) -> None: ...

    async def send_verification(self, recipient: str, link: str) -> None: ...


class LoungeCredentialTransition(Protocol):
    def current_request(self) -> LoungeOperationRequest | None: ...

    def publish_issued_credentials(
        self,
        credential_payload: Mapping[str, Any],
    ) -> None: ...

    def publish_revocation(self) -> None: ...


__all__ = [
    "LoungeAccountConflict",
    "LoungeAccountGateway",
    "LoungeConversationUnavailable",
    "LoungeCredentialTransition",
    "LoungeEmailToken",
    "LoungeInvalidAuthToken",
    "LoungeInvalidCredentials",
    "LoungeIssuedOwnerSession",
    "LoungeMailDelivery",
    "LoungeMailDeliveryUnavailable",
    "LoungeMailRecipientRejected",
    "LoungeOperationRequest",
    "LoungeRateLimitExceeded",
    "LoungeRateLimiter",
    "LoungeSessionUnavailable",
    "LoungeVerificationDeliveryContext",
]
