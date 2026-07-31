from __future__ import annotations

import asyncio
import hashlib
from pathlib import Path
from types import SimpleNamespace

from fastapi import FastAPI
from fastapi.testclient import TestClient
from routedeck_core import RouteDeckRuntime
from routedeck_core.contracts.session import SessionSnapshot
from routedeck_fastapi import SameOriginMutationPolicy

from corpus.auth.conversations import create_conversation_router
from corpus.auth.database import AuthDatabase
from corpus.auth.http import AuthHttpProblem, auth_problem_response
from corpus.auth.service import AuthService
from corpus.composition import compile_corpus_app
from corpus.session import create_guest_session


class FakeStore:
    def __init__(self) -> None:
        self.snapshots: dict[str, SessionSnapshot] = {}
        self.creation_requests: list[tuple[str, str, str]] = []

    async def create_for_request(self, created, request_id, fingerprint):
        self.creation_requests.append(
            (created.session_id, request_id, fingerprint)
        )
        snapshot = SessionSnapshot(state=created)
        self.snapshots[created.session_id] = snapshot
        return snapshot

    async def load(self, session_id):
        return self.snapshots[session_id]


class FakeConversationRuns:
    def __init__(self) -> None:
        self.ensured: list[str] = []

    async def ensure_declared_entry_run(self, snapshot):
        self.ensured.append(snapshot.state.session_id)
        return None


def _runtime() -> RouteDeckRuntime:
    store = FakeStore()
    compiled = compile_corpus_app()
    services = SimpleNamespace(
        app=SimpleNamespace(app=compiled),
        store=store,
        runner=object(),
        id_factory=lambda prefix: f"{prefix}-id",
    )
    conversation_runs = FakeConversationRuns()
    runtime = RouteDeckRuntime(
        services=services,
        private_form_codec=None,  # type: ignore[arg-type]
        session_factory=lambda app, session_id: create_guest_session(
            app,
            session_id,
        ),
        session_initializer=lambda _services, snapshot: snapshot,
        agent_driver=None,
        lifecycle=SimpleNamespace(close=lambda: None),
    )
    object.__setattr__(runtime, "conversation_runs", conversation_runs)
    return runtime


def test_catalog_creates_real_runtime_session_without_exposing_internal_id(
    tmp_path: Path,
) -> None:
    database = AuthDatabase(
        f"sqlite+aiosqlite:///{(tmp_path / 'auth.sqlite3').as_posix()}"
    )
    asyncio.run(database.create_schema_for_tests())
    service = AuthService(database)
    runtime = _runtime()
    policy = SameOriginMutationPolicy(
        trusted_origins=frozenset({"http://127.0.0.1:5199"})
    )
    app = FastAPI()
    app.add_exception_handler(AuthHttpProblem, auth_problem_response)
    app.include_router(
        create_conversation_router(
            service=service,
            mutation_policy=policy,
            runtime_provider=lambda _request: runtime,
        )
    )
    try:
        anonymous = asyncio.run(service.issue_anonymous())
        headers = {
            "Authorization": f"Bearer {anonymous.access_token}",
            "Origin": "http://127.0.0.1:5199",
        }
        with TestClient(app) as client:
            created = client.post("/api/conversations", headers=headers)
            assert created.status_code == 201, created.text
            assert set(created.json()) == {
                "id",
                "current_node_id",
                "session_version",
                "updated_at",
                "active_run",
            }
            assert created.json()["current_node_id"] == "lounge.home"
            assert runtime.conversation_runs.ensured
            assert "route_session_id" not in created.text
            store = runtime.services.store
            assert isinstance(store, FakeStore)
            assert len(store.creation_requests) == 1
            session_id, request_id, fingerprint = store.creation_requests[0]
            assert session_id == runtime.conversation_runs.ensured[0]
            assert request_id
            assert fingerprint == hashlib.sha256(
                b"routedeck.session-creation.v1"
            ).hexdigest()

            listed = client.get(
                "/api/conversations",
                headers={"Authorization": headers["Authorization"]},
            )
            assert listed.json() == {"conversations": [created.json()]}

            second = client.post("/api/conversations", headers=headers)
            assert second.status_code == 409
            assert second.json()["code"] == "conversation_limit_reached"
    finally:
        asyncio.run(database.close())
