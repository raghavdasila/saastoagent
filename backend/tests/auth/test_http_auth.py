from __future__ import annotations

import asyncio
from pathlib import Path

from fastapi import FastAPI
from fastapi.testclient import TestClient
from routedeck_fastapi import SameOriginMutationPolicy

from corpus.auth.config import AuthSettings
from corpus.auth.database import AuthDatabase
from corpus.auth.http import AuthHttpProblem, auth_problem_response, create_auth_router
from corpus.auth.mail import OwnerMailDelivery
from corpus.auth.rate_limits import AuthRateLimiter
from corpus.auth.service import AuthService


class RecordingMail(OwnerMailDelivery):
    def __init__(self) -> None:
        self.verification: list[tuple[str, str]] = []
        self.resets: list[tuple[str, str]] = []

    async def send_verification(self, recipient: str, link: str) -> None:
        self.verification.append((recipient, link))

    async def send_password_reset(self, recipient: str, link: str) -> None:
        self.resets.append((recipient, link))


def _settings(database_url: str) -> AuthSettings:
    return AuthSettings(
        database_url=database_url,
        migration_revision="0001_owner_auth",
        reset_secret="r" * 40,
        verification_secret="v" * 40,
        auth_cookie_name="corpus_auth",
        owner_route_cookie_name="corpus_owner_route",
        auth_cookie_secure=False,
        auth_cookie_path="/",
        public_frontend_url="http://127.0.0.1:5199",
    )


def test_owner_auth_http_contract_sets_and_revokes_http_only_cookies(
    tmp_path: Path,
) -> None:
    database_url = f"sqlite+aiosqlite:///{(tmp_path / 'auth.sqlite3').as_posix()}"
    database = AuthDatabase(database_url)
    asyncio.run(database.create_schema_for_tests())
    settings = _settings(database_url)
    mail = RecordingMail()
    service = AuthService(
        database,
        reset_secret=settings.reset_secret.get_secret_value(),
        verification_secret=settings.verification_secret.get_secret_value(),
    )
    app = FastAPI()
    app.add_exception_handler(AuthHttpProblem, auth_problem_response)
    app.include_router(
        create_auth_router(
            service=service,
            limiter=AuthRateLimiter(database),
            mail=mail,
            settings=settings,
            mutation_policy=SameOriginMutationPolicy(
                trusted_origins=frozenset({"http://127.0.0.1:5199"})
            ),
            guest_cookie_name="corpus_guest",
            route_session_exists=lambda _request, _session_id: _true(),
        )
    )
    try:
        with TestClient(app) as client:
            client.cookies.set(
                "corpus_guest",
                "guest-route-1",
                domain="testserver.local",
                path="/",
            )
            registered = client.post(
                "/api/auth/register",
                headers={"Origin": "http://127.0.0.1:5199"},
                json={
                    "email": "owner@example.com",
                    "password": "a sufficiently private password",
                    "display_name": "Ada",
                },
            )
            assert registered.status_code == 201
            assert registered.json()["organization"]["name"] == "Ada's Workspace"
            assert "corpus_auth=" in registered.headers["set-cookie"]
            assert "corpus_owner_route=" in registered.headers["set-cookie"]
            assert client.cookies.get("corpus_guest") is None
            assert "auth_token" not in registered.text

            current = client.get("/api/auth/session")
            assert current.status_code == 200
            assert current.json()["owner"]["is_verified"] is False

            sent = client.post(
                "/api/auth/verification-email",
                headers={"Origin": "http://127.0.0.1:5199"},
                json={},
            )
            assert sent.status_code == 204
            assert len(mail.verification) == 1

            signed_out = client.post(
                "/api/auth/sign-out",
                headers={"Origin": "http://127.0.0.1:5199"},
                json={},
            )
            assert signed_out.status_code == 204
            assert client.get("/api/auth/session").status_code == 401
    finally:
        asyncio.run(database.close())


def test_mutations_reject_cross_origin_with_stable_auth_problem(tmp_path: Path) -> None:
    database_url = f"sqlite+aiosqlite:///{(tmp_path / 'auth.sqlite3').as_posix()}"
    database = AuthDatabase(database_url)
    asyncio.run(database.create_schema_for_tests())
    settings = _settings(database_url)
    app = FastAPI()
    app.add_exception_handler(AuthHttpProblem, auth_problem_response)
    app.include_router(
        create_auth_router(
            service=AuthService(database),
            limiter=AuthRateLimiter(database),
            mail=RecordingMail(),
            settings=settings,
            mutation_policy=SameOriginMutationPolicy(
                trusted_origins=frozenset({"http://127.0.0.1:5199"})
            ),
            guest_cookie_name="corpus_guest",
            route_session_exists=lambda _request, _session_id: _true(),
        )
    )
    try:
        with TestClient(app) as client:
            response = client.post(
                "/api/auth/password-reset/request",
                headers={"Origin": "https://attacker.invalid"},
                json={"email": "owner@example.com"},
            )
        assert response.status_code == 403
        assert response.json() == {
            "code": "mutation_origin_rejected",
            "message": "The mutation request origin is not authorized.",
        }
    finally:
        asyncio.run(database.close())


async def _true() -> bool:
    return True
