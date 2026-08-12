from __future__ import annotations

import uuid
from dataclasses import replace
from datetime import UTC, datetime
from pathlib import Path

import pytest

from corpus.features.builder.domain import BuilderInputSnapshot, BuilderRecord, BuilderSourceBinding, RuntimeBuildArtifact
from corpus.features.builder.ports import BuilderConflict
from corpus.features.builder.service import BuilderService
from corpus.features.builder.schemas import build_runtime_lifecycle_arguments
from routedeck_core.contracts.operations import OperationSource
from corpus.jobs.domain import DurableJobRecord, DurableJobState
from corpus.features.sandbox.domain import RuntimeSandboxRun, SandboxRecord
from corpus.features.sandbox.ports import SandboxRunFailed
from corpus.features.sandbox.service import SandboxService
from corpus.features.sandbox.operations import sandbox_tool_observation


def build_record(*, status="queued", runtime_hash=None, bindings=()):
    now = datetime.now(UTC)
    return BuilderRecord(
        uuid.uuid4(), uuid.uuid4(), uuid.uuid4(), uuid.uuid4(), uuid.uuid4(), 3,
        status, "running" if status == "ready" else "stopped",
        runtime_hash, "gemma4", "d" * 64, tuple(bindings),
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
            "ready", "stopped", artifact.runtime_build_hash, artifact.model, artifact.model_digest,
            source_bindings, artifact.allowed_operation_ids, artifact.navgraph_hash,
            artifact.compiled_navgraph, artifact.frontend_contract, None, None,
            self.value.created_at, datetime.now(UTC),
        )
        return self.value
    async def link_job(self, _owner, _build, job_id):
        self.value = replace(self.value, job_id=job_id)
        return self.value
    async def fail(self, *_args, **_kwargs): raise AssertionError("unexpected failure")
    async def get_for_agent(self, *_): return (self.value,)
    async def get(self, *_): return self.value
    async def set_runtime_lifecycle(self, _owner, _agent, _build, *, lifecycle):
        self.value = BuilderRecord(
            self.value.id, self.value.organization_id, self.value.agent_id,
            self.value.build_request_id, self.value.design_revision_id,
            self.value.agent_version, self.value.status, lifecycle,
            self.value.runtime_build_hash, self.value.model, self.value.model_digest,
            self.value.source_bindings, self.value.allowed_operation_ids,
            self.value.navgraph_hash, self.value.compiled_navgraph,
            self.value.frontend_contract, self.value.failure_code,
            self.value.failure_message, self.value.created_at, datetime.now(UTC),
        )
        return self.value


class Inputs:
    def __init__(self, snapshot): self.value = snapshot
    async def current_build_request_id(self, *_): return self.value.build_request_id
    async def snapshot(self, *_): return self.value


@pytest.mark.asyncio
async def test_builder_agent_lifecycle_resolves_only_exact_current_build_after_async_completion():
    current = build_record(status="ready", runtime_hash="a" * 64)
    stale = replace(
        build_record(status="ready", runtime_hash="b" * 64),
        organization_id=current.organization_id,
        agent_id=current.agent_id,
        build_request_id=uuid.uuid4(),
    )
    failed_prior_attempt = replace(
        current,
        id=uuid.uuid4(),
        status="failed",
        runtime_build_hash=None,
        attempt_number=current.attempt_number - 1 if current.attempt_number > 1 else 1,
    )
    current = replace(current, attempt_number=failed_prior_attempt.attempt_number + 1)

    arguments = build_runtime_lifecycle_arguments(
        {"agent_ref": "agent-current", "build_id": str(stale.id)},
        OperationSource.AGENT,
    )
    assert arguments.agent_ref == "agent-current"
    assert arguments.build_id is None
    surface = build_runtime_lifecycle_arguments(
        {"agent_ref": "agent-current", "build_id": str(stale.id)},
        OperationSource.SURFACE,
    )
    assert surface.build_id == stale.id
    with pytest.raises(ValueError, match="selected build"):
        build_runtime_lifecycle_arguments(
            {"agent_ref": "agent-current"},
            OperationSource.SURFACE,
        )

    class CurrentInputs:
        async def current_build_request_id(self, organization_id, agent_id):
            assert (organization_id, agent_id) == (
                current.organization_id,
                current.agent_id,
            )
            return current.build_request_id

    class CurrentRepository(BuilderRepo):
        async def get_for_agent(self, *_):
            return (current, failed_prior_attempt, stale)

    service = BuilderService(
        CurrentRepository(current),
        CurrentInputs(),
        BuildRuntime(),
        Agents(),
    )

    assert await service.current_build_id(
        current.organization_id,
        current.agent_id,
    ) == current.id


class BuildRuntime:
    async def assemble(self, snapshot):
        return RuntimeBuildArtifact(
            "a" * 64, "gemma4", "d" * 64,
            tuple(op for item in snapshot.source_bindings for op in item.included_operation_ids),
            "n" * 64, {"nodes": []}, {"nodes": {}},
        )
    async def validate_immutable_build(self, runtime_build_hash):
        assert runtime_build_hash == "a" * 64


class InitialEvaluations:
    def __init__(self): self.scheduled = None
    async def schedule_initial_set(self, organization_id, agent_id, *, build_id):
        self.scheduled = (organization_id, agent_id, build_id)


class Jobs:
    def __init__(self): self.enqueued = None
    async def enqueue(self, **values):
        self.enqueued = values
        now = datetime.now(UTC)
        return DurableJobRecord(
            uuid.uuid4(), values["owner_id"], values["job_type"],
            DurableJobState.QUEUED, values["payload"], 0, values["max_attempts"],
            None, None, None, now, now, None, None,
        )


@pytest.mark.asyncio
async def test_builder_request_queues_exact_attempt_without_inline_assembly():
    pending = build_record(status="queued")
    repository = BuilderRepo(pending)
    runtime = BuildRuntime()
    service = BuilderService(repository, Inputs(None), runtime, Agents())
    jobs = Jobs()
    service.bind_assembly_jobs(jobs)

    result = await service.assemble(
        pending.organization_id,
        pending.agent_id,
        build_request_id=pending.build_request_id,
    )

    assert result.status == "queued"
    assert result.job_id is not None
    assert jobs.enqueued == {
        "owner_id": pending.organization_id,
        "job_type": "builder.assemble",
        "payload": {
            "agent_id": str(pending.agent_id),
            "build_id": str(pending.id),
            "build_request_id": str(pending.build_request_id),
            "design_revision_id": str(pending.design_revision_id),
            "attempt_number": pending.attempt_number,
        },
        "max_attempts": 1,
    }


@pytest.mark.asyncio
async def test_builder_persists_exact_runtime_binding_and_historical_lineage(tmp_path: Path):
    pending = build_record(status="running")
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
        ("Catalog lookup",), ("GetProductTypes",),
        ({"title": "Catalog", "capability_titles": ("Catalog lookup",)},),
        (binding,),
    )
    agents, repository = Agents(), BuilderRepo(pending)
    service = BuilderService(repository, Inputs(snapshot), BuildRuntime(), agents)
    initial_evaluations = InitialEvaluations()
    service.bind_initial_evaluation_scheduler(initial_evaluations)

    result = await service.execute_assembly(
        pending.organization_id,
        pending.agent_id,
        build_id=pending.id,
        expected_build_request_id=pending.build_request_id,
        expected_design_revision_id=pending.design_revision_id,
        expected_attempt_number=pending.attempt_number,
    )

    assert result.status == "ready"
    assert result.runtime_lifecycle == "stopped"
    assert result.runtime_build_hash == "a" * 64
    assert result.source_bindings[0].profile_id == "profile-00000001"
    assert result.source_bindings[0].credential_version == 2
    assert agents.lineage[2]["source_references"] == (("source-000000001", "revision-0000001"),)
    assert initial_evaluations.scheduled == (
        pending.organization_id, pending.agent_id, pending.id
    )


class ReadyBuilds:
    def __init__(self, value): self.value = value
    async def require_running(self, *_): return self.value
    async def list(self, *_): return object()


@pytest.mark.asyncio
async def test_builder_runtime_lifecycle_is_explicit_and_removal_preserves_build_lineage(tmp_path: Path):
    ready = build_record(
        status="ready", runtime_hash="a" * 64,
        bindings=({
            "source_id": "source-000000001",
            "source_revision_id": "revision-0000001",
            "curation_id": "curation-0000001",
            "inventory_fingerprint": "f" * 64,
            "included_operation_ids": ["GetProductTypes"],
            "profile_id": "profile-00000001",
            "credential_reference_id": None,
            "credential_version": None,
        },),
    )
    repository = BuilderRepo(ready)
    service = BuilderService(repository, Inputs(None), BuildRuntime(), Agents())

    paused = await service.pause(
        ready.organization_id, ready.agent_id, build_id=ready.id
    )
    assert paused.runtime_lifecycle == "paused"
    with pytest.raises(BuilderConflict, match="stopped"):
        await service.remove_runtime(
            ready.organization_id, ready.agent_id, build_id=ready.id
        )
    running = await service.run(
        ready.organization_id, ready.agent_id, build_id=ready.id
    )
    assert running.runtime_lifecycle == "running"
    stopped = await service.stop(
        ready.organization_id, ready.agent_id, build_id=ready.id
    )
    assert stopped.runtime_lifecycle == "stopped"
    restarted = await service.run(
        ready.organization_id, ready.agent_id, build_id=ready.id
    )
    assert restarted.runtime_lifecycle == "running"
    await service.stop(ready.organization_id, ready.agent_id, build_id=ready.id)
    removed = await service.remove_runtime(
        ready.organization_id, ready.agent_id, build_id=ready.id
    )

    assert removed.runtime_lifecycle == "removed"
    assert removed.runtime_build_hash == ready.runtime_build_hash
    assert removed.source_bindings[0].source_id == "source-000000001"
    assert removed.source_bindings[0].source_revision_id == "revision-0000001"
    with pytest.raises(Exception, match="removed"):
        await service.run(
            ready.organization_id, ready.agent_id, build_id=ready.id
        )


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


@pytest.mark.asyncio
async def test_sandbox_failure_exposes_only_the_retained_run_identity():
    ready = build_record(
        status="ready", runtime_hash="a" * 64,
        bindings=({"source_id": "source-000000001"},),
    )
    repository = SandboxRepo(ready)

    async def fail(_owner, _record_id, *, code):
        assert code == "RuntimeError"
        repository.value = SandboxRecord(
            repository.value.id, repository.value.organization_id,
            repository.value.agent_id, repository.value.build_id,
            repository.value.runtime_build_hash, repository.value.runtime_session_id,
            repository.value.runtime_run_id, "failed", None, None, 0, (), {},
            code, repository.value.created_at, datetime.now(UTC),
            repository.value.message,
        )
        return repository.value

    repository.fail = fail

    class FailingRuntime:
        async def start(self, **_values):
            raise RuntimeError("private provider detail")

    service = SandboxService(repository, FailingRuntime(), ReadyBuilds(ready))

    with pytest.raises(SandboxRunFailed) as captured:
        await service.start(
            ready.organization_id, ready.agent_id,
            build_id=ready.id, message="List product types",
        )

    assert captured.value.run_id == repository.value.id
    assert str(captured.value) == "The Sandbox run failed."
    assert repository.value.status == "failed"


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
