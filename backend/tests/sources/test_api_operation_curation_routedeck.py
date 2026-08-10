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
from routedeck_core.ports.executor import ExecutionContext
from routedeck_sqlalchemy import open_sqlalchemy_routedeck_runtime

from corpus.bindings import bind_corpus_app
from corpus.composition import compile_corpus_app
from corpus.features.sources.connectors.api.operation_curation import (
    ApiOperationCurationService,
)
from corpus.features.sources.connectors.api.connections import (
    ApiConnectionProfileRepository,
)
from corpus.features.sources.connectors.api.graph import ApiGraphPresenter
from corpus.features.sources.operations import InspectCurrentApiHandler
from corpus.session import create_guest_session, create_owner_session, initialize_guest_session

from backend.tests.sources.test_api_connection_check_routedeck import (
    OwnerProbe,
    SequentialIds,
    WorkspaceProbe,
)
from backend.tests.sources.test_api_operation_curation import OWNER, _ready_source


@pytest.mark.asyncio
async def test_agent_inspects_current_api_without_user_supplied_product_ids(
    tmp_path: Path,
) -> None:
    repository, source_id, revision_id = _ready_source(tmp_path)
    handler = InspectCurrentApiHandler(
        ApiGraphPresenter(repository),
        ApiOperationCurationService(repository),
        SimpleNamespace(profiles=ApiConnectionProfileRepository(repository)),
        OwnerProbe(OWNER),
    )
    outcome = await handler(
        {},
        ExecutionContext(
            session_id="source-check-inspection",
            request_id="inspect-current-api",
            attempt_id="inspect-current-api-attempt",
            node_id="sources.home",
            source=OperationSource.AGENT,
            context_fingerprint="inspection-context",
        ),
    )

    assert outcome.outcome == "inspected"
    observation = outcome.observation.to_dict()
    assert observation["source_id"] == source_id
    assert observation["source_revision_id"] == revision_id
    assert observation["saved_profile_count"] == 0
    assert {
        item["operation_id"] for item in observation["operations"]
    } == {"createWidget", "listWidgets"}
    assert observation["semantic_groups"] == [
        {
            "label": "widgets",
            "operation_ids": ["createWidget", "listWidgets"],
        }
    ]


@pytest.mark.asyncio
async def test_sql_routedeck_saves_exact_curation_and_guard_blocks_stale_inventory(
    tmp_path: Path,
) -> None:
    repository, source_id, revision_id = _ready_source(tmp_path)
    service = ApiOperationCurationService(repository)
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
            source_graph_presenter=ApiGraphPresenter(repository),
            source_connection_service=object(),
            source_contract_revision_service=object(),
            source_connection_check_service=SimpleNamespace(
                profiles=ApiConnectionProfileRepository(repository)
            ),
            source_operation_curation_service=service,
        ),
        session_factory=create_guest_session,
        session_initializer=initialize_guest_session,
        public_key_validator_factory=lambda _session: None,
        agent_driver_factory=None,
        database_url=f"sqlite+pysqlite:///{(tmp_path / 'routedeck.sqlite3').as_posix()}",
        encryption_key=Fernet.generate_key().decode("ascii"),
        instance_id="source-curation-runtime",
        review_ttl=timedelta(minutes=15),
        resume_capability_ttl=timedelta(hours=1),
        worker_count=1,
        id_factory=SequentialIds(),
    )
    try:
        session_id = "source-check-curation"
        initial = create_owner_session(
            compiled,
            session_id,
            now=datetime.now(UTC),
            resume_handle="resume-source-curation",
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
        selected = await runtime.services.store.load(session_id)
        inspected = await runtime.services.runner.run(
            OperationRequest(
                session_id=session_id,
                request_id="inspect-current-api-agent",
                expected_session_version=selected.session_version,
                operation_id="sources.inspect_current_api",
                source=OperationSource.AGENT,
                arguments=FrozenJsonObject({}),
            )
        )
        assert inspected.disposition is OperationDisposition.COMPLETED
        assert inspected.outcome == "inspected"

        inventory = service.inspect(
            owner_id=OWNER,
            source_id=source_id,
            source_revision_id=revision_id,
        )
        arguments = {
            "source_id": source_id,
            "source_revision_id": revision_id,
            "inventory_fingerprint": inventory.inventory_fingerprint,
            "included_operation_ids": ["listWidgets"],
            "excluded_operation_ids": [],
            "expected_current_curation_id": None,
        }
        selected = await runtime.services.store.load(session_id)
        saved = await runtime.services.runner.run(
            OperationRequest(
                session_id=session_id,
                request_id="save-curation-agent",
                expected_session_version=selected.session_version,
                operation_id="sources.save_api_operation_curation",
                source=OperationSource.AGENT,
                arguments=FrozenJsonObject(arguments),
            )
        )
        assert saved.disposition is OperationDisposition.COMPLETED
        assert saved.outcome == "saved"
        first_view = service.inspect(
            owner_id=OWNER,
            source_id=source_id,
            source_revision_id=revision_id,
        )
        assert len(first_view.history) == 1
        assert first_view.current is not None
        assert first_view.current.excluded_operation_ids == ("createWidget",)

        current = await runtime.services.store.load(session_id)
        resaved = await runtime.services.runner.run(
            OperationRequest(
                session_id=session_id,
                request_id="save-current-curation-agent",
                expected_session_version=current.session_version,
                operation_id="sources.save_api_operation_curation",
                source=OperationSource.AGENT,
                arguments=FrozenJsonObject(
                        {
                            "source_id": "bogus-source-001",
                            "source_revision_id": "bogus-revision01",
                            "included_operation_ids": ["createWidget"],
                            "excluded_operation_ids": ["listWidgets"],
                        }
                ),
            )
        )
        assert resaved.disposition is OperationDisposition.COMPLETED
        assert resaved.outcome == "saved"
        current_view = service.inspect(
            owner_id=OWNER,
            source_id=source_id,
            source_revision_id=revision_id,
        )
        assert current_view.current is not None
        assert current_view.current.included_operation_ids == ("createWidget",)
        assert current_view.current.excluded_operation_ids == ("listWidgets",)
        assert len(current_view.history) == 2

        stale = await runtime.services.store.load(session_id)
        blocked = await runtime.services.runner.run(
            OperationRequest(
                session_id=session_id,
                request_id="save-curation-stale-surface",
                expected_session_version=stale.session_version,
                operation_id="sources.save_api_operation_curation",
                source=OperationSource.SURFACE,
                arguments=FrozenJsonObject(
                    {
                        **arguments,
                        "inventory_fingerprint": "0" * 64,
                        "expected_current_curation_id": service.inspect(
                            owner_id=OWNER,
                            source_id=source_id,
                            source_revision_id=revision_id,
                        ).current.id,
                    }
                ),
            )
        )
        assert blocked.disposition is not OperationDisposition.COMPLETED
        assert blocked.failure is not None
        assert blocked.failure.code == "api_operation_curation_selection_stale"
        assert len(service.inspect(
            owner_id=OWNER,
            source_id=source_id,
            source_revision_id=revision_id,
        ).history) == 2
    finally:
        await runtime.close()
