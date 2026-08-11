from __future__ import annotations

import uuid
from dataclasses import replace
from datetime import UTC, datetime
from pathlib import Path
from types import SimpleNamespace

import pytest
from routedeck_core.contracts.operations import (
    OperationRequest,
    OperationSource,
    ReviewPolicy,
    SafetyClass,
)

from corpus.auth.models import Organization
from corpus.features.agents.repository import SqlAlchemyAgentRepository
from corpus.features.agents.schemas import CreateAgentArguments
from corpus.features.agents.service import AgentService
from corpus.features.designer.declarations import APPROVE_DESIGN, PROPOSE_DESIGN, REQUEST_BUILD
from corpus.features.designer.domain import (
    DesignerInputSnapshot,
    DesignerSemanticGroup,
    DesignerSourceInput,
)
from corpus.features.designer.ports import DesignerConflict, DesignerUnavailable
from corpus.features.designer.providers import CurrentDesignProvider
from corpus.features.designer.repository import SqlAlchemyDesignerRepository
from corpus.features.designer.schemas import DesignContent
from corpus.features.designer.service import DesignerService
from corpus.features.designer.topology import DesignerTopologyError, compile_design_topology
from corpus.composition import compile_corpus_app
from corpus.persistence import CorpusDatabase


class InputProbe:
    def __init__(self, snapshot: DesignerInputSnapshot) -> None:
        self.value = snapshot

    async def snapshot(self, organization_id, agent_id):
        if organization_id != OWNER_ID or agent_id != self.value.agent_id:
            raise DesignerUnavailable("The selected Agent inputs are unavailable.")
        return self.value


OWNER_ID = uuid.uuid4()


@pytest.mark.asyncio
async def test_designer_appends_exact_revisions_accepts_and_requests_one_build(tmp_path: Path) -> None:
    database = CorpusDatabase(f"sqlite+aiosqlite:///{(tmp_path / 'designer.sqlite3').as_posix()}")
    await database.create_schema_for_tests()
    other_id = uuid.uuid4()
    async with database.session() as session:
        async with session.begin():
            session.add_all([
                Organization(id=OWNER_ID, name="Owner", slug=f"owner-{uuid.uuid4().hex}", created_at=datetime.now(UTC)),
                Organization(id=other_id, name="Other", slug=f"other-{uuid.uuid4().hex}", created_at=datetime.now(UTC)),
            ])
    agents = AgentService(SqlAlchemyAgentRepository(database))
    agent = await agents.create(OWNER_ID, CreateAgentArguments(name="Designer Agent", description="Serve store operators", instructions="Use curated tools only."))
    inputs = InputProbe(DesignerInputSnapshot(
        agent_id=agent.id,
        agent_version=1,
        agent_name=agent.name,
        description=agent.description,
        instructions=agent.instructions,
        sources=(DesignerSourceInput(
            source_id="source-ready-001",
            source_revision_id="revision-ready01",
            display_name="Store API",
            curation_id="curation-ready1",
            inventory_fingerprint="a" * 64,
            included_operation_ids=("GetProductTypes", "GetProductTags"),
            semantic_groups=(
                DesignerSemanticGroup(
                    label="Product taxonomy",
                    operation_ids=("GetProductTypes", "GetProductTags"),
                ),
            ),
        ),),
    ))
    service = DesignerService(SqlAlchemyDesignerRepository(database), inputs)
    try:
        proposed = await service.propose(OWNER_ID, agent.id)
        assert len(proposed.revisions) == 1
        first = proposed.revisions[0]
        assert first.agent_version == 1
        assert first.content.tools == ("GetProductTags", "GetProductTypes")
        assert first.content.features == ("Product taxonomy API feature",)
        assert first.content.capabilities == (
            "Product taxonomy: GetProductTypes, GetProductTags",
        )
        assert first.topology.entry_node_id == "agent_runtime.home"
        assert first.topology.nodes[0].capability_ids == (
            first.topology.capabilities[0].id,
        )
        assert first.topology.capabilities[0].title == "Product taxonomy"
        assert first.topology.capabilities[0].operation_ids == (
            "GetProductTypes",
            "GetProductTags",
        )
        assert len(first.topology.topology_hash) == 64
        assert first.source_inputs[0]["source_revision_id"] == "revision-ready01"
        assert first.source_inputs[0]["semantic_groups"] == [
            {
                "label": "Product taxonomy",
                "operation_ids": ["GetProductTypes", "GetProductTags"],
            }
        ]
        assert proposed.accepted_revision_id is None
        assert proposed.current_inputs_ready is True
        assert proposed.current_inputs_match is True

        invalid = first.content.model_copy(update={
            "capabilities": (
                "Product types: GetProductTypes",
                "Duplicate types: GetProductTypes",
            )
        })
        with pytest.raises(DesignerTopologyError):
            await service.customize(
                OWNER_ID,
                agent.id,
                expected_revision_id=first.id,
                content=invalid,
            )
        assert len((await service.get(OWNER_ID, agent.id)).revisions) == 1

        custom = first.content.model_copy(update={"behaviors": ("Answer store taxonomy questions.",)})
        customized = await service.customize(
            OWNER_ID,
            agent.id,
            expected_revision_id=first.id,
            content=custom,
        )
        assert len(customized.revisions) == 2
        second = customized.revisions[-1]
        assert second.id != first.id
        assert customized.revisions[0].content == first.content
        with pytest.raises(DesignerConflict):
            await service.customize(OWNER_ID, agent.id, expected_revision_id=first.id, content=custom)

        accepted = await service.accept(OWNER_ID, agent.id, expected_revision_id=second.id)
        assert accepted.accepted_revision_id == second.id
        requested = await service.request_build(OWNER_ID, agent.id, accepted_revision_id=second.id)
        assert requested.build_request is not None
        assert requested.build_request.design_revision_id == second.id
        assert requested.build_request.status == "pending"

        inputs.value = replace(
            inputs.value,
            sources=(
                replace(inputs.value.sources[0], source_revision_id="revision-ready02"),
            ),
        )
        drifted = await service.get(OWNER_ID, agent.id)
        assert drifted.current_inputs_ready is True
        assert drifted.current_inputs_match is False
        reproposed = await service.propose(OWNER_ID, agent.id)
        assert reproposed.revisions[-1].source_inputs[0]["source_revision_id"] == "revision-ready02"
        assert reproposed.current_inputs_match is True
        assert reproposed.accepted_revision_id == second.id
        with pytest.raises(DesignerConflict):
            await service.request_build(OWNER_ID, agent.id, accepted_revision_id=second.id)

        reloaded = DesignerService(SqlAlchemyDesignerRepository(database), inputs)
        durable = await reloaded.get(OWNER_ID, agent.id)
        assert durable.current_revision_id == reproposed.current_revision_id
        assert durable.accepted_revision_id == second.id
        assert len(durable.revisions) == 3
        with pytest.raises(DesignerUnavailable):
            await reloaded.get(other_id, agent.id)
    finally:
        await database.close()


def test_designer_topology_fails_closed_when_capabilities_do_not_partition_tools() -> None:
    content = DesignContent(
        goal="Answer catalog questions",
        instructions="Use exact catalog evidence.",
        features=("Catalog",),
        behaviors=("Answer one catalog request.",),
        policies=("Never invent a product.",),
        capabilities=("Catalog lookup: GetProductTypes",),
        tools=("GetProductTypes", "GetProductTags"),
    )

    with pytest.raises(DesignerTopologyError, match="exactly one capability"):
        compile_design_topology(content)


@pytest.mark.asyncio
async def test_designer_proposal_partitions_overlapping_semantic_groups(tmp_path: Path) -> None:
    database = CorpusDatabase(
        f"sqlite+aiosqlite:///{(tmp_path / 'overlapping-groups.sqlite3').as_posix()}"
    )
    await database.create_schema_for_tests()
    async with database.session() as session:
        async with session.begin():
            session.add(Organization(
                id=OWNER_ID,
                name="Owner",
                slug=f"owner-{uuid.uuid4().hex}",
                created_at=datetime.now(UTC),
            ))
    agents = AgentService(SqlAlchemyAgentRepository(database))
    agent = await agents.create(
        OWNER_ID,
        CreateAgentArguments(
            name="Overlapping graph Agent",
            description="Serve taxonomy questions",
            instructions="Use curated tools only.",
        ),
    )
    inputs = InputProbe(DesignerInputSnapshot(
        agent_id=agent.id,
        agent_version=1,
        agent_name=agent.name,
        description=agent.description,
        instructions=agent.instructions,
        sources=(DesignerSourceInput(
            source_id="source-ready-001",
            source_revision_id="revision-ready01",
            display_name="Store API",
            curation_id="curation-ready1",
            inventory_fingerprint="b" * 64,
            included_operation_ids=("GetProductTags", "GetProductTypes"),
            semantic_groups=(
                DesignerSemanticGroup(label="product_tags", operation_ids=("GetProductTags",)),
                DesignerSemanticGroup(label="product_types", operation_ids=("GetProductTypes",)),
                DesignerSemanticGroup(label="producttaglistresponse", operation_ids=("GetProductTags",)),
                DesignerSemanticGroup(label="producttypelistresponse", operation_ids=("GetProductTypes",)),
                DesignerSemanticGroup(label="store", operation_ids=("GetProductTags", "GetProductTypes")),
            ),
        ),),
    ))
    service = DesignerService(SqlAlchemyDesignerRepository(database), inputs)
    try:
        proposed = await service.propose(OWNER_ID, agent.id)
        revision = proposed.revisions[0]
        assert revision.content.capabilities == (
            "product_tags: GetProductTags",
            "product_types: GetProductTypes",
        )
        assert tuple(
            operation_id
            for capability in revision.topology.capabilities
            for operation_id in capability.operation_ids
        ) == ("GetProductTags", "GetProductTypes")
        assert revision.source_inputs[0]["semantic_groups"][-1] == {
            "label": "store",
            "operation_ids": ["GetProductTags", "GetProductTypes"],
        }
    finally:
        await database.close()


def test_designer_routedeck_contract_keeps_review_and_build_separate() -> None:
    assert PROPOSE_DESIGN.safety_class is SafetyClass.DRAFT
    assert PROPOSE_DESIGN.review_policy is ReviewPolicy.NONE
    assert APPROVE_DESIGN.review_policy is ReviewPolicy.REQUIRED
    assert APPROVE_DESIGN.public_metadata_value() == {"review_surface_id": "designer.review"}
    assert REQUEST_BUILD.review_policy is ReviewPolicy.NONE


def test_designer_exposes_exact_attached_source_prerequisite_handoff() -> None:
    contract = compile_corpus_app().frontend_contract
    surface = contract.surfaces["designer.home"]
    affordances = {
        affordance.id: affordance.operation.id
        for affordance in surface.affordances
    }
    transitions = {
        (transition.source, transition.operation_id, transition.target)
        for transition in contract.transitions
    }

    assert affordances["open_source_prerequisite"] == "agents.open_attached_source"
    assert (
        "designer.home",
        "agents.open_attached_source",
        "sources.api",
    ) in transitions


@pytest.mark.asyncio
async def test_current_design_provider_reads_real_operation_request_arguments() -> None:
    agent_id = uuid.uuid4()
    current_revision_id = uuid.uuid4()

    class ServiceProbe:
        async def get(self, organization_id, selected_agent_id):
            assert organization_id == OWNER_ID
            assert selected_agent_id == agent_id
            return SimpleNamespace(
                current_revision_id=current_revision_id,
                accepted_revision_id=None,
            )

    class OwnerProbe:
        async def organization_id_for_route(self, route_session_id):
            assert route_session_id == "route-session"
            return OWNER_ID

    handle = f"agent-{agent_id.hex[:20]}"
    request = OperationRequest(
        session_id="route-session",
        request_id="request-1",
        expected_session_version=3,
        operation_id="designer.approve",
        source=OperationSource.SURFACE,
        arguments={
            "agent_ref": handle,
            "expected_revision_id": str(current_revision_id),
        },
    )
    context = SimpleNamespace(
        request=request,
        attempt_id="attempt-1",
        session=SimpleNamespace(
            session_id="route-session",
            private_state=SimpleNamespace(
                entity_bindings=(SimpleNamespace(
                    entity_kind="agent",
                    public_handle=handle,
                    private_id=str(agent_id),
                ),),
            ),
        ),
    )

    result = await CurrentDesignProvider(ServiceProbe(), OwnerProbe())(context)

    assert result.values.to_dict() == {
        "current_revision_id": str(current_revision_id),
        "accepted_revision_id": None,
    }
