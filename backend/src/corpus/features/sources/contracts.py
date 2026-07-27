from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Literal


SourceTraceMode = Literal["bounded", "full"]


@dataclass(frozen=True)
class SourceRankedItem:
    item_id: str
    item_kind: str
    score: float


@dataclass(frozen=True)
class SourceRetrievalStep:
    query: str
    ranked_items: tuple[SourceRankedItem, ...]
    trace: dict[str, Any]


@dataclass(frozen=True)
class SourceRetrievalResult:
    query: str
    decision_type: str
    decision_reason: str
    decomposed: bool
    steps: tuple[SourceRetrievalStep, ...]
    missing_inputs: tuple[str, ...] = ()
    ambiguity: dict[str, Any] | None = None
    decision_evidence: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class SourceEvalsetResult:
    evalset_id: str
    status: Literal["ready", "quarantined", "failed"]
    completed_count: int
    expected_count: int
    accepted_count: int
    quarantined_count: int
    terminal_status_counts: dict[str, int]
    offline_tokens: int
    generator_model: str
    generator_model_digest: str
    reviewer_model: str
    reviewer_model_digest: str
    accepted_tasks: tuple[dict[str, Any], ...]
    summary: dict[str, Any]


__all__ = [
    "SourceEvalsetResult",
    "SourceRankedItem",
    "SourceRetrievalResult",
    "SourceRetrievalStep",
    "SourceTraceMode",
]
