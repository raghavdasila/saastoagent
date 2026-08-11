from __future__ import annotations

from pathlib import Path

import pytest
from agent_execution_runtime import (
    ApiCallResult,
    RoutingCandidate,
    RoutingDecision,
)
from agent_execution_runtime.ports import ModelDecision, ModelToolRequest, ReviewResult

from corpus.integrations.agent_execution import (
    BuildConnectionSpec,
    EvaluationCaseSpec,
    ImmutableBuildSpec,
    NeutralAgentExecutionAdapter,
    NeutralEvaluationAdapter,
    SandboxRunSpec,
)


class MemoryStore:
    def __init__(self) -> None:
        self.builds = {}
        self.runs = {}
        self.run_events = {}
        self.cases = {}
        self.evaluation_runs = []

    def save_build(self, build): self.builds[build.content_hash] = build
    def get_build(self, build_hash): return self.builds[build_hash]
    def create_run(self, run): self.runs[(run.tenant_id, run.run_id)] = run; self.run_events[run.run_id] = []
    def update_run(self, run): self.runs[(run.tenant_id, run.run_id)] = run
    def append_event(self, run_id, event): self.run_events[run_id].append(event)
    def get_run(self, tenant_id, run_id): return self.runs[(tenant_id, run_id)]
    def events(self, tenant_id, run_id): return tuple(self.run_events[run_id])
    def list_runs(self, tenant_id): return tuple(run for (owner, _), run in self.runs.items() if owner == tenant_id)
    def save_case(self, case): self.cases[case.case_id] = case
    def get_case(self, case_id): return self.cases[case_id]
    def save_eval_run(self, run): self.evaluation_runs.append(run)
    def eval_runs(self, build_hash): return tuple(run for run in self.evaluation_runs if run.build_hash == build_hash)


class ModelProbe:
    def decide(self, build, message):
        return ModelDecision("api", (ModelToolRequest("call-1", "list product types"),))

    def answer(self, build, message, results):
        return "Observed product types."


class RouterProbe:
    def route(self, build, query, provided):
        return RoutingDecision(
            "ROUTE",
            "exact curated operation",
            (RoutingCandidate("GetProductTypes", 1.0),),
        )


class ClarificationRouterProbe:
    def route(self, build, query, provided):
        if provided.get("id") == "pt_exact":
            return RoutingDecision(
                "ROUTE",
                "exact curated operation",
                (RoutingCandidate("GetProductTypesId", 1.0),),
            )
        return RoutingDecision(
            "ASK_PARAM",
            "required id is missing",
            (RoutingCandidate("GetProductTypesId", 1.0),),
            ("id",),
        )


class AmbiguousRouterProbe:
    def route(self, build, query, provided):
        return RoutingDecision(
            "ASK_DISAMBIGUATE",
            "taxonomy choice required",
            (
                RoutingCandidate("GetProductTypes", 0.61),
                RoutingCandidate("GetProductTags", 0.60),
            ),
        )


class ExecutorProbe:
    def __init__(self) -> None:
        self.calls = 0

    async def execute(self, *, build, tenant_id, operation_id, inputs, execution_id):
        self.calls += 1
        return ApiCallResult(
            execution_id,
            operation_id,
            "succeeded",
            200,
            {"product_types": []},
            outcome_verified=True,
        )


class ReviewerProbe:
    def review(self, case, run, events):
        return ReviewResult(True, (), "reviewer-v1", "b" * 64, "c" * 64, 12)


@pytest.mark.asyncio
async def test_neutral_adapter_keeps_build_immutable_and_returns_redacted_run_projection(tmp_path: Path) -> None:
    store = MemoryStore()
    executor = ExecutorProbe()
    adapter = NeutralAgentExecutionAdapter(store, ModelProbe(), RouterProbe(), executor)
    source_hash = "6fca793be700dfb8bf511c2217d72cf97abf2f6cba08fbc2cd26ef0369b8f3f6"
    built = adapter.assemble(ImmutableBuildSpec(
        build_id="build-0000000001",
        version=1,
        name="Store helper",
        instructions="Use the exact curated operation.",
        model="gemma4:latest",
        model_digest="a" * 64,
        source_path=str(tmp_path / "effective-openapi.json"),
        source_hash=source_hash,
        allowed_operations=("GetProductTypes",),
        preauthorized_write_operations=(),
        connections=(BuildConnectionSpec(
            connection_id="profile-00000001",
            revision=1,
            base_url="http://127.0.0.1:9100",
            openapi_path=str(tmp_path / "effective-openapi.json"),
            openapi_hash=source_hash,
            auth_plugin_id="api_key",
            credential_ref="credential-ref-not-public",
            operation_ids=("GetProductTypes",),
        ),),
    ))
    assert adapter.load_build(built.content_hash) == built

    canary = "user-secret-canary"
    result = await adapter.run(SandboxRunSpec(
        tenant_id="owner-0000000001",
        session_id="sandbox-session-01",
        build_hash=built.content_hash,
        message=f"List product types {canary}",
    ))

    assert result.status == "succeeded"
    assert result.final_response == "Observed product types."
    assert result.api_call_count == 1
    assert executor.calls == 1
    serialized = repr(result)
    assert canary not in serialized
    assert "credential-ref-not-public" not in serialized
    assert "GetProductTypes" in serialized
    assert adapter.load_run("owner-0000000001", result.run_id) == result

    evaluation = NeutralEvaluationAdapter(store, ReviewerProbe())
    case = evaluation.promote(EvaluationCaseSpec(
        tenant_id="owner-0000000001",
        run_id=result.run_id,
        message="List product types",
        expected_operation_ids=("GetProductTypes",),
    ))
    evaluated = evaluation.evaluate("owner-0000000001", case.case_id)
    eligibility = evaluation.eligibility(built.content_hash, (case.case_id,))

    assert evaluation.load_case(case.case_id) == case
    assert evaluated.status == "passed"
    assert eligibility.eligible is True
    assert eligibility.supporting_evaluation_run_ids == (evaluated.evaluation_run_id,)
    assert canary not in repr((case, evaluated, eligibility))


@pytest.mark.asyncio
async def test_ambiguous_operation_question_uses_natural_labels_not_internal_ids(tmp_path: Path) -> None:
    store = MemoryStore()
    executor = ExecutorProbe()
    adapter = NeutralAgentExecutionAdapter(
        store, ModelProbe(), AmbiguousRouterProbe(), executor
    )
    source_hash = "6" * 64
    build = adapter.assemble(ImmutableBuildSpec(
        build_id="build-ambiguity-1",
        version=1,
        name="Taxonomy helper",
        instructions="Ask when the taxonomy category is unclear.",
        model="model",
        model_digest="a" * 64,
        source_path=str(tmp_path / "effective-openapi.json"),
        source_hash=source_hash,
        allowed_operations=("GetProductTypes", "GetProductTags"),
        preauthorized_write_operations=(),
        connections=(BuildConnectionSpec(
            connection_id="profile-ambiguity",
            revision=1,
            base_url="http://127.0.0.1:9100",
            openapi_path=str(tmp_path / "effective-openapi.json"),
            openapi_hash=source_hash,
            auth_plugin_id="api_key",
            credential_ref="credential-ref-not-public",
            operation_ids=("GetProductTypes", "GetProductTags"),
        ),),
    ))

    waiting = await adapter.run(SandboxRunSpec(
        tenant_id="owner-ambiguity",
        session_id="session-ambiguity",
        build_hash=build.content_hash,
        message="get product taxonomy",
    ))

    assert waiting.status == "waiting"
    assert waiting.final_response == "Should I use product types or product tags?"
    assert "GetProduct" not in waiting.final_response
    assert executor.calls == 0


@pytest.mark.asyncio
async def test_neutral_adapter_exposes_natural_same_run_clarification_without_internal_outcomes(tmp_path: Path) -> None:
    store = MemoryStore()
    executor = ExecutorProbe()
    adapter = NeutralAgentExecutionAdapter(
        store, ModelProbe(), ClarificationRouterProbe(), executor
    )
    source_hash = "6" * 64
    build = adapter.assemble(ImmutableBuildSpec(
        build_id="build-clarification-1",
        version=1,
        name="Clarifying store helper",
        instructions="Use the exact curated operation and ask for missing input.",
        model="gemma4:latest",
        model_digest="a" * 64,
        source_path=str(tmp_path / "effective-openapi.json"),
        source_hash=source_hash,
        allowed_operations=("GetProductTypesId",),
        preauthorized_write_operations=(),
        connections=(BuildConnectionSpec(
            connection_id="profile-clarification",
            revision=1,
            base_url="http://127.0.0.1:9100",
            openapi_path=str(tmp_path / "effective-openapi.json"),
            openapi_hash=source_hash,
            auth_plugin_id="api_key",
            credential_ref="credential-ref-not-public",
            operation_ids=("GetProductTypesId",),
        ),),
    ))

    waiting = await adapter.run(SandboxRunSpec(
        tenant_id="owner-clarification",
        session_id="session-clarification",
        build_hash=build.content_hash,
        message="Get a product type by id",
        run_id="run-clarification",
    ))

    assert waiting.status == "waiting"
    assert waiting.awaiting == "routing_input"
    assert waiting.final_response == "What value should I use for id?"
    assert "ASK_PARAM" not in repr(waiting)
    assert "required id is missing" not in repr(waiting)
    assert executor.calls == 0
    assert adapter.session_messages(
        "owner-clarification", "session-clarification", build.content_hash
    ) == (
        {"role": "user", "content": "Get a product type by id"},
        {"role": "assistant", "content": "What value should I use for id?"},
    )

    resumed = await adapter.run(SandboxRunSpec(
        tenant_id="owner-clarification",
        session_id="session-clarification",
        build_hash=build.content_hash,
        message="pt_exact",
        run_id=waiting.run_id,
        command="resume",
        selected_operation_id="GetProductTypesId",
        provided_inputs={"id": "pt_exact", "path": {"id": "pt_exact"}},
    ))

    assert resumed.run_id == waiting.run_id
    assert resumed.status == "succeeded"
    assert resumed.api_call_count == 1
    assert executor.calls == 1
    assert any(event.kind == "clarification.user_answer" for event in resumed.events)
    assert "pt_exact" not in repr(resumed.events)
    assert adapter.session_messages(
        "owner-clarification", "session-clarification", build.content_hash
    ) == (
        {"role": "user", "content": "Get a product type by id"},
        {"role": "assistant", "content": "What value should I use for id?"},
        {"role": "user", "content": "pt_exact"},
        {"role": "assistant", "content": "Observed product types."},
    )
