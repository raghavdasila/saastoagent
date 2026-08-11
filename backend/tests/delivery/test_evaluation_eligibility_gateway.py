from __future__ import annotations

import uuid
from datetime import UTC, datetime

import pytest

from corpus.app.delivery_adapters import CorpusEligibilityGateway
from corpus.features.deployment.ports import DeploymentConflict
from corpus.features.evaluation.domain import (
    EvaluationCaseRecord,
    EvaluationRunRecord,
    EvaluationSetRecord,
    EligibilityRecord,
)


class Repository:
    def __init__(self, evaluation_set, cases, runs, eligibility):
        self.evaluation_set = evaluation_set
        self.case_values = cases
        self.run_values = runs
        self.eligibility = eligibility

    async def list_sets(self, owner_id, agent_id):
        assert (owner_id, agent_id) == (
            self.evaluation_set.organization_id,
            self.evaluation_set.agent_id,
        )
        return (self.evaluation_set,)

    async def cases(self, owner_id, evaluation_set_id):
        assert (owner_id, evaluation_set_id) == (
            self.evaluation_set.organization_id,
            self.evaluation_set.id,
        )
        return self.case_values

    async def runs(self, owner_id, evaluation_set_id):
        assert (owner_id, evaluation_set_id) == (
            self.evaluation_set.organization_id,
            self.evaluation_set.id,
        )
        return self.run_values

    async def latest_eligibility(self, owner_id, agent_id, build_id):
        assert (owner_id, agent_id, build_id) == (
            self.evaluation_set.organization_id,
            self.evaluation_set.agent_id,
            self.evaluation_set.build_id,
        )
        return self.eligibility


def records():
    owner_id, agent_id, build_id, evaluation_set_id = (
        uuid.uuid4(),
        uuid.uuid4(),
        uuid.uuid4(),
        uuid.uuid4(),
    )
    now = datetime.now(UTC)
    evaluation_set = EvaluationSetRecord(
        evaluation_set_id,
        owner_id,
        agent_id,
        build_id,
        "Deployment gate",
        None,
        "manual",
        None,
        None,
        None,
        now,
        now,
    )
    first_case = EvaluationCaseRecord(
        uuid.uuid4(), owner_id, evaluation_set_id, build_id, "runtime-case-1",
        None, "sandbox", "run-1", "Existing", "List products", "routing",
        "easy", ("GetProducts",), (), False, True, 1, None, now,
    )
    second_case = EvaluationCaseRecord(
        uuid.uuid4(), owner_id, evaluation_set_id, build_id, "runtime-case-2",
        None, "operations", "interaction-2", "New regression",
        "List product types", "deployed-interaction", "medium",
        ("GetProductTypes",), (), False, True, 1, None, now,
    )
    first_run = EvaluationRunRecord(
        uuid.uuid4(), owner_id, first_case.id, build_id, "runtime-eval-1",
        "passed", True, True, 1, (), now,
    )
    eligibility = EligibilityRecord(
        uuid.uuid4(), owner_id, agent_id, build_id, "b" * 64, True,
        ("runtime-eval-1",), ("all_mandatory_cases_passed",), now,
    )
    return evaluation_set, first_case, second_case, first_run, eligibility


@pytest.mark.asyncio
async def test_deployment_rejects_stored_eligibility_after_new_mandatory_case():
    evaluation_set, first_case, second_case, first_run, eligibility = records()
    gateway = CorpusEligibilityGateway(
        Repository(
            evaluation_set,
            (first_case, second_case),
            (first_run,),
            eligibility,
        )
    )

    with pytest.raises(DeploymentConflict, match="not eligible"):
        await gateway.require_eligible(
            evaluation_set.organization_id,
            evaluation_set.agent_id,
            evaluation_set.build_id,
        )


@pytest.mark.asyncio
async def test_deployment_accepts_current_evidence_for_every_mandatory_case():
    evaluation_set, first_case, second_case, first_run, eligibility = records()
    now = datetime.now(UTC)
    second_run = EvaluationRunRecord(
        uuid.uuid4(), evaluation_set.organization_id, second_case.id,
        evaluation_set.build_id, "runtime-eval-2", "passed", True, True, 1, (), now,
    )
    eligibility = EligibilityRecord(
        eligibility.id,
        eligibility.organization_id,
        eligibility.agent_id,
        eligibility.build_id,
        eligibility.runtime_build_hash,
        True,
        ("runtime-eval-1", "runtime-eval-2"),
        eligibility.reasons,
        now,
    )
    gateway = CorpusEligibilityGateway(
        Repository(
            evaluation_set,
            (first_case, second_case),
            (first_run, second_run),
            eligibility,
        )
    )

    value = await gateway.require_eligible(
        evaluation_set.organization_id,
        evaluation_set.agent_id,
        evaluation_set.build_id,
    )

    assert value.eligibility_id == eligibility.id
    assert value.runtime_build_hash == eligibility.runtime_build_hash
    assert len(value.eligibility_hash) == 64
