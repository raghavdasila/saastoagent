from __future__ import annotations

import asyncio
import uuid

from corpus.features.builder.service import BuilderService
from corpus.features.sandbox.service import SandboxService

from .ports import EvaluationConflict, EvaluationRepository, EvaluationRuntimeGateway, EvaluationUnavailable
from .schemas import EvaluationCaseView, EvaluationCollectionView, EvaluationSetView


class EvaluationService:
    def __init__(self, repository: EvaluationRepository, runtime: EvaluationRuntimeGateway, builds: BuilderService, sandbox: SandboxService) -> None:
        self.repository, self.runtime, self.builds, self.sandbox = repository, runtime, builds, sandbox

    async def create_case_from_sandbox(
        self, organization_id: uuid.UUID, agent_id: uuid.UUID, *, build_id: uuid.UUID,
        sandbox_run_id: uuid.UUID, set_name: str, title: str, category: str,
        difficulty: str, mandatory: bool,
    ) -> EvaluationCollectionView:
        build = await self.builds.require_ready(organization_id, agent_id, build_id)
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

    async def run_case(self, organization_id: uuid.UUID, agent_id: uuid.UUID, case_id: uuid.UUID) -> EvaluationCollectionView:
        evaluation_set, case = await self.repository.get_case(organization_id, agent_id, case_id)
        build = await self.builds.require_ready(organization_id, agent_id, evaluation_set.build_id)
        result = await asyncio.to_thread(self.runtime.evaluate, str(organization_id), case.runtime_case_id)
        if result.build_hash != build.runtime_build_hash or result.case_id != case.runtime_case_id:
            raise EvaluationConflict("The evaluation result did not retain the exact case and build identity.")
        await self.repository.add_run(organization_id, case, result)
        cases = await self.repository.cases(organization_id, evaluation_set.id)
        mandatory = tuple(value.runtime_case_id for value in cases if value.mandatory)
        eligibility = await asyncio.to_thread(self.runtime.eligibility, build.runtime_build_hash, mandatory)
        await self.repository.add_eligibility(
            organization_id, agent_id, build.id, build.runtime_build_hash, eligibility,
        )
        return await self.list(organization_id, agent_id)

    async def run_current_case(
        self,
        organization_id: uuid.UUID,
        agent_id: uuid.UUID,
    ) -> EvaluationCollectionView:
        pending = tuple(
            case
            for evaluation_set in (await self.list(organization_id, agent_id)).evaluation_sets
            for case in evaluation_set.cases
            if case.latest_status is None
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
        build = await self.builds.require_ready(organization_id, agent_id, build_id)
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
        return await self.list(organization_id, agent_id)

    async def list(self, organization_id: uuid.UUID, agent_id: uuid.UUID) -> EvaluationCollectionView:
        sets = await self.repository.list_sets(organization_id, agent_id)
        views = []
        for value in sets:
            cases = await self.repository.cases(organization_id, value.id)
            runs = await self.repository.runs(organization_id, value.id)
            latest_by_case = {run.case_id: run for run in runs}
            eligibility = await self.repository.latest_eligibility(organization_id, agent_id, value.build_id)
            views.append(EvaluationSetView(
                id=value.id, agent_id=value.agent_id, build_id=value.build_id,
                name=value.name,
                cases=tuple(EvaluationCaseView(
                    id=case.id, title=case.title, category=case.category,
                    difficulty=case.difficulty, mandatory=case.mandatory,
                    expected_operation_ids=case.expected_operation_ids,
                    latest_status=(latest_by_case[case.id].status if case.id in latest_by_case else None),
                ) for case in cases),
                eligible=(eligibility.eligible if eligibility is not None else None),
                eligibility_reasons=(eligibility.reasons if eligibility is not None else ()),
                created_at=value.created_at,
            ))
        return EvaluationCollectionView(agent_id=agent_id, evaluation_sets=tuple(views))


__all__ = ["EvaluationService"]


def _sandbox_operation_evidence(run) -> tuple[str, ...]:
    return tuple(dict.fromkeys(
        operation_id
        for event in run.events
        for operation_id in (event.safe_data.get("operation_id"),)
        if isinstance(operation_id, str) and operation_id
    ))
