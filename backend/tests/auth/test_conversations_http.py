from __future__ import annotations

import asyncio
import hashlib
from datetime import UTC, datetime
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from routedeck_core import RouteDeckRuntime
from routedeck_core.contracts.session import SessionSnapshot
from routedeck_core.ports import SessionStoreError
from routedeck_core.ports.session_store import SessionStoreErrorCode
from routedeck_core.projection import ProjectionProjector
from routedeck_fastapi import SameOriginMutationPolicy

from corpus.auth.conversations import create_conversation_router
from corpus.persistence import CorpusDatabase
from corpus.auth.http import AuthHttpProblem, auth_problem_response
from corpus.auth.service import AuthService
from corpus.composition import compile_corpus_app
from corpus.session import create_guest_session, create_principal_session_factory


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


def _runtime(session_factory=None) -> RouteDeckRuntime:
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
        session_factory=(
            session_factory
            if session_factory is not None
            else lambda app, session_id: create_guest_session(app, session_id)
        ),
        session_initializer=lambda _services, snapshot: snapshot,
        agent_driver=None,
        lifecycle=SimpleNamespace(close=lambda: None),
    )
    object.__setattr__(runtime, "conversation_runs", conversation_runs)
    return runtime


def test_new_conversation_entry_follows_exact_authenticated_principal(
    tmp_path: Path,
) -> None:
    database = CorpusDatabase(
        f"sqlite+aiosqlite:///{(tmp_path / 'auth.sqlite3').as_posix()}"
    )
    asyncio.run(database.create_schema_for_tests())
    service = AuthService(database)
    runtime = _runtime(create_principal_session_factory(service))
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
        anonymous_headers = {
            "Authorization": f"Bearer {anonymous.access_token}",
            "Origin": "http://127.0.0.1:5199",
        }
        with TestClient(app) as client:
            arrival = client.post("/api/conversations", headers=anonymous_headers)
            assert arrival.status_code == 201, arrival.text
            assert arrival.json()["current_node_id"] == "lounge.home"
            adopted = asyncio.run(
                service.resolve_conversation(
                    access_token=anonymous.access_token,
                    conversation_id=arrival.json()["id"],
                )
            )
            owner = asyncio.run(
                service.register(
                    email="conversation-owner@example.com",
                    password="a sufficiently private password",
                    display_name="Conversation Owner",
                    anonymous_access_token=anonymous.access_token,
                    conversation_id=adopted.public_id,
                    route_session_id=adopted.route_session_id,
                )
            )
            owner_headers = {
                "Authorization": f"Bearer {owner.tokens.access_token}",
                "Origin": "http://127.0.0.1:5199",
            }
            first = client.post("/api/conversations", headers=owner_headers)
            second = client.post("/api/conversations", headers=owner_headers)

            assert first.status_code == 201, first.text
            assert second.status_code == 201, second.text
            assert first.json()["id"] != second.json()["id"]
            assert first.json()["current_node_id"] == "workspace.home"
            assert second.json()["current_node_id"] == "workspace.home"

            owner_conversations = asyncio.run(
                service.list_conversations(owner.tokens.access_token)
            )
            route_ids = {
                item.public_id: item.route_session_id for item in owner_conversations
            }
            store = runtime.services.store
            assert isinstance(store, FakeStore)
            first_snapshot = store.snapshots[route_ids[first.json()["id"]]]
            second_snapshot = store.snapshots[route_ids[second.json()["id"]]]
            compiled = runtime.services.app.app
            for snapshot in (first_snapshot, second_snapshot):
                projection = ProjectionProjector(
                    compiled,
                    now=datetime.now(UTC),
                ).project(snapshot.state)
                assert projection.current.node_id == "workspace.home"
                assert projection.surfaces.active is not None
                assert projection.surfaces.active.surface_id == "workspace.home"
            assert first_snapshot.state.session_id != second_snapshot.state.session_id
            assert first_snapshot.state.current.node_id == "workspace.home"
    finally:
        asyncio.run(database.close())


def test_principal_session_factory_rejects_an_unknown_principal() -> None:
    resolver = SimpleNamespace(
        route_principal_kind=AsyncMock(return_value="unexpected")
    )
    factory = create_principal_session_factory(resolver)

    with pytest.raises(RuntimeError, match="principal is invalid"):
        asyncio.run(factory(compile_corpus_app(), "route-session"))


def test_catalog_creates_real_runtime_session_without_exposing_internal_id(
    tmp_path: Path,
) -> None:
    database = CorpusDatabase(
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


def test_anonymous_replacement_archives_old_mapping_after_provisioning(
    tmp_path: Path,
) -> None:
    database = CorpusDatabase(
        f"sqlite+aiosqlite:///{(tmp_path / 'auth.sqlite3').as_posix()}"
    )
    asyncio.run(database.create_schema_for_tests())
    service = AuthService(database)
    runtime = _runtime()
    app = FastAPI()
    app.add_exception_handler(AuthHttpProblem, auth_problem_response)
    app.include_router(
        create_conversation_router(
            service=service,
            mutation_policy=SameOriginMutationPolicy(
                trusted_origins=frozenset({"http://127.0.0.1:5199"})
            ),
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
            original = client.post("/api/conversations", headers=headers).json()
            response = client.post(
                f"/api/conversations/{original['id']}/replacement",
                headers=headers,
            )
            assert response.status_code == 201, response.text
            replacement = response.json()
            assert replacement["id"] != original["id"]
            assert "route_session_id" not in response.text
            assert client.get(
                f"/api/conversations/{original['id']}",
                headers={"Authorization": headers["Authorization"]},
            ).status_code == 404
            assert client.get(
                "/api/conversations",
                headers={"Authorization": headers["Authorization"]},
            ).json() == {"conversations": [replacement]}

            foreign = asyncio.run(service.issue_anonymous())
            store = runtime.services.store
            provision_count = len(store.creation_requests)
            denied = client.post(
                f"/api/conversations/{replacement['id']}/replacement",
                headers={
                    "Authorization": f"Bearer {foreign.access_token}",
                    "Origin": "http://127.0.0.1:5199",
                },
            )
            assert denied.status_code == 404
            assert len(store.creation_requests) == provision_count
    finally:
        asyncio.run(database.close())


def test_catalog_releases_only_a_conversation_whose_saved_contract_is_stale(
    tmp_path: Path,
) -> None:
    database = CorpusDatabase(
        f"sqlite+aiosqlite:///{(tmp_path / 'auth.sqlite3').as_posix()}"
    )
    asyncio.run(database.create_schema_for_tests())
    service = AuthService(database)
    runtime = _runtime()
    app = FastAPI()
    app.add_exception_handler(AuthHttpProblem, auth_problem_response)
    app.include_router(
        create_conversation_router(
            service=service,
            mutation_policy=SameOriginMutationPolicy(
                trusted_origins=frozenset({"http://127.0.0.1:5199"})
            ),
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

            store = runtime.services.store

            async def stale_contract(_session_id):
                raise SessionStoreError(
                    SessionStoreErrorCode.SESSION_UPGRADE_REQUIRED
                )

            store.load = stale_contract
            listed = client.get(
                "/api/conversations",
                headers={"Authorization": headers["Authorization"]},
            )
            assert listed.status_code == 200, listed.text
            assert listed.json() == {"conversations": []}

            store.load = FakeStore.load.__get__(store, FakeStore)
            replacement = client.post("/api/conversations", headers=headers)
            assert replacement.status_code == 201, replacement.text
    finally:
        asyncio.run(database.close())


def test_anonymous_replacement_keeps_old_mapping_when_provisioning_fails(
    tmp_path: Path,
) -> None:
    database = CorpusDatabase(
        f"sqlite+aiosqlite:///{(tmp_path / 'auth.sqlite3').as_posix()}"
    )
    asyncio.run(database.create_schema_for_tests())
    service = AuthService(database)
    runtime = _runtime()
    app = FastAPI()
    app.add_exception_handler(AuthHttpProblem, auth_problem_response)
    app.include_router(
        create_conversation_router(
            service=service,
            mutation_policy=SameOriginMutationPolicy(
                trusted_origins=frozenset({"http://127.0.0.1:5199"})
            ),
            runtime_provider=lambda _request: runtime,
        )
    )
    try:
        anonymous = asyncio.run(service.issue_anonymous())
        headers = {
            "Authorization": f"Bearer {anonymous.access_token}",
            "Origin": "http://127.0.0.1:5199",
        }
        with TestClient(app, raise_server_exceptions=False) as client:
            original = client.post("/api/conversations", headers=headers).json()
            object.__setattr__(
                runtime,
                "provision_session",
                AsyncMock(side_effect=RuntimeError("offline")),
            )
            response = client.post(
                f"/api/conversations/{original['id']}/replacement",
                headers=headers,
            )
            assert response.status_code == 500
            current = client.get(
                f"/api/conversations/{original['id']}",
                headers={"Authorization": headers["Authorization"]},
            )
            assert current.status_code == 200
    finally:
        asyncio.run(database.close())
