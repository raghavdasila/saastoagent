from __future__ import annotations

import uuid

import pytest
from routedeck_core.contracts.interactions import OperationSource
from routedeck_core.contracts.operations import DeliveryPhase
from routedeck_core.ports.executor import ExecutionContext, ResolvedEntityInput

from corpus.features.evaluation.operations import GenerateSetHandler, RunCaseHandler
from corpus.features.evaluation.schemas import run_evaluation_case_arguments


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
        self.queued: tuple[object, ...] | None = None

    async def queue_current_case(
        self,
        owner_id: uuid.UUID,
        agent_id: uuid.UUID,
        *,
        case_origin: str | None = None,
    ) -> None:
        self.queued = (owner_id, agent_id, case_origin)


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


@pytest.mark.asyncio
async def test_agent_run_case_resolves_one_semantic_origin_without_model_case_id() -> None:
    owner_id = uuid.uuid4()
    agent_id = uuid.uuid4()
    service = _EvaluationService()
    context = ExecutionContext(
        session_id="evaluation-generation-session",
        request_id="evaluation-run-request",
        attempt_id="evaluation-run-attempt",
        node_id="evaluation.home",
        source=OperationSource.AGENT,
        context_fingerprint="evaluation-run-context",
        resolved_entities=(
            ResolvedEntityInput(
                argument_name="agent_ref",
                entity_kind="agent",
                private_id=str(agent_id),
            ),
        ),
    )

    outcome = await RunCaseHandler(service, _OwnerScope(owner_id))(
        {
            "agent_ref": "selected-agent",
            "case_origin": "generated",
            "case_id": str(uuid.uuid4()),
        },
        context,
    )

    assert service.queued == (owner_id, agent_id, "generated")
    assert outcome.outcome == "queued"


def test_surface_run_case_requires_exact_id_and_rejects_semantic_origin() -> None:
    exact_case = uuid.uuid4()
    payload = run_evaluation_case_arguments(
        {"agent_ref": "selected-agent", "case_id": exact_case},
        OperationSource.SURFACE,
    )
    assert payload.case_id == exact_case

    with pytest.raises(ValueError, match="exact case selection"):
        run_evaluation_case_arguments(
            {"agent_ref": "selected-agent", "case_origin": "generated"},
            OperationSource.SURFACE,
        )


def test_run_case_contract_exposes_only_public_semantic_origins() -> None:
    from corpus.features.evaluation.declarations import RUN_CASE

    schema = RUN_CASE.input_schema.to_dict()
    origin = schema["properties"]["case_origin"]
    enum_values = next(item["enum"] for item in origin["anyOf"] if "enum" in item)
    assert enum_values == ["generated", "sandbox", "operations"]
