from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

from .schemas import TokenPairView


@dataclass(frozen=True)
class AccountOperationRequest:
    """Request facts that supervised account operations are allowed to use."""

    client_ip: str
    current_access_token: str | None
    selected_conversation_id: str | None


class CredentialTransition(Protocol):
    """Corpus-owned boundary for account credentials outside RouteDeck state."""

    def current_request(self) -> AccountOperationRequest | None: ...

    def publish_issued_tokens(self, tokens: TokenPairView) -> None: ...

    def publish_revocation(self) -> None: ...


__all__ = ["AccountOperationRequest", "CredentialTransition"]
