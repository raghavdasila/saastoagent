from __future__ import annotations

import uuid
from datetime import UTC, datetime
from pathlib import Path

import pytest

from corpus.auth.models import Organization
from corpus.features.agents.repository import SqlAlchemyAgentRepository
from corpus.features.agents.schemas import CreateAgentArguments
from corpus.features.agents.service import AgentService
from corpus.features.builder.repository import SqlAlchemyBuilderRepository
from corpus.features.designer.domain import DesignerInputSnapshot, DesignerSemanticGroup, DesignerSourceInput
from corpus.features.designer.repository import SqlAlchemyDesignerRepository
from corpus.features.designer.service import DesignerService
from corpus.persistence import CorpusDatabase


@pytest.mark.asyncio
async def test_explicit_retry_appends_attempt_and_preserves_failed_history(
    tmp_path: Path,
) -> None:
    database = CorpusDatabase(
        f"sqlite+aiosqlite:///{(tmp_path / 'builder-retry.sqlite3').as_posix()}"
    )
    await database.create_schema_for_tests()
    owner_id = uuid.uuid4()
    async with database.session() as session:
        async with session.begin():
            session.add(Organization(
                id=owner_id,
                name="Owner",
                slug=f"owner-{uuid.uuid4().hex}",
                created_at=datetime.now(UTC),
            ))
    agents = AgentService(SqlAlchemyAgentRepository(database))
    agent = await agents.create(owner_id, CreateAgentArguments(
        name="Retry Agent",
        description="Retain exact build attempts",
        instructions="Use only accepted Source inputs.",
    ))

    class Inputs:
        async def snapshot(self, organization_id, agent_id):
            assert organization_id == owner_id
            assert agent_id == agent.id
            return DesignerInputSnapshot(
                agent_id=agent.id,
                agent_version=1,
                agent_name=agent.name,
                description=agent.description,
                instructions=agent.instructions,
                sources=(DesignerSourceInput(
                    source_id="source-retry-001",
                    source_revision_id="revision-retry01",
                    display_name="Retry API",
                    curation_id="curation-retry1",
                    inventory_fingerprint="a" * 64,
                    included_operation_ids=("GetProductTypes",),
                    semantic_groups=(DesignerSemanticGroup(
                        label="taxonomy",
                        operation_ids=("GetProductTypes",),
                    ),),
                ),),
            )

    designer = DesignerService(SqlAlchemyDesignerRepository(database), Inputs())
    try:
        proposed = await designer.propose(owner_id, agent.id)
        accepted = await designer.accept(
            owner_id, agent.id, expected_revision_id=proposed.current_revision_id
        )
        requested = await designer.request_build(
            owner_id, agent.id, accepted_revision_id=accepted.accepted_revision_id
        )
        assert requested.build_request is not None

        repository = SqlAlchemyBuilderRepository(database)
        first = await repository.begin(
            owner_id, agent.id, build_request_id=requested.build_request.id
        )
        failed = await repository.fail(
            owner_id,
            first.id,
            code="builderunavailable",
            message="Connection setup is missing.",
        )
        second = await repository.begin(
            owner_id, agent.id, build_request_id=requested.build_request.id
        )

        assert failed.attempt_number == 1
        assert failed.status == "failed"
        assert second.attempt_number == 2
        assert second.status == "assembling"
        assert second.id != failed.id
        history = await repository.get_for_agent(owner_id, agent.id)
        assert [(item.attempt_number, item.status) for item in history] == [
            (2, "assembling"),
            (1, "failed"),
        ]
    finally:
        await database.close()
