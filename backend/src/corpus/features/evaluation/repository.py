from __future__ import annotations

import uuid
from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError

from corpus.persistence import CorpusDatabase

from .domain import EvaluationCaseRecord, EvaluationRunRecord, EvaluationSetRecord, EligibilityRecord
from .models import AgentEvaluationCase, AgentEvaluationEligibility, AgentEvaluationRun, AgentEvaluationSet
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
            value = AgentEvaluationSet(id=uuid.uuid4(), organization_id=organization_id, agent_id=agent_id, build_id=build_id, name=name.strip(), created_at=now, updated_at=now)
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
            runtime_case_id=runtime.case_id, created_at=utc_now(),
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

    async def add_run(self, organization_id, case, runtime):
        value = AgentEvaluationRun(
            id=uuid.uuid4(), organization_id=organization_id, case_id=case.id,
            build_id=case.build_id, runtime_evaluation_run_id=runtime.evaluation_run_id,
            status=runtime.status, deterministic_pass=runtime.deterministic_pass,
            review_pass=runtime.review_pass, reasons=list(runtime.reasons),
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
    return EvaluationSetRecord(value.id, value.organization_id, value.agent_id, value.build_id, value.name, value.created_at, value.updated_at)


def _case(value):
    return EvaluationCaseRecord(
        value.id, value.organization_id, value.evaluation_set_id, value.build_id,
        value.runtime_case_id, value.source_kind, value.source_record_id, value.title,
        value.message, value.category, value.difficulty,
        tuple(value.expected_operation_ids), tuple(value.required_response_fields),
        value.require_write_verification, value.mandatory, value.created_at,
    )


def _run(value):
    return EvaluationRunRecord(
        value.id, value.organization_id, value.case_id, value.build_id,
        value.runtime_evaluation_run_id, value.status, value.deterministic_pass,
        value.review_pass, tuple(value.reasons), value.created_at,
    )


def _eligibility(value):
    return EligibilityRecord(
        value.id, value.organization_id, value.agent_id, value.build_id,
        value.runtime_build_hash, value.eligible,
        tuple(value.supporting_evaluation_run_ids), tuple(value.reasons), value.created_at,
    )


__all__ = ["SqlAlchemyEvaluationRepository"]
