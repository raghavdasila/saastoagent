from __future__ import annotations

import asyncio
from pathlib import Path

from fastapi import FastAPI
from fastapi.testclient import TestClient
from routedeck_fastapi import SameOriginMutationPolicy

from corpus.persistence import CorpusDatabase
from corpus.auth.http import AuthHttpProblem, auth_problem_response, create_auth_router
from corpus.auth.rate_limits import AuthRateLimiter, RateLimitExceeded
from corpus.auth.security import hash_opaque_token
from corpus.auth.service import AuthService


def _app(
    database: CorpusDatabase,
    *,
    limiter=None,
    trusted_proxies: tuple[str, ...] = (),
) -> FastAPI:
    app = FastAPI()
    app.add_exception_handler(AuthHttpProblem, auth_problem_response)
    app.include_router(
        create_auth_router(
            service=AuthService(database),
            limiter=limiter or AuthRateLimiter(database),
            trusted_proxies=trusted_proxies,
            mutation_policy=SameOriginMutationPolicy(
                trusted_origins=frozenset({"http://127.0.0.1:5199"})
            ),
        )
    )
    return app


def test_anonymous_refresh_session_and_signout_are_bearer_only(
    tmp_path: Path,
) -> None:
    database = CorpusDatabase(
        f"sqlite+aiosqlite:///{(tmp_path / 'auth.sqlite3').as_posix()}"
    )
    asyncio.run(database.create_schema_for_tests())
    try:
        with TestClient(_app(database)) as client:
            anonymous = client.post(
                "/api/auth/anonymous",
                headers={"Origin": "http://127.0.0.1:5199"},
            )
            assert anonymous.status_code == 201
            tokens = anonymous.json()
            assert tokens["principal"] == {"type": "anonymous"}
            assert "set-cookie" not in anonymous.headers

            current = client.get(
                "/api/auth/session",
                headers={
                    "Authorization": f"Bearer {tokens['access_token']}"
                },
            )
            assert current.json() == {"type": "anonymous"}

            refreshed = client.post(
                "/api/auth/refresh",
                headers={"Origin": "http://127.0.0.1:5199"},
                json={"refresh_token": tokens["refresh_token"]},
            )
            assert refreshed.status_code == 200
            assert refreshed.json()["refresh_token"] != tokens["refresh_token"]
            stale = client.post(
                "/api/auth/refresh",
                headers={"Origin": "http://127.0.0.1:5199"},
                json={"refresh_token": tokens["refresh_token"]},
            )
            assert stale.status_code == 401

            signed_out = client.post(
                "/api/auth/sign-out",
                headers={
                    "Origin": "http://127.0.0.1:5199",
                    "Authorization": (
                        f"Bearer {refreshed.json()['access_token']}"
                    ),
                },
            )
            assert signed_out.status_code == 204
            assert "set-cookie" not in signed_out.headers
    finally:
        asyncio.run(database.close())


class RecordingLimiter:
    def __init__(self, *, reject: bool = False) -> None:
        self.reject = reject
        self.calls = []

    async def consume(self, **values) -> None:
        self.calls.append(values)
        if self.reject:
            raise RateLimitExceeded("limited")


def test_anonymous_and_refresh_apply_explicit_rate_limits(tmp_path: Path) -> None:
    database = CorpusDatabase(
        f"sqlite+aiosqlite:///{(tmp_path / 'auth.sqlite3').as_posix()}"
    )
    asyncio.run(database.create_schema_for_tests())
    recording = RecordingLimiter()
    try:
        with TestClient(
            _app(
                database,
                limiter=recording,
                trusted_proxies=("testclient",),
            )
        ) as client:
            anonymous = client.post(
                "/api/auth/anonymous",
                headers={
                    "Origin": "http://127.0.0.1:5199",
                    "X-Forwarded-For": "198.51.100.8, 10.0.0.1",
                },
            )
            refresh_token = anonymous.json()["refresh_token"]
            refreshed = client.post(
                "/api/auth/refresh",
                headers={"Origin": "http://127.0.0.1:5199"},
                json={"refresh_token": refresh_token},
            )
        assert refreshed.status_code == 200
        assert recording.calls[0]["scope"] == "anonymous-ip"
        assert recording.calls[0]["subject"] == "198.51.100.8"
        assert recording.calls[1]["scope"] == "refresh-token"
        assert recording.calls[1]["subject"] == hash_opaque_token(refresh_token)

        rejecting = RecordingLimiter(reject=True)
        with TestClient(_app(database, limiter=rejecting)) as client:
            limited = client.post(
                "/api/auth/anonymous",
                headers={"Origin": "http://127.0.0.1:5199"},
            )
        assert limited.status_code == 429
        assert limited.json() == {
            "code": "rate_limit_exceeded",
            "message": "Too many authentication attempts. Try again later.",
        }
    finally:
        asyncio.run(database.close())


def test_recover_is_removed_and_mutations_reject_cross_origin(
    tmp_path: Path,
) -> None:
    database = CorpusDatabase(
        f"sqlite+aiosqlite:///{(tmp_path / 'auth.sqlite3').as_posix()}"
    )
    asyncio.run(database.create_schema_for_tests())
    try:
        with TestClient(_app(database)) as client:
            assert client.post("/api/auth/recover").status_code == 404
            response = client.post(
                "/api/auth/anonymous",
                headers={"Origin": "https://attacker.invalid"},
            )
        assert response.status_code == 403
        assert response.json()["code"] == "mutation_origin_rejected"
    finally:
        asyncio.run(database.close())
