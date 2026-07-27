from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Literal, Mapping


TraceMode = Literal["bounded", "full"]


@dataclass(frozen=True)
class IngestRequest:
    source_path: Path
    artifact_dir: Path


@dataclass(frozen=True)
class IngestResult:
    endpoint_count: int
    schema_count: int
    security_scheme_count: int
    repair_count: int
    validation_status: str
    graph_node_count: int
    graph_edge_count: int
    graph_card_count: int
    artifact_dir: Path


@dataclass(frozen=True)
class RetrievalRequest:
    artifact_dir: Path
    query: str
    top_k: int = 5
    provided_params: Mapping[str, Any] | None = None
    trace_mode: TraceMode = "bounded"


@dataclass(frozen=True)
class RankedEndpoint:
    endpoint_id: str
    score: float


@dataclass(frozen=True)
class RetrievalStep:
    query: str
    ranked_endpoints: tuple[RankedEndpoint, ...]
    trace: dict[str, Any]


@dataclass(frozen=True)
class RetrievalResult:
    query: str
    decision_type: str
    decision_reason: str
    decomposed: bool
    steps: tuple[RetrievalStep, ...]
    missing_params: tuple[str, ...] = ()
    ambiguity: dict[str, Any] | None = None
    decision_evidence: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class EvalsetRequest:
    artifact_dir: Path
    evalset_id: str
    categories: tuple[str, ...] = ("paraphrase",)
    tasks_per_category: int = 1
    max_generation_attempts: int = 2
    max_review_attempts: int = 2


@dataclass(frozen=True)
class EvalsetResult:
    evalset_id: str
    status: Literal["ready", "quarantined", "failed"]
    run_dir: Path
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
    "EvalsetRequest",
    "EvalsetResult",
    "IngestRequest",
    "IngestResult",
    "RankedEndpoint",
    "RetrievalRequest",
    "RetrievalResult",
    "RetrievalStep",
    "TraceMode",
]
