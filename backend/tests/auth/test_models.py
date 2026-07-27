from __future__ import annotations

from corpus.auth.models import Base, MembershipRole


def test_owner_auth_schema_has_only_hashed_browser_credentials() -> None:
    tables = Base.metadata.tables

    assert {
        "users",
        "organizations",
        "memberships",
        "auth_sessions",
        "owner_route_claims",
        "owner_route_handles",
        "auth_rate_limits",
    }.issubset(tables)
    assert "token_hash" in tables["auth_sessions"].columns
    assert "token" not in tables["auth_sessions"].columns
    assert "token_hash" in tables["owner_route_handles"].columns
    assert "handle" not in tables["owner_route_handles"].columns
    assert {role.value for role in MembershipRole} == {
        "owner",
        "admin",
        "member",
    }
