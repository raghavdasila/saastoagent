from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from pathlib import Path
from types import SimpleNamespace
import uuid

import httpx
import pytest
from cryptography.fernet import Fernet
from pydantic import BaseModel
from routedeck_core.contracts.operations import (
    OperationDisposition,
    OperationRequest,
    OperationSource,
)
from routedeck_core.contracts.projection import FrozenJsonObject
from routedeck_sqlalchemy import open_sqlalchemy_routedeck_runtime

from corpus.auth.contracts import OwnerRouteContext
from corpus.bindings import bind_corpus_app
from corpus.composition import compile_corpus_app
from corpus.features.sources.connectors.api import connection_checks as checks_module
from corpus.session import create_guest_session, create_owner_session, initialize_guest_session

from backend.tests.sources.test_api_connection_checks import (
    OWNER,
    FixedVault,
    _fixture,
    _service,
)


@dataclass
class OwnerProbe:
    organization_id: uuid.UUID

    async def organization_id_for_route(self, route_session_id: str) -> uuid.UUID:
        assert route_session_id.startswith("source-check-")
        return self.organization_id

    async def owner_context_for_route(self, route_session_id: str) -> OwnerRouteContext:
        await self.organization_id_for_route(route_session_id)
        return OwnerRouteContext(
            display_name="Owner",
            organization_name="Safe Check Workspace",
            organization_slug="safe-check-workspace",
            role="owner",
            is_verified=True,
        )


class WorkspaceProjection(BaseModel):
    active_agent_count: int = 0
    source_count: int = 1


class WorkspaceProbe:
    async def for_route(self, route_session_id: str) -> WorkspaceProjection:
        assert route_session_id.startswith("source-check-")
        return WorkspaceProjection()


class SequentialIds:
    def __init__(self) -> None:
        self.value = 0

    def __call__(self, kind: str) -> str:
        self.value += 1
        return f"{kind}-source-check-{self.value}"


@pytest.mark.asyncio
async def test_sql_routedeck_guard_allows_exact_agent_check_and_blocks_stale_surface_selection(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    repository, source_id, revision_id, profile_id, contract_hash = _fixture(tmp_path)
    monkeypatch.setattr(checks_module, "MEDUSA_EFFECTIVE_CONTRACT_HASH", contract_hash)
    calls = 0

    async def respond(request: httpx.Request) -> httpx.Response:
        nonlocal calls
        calls += 1
        return httpx.Response(
            200,
            headers={"content-type": "application/json"},
            json={"product_types": []},
        )

    service = _service(repository, FixedVault(), httpx.MockTransport(respond))
    owner = OwnerProbe(OWNER)
    compiled = compile_corpus_app()
    runtime = await open_sqlalchemy_routedeck_runtime(
        compiled_app=compiled,
        application_factory=lambda resources: bind_corpus_app(
            compiled,
            owner,
            auth_service=owner,
            auth_limiter=object(),
            auth_mail=object(),
            auth_settings=SimpleNamespace(public_frontend_url="http://127.0.0.1:5199"),
            private_form_store=resources.store,
            private_form_codec=resources.codec,
            credential_transition=object(),
            agent_service=object(),
            designer_service=object(),
            builder_service=object(),
            sandbox_service=object(),
            evaluation_service=object(),
            channel_service=object(),
            deployment_service=object(),
            operations_service=object(),
            workspace_service=WorkspaceProbe(),
            source_service=SimpleNamespace(repository=repository),
            source_graph_presenter=object(),
            source_connection_service=object(),
            source_contract_revision_service=object(),
            source_connection_check_service=service,
            source_operation_curation_service=object(),
        ),
        session_factory=create_guest_session,
        session_initializer=initialize_guest_session,
        public_key_validator_factory=lambda _session: None,
        agent_driver_factory=None,
        database_url=f"sqlite+pysqlite:///{(tmp_path / 'routedeck.sqlite3').as_posix()}",
        encryption_key=Fernet.generate_key().decode("ascii"),
        instance_id="source-check-runtime",
        review_ttl=timedelta(minutes=15),
        resume_capability_ttl=timedelta(hours=1),
        worker_count=1,
        id_factory=SequentialIds(),
    )
    try:
        session_id = "source-check-route"
        initial = create_owner_session(
            compiled,
            session_id,
            now=datetime.now(UTC),
            resume_handle="resume-source-check-route",
            resume_ttl=timedelta(hours=1),
        )
        snapshot = await runtime.services.store.create(initial)
        opened = await runtime.services.runner.run(
            OperationRequest(
                session_id=session_id,
                request_id="open-sources",
                expected_session_version=snapshot.session_version,
                operation_id="workspace.open_sources",
                source=OperationSource.SURFACE,
                arguments=FrozenJsonObject({}),
            )
        )
        assert opened.disposition is OperationDisposition.COMPLETED
        hub = await runtime.services.store.load(session_id)
        api_opened = await runtime.services.runner.run(
            OperationRequest(
                session_id=session_id,
                request_id="open-api-source-workflow",
                expected_session_version=hub.session_version,
                operation_id="sources.open_api_creation",
                source=OperationSource.SURFACE,
                arguments=FrozenJsonObject({}),
            )
        )
        assert api_opened.disposition is OperationDisposition.COMPLETED
        exact = {
            "source_id": source_id,
            "source_revision_id": revision_id,
            "connection_profile_id": profile_id,
            "operation_id": "GetProductTypes",
        }
        selected = await runtime.services.store.load(session_id)
        succeeded = await runtime.services.runner.run(
            OperationRequest(
                session_id=session_id,
                request_id="safe-check-agent",
                expected_session_version=selected.session_version,
                operation_id="sources.test_api_connection",
                source=OperationSource.AGENT,
                arguments=FrozenJsonObject(exact),
            )
        )
        assert succeeded.disposition is OperationDisposition.COMPLETED
        assert succeeded.outcome == "checked"
        assert calls == 1
        assert len(service.list(
            owner_id=OWNER,
            source_id=source_id,
            source_revision_id=revision_id,
        )) == 1

        current_snapshot = await runtime.services.store.load(session_id)
        current = await runtime.services.runner.run(
            OperationRequest(
                session_id=session_id,
                request_id="safe-check-current-agent",
                expected_session_version=current_snapshot.session_version,
                operation_id="sources.test_api_connection",
                source=OperationSource.AGENT,
                arguments=FrozenJsonObject(
                    {"operation_id": "GetProductTypes"}
                ),
            )
        )
        assert current.disposition is OperationDisposition.COMPLETED
        assert current.outcome == "checked"
        assert calls == 2
        assert len(service.list(
            owner_id=OWNER,
            source_id=source_id,
            source_revision_id=revision_id,
        )) == 2

        stale_snapshot = await runtime.services.store.load(session_id)
        blocked = await runtime.services.runner.run(
            OperationRequest(
                session_id=session_id,
                request_id="safe-check-stale-surface",
                expected_session_version=stale_snapshot.session_version,
                operation_id="sources.test_api_connection",
                source=OperationSource.SURFACE,
                arguments=FrozenJsonObject(
                    {**exact, "connection_profile_id": "profilemissing01"}
                ),
            )
        )
        assert blocked.disposition is not OperationDisposition.COMPLETED
        assert blocked.failure is not None
        assert blocked.failure.code == "api_connection_check_selection_stale"
        assert calls == 2
        assert len(service.list(
            owner_id=OWNER,
            source_id=source_id,
            source_revision_id=revision_id,
        )) == 2
    finally:
        await runtime.close()
