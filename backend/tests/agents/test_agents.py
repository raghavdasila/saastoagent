from __future__ import annotations

import asyncio
import uuid
from datetime import UTC, datetime
from pathlib import Path
from types import SimpleNamespace

import pytest
from pydantic import SecretStr
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import func, select

from corpus.auth.models import Organization
from corpus.features.agents.http import (
    AgentsHttpProblem,
    agents_problem_response,
    create_agents_router,
)
from corpus.features.agents.guards import DeleteDependenciesGuard
from corpus.features.agents.declarations import ARCHIVE_AGENT, DELETE_AGENT
from corpus.features.agents.domain import AgentLifecycle
from corpus.features.agents.models import Agent, AgentSourceAttachment, AgentVersion
from corpus.features.agents.operations import (
    AgentLifecycleHandler,
    AttachSourceHandler,
    CancelAgentCreationHandler,
    CreateAgentHandler,
    OpenAgentCreationHandler,
    OpenAgentAreaHandler,
    OpenExistingAgentForSourceHandler,
    OpenSourceCreationHandler,
    OpenAttachedSourceHandler,
    SaveAgentChangesHandler,
    SelectAgentHandler,
    _agent_surface_effects,
    _designer_surface_effects,
    _external_agent_surface_effects,
)
from corpus.features.agents.ports import (
    AgentNameConflict,
    AgentBuildLineageConflict,
    AgentDependencyConflict,
    AgentLifecycleConflict,
    AgentNotFound,
    AgentOwnerScopeUnavailable,
    AgentVersionConflict,
    AgentSourceAttachmentConflict,
    AgentSourceAttachmentUnavailable,
    AttachableSource,
)
from corpus.features.agents.repository import SqlAlchemyAgentRepository
from corpus.features.agents.schemas import (
    CreateAgentArguments,
    UpdateAgentArguments,
)
from corpus.features.agents.service import AgentService
from corpus.persistence import CorpusDatabase
from corpus.composition import compile_corpus_app
from routedeck_core.contracts.operations import (
    OperationRequest,
    OperationSource,
    ReviewPolicy,
    SafetyClass,
)
from routedeck_core.contracts.projection import FrozenJsonObject
from routedeck_core.contracts.session import PrivateSessionState
from routedeck_core.ports.executor import ResolvedEntityInput
from routedeck_core.state.session import create_session
from routedeck_core.supervision.guards import GuardInvocationContext


class OwnerScopeProbe:
    def __init__(self, organization_id: uuid.UUID) -> None:
        self.organization_id = organization_id

    async def organization_id_for_route(self, route_session_id: str) -> uuid.UUID:
        if route_session_id != "owner-route":
            raise AgentOwnerScopeUnavailable("Authentication is required.")
        return self.organization_id

    async def organization_id_for_access_token(self, access_token: str) -> uuid.UUID:
        if access_token != "owner-token":
            raise AgentOwnerScopeUnavailable("Authentication is required.")
        return self.organization_id


class SourceGatewayProbe:
    def __init__(self, owner_id: uuid.UUID) -> None:
        self.owner_id = owner_id
        self.current_revision = "revision-ready01"
        self.display_name = "Ready API"
        self.ready = True

    async def ready_inventory(
        self,
        organization_id: uuid.UUID,
    ) -> tuple[AttachableSource, ...]:
        if organization_id != self.owner_id or not self.ready:
            return ()
        return (
            AttachableSource(
                "source-ready-001",
                self.current_revision,
                self.display_name,
            ),
        )

    async def ready_current(self, organization_id: uuid.UUID, source_id: str) -> AttachableSource:
        if organization_id != self.owner_id or source_id != "source-ready-001":
            raise AgentSourceAttachmentUnavailable("The selected Source is unavailable in this Workspace.")
        if not self.ready:
            raise AgentSourceAttachmentUnavailable("Only a ready Source revision can be attached.")
        return AttachableSource(source_id, self.current_revision, self.display_name)

    async def exact_revision(
        self,
        organization_id: uuid.UUID,
        source_id: str,
        source_revision_id: str,
    ) -> AttachableSource:
        current = await self.ready_current(organization_id, source_id)
        if source_revision_id != self.current_revision:
            raise AgentSourceAttachmentUnavailable("The attached Source revision is no longer current.")
        return current

async def _database(path: Path) -> tuple[CorpusDatabase, uuid.UUID, uuid.UUID]:
    database = CorpusDatabase(f"sqlite+aiosqlite:///{path.as_posix()}")
    await database.create_schema_for_tests()
    first = Organization(
        name="First Workspace",
        slug=f"first-{uuid.uuid4().hex}",
        created_at=datetime.now(UTC),
    )
    second = Organization(
        name="Second Workspace",
        slug=f"second-{uuid.uuid4().hex}",
        created_at=datetime.now(UTC),
    )
    async with database.session() as session:
        async with session.begin():
            session.add_all((first, second))
            await session.flush()
    return database, first.id, second.id


def test_lifecycle_operations_are_destructive_reviewed_and_exact_entity_bound() -> None:
    for operation in (ARCHIVE_AGENT, DELETE_AGENT):
        assert operation.safety_class is SafetyClass.DESTRUCTIVE
        assert operation.review_policy is ReviewPolicy.REQUIRED
        assert operation.entity_inputs[0].argument_name == "agent_ref"
        assert operation.entity_inputs[0].entity_kind == "agent"
    assert ARCHIVE_AGENT.public_metadata_value() == {
        "review_surface_id": "agents.archive_review"
    }
    assert DELETE_AGENT.public_metadata_value() == {
        "review_surface_id": "agents.delete_review"
    }


@pytest.mark.asyncio
async def test_agent_service_persists_scoped_immutable_versions(tmp_path: Path) -> None:
    database, first_id, second_id = await _database(tmp_path / "agents.sqlite3")
    service = AgentService(SqlAlchemyAgentRepository(database))
    try:
        created = await service.create(
            first_id,
            CreateAgentArguments(
                name="  Research   Agent ",
                description=" First configuration ",
                instructions=" Research carefully. ",
            ),
        )
        assert created.name == "Research Agent"
        assert created.description == "First configuration"
        assert created.instructions == "Research carefully."
        assert created.current_version == 1
        listed = (await service.list(first_id)).agents
        assert len(listed) == 1
        assert listed[0].id == created.id
        assert listed[0].current_version == 1
        assert (await service.list(second_id)).agents == ()
        with pytest.raises(AgentNotFound):
            await service.get(second_id, created.id)

        updated = await service.update(
            first_id,
            UpdateAgentArguments(
                agent_id=created.id,
                expected_version=1,
                name="Research Agent",
                description="Second configuration",
                instructions="Research, cite, and report.",
            ),
        )
        assert updated.current_version == 2
        assert updated.instructions == "Research, cite, and report."
        async with database.session() as session:
            version_count = await session.scalar(
                select(func.count())
                .select_from(AgentVersion)
                .where(AgentVersion.agent_id == created.id)
            )
        assert version_count == 2

        with pytest.raises(AgentVersionConflict):
            await service.update(
                first_id,
                UpdateAgentArguments(
                    agent_id=created.id,
                    expected_version=1,
                    name="Research Agent",
                    description="Stale edit",
                    instructions="This must not replace version 2.",
                ),
            )
        with pytest.raises(AgentNameConflict):
            await service.create(
                first_id,
                CreateAgentArguments(
                    name="research agent",
                    instructions="Duplicate names are not allowed.",
                ),
            )
    finally:
        await database.close()


@pytest.mark.asyncio
async def test_agent_source_attachment_is_owner_scoped_pinned_and_never_overwritten(
    tmp_path: Path,
) -> None:
    database, first_id, second_id = await _database(tmp_path / "attachments.sqlite3")
    sources = SourceGatewayProbe(first_id)
    service = AgentService(SqlAlchemyAgentRepository(database), sources)
    try:
        agent = await service.create(
            first_id,
            CreateAgentArguments(name="Attached Agent", instructions="Use the pinned Source."),
        )
        attachment = await service.attach_source(first_id, agent.id, "source-ready-001")
        assert attachment.source_revision_id == "revision-ready01"
        listed = (await service.list_source_attachments(first_id, agent.id)).attachments
        assert len(listed) == 1
        assert listed[0].source_id == attachment.source_id
        assert listed[0].source_revision_id == attachment.source_revision_id
        sources.display_name = "Renamed Ready API"
        renamed = (await service.list_source_attachments(first_id, agent.id)).attachments
        assert renamed[0].display_name == "Renamed Ready API"

        sources.ready = False
        with pytest.raises(AgentSourceAttachmentUnavailable):
            await service.list_source_attachments(first_id, agent.id)
        sources.ready = True

        with pytest.raises(AgentNotFound):
            await service.list_source_attachments(second_id, agent.id)
        with pytest.raises(AgentSourceAttachmentUnavailable):
            await service.attach_source(second_id, agent.id, "source-ready-001")

        repeated = await service.attach_source(first_id, agent.id, "source-ready-001")
        assert repeated.attached_at.replace(tzinfo=UTC) == attachment.attached_at
        assert repeated.source_revision_id == "revision-ready01"
        assert len((await service.list_source_attachments(first_id, agent.id)).attachments) == 1

        sources.current_revision = "revision-ready02"
        refreshable = await service.one_attachable_ready_source(first_id, agent.id)
        assert refreshable.source_id == "source-ready-001"
        assert refreshable.source_revision_id == "revision-ready02"
        refreshed = await service.attach_source(first_id, agent.id, "source-ready-001")
        assert refreshed.attached_at.replace(tzinfo=UTC) > attachment.attached_at
        assert refreshed.source_revision_id == "revision-ready02"
        opened = await service.open_attached_source(first_id, agent.id, "source-ready-001")
        assert opened.source_revision_id == "revision-ready02"
        assert len((await service.list_source_attachments(first_id, agent.id)).attachments) == 1

        async with database.session() as session:
            persisted = await session.scalar(
                select(AgentSourceAttachment).where(AgentSourceAttachment.agent_id == agent.id)
            )
        assert persisted is not None
        assert persisted.source_revision_id == "revision-ready02"
        assert not hasattr(persisted, "source_display_name")
    finally:
        await database.close()


@pytest.mark.asyncio
async def test_detaching_current_source_preserves_immutable_build_lineage(
    tmp_path: Path,
) -> None:
    database, first_id, second_id = await _database(tmp_path / "detach-source.sqlite3")
    sources = SourceGatewayProbe(first_id)
    service = AgentService(SqlAlchemyAgentRepository(database), sources)
    build_id = uuid.uuid4()
    try:
        agent = await service.create(
            first_id,
            CreateAgentArguments(name="Detach Agent", instructions="Preserve historical inputs."),
        )
        attachment = await service.attach_source(first_id, agent.id, "source-ready-001")
        await service.record_build_lineage(
            first_id,
            agent.id,
            build_id=build_id,
            expected_agent_version=1,
            source_references=((attachment.source_id, attachment.source_revision_id),),
        )

        with pytest.raises(AgentNotFound):
            await service.detach_source(second_id, agent.id, attachment.source_id)

        await service.detach_source(first_id, agent.id, attachment.source_id)
        assert (await service.list_source_attachments(first_id, agent.id)).attachments == ()
        dependencies = await service.inspect_dependencies(first_id, agent.id)
        assert dependencies.source_attachments == ()
        assert dependencies.build_ids == (build_id,)
        assert dependencies.blocks_delete is True
        lineage = (await service.list_build_lineages(first_id, agent.id)).builds
        assert lineage[0].source_references[0].source_id == attachment.source_id
        assert lineage[0].source_references[0].source_revision_id == attachment.source_revision_id

        with pytest.raises(AgentSourceAttachmentUnavailable):
            await service.detach_source(first_id, agent.id, attachment.source_id)
    finally:
        await database.close()


@pytest.mark.asyncio
async def test_agent_build_lineage_is_owner_scoped_immutable_and_never_retargets(
    tmp_path: Path,
) -> None:
    database, first_id, second_id = await _database(tmp_path / "build-lineage.sqlite3")
    sources = SourceGatewayProbe(first_id)
    service = AgentService(SqlAlchemyAgentRepository(database), sources)
    build_id = uuid.uuid4()
    try:
        agent = await service.create(
            first_id,
            CreateAgentArguments(name="Built Agent", instructions="Use the exact build inputs."),
        )
        attachment = await service.attach_source(first_id, agent.id, "source-ready-001")
        recorded = await service.record_build_lineage(
            first_id,
            agent.id,
            build_id=build_id,
            expected_agent_version=1,
            source_references=((attachment.source_id, attachment.source_revision_id),),
        )
        assert recorded.build_id == build_id
        assert recorded.agent_version == 1
        assert recorded.source_references[0].source_revision_id == "revision-ready01"
        assert recorded.source_references[0].available is True

        with pytest.raises(AgentBuildLineageConflict):
            await service.record_build_lineage(
                first_id,
                agent.id,
                build_id=build_id,
                expected_agent_version=1,
                source_references=((attachment.source_id, attachment.source_revision_id),),
            )
        with pytest.raises(AgentNotFound):
            await service.list_build_lineages(second_id, agent.id)

        sources.current_revision = "revision-ready02"
        reloaded = AgentService(SqlAlchemyAgentRepository(database), sources)
        history = (await reloaded.list_build_lineages(first_id, agent.id)).builds
        assert len(history) == 1
        assert history[0].build_id == build_id
        assert history[0].source_references[0].source_revision_id == "revision-ready01"
        assert history[0].source_references[0].available is False
        dependencies = await reloaded.inspect_dependencies(first_id, agent.id)
        assert dependencies.build_ids == (build_id,)
        assert dependencies.blocks_delete is True
    finally:
        await database.close()


@pytest.mark.asyncio
async def test_agent_operation_handlers_report_action_result_and_state_errors(
    tmp_path: Path,
) -> None:
    database, organization_id, _ = await _database(tmp_path / "operations.sqlite3")
    service = AgentService(
        SqlAlchemyAgentRepository(database),
        SourceGatewayProbe(organization_id),
    )
    scope = OwnerScopeProbe(organization_id)
    context = SimpleNamespace(
        session_id="owner-route",
        attempt_id="attempt-1",
        request_id="request-1",
    )
    try:
        create = await CreateAgentHandler(service, scope)(
            {
                "name": "Support Agent",
                "description": "Handles support",
                "instructions": "Resolve the owner's support work.",
            },
            context,
        )
        assert create.outcome == "created"
        assert create.failure is None
        persisted = (await service.list(organization_id)).agents[0]
        created_binding = create.effects.replace_entities[0].bindings[0]
        assert created_binding.public.entity_kind == "agent"
        assert created_binding.private_id.get_secret_value() == str(persisted.id)
        assert "agents.open_designer" in created_binding.allowed_operation_ids
        assert "agents.open_channels" in created_binding.allowed_operation_ids
        assert create.effects.surface_updates[0].surface_id == "agents.home"

        opened_inventory = await OpenExistingAgentForSourceHandler(service, scope)(
            {
                "source_id": "source-ready-001",
                "source_revision_id": "revision-ready01",
            },
            context,
        )
        assert opened_inventory.outcome == "opened"
        assert (await service.list_source_attachments(organization_id, persisted.id)).attachments == ()
        pending_values = {
            item.name: item.value.to_python()
            for item in opened_inventory.effects.surface_updates[0].values
        }
        assert pending_values == {
            "pending_source_id": "source-ready-001",
            "pending_source_revision_id": "revision-ready01",
            "pending_source_display_name": "Ready API",
        }
        provider_values = FrozenJsonObject({
            "agents.pending_source": {
                "source_id": "source-ready-001",
                "source_revision_id": "revision-ready01",
                "display_name": "Ready API",
            }
        })
        opened_new_agent = await OpenAgentCreationHandler(service, scope)(
            {
                "source_id": "source-ready-001",
                "source_revision_id": "revision-ready01",
            },
            context,
        )
        assert opened_new_agent.outcome == "opened"
        assert [
            update.surface_id for update in opened_new_agent.effects.surface_updates
        ] == ["agents.create"]
        assert {
            item.name: item.value.to_python()
            for item in opened_new_agent.effects.surface_updates[0].values
        } == pending_values

        cancelled_new_agent = await CancelAgentCreationHandler()(
            {},
            SimpleNamespace(provider_values=provider_values),
        )
        assert cancelled_new_agent.outcome == "opened"
        assert [
            update.surface_id for update in cancelled_new_agent.effects.surface_updates
        ] == ["agents.home"]
        assert {
            item.name: item.value.to_python()
            for item in cancelled_new_agent.effects.surface_updates[0].values
        } == pending_values

        selected_agent = await SelectAgentHandler(service, scope)(
            {"agent_id": str(persisted.id)},
            SimpleNamespace(
                session_id="owner-route",
                provider_values=provider_values,
            ),
        )
        assert selected_agent.outcome == "selected"
        assert {
            item.name: item.value.to_python()
            for item in selected_agent.effects.surface_updates[0].values
        } == {
            "selected_agent_ref": created_binding.public.handle,
            **pending_values,
        }

        opened_channels = await OpenAgentAreaHandler(
            service,
            scope,
            "agents.open_channels",
            "channels",
        )(
            {"agent_ref": created_binding.public.handle},
            SimpleNamespace(
                session_id="owner-route",
                attempt_id="open-channels-attempt",
                request_id="open-channels-request",
                private_entity_id=lambda argument_name: str(persisted.id),
            ),
        )
        assert opened_channels.outcome == "opened"
        channels_binding = opened_channels.effects.replace_entities[0].bindings[0]
        assert "agents.open_evaluation" in channels_binding.allowed_operation_ids
        assert opened_channels.effects.surface_updates[0].surface_id == "channels.home"

        opened_evaluation = await OpenAgentAreaHandler(
            service,
            scope,
            "agents.open_evaluation",
            "evaluation",
        )(
            {"agent_ref": created_binding.public.handle},
            SimpleNamespace(
                session_id="owner-route",
                attempt_id="open-evaluation-attempt",
                request_id="open-evaluation-request",
                private_entity_id=lambda argument_name: str(persisted.id),
            ),
        )
        assert opened_evaluation.outcome == "opened"
        evaluation_binding = opened_evaluation.effects.replace_entities[0].bindings[0]
        assert set(evaluation_binding.allowed_operation_ids) == {
            "evaluation.create_case",
            "evaluation.generate_set",
            "evaluation.retry_generation",
            "evaluation.edit_case",
            "evaluation.delete_case",
            "evaluation.run_case",
            "agents.open_builds",
            "agents.open_channels",
            "agents.return_to_hub",
        }
        assert opened_evaluation.effects.surface_updates[0].surface_id == "evaluation.home"

        opened_creation = await OpenSourceCreationHandler(service, scope)(
            {"agent_ref": created_binding.public.handle},
            SimpleNamespace(
                session_id="owner-route",
                private_entity_id=lambda argument_name: str(persisted.id),
            ),
        )
        assert opened_creation.outcome == "opened"
        assert opened_creation.effects.surface_updates[0].surface_id == "sources.api_intake"
        assert {
            item.name: item.value.to_python()
            for item in opened_creation.effects.surface_updates[0].values
        } == {
            "return_agent_ref": created_binding.public.handle,
            "agent_handoff_mode": "create",
            "mode": "create",
        }

        attached_source = await AttachSourceHandler(
            service,
            scope,
            "agents.attach_source",
        )(
            {"agent_ref": created_binding.public.handle},
            SimpleNamespace(
                session_id="owner-route",
                attempt_id="attach-source-attempt",
                request_id="attach-source-request",
                provider_values=provider_values,
                private_entity_id=lambda argument_name: str(persisted.id),
            ),
        )
        assert attached_source.outcome == "attached"
        attached = (await service.list_source_attachments(organization_id, persisted.id)).attachments
        assert [(item.source_id, item.source_revision_id) for item in attached] == [
            ("source-ready-001", "revision-ready01")
        ]
        opened_source = await OpenAttachedSourceHandler(service, scope)(
            {"agent_ref": created_binding.public.handle},
            SimpleNamespace(
                session_id="owner-route",
                attempt_id="open-source-attempt",
                request_id="open-source-request",
                private_entity_id=lambda argument_name: str(persisted.id),
            ),
        )
        assert opened_source.outcome == "opened"
        source_updates = {
            update.surface_id: {
                item.name: item.value.to_python()
                for item in update.values
            }
            for update in opened_source.effects.surface_updates
        }
        assert set(source_updates) == {"sources.api"}
        assert source_updates["sources.api"] == {
            "return_agent_ref": created_binding.public.handle,
            "agent_handoff_mode": "inspect",
            "selected_source_id": "source-ready-001",
            "selected_source_revision_id": "revision-ready01",
            "form_handle": "sources-api-connection",
            "mode": "inspect",
            "return_context": "agent",
            "initial_workspace": "graph",
        }
        source_binding = opened_source.effects.replace_entities[0].bindings[0]
        assert "agents.return_from_source" in source_binding.allowed_operation_ids
        assert set(source_binding.allowed_operation_ids) == {"agents.return_from_source"}

        saved = await SaveAgentChangesHandler(service, scope)(
            {
                "agent_id": str(persisted.id),
                "expected_version": 1,
                "name": "Support Agent",
                "description": "Handles support",
                "instructions": "Resolve and document support work.",
            },
            context,
        )
        assert saved.outcome == "saved"
        assert (await service.get(organization_id, persisted.id)).current_version == 2

        stale = await SaveAgentChangesHandler(service, scope)(
            {
                "agent_id": str(persisted.id),
                "expected_version": 1,
                "name": "Support Agent",
                "description": "Stale",
                "instructions": "This stale action must fail.",
            },
            context,
        )
        assert stale.failure is not None
        assert stale.failure.code == "agent_version_conflict"
        assert stale.outcome is None
    finally:
        await database.close()


@pytest.mark.asyncio
async def test_archive_preserves_record_versions_and_attachments_but_leaves_active_inventory(
    tmp_path: Path,
) -> None:
    database, organization_id, other_id = await _database(tmp_path / "archive.sqlite3")
    sources = SourceGatewayProbe(organization_id)
    service = AgentService(SqlAlchemyAgentRepository(database), sources)
    try:
        agent = await service.create(
            organization_id,
            CreateAgentArguments(name="Archive Agent", instructions="Preserve history."),
        )
        await service.attach_source(organization_id, agent.id, "source-ready-001")

        archived = await service.archive(organization_id, agent.id)

        assert archived.lifecycle is AgentLifecycle.ARCHIVED
        assert (await service.list(organization_id)).agents == ()
        with pytest.raises(AgentNotFound):
            await service.get(organization_id, agent.id)
        with pytest.raises(AgentLifecycleConflict):
            await service.archive(organization_id, agent.id)
        stale_handler = await AgentLifecycleHandler(
            service,
            OwnerScopeProbe(organization_id),
            ARCHIVE_AGENT.id,
        )(
            {"agent_ref": f"agent-{agent.id.hex[:20]}"},
            SimpleNamespace(
                session_id="owner-route",
                attempt_id="archive-attempt",
                request_id="archive-request",
                private_entity_id=lambda argument_name: str(agent.id),
            ),
        )
        assert stale_handler.outcome is None
        assert stale_handler.failure is not None
        assert stale_handler.failure.code == "agent_lifecycle_conflict"
        with pytest.raises(AgentNotFound):
            await service.archive(other_id, agent.id)
        async with database.session() as session:
            persisted = await session.get(Agent, agent.id)
            version_count = await session.scalar(
                select(func.count(AgentVersion.id)).where(AgentVersion.agent_id == agent.id)
            )
            attachment_count = await session.scalar(
                select(func.count(AgentSourceAttachment.id)).where(
                    AgentSourceAttachment.agent_id == agent.id
                )
            )
        assert persisted is not None
        assert persisted.lifecycle is AgentLifecycle.ARCHIVED
        assert version_count == 1
        assert attachment_count == 1
    finally:
        await database.close()


@pytest.mark.asyncio
async def test_delete_rechecks_dependencies_and_never_cascades_or_detaches(
    tmp_path: Path,
) -> None:
    database, organization_id, _ = await _database(tmp_path / "delete.sqlite3")
    sources = SourceGatewayProbe(organization_id)
    service = AgentService(SqlAlchemyAgentRepository(database), sources)
    try:
        blocked = await service.create(
            organization_id,
            CreateAgentArguments(name="Blocked Agent", instructions="Stay intact."),
        )
        await service.attach_source(organization_id, blocked.id, "source-ready-001")
        dependencies = await service.inspect_dependencies(organization_id, blocked.id)
        assert dependencies.blocks_delete is True
        assert [item.source_id for item in dependencies.source_attachments] == [
            "source-ready-001"
        ]
        session = create_session(
            app=compile_corpus_app(),
            session_id="owner-route",
            private_state=PrivateSessionState(),
        )
        guard_decision = await DeleteDependenciesGuard(
            service,
            OwnerScopeProbe(organization_id),
        )(
            GuardInvocationContext(
                session=session,
                request=OperationRequest(
                    session_id=session.session_id,
                    request_id="delete-guard-request",
                    expected_session_version=session.session_version,
                    operation_id="agents.delete_agent",
                    source=OperationSource.SURFACE,
                    arguments=FrozenJsonObject(
                        {"agent_ref": f"agent-{blocked.id.hex[:20]}"}
                    ),
                ),
                attempt_id="delete-guard-attempt",
                resolved_entities=(
                    ResolvedEntityInput(
                        argument_name="agent_ref",
                        entity_kind="agent",
                        private_id=SecretStr(str(blocked.id)),
                    ),
                ),
            )
        )
        assert guard_decision.allowed is False
        assert guard_decision.failure is not None
        assert guard_decision.failure.code == "agent_dependency_conflict"

        with pytest.raises(AgentDependencyConflict, match="1 Source attachment"):
            await service.delete(organization_id, blocked.id)
        assert (await service.get(organization_id, blocked.id)).id == blocked.id
        assert len((await service.list_source_attachments(organization_id, blocked.id)).attachments) == 1

        removable = await service.create(
            organization_id,
            CreateAgentArguments(name="Removable Agent", instructions="May be deleted."),
        )
        await service.delete(organization_id, removable.id)
        with pytest.raises(AgentNotFound):
            await service.get(organization_id, removable.id)
        async with database.session() as session:
            assert await session.get(Agent, removable.id) is None
            assert await session.scalar(
                select(func.count(AgentVersion.id)).where(AgentVersion.agent_id == removable.id)
            ) == 0
    finally:
        await database.close()


def test_selected_agent_binding_keeps_every_horizontal_destination_available() -> None:
    expected_navigation = {
        "agents.open_operations",
        "agents.open_designer",
        "agents.open_builds",
        "agents.open_sandbox",
        "agents.open_evaluation",
        "agents.open_channels",
    }
    hub = _agent_surface_effects(
        "agent-horizontal",
        "00000000-0000-0000-0000-000000000001",
    )
    designer = _designer_surface_effects(
        "agent-horizontal",
        "00000000-0000-0000-0000-000000000001",
    )
    builder = _external_agent_surface_effects(
        "agent-horizontal",
        "00000000-0000-0000-0000-000000000001",
        surface_id="builder.home",
        operation_ids=("builder.assemble",),
    )
    assert expected_navigation <= set(hub.replace_entities[0].bindings[0].allowed_operation_ids)
    assert "agents.return_to_hub" not in designer.replace_entities[0].bindings[0].allowed_operation_ids
    assert set(builder.replace_entities[0].bindings[0].allowed_operation_ids) == {
        "builder.assemble",
        "agents.return_to_hub",
    }


def test_agents_http_reads_are_authenticated_and_workspace_scoped(tmp_path: Path) -> None:
    database, organization_id, other_id = asyncio.run(
        _database(tmp_path / "http-agents.sqlite3")
    )
    service = AgentService(SqlAlchemyAgentRepository(database))
    owned = asyncio.run(
        service.create(
            organization_id,
            CreateAgentArguments(name="Owned Agent", instructions="Owned."),
        )
    )
    asyncio.run(
        service.create(
            other_id,
            CreateAgentArguments(name="Other Agent", instructions="Other."),
        )
    )
    app = FastAPI()
    app.add_exception_handler(AgentsHttpProblem, agents_problem_response)
    app.include_router(create_agents_router(service, OwnerScopeProbe(organization_id)))
    try:
        with TestClient(app) as client:
            assert client.get("/api/agents").status_code == 401
            rejected = client.get(
                "/api/agents",
                headers={"Authorization": "Bearer wrong-token"},
            )
            assert rejected.status_code == 401
            listed = client.get(
                "/api/agents",
                headers={"Authorization": "Bearer owner-token"},
            )
            assert listed.status_code == 200
            assert [item["name"] for item in listed.json()["agents"]] == [
                "Owned Agent"
            ]
            inspected = client.get(
                f"/api/agents/{owned.id}",
                headers={"Authorization": "Bearer owner-token"},
            )
            assert inspected.status_code == 200
            assert inspected.json()["current_version"] == 1
            assert inspected.headers["cache-control"] == "private, no-store"
            dependencies = client.get(
                f"/api/agents/{owned.id}/dependencies",
                headers={"Authorization": "Bearer owner-token"},
            )
            assert dependencies.status_code == 200
            assert dependencies.json() == {
                "agent_id": str(owned.id),
                "source_attachments": [],
                "build_ids": [],
                "blocks_delete": False,
            }
            foreign_dependencies = client.get(
                f"/api/agents/{uuid.uuid4()}/dependencies",
                headers={"Authorization": "Bearer owner-token"},
            )
            assert foreign_dependencies.status_code == 404
    finally:
        asyncio.run(database.close())
