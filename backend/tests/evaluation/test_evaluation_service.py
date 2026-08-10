from __future__ import annotations

import json
import uuid
from datetime import UTC, datetime
from types import SimpleNamespace

import pytest

from corpus.features.evaluation.domain import EvaluationCaseRecord, EvaluationRunRecord, EvaluationSetRecord, EligibilityRecord
from corpus.features.evaluation.schemas import CreateEvaluationCaseArguments
from corpus.features.evaluation.service import EvaluationService
from corpus.app.agent_runtime_adapters import CorpusEvaluationReviewerPort
from corpus.integrations.agent_execution import EligibilityProjection, EvaluationCaseProjection, EvaluationRunProjection


class Builds:
    def __init__(self, owner, agent, build): self.owner, self.agent, self.build = owner, agent, build
    async def require_ready(self, owner, agent, build_id):
        assert (owner, agent, build_id) == (self.owner, self.agent, self.build.id)
        return self.build


class Sandbox:
    def __init__(self, run): self.run = run
    async def list(self, owner, agent): return SimpleNamespace(runs=(self.run,))


class Runtime:
    def __init__(self, build_hash): self.build_hash = build_hash; self.case_id = "runtime-case-1"; self.runs = 0
    def promote(self, **values):
        assert values["message"] == "List product types"
        return EvaluationCaseProjection(self.case_id, self.build_hash, values["run_id"], values["expected_operation_ids"], "e" * 64, 4, True)
    def evaluate(self, tenant_id, case_id):
        assert case_id == self.case_id
        self.runs += 1
        return EvaluationRunProjection(f"eval-{self.runs}", case_id, self.build_hash, "passed", True, True, (), datetime.now(UTC).isoformat())
    def eligibility(self, build_hash, case_ids):
        assert (build_hash, case_ids) == (self.build_hash, (self.case_id,))
        return EligibilityProjection(build_hash, True, ("eval-1",), ("all_mandatory_cases_passed",))


class Repository:
    def __init__(self): self.set = None; self.case = None; self.run = None; self.eligibility = None
    async def create_set(self, owner, agent, build, name):
        self.set = EvaluationSetRecord(uuid.uuid4(), owner, agent, build, name, datetime.now(UTC), datetime.now(UTC)); return self.set
    async def get_set(self, owner, agent, evaluation_set_id): return self.set
    async def list_sets(self, owner, agent): return (self.set,) if self.set else ()
    async def add_case(self, owner, evaluation_set, **values):
        runtime = values.pop("runtime")
        self.case = EvaluationCaseRecord(
            uuid.uuid4(), owner, evaluation_set.id, evaluation_set.build_id, runtime.case_id,
            values["source_kind"], values["source_record_id"], values["title"], values["message"],
            values["category"], values["difficulty"], values["expected_operation_ids"],
            values["required_response_fields"], values["require_write_verification"], values["mandatory"], datetime.now(UTC),
        ); return self.case
    async def get_case(self, owner, agent, case_id): return self.set, self.case
    async def cases(self, owner, evaluation_set_id): return (self.case,) if self.case else ()
    async def add_run(self, owner, case, runtime):
        self.run = EvaluationRunRecord(uuid.uuid4(), owner, case.id, case.build_id, runtime.evaluation_run_id, runtime.status, runtime.deterministic_pass, runtime.review_pass, runtime.reasons, datetime.now(UTC)); return self.run
    async def runs(self, owner, evaluation_set_id): return (self.run,) if self.run else ()
    async def add_eligibility(self, owner, agent, build, build_hash, runtime):
        self.eligibility = EligibilityRecord(uuid.uuid4(), owner, agent, build, build_hash, runtime.eligible, runtime.supporting_evaluation_run_ids, runtime.reasons, datetime.now(UTC)); return self.eligibility
    async def latest_eligibility(self, owner, agent, build): return self.eligibility


@pytest.mark.asyncio
async def test_sandbox_interaction_becomes_exact_build_case_and_eligibility():
    owner, agent, build_id, sandbox_id = uuid.uuid4(), uuid.uuid4(), uuid.uuid4(), uuid.uuid4()
    build_hash = "a" * 64
    build = SimpleNamespace(id=build_id, runtime_build_hash=build_hash, allowed_operation_ids=("GetProductTypes",))
    sandbox = SimpleNamespace(
        id=sandbox_id,
        build_id=build_id,
        runtime_run_id="runtime-run-1",
        status="succeeded",
        message="List product types",
        events=(SimpleNamespace(safe_data={"operation_id": "GetProductTypes"}),),
    )
    repository, runtime = Repository(), Runtime(build_hash)
    service = EvaluationService(repository, runtime, Builds(owner, agent, build), Sandbox(sandbox))

    created = await service.create_case_from_sandbox(
        owner, agent, build_id=build_id, sandbox_run_id=sandbox_id,
        set_name="Store taxonomy", title="Lists product types", category="routing",
        difficulty="easy", mandatory=True,
    )
    assert created.evaluation_sets[0].cases[0].category == "routing"
    assert created.evaluation_sets[0].cases[0].expected_operation_ids == ("GetProductTypes",)
    evaluated = await service.run_case(owner, agent, repository.case.id)
    assert evaluated.evaluation_sets[0].cases[0].latest_status == "passed"
    assert evaluated.evaluation_sets[0].eligible is True
    assert runtime.runs == 1


def test_create_case_contract_does_not_accept_client_supplied_operation_evidence():
    properties = CreateEvaluationCaseArguments.model_json_schema()["properties"]

    assert "expected_operation_ids" not in properties
    with pytest.raises(ValueError):
        CreateEvaluationCaseArguments.model_validate({
            "agent_ref": "agent-ref",
            "set_name": "Store taxonomy",
            "title": "Lists product types",
            "category": "routing",
            "difficulty": "easy",
            "expected_operation_ids": ["GetProductTypes"],
        })


def test_evaluation_reviewer_treats_intentional_body_redaction_as_absence_not_failure():
    class Model:
        messages = None

        def invoke(self, messages):
            self.messages = messages
            return SimpleNamespace(content=json.dumps({"passed": True, "reasons": ["safe evidence is consistent"]}))

    model = Model()
    reviewer = CorpusEvaluationReviewerPort(
        model,
        lambda: ("test-model", "digest"),
        plain_json=True,
    )
    review = reviewer.review(
        SimpleNamespace(expected_operations=("GetProductTypes",)),
        SimpleNamespace(
            status=SimpleNamespace(value="succeeded"),
            final_response="No product types are available. The request succeeded, but returned an empty list.",
        ),
        (
            SimpleNamespace(
                sequence=1,
                kind="api.result",
                safe_data={
                    "operation_id": "GetProductTypes",
                    "status": "succeeded",
                    "http_status": 200,
                    "outcome_verified": True,
                    "validation_issues": [],
                    "response_summary": {
                        "type": "dict",
                        "keys": ["count", "limit", "offset", "product_types"],
                    },
                },
            ),
        ),
    )

    assert review.passed is True
    system = model.messages[0][1]
    assert "Raw API response bodies are intentionally absent for privacy." in system
    assert "Do not fail merely because" in system
