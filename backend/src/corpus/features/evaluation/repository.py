from __future__ import annotations

import uuid
from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError

from corpus.persistence import CorpusDatabase

from .domain import (
    EvaluationCaseRecord,
    EvaluationRunAttemptRecord,
    EvaluationRunRecord,
    EvaluationSetRecord,
    EligibilityRecord,
)
from .models import (
    AgentEvaluationCase,
    AgentEvaluationCaseRevision,
    AgentEvaluationEligibility,
    AgentEvaluationRun,
    AgentEvaluationRunAttempt,
    AgentEvaluationSet,
)
from .ports import EvaluationConflict, EvaluationUnavailable


def utc_now():
    return datetime.now(UTC)


class SqlAlchemyEvaluationRepository:
    def __init__(self, database: CorpusDatabase) -> None:
        self.database = database

    async def create_set(self, organization_id, agent_id, build_id, name):
        now = utc_now()
        async with self.database.session() as session:
            existing = await session.scalar(select(AgentEvaluationSet).where(
                AgentEvaluationSet.organization_id == organization_id,
                AgentEvaluationSet.agent_id == agent_id,
                AgentEvaluationSet.build_id == build_id,
                AgentEvaluationSet.name == name.strip(),
            ))
            if existing is not None:
                return _set(existing)
            value = AgentEvaluationSet(
                id=uuid.uuid4(), organization_id=organization_id,
                agent_id=agent_id, build_id=build_id, name=name.strip(),
                generation_status="manual", generation_job_id=None,
                generation_failure_code=None, generation_failure_message=None,
                generation_summary=None, created_at=now, updated_at=now,
            )
            session.add(value)
            try:
                await session.commit()
            except IntegrityError as error:
                raise EvaluationConflict("That evaluation set already exists for this build.") from error
            return _set(value)

    async def get_set(self, organization_id, agent_id, evaluation_set_id):
        async with self.database.session() as session:
            value = await session.scalar(select(AgentEvaluationSet).where(
                AgentEvaluationSet.id == evaluation_set_id,
                AgentEvaluationSet.organization_id == organization_id,
                AgentEvaluationSet.agent_id == agent_id,
            ))
            if value is None:
                raise EvaluationUnavailable("The selected evaluation set is unavailable.")
            return _set(value)

    async def list_sets(self, organization_id, agent_id):
        async with self.database.session() as session:
            values = (await session.scalars(select(AgentEvaluationSet).where(
                AgentEvaluationSet.organization_id == organization_id,
                AgentEvaluationSet.agent_id == agent_id,
            ).order_by(AgentEvaluationSet.created_at.desc()))).all()
            return tuple(_set(value) for value in values)

    async def add_case(self, organization_id, evaluation_set, **values):
        runtime = values.pop("runtime")
        value = AgentEvaluationCase(
            id=uuid.uuid4(), organization_id=organization_id,
            evaluation_set_id=evaluation_set.id, build_id=evaluation_set.build_id,
            runtime_case_id=runtime.case_id, generation_task_id=None,
            current_revision=1, removed_at=None, created_at=utc_now(),
            expected_operation_ids=list(values.pop("expected_operation_ids")),
            required_response_fields=list(values.pop("required_response_fields")),
            **values,
        )
        async with self.database.session() as session:
            session.add(value)
            try:
                await session.commit()
            except IntegrityError as error:
                raise EvaluationConflict("This interaction is already an evaluation case.") from error
            return _case(value)

    async def add_generated_case(self, organization_id, evaluation_set, **values):
        task_id = str(values.pop("task_id")).strip()
        if not task_id:
            raise EvaluationConflict("Generated evaluation task identity is required.")
        async with self.database.session() as session:
            async with session.begin():
                existing = await session.scalar(select(AgentEvaluationCase).where(
                    AgentEvaluationCase.organization_id == organization_id,
                    AgentEvaluationCase.evaluation_set_id == evaluation_set.id,
                    AgentEvaluationCase.source_kind == "toolrouter",
                    AgentEvaluationCase.generation_task_id == task_id,
                ))
                if existing is not None:
                    return _case(existing)
                value = AgentEvaluationCase(
                    id=uuid.uuid4(), organization_id=organization_id,
                    evaluation_set_id=evaluation_set.id,
                    build_id=evaluation_set.build_id, runtime_case_id=None,
                    generation_task_id=task_id, source_kind="toolrouter",
                    source_record_id=task_id, required_response_fields=[],
                    require_write_verification=False,
                    expected_operation_ids=list(values.pop("expected_operation_ids")),
                    current_revision=1, removed_at=None, created_at=utc_now(),
                    **values,
                )
                session.add(value)
                await session.flush()
                return _case(value)

    async def set_generation_job(self, organization_id, evaluation_set_id, job_id):
        async with self.database.session() as session:
            async with session.begin():
                value = await session.scalar(select(AgentEvaluationSet).where(
                    AgentEvaluationSet.id == evaluation_set_id,
                    AgentEvaluationSet.organization_id == organization_id,
                ).with_for_update())
                if value is None:
                    raise EvaluationUnavailable("The evaluation set is unavailable.")
                value.generation_job_id = job_id
                if value.generation_status in {"manual", "failed"}:
                    value.generation_status = "queued"
                    value.generation_failure_code = None
                    value.generation_failure_message = None
                    value.generation_summary = None
                value.updated_at = utc_now()
                await session.flush()
                return _set(value)

    async def mark_generation_running(self, organization_id, evaluation_set_id):
        return await self._update_generation(
            organization_id, evaluation_set_id, status="running"
        )

    async def mark_generation_ready(self, organization_id, evaluation_set_id, summary):
        return await self._update_generation(
            organization_id, evaluation_set_id, status="ready", summary=summary,
        )

    async def mark_generation_failed(self, organization_id, evaluation_set_id, *, code, message):
        return await self._update_generation(
            organization_id, evaluation_set_id, status="failed",
            failure_code=code, failure_message=message,
        )

    async def _update_generation(
        self, organization_id, evaluation_set_id, *, status, job_id=None,
        summary=None, failure_code=None, failure_message=None,
    ):
        async with self.database.session() as session:
            async with session.begin():
                value = await session.scalar(select(AgentEvaluationSet).where(
                    AgentEvaluationSet.id == evaluation_set_id,
                    AgentEvaluationSet.organization_id == organization_id,
                ).with_for_update())
                if value is None:
                    raise EvaluationUnavailable("The evaluation set is unavailable.")
                value.generation_status = status
                if job_id is not None:
                    value.generation_job_id = job_id
                value.generation_summary = summary
                value.generation_failure_code = failure_code
                value.generation_failure_message = failure_message
                value.updated_at = utc_now()
                await session.flush()
                return _set(value)

    async def edit_case(
        self, organization_id, agent_id, case_id, *, expected_revision,
        title, category, difficulty, mandatory,
    ):
        async with self.database.session() as session:
            async with session.begin():
                row = (await session.execute(select(
                    AgentEvaluationSet, AgentEvaluationCase
                ).join(
                    AgentEvaluationCase,
                    AgentEvaluationCase.evaluation_set_id == AgentEvaluationSet.id,
                ).where(
                    AgentEvaluationCase.id == case_id,
                    AgentEvaluationCase.organization_id == organization_id,
                    AgentEvaluationSet.agent_id == agent_id,
                ).with_for_update())).first()
                if row is None:
                    raise EvaluationUnavailable("The selected evaluation case is unavailable.")
                case = row[1]
                _require_editable_revision(case, expected_revision)
                await _snapshot_revision(session, case)
                case.title = title.strip()
                case.category = category.strip()
                case.difficulty = difficulty
                case.mandatory = mandatory
                case.current_revision += 1
                await session.flush()
                return _case(case)

    async def remove_case(
        self, organization_id, agent_id, case_id, *, expected_revision,
    ):
        async with self.database.session() as session:
            async with session.begin():
                row = (await session.execute(select(
                    AgentEvaluationSet, AgentEvaluationCase
                ).join(
                    AgentEvaluationCase,
                    AgentEvaluationCase.evaluation_set_id == AgentEvaluationSet.id,
                ).where(
                    AgentEvaluationCase.id == case_id,
                    AgentEvaluationCase.organization_id == organization_id,
                    AgentEvaluationSet.agent_id == agent_id,
                ).with_for_update())).first()
                if row is None:
                    raise EvaluationUnavailable("The selected evaluation case is unavailable.")
                case = row[1]
                _require_editable_revision(case, expected_revision)
                await _snapshot_revision(session, case)
                case.removed_at = utc_now()
                await session.flush()
                return _case(case)

    async def link_generated_run(
        self, organization_id, case_id, sandbox_run_id,
    ):
        async with self.database.session() as session:
            async with session.begin():
                case = await session.scalar(select(AgentEvaluationCase).where(
                    AgentEvaluationCase.id == case_id,
                    AgentEvaluationCase.organization_id == organization_id,
                ).with_for_update())
                if case is None or case.source_kind != "toolrouter":
                    raise EvaluationUnavailable("The generated evaluation case is unavailable.")
                if case.removed_at is not None or case.runtime_case_id is not None:
                    raise EvaluationConflict("The generated evaluation case is no longer waiting for a run.")
                if case.generation_task_id is None:
                    raise EvaluationConflict("The generated evaluation case has no ToolRouter task identity.")
                if case.source_record_id not in {
                    case.generation_task_id, str(sandbox_run_id)
                }:
                    raise EvaluationConflict("The generated evaluation case is already bound to another run.")
                case.source_record_id = str(sandbox_run_id)
                await session.flush()
                return _case(case)

    async def bind_generated_runtime(
        self, organization_id, case_id, runtime,
    ):
        async with self.database.session() as session:
            async with session.begin():
                case = await session.scalar(select(AgentEvaluationCase).where(
                    AgentEvaluationCase.id == case_id,
                    AgentEvaluationCase.organization_id == organization_id,
                ).with_for_update())
                if case is None or case.source_kind != "toolrouter":
                    raise EvaluationUnavailable("The generated evaluation case is unavailable.")
                if case.removed_at is not None:
                    raise EvaluationConflict("The generated evaluation case was removed.")
                if case.runtime_case_id is not None and case.runtime_case_id != runtime.case_id:
                    raise EvaluationConflict("The generated evaluation case runtime changed.")
                case.runtime_case_id = runtime.case_id
                await session.flush()
                return _case(case)

    async def get_case(self, organization_id, agent_id, case_id):
        async with self.database.session() as session:
            row = (await session.execute(select(AgentEvaluationSet, AgentEvaluationCase).join(
                AgentEvaluationCase, AgentEvaluationCase.evaluation_set_id == AgentEvaluationSet.id,
            ).where(
                AgentEvaluationCase.id == case_id,
                AgentEvaluationCase.organization_id == organization_id,
                AgentEvaluationSet.agent_id == agent_id,
            ))).first()
            if row is None:
                raise EvaluationUnavailable("The selected evaluation case is unavailable.")
            return _set(row[0]), _case(row[1])

    async def cases(self, organization_id, evaluation_set_id):
        async with self.database.session() as session:
            values = (await session.scalars(select(AgentEvaluationCase).where(
                AgentEvaluationCase.organization_id == organization_id,
                AgentEvaluationCase.evaluation_set_id == evaluation_set_id,
            ).order_by(AgentEvaluationCase.created_at))).all()
            return tuple(_case(value) for value in values)

    async def cases_by_source(
        self, organization_id, *, source_kind, source_record_id,
    ):
        async with self.database.session() as session:
            values = (await session.scalars(select(AgentEvaluationCase).where(
                AgentEvaluationCase.organization_id == organization_id,
                AgentEvaluationCase.source_kind == source_kind,
                AgentEvaluationCase.source_record_id == source_record_id,
            ).order_by(AgentEvaluationCase.created_at))).all()
            return tuple(_case(value) for value in values)

    async def add_run(self, organization_id, case, runtime):
        value = AgentEvaluationRun(
            id=uuid.uuid4(), organization_id=organization_id, case_id=case.id,
            build_id=case.build_id, runtime_evaluation_run_id=runtime.evaluation_run_id,
            status=runtime.status, deterministic_pass=runtime.deterministic_pass,
            review_pass=runtime.review_pass, case_revision=case.current_revision,
            reasons=list(runtime.reasons),
            created_at=utc_now(),
        )
        async with self.database.session() as session:
            session.add(value)
            await session.commit()
            return _run(value)

    async def runs(self, organization_id, evaluation_set_id):
        async with self.database.session() as session:
            values = (await session.scalars(select(AgentEvaluationRun).join(
                AgentEvaluationCase, AgentEvaluationCase.id == AgentEvaluationRun.case_id,
            ).where(
                AgentEvaluationRun.organization_id == organization_id,
                AgentEvaluationCase.evaluation_set_id == evaluation_set_id,
            ).order_by(AgentEvaluationRun.created_at))).all()
            return tuple(_run(value) for value in values)

    async def create_run_attempt(
        self, organization_id, agent_id, case_id, *, retry_of_attempt_id=None,
    ):
        now = utc_now()
        async with self.database.session() as session:
            async with session.begin():
                row = (await session.execute(select(
                    AgentEvaluationSet, AgentEvaluationCase
                ).join(
                    AgentEvaluationCase,
                    AgentEvaluationCase.evaluation_set_id == AgentEvaluationSet.id,
                ).where(
                    AgentEvaluationCase.id == case_id,
                    AgentEvaluationCase.organization_id == organization_id,
                    AgentEvaluationSet.agent_id == agent_id,
                ).with_for_update())).first()
                if row is None:
                    raise EvaluationUnavailable(
                        "The selected evaluation case is unavailable."
                    )
                evaluation_set, case = row
                if case.removed_at is not None:
                    raise EvaluationConflict(
                        "A removed evaluation case cannot be run."
                    )
                if retry_of_attempt_id is not None:
                    retry = await session.scalar(select(
                        AgentEvaluationRunAttempt
                    ).where(
                        AgentEvaluationRunAttempt.id == retry_of_attempt_id,
                        AgentEvaluationRunAttempt.organization_id == organization_id,
                        AgentEvaluationRunAttempt.agent_id == agent_id,
                        AgentEvaluationRunAttempt.case_id == case.id,
                    ).with_for_update())
                    if (
                        retry is None
                        or retry.status != "failed"
                        or retry.case_revision != case.current_revision
                    ):
                        raise EvaluationConflict(
                            "Only the exact failed current evaluation attempt can be retried."
                        )
                value = AgentEvaluationRunAttempt(
                    id=uuid.uuid4(), organization_id=organization_id,
                    agent_id=agent_id, evaluation_set_id=evaluation_set.id,
                    case_id=case.id, build_id=case.build_id,
                    case_revision=case.current_revision, job_id=None,
                    retry_of_attempt_id=retry_of_attempt_id,
                    active_case_id=case.id, status="queued",
                    failure_code=None, failure_message=None,
                    runtime_evaluation_run_id=None,
                    created_at=now, updated_at=now, completed_at=None,
                )
                session.add(value)
                try:
                    await session.flush()
                except IntegrityError as error:
                    raise EvaluationConflict(
                        "That evaluation case already has an active run."
                    ) from error
                return _attempt(value)

    async def link_run_attempt_job(
        self, organization_id, attempt_id, job_id,
    ):
        async with self.database.session() as session:
            async with session.begin():
                value = await session.scalar(select(
                    AgentEvaluationRunAttempt
                ).where(
                    AgentEvaluationRunAttempt.id == attempt_id,
                    AgentEvaluationRunAttempt.organization_id == organization_id,
                ).with_for_update())
                if value is None:
                    raise EvaluationUnavailable(
                        "The evaluation run attempt is unavailable."
                    )
                if value.job_id is not None and value.job_id != job_id:
                    raise EvaluationConflict(
                        "The evaluation run attempt is already linked to another job."
                    )
                value.job_id = job_id
                value.updated_at = utc_now()
                await session.flush()
                return _attempt(value)

    async def get_run_attempt(
        self, organization_id, agent_id, attempt_id,
    ):
        async with self.database.session() as session:
            row = (await session.execute(select(
                AgentEvaluationSet,
                AgentEvaluationCase,
                AgentEvaluationRunAttempt,
            ).join(
                AgentEvaluationCase,
                AgentEvaluationCase.evaluation_set_id == AgentEvaluationSet.id,
            ).join(
                AgentEvaluationRunAttempt,
                AgentEvaluationRunAttempt.case_id == AgentEvaluationCase.id,
            ).where(
                AgentEvaluationRunAttempt.id == attempt_id,
                AgentEvaluationRunAttempt.organization_id == organization_id,
                AgentEvaluationRunAttempt.agent_id == agent_id,
                AgentEvaluationSet.agent_id == agent_id,
            ))).first()
            if row is None:
                raise EvaluationUnavailable(
                    "The evaluation run attempt is unavailable."
                )
            return _set(row[0]), _case(row[1]), _attempt(row[2])

    async def mark_run_attempt_running(
        self, organization_id, attempt_id, job_id,
    ):
        return await self._update_run_attempt(
            organization_id, attempt_id, expected=("queued",),
            status="running", job_id=job_id,
        )

    async def mark_run_attempt_succeeded(
        self, organization_id, attempt_id, runtime_evaluation_run_id,
    ):
        return await self._update_run_attempt(
            organization_id, attempt_id, expected=("running",),
            status="succeeded",
            runtime_evaluation_run_id=runtime_evaluation_run_id,
        )

    async def mark_run_attempt_failed(
        self, organization_id, attempt_id, *, code, message,
    ):
        return await self._update_run_attempt(
            organization_id, attempt_id, expected=("queued", "running"),
            status="failed", failure_code=code,
            failure_message=message[:500],
        )

    async def _update_run_attempt(
        self, organization_id, attempt_id, *, expected, status,
        job_id=None, runtime_evaluation_run_id=None,
        failure_code=None, failure_message=None,
    ):
        async with self.database.session() as session:
            async with session.begin():
                value = await session.scalar(select(
                    AgentEvaluationRunAttempt
                ).where(
                    AgentEvaluationRunAttempt.id == attempt_id,
                    AgentEvaluationRunAttempt.organization_id == organization_id,
                ).with_for_update())
                if value is None:
                    raise EvaluationUnavailable(
                        "The evaluation run attempt is unavailable."
                    )
                if value.status == status:
                    return _attempt(value)
                if value.status not in expected:
                    raise EvaluationConflict(
                        "The evaluation run attempt changed before this update."
                    )
                if job_id is not None:
                    if value.job_id is not None and value.job_id != job_id:
                        raise EvaluationConflict(
                            "The evaluation run attempt job identity changed."
                        )
                    value.job_id = job_id
                value.status = status
                value.failure_code = failure_code
                value.failure_message = failure_message
                value.runtime_evaluation_run_id = runtime_evaluation_run_id
                value.updated_at = utc_now()
                if status in {"succeeded", "failed"}:
                    value.active_case_id = None
                    value.completed_at = value.updated_at
                await session.flush()
                return _attempt(value)

    async def run_attempts(self, organization_id, evaluation_set_id):
        async with self.database.session() as session:
            values = (await session.scalars(select(
                AgentEvaluationRunAttempt
            ).where(
                AgentEvaluationRunAttempt.organization_id == organization_id,
                AgentEvaluationRunAttempt.evaluation_set_id == evaluation_set_id,
            ).order_by(
                AgentEvaluationRunAttempt.created_at,
                AgentEvaluationRunAttempt.id,
            ))).all()
            return tuple(_attempt(value) for value in values)

    async def add_eligibility(self, organization_id, agent_id, build_id, runtime_build_hash, runtime):
        value = AgentEvaluationEligibility(
            id=uuid.uuid4(), organization_id=organization_id, agent_id=agent_id,
            build_id=build_id, runtime_build_hash=runtime_build_hash,
            eligible=runtime.eligible,
            supporting_evaluation_run_ids=list(runtime.supporting_evaluation_run_ids),
            reasons=list(runtime.reasons), created_at=utc_now(),
        )
        async with self.database.session() as session:
            session.add(value)
            await session.commit()
            return _eligibility(value)

    async def latest_eligibility(self, organization_id, agent_id, build_id):
        async with self.database.session() as session:
            value = await session.scalar(select(AgentEvaluationEligibility).where(
                AgentEvaluationEligibility.organization_id == organization_id,
                AgentEvaluationEligibility.agent_id == agent_id,
                AgentEvaluationEligibility.build_id == build_id,
            ).order_by(AgentEvaluationEligibility.created_at.desc()))
            return None if value is None else _eligibility(value)


def _set(value):
    return EvaluationSetRecord(
        value.id, value.organization_id, value.agent_id, value.build_id,
        value.name, value.generation_job_id, value.generation_status,
        value.generation_failure_code, value.generation_failure_message,
        (dict(value.generation_summary) if value.generation_summary else None),
        value.created_at, value.updated_at,
    )


def _case(value):
    return EvaluationCaseRecord(
        value.id, value.organization_id, value.evaluation_set_id, value.build_id,
        value.runtime_case_id, value.generation_task_id, value.source_kind,
        value.source_record_id, value.title,
        value.message, value.category, value.difficulty,
        tuple(value.expected_operation_ids), tuple(value.required_response_fields),
        value.require_write_verification, value.mandatory,
        value.current_revision, value.removed_at, value.created_at,
    )


def _run(value):
    return EvaluationRunRecord(
        value.id, value.organization_id, value.case_id, value.build_id,
        value.runtime_evaluation_run_id, value.status, value.deterministic_pass,
        value.review_pass, value.case_revision, tuple(value.reasons), value.created_at,
    )


def _attempt(value):
    return EvaluationRunAttemptRecord(
        value.id, value.organization_id, value.agent_id,
        value.evaluation_set_id, value.case_id, value.build_id,
        value.case_revision, value.job_id, value.retry_of_attempt_id,
        value.status, value.failure_code, value.failure_message,
        value.runtime_evaluation_run_id, value.created_at,
        value.updated_at, value.completed_at,
    )


def _eligibility(value):
    return EligibilityRecord(
        value.id, value.organization_id, value.agent_id, value.build_id,
        value.runtime_build_hash, value.eligible,
        tuple(value.supporting_evaluation_run_ids), tuple(value.reasons), value.created_at,
    )


__all__ = ["SqlAlchemyEvaluationRepository"]


def _require_editable_revision(case, expected_revision: int) -> None:
    if case.removed_at is not None:
        raise EvaluationConflict("The evaluation case was already removed.")
    if case.current_revision != expected_revision:
        raise EvaluationConflict(
            "The evaluation case changed; reload it before editing or removing it."
        )


async def _snapshot_revision(session, case) -> None:
    existing = await session.scalar(select(AgentEvaluationCaseRevision).where(
        AgentEvaluationCaseRevision.case_id == case.id,
        AgentEvaluationCaseRevision.revision == case.current_revision,
    ))
    if existing is None:
        session.add(AgentEvaluationCaseRevision(
            id=uuid.uuid4(), organization_id=case.organization_id,
            case_id=case.id, revision=case.current_revision,
            title=case.title, category=case.category,
            difficulty=case.difficulty, mandatory=case.mandatory,
            changed_at=utc_now(),
        ))
