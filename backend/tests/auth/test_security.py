from __future__ import annotations

from datetime import UTC, datetime, timedelta

import pytest

from corpus.auth.security import (
    PasswordPolicyError,
    SessionLifetime,
    hash_opaque_token,
    issue_opaque_token,
    normalize_email,
    validate_password,
)


def test_email_normalization_and_password_policy() -> None:
    assert normalize_email("  Owner@Example.COM ") == "owner@example.com"

    validate_password("a sufficiently long secret", "owner@example.com")

    with pytest.raises(PasswordPolicyError, match="12 and 128"):
        validate_password("too-short", "owner@example.com")
    with pytest.raises(PasswordPolicyError, match="email"):
        validate_password(
            "prefix-owner@example.com-suffix",
            "owner@example.com",
        )


def test_opaque_tokens_are_random_and_only_their_hash_is_persistable() -> None:
    first = issue_opaque_token()
    second = issue_opaque_token()

    assert first.raw != second.raw
    assert first.digest == hash_opaque_token(first.raw)
    assert first.raw not in first.digest
    assert len(first.digest) == 64


def test_session_lifetime_enforces_idle_absolute_and_revocation() -> None:
    now = datetime(2026, 7, 22, tzinfo=UTC)
    lifetime = SessionLifetime(
        created_at=now - timedelta(days=2),
        last_seen_at=now - timedelta(days=6),
        absolute_expires_at=now + timedelta(days=28),
        revoked_at=None,
    )
    assert lifetime.is_active(now=now, idle_timeout=timedelta(days=7))
    assert not lifetime.is_active(
        now=now + timedelta(days=2),
        idle_timeout=timedelta(days=7),
    )
    assert not SessionLifetime(
        created_at=now,
        last_seen_at=now,
        absolute_expires_at=now + timedelta(days=30),
        revoked_at=now,
    ).is_active(now=now, idle_timeout=timedelta(days=7))
