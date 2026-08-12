from __future__ import annotations

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

from corpus.bindings import bind_corpus_app
from corpus.composition import compile_corpus_app
from corpus.session import create_guest_session, create_owner_session, initialize_guest_session

from backend.tests.sources.test_api_connection_check_routedeck import (
    OwnerProbe,
    SequentialIds,
    WorkspaceProbe,
)
from backend.tests.sources.test_api_route_plans import OWNER, _service


@pytest.mark.asyncio
async def test_sql_routedeck_opens_nonexecuting_planner_from_agent_and_surface(
    tmp_path: Path,
) -> None:
    compiled = compile_corpus_app()
    route_plans, _engine, source_id, revision_id, _profile_id, _curation_id = _service(
        tmp_path.parent / "rp-route-plans"
    )
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
                source_service=SimpleNamespace(
                    get_source=lambda **_kwargs: SimpleNamespace(
                        source_id=source_id,
                        revision=SimpleNamespace(revision_id=revision_id),
                    )
                ),
                source_graph_presenter=object(),
                source_connection_service=object(),
                source_contract_revision_service=object(),
                source_connection_check_service=object(),
                source_operation_curation_service=object(),
                source_route_plan_service=route_plans,
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

    session_id = "source-check-route-planner"
    runtime = await open_runtime("source-route-plan-first")
    try:
        initial = create_owner_session(
            compiled,
            session_id,
            now=datetime.now(UTC),
            resume_handle="resume-source-route-plan",
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
                operation_id="sources.open_api_source",
                source=OperationSource.SURFACE,
                arguments=FrozenJsonObject(
                    {
                        "source_id": source_id,
                        "source_revision_id": revision_id,
                    }
                ),
            )
        )
        assert api_opened.disposition is OperationDisposition.COMPLETED
        selected = await runtime.services.store.load(session_id)
        planned = await runtime.services.runner.run(
            OperationRequest(
                session_id=session_id,
                request_id="prepare-from-agent",
                expected_session_version=selected.session_version,
                operation_id="sources.prepare_routed_api_test",
                source=OperationSource.AGENT,
                arguments=FrozenJsonObject({}),
            )
        )
        assert planned.disposition is OperationDisposition.COMPLETED
        assert planned.outcome == "opened"
    finally:
        await runtime.close()

    reopened = await open_runtime("source-route-plan-second")
    try:
        durable = await reopened.services.store.load(session_id)
        projection = reopened.services.projector.project(durable.state)
        detail = next(
            surface
            for surface in projection.surfaces.detail
            if surface.surface_id == "sources.api_operation_test"
        )
        assert {item.name: item.value.to_python() for item in detail.props} == {
            "open": True,
            "source_id": source_id,
            "source_revision_id": revision_id,
        }
        planned = await reopened.services.runner.run(
            OperationRequest(
                session_id=session_id,
                request_id="prepare-from-surface",
                expected_session_version=durable.session_version,
                operation_id="sources.prepare_routed_api_test",
                source=OperationSource.SURFACE,
                arguments=FrozenJsonObject({}),
            )
        )
        assert planned.disposition is OperationDisposition.COMPLETED
        assert planned.outcome == "opened"
        selected = await reopened.services.store.load(session_id)
        created = await reopened.services.runner.run(
            OperationRequest(
                session_id=session_id,
                request_id="create-plan-from-agent",
                expected_session_version=selected.session_version,
                operation_id="sources.create_api_route_plan",
                source=OperationSource.AGENT,
                arguments=FrozenJsonObject(
                    {
                        "request_text": "List widgets for this customer",
                        "profile_name": "Local",
                        "provided_inputs": {},
                    }
                ),
            )
        )
        assert created.disposition is OperationDisposition.COMPLETED, created.failure
        assert created.outcome == "planned"
        assert created.observation.to_dict() == {
            "state": "needs_input",
            "question": "What should Corpus use for customer_id?",
            "choices": [],
            "missing_inputs": ["customer_id"],
            "method": "GET",
            "path": "/widgets",
        }
        waiting = await reopened.services.store.load(session_id)
        continued = await reopened.services.runner.run(
            OperationRequest(
                session_id=session_id,
                request_id="continue-plan-from-surface",
                expected_session_version=waiting.session_version,
                operation_id="sources.continue_api_route_plan",
                source=OperationSource.SURFACE,
                arguments=FrozenJsonObject({"answer": "customer-1"}),
            )
        )
        assert continued.disposition is OperationDisposition.COMPLETED
        assert continued.outcome == "continued"
        assert continued.observation.to_dict()["state"] == "ready"
        assert len(_engine.calls) == 2
    finally:
        await reopened.close()
