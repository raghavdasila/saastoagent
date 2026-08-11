from __future__ import annotations

import uuid

import pytest
from routedeck_core.contracts.interactions import OperationSource
from routedeck_core.contracts.operations import DeliveryPhase
from routedeck_core.ports.executor import ExecutionContext, ResolvedEntityInput

from corpus.features.evaluation.operations import GenerateSetHandler


class _OwnerScope:
    def __init__(self, owner_id: uuid.UUID) -> None:
        self.owner_id = owner_id

    async def organization_id_for_route(self, session_id: str) -> uuid.UUID:
        assert session_id == "evaluation-generation-session"
        return self.owner_id


class _EvaluationService:
    def __init__(self) -> None:
        self.generated: tuple[object, ...] | None = None

    async def generate_set(
        self,
        owner_id: uuid.UUID,
        agent_id: uuid.UUID,
        *,
        build_id: uuid.UUID | None,
        set_name: str,
        categories: tuple[str, ...],
    ) -> None:
        self.generated = (owner_id, agent_id, build_id, set_name, categories)


@pytest.mark.asyncio
async def test_generate_set_handler_returns_a_valid_queued_success_after_enqueue() -> None:
    owner_id = uuid.uuid4()
    agent_id = uuid.uuid4()
    service = _EvaluationService()
    context = ExecutionContext(
        session_id="evaluation-generation-session",
        request_id="evaluation-generation-request",
        attempt_id="evaluation-generation-attempt",
        node_id="evaluation.home",
        source=OperationSource.SURFACE,
        context_fingerprint="evaluation-generation-context",
        resolved_entities=(
            ResolvedEntityInput(
                argument_name="agent_ref",
                entity_kind="agent",
                private_id=str(agent_id),
            ),
        ),
    )

    outcome = await GenerateSetHandler(service, _OwnerScope(owner_id))(
        {
            "agent_ref": "selected-agent",
            "set_name": "Generated coverage",
            "categories": ["paraphrase"],
        },
        context,
    )

    assert service.generated == (
        owner_id,
        agent_id,
        None,
        "Generated coverage",
        ("paraphrase",),
    )
    assert outcome.outcome == "queued"
    assert outcome.delivery_phase is DeliveryPhase.RESPONSE_RECEIVED
