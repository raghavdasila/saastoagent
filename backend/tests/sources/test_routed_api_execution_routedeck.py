from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from pathlib import Path
from types import SimpleNamespace

import pytest
from cryptography.fernet import Fernet
from routedeck_core.contracts.operations import (
    OperationDisposition,
    OperationRequest,
    OperationSource,
)
from routedeck_core.contracts.projection import FrozenJsonObject
from routedeck_sqlalchemy import open_sqlalchemy_routedeck_runtime
from pydantic import BaseModel

from corpus.auth.contracts import OwnerRouteContext
from corpus.bindings import bind_corpus_app
from corpus.composition import compile_corpus_app
from corpus.features.sources.connectors.api.routed_executions import (
    ApiRoutedExecutionConflict,
    ApiRoutedExecutionView,
)
from corpus.session import create_guest_session, create_owner_session, initialize_guest_session

from backend.tests.sources.test_api_connection_check_routedeck import SequentialIds
from backend.tests.sources.test_api_route_plans import OWNER


PLAN = "planopaque000001"


@dataclass
class OwnerProbe:
    organization_id: object

    async def organization_id_for_route(self, route_session_id: str):
        assert route_session_id.startswith("source-routed-")
        return self.organization_id

    async def owner_context_for_route(self, route_session_id: str):
        await self.organization_id_for_route(route_session_id)
        return OwnerRouteContext(
            display_name="Owner",
            organization_name="Routed Workspace",
            organization_slug="routed-workspace",
            role="owner",
            is_verified=True,
        )


class WorkspaceProjection(BaseModel):
    active_agent_count: int = 0
    source_count: int = 1


class WorkspaceProbe:
    async def for_route(self, route_session_id: str) -> WorkspaceProjection:
        assert route_session_id.startswith("source-routed-")
        return WorkspaceProjection()


class PlanProbe:
    def locate(self, *, owner_id, plan_id):
        assert owner_id == OWNER
        assert plan_id == PLAN
        return SimpleNamespace(conversation_id="conversation-owner-a")


@dataclass
class ExecutionProbe:
    mode: str = "success"
    stale: bool = False
    calls: int = 0

    def __post_init__(self):
        self.plans = PlanProbe()

    def require_variant(self, **kwargs):
        assert kwargs["plan_id"] == PLAN
        if self.stale:
            raise ApiRoutedExecutionConflict("The exact route plan changed.")
        return SimpleNamespace(plan_id=PLAN)

    async def execute(self, **kwargs):
        self.calls += 1
        assert kwargs["plan_id"] == PLAN
        safety = kwargs["expected_safety"]
        if safety == "write":
            assert kwargs["approved_write"] is True
        now = datetime.now(UTC)
        unknown = self.mode == "unknown"
        return ApiRoutedExecutionView(
            result_id="resultopaque0001",
            plan_id=PLAN,
            source_id="sourceopaque0001",
            source_revision_id="revisionopaque01",
            operation_id="CreateCart" if safety == "write" else "GetProductTypes",
            method="POST" if safety == "write" else "GET",
            path_template="/store/carts" if safety == "write" else "/store/product-types",
            safety=safety,
            status="outcome_unknown" if unknown else "succeeded",
            delivery="possibly_sent" if unknown else "response_received",
            status_code=None if unknown else 200,
            response_media_type=None if unknown else "application/json",
            response_byte_count=0,
            response_body_sha256=None,
            error_code="transport_outcome_unknown" if unknown else None,
            public_message=None,
            validation_issue_count=0,
            validation_phases=(),
            outcome_verified=True if safety == "read" and not unknown else None,
            http_call_count=1,
            started_at=now,
            finished_at=now,
            traces=(),
        )


@pytest.mark.asyncio
async def test_sql_routedeck_read_and_durable_write_review_lifecycle(tmp_path: Path) -> None:
    probe = ExecutionProbe()
    runtime, reopen = await _runtime(tmp_path, probe)
    session_id = "source-routed-review"
    try:
        await _create_sources_session(runtime, session_id)
        read_request = await _request(
            runtime,
            session_id,
            "sources.test_routed_api_read",
            "read-request-0001",
        )
        read = await runtime.services.runner.run(read_request)
        assert read.disposition is OperationDisposition.COMPLETED, read.failure
        assert read.outcome == "observed"
        assert probe.calls == 1
        replayed = await runtime.services.runner.run(read_request)
        assert replayed == read
        assert probe.calls == 1

        staged = await _dispatch(runtime, session_id, "sources.test_routed_api_write", "write-stage-00001")
        assert staged.disposition is OperationDisposition.REQUIRES_REVIEW
        assert staged.review is not None
        assert probe.calls == 1
        await runtime.close()

        runtime = await reopen("source-routed-reopened")
        snapshot = await runtime.services.store.load(session_id)
        projection = runtime.services.projector.project(snapshot.state)
        review_surfaces = {
            surface.surface_id: surface for surface in projection.surfaces.review
        }
        assert dict(review_surfaces["sources.routed_api_write_review"].props)
        assert dict(review_surfaces["sources.contract_revision_review"].props) == {}
        rejected = await runtime.services.runner.reject_review(
            staged.review.id,
            request_id="write-reject-0001",
            expected_session_version=snapshot.session_version,
            session_id=session_id,
        )
        assert rejected.failure is not None
        assert rejected.failure.code == "review_rejected"
        assert probe.calls == 1

        restaged = await _dispatch(runtime, session_id, "sources.test_routed_api_write", "write-stage-00002")
        before = await runtime.services.store.load(session_id)
        accepted = await runtime.services.runner.accept_review(
            restaged.review.id,
            request_id="write-accept-0001",
            expected_session_version=before.session_version,
            session_id=session_id,
        )
        assert accepted.disposition is OperationDisposition.COMPLETED
        assert accepted.outcome == "observed"
        assert probe.calls == 2
    finally:
        await runtime.close()


@pytest.mark.asyncio
async def test_sql_routedeck_write_stale_and_unknown_are_native_terminal_states(
    tmp_path: Path,
) -> None:
    probe = ExecutionProbe()
    runtime, _reopen = await _runtime(tmp_path, probe)
    try:
        stale_session = "source-routed-stale"
        await _create_sources_session(runtime, stale_session)
        staged = await _dispatch(runtime, stale_session, "sources.test_routed_api_write", "write-stale-00001")
        probe.stale = True
        before = await runtime.services.store.load(stale_session)
        stale = await runtime.services.runner.accept_review(
            staged.review.id,
            request_id="write-stale-accept",
            expected_session_version=before.session_version,
            session_id=stale_session,
        )
        assert stale.disposition is OperationDisposition.FAILED
        assert stale.failure is not None
        assert stale.failure.code == "review_stale"
        assert probe.calls == 0

        probe.stale = False
        probe.mode = "unknown"
        unknown_session = "source-routed-unknown"
        await _create_sources_session(runtime, unknown_session)
        staged = await _dispatch(runtime, unknown_session, "sources.test_routed_api_write", "write-unknown-0001")
        before = await runtime.services.store.load(unknown_session)
        unknown = await runtime.services.runner.accept_review(
            staged.review.id,
            request_id="write-unknown-accept",
            expected_session_version=before.session_version,
            session_id=unknown_session,
        )
        assert unknown.disposition is OperationDisposition.EXTERNAL_OUTCOME_UNKNOWN
        assert unknown.failure is not None
        assert unknown.failure.code == "external_outcome_unknown"
        assert unknown.evidence.delivery_phase.value == "possibly_sent"
        assert probe.calls == 1
    finally:
        await runtime.close()


async def _runtime(tmp_path: Path, probe: ExecutionProbe):
    compiled = compile_corpus_app()
    owner = OwnerProbe(OWNER)
    database_url = f"sqlite+pysqlite:///{(tmp_path / 'routedeck.sqlite3').as_posix()}"
    encryption_key = Fernet.generate_key().decode("ascii")
    ids = SequentialIds()

    async def open_runtime(instance_id: str):
        return await open_sqlalchemy_routedeck_runtime(
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
                source_service=object(),
                source_graph_presenter=object(),
                source_connection_service=object(),
                source_contract_revision_service=object(),
                source_connection_check_service=object(),
                source_operation_curation_service=object(),
                source_routed_execution_service=probe,
            ),
            session_factory=create_guest_session,
            session_initializer=initialize_guest_session,
            public_key_validator_factory=lambda _session: None,
            agent_driver_factory=None,
            database_url=database_url,
            encryption_key=encryption_key,
            instance_id=instance_id,
            review_ttl=timedelta(minutes=15),
            resume_capability_ttl=timedelta(hours=1),
            worker_count=1,
            id_factory=ids,
        )

    return await open_runtime("source-routed-first"), open_runtime


async def _create_sources_session(runtime, session_id: str) -> None:
    compiled = compile_corpus_app()
    initial = create_owner_session(
        compiled,
        session_id,
        now=datetime.now(UTC),
        resume_handle=f"resume-{session_id}",
        resume_ttl=timedelta(hours=1),
    )
    snapshot = await runtime.services.store.create(initial)
    opened = await runtime.services.runner.run(
        OperationRequest(
            session_id=session_id,
            request_id=f"open-{session_id}",
            expected_session_version=snapshot.session_version,
            operation_id="workspace.open_sources",
            source=OperationSource.SURFACE,
            arguments=FrozenJsonObject({}),
        )
    )
    assert opened.disposition is OperationDisposition.COMPLETED


async def _dispatch(runtime, session_id: str, operation_id: str, request_id: str):
    return await runtime.services.runner.run(
        await _request(runtime, session_id, operation_id, request_id)
    )


async def _request(runtime, session_id: str, operation_id: str, request_id: str):
    snapshot = await runtime.services.store.load(session_id)
    return OperationRequest(
        session_id=session_id,
        request_id=request_id,
        expected_session_version=snapshot.session_version,
        operation_id=operation_id,
        source=OperationSource.SURFACE,
        arguments=FrozenJsonObject({"plan_id": PLAN}),
    )
