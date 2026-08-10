from __future__ import annotations

import uuid
from datetime import UTC, datetime
from pathlib import Path

import pytest

from corpus.features.builder.domain import BuilderInputSnapshot, BuilderRecord, BuilderSourceBinding, RuntimeBuildArtifact
from corpus.features.builder.service import BuilderService
from corpus.features.sandbox.domain import RuntimeSandboxRun, SandboxRecord
from corpus.features.sandbox.service import SandboxService
from corpus.features.sandbox.operations import sandbox_tool_observation


def build_record(*, status="assembling", runtime_hash=None, bindings=()):
    now = datetime.now(UTC)
    return BuilderRecord(
        uuid.uuid4(), uuid.uuid4(), uuid.uuid4(), uuid.uuid4(), uuid.uuid4(), 3,
        status, runtime_hash, "gemma4", "d" * 64, tuple(bindings),
        ("GetProductTypes",) if status == "ready" else (), "n" * 64, {"nodes": []}, {"nodes": {}},
        None, None, now, now,
    )


class Agents:
    def __init__(self): self.lineage = None
    async def get(self, *_): return object()
    async def record_build_lineage(self, organization_id, agent_id, **values): self.lineage = (organization_id, agent_id, values)


class BuilderRepo:
    def __init__(self, value): self.value = value
    async def begin(self, *_args, **_kwargs): return self.value
    async def complete(self, _owner, _build, *, artifact, source_bindings):
        self.value = BuilderRecord(
            self.value.id, self.value.organization_id, self.value.agent_id,
            self.value.build_request_id, self.value.design_revision_id, self.value.agent_version,
            "ready", artifact.runtime_build_hash, artifact.model, artifact.model_digest,
            source_bindings, artifact.allowed_operation_ids, artifact.navgraph_hash,
            artifact.compiled_navgraph, artifact.frontend_contract, None, None,
            self.value.created_at, datetime.now(UTC),
        )
        return self.value
    async def fail(self, *_args, **_kwargs): raise AssertionError("unexpected failure")
    async def get_for_agent(self, *_): return (self.value,)
    async def get(self, *_): return self.value


class Inputs:
    def __init__(self, snapshot): self.value = snapshot
    async def current_build_request_id(self, *_): return self.value.build_request_id
    async def snapshot(self, *_): return self.value


class BuildRuntime:
    async def assemble(self, snapshot):
        return RuntimeBuildArtifact(
            "a" * 64, "gemma4", "d" * 64,
            tuple(op for item in snapshot.source_bindings for op in item.included_operation_ids),
            "n" * 64, {"nodes": []}, {"nodes": {}},
        )


@pytest.mark.asyncio
async def test_builder_persists_exact_runtime_binding_and_historical_lineage(tmp_path: Path):
    pending = build_record()
    binding = BuilderSourceBinding(
        "source-000000001", "revision-0000001", "curation-0000001", "f" * 64,
        ("GetProductTypes",), tmp_path / "artifacts", tmp_path / "openapi.json", "6" * 64,
        "profile-00000001", "http://127.0.0.1:9100", "api_key", "x-api-key",
        uuid.uuid4(), 2,
    )
    snapshot = BuilderInputSnapshot(
        pending.id, pending.build_request_id, pending.organization_id, pending.agent_id,
        pending.agent_version, pending.design_revision_id, "i" * 64, "Agent", "Answer exactly.",
        "Answer exactly.", ("Catalog",), ("Answer questions",), ("Use exact data.",),
        ("Catalog lookup",), ("GetProductTypes",), (binding,),
    )
    agents, repository = Agents(), BuilderRepo(pending)
    service = BuilderService(repository, Inputs(snapshot), BuildRuntime(), agents)

    result = await service.assemble_current(pending.organization_id, pending.agent_id)

    assert result.status == "ready"
    assert result.runtime_build_hash == "a" * 64
    assert result.source_bindings[0].profile_id == "profile-00000001"
    assert result.source_bindings[0].credential_version == 2
    assert agents.lineage[2]["source_references"] == (("source-000000001", "revision-0000001"),)


class ReadyBuilds:
    def __init__(self, value): self.value = value
    async def require_ready(self, *_): return self.value
    async def list(self, *_): return object()


class SandboxRepo:
    def __init__(self, build):
        now = datetime.now(UTC)
        self.value = SandboxRecord(uuid.uuid4(), build.organization_id, build.agent_id, build.id, build.runtime_build_hash, str(uuid.uuid4()), str(uuid.uuid4()), "running", None, None, 0, (), {}, None, now, now)
    async def begin(self, *_args, **_kwargs): return self.value
    async def complete(self, _owner, _id, result):
        self.value = SandboxRecord(
            self.value.id, self.value.organization_id, self.value.agent_id, self.value.build_id,
            self.value.runtime_build_hash, self.value.runtime_session_id, self.value.runtime_run_id,
            result.status, result.awaiting, result.final_response, result.api_call_count,
            result.safe_events, result.routedeck_projection, None, self.value.created_at, datetime.now(UTC),
        )
        return self.value
    async def begin_resume(self, owner, agent, record_id):
        assert (owner, agent, record_id) == (
            self.value.organization_id, self.value.agent_id, self.value.id
        )
        assert self.value.status == "waiting"
        self.value = SandboxRecord(
            self.value.id, self.value.organization_id, self.value.agent_id,
            self.value.build_id, self.value.runtime_build_hash,
            self.value.runtime_session_id, self.value.runtime_run_id, "running", None,
            self.value.final_response, self.value.api_call_count, self.value.safe_events,
            self.value.routedeck_projection, None, self.value.created_at, datetime.now(UTC), self.value.message,
        )
        return self.value
    async def fail(self, *_args, **_kwargs): raise AssertionError("unexpected failure")
    async def list(self, *_): return (self.value,)


class SandboxRuntime:
    def __init__(self): self.seen = None
    async def start(self, **values):
        self.seen = values
        return RuntimeSandboxRun(values["run_id"], "succeeded", None, "Observed Hats from the validated response.", 1, ({"sequence": 1, "kind": "api.result", "occurred_at": "now", "safe_data": {"operation_id": "GetProductTypes"}},), {"current": {"node_id": "agent_runtime.home"}})


@pytest.mark.asyncio
async def test_sandbox_uses_exact_ready_build_and_retains_safe_response_derived_result():
    ready = build_record(status="ready", runtime_hash="a" * 64, bindings=({"source_id": "source-000000001"},))
    repository, runtime = SandboxRepo(ready), SandboxRuntime()
    service = SandboxService(repository, runtime, ReadyBuilds(ready))

    result = await service.start(ready.organization_id, ready.agent_id, build_id=ready.id, message="List product types")

    assert runtime.seen["build"].id == ready.id
    assert result.final_response == "Observed Hats from the validated response."
    assert result.api_call_count == 1
    assert repr(result.events) == "(SandboxEventView(sequence=1, kind='api.result', occurred_at='now', safe_data={'operation_id': 'GetProductTypes'}),)"


class ClarifyingSandboxRuntime:
    def __init__(self): self.resume_values = None
    async def start(self, **values):
        return RuntimeSandboxRun(
            values["run_id"], "waiting", "routing_input", "What value should I use for id?", 0,
            ({"sequence": 1, "kind": "router.decision", "occurred_at": "now", "safe_data": {
                "resolution": "input_required",
                "candidates": [{
                    "operation_id": "GetProductTypesId",
                    "label": "Retrieve a Product Type",
                    "score": 1.0,
                }],
                "missing_params": ["id"],
            }},), {"current": {"node_id": "agent_runtime.home"}},
        )
    async def resume(self, **values):
        self.resume_values = values
        return RuntimeSandboxRun(
            values["record"].runtime_run_id, "succeeded", None,
            "Observed the exact product type.", 1,
            ({"sequence": 2, "kind": "clarification.user_answer", "occurred_at": "now", "safe_data": {"source": "user"}},),
            {"current": {"node_id": "agent_runtime.home"}},
        )


@pytest.mark.asyncio
async def test_sandbox_continues_the_exact_waiting_run_with_safe_clarification():
    ready = build_record(
        status="ready", runtime_hash="a" * 64,
        bindings=({"source_id": "source-000000001"},),
    )
    repository, runtime = SandboxRepo(ready), ClarifyingSandboxRuntime()
    service = SandboxService(repository, runtime, ReadyBuilds(ready))
    waiting = await service.start(
        ready.organization_id, ready.agent_id,
        build_id=ready.id, message="Get a product type by id",
    )

    assert waiting.status == "waiting"
    assert waiting.clarification is not None
    assert waiting.clarification.candidate_choices[0].operation_id == "GetProductTypesId"
    assert waiting.clarification.candidate_choices[0].label == "Retrieve a Product Type"
    assert waiting.clarification.missing_input_names == ("id",)
    assert sandbox_tool_observation(waiting) == {
        "status": "waiting",
        "final_response": "What value should I use for id?",
        "api_call_count": 0,
        "clarification": {
            "question": "What value should I use for id?",
            "candidate_choices": [{
                "operation_id": "GetProductTypesId",
                "label": "Retrieve a Product Type",
            }],
            "missing_input_names": ["id"],
        },
    }

    resumed = await service.resume(
        ready.organization_id, ready.agent_id,
        run_id=waiting.id,
        message="pt_exact",
        selected_operation_id="GetProductTypesId",
        answers={"id": "pt_exact"},
    )

    assert resumed.id == waiting.id
    assert resumed.status == "succeeded"
    assert resumed.api_call_count == 1
    assert runtime.resume_values["record"].runtime_run_id == waiting.runtime_run_id
