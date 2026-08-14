from __future__ import annotations

import uuid
from types import SimpleNamespace

import pytest
from pydantic import SecretStr
from routedeck_core.contracts.navigation import NodeRef

from corpus.features.evaluation.declarations import (
    CURRENT_EVALUATION_PROVIDER,
    RUN_CASE,
)
from corpus.features.evaluation.feature import create_evaluation_feature
from corpus.features.evaluation.providers import CurrentEvaluationProvider


class _OwnerScope:
    def __init__(self, owner_id: uuid.UUID) -> None:
        self.owner_id = owner_id

    async def organization_id_for_route(self, session_id: str) -> uuid.UUID:
        assert session_id == "evaluation-session"
        return self.owner_id


class _EvaluationService:
    def __init__(self, collection) -> None:
        self.collection = collection
        self.request = None

    async def list(self, owner_id: uuid.UUID, agent_id: uuid.UUID):
        self.request = (owner_id, agent_id)
        return self.collection


def _case(
    source_kind: str,
    *,
    run_status: str | None = None,
    latest_status: str | None = None,
    removed: bool = False,
):
    return SimpleNamespace(
        source_kind=source_kind,
        latest_status=latest_status,
        removed=removed,
        latest_run_attempt=(
            None if run_status is None else SimpleNamespace(status=run_status)
        ),
    )


@pytest.mark.asyncio
async def test_current_evaluation_provider_exposes_exact_pending_origin_counts() -> None:
    owner_id = uuid.uuid4()
    agent_id = uuid.uuid4()
    service = _EvaluationService(
        SimpleNamespace(
            evaluation_sets=(
                SimpleNamespace(
                    cases=(
                        _case("toolrouter"),
                        _case("sandbox"),
                        _case("operations", run_status="running"),
                        _case("operations", run_status="failed"),
                        _case("toolrouter", latest_status="passed"),
                        _case("sandbox", removed=True),
                        _case("unknown"),
                    )
                ),
            )
        )
    )
    provider = CurrentEvaluationProvider(service, _OwnerScope(owner_id))

    result = await provider(
        SimpleNamespace(
            session=SimpleNamespace(
                session_id="evaluation-session",
                private_state=SimpleNamespace(
                    entity_bindings=(
                        SimpleNamespace(
                            entity_kind="agent",
                            private_id=SecretStr(str(agent_id)),
                        ),
                    )
                ),
            )
        )
    )

    assert result.values.to_dict() == {
        "evaluation_set_count": 1,
        "pending_generated_case_count": 1,
        "pending_sandbox_case_count": 1,
        "pending_operations_case_count": 1,
        "active_case_run_count": 1,
    }
    assert service.request == (owner_id, agent_id)


def test_evaluation_node_and_run_case_require_current_evaluation_context() -> None:
    feature = create_evaluation_feature(
        NodeRef(id="agents.home"),
        NodeRef(id="builder.home"),
        NodeRef(id="channels.home"),
    )
    home = feature.nodes[0]

    assert CURRENT_EVALUATION_PROVIDER.id in {
        provider.id for provider in home.context_providers
    }
    assert CURRENT_EVALUATION_PROVIDER.ref in RUN_CASE.provider_refs
