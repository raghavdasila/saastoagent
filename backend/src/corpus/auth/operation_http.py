from __future__ import annotations

import json
from contextvars import ContextVar
from dataclasses import dataclass

from starlette.datastructures import Headers
from starlette.types import ASGIApp, Message, Receive, Scope, Send

from .credential_transition import AccountOperationRequest
from .schemas import TokenPairView


AUTH_TOKENS_HEADER = "X-Corpus-Auth-Tokens"
AUTH_REVOKED_HEADER = "X-Corpus-Auth-Revoked"


@dataclass
class _AuthOperationRequestState:
    request: AccountOperationRequest
    issued_tokens: TokenPairView | None = None
    credentials_revoked: bool = False


_CURRENT_AUTH_OPERATION_REQUEST: ContextVar[
    _AuthOperationRequestState | None
] = ContextVar("corpus_auth_operation_request", default=None)


class HttpCredentialTransition:
    """Adapt account credential transitions to the supervised HTTP response."""

    def current_request(self) -> AccountOperationRequest | None:
        current = _CURRENT_AUTH_OPERATION_REQUEST.get()
        return None if current is None else current.request

    def publish_issued_tokens(self, tokens: TokenPairView) -> None:
        current = self._require_context("Issued credentials")
        current.issued_tokens = tokens

    def publish_revocation(self) -> None:
        current = self._require_context("Credential revocation")
        current.credentials_revoked = True

    def open_request(
        self,
        *,
        client_ip: str,
        current_access_token: str | None,
        selected_conversation_id: str | None,
    ):
        return _CURRENT_AUTH_OPERATION_REQUEST.set(
            _AuthOperationRequestState(
                request=AccountOperationRequest(
                    client_ip=client_ip,
                    current_access_token=current_access_token,
                    selected_conversation_id=selected_conversation_id,
                )
            )
        )

    def close_request(self, token) -> None:
        _CURRENT_AUTH_OPERATION_REQUEST.reset(token)

    def response_headers(self) -> list[tuple[bytes, bytes]]:
        current = _CURRENT_AUTH_OPERATION_REQUEST.get()
        if current is None:
            raise RuntimeError("Credential response requires an HTTP request context")
        return _auth_headers(current)

    def _require_context(self, action: str) -> _AuthOperationRequestState:
        current = _CURRENT_AUTH_OPERATION_REQUEST.get()
        if current is None:
            raise RuntimeError(f"{action} require an HTTP request context")
        return current


class AuthOperationTokenMiddleware:
    """Publish supervised account-operation credentials outside RouteDeck state."""

    def __init__(
        self,
        app: ASGIApp,
        *,
        credential_transition: HttpCredentialTransition,
        trusted_proxies: tuple[str, ...] = (),
    ) -> None:
        self._app = app
        self._credential_transition = credential_transition
        self._trusted_proxies = trusted_proxies

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await self._app(scope, receive, send)
            return
        headers = Headers(scope=scope)
        token = self._credential_transition.open_request(
            client_ip=_client_ip(scope, headers, self._trusted_proxies),
            current_access_token=_bearer_value(headers.get("authorization")),
            selected_conversation_id=headers.get("x-corpus-conversation-id"),
        )

        async def send_with_auth_tokens(message: Message) -> None:
            if message["type"] == "http.response.start":
                additions = self._credential_transition.response_headers()
                if additions:
                    message = {
                        **message,
                        "headers": [*message.get("headers", []), *additions],
                    }
            await send(message)

        try:
            await self._app(scope, receive, send_with_auth_tokens)
        finally:
            self._credential_transition.close_request(token)


def _auth_headers(
    context: _AuthOperationRequestState,
) -> list[tuple[bytes, bytes]]:
    if context.issued_tokens is not None:
        payload = context.issued_tokens
        value = json.dumps(
            payload.model_dump(mode="json"),
            separators=(",", ":"),
        )
        return [(AUTH_TOKENS_HEADER.lower().encode("ascii"), value.encode("ascii"))]
    if context.credentials_revoked:
        return [(AUTH_REVOKED_HEADER.lower().encode("ascii"), b"true")]
    return []


def _bearer_value(authorization: str | None) -> str | None:
    if authorization is None:
        return None
    scheme, separator, value = authorization.partition(" ")
    if (
        not separator
        or scheme.casefold() != "bearer"
        or not value
        or value != value.strip()
        or " " in value
        or len(value) > 512
    ):
        return None
    return value


def _client_ip(
    scope: Scope,
    headers: Headers,
    trusted_proxies: tuple[str, ...],
) -> str:
    client = scope.get("client")
    peer = client[0] if client is not None else "unknown"
    if peer in trusted_proxies:
        forwarded = headers.get("x-forwarded-for")
        if forwarded:
            return forwarded.split(",", 1)[0].strip()
    return peer


__all__ = [
    "AUTH_REVOKED_HEADER",
    "AUTH_TOKENS_HEADER",
    "AuthOperationTokenMiddleware",
    "HttpCredentialTransition",
]
