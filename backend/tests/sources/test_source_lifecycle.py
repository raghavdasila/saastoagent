from __future__ import annotations

from dataclasses import dataclass
from datetime import timedelta
from pathlib import Path
from types import SimpleNamespace
import uuid

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
from corpus.features.sources.connectors.api.staged_descriptions import (
    ApiStagedDescriptionRepository,
    ApiStagedDescriptionService,
    ApiStagedDescriptionUnavailable,
)
from corpus.features.sources.lifecycle import (
    SourceDependencyConflict,
    SourceLifecycleService,
)
from corpus.features.sources.ports import SourceDependencyReferences
from corpus.features.sources.repository import (
    LocalSourceRepository,
    SourceNotFound,
    SourceNotReady,
)
from corpus.session import create_guest_session, initialize_guest_session

from backend.tests.sources.test_api_contract_revision_reviews import (
    RuntimeOwnerProbe,
    SequentialIds,
    WorkspaceProbe,
    _create_sources_session,
)


OWNER = uuid.UUID("00000000-0000-0000-0000-000000000001")
AGENT = uuid.UUID("00000000-0000-0000-0000-000000000002")
BUILD = uuid.UUID("00000000-0000-0000-0000-000000000003")
DESIGN = uuid.UUID("00000000-0000-0000-0000-000000000004")


def _failed_source(repository: LocalSourceRepository):
    prepared = repository.begin_source(
        owner_key=str(OWNER),
        connector_key="api",
        display_name="Store API",
        original_filename="store.yaml",
        content=b"openapi: 3.0.3\n",
    )
    return repository.mark_failed(
        owner_key=str(OWNER),
        source_id=prepared.source.source_id,
        revision_id=prepared.revision.revision_id,
        failure_code="test_terminal_state",
        failure_message="Terminal state for lifecycle testing.",
    )


def test_description_history_is_immutable_and_never_changes_api_revision(
    tmp_path: Path,
) -> None:
    repository = LocalSourceRepository(tmp_path / "sources")
    source = _failed_source(repository)
    first = repository.save_description(
        owner_key=str(OWNER),
        source_id=source.source_id,
        expected_revision_id=source.revision.revision_id,
        filename="store.md",
        content=b"# Store API\nFirst description.",
    )

    with pytest.raises(SourceNotReady):
        repository.save_description(
            owner_key=str(OWNER),
            source_id=source.source_id,
            expected_revision_id="anotherrevision1",
            filename="replacement.md",
            content=b"# Must not replace the current description",
        )

    assert repository.get_description(
        owner_key=str(OWNER), source_id=source.source_id
    ) == first
    second = repository.save_description(
        owner_key=str(OWNER),
        source_id=source.source_id,
        expected_revision_id=source.revision.revision_id,
        filename="store-v2.markdown",
        content=b"# Store API\nUpdated description.",
    )

    reloaded = LocalSourceRepository(tmp_path / "sources")
    assert reloaded.get_description(
        owner_key=str(OWNER), source_id=source.source_id
    ) == second
    assert reloaded.get(
        owner_key=str(OWNER), source_id=source.source_id
    ).revision.revision_id == source.revision.revision_id
    record_dirs = tuple((tmp_path / "sources").rglob("d/records/*/record.json"))
    assert len(record_dirs) == 2


def test_staged_description_is_owner_conversation_session_bound_and_single_use(
    tmp_path: Path,
) -> None:
    sources = LocalSourceRepository(tmp_path / "sources")
    source = _failed_source(sources)
    service = ApiStagedDescriptionService(
        repository=ApiStagedDescriptionRepository(tmp_path / "sources"),
        sources=sources,
    )
    staged = service.stage(
        owner_key=str(OWNER),
        conversation_id="conversation-0001",
        route_session_id="source-description-session",
        filename="usage.md",
        content=b"# Usage\nUse collection routes.",
    )

    assert staged.state == "staged"
    assert service.current(
        owner_key=str(OWNER),
        conversation_id="conversation-0002",
        route_session_id="another-session",
    ) is None
    with pytest.raises(ApiStagedDescriptionUnavailable):
        service.save_current(
            owner_key=str(OWNER),
            conversation_id="conversation-0001",
            route_session_id="another-session",
            source_id=source.source_id,
            source_revision_id=source.revision.revision_id,
        )

    saved = service.save_current(
        owner_key=str(OWNER),
        conversation_id="conversation-0001",
        route_session_id="source-description-session",
        source_id=source.source_id,
        source_revision_id=source.revision.revision_id,
    )
    assert saved.filename == "usage.md"
    with pytest.raises(ApiStagedDescriptionUnavailable):
        service.save_current(
            owner_key=str(OWNER),
            conversation_id="conversation-0001",
            route_session_id="source-description-session",
            source_id=source.source_id,
            source_revision_id=source.revision.revision_id,
        )


@dataclass
class DependencyProbe:
    references: SourceDependencyReferences

    async def inspect_source_dependencies(
        self, organization_id: uuid.UUID, source_id: str
    ) -> SourceDependencyReferences:
        assert organization_id == OWNER
        assert len(source_id) == 16
        return self.references


@pytest.mark.asyncio
async def test_delete_exposes_every_dependency_and_never_cascades(
    tmp_path: Path,
) -> None:
    repository = LocalSourceRepository(tmp_path / "sources")
    source = _failed_source(repository)
    probe = DependencyProbe(
        SourceDependencyReferences(
            attached_agent_ids=(AGENT,),
            build_ids=(BUILD,),
            design_revision_ids=(DESIGN,),
        )
    )
    service = SourceLifecycleService(repository, probe)

    dependencies = await service.inspect_dependencies(OWNER, source.source_id)
    assert dependencies.blocks_delete is True
    assert dependencies.attached_agent_ids == (AGENT,)
    assert dependencies.build_ids == (BUILD,)
    assert dependencies.design_revision_ids == (DESIGN,)
    with pytest.raises(SourceDependencyConflict, match="Agent attachment"):
        await service.delete(OWNER, source.source_id)
    assert repository.get(owner_key=str(OWNER), source_id=source.source_id)

    probe.references = SourceDependencyReferences()
    await service.delete(OWNER, source.source_id)
    with pytest.raises(SourceNotFound):
        repository.get(owner_key=str(OWNER), source_id=source.source_id)


@pytest.mark.asyncio
async def test_delete_review_survives_reload_rejects_without_delete_and_accepts_once(
    tmp_path: Path,
) -> None:
    repository = LocalSourceRepository(tmp_path / "sources")
    source = _failed_source(repository)
    dependency_probe = DependencyProbe(SourceDependencyReferences())
    lifecycle = SourceLifecycleService(repository, dependency_probe)
    owner = RuntimeOwnerProbe(OWNER)
    compiled = compile_corpus_app()
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
                auth_settings=SimpleNamespace(
                    public_frontend_url="http://127.0.0.1:5199"
                ),
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
                    repository=repository,
                    get_source=lambda *, owner_key, source_id, revision_id=None: (
                        repository.get(owner_key=owner_key, source_id=source_id)
                        if revision_id is None
                        else repository.get_revision(
                            owner_key=owner_key,
                            source_id=source_id,
                            revision_id=revision_id,
                        )
                    ),
                ),
                source_graph_presenter=object(),
                source_connection_service=object(),
                source_contract_revision_service=object(),
                source_connection_check_service=object(),
                source_operation_curation_service=object(),
                source_staged_description_service=object(),
                source_lifecycle_service=lifecycle,
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

    async def stage(runtime, session_id: str, request_id: str):
        snapshot = await runtime.services.store.load(session_id)
        return await runtime.services.runner.run(
            OperationRequest(
                session_id=session_id,
                request_id=request_id,
                expected_session_version=snapshot.session_version,
                operation_id="sources.delete_api_source",
                source=OperationSource.SURFACE,
                arguments=FrozenJsonObject({}),
            )
        )

    runtime = await open_runtime("source-delete-first")
    try:
        session_id = "source-review-delete-lifecycle"
        await _create_sources_session(
            runtime,
            compiled,
            session_id,
            source.source_id,
            source.revision.revision_id,
        )
        pending = await stage(runtime, session_id, "delete-stage-first")
        assert pending.disposition is OperationDisposition.REQUIRES_REVIEW
        assert pending.review is not None
        await runtime.close()

        runtime = await open_runtime("source-delete-reopened")
        reopened = await runtime.services.store.load(session_id)
        projection = runtime.services.projector.project(reopened.state)
        review_surfaces = {
            item.surface_id: item for item in projection.surfaces.review
        }
        assert dict(review_surfaces["sources.delete_review"].props)
        assert dict(review_surfaces["sources.contract_revision_review"].props) == {}
        assert dict(review_surfaces["sources.routed_api_write_review"].props) == {}

        rejected = await runtime.services.runner.reject_review(
            pending.review.id,
            request_id="delete-reject",
            expected_session_version=reopened.session_version,
            session_id=session_id,
        )
        assert rejected.failure is not None
        assert rejected.failure.code == "review_rejected"
        assert repository.get(owner_key=str(OWNER), source_id=source.source_id)

        restaged = await stage(runtime, session_id, "delete-stage-second")
        assert restaged.review is not None
        dependency_probe.references = SourceDependencyReferences(
            attached_agent_ids=(AGENT,),
        )
        accept_snapshot = await runtime.services.store.load(session_id)
        stale = await runtime.services.runner.accept_review(
            restaged.review.id,
            request_id="delete-stale-accept",
            expected_session_version=accept_snapshot.session_version,
            session_id=session_id,
        )
        assert stale.disposition is OperationDisposition.FAILED
        assert stale.failure is not None
        assert stale.failure.code == "review_stale"
        assert repository.get(owner_key=str(OWNER), source_id=source.source_id)

        dependency_probe.references = SourceDependencyReferences()
        final_review = await stage(runtime, session_id, "delete-stage-final")
        assert final_review.review is not None
        final_snapshot = await runtime.services.store.load(session_id)
        deleted = await runtime.services.runner.accept_review(
            final_review.review.id,
            request_id="delete-accept",
            expected_session_version=final_snapshot.session_version,
            session_id=session_id,
        )
        assert deleted.disposition is OperationDisposition.COMPLETED
        assert deleted.outcome == "deleted"
        with pytest.raises(SourceNotFound):
            repository.get(owner_key=str(OWNER), source_id=source.source_id)
    finally:
        await runtime.close()
