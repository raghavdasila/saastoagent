from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from datetime import timedelta
from typing import Any

from corpus.auth.credential_transition import CredentialTransition
from corpus.auth.mail import (
    MailDeliveryUnavailable,
    MailRecipientRejected,
    OwnerMailDelivery,
)
from corpus.auth.rate_limits import AuthRateLimiter, RateLimitExceeded
from corpus.auth.schemas import TokenPairView
from corpus.auth.service import (
    AuthConflict,
    AuthService,
    ConversationUnavailable,
    InvalidAuthToken,
    InvalidCredentials,
    SessionUnavailable,
)
from corpus.features.lounge.ports import (
    LoungeAccountConflict,
    LoungeConversationUnavailable,
    LoungeEmailToken,
    LoungeInvalidAuthToken,
    LoungeInvalidCredentials,
    LoungeIssuedOwnerSession,
    LoungeMailDeliveryUnavailable,
    LoungeMailRecipientRejected,
    LoungeOperationRequest,
    LoungeRateLimitExceeded,
    LoungeSessionUnavailable,
    LoungeVerificationDeliveryContext,
)


@dataclass(frozen=True)
class AuthLoungeAccountGateway:
    service: AuthService

    async def register(self, **values) -> LoungeIssuedOwnerSession:
        try:
            issued = await self.service.register(**values)
        except AuthConflict as error:
            raise LoungeAccountConflict(str(error)) from error
        except ConversationUnavailable as error:
            raise LoungeConversationUnavailable(str(error)) from error
        except SessionUnavailable as error:
            raise LoungeSessionUnavailable(str(error)) from error
        return LoungeIssuedOwnerSession(
            credential_payload=issued.tokens.model_dump(mode="json")
        )

    async def sign_in(self, **values) -> LoungeIssuedOwnerSession:
        try:
            issued = await self.service.sign_in(**values)
        except InvalidCredentials as error:
            raise LoungeInvalidCredentials(str(error)) from error
        except ConversationUnavailable as error:
            raise LoungeConversationUnavailable(str(error)) from error
        except SessionUnavailable as error:
            raise LoungeSessionUnavailable(str(error)) from error
        return LoungeIssuedOwnerSession(
            credential_payload=issued.tokens.model_dump(mode="json")
        )

    async def request_password_reset(self, email: str) -> LoungeEmailToken | None:
        token = await self.service.request_password_reset(email)
        return (
            None
            if token is None
            else LoungeEmailToken(recipient=token.recipient, token=token.token)
        )

    async def confirm_password_reset(
        self,
        token: str,
        new_password: str,
    ) -> None:
        try:
            await self.service.confirm_password_reset(token, new_password)
        except InvalidAuthToken as error:
            raise LoungeInvalidAuthToken(str(error)) from error

    async def verification_delivery_context_for_route(
        self,
        route_session_id: str,
    ) -> LoungeVerificationDeliveryContext:
        try:
            context = await self.service.verification_delivery_context_for_route(
                route_session_id
            )
        except SessionUnavailable as error:
            raise LoungeSessionUnavailable(str(error)) from error
        return LoungeVerificationDeliveryContext(
            recipient=context.recipient,
            already_verified=context.already_verified,
        )

    async def request_verification_for_route(
        self,
        route_session_id: str,
    ) -> LoungeEmailToken | None:
        token = await self.service.request_verification_for_route(route_session_id)
        return (
            None
            if token is None
            else LoungeEmailToken(recipient=token.recipient, token=token.token)
        )

    async def verify(self, token: str) -> None:
        try:
            await self.service.verify(token)
        except InvalidAuthToken as error:
            raise LoungeInvalidAuthToken(str(error)) from error


@dataclass(frozen=True)
class AuthLoungeRateLimiter:
    limiter: AuthRateLimiter

    async def consume(
        self,
        *,
        scope: str,
        subject: str,
        limit: int,
        window: timedelta,
    ) -> None:
        try:
            await self.limiter.consume(
                scope=scope,
                subject=subject,
                limit=limit,
                window=window,
            )
        except RateLimitExceeded as error:
            raise LoungeRateLimitExceeded(str(error)) from error


@dataclass(frozen=True)
class AuthLoungeMailDelivery:
    delivery: OwnerMailDelivery

    @property
    def known_unavailable(self) -> bool:
        return self.delivery.known_unavailable

    async def send_password_reset(self, recipient: str, link: str) -> None:
        try:
            await self.delivery.send_password_reset(recipient, link)
        except MailDeliveryUnavailable as error:
            raise LoungeMailDeliveryUnavailable(str(error)) from error
        except MailRecipientRejected as error:
            raise LoungeMailRecipientRejected(str(error)) from error

    async def send_verification(self, recipient: str, link: str) -> None:
        try:
            await self.delivery.send_verification(recipient, link)
        except MailDeliveryUnavailable as error:
            raise LoungeMailDeliveryUnavailable(str(error)) from error
        except MailRecipientRejected as error:
            raise LoungeMailRecipientRejected(str(error)) from error


@dataclass(frozen=True)
class AuthLoungeCredentialTransition:
    transition: CredentialTransition

    def current_request(self) -> LoungeOperationRequest | None:
        request = self.transition.current_request()
        if request is None:
            return None
        return LoungeOperationRequest(
            client_ip=request.client_ip,
            current_access_token=request.current_access_token,
            selected_conversation_id=request.selected_conversation_id,
        )

    def publish_issued_credentials(
        self,
        credential_payload: Mapping[str, Any],
    ) -> None:
        self.transition.publish_issued_tokens(
            TokenPairView.model_validate(credential_payload)
        )

    def publish_revocation(self) -> None:
        self.transition.publish_revocation()


__all__ = [
    "AuthLoungeAccountGateway",
    "AuthLoungeCredentialTransition",
    "AuthLoungeMailDelivery",
    "AuthLoungeRateLimiter",
]
