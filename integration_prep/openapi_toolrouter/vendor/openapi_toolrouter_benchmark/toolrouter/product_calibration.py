from __future__ import annotations

from collections import Counter
from pathlib import Path
from statistics import mean
from typing import Any

from .feedback import FeedbackEvent, feedback_manifest_path, train_feedback_ranker, write_feedback_event


DECISION_TYPES = [
    "ROUTE",
    "SHOW_TOPK",
    "ASK_PARAM",
    "ASK_DISAMBIGUATE",
    "ASK_POLICY",
    "BLOCK_UNSAFE",
]

REQUESTED_CONFUSION_PAIRS = [
    ("ROUTE", "SHOW_TOPK"),
    ("ROUTE", "ASK_PARAM"),
    ("ROUTE", "BLOCK_UNSAFE"),
    ("ASK_PARAM", "ASK_DISAMBIGUATE"),
    ("ASK_POLICY", "ASK_DISAMBIGUATE"),
]


def decision_config_grid() -> list[Any]:
    from .decision_router import DecisionConfig

    configs: list[DecisionConfig] = []
    for route_threshold in [0.30, 0.42, 0.54]:
        for margin_threshold in [0.00, 0.03, 0.06, 0.10]:
            for param_threshold in [0.00, 0.10, 0.20]:
                for topk_threshold in [0.18, 0.24, 0.35]:
                    for unsafe_threshold in [0.20, 0.35, 0.50]:
                        configs.append(
                            DecisionConfig(
                                name=(
                                    f"route{route_threshold:.2f}_margin{margin_threshold:.2f}_"
                                    f"param{param_threshold:.2f}_topk{topk_threshold:.2f}_unsafe{unsafe_threshold:.2f}"
                                ),
                                route_confidence_threshold=route_threshold,
                                route_margin_threshold=margin_threshold,
                                param_confidence_threshold=param_threshold,
                                show_topk_confidence_threshold=topk_threshold,
                                unsafe_write_threshold=unsafe_threshold,
                            )
                        )
    return configs


def config_record(config: Any) -> dict[str, Any]:
    return {
        "name": getattr(config, "name", "unnamed"),
        "route_confidence_threshold": float(getattr(config, "route_confidence_threshold", 0.0)),
        "route_margin_threshold": float(getattr(config, "route_margin_threshold", 0.0)),
        "param_confidence_threshold": float(getattr(config, "param_confidence_threshold", 0.0)),
        "show_topk_confidence_threshold": float(getattr(config, "show_topk_confidence_threshold", 0.0)),
        "unsafe_write_threshold": float(getattr(config, "unsafe_write_threshold", 0.0)),
        "feedback_model_weight": float(getattr(config, "feedback_model_weight", 0.0)),
    }


def metric_mean(rows: list[dict[str, Any]], key: str) -> float:
    return mean(float(row.get(key, 0.0)) for row in rows) if rows else 0.0


def product_metrics_for_rows(rows: list[dict[str, Any]]) -> dict[str, Any]:
    routing_rows = [row for row in rows if row.get("expected_endpoint_sequence")]
    natural_routing = [
        row
        for row in routing_rows
        if str(row.get("track", "natural_routing")) == "natural_routing"
    ]
    scored_routing = natural_routing or routing_rows
    return {
        "task_count": len(rows),
        "natural_top1_route_accuracy": metric_mean(scored_routing, "natural_top1_route_accuracy"),
        "natural_top3_recoverability": metric_mean(scored_routing, "natural_top3_recoverability"),
        "natural_top10_candidate_recall": metric_mean(scored_routing, "natural_top10_candidate_recall"),
        "correct_decision_type": metric_mean(rows, "correct_decision_type"),
        "false_execution_rate": metric_mean(rows, "false_execution"),
        "false_overclarification_rate": metric_mean(rows, "false_overclarification"),
        "validation_pass_rate": metric_mean(rows, "validation_pass"),
    }


def select_decision_config_from_rows(
    configs: list[Any],
    rows_by_config: dict[str, list[dict[str, Any]]],
    dev_ids: set[str],
) -> tuple[Any, list[dict[str, Any]]]:
    scoped_rows_by_config: dict[str, list[dict[str, Any]]] = {}
    ablation: list[dict[str, Any]] = []
    for config in configs:
        name = getattr(config, "name", "unnamed")
        all_rows = rows_by_config.get(name, [])
        scoped_rows = [row for row in all_rows if not dev_ids or str(row.get("task_id")) in dev_ids]
        scoped_rows_by_config[name] = scoped_rows
        metrics = product_metrics_for_rows(scoped_rows)
        ablation.append(
            {
                "scope": "dev",
                "selected": False,
                **config_record(config),
                **metrics,
            }
        )

    satisfying = [
        config
        for config in configs
        if product_metrics_for_rows(scoped_rows_by_config.get(getattr(config, "name", "unnamed"), []))[
            "false_execution_rate"
        ]
        <= 0.10
    ]
    candidates = satisfying or configs

    def sort_key(config: Any) -> tuple[float, float, float, str]:
        metrics = product_metrics_for_rows(scoped_rows_by_config.get(getattr(config, "name", "unnamed"), []))
        return (
            -float(metrics["natural_top1_route_accuracy"]),
            -float(metrics["correct_decision_type"]),
            float(metrics["false_overclarification_rate"]),
            str(getattr(config, "name", "unnamed")),
        )

    selected = sorted(candidates, key=sort_key)[0] if candidates else configs[0]
    for row in ablation:
        row["selected"] = row["name"] == getattr(selected, "name", "unnamed")
    return selected, ablation


def decision_confusion_rows(details: list[dict[str, Any]]) -> list[dict[str, Any]]:
    counts = Counter(
        (
            str(row.get("expected_decision_type") or ""),
            str(row.get("decision_type") or ""),
        )
        for row in details
    )
    pairs = set(counts) | set(REQUESTED_CONFUSION_PAIRS)
    for expected in DECISION_TYPES:
        for actual in DECISION_TYPES:
            if (expected, actual) in counts:
                pairs.add((expected, actual))
    return [
        {
            "expected_decision_type": expected,
            "decision_type": actual,
            "count": int(counts.get((expected, actual), 0)),
            "highlight_pair": (expected, actual) in REQUESTED_CONFUSION_PAIRS,
        }
        for expected, actual in sorted(pairs)
    ]


def decision_calibration_rows(details: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for detail in details:
        top3 = [
            str(candidate.get("endpoint_id"))
            for candidate in detail.get("top_candidates", [])[:3]
            if candidate.get("endpoint_id")
        ]
        rows.append(
            {
                "task_id": detail.get("task_id"),
                "track": detail.get("track"),
                "split": detail.get("split", "all"),
                "query": detail.get("query"),
                "expected_decision_type": detail.get("expected_decision_type"),
                "decision_type": detail.get("decision_type"),
                "expected_endpoint": (detail.get("expected_endpoint_sequence") or [None])[0],
                "selected_endpoint": detail.get("selected_endpoint"),
                "top3_candidates": top3,
                "confidence": float(detail.get("confidence", 0.0)),
                "margin": float(detail.get("margin", 0.0)),
                "missing_params": list(detail.get("missing_params", []) or []),
                "unsafe_flag": bool(detail.get("unsafe_flag", False)),
                "validation_result": detail.get("validation_result", {}),
                "decision_reason": detail.get("decision_reason", ""),
            }
        )
    return rows


def synthetic_feedback_events_from_details(details: list[dict[str, Any]]) -> list[FeedbackEvent]:
    events: list[FeedbackEvent] = []
    for detail in details:
        expected = [str(item) for item in detail.get("expected_endpoint_sequence", []) or []]
        selected = detail.get("selected_endpoint")
        top_candidates = list(detail.get("top_candidates", []) or [])
        candidate_ids = [
            str(candidate.get("endpoint_id"))
            for candidate in top_candidates
            if candidate.get("endpoint_id")
        ]
        rejected: list[str] = []
        corrected: str | None = None
        validation_pass = bool(detail.get("validation_pass", 0.0))
        if expected:
            if selected in expected:
                validation_pass = True
            else:
                corrected = expected[0]
                rejected.extend(candidate_id for candidate_id in candidate_ids if candidate_id not in expected)
                if selected and selected not in expected:
                    rejected.append(str(selected))
        else:
            rejected.extend(candidate_id for candidate_id in candidate_ids if candidate_id)
            if selected:
                rejected.append(str(selected))
        if not selected and corrected:
            top_candidates.append({"endpoint_id": corrected, "score": 1.0})
        rejected = sorted(set(rejected))
        if not expected and not rejected:
            continue
        events.append(
            FeedbackEvent(
                query=str(detail.get("query") or ""),
                decision_type=str(detail.get("decision_type") or ""),
                top_candidates=top_candidates,
                selected_endpoint=str(selected) if selected else None,
                confidence=float(detail.get("confidence", 0.0)),
                missing_params=list(detail.get("missing_params", []) or []),
                follow_up_question=str(detail.get("follow_up_question") or ""),
                corrected_endpoint=corrected,
                rejected_endpoints=rejected,
                validation_result={"validation_pass": 1.0 if validation_pass else 0.0},
                execution_result={"status": "dry_run"},
                source="synthetic_offline",
            )
        )
    return events


def write_synthetic_feedback_events(path: Path, details: list[dict[str, Any]]) -> list[FeedbackEvent]:
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        path.unlink()
    events = synthetic_feedback_events_from_details(details)
    for event in events:
        write_feedback_event(path, event)
    return events


def synthetic_feedback_experiment_record(
    before_summary: list[dict[str, Any]],
    after_summary: list[dict[str, Any]],
    feedback_path: Path,
    model_path: Path,
    manifest: dict[str, Any],
    event_count: int,
) -> dict[str, Any]:
    return {
        "source": "synthetic_offline",
        "event_count": event_count,
        "feedback_path": str(feedback_path),
        "model_path": str(model_path),
        "manifest_path": str(feedback_manifest_path(model_path)),
        "model_status": manifest.get("model_status", "unknown"),
        "before": before_summary,
        "after": after_summary,
        "note": "Offline experiment generated from benchmark corrections; not real runtime feedback.",
    }


def train_synthetic_feedback(feedback_path: Path, model_path: Path, bundle: Any) -> dict[str, Any]:
    return train_feedback_ranker(feedback_path, bundle, model_path)
