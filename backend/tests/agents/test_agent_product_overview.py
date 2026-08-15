from __future__ import annotations

import asyncio
import uuid
from datetime import UTC, datetime, timedelta
from types import SimpleNamespace

from routedeck_core.contracts.session import PrivateEntityBinding

from corpus.app.agent_overview_adapters import CorpusAgentProductOverviewGateway
from corpus.features.designer.ports import DesignerUnavailable
from corpus.features.agents.providers import SelectedAgentOverviewProvider
from corpus.features.agents.schemas import AgentProductOverviewView


NOW = datetime(2026, 8, 11, tzinfo=UTC)
ORG = uuid.uuid4()
AGENT = uuid.uuid4()


class Repository:
    async def list_source_attachments(self, organization_id, agent_id):
        assert (organization_id, agent_id) == (ORG, AGENT)
        return (object(), object())


class Agents:
    repository = Repository()

    async def get(self, organization_id, agent_id):
        assert (organization_id, agent_id) == (ORG, AGENT)
        return SimpleNamespace(id=AGENT, current_version=4)


class Designer:
    async def get(self, organization_id, agent_id):
        return SimpleNamespace(
            accepted_revision_id=uuid.uuid4(),
            revisions=(SimpleNamespace(revision=3),),
        )


class Builder:
    async def list(self, organization_id, agent_id):
        return SimpleNamespace(builds=(SimpleNamespace(
            id=uuid.uuid4(), status="ready", runtime_lifecycle="running",
            created_at=NOW,
        ),))


class Evaluation:
    async def list(self, organization_id, agent_id):
        case = SimpleNamespace(latest_run_attempt=SimpleNamespace(status="succeeded"))
        return SimpleNamespace(evaluation_sets=(SimpleNamespace(
            generation_status="ready", cases=(case, case), eligible=True,
            created_at=NOW,
        ),))


class Channels:
    def __init__(self, active_id):
        self.active_id = active_id

    async def list(self, organization_id, agent_id):
        return (SimpleNamespace(
            id=uuid.uuid4(), slug="store-taxonomy", status="ready", enabled=True,
            active_deployment_id=self.active_id, created_at=NOW,
        ),)


class Deployments:
    def __init__(self, active_id):
        self.active_id = active_id

    async def list(self, organization_id, agent_id):
        return (
            SimpleNamespace(
                id=self.active_id, status="ready", created_at=NOW,
            ),
            SimpleNamespace(
                id=uuid.uuid4(), status="failed", created_at=NOW + timedelta(seconds=1),
            ),
        )


class Operations:
    async def list(self, organization_id, agent_id):
        return SimpleNamespace(interactions=(object(), object(), object()))


def test_selected_agent_overview_joins_current_authoritative_module_truth() -> None:
    active_id = uuid.uuid4()
    value = asyncio.run(CorpusAgentProductOverviewGateway(
        Agents(), Designer(), Builder(), Evaluation(), Channels(active_id),
        Deployments(active_id), Operations(),
    ).overview(ORG, AGENT))

    assert value.agent_id == AGENT
    assert value.agent_version == 4
    assert value.source_count == 2
    assert (value.design_status, value.design_revision) == ("accepted", 3)
    assert (value.build_status, value.build_runtime_lifecycle) == ("ready", "running")
    assert (value.evaluation_status, value.evaluation_case_count, value.evaluation_eligible) == (
        "eligible", 2, True,
    )
    # A later failed deployment attempt does not erase the exact active deployment.
    assert (value.delivery_status, value.hosted_path) == ("live", "/store-taxonomy")
    assert value.operations_count == 3
    assert value.next_step == "Inspect deployed interaction evidence in Operations."


def test_selected_agent_overview_reports_missing_design_without_inventing_downstream_state() -> None:
    class MissingDesigner:
        async def get(self, organization_id, agent_id):
            raise DesignerUnavailable("No design exists.")

    class Empty:
        async def list(self, organization_id, agent_id):
            return ()

    class EmptyBuilds:
        async def list(self, organization_id, agent_id):
            return SimpleNamespace(builds=())

    class EmptyEvaluation:
        async def list(self, organization_id, agent_id):
            return SimpleNamespace(evaluation_sets=())

    class EmptyOperations:
        async def list(self, organization_id, agent_id):
            return SimpleNamespace(interactions=())

    value = asyncio.run(CorpusAgentProductOverviewGateway(
        Agents(), MissingDesigner(), EmptyBuilds(), EmptyEvaluation(), Empty(),
        Empty(), EmptyOperations(),
    ).overview(ORG, AGENT))

    assert value.design_status == "missing"
    assert value.build_status is None
    assert value.delivery_status == "none"
    assert value.next_step == "Describe and review this Agent in Designer."


def test_selected_agent_context_is_empty_without_selection_and_exact_after_selection() -> None:
    class Overview:
        async def get(self, organization_id, agent_id):
            assert (organization_id, agent_id) == (ORG, AGENT)
            return AgentProductOverviewView(
                agent_id=AGENT, agent_version=4, source_count=2,
                design_status="accepted", design_revision=3,
                build_status="ready", build_runtime_lifecycle="running",
                evaluation_status="eligible", evaluation_case_count=2,
                evaluation_eligible=True, delivery_status="live",
                hosted_path="/store-taxonomy", operations_count=3,
                next_step="Inspect deployed interaction evidence in Operations.",
            )

    class OwnerScope:
        async def organization_id_for_route(self, route_session_id):
            assert route_session_id == "route-session"
            return ORG

    provider = SelectedAgentOverviewProvider(Overview(), OwnerScope())
    no_selection = SimpleNamespace(session=SimpleNamespace(
        session_id="route-session",
        private_state=SimpleNamespace(entity_bindings=()),
    ))
    empty = asyncio.run(provider(no_selection))
    assert empty.values.to_dict() == {}

    selected = SimpleNamespace(session=SimpleNamespace(
        session_id="route-session",
        private_state=SimpleNamespace(entity_bindings=(PrivateEntityBinding(
            entity_kind="agent",
            public_handle=f"agent-{AGENT.hex[:20]}",
            private_id=str(AGENT),
        ),)),
    ))
    populated = asyncio.run(provider(selected))
    assert populated.values.to_dict()["agent_id"] == str(AGENT)
    assert populated.values.to_dict()["delivery_status"] == "live"
