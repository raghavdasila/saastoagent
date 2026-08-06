from __future__ import annotations

import asyncio
import uuid
from datetime import UTC, datetime
from pathlib import Path
from types import SimpleNamespace

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import func, select

from corpus.auth.models import Organization
from corpus.features.agents.http import (
    AgentsHttpProblem,
    agents_problem_response,
    create_agents_router,
)
from corpus.features.agents.models import AgentVersion
from corpus.features.agents.operations import (
    CreateAgentHandler,
    SaveAgentChangesHandler,
)
from corpus.features.agents.ports import (
    AgentNameConflict,
    AgentNotFound,
    AgentOwnerScopeUnavailable,
    AgentVersionConflict,
)
from corpus.features.agents.repository import SqlAlchemyAgentRepository
from corpus.features.agents.schemas import (
    CreateAgentArguments,
    UpdateAgentArguments,
)
from corpus.features.agents.service import AgentService
from corpus.persistence import CorpusDatabase


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
async def test_agent_operation_handlers_report_action_result_and_state_errors(
    tmp_path: Path,
) -> None:
    database, organization_id, _ = await _database(tmp_path / "operations.sqlite3")
    service = AgentService(SqlAlchemyAgentRepository(database))
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
    finally:
        asyncio.run(database.close())
