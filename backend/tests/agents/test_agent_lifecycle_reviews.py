from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
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
from routedeck_core.contracts.session import Location
from routedeck_sqlalchemy import open_sqlalchemy_routedeck_runtime

from corpus.auth.contracts import OwnerRouteContext
from corpus.auth.models import Organization
from corpus.bindings import bind_corpus_app
from corpus.composition import compile_corpus_app
from corpus.features.agents.ports import AgentNotFound, AttachableSource
from corpus.features.agents.repository import SqlAlchemyAgentRepository
from corpus.features.agents.schemas import CreateAgentArguments
from corpus.features.agents.service import AgentService
from corpus.persistence import CorpusDatabase
from corpus.session import create_guest_session, initialize_guest_session


@dataclass
class RuntimeOwnerProbe:
    organization_id: uuid.UUID

    async def organization_id_for_route(self, route_session_id: str) -> uuid.UUID:
        if not route_session_id.startswith("agent-review-"):
            raise RuntimeError("unexpected route session")
        return self.organization_id

    async def owner_context_for_route(self, route_session_id: str) -> OwnerRouteContext:
        await self.organization_id_for_route(route_session_id)
        return OwnerRouteContext(
            display_name="Owner",
            organization_name="Review Workspace",
            organization_slug="review-workspace",
            role="owner",
            is_verified=True,
        )


@dataclass
class RuntimeSourceProbe:
    organization_id: uuid.UUID

    async def ready_current(
        self,
        organization_id: uuid.UUID,
        source_id: str,
    ) -> AttachableSource:
        if organization_id != self.organization_id or source_id != "source-ready-001":
            raise RuntimeError("unexpected Source")
        return AttachableSource(
            source_id="source-ready-001",
            source_revision_id="revision-ready01",
            display_name="Ready API",
        )

    async def exact_revision(
        self,
        organization_id: uuid.UUID,
        source_id: str,
        source_revision_id: str,
    ) -> AttachableSource:
        source = await self.ready_current(organization_id, source_id)
        if source_revision_id != source.source_revision_id:
            raise RuntimeError("unexpected Source revision")
        return source


class SequentialIds:
    def __init__(self) -> None:
        self.value = 0

    def __call__(self, kind: str) -> str:
        self.value += 1
        return f"{kind}-agent-lifecycle-{self.value}"


@pytest.mark.asyncio
async def test_route_deck_review_rejection_reopen_acceptance_and_guard_recheck(
    tmp_path: Path,
) -> None:
    corpus = CorpusDatabase(
        f"sqlite+aiosqlite:///{(tmp_path / 'corpus.sqlite3').as_posix()}"
    )
    await corpus.create_schema_for_tests()
    organization = Organization(
        name="Review Workspace",
        slug=f"review-{uuid.uuid4().hex}",
        created_at=datetime.now(UTC),
    )
    async with corpus.session() as session:
        async with session.begin():
            session.add(organization)
            await session.flush()
    service = AgentService(
        SqlAlchemyAgentRepository(corpus),
        RuntimeSourceProbe(organization.id),
    )
    owner = RuntimeOwnerProbe(organization.id)
    compiled = compile_corpus_app()
    route_database_url = (
        f"sqlite+pysqlite:///{(tmp_path / 'routedeck.sqlite3').as_posix()}"
    )
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
                agent_service=service,
                designer_service=object(),
                builder_service=object(),
                sandbox_service=object(),
                evaluation_service=object(),
                channel_service=object(),
                deployment_service=object(),
                operations_service=object(),
                workspace_service=object(),
                source_service=object(),
                source_graph_presenter=object(),
                    source_connection_service=object(),
                source_contract_revision_service=object(),
                source_connection_check_service=object(),
                source_operation_curation_service=object(),
            ),
            session_factory=create_guest_session,
            session_initializer=initialize_guest_session,
            public_key_validator_factory=lambda _session: None,
            agent_driver_factory=None,
            database_url=route_database_url,
            encryption_key=encryption_key,
            instance_id=instance_id,
            review_ttl=timedelta(minutes=15),
            resume_capability_ttl=timedelta(hours=1),
            worker_count=1,
            id_factory=ids,
        )

    runtime = await open_runtime("agent-lifecycle-first")
    try:
        rejected_agent = await service.create(
            organization.id,
            CreateAgentArguments(name="Rejected Agent", instructions="Remain active."),
        )
        rejected_session = await _create_selected_session(
            runtime,
            compiled,
            service,
            rejected_agent.id,
            "agent-review-rejected",
        )
        proposed = await _stage_review(
            runtime,
            rejected_session,
            rejected_agent.id,
            operation_id="agents.archive_agent",
            request_id="archive-proposal",
        )
        assert proposed.disposition is OperationDisposition.REQUIRES_REVIEW
        assert proposed.review is not None
        persisted = await runtime.services.store.find_review(
            rejected_session,
            proposed.review.id,
        )
        assert persisted is not None
        assert persisted.attempt.operation_id == "agents.archive_agent"
        await runtime.close()

        runtime = await open_runtime("agent-lifecycle-reopened")
        reopened = await runtime.services.store.load(rejected_session)
        projection = runtime.services.projector.project(reopened.state)
        review_surfaces = {
            surface.surface_id: surface for surface in projection.surfaces.review
        }
        assert set(review_surfaces) == {
            "agents.archive_review",
            "agents.delete_review",
        }
        archive_props = {
            prop.name: prop.value.to_python()
            for prop in review_surfaces["agents.archive_review"].props
        }
        delete_props = {
            prop.name: prop.value.to_python()
            for prop in review_surfaces["agents.delete_review"].props
        }
        assert archive_props["state"] == "pending"
        assert delete_props == {}
        rejected = await runtime.services.runner.reject_review(
            proposed.review.id,
            request_id="archive-rejected",
            expected_session_version=reopened.session_version,
            session_id=rejected_session,
        )
        assert rejected.disposition is OperationDisposition.FAILED
        assert rejected.failure is not None
        assert rejected.failure.code == "review_rejected"
        assert (await service.get(organization.id, rejected_agent.id)).id == rejected_agent.id

        archive_agent = await service.create(
            organization.id,
            CreateAgentArguments(name="Accepted Archive", instructions="Archive me."),
        )
        archive_session = await _create_selected_session(
            runtime,
            compiled,
            service,
            archive_agent.id,
            "agent-review-archive-success",
        )
        archive_proposed = await _stage_review(
            runtime,
            archive_session,
            archive_agent.id,
            operation_id="agents.archive_agent",
            request_id="archive-success-proposal",
        )
        archive_snapshot = await runtime.services.store.load(archive_session)
        archived = await runtime.services.runner.accept_review(
            archive_proposed.review.id,
            request_id="archive-accepted",
            expected_session_version=archive_snapshot.session_version,
            session_id=archive_session,
        )
        assert archived.disposition is OperationDisposition.COMPLETED
        assert archived.outcome == "archived"
        with pytest.raises(AgentNotFound):
            await service.get(organization.id, archive_agent.id)

        blocked_agent = await service.create(
            organization.id,
            CreateAgentArguments(name="Guard Recheck", instructions="Block deletion."),
        )
        blocked_session = await _create_selected_session(
            runtime,
            compiled,
            service,
            blocked_agent.id,
            "agent-review-delete-blocked",
        )
        delete_proposed = await _stage_review(
            runtime,
            blocked_session,
            blocked_agent.id,
            operation_id="agents.delete_agent",
            request_id="delete-blocked-proposal",
        )
        await service.attach_source(
            organization.id,
            blocked_agent.id,
            "source-ready-001",
        )
        blocked_snapshot = await runtime.services.store.load(blocked_session)
        blocked_accept = await runtime.services.runner.accept_review(
            delete_proposed.review.id,
            request_id="delete-blocked-accept",
            expected_session_version=blocked_snapshot.session_version,
            session_id=blocked_session,
        )
        assert blocked_accept.disposition is OperationDisposition.FAILED
        assert blocked_accept.failure is not None
        assert blocked_accept.failure.code == "review_stale"
        assert (await service.get(organization.id, blocked_agent.id)).id == blocked_agent.id
        assert len(
            (await service.inspect_dependencies(organization.id, blocked_agent.id)).source_attachments
        ) == 1

        deleted_agent = await service.create(
            organization.id,
            CreateAgentArguments(name="Accepted Delete", instructions="Delete me."),
        )
        delete_session = await _create_selected_session(
            runtime,
            compiled,
            service,
            deleted_agent.id,
            "agent-review-delete-success",
        )
        successful_delete = await _stage_review(
            runtime,
            delete_session,
            deleted_agent.id,
            operation_id="agents.delete_agent",
            request_id="delete-success-proposal",
        )
        delete_snapshot = await runtime.services.store.load(delete_session)
        deleted = await runtime.services.runner.accept_review(
            successful_delete.review.id,
            request_id="delete-success-accept",
            expected_session_version=delete_snapshot.session_version,
            session_id=delete_session,
        )
        assert deleted.disposition is OperationDisposition.COMPLETED
        assert deleted.outcome == "deleted"
        with pytest.raises(AgentNotFound):
            await service.get(organization.id, deleted_agent.id)
    finally:
        await runtime.close()
        await corpus.close()


async def _create_selected_session(
    runtime,
    compiled,
    service: AgentService,
    agent_id: uuid.UUID,
    session_id: str,
) -> str:
    initial = create_guest_session(compiled, session_id).model_copy(
        update={"current": Location(node_id="agents.home", entry_id=1)}
    )
    snapshot = await runtime.services.store.create(initial)
    selected = await runtime.services.runner.run(
        OperationRequest(
            session_id=session_id,
            request_id=f"select-{session_id}",
            expected_session_version=snapshot.session_version,
            operation_id="agents.select_agent",
            source=OperationSource.SURFACE,
            arguments=FrozenJsonObject({"agent_id": str(agent_id)}),
        )
    )
    assert selected.disposition is OperationDisposition.COMPLETED
    assert selected.outcome == "selected"
    return session_id


async def _stage_review(
    runtime,
    session_id: str,
    agent_id: uuid.UUID,
    *,
    operation_id: str,
    request_id: str,
):
    snapshot = await runtime.services.store.load(session_id)
    handle = f"agent-{agent_id.hex[:20]}"
    result = await runtime.services.runner.run(
        OperationRequest(
            session_id=session_id,
            request_id=request_id,
            expected_session_version=snapshot.session_version,
            operation_id=operation_id,
            source=OperationSource.SURFACE,
            arguments=FrozenJsonObject({"agent_ref": handle}),
        )
    )
    assert result.review is not None
    return result
