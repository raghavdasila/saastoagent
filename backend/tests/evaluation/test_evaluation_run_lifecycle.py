from __future__ import annotations

import asyncio
import uuid
from dataclasses import replace
from datetime import UTC, datetime
from types import SimpleNamespace

import pytest

from corpus.auth.models import Organization
from corpus.features.agents.domain import AgentLifecycle
from corpus.features.agents.models import Agent
from corpus.features.builder.models import AgentRunnableBuild
from corpus.features.designer.models import (
    AgentBuildRequest,
    AgentDesign,
    AgentDesignRevision,
)
from corpus.features.evaluation.domain import (
    EvaluationCaseRecord,
    EvaluationRunAttemptRecord,
    EvaluationRunRecord,
    EvaluationSetRecord,
)
from corpus.features.evaluation.execution import EvaluationRunProcessor
from corpus.features.evaluation.models import AgentEvaluationCase, AgentEvaluationSet
from corpus.features.evaluation.ports import EvaluationConflict
from corpus.features.evaluation.repository import SqlAlchemyEvaluationRepository
from corpus.features.evaluation.service import EvaluationService
from corpus.jobs import DurableJobRecord, DurableJobState
from corpus.persistence import CorpusDatabase


def now() -> datetime:
    return datetime.now(UTC)


class Builds:
    def __init__(self, build_id: uuid.UUID) -> None:
        self.build = SimpleNamespace(
            id=build_id,
            runtime_build_hash="b" * 64,
            allowed_operation_ids=("GetProductTypes",),
        )

    async def require_running(self, _owner, _agent, build_id):
        assert build_id == self.build.id
        return self.build


class QueueRepository:
    def __init__(self, owner, agent, build_id) -> None:
        timestamp = now()
        self.evaluation_set = EvaluationSetRecord(
            uuid.uuid4(), owner, agent, build_id, "Baseline",
            None, "manual", None, None, None, timestamp, timestamp,
        )
        self.case = EvaluationCaseRecord(
            uuid.uuid4(), owner, self.evaluation_set.id, build_id,
            "runtime-case", None, "sandbox", "sandbox-run",
            "Store taxonomy", "List product types", "routing", "easy",
            ("GetProductTypes",), (), False, True, 1, None, timestamp,
        )
        self.attempts: list[EvaluationRunAttemptRecord] = []

    async def get_case(self, owner, agent, case_id):
        assert (owner, agent, case_id) == (
            self.case.organization_id,
            self.evaluation_set.agent_id,
            self.case.id,
        )
        return self.evaluation_set, self.case

    async def create_run_attempt(
        self, owner, agent, case_id, *, retry_of_attempt_id=None,
    ):
        if any(value.status in {"queued", "running"} for value in self.attempts):
            raise EvaluationConflict("That evaluation case already has an active run.")
        if retry_of_attempt_id is not None:
            retry = next(value for value in self.attempts if value.id == retry_of_attempt_id)
            assert retry.status == "failed"
        timestamp = now()
        value = EvaluationRunAttemptRecord(
            uuid.uuid4(), owner, agent, self.evaluation_set.id, case_id,
            self.case.build_id, self.case.current_revision, None,
            retry_of_attempt_id, "queued", None, None, None,
            timestamp, timestamp, None,
        )
        self.attempts.append(value)
        return value

    async def link_run_attempt_job(self, owner, attempt_id, job_id):
        index = next(i for i, value in enumerate(self.attempts) if value.id == attempt_id)
        self.attempts[index] = replace(self.attempts[index], job_id=job_id)
        return self.attempts[index]

    async def get_run_attempt(self, owner, agent, attempt_id):
        attempt = next(value for value in self.attempts if value.id == attempt_id)
        assert (owner, agent) == (attempt.organization_id, attempt.agent_id)
        return self.evaluation_set, self.case, attempt

    async def list_sets(self, owner, agent):
        return (self.evaluation_set,)

    async def cases(self, owner, evaluation_set_id):
        return (self.case,)

    async def runs(self, owner, evaluation_set_id):
        return ()

    async def run_attempts(self, owner, evaluation_set_id):
        return tuple(self.attempts)

    async def latest_eligibility(self, owner, agent, build_id):
        return None


class Jobs:
    def __init__(self, owner) -> None:
        self.owner = owner
        self.enqueued: list[DurableJobRecord] = []

    async def enqueue(self, *, owner_id, job_type, payload, max_attempts=1):
        assert owner_id == self.owner
        value = DurableJobRecord(
            uuid.uuid4(), owner_id, job_type, DurableJobState.QUEUED,
            dict(payload), 0, max_attempts, None, None, None,
            now(), now(), None, None,
        )
        self.enqueued.append(value)
        return value


@pytest.mark.asyncio
async def test_run_operation_queues_without_calling_runtime_and_retry_appends_attempt():
    owner, agent, build_id = uuid.uuid4(), uuid.uuid4(), uuid.uuid4()
    repository = QueueRepository(owner, agent, build_id)
    jobs = Jobs(owner)
    service = EvaluationService(
        repository,
        SimpleNamespace(),
        Builds(build_id),
        SimpleNamespace(),
        run_jobs=jobs,
    )

    queued = await service.queue_case(owner, agent, repository.case.id)

    attempt = repository.attempts[-1]
    assert attempt.status == "queued"
    assert attempt.job_id == jobs.enqueued[-1].id
    assert jobs.enqueued[-1].job_type == "evaluation.run_case"
    assert jobs.enqueued[-1].max_attempts == 1
    assert queued.evaluation_sets[0].cases[0].latest_run_attempt.status == "queued"

    repository.attempts[-1] = replace(
        attempt, status="failed", failure_code="evaluation_run_failed",
        failure_message="The queued evaluation run failed.", completed_at=now(),
    )
    retried = await service.retry_case_run(owner, agent, attempt.id)

    assert len(repository.attempts) == 2
    assert repository.attempts[-1].retry_of_attempt_id == attempt.id
    assert len(jobs.enqueued) == 2
    assert retried.evaluation_sets[0].cases[0].latest_run_attempt.status == "queued"


class JobRepository:
    def __init__(self, job: DurableJobRecord) -> None:
        self.job = job
        self.succeeded = None
        self.failed = None

    async def mark_running(self, *, job_id):
        assert job_id == self.job.id
        return replace(self.job, state=DurableJobState.RUNNING)

    async def mark_succeeded(self, *, job_id, result):
        self.succeeded = (job_id, result)

    async def mark_failed(self, *, job_id, error_code, error_message):
        self.failed = (job_id, error_code, error_message)


class ProcessorRepository(QueueRepository):
    async def mark_run_attempt_running(self, owner, attempt_id, job_id):
        index = next(i for i, value in enumerate(self.attempts) if value.id == attempt_id)
        self.attempts[index] = replace(
            self.attempts[index], status="running", job_id=job_id, updated_at=now()
        )
        return self.attempts[index]

    async def mark_run_attempt_succeeded(self, owner, attempt_id, runtime_id):
        index = next(i for i, value in enumerate(self.attempts) if value.id == attempt_id)
        self.attempts[index] = replace(
            self.attempts[index], status="succeeded",
            runtime_evaluation_run_id=runtime_id, updated_at=now(), completed_at=now(),
        )
        return self.attempts[index]

    async def mark_run_attempt_failed(self, owner, attempt_id, *, code, message):
        index = next(i for i, value in enumerate(self.attempts) if value.id == attempt_id)
        self.attempts[index] = replace(
            self.attempts[index], status="failed", failure_code=code,
            failure_message=message, updated_at=now(), completed_at=now(),
        )
        return self.attempts[index]


@pytest.mark.asyncio
async def test_worker_marks_exact_attempt_terminal_and_never_retries():
    owner, agent, build_id = uuid.uuid4(), uuid.uuid4(), uuid.uuid4()
    repository = ProcessorRepository(owner, agent, build_id)
    attempt = await repository.create_run_attempt(owner, agent, repository.case.id)
    job = DurableJobRecord(
        uuid.uuid4(), owner, "evaluation.run_case", DurableJobState.QUEUED,
        {
            "agent_id": str(agent), "case_id": str(repository.case.id),
            "case_revision": 1, "attempt_id": str(attempt.id),
        },
        0, 1, None, None, None, now(), now(), None, None,
    )
    await repository.link_run_attempt_job(owner, attempt.id, job.id)
    jobs = JobRepository(job)

    class Service:
        async def execute_case(self, owner_id, agent_id, case_id, *, expected_case_revision):
            assert (owner_id, agent_id, case_id, expected_case_revision) == (
                owner, agent, repository.case.id, 1,
            )
            return EvaluationRunRecord(
                uuid.uuid4(), owner, case_id, build_id, "runtime-eval-1",
                "passed", True, True, 1, (), now(),
            )

    result = await EvaluationRunProcessor(jobs, repository, Service()).process(job.id)

    assert result["runtime_evaluation_run_id"] == "runtime-eval-1"
    assert repository.attempts[-1].status == "succeeded"
    assert jobs.succeeded is not None
    assert jobs.failed is None


@pytest.mark.asyncio
async def test_sql_repository_allows_one_active_attempt_and_preserves_retry_lineage(
    tmp_path,
):
    database = CorpusDatabase(
        f"sqlite+aiosqlite:///{(tmp_path / 'evaluation-runs.sqlite3').as_posix()}"
    )
    await database.create_schema_for_tests()
    owner_id, agent_id = uuid.uuid4(), uuid.uuid4()
    design_id, design_revision_id = uuid.uuid4(), uuid.uuid4()
    build_request_id, build_id = uuid.uuid4(), uuid.uuid4()
    evaluation_set_id, case_id = uuid.uuid4(), uuid.uuid4()
    timestamp = now()
    async with database.session() as session:
        async with session.begin():
            session.add(Organization(
                id=owner_id, name="Owner",
                slug=f"owner-{owner_id.hex}", created_at=timestamp,
            ))
            await session.flush()
            session.add(Agent(
                id=agent_id, organization_id=owner_id,
                name="Evaluation Agent", name_key="evaluation agent",
                lifecycle=AgentLifecycle.ACTIVE, current_version=1,
                created_at=timestamp, updated_at=timestamp,
            ))
            await session.flush()
            session.add(AgentDesign(
                id=design_id, organization_id=owner_id, agent_id=agent_id,
                current_revision_id=design_revision_id, current_revision=1,
                accepted_revision_id=design_revision_id,
                created_at=timestamp, updated_at=timestamp,
            ))
            await session.flush()
            session.add(AgentDesignRevision(
                id=design_revision_id, design_id=design_id, revision=1,
                agent_version=1, input_fingerprint="d" * 64,
                content={}, source_inputs=[], created_at=timestamp,
            ))
            await session.flush()
            session.add(AgentBuildRequest(
                id=build_request_id, organization_id=owner_id,
                agent_id=agent_id, design_revision_id=design_revision_id,
                status="assembled", created_at=timestamp,
            ))
            await session.flush()
            session.add(AgentRunnableBuild(
                id=build_id, organization_id=owner_id, agent_id=agent_id,
                build_request_id=build_request_id,
                design_revision_id=design_revision_id, agent_version=1,
                attempt_number=1, status="ready", runtime_lifecycle="running",
                runtime_build_hash="b" * 64, model="model",
                model_digest="digest", source_bindings=[],
                allowed_operation_ids=["GetProductTypes"],
                navgraph_hash="n" * 64, compiled_navgraph={},
                frontend_contract={}, failure_code=None, failure_message=None,
                created_at=timestamp, updated_at=timestamp,
            ))
            await session.flush()
            session.add(AgentEvaluationSet(
                id=evaluation_set_id, organization_id=owner_id,
                agent_id=agent_id, build_id=build_id, name="Baseline",
                generation_job_id=None, generation_status="manual",
                generation_failure_code=None, generation_failure_message=None,
                generation_summary=None, created_at=timestamp,
                updated_at=timestamp,
            ))
            await session.flush()
            session.add(AgentEvaluationCase(
                id=case_id, organization_id=owner_id,
                evaluation_set_id=evaluation_set_id, build_id=build_id,
                runtime_case_id="runtime-case-sql", generation_task_id=None,
                source_kind="sandbox", source_record_id="sandbox-run-sql",
                title="Store taxonomy", message="List product types",
                category="routing", difficulty="easy",
                expected_operation_ids=["GetProductTypes"],
                required_response_fields=[], require_write_verification=False,
                mandatory=True, current_revision=1, removed_at=None,
                created_at=timestamp,
            ))

    repository = SqlAlchemyEvaluationRepository(database)
    try:
        results = await asyncio.gather(
            repository.create_run_attempt(owner_id, agent_id, case_id),
            repository.create_run_attempt(owner_id, agent_id, case_id),
            return_exceptions=True,
        )
        attempts = [result for result in results if not isinstance(result, Exception)]
        conflicts = [result for result in results if isinstance(result, EvaluationConflict)]
        assert len(attempts) == 1
        assert len(conflicts) == 1

        failed = await repository.mark_run_attempt_failed(
            owner_id, attempts[0].id,
            code="evaluation_run_failed", message="The evaluation run failed.",
        )
        retry = await repository.create_run_attempt(
            owner_id, agent_id, case_id, retry_of_attempt_id=failed.id,
        )
        history = await repository.run_attempts(owner_id, evaluation_set_id)

        assert failed.status == "failed"
        assert retry.status == "queued"
        assert retry.retry_of_attempt_id == failed.id
        assert [item.status for item in history] == ["failed", "queued"]
    finally:
        await database.close()
