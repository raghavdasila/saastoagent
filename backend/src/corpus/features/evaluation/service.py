from __future__ import annotations

import asyncio
import uuid

from corpus.features.builder.service import BuilderService
from corpus.features.sandbox.ports import SandboxRunFailed
from corpus.features.sandbox.service import SandboxService
from corpus.jobs import DurableJobEnqueueError, DurableJobPort
from corpus.jobs.repository import DurableJobNotFound, DurableJobStateConflict
from corpus.integrations.agent_execution import EligibilityProjection

from .eligibility import current_eligibility
from .ports import EvaluationConflict, EvaluationRepository, EvaluationRuntimeGateway, EvaluationUnavailable
from .schemas import (
    EvaluationCaseView,
    EvaluationCollectionView,
    EvaluationRunAttemptView,
    EvaluationSetView,
)


class EvaluationService:
    def __init__(
        self,
        repository: EvaluationRepository,
        runtime: EvaluationRuntimeGateway,
        builds: BuilderService,
        sandbox: SandboxService,
        generation_jobs: DurableJobPort | None = None,
        run_jobs: DurableJobPort | None = None,
    ) -> None:
        self.repository = repository
        self.runtime = runtime
        self.builds = builds
        self.sandbox = sandbox
        self.generation_jobs = generation_jobs
        self.run_jobs = run_jobs

    async def schedule_initial_set(
        self,
        organization_id: uuid.UUID,
        agent_id: uuid.UUID,
        *,
        build_id: uuid.UUID,
    ) -> None:
        current = await self.list(organization_id, agent_id)
        existing = next(
            (
                value
                for value in current.evaluation_sets
                if value.build_id == build_id and value.name == "Generated coverage"
            ),
            None,
        )
        if existing is not None:
            return
        try:
            await self.generate_set(
                organization_id,
                agent_id,
                build_id=build_id,
                set_name="Generated coverage",
                categories=("paraphrase",),
            )
        except EvaluationUnavailable:
            current = await self.list(organization_id, agent_id)
            failed = next(
                (
                    value
                    for value in current.evaluation_sets
                    if value.build_id == build_id
                    and value.name == "Generated coverage"
                    and value.generation_status == "failed"
                ),
                None,
            )
            if failed is None:
                raise

    async def generate_set(
        self,
        organization_id: uuid.UUID,
        agent_id: uuid.UUID,
        *,
        build_id: uuid.UUID | None,
        set_name: str,
        categories: tuple[str, ...],
    ) -> EvaluationCollectionView:
        if self.generation_jobs is None:
            raise EvaluationUnavailable("Evaluation generation is unavailable.")
        build = await self._exact_build(organization_id, agent_id, build_id)
        evaluation_set = await self.repository.create_set(
            organization_id, agent_id, build.id, set_name
        )
        if evaluation_set.generation_status in {"queued", "running", "ready"}:
            raise EvaluationConflict(
                "That exact build evaluation set already has generation history."
            )
        try:
            job = await self.generation_jobs.enqueue(
                owner_id=organization_id,
                job_type="evaluation.generate_build_evalset",
                payload={
                    "evaluation_set_id": str(evaluation_set.id),
                    "agent_id": str(agent_id),
                    "build_id": str(build.id),
                    "categories": list(categories),
                },
                max_attempts=2,
            )
            await self.repository.set_generation_job(
                organization_id, evaluation_set.id, job.id
            )
        except DurableJobEnqueueError as error:
            await self.repository.mark_generation_failed(
                organization_id,
                evaluation_set.id,
                code="queue_unavailable",
                message=str(error),
            )
            raise EvaluationUnavailable(str(error)) from error
        return await self.list(organization_id, agent_id)

    async def retry_generation(
        self,
        organization_id: uuid.UUID,
        agent_id: uuid.UUID,
        evaluation_set_id: uuid.UUID,
    ) -> EvaluationCollectionView:
        if self.generation_jobs is None:
            raise EvaluationUnavailable("Evaluation generation is unavailable.")
        evaluation_set = await self.repository.get_set(
            organization_id, agent_id, evaluation_set_id
        )
        if evaluation_set.generation_status != "failed" or evaluation_set.generation_job_id is None:
            raise EvaluationConflict("Only a failed generated evaluation set can be retried.")
        try:
            job = await self.generation_jobs.retry(
                owner_id=organization_id,
                job_id=evaluation_set.generation_job_id,
            )
            await self.repository.set_generation_job(
                organization_id, evaluation_set.id, job.id
            )
        except (DurableJobNotFound, DurableJobStateConflict, DurableJobEnqueueError) as error:
            raise EvaluationUnavailable("The evaluation generation retry is unavailable.") from error
        return await self.list(organization_id, agent_id)

    async def edit_case(
        self, organization_id: uuid.UUID, agent_id: uuid.UUID, *,
        case_id: uuid.UUID, expected_revision: int, title: str,
        category: str, difficulty: str, mandatory: bool,
    ) -> EvaluationCollectionView:
        evaluation_set, _case = await self.repository.get_case(
            organization_id, agent_id, case_id
        )
        build = await self.builds.require_immutable_built(
            organization_id, agent_id, evaluation_set.build_id
        )
        await self.repository.edit_case(
            organization_id, agent_id, case_id,
            expected_revision=expected_revision, title=title,
            category=category, difficulty=difficulty, mandatory=mandatory,
        )
        await self.repository.add_eligibility(
            organization_id, agent_id, build.id, build.runtime_build_hash,
            EligibilityProjection(
                build.runtime_build_hash, False, (),
                ("evaluation_case_revision_changed",),
            ),
        )
        return await self.list(organization_id, agent_id)

    async def remove_case(
        self, organization_id: uuid.UUID, agent_id: uuid.UUID, *,
        case_id: uuid.UUID, expected_revision: int,
    ) -> EvaluationCollectionView:
        evaluation_set, _case = await self.repository.get_case(
            organization_id, agent_id, case_id
        )
        build = await self.builds.require_immutable_built(
            organization_id, agent_id, evaluation_set.build_id
        )
        await self.repository.remove_case(
            organization_id, agent_id, case_id,
            expected_revision=expected_revision,
        )
        await self.repository.add_eligibility(
            organization_id, agent_id, build.id, build.runtime_build_hash,
            EligibilityProjection(
                build.runtime_build_hash, False, (),
                ("evaluation_case_removed",),
            ),
        )
        return await self.list(organization_id, agent_id)

    async def create_case_from_sandbox(
        self, organization_id: uuid.UUID, agent_id: uuid.UUID, *, build_id: uuid.UUID,
        sandbox_run_id: uuid.UUID, set_name: str, title: str, category: str,
        difficulty: str, mandatory: bool,
    ) -> EvaluationCollectionView:
        build = await self.builds.require_running(organization_id, agent_id, build_id)
        runs = (await self.sandbox.list(organization_id, agent_id)).runs
        sandbox_run = next((value for value in runs if value.id == sandbox_run_id), None)
        if sandbox_run is None or sandbox_run.build_id != build_id:
            raise EvaluationUnavailable("The exact Sandbox interaction is unavailable for this build.")
        if sandbox_run.status != "succeeded":
            raise EvaluationConflict("Only a successful immutable Sandbox interaction can become an evaluation case.")
        expected = _sandbox_operation_evidence(sandbox_run)
        if not expected or not set(expected).issubset(set(build.allowed_operation_ids)):
            raise EvaluationConflict(
                "The successful Sandbox interaction has no valid operation evidence for the exact immutable build."
            )
        evaluation_set = await self.repository.create_set(organization_id, agent_id, build_id, set_name)
        runtime_case = await asyncio.to_thread(
            self.runtime.promote,
            tenant_id=str(organization_id), run_id=sandbox_run.runtime_run_id,
            message=sandbox_run.message, expected_operation_ids=expected,
            required_response_fields=(), require_write_verification=False,
        )
        if runtime_case.build_hash != build.runtime_build_hash:
            raise EvaluationConflict("The promoted interaction did not retain the exact build identity.")
        await self.repository.add_case(
            organization_id, evaluation_set, runtime=runtime_case,
            source_kind="sandbox", source_record_id=str(sandbox_run.id), title=title,
            message=sandbox_run.message, category=category, difficulty=difficulty,
            expected_operation_ids=expected, required_response_fields=(),
            require_write_verification=False, mandatory=mandatory,
        )
        await self._mark_case_added(organization_id, agent_id, build)
        return await self.list(organization_id, agent_id)

    async def create_case_from_current_sandbox(
        self,
        organization_id: uuid.UUID,
        agent_id: uuid.UUID,
        *,
        set_name: str,
        title: str,
        category: str,
        difficulty: str,
        mandatory: bool,
    ) -> EvaluationCollectionView:
        successful = tuple(
            run
            for run in (await self.sandbox.list(organization_id, agent_id)).runs
            if run.status == "succeeded"
        )
        if len(successful) != 1:
            raise EvaluationUnavailable(
                "Evaluation requires one exact successful Sandbox interaction."
            )
        run = successful[0]
        return await self.create_case_from_sandbox(
            organization_id,
            agent_id,
            build_id=run.build_id,
            sandbox_run_id=run.id,
            set_name=set_name,
            title=title,
            category=category,
            difficulty=difficulty,
            mandatory=mandatory,
        )

    async def queue_case(
        self,
        organization_id: uuid.UUID,
        agent_id: uuid.UUID,
        case_id: uuid.UUID,
        *,
        retry_of_attempt_id: uuid.UUID | None = None,
    ) -> EvaluationCollectionView:
        if self.run_jobs is None:
            raise EvaluationUnavailable("Evaluation execution is unavailable.")
        evaluation_set, case = await self.repository.get_case(
            organization_id, agent_id, case_id
        )
        if case.removed_at is not None:
            raise EvaluationConflict("A removed evaluation case cannot be run.")
        await self.builds.require_running(
            organization_id, agent_id, evaluation_set.build_id
        )
        attempt = await self.repository.create_run_attempt(
            organization_id,
            agent_id,
            case.id,
            retry_of_attempt_id=retry_of_attempt_id,
        )
        try:
            job = await self.run_jobs.enqueue(
                owner_id=organization_id,
                job_type="evaluation.run_case",
                payload={
                    "agent_id": str(agent_id),
                    "case_id": str(case.id),
                    "case_revision": case.current_revision,
                    "attempt_id": str(attempt.id),
                },
                max_attempts=1,
            )
            await self.repository.link_run_attempt_job(
                organization_id, attempt.id, job.id
            )
        except DurableJobEnqueueError as error:
            await self.repository.mark_run_attempt_failed(
                organization_id,
                attempt.id,
                code="queue_unavailable",
                message="The evaluation queue rejected this run.",
            )
            raise EvaluationUnavailable(
                "The evaluation run could not be queued."
            ) from error
        return await self.list(organization_id, agent_id)

    async def retry_case_run(
        self,
        organization_id: uuid.UUID,
        agent_id: uuid.UUID,
        attempt_id: uuid.UUID,
    ) -> EvaluationCollectionView:
        _evaluation_set, case, attempt = await self.repository.get_run_attempt(
            organization_id, agent_id, attempt_id
        )
        if attempt.status != "failed":
            raise EvaluationConflict(
                "Only a failed evaluation run can be retried."
            )
        if attempt.case_revision != case.current_revision:
            raise EvaluationConflict(
                "The evaluation case changed; run the current revision instead."
            )
        return await self.queue_case(
            organization_id,
            agent_id,
            case.id,
            retry_of_attempt_id=attempt.id,
        )

    async def queue_current_case(
        self,
        organization_id: uuid.UUID,
        agent_id: uuid.UUID,
        *,
        case_origin: str | None = None,
    ) -> EvaluationCollectionView:
        pending = tuple(
            case
            for evaluation_set in (await self.list(
                organization_id, agent_id
            )).evaluation_sets
            for case in evaluation_set.cases
            if case.latest_status is None
            and not case.removed
            and (
                case_origin is None
                or (case_origin == "generated" and case.source_kind == "toolrouter")
                or (case_origin == "sandbox" and case.source_kind == "sandbox")
                or (case_origin == "operations" and case.source_kind == "operations")
            )
            and (
                case.latest_run_attempt is None
                or case.latest_run_attempt.status == "failed"
            )
        )
        if len(pending) != 1:
            raise EvaluationUnavailable(
                "Run evaluation requires one exact pending evaluation case for the requested origin."
            )
        return await self.queue_case(
            organization_id, agent_id, pending[0].id
        )

    async def run_case(self, organization_id: uuid.UUID, agent_id: uuid.UUID, case_id: uuid.UUID) -> EvaluationCollectionView:
        await self.execute_case(organization_id, agent_id, case_id)
        return await self.list(organization_id, agent_id)

    async def execute_case(
        self,
        organization_id: uuid.UUID,
        agent_id: uuid.UUID,
        case_id: uuid.UUID,
        *,
        expected_case_revision: int | None = None,
    ):
        evaluation_set, case = await self.repository.get_case(organization_id, agent_id, case_id)
        if case.removed_at is not None:
            raise EvaluationConflict("A removed evaluation case cannot be run.")
        if (
            expected_case_revision is not None
            and case.current_revision != expected_case_revision
        ):
            raise EvaluationConflict(
                "The evaluation case changed before its queued run started."
            )
        build = await self.builds.require_running(organization_id, agent_id, evaluation_set.build_id)
        if case.runtime_case_id is None:
            case = await self._materialize_generated_case(
                organization_id, agent_id, case
            )
        if case.runtime_case_id is None:
            raise EvaluationConflict("The generated evaluation case is not runnable yet.")
        result = await asyncio.to_thread(self.runtime.evaluate, str(organization_id), case.runtime_case_id)
        if result.build_hash != build.runtime_build_hash or result.case_id != case.runtime_case_id:
            raise EvaluationConflict("The evaluation result did not retain the exact case and build identity.")
        stored_run = await self.repository.add_run(organization_id, case, result)
        cases, _runs = await self._build_evaluation_state(
            organization_id, agent_id, build.id
        )
        mandatory_cases = tuple(
            value for value in cases if value.mandatory and value.removed_at is None
        )
        if not mandatory_cases:
            eligibility = EligibilityProjection(
                build.runtime_build_hash, False, (),
                ("no_active_mandatory_evaluation_cases",),
            )
        elif any(value.runtime_case_id is None for value in mandatory_cases):
            eligibility = EligibilityProjection(
                build.runtime_build_hash, False, (),
                ("mandatory_evaluation_case_pending",),
            )
        else:
            eligibility = await asyncio.to_thread(
                self.runtime.eligibility,
                build.runtime_build_hash,
                tuple(value.runtime_case_id for value in mandatory_cases),
            )
        await self.repository.add_eligibility(
            organization_id, agent_id, build.id, build.runtime_build_hash, eligibility,
        )
        return stored_run

    async def run_current_case(
        self,
        organization_id: uuid.UUID,
        agent_id: uuid.UUID,
    ) -> EvaluationCollectionView:
        pending = tuple(
            case
            for evaluation_set in (await self.list(organization_id, agent_id)).evaluation_sets
            for case in evaluation_set.cases
            if case.latest_status is None and not case.removed
        )
        if len(pending) != 1:
            raise EvaluationUnavailable(
                "Run evaluation requires one exact pending evaluation case."
            )
        return await self.run_case(organization_id, agent_id, pending[0].id)

    async def create_case_from_operations(
        self, organization_id: uuid.UUID, agent_id: uuid.UUID, *, build_id: uuid.UUID,
        runtime_run_id: str, interaction_id: str, message: str, set_name: str,
        title: str, category: str, difficulty: str,
        expected_operation_ids: tuple[str, ...], mandatory: bool,
    ) -> EvaluationCollectionView:
        build = await self.builds.require_running(organization_id, agent_id, build_id)
        expected = tuple(dict.fromkeys(expected_operation_ids))
        if not expected or not set(expected).issubset(set(build.allowed_operation_ids)):
            raise EvaluationConflict("Operations evidence must use operations from the exact immutable build.")
        evaluation_set = await self.repository.create_set(organization_id, agent_id, build_id, set_name)
        runtime_case = await asyncio.to_thread(
            self.runtime.promote,
            tenant_id=str(organization_id), run_id=runtime_run_id, message=message,
            expected_operation_ids=expected, required_response_fields=(),
            require_write_verification=False,
        )
        if runtime_case.build_hash != build.runtime_build_hash:
            raise EvaluationConflict("The Operations interaction did not retain the exact build identity.")
        await self.repository.add_case(
            organization_id, evaluation_set, runtime=runtime_case,
            source_kind="operations", source_record_id=interaction_id, title=title,
            message=message, category=category, difficulty=difficulty,
            expected_operation_ids=expected, required_response_fields=(),
            require_write_verification=False, mandatory=mandatory,
        )
        await self._mark_case_added(organization_id, agent_id, build)
        return await self.list(organization_id, agent_id)

    async def promoted_operations_case_id(
        self, organization_id: uuid.UUID, interaction_id: str,
    ) -> uuid.UUID | None:
        cases = await self.repository.cases_by_source(
            organization_id,
            source_kind="operations",
            source_record_id=interaction_id,
        )
        if len(cases) > 1:
            raise EvaluationConflict(
                "The Operations interaction has conflicting Evaluation promotion lineage."
            )
        return cases[0].id if cases else None

    async def list(self, organization_id: uuid.UUID, agent_id: uuid.UUID) -> EvaluationCollectionView:
        sets = await self.repository.list_sets(organization_id, agent_id)
        state_by_set = {}
        cases_by_build: dict[uuid.UUID, list[object]] = {}
        runs_by_build: dict[uuid.UUID, list[object]] = {}
        for value in sets:
            cases = await self.repository.cases(organization_id, value.id)
            runs = await self.repository.runs(organization_id, value.id)
            attempts = await self.repository.run_attempts(
                organization_id, value.id
            )
            state_by_set[value.id] = (cases, runs, attempts)
            cases_by_build.setdefault(value.build_id, []).extend(cases)
            runs_by_build.setdefault(value.build_id, []).extend(runs)
        eligibility_by_build = {}
        for build_id in cases_by_build:
            stored = await self.repository.latest_eligibility(
                organization_id, agent_id, build_id
            )
            eligibility_by_build[build_id] = current_eligibility(
                cases_by_build[build_id], runs_by_build[build_id], stored
            )
        views = []
        for value in sets:
            cases, runs, attempts = state_by_set[value.id]
            latest_by_case = {run.case_id: run for run in runs}
            latest_attempt_by_case = {
                attempt.case_id: attempt for attempt in attempts
            }
            eligibility = eligibility_by_build[value.build_id]
            views.append(EvaluationSetView(
                id=value.id, agent_id=value.agent_id, build_id=value.build_id,
                name=value.name, generation_job_id=value.generation_job_id,
                generation_status=value.generation_status,
                generation_failure_code=value.generation_failure_code,
                generation_failure_message=value.generation_failure_message,
                generation_summary=value.generation_summary,
                cases=tuple(EvaluationCaseView(
                    id=case.id, title=case.title, message=case.message,
                    source_kind=case.source_kind, category=case.category,
                    difficulty=case.difficulty, mandatory=case.mandatory,
                    expected_operation_ids=case.expected_operation_ids,
                    current_revision=case.current_revision,
                    removed=case.removed_at is not None,
                    runnable=case.runtime_case_id is not None,
                    latest_status=(latest_by_case[case.id].status if case.id in latest_by_case else None),
                    latest_run_attempt=(
                        EvaluationRunAttemptView(
                            id=latest_attempt_by_case[case.id].id,
                            status=latest_attempt_by_case[case.id].status,
                            failure_code=latest_attempt_by_case[case.id].failure_code,
                            failure_message=latest_attempt_by_case[case.id].failure_message,
                            retry_of_attempt_id=latest_attempt_by_case[case.id].retry_of_attempt_id,
                            created_at=latest_attempt_by_case[case.id].created_at,
                            updated_at=latest_attempt_by_case[case.id].updated_at,
                        )
                        if case.id in latest_attempt_by_case
                        else None
                    ),
                ) for case in cases),
                eligible=eligibility.eligible,
                eligibility_reasons=eligibility.reasons,
                created_at=value.created_at,
            ))
        return EvaluationCollectionView(agent_id=agent_id, evaluation_sets=tuple(views))

    async def _exact_build(
        self, organization_id: uuid.UUID, agent_id: uuid.UUID,
        build_id: uuid.UUID | None,
    ):
        if build_id is not None:
            return await self.builds.require_immutable_built(
                organization_id, agent_id, build_id
            )
        values = tuple(
            value for value in (await self.builds.list(organization_id, agent_id)).builds
            if value.status == "ready" and value.runtime_lifecycle != "removed"
        )
        if len(values) != 1:
            raise EvaluationUnavailable(
                "Evaluation generation requires one exact immutable Agent build."
            )
        return await self.builds.require_immutable_built(
            organization_id, agent_id, values[0].id
        )

    async def _mark_case_added(self, organization_id, agent_id, build) -> None:
        await self.repository.add_eligibility(
            organization_id,
            agent_id,
            build.id,
            build.runtime_build_hash,
            EligibilityProjection(
                build.runtime_build_hash,
                False,
                (),
                ("evaluation_case_added",),
            ),
        )

    async def _build_evaluation_state(
        self, organization_id, agent_id, build_id
    ):
        cases = []
        runs = []
        for evaluation_set in await self.repository.list_sets(
            organization_id, agent_id
        ):
            if evaluation_set.build_id != build_id:
                continue
            cases.extend(
                await self.repository.cases(organization_id, evaluation_set.id)
            )
            runs.extend(
                await self.repository.runs(organization_id, evaluation_set.id)
            )
        return tuple(cases), tuple(runs)

    async def _materialize_generated_case(
        self, organization_id: uuid.UUID, agent_id: uuid.UUID, case,
    ):
        if case.source_kind != "toolrouter" or case.generation_task_id is None:
            raise EvaluationConflict("The evaluation case has no immutable runtime evidence.")
        runs = (await self.sandbox.list(organization_id, agent_id)).runs
        sandbox_run = next(
            (run for run in runs if str(run.id) == case.source_record_id), None
        )
        if sandbox_run is None:
            try:
                sandbox_run = await self.sandbox.start(
                    organization_id, agent_id,
                    build_id=case.build_id, message=case.message,
                )
            except SandboxRunFailed as error:
                await self.repository.link_generated_run(
                    organization_id, case.id, error.run_id
                )
                raise EvaluationConflict(
                    "The generated case retained a failed exact-build Sandbox trial."
                ) from error
            case = await self.repository.link_generated_run(
                organization_id, case.id, sandbox_run.id
            )
        if sandbox_run.status == "waiting":
            raise EvaluationConflict(
                "This generated case is waiting for one natural answer in Sandbox."
            )
        if sandbox_run.status != "succeeded":
            raise EvaluationConflict(
                "The generated case did not produce a successful exact-build trial."
            )
        expected = _sandbox_operation_evidence(sandbox_run)
        if expected != case.expected_operation_ids:
            raise EvaluationConflict(
                "The generated case did not preserve its exact expected operation."
            )
        runtime_case = await asyncio.to_thread(
            self.runtime.promote,
            tenant_id=str(organization_id), run_id=sandbox_run.runtime_run_id,
            message=case.message,
            expected_operation_ids=case.expected_operation_ids,
            required_response_fields=case.required_response_fields,
            require_write_verification=case.require_write_verification,
        )
        build = await self.builds.require_running(
            organization_id, agent_id, case.build_id
        )
        if runtime_case.build_hash != build.runtime_build_hash:
            raise EvaluationConflict(
                "The generated evaluation trial changed its exact build identity."
            )
        return await self.repository.bind_generated_runtime(
            organization_id, case.id, runtime_case
        )


__all__ = ["EvaluationService"]


def _sandbox_operation_evidence(run) -> tuple[str, ...]:
    return tuple(dict.fromkeys(
        operation_id
        for event in run.events
        for operation_id in (event.safe_data.get("operation_id"),)
        if isinstance(operation_id, str) and operation_id
    ))
