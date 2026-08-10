from __future__ import annotations

import uuid

import pytest

from corpus.features.operations.domain import OperationsLineage
from corpus.features.operations.service import OperationsService
from corpus.integrations.agent_delivery import InteractionProjection


class Delivery:
    def __init__(self, interaction): self.value = interaction
    def interactions(self): return (self.value,)
    def interaction(self, interaction_id): assert interaction_id == self.value.interaction_id; return self.value


class Lineage:
    def __init__(self, owner, value): self.owner, self.value = owner, value
    async def resolve(self, owner, deployment_id, request_id):
        return self.value if owner == self.owner and deployment_id == "runtime-deployment" and request_id == "runtime-run" else None


class Evaluation:
    def __init__(self): self.values = None
    async def create_case_from_operations(self, owner, agent, **values): self.values = (owner, agent, values); return "created"


@pytest.mark.asyncio
async def test_owner_operations_projects_safe_trace_and_promotes_exact_runtime_run():
    owner, agent, build, deployment = uuid.uuid4(), uuid.uuid4(), uuid.uuid4(), uuid.uuid4()
    interaction = InteractionProjection(
        "interaction-1", "public-session", "runtime-deployment",
        "List product types", "Observed Hats", "completed", {"request_id": "runtime-run"},
    )
    lineage = OperationsLineage(agent, build, deployment, "runtime-run", ({
        "sequence": 1, "kind": "api.result", "safe_data": {"operation_id": "GetProductTypes", "status": "succeeded"},
    },))
    evaluation = Evaluation()
    service = OperationsService(Delivery(interaction), Lineage(owner, lineage), evaluation)

    inventory = await service.list(owner)
    assert inventory.interactions[0].events[0].safe_data["operation_id"] == "GetProductTypes"
    await service.promote(owner, interaction_id="interaction-1", set_name="Production", title="Taxonomy", category="operations", difficulty="medium", mandatory=True)
    assert evaluation.values[2]["runtime_run_id"] == "runtime-run"
    assert evaluation.values[2]["expected_operation_ids"] == ("GetProductTypes",)
