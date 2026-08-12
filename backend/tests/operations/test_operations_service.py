from __future__ import annotations

import uuid

import pytest

from corpus.features.operations.domain import OperationsLineage
from corpus.features.operations.ports import OperationsUnavailable
from corpus.features.operations.service import OperationsService
from corpus.integrations.agent_delivery import InteractionProjection


class Delivery:
    def __init__(self, interaction):
        self.values = (interaction,)

    def interactions(self):
        return self.values

    def interaction(self, interaction_id):
        return next(value for value in self.values if value.interaction_id == interaction_id)


class Lineage:
    def __init__(self, owner, value): self.owner, self.value = owner, value
    async def resolve(self, owner, deployment_id, request_id):
        return self.value if owner == self.owner and deployment_id == "runtime-deployment" and request_id == "runtime-run" else None


class Evaluation:
    def __init__(self): self.values = None; self.promoted = {}
    async def create_case_from_operations(self, owner, agent, **values): self.values = (owner, agent, values); return "created"
    async def promoted_operations_case_id(self, owner, interaction_id):
        return self.promoted.get((owner, interaction_id))


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
    assert inventory.interactions[0].status == "completed"
    assert inventory.interactions[0].evaluation_case_id is None
    assert inventory.interactions[0].events[0].safe_data["operation_id"] == "GetProductTypes"
    await service.promote(owner, interaction_id="interaction-1", set_name="Production", title="Taxonomy", category="operations", difficulty="medium", mandatory=True)
    assert evaluation.values[2]["runtime_run_id"] == "runtime-run"
    assert evaluation.values[2]["expected_operation_ids"] == ("GetProductTypes",)


@pytest.mark.asyncio
async def test_operations_projects_persisted_evaluation_promotion_after_reload():
    owner, agent, build, deployment, case_id = (
        uuid.uuid4(), uuid.uuid4(), uuid.uuid4(), uuid.uuid4(), uuid.uuid4()
    )
    interaction = InteractionProjection(
        "interaction-promoted", "public-session", "runtime-deployment",
        "List product types", "Observed Apparel", "completed",
        {"request_id": "runtime-run"},
    )
    lineage = OperationsLineage(agent, build, deployment, "runtime-run", ({
        "sequence": 1, "kind": "api.result",
        "safe_data": {"operation_id": "GetProductTypes", "status": "succeeded"},
    },))
    evaluation = Evaluation()
    evaluation.promoted[(owner, interaction.interaction_id)] = case_id
    service = OperationsService(Delivery(interaction), Lineage(owner, lineage), evaluation)

    inventory = await service.list(owner)

    assert inventory.interactions[0].evaluation_case_id == case_id


@pytest.mark.asyncio
async def test_operations_rejects_failed_api_result_as_evaluation_evidence():
    owner, agent, build, deployment = (
        uuid.uuid4(), uuid.uuid4(), uuid.uuid4(), uuid.uuid4()
    )
    interaction = InteractionProjection(
        "interaction-failed-result", "public-session", "runtime-deployment",
        "List product types", "The API request failed.", "completed",
        {"request_id": "runtime-run"},
    )
    lineage = OperationsLineage(agent, build, deployment, "runtime-run", ({
        "sequence": 1,
        "kind": "api.result",
        "safe_data": {
            "operation_id": "GetProductTypes",
            "status": "failed",
        },
    },))
    service = OperationsService(Delivery(interaction), Lineage(owner, lineage), Evaluation())

    with pytest.raises(OperationsUnavailable, match="no completed API operation"):
        await service.promote(
            owner,
            interaction_id="interaction-failed-result",
            set_name="Production",
            title="Taxonomy",
            category="operations",
            difficulty="medium",
            mandatory=True,
        )


@pytest.mark.asyncio
async def test_operations_projects_the_completed_clarification_continuation_as_one_run():
    owner, agent, build, deployment = (
        uuid.uuid4(), uuid.uuid4(), uuid.uuid4(), uuid.uuid4()
    )
    initial = InteractionProjection(
        "interaction-initial", "public-session", "runtime-deployment",
        "Show me the product taxonomy.",
        "Should I use product tags or product types?", "completed",
        {"request_id": "runtime-run"},
    )
    continuation = InteractionProjection(
        "interaction-continuation", "public-session", "runtime-deployment",
        "Product types.", "No product types were found.", "completed",
        {"request_id": "continuation-request"},
    )
    delivery = Delivery(initial)
    # The neutral delivery boundary returns newest interactions first.
    delivery.values = (continuation, initial)
    lineage = OperationsLineage(agent, build, deployment, "runtime-run", (
        {
            "sequence": 1,
            "kind": "run.needs_input",
            "safe_data": {"status": "waiting"},
        },
        {
            "sequence": 2,
            "kind": "clarification.user_answer",
            "safe_data": {},
        },
        {
            "sequence": 3,
            "kind": "api.result",
            "safe_data": {
                "operation_id": "GetProductTypes", "status": "succeeded"
            },
        },
        {"sequence": 4, "kind": "run.completed", "safe_data": {}},
    ))
    evaluation = Evaluation()
    service = OperationsService(delivery, Lineage(owner, lineage), evaluation)

    inventory = await service.list(owner)

    assert len(inventory.interactions) == 1
    interaction = inventory.interactions[0]
    assert interaction.interaction_id == "interaction-initial"
    assert interaction.input_summary == "Show me the product taxonomy."
    assert interaction.output_summary == "No product types were found."
    assert [event.kind for event in interaction.events] == [
        "run.needs_input",
        "clarification.user_answer",
        "api.result",
        "run.completed",
    ]


@pytest.mark.asyncio
async def test_operations_does_not_borrow_an_unmatched_interaction_without_answer_evidence():
    owner, agent, build, deployment = (
        uuid.uuid4(), uuid.uuid4(), uuid.uuid4(), uuid.uuid4()
    )
    initial = InteractionProjection(
        "interaction-initial", "public-session", "runtime-deployment",
        "List product types.", "No product types were found.", "completed",
        {"request_id": "runtime-run"},
    )
    unmatched = InteractionProjection(
        "interaction-unmatched", "public-session", "runtime-deployment",
        "Unrelated later request.", "Unrelated output.", "completed",
        {"request_id": "missing-run"},
    )
    delivery = Delivery(initial)
    delivery.values = (unmatched, initial)
    lineage = OperationsLineage(agent, build, deployment, "runtime-run", (
        {
            "sequence": 1,
            "kind": "api.result",
            "safe_data": {
                "operation_id": "GetProductTypes", "status": "succeeded"
            },
        },
        {"sequence": 2, "kind": "run.completed", "safe_data": {}},
    ))
    service = OperationsService(
        delivery, Lineage(owner, lineage), Evaluation()
    )

    inventory = await service.list(owner)

    assert len(inventory.interactions) == 1
    assert inventory.interactions[0].output_summary == "No product types were found."
