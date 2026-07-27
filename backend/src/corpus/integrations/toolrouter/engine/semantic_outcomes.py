from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Protocol


TOOLROUTER_OUTCOMES = (
    "ROUTE",
    "ASK_DISAMBIGUATE",
    "ASK_PARAM",
    "NO_TOOL",
    "ABSTAIN",
)

DOWNSTREAM_ONLY_OUTCOMES = (
    "ASK_POLICY",
    "BLOCK_UNSAFE",
)

CAPABILITY_STATUSES = (
    "covered",
    "not_covered",
    "unknown",
)


@dataclass(frozen=True)
class CapabilityAssessment:
    """Closed-world evidence used to distinguish NO_TOOL from ABSTAIN.

    A negative assessment is valid only when the assessor checked a complete
    catalog and retained evidence describing that check. Retrieval score
    margins are deliberately not part of this contract.
    """

    status: str
    catalog_complete: bool
    evidence: tuple[dict[str, Any], ...] = field(default_factory=tuple)

    def __post_init__(self) -> None:
        if self.status not in CAPABILITY_STATUSES:
            raise ValueError(f"Unsupported capability assessment status: {self.status}")
        if self.status == "not_covered" and not self.catalog_complete:
            raise ValueError("A not_covered assessment requires a complete catalog check.")
        if self.status == "not_covered" and not self.evidence:
            raise ValueError("A not_covered assessment requires retained catalog evidence.")


class CapabilityAssessor(Protocol):
    def assess(self, query: str, *, semantic_index: Any) -> CapabilityAssessment:
        ...


def validate_outcome_payload(
    decision_type: str,
    *,
    reason: str,
    candidate_endpoint_ids: list[str] | tuple[str, ...] = (),
    missing_params: list[str] | tuple[str, ...] = (),
    evidence: dict[str, Any] | None = None,
) -> None:
    """Protect the five-outcome surface from semantically invalid payloads."""

    if decision_type not in TOOLROUTER_OUTCOMES:
        raise ValueError(f"Unsupported ToolRouter outcome: {decision_type}")
    if not str(reason or "").strip():
        raise ValueError(f"{decision_type} requires a decision reason.")

    candidates = tuple(dict.fromkeys(str(value) for value in candidate_endpoint_ids if str(value)))
    missing = tuple(dict.fromkeys(str(value) for value in missing_params if str(value)))
    evidence = evidence or {}

    if decision_type == "ROUTE" and not candidates:
        raise ValueError("ROUTE requires at least one endpoint candidate.")
    if decision_type == "ASK_DISAMBIGUATE" and len(candidates) < 2:
        raise ValueError("ASK_DISAMBIGUATE requires at least two distinct endpoint candidates.")
    if decision_type == "ASK_PARAM" and (not candidates or not missing):
        raise ValueError("ASK_PARAM requires an endpoint candidate and at least one missing parameter.")
    if decision_type == "NO_TOOL":
        if evidence.get("capability_status") != "not_covered" or evidence.get("catalog_complete") is not True:
            raise ValueError("NO_TOOL requires a complete, explicit not_covered capability assessment.")
        catalog_evidence = evidence.get("catalog_evidence")
        if not isinstance(catalog_evidence, (list, tuple)) or not catalog_evidence:
            raise ValueError("NO_TOOL requires retained complete-catalog evidence.")
    if decision_type == "ABSTAIN" and evidence.get("capability_status") == "not_covered":
        raise ValueError("ABSTAIN cannot carry a definitive not_covered capability assessment.")
