from __future__ import annotations

import hashlib
import secrets
from dataclasses import dataclass
from datetime import datetime, timedelta

from email_validator import EmailNotValidError, validate_email


class PasswordPolicyError(ValueError):
    """Raised when an owner password violates the Corpus policy."""


def normalize_email(value: str) -> str:
    try:
        validated = validate_email(value.strip(), check_deliverability=False)
    except EmailNotValidError as error:
        raise ValueError("A valid email address is required.") from error
    return validated.normalized.lower()


def validate_password(password: str, normalized_email: str) -> None:
    if not 12 <= len(password) <= 128:
        raise PasswordPolicyError("Password must be between 12 and 128 characters.")
    if normalized_email.casefold() in password.casefold():
        raise PasswordPolicyError("Password must not contain the normalized email.")


def hash_opaque_token(raw: str) -> str:
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


@dataclass(frozen=True)
class OpaqueToken:
    raw: str
    digest: str


def issue_opaque_token() -> OpaqueToken:
    raw = secrets.token_urlsafe(32)
    return OpaqueToken(raw=raw, digest=hash_opaque_token(raw))


@dataclass(frozen=True)
class SessionLifetime:
    created_at: datetime
    last_seen_at: datetime
    absolute_expires_at: datetime
    revoked_at: datetime | None

    def is_active(self, *, now: datetime, idle_timeout: timedelta) -> bool:
        return (
            self.revoked_at is None
            and now < self.absolute_expires_at
            and now - self.last_seen_at < idle_timeout
        )


__all__ = [
    "OpaqueToken",
    "PasswordPolicyError",
    "SessionLifetime",
    "hash_opaque_token",
    "issue_opaque_token",
    "normalize_email",
    "validate_password",
]
