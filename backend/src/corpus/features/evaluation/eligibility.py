from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

from .domain import EvaluationCaseRecord, EvaluationRunRecord, EligibilityRecord


@dataclass(frozen=True)
class CurrentEligibility:
    eligible: bool | None
    reasons: tuple[str, ...]


def current_eligibility(
    cases: Iterable[EvaluationCaseRecord],
    runs: Iterable[EvaluationRunRecord],
    stored: EligibilityRecord | None,
) -> CurrentEligibility:
    if stored is None:
        return CurrentEligibility(None, ())
    if not stored.eligible:
        return CurrentEligibility(False, stored.reasons)
    mandatory = tuple(
        case for case in cases if case.mandatory and case.removed_at is None
    )
    if not mandatory:
        return CurrentEligibility(False, ("no_active_mandatory_evaluation_cases",))
    latest_by_case: dict[object, EvaluationRunRecord] = {}
    for run in sorted(runs, key=lambda value: (value.created_at, str(value.id))):
        latest_by_case[run.case_id] = run
    if any(case.id not in latest_by_case for case in mandatory):
        return CurrentEligibility(False, ("mandatory_evaluation_case_pending",))
    latest = tuple(latest_by_case[case.id] for case in mandatory)
    if any(run.case_revision != case.current_revision for case, run in zip(mandatory, latest)):
        return CurrentEligibility(False, ("mandatory_evaluation_case_changed",))
    if any(
        run.status != "passed" or not run.deterministic_pass or not run.review_pass
        for run in latest
    ):
        return CurrentEligibility(False, ("mandatory_evaluation_case_not_passed",))
    supporting = set(stored.supporting_evaluation_run_ids)
    if any(run.runtime_evaluation_run_id not in supporting for run in latest):
        return CurrentEligibility(False, ("eligibility_evidence_stale",))
    return CurrentEligibility(True, stored.reasons)


__all__ = ["CurrentEligibility", "current_eligibility"]
