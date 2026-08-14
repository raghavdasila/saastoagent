from __future__ import annotations

from dataclasses import dataclass

from agent_execution_runtime import EvaluationService
from agent_execution_runtime.ports import ReviewerPort, RuntimeStore

from corpus.shared.agent_execution import (
    EligibilityProjection,
    EvaluationCaseProjection,
    EvaluationCaseSpec,
    EvaluationRunProjection,
)


@dataclass(frozen=True)
class NeutralEvaluationAdapter:
    """Thin Corpus boundary over the neutral runtime evaluation service."""

    store: RuntimeStore
    reviewer: ReviewerPort

    def promote(self, spec: EvaluationCaseSpec) -> EvaluationCaseProjection:
        case = self._service().promote(
            spec.tenant_id,
            spec.run_id,
            message=spec.message,
            expected_operations=spec.expected_operation_ids,
            required_response_fields=spec.required_response_fields,
            require_write_verification=spec.require_write_verification,
        )
        return _case_projection(case)

    def load_case(self, case_id: str) -> EvaluationCaseProjection:
        return _case_projection(self.store.get_case(case_id))

    def evaluate(self, tenant_id: str, case_id: str) -> EvaluationRunProjection:
        result = self._service().evaluate_record(tenant_id, case_id)
        return _run_projection(result)

    def eligibility(
        self,
        build_hash: str,
        mandatory_case_ids: tuple[str, ...],
    ) -> EligibilityProjection:
        result = self._service().eligibility(build_hash, mandatory_case_ids)
        return EligibilityProjection(
            build_hash=result.build_hash,
            eligible=result.eligible,
            supporting_evaluation_run_ids=result.supporting_eval_run_ids,
            reasons=result.reasons,
        )

    def _service(self) -> EvaluationService:
        return EvaluationService(self.store, self.reviewer)


def _case_projection(value: object) -> EvaluationCaseProjection:
    return EvaluationCaseProjection(
        case_id=value.case_id,
        build_hash=value.build_hash,
        source_run_id=value.source_run_id,
        expected_operation_ids=value.expected_operations,
        source_evidence_hash=value.source_evidence_hash,
        source_event_count=value.source_event_count,
        mandatory=value.mandatory,
    )


def _run_projection(value: object) -> EvaluationRunProjection:
    return EvaluationRunProjection(
        evaluation_run_id=value.eval_run_id,
        case_id=value.case_id,
        build_hash=value.build_hash,
        status=value.status,
        deterministic_pass=value.deterministic_pass,
        review_pass=value.review_pass,
        reasons=value.reasons,
        created_at=value.created_at,
    )


__all__ = ["NeutralEvaluationAdapter"]
