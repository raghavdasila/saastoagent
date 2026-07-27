from __future__ import annotations

import asyncio
from pathlib import Path

from cryptography.fernet import Fernet
from fastapi.testclient import TestClient

from corpus.app.config import RouteDeckHostSettings
from corpus.auth.config import AuthSettings
from corpus.auth.migrations import upgrade_database
from corpus.main import create_live_app
from corpus.features.sources.config import SourceSettings
from corpus.runtime.config import CorpusRuntimeSettings


def test_live_http_app_serves_contract_and_creates_a_guest_lounge_session(
    tmp_path: Path,
) -> None:
    auth_database_url = f"sqlite+aiosqlite:///{(tmp_path / 'auth.sqlite3').as_posix()}"
    asyncio.run(upgrade_database(auth_database_url))
    settings = CorpusRuntimeSettings(
        host=RouteDeckHostSettings(
            routedeck_database_url=(
                f"sqlite+pysqlite:///{(tmp_path / 'http.sqlite3').as_posix()}"
            ),
            routedeck_state_encryption_key=Fernet.generate_key().decode("ascii"),
            routedeck_instance_id="corpus-http-test",
            routedeck_review_ttl_seconds=300,
            routedeck_resume_capability_ttl_seconds=600,
            routedeck_worker_count=1,
            routedeck_guest_cookie_name="corpus_guest",
            routedeck_guest_cookie_secure=False,
            routedeck_guest_cookie_path="/",
            routedeck_browser_origins=("http://127.0.0.1:5199",),
        ),
        auth=AuthSettings(
            database_url=auth_database_url,
            migration_revision="0001_owner_auth",
            reset_secret="r" * 40,
            verification_secret="v" * 40,
            auth_cookie_name="corpus_auth",
            owner_route_cookie_name="corpus_owner_route",
            auth_cookie_secure=False,
            auth_cookie_path="/",
            public_frontend_url="http://127.0.0.1:5199",
        ),
        sources=SourceSettings(data_root=tmp_path / "sources"),
        ollama_base_url="http://127.0.0.1:11434",
        ollama_model="gemma4:latest",
    )
    app = create_live_app(settings)

    with TestClient(app) as client:
        assert client.get("/healthz").json() == {"status": "ok"}
        assert client.get("/readyz").json() == {"status": "ready"}
        contract = client.get("/api/routedeck/contract")
        assert contract.status_code == 200
        assert contract.json()["frontend_contract"]["entry_node_id"] == (
            "workspace.lounge"
        )
        created = client.post(
            "/api/routedeck/sessions",
            headers={"Origin": "http://127.0.0.1:5199"},
            json={"request_id": "http-session-create"},
        )
        assert created.status_code == 201
        projection = created.json()["projection"]
        assert projection["current"]["node_id"] == "workspace.lounge"
        assert projection["surfaces"]["active"]["component"] == (
            "workspace.lounge"
        )
        assert "corpus_guest=" in created.headers["set-cookie"]
        guest_session_cookie = client.cookies.get("corpus_guest")
        assert guest_session_cookie is not None

        opened_registration = client.post(
            "/api/routedeck/dispatch",
            headers={"Origin": "http://127.0.0.1:5199"},
            json={
                "request_id": "open-registration",
                "expected_session_version": projection["session_version"],
                "operation_id": "workspace.open_registration",
                "arguments": {},
            },
        )
        assert opened_registration.status_code == 200
        registration_version = opened_registration.json()["session_version"]

        registered = client.post(
            "/api/auth/register",
            headers={"Origin": "http://127.0.0.1:5199"},
            json={
                "email": "owner@example.com",
                "password": "a sufficiently private password",
                "display_name": "Owner",
            },
        )
        assert registered.status_code == 201
        assert registered.json()["route_session_state"] == "adopted"
        assert client.cookies.get("corpus_guest") is None

        continued = client.post(
            "/api/routedeck/dispatch",
            headers={"Origin": "http://127.0.0.1:5199"},
            json={
                "request_id": "auth-continuation",
                "expected_session_version": registration_version,
                "operation_id": "workspace.authentication_completed",
                "arguments": {},
            },
        )
        assert continued.status_code == 200, continued.text
        assert continued.json()["outcome"] == "opened"
        owned = client.get("/api/routedeck/session")
        assert owned.status_code == 200
        assert owned.json()["projection"]["current"]["node_id"] == "workspace.home"

        client.cookies.clear()
        client.cookies.set(
            "corpus_guest",
            guest_session_cookie,
            domain="testserver.local",
            path="/",
        )
        rejected = client.get("/api/routedeck/session")
        assert rejected.status_code == 404
        assert "session_not_found" in rejected.text
