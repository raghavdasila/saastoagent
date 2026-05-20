from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import joblib
import numpy as np
from sklearn.linear_model import LogisticRegression

from .openapi_loader import NormalizedBundle, NormalizedEndpoint, normalize_text


FEEDBACK_FEATURE_NAMES = [
    "rag_score",
    "bm25_score",
    "graph_sparse_score",
    "grag_score",
    "schema_param_match",
    "operation_class_confidence",
    "resource_overlap",
    "path_token_overlap",
    "auth_required_param_compatibility",
    "previous_successful_usage_count",
    "previous_correction_count",
    "previous_rejection_count",
]

@dataclass
class FeedbackEvent:
    query: str
    decision_type: str
    top_candidates: list[dict[str, Any]]
    selected_endpoint: str | None
    confidence: float
    missing_params: list[str]
    follow_up_question: str
    user_selected_endpoint: str | None = None
    corrected_endpoint: str | None = None
    rejected_endpoints: list[str] = field(default_factory=list)
    validation_result: dict[str, Any] = field(default_factory=dict)
    execution_result: dict[str, Any] = field(default_factory=dict)
    source: str = "runtime"
    timestamp: str = ""

    def to_record(self) -> dict[str, Any]:
        record = asdict(self)
        if not record["timestamp"]:
            record["timestamp"] = datetime.now(timezone.utc).isoformat()
        return record


def write_feedback_event(path: Path, event: FeedbackEvent) -> dict[str, Any]:
    path.parent.mkdir(parents=True, exist_ok=True)
    record = event.to_record()
    with path.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(record, sort_keys=True) + "\n")
    return record


def read_feedback_events(path: Path | None) -> list[dict[str, Any]]:
    if path is None or not path.exists():
        return []
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def empty_adjustment() -> dict[str, int]:
    return {
        "previous_successful_usage_count": 0,
        "previous_correction_count": 0,
        "previous_rejection_count": 0,
    }


def feedback_adjustments(path: Path | None) -> dict[str, dict[str, int]]:
    stats: dict[str, dict[str, int]] = {}
    for event in read_feedback_events(path):
        positive = event.get("corrected_endpoint") or event.get("user_selected_endpoint") or event.get("selected_endpoint")
        if positive:
            stats.setdefault(str(positive), empty_adjustment())["previous_successful_usage_count"] += 1
        if event.get("corrected_endpoint"):
            stats.setdefault(str(event["corrected_endpoint"]), empty_adjustment())["previous_correction_count"] += 1
        for endpoint_id in event.get("rejected_endpoints", []) or []:
            stats.setdefault(str(endpoint_id), empty_adjustment())["previous_rejection_count"] += 1
        selected = event.get("selected_endpoint")
        corrected = event.get("corrected_endpoint")
        if selected and corrected and selected != corrected:
            stats.setdefault(str(selected), empty_adjustment())["previous_correction_count"] -= 1
            stats.setdefault(str(selected), empty_adjustment())["previous_rejection_count"] += 1
    return stats


def endpoint_path_tokens(endpoint: NormalizedEndpoint) -> set[str]:
    tokens: set[str] = set()
    for segment in endpoint.path.strip("/").split("/"):
        if not segment or segment.startswith("{"):
            continue
        tokens.update(normalize_text(segment).replace("-", " ").replace("_", " ").split())
    return {token for token in tokens if token}


def token_overlap(query: str, terms: list[str] | set[str]) -> float:
    query_tokens = set(normalize_text(query).replace("-", " ").replace("_", " ").split())
    term_tokens: set[str] = set()
    for term in terms:
        term_tokens.update(normalize_text(term).replace("-", " ").replace("_", " ").split())
    if not query_tokens or not term_tokens:
        return 0.0
    return len(query_tokens & term_tokens) / len(term_tokens)


def component_value(candidate: dict[str, Any], names: list[str]) -> float:
    components = candidate.get("score_components", {}) if isinstance(candidate.get("score_components"), dict) else {}
    for name in names:
        if name in components:
            return float(components.get(name, 0.0))
        if name in candidate:
            return float(candidate.get(name, 0.0))
    return float(candidate.get("score", 0.0)) if "fallback_score" in names else 0.0


def candidate_features(
    query: str,
    endpoint: NormalizedEndpoint,
    candidate: dict[str, Any],
    feedback_stats: dict[str, dict[str, int]] | None = None,
    missing_params: list[str] | None = None,
) -> list[float]:
    feedback_stats = feedback_stats or {}
    stats = feedback_stats.get(endpoint.id, {})
    grag_values = [
        component_value(candidate, ["grag_expand"]),
        component_value(candidate, ["grag_rerank"]),
        component_value(candidate, ["grag_constrained"]),
    ]
    required = list(endpoint.required_params)
    missing = set(missing_params or [])
    compatibility = 1.0
    if required:
        compatibility = 1.0 - (len(set(required) & missing) / len(required))
    return [
        component_value(candidate, ["rag_all_max", "rag_score", "fallback_score"]),
        component_value(candidate, ["bm25_all_max", "bm25_score"]),
        component_value(candidate, ["graph_sparse", "graph_sparse_score"]),
        max(grag_values),
        component_value(candidate, ["schema_param", "schema_param_match"]),
        float(endpoint.operation_confidence),
        token_overlap(query, set(endpoint.resources)),
        token_overlap(query, endpoint_path_tokens(endpoint)),
        compatibility,
        float(stats.get("previous_successful_usage_count", 0)),
        float(stats.get("previous_correction_count", 0)),
        float(stats.get("previous_rejection_count", 0)),
    ]


def feedback_manifest_path(out: Path) -> Path:
    return out.with_name(f"{out.stem}.manifest.json")


def labels_for_event(event: dict[str, Any]) -> tuple[set[str], set[str]]:
    positives: set[str] = set()
    negatives: set[str] = set(str(item) for item in event.get("rejected_endpoints", []) or [])
    if event.get("corrected_endpoint"):
        positives.add(str(event["corrected_endpoint"]))
        selected = event.get("selected_endpoint")
        if selected and selected != event["corrected_endpoint"]:
            negatives.add(str(selected))
    elif event.get("user_selected_endpoint"):
        positives.add(str(event["user_selected_endpoint"]))
    elif event.get("selected_endpoint") and event.get("validation_result", {}).get("validation_pass", 0):
        positives.add(str(event["selected_endpoint"]))
    elif event.get("selected_endpoint") and not event.get("corrected_endpoint"):
        positives.add(str(event["selected_endpoint"]))
    return positives, negatives


def training_rows(events: list[dict[str, Any]], bundle: NormalizedBundle) -> tuple[list[list[float]], list[int]]:
    stats = feedback_adjustments_from_events(events)
    features: list[list[float]] = []
    labels: list[int] = []
    for event in events:
        query = str(event.get("query", ""))
        positives, negatives = labels_for_event(event)
        candidates = event.get("top_candidates", []) or []
        seen_candidates = {str(candidate.get("endpoint_id")) for candidate in candidates if candidate.get("endpoint_id")}
        for positive in positives - seen_candidates:
            candidates.append({"endpoint_id": positive, "score": 1.0})
        for negative in negatives - seen_candidates:
            candidates.append({"endpoint_id": negative, "score": 0.0})
        for candidate in candidates:
            endpoint_id = str(candidate.get("endpoint_id", ""))
            try:
                endpoint = bundle.endpoint_by_id(endpoint_id)
            except KeyError:
                continue
            label = 1 if endpoint_id in positives else 0 if endpoint_id in negatives else None
            if label is None:
                continue
            features.append(
                candidate_features(
                    query,
                    endpoint,
                    candidate,
                    feedback_stats=stats,
                    missing_params=list(event.get("missing_params", []) or []),
                )
            )
            labels.append(label)
    return features, labels


def feedback_adjustments_from_events(events: list[dict[str, Any]]) -> dict[str, dict[str, int]]:
    stats: dict[str, dict[str, int]] = {}
    for event in events:
        positive = event.get("corrected_endpoint") or event.get("user_selected_endpoint") or event.get("selected_endpoint")
        if positive:
            stats.setdefault(str(positive), empty_adjustment())["previous_successful_usage_count"] += 1
        if event.get("corrected_endpoint"):
            stats.setdefault(str(event["corrected_endpoint"]), empty_adjustment())["previous_correction_count"] += 1
        for endpoint_id in event.get("rejected_endpoints", []) or []:
            stats.setdefault(str(endpoint_id), empty_adjustment())["previous_rejection_count"] += 1
        selected = event.get("selected_endpoint")
        corrected = event.get("corrected_endpoint")
        if selected and corrected and selected != corrected:
            stats.setdefault(str(selected), empty_adjustment())["previous_correction_count"] -= 1
            stats.setdefault(str(selected), empty_adjustment())["previous_rejection_count"] += 1
    return stats


def train_feedback_ranker(feedback_path: Path, bundle: NormalizedBundle, out: Path) -> dict[str, Any]:
    events = read_feedback_events(feedback_path)
    features, labels = training_rows(events, bundle)
    manifest = {
        "model_status": "insufficient_data",
        "event_count": len(events),
        "training_row_count": len(labels),
        "positive_count": sum(labels),
        "negative_count": len(labels) - sum(labels),
        "feature_names": FEEDBACK_FEATURE_NAMES,
    }
    out.parent.mkdir(parents=True, exist_ok=True)
    if set(labels) != {0, 1}:
        feedback_manifest_path(out).write_text(json.dumps(manifest, indent=2), encoding="utf-8")
        return manifest

    model = LogisticRegression(random_state=0, solver="liblinear")
    model.fit(np.asarray(features, dtype=float), np.asarray(labels, dtype=int))
    joblib.dump({"model": model, "feature_names": FEEDBACK_FEATURE_NAMES}, out)
    manifest["model_status"] = "trained"
    feedback_manifest_path(out).write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    return manifest


def load_feedback_ranker(path: Path | None) -> dict[str, Any] | None:
    if path is None or not path.exists():
        return None
    payload = joblib.load(path)
    if not isinstance(payload, dict) or "model" not in payload:
        raise ValueError(f"Invalid feedback ranker at {path}")
    return payload


def candidate_from_score_maps(endpoint_id: str, score_maps: dict[str, dict[str, float]]) -> dict[str, Any]:
    components = {name: float(scores.get(endpoint_id, 0.0)) for name, scores in score_maps.items()}
    return {
        "endpoint_id": endpoint_id,
        "score": max(components.values()) if components else 0.0,
        "score_components": components,
    }


def apply_feedback_model_scores(
    query: str,
    bundle: NormalizedBundle,
    endpoint_ids: list[str],
    score_maps: dict[str, dict[str, float]],
    model_payload: dict[str, Any] | None,
    feedback_log: Path | None = None,
) -> dict[str, float]:
    if not model_payload:
        return {}
    model = model_payload["model"]
    stats = feedback_adjustments(feedback_log)
    matrix = []
    valid_endpoint_ids = []
    for endpoint_id in endpoint_ids:
        try:
            endpoint = bundle.endpoint_by_id(endpoint_id)
        except KeyError:
            continue
        matrix.append(candidate_features(query, endpoint, candidate_from_score_maps(endpoint_id, score_maps), stats))
        valid_endpoint_ids.append(endpoint_id)
    if not matrix:
        return {}
    if hasattr(model, "predict_proba"):
        values = model.predict_proba(np.asarray(matrix, dtype=float))[:, 1]
    else:
        values = model.decision_function(np.asarray(matrix, dtype=float))
    return {endpoint_id: float(score) for endpoint_id, score in zip(valid_endpoint_ids, values)}
