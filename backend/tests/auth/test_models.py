from __future__ import annotations

from corpus.auth.models import Base, MembershipRole


def test_auth_schema_has_hashed_bearer_credentials_and_opaque_conversations() -> None:
    tables = Base.metadata.tables

    assert {
        "users",
        "organizations",
        "memberships",
        "auth_sessions",
        "access_tokens",
        "corpus_conversations",
        "auth_rate_limits",
    } == set(tables)
    assert "refresh_token_hash" in tables["auth_sessions"].columns
    assert "refresh_token" not in tables["auth_sessions"].columns
    assert "token_hash" in tables["access_tokens"].columns
    assert "token" not in tables["access_tokens"].columns
    assert "public_id" in tables["corpus_conversations"].columns
    assert "route_session_id" in tables["corpus_conversations"].columns
    assert {role.value for role in MembershipRole} == {
        "owner",
        "admin",
        "member",
    }
