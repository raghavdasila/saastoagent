from __future__ import annotations

import time
from dataclasses import asdict, dataclass, field
from pathlib import Path
from statistics import mean
from typing import Any

from .feedback import (
    FeedbackEvent,
    apply_feedback_model_scores,
    feedback_adjustments,
    load_feedback_ranker,
    write_feedback_event,
)
from .openapi_loader import NormalizedBundle, NormalizedEndpoint, normalize_text
from .retrieval_indices import RetrievalIndices, minmax
from .router_baselines import (
    compute_scores_for_query,
    constrained_grid,
    grag_constrained_scores,
    grag_expand_grid,
    grag_expand_scores,
    grag_rerank_scores,
    rerank_weight_grid,
    top_ids_from_scores,
)


DECISION_TYPES = {
    "ROUTE",
    "SHOW_TOPK",
    "ASK_PARAM",
    "ASK_DISAMBIGUATE",
    "ASK_POLICY",
    "BLOCK_UNSAFE",
}


@dataclass
class DecisionConfig:
    name: str = "default"
    route_confidence_threshold: float = 0.42
    route_margin_threshold: float = 0.06
    param_confidence_threshold: float = 0.20
    show_topk_confidence_threshold: float = 0.24
    unsafe_write_threshold: float = 0.35
    feedback_model_weight: float = 0.25


@dataclass
class ProductDecision:
    query: str
    decision_type: str
    confidence: float
    margin: float
    unsafe_flag: bool
    decision_reason: str
    top_candidates: list[dict[str, Any]]
    selected_endpoint: str | None = None
    missing_params: list[str] = field(default_factory=list)
    follow_up_question: str = ""
    candidate_endpoint_ids: list[str] = field(default_factory=list)
    score_components: dict[str, dict[str, float]] = field(default_factory=dict)
    latency_ms: float = 0.0

    def to_record(self) -> dict[str, Any]:
        return asdict(self)


def product_score_maps(query: str, bundle: NormalizedBundle, indices: RetrievalIndices) -> dict[str, dict[str, float]]:
    scores = compute_scores_for_query(query, indices)
    scores["grag_expand"], _expand_trace = grag_expand_scores(query, indices, grag_expand_grid()[0])
    semantic = rerank_weight_grid()[-1]
    semantic_weights = {key: float(semantic[key]) for key in semantic if key != "name"}
    scores["grag_rerank"], _rerank_trace = grag_rerank_scores(query, bundle, indices, scores, semantic_weights)
    scores["grag_constrained"], _constrained_trace = grag_constrained_scores(query, bundle, indices, scores, constrained_grid()[0])
    return scores


def combined_product_scores(
    score_maps: dict[str, dict[str, float]],
    endpoint_ids: list[str],
    feedback_stats: dict[str, dict[str, int]] | None = None,
    feedback_model_scores: dict[str, float] | None = None,
    feedback_model_weight: float = 0.25,
) -> dict[str, float]:
    feedback_stats = feedback_stats or {}
    feedback_model_scores = feedback_model_scores or {}
    weights = {
        "rag_all_max": 0.30,
        "bm25_all_max": 0.20,
        "grag_expand": 0.20,
        "grag_rerank": 0.10,
        "grag_constrained": 0.10,
        "graph_sparse": 0.05,
        "schema_param": 0.05,
    }
    scores: dict[str, float] = {}
    for endpoint_id in endpoint_ids:
        value = sum(weight * score_maps.get(name, {}).get(endpoint_id, 0.0) for name, weight in weights.items())
        stats = feedback_stats.get(endpoint_id, {})
        value += min(0.20, 0.025 * float(stats.get("previous_successful_usage_count", 0)))
        value += min(0.15, 0.030 * float(stats.get("previous_correction_count", 0)))
        value -= min(0.25, 0.050 * float(stats.get("previous_rejection_count", 0)))
        value += feedback_model_weight * feedback_model_scores.get(endpoint_id, 0.0)
        scores[endpoint_id] = value
    return minmax(scores)


def endpoint_reason(endpoint: NormalizedEndpoint, score: float) -> str:
    label = endpoint.summary or endpoint.operation_id or endpoint.path
    return f"{endpoint.method} {endpoint.path} - {label} ({score:.2f})"


def candidate_records(
    bundle: NormalizedBundle,
    scores: dict[str, float],
    limit: int,
    score_maps: dict[str, dict[str, float]],
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for endpoint_id in top_ids_from_scores(scores, limit):
        endpoint = bundle.endpoint_by_id(endpoint_id)
        rows.append(
            {
                "endpoint_id": endpoint.id,
                "method": endpoint.method,
                "path": endpoint.path,
                "operation_id": endpoint.operation_id,
                "summary": endpoint.summary,
                "score": float(scores.get(endpoint.id, 0.0)),
                "reason": endpoint_reason(endpoint, float(scores.get(endpoint.id, 0.0))),
                "score_components": {
                    name: float(values.get(endpoint.id, 0.0))
                    for name, values in score_maps.items()
                    if name in {"rag_all_max", "bm25_all_max", "graph_sparse", "grag_expand", "grag_rerank", "grag_constrained", "schema_param"}
                },
            }
        )
    return rows


def query_mentions_param(query: str, param_name: str) -> bool:
    normalized = normalize_text(query).replace("-", " ").replace("_", " ")
    param_tokens = normalize_text(param_name).replace("-", " ").replace("_", " ").split()
    return bool(param_tokens) and all(token in normalized for token in param_tokens)


def required_body_fields(endpoint: NormalizedEndpoint, bundle: NormalizedBundle) -> list[str]:
    fields: list[str] = []
    for schema_name in endpoint.request_schemas:
        schema = bundle.schemas.get(schema_name, {}) or {}
        required = schema.get("required", [])
        if isinstance(required, list):
            fields.extend(str(item) for item in required if str(item))
    return list(dict.fromkeys(fields))


def missing_required_params(
    endpoint: NormalizedEndpoint,
    bundle: NormalizedBundle,
    query: str,
    provided_params: dict[str, Any],
) -> list[str]:
    missing: list[str] = []
    for param in list(endpoint.required_params) + required_body_fields(endpoint, bundle):
        if param in provided_params or query_mentions_param(query, param):
            continue
        missing.append(param)
    return list(dict.fromkeys(missing))


def policy_gap_requested(query: str) -> bool:
    q = normalize_text(query)
    return any(token in q for token in ["policy", "approval", "allowed", "compliance", "business rule"])


def endpoint_is_destructive(endpoint: NormalizedEndpoint | None) -> bool:
    return bool(endpoint and (endpoint.method.upper() == "DELETE" or endpoint.operation_class == "delete"))


def follow_up_for_params(endpoint: NormalizedEndpoint, missing: list[str]) -> str:
    label = endpoint.summary or endpoint.operation_id or endpoint.path
    return f"I can use {endpoint.method} {endpoint.path} ({label}), but I need {', '.join(missing)} before preparing the call."


def follow_up_for_disambiguation(top_candidates: list[dict[str, Any]]) -> str:
    choices = "; ".join(candidate["reason"] for candidate in top_candidates[:3])
    return f"I found multiple plausible API candidates. Which one should I use? {choices}"


def follow_up_for_topk(top_candidates: list[dict[str, Any]]) -> str:
    choices = "; ".join(candidate["reason"] for candidate in top_candidates[:3])
    return f"I am not confident enough to route directly. Top candidates: {choices}"


def follow_up_for_policy() -> str:
    return (
        "OpenAPI exposes possible actions. OpenAPI defines possible actions, but it does not define the qualification or business policy needed "
        "to decide this. Which policy source should I use?"
    )


def follow_up_for_unsafe(endpoint: NormalizedEndpoint) -> str:
    return (
        f"{endpoint.method} {endpoint.path} is a destructive endpoint. Please provide explicit confirmation "
        "or ask me to keep it as a dry-run candidate before it is used."
    )


def product_ranking_context(
    query: str,
    bundle: NormalizedBundle,
    indices: RetrievalIndices,
    feedback_stats: dict[str, dict[str, int]] | None = None,
    feedback_log: Path | None = None,
    feedback_model: dict[str, Any] | Path | None = None,
    config: DecisionConfig | None = None,
) -> dict[str, Any]:
    started = time.perf_counter()
    config = config or DecisionConfig()
    model_payload = load_feedback_ranker(feedback_model) if isinstance(feedback_model, Path) else feedback_model
    score_maps = product_score_maps(query, bundle, indices)
    feedback_model_scores = apply_feedback_model_scores(
        query,
        bundle,
        indices.endpoint_ids,
        score_maps,
        model_payload,
        feedback_log=feedback_log,
    )
    scores = combined_product_scores(
        score_maps,
        indices.endpoint_ids,
        feedback_stats=feedback_stats,
        feedback_model_scores=feedback_model_scores,
        feedback_model_weight=config.feedback_model_weight,
    )
    ranked_ids = top_ids_from_scores(scores, 10)
    top_endpoint = bundle.endpoint_by_id(ranked_ids[0]) if ranked_ids else None
    top_score = float(scores.get(ranked_ids[0], 0.0)) if ranked_ids else 0.0
    second_score = float(scores.get(ranked_ids[1], 0.0)) if len(ranked_ids) > 1 else 0.0
    top_candidates = candidate_records(bundle, scores, 3, score_maps)
    candidate_ids = ranked_ids[:10]
    return {
        "query": query,
        "score_maps": score_maps,
        "scores": scores,
        "ranked_ids": ranked_ids,
        "top_endpoint": top_endpoint,
        "top_score": top_score,
        "second_score": second_score,
        "margin": top_score - second_score,
        "top_candidates": top_candidates,
        "candidate_ids": candidate_ids,
        "latency_ms": (time.perf_counter() - started) * 1000,
    }


def decide_from_ranking_context(
    context: dict[str, Any],
    bundle: NormalizedBundle,
    provided_params: dict[str, Any] | None = None,
    confirmed: bool = False,
    config: DecisionConfig | None = None,
) -> ProductDecision:
    provided_params = provided_params or {}
    config = config or DecisionConfig()
    query = str(context.get("query") or "")
    ranked_ids = list(context.get("ranked_ids", []) or [])
    top_endpoint = context.get("top_endpoint")
    top_score = float(context.get("top_score", 0.0))
    margin = float(context.get("margin", 0.0))
    top_candidates = list(context.get("top_candidates", []) or [])
    candidate_ids = list(context.get("candidate_ids", []) or [])
    score_maps = context.get("score_maps", {}) if isinstance(context.get("score_maps"), dict) else {}

    decision_type = "ROUTE"
    selected_endpoint = ranked_ids[0] if ranked_ids else None
    missing: list[str] = []
    follow_up = ""
    unsafe_flag = False
    decision_reason = "high_confidence_route"

    if policy_gap_requested(query):
        decision_type = "ASK_POLICY"
        selected_endpoint = None
        follow_up = follow_up_for_policy()
        decision_reason = "policy_gap"
    elif top_endpoint is None:
        decision_type = "ASK_DISAMBIGUATE"
        selected_endpoint = None
        follow_up = "I could not find a clear endpoint candidate. Please clarify the workflow."
        decision_reason = "vague_query_disambiguation"
    else:
        missing = missing_required_params(top_endpoint, bundle, query, provided_params)
        unsafe_flag = endpoint_is_destructive(top_endpoint) and not confirmed and top_score >= config.unsafe_write_threshold
        vague_query = len(normalize_text(query).split()) <= 3
        if missing and top_score >= config.param_confidence_threshold:
            decision_type = "ASK_PARAM"
            selected_endpoint = top_endpoint.id
            follow_up = follow_up_for_params(top_endpoint, missing)
            decision_reason = "missing_required_inputs"
        elif unsafe_flag:
            decision_type = "BLOCK_UNSAFE"
            selected_endpoint = None
            follow_up = follow_up_for_unsafe(top_endpoint)
            decision_reason = "unsafe_unconfirmed_write"
        elif vague_query or margin < config.route_margin_threshold:
            decision_type = "ASK_DISAMBIGUATE" if vague_query else "SHOW_TOPK"
            selected_endpoint = None
            follow_up = follow_up_for_disambiguation(top_candidates) if vague_query else follow_up_for_topk(top_candidates)
            decision_reason = "vague_query_disambiguation" if vague_query else "low_margin_topk"
        elif top_score < config.route_confidence_threshold:
            decision_type = "SHOW_TOPK"
            selected_endpoint = None
            follow_up = follow_up_for_topk(top_candidates)
            decision_reason = "low_confidence_topk"

    return ProductDecision(
        query=query,
        decision_type=decision_type,
        confidence=top_score,
        margin=margin,
        unsafe_flag=unsafe_flag,
        decision_reason=decision_reason,
        top_candidates=top_candidates,
        selected_endpoint=selected_endpoint,
        missing_params=missing,
        follow_up_question=follow_up,
        candidate_endpoint_ids=candidate_ids,
        score_components={
            endpoint_id: {
                name: float(values.get(endpoint_id, 0.0))
                for name, values in score_maps.items()
                if name in {"rag_all_max", "bm25_all_max", "graph_sparse", "grag_expand", "grag_rerank", "grag_constrained", "schema_param"}
            }
            for endpoint_id in candidate_ids[:3]
        },
        latency_ms=float(context.get("latency_ms", 0.0)),
    )


def route_product_query(
    query: str,
    bundle: NormalizedBundle,
    indices: RetrievalIndices,
    provided_params: dict[str, Any] | None = None,
    confirmed: bool = False,
    feedback_stats: dict[str, dict[str, int]] | None = None,
    feedback_log: Path | None = None,
    feedback_model: dict[str, Any] | Path | None = None,
    config: DecisionConfig | None = None,
) -> ProductDecision:
    context = product_ranking_context(
        query,
        bundle,
        indices,
        feedback_stats=feedback_stats,
        feedback_log=feedback_log,
        feedback_model=feedback_model,
        config=config,
    )
    return decide_from_ranking_context(
        context,
        bundle,
        provided_params=provided_params,
        confirmed=confirmed,
        config=config,
    )


def expected_endpoint_ids(task: dict[str, Any]) -> list[str]:
    return list(task.get("expected_endpoint_sequence", []) or [])


def expected_decision(task: dict[str, Any]) -> str:
    return str(task.get("expected_decision_type") or ("ROUTE" if expected_endpoint_ids(task) else "ASK_DISAMBIGUATE"))


def route_hit(candidate_ids: list[str], task: dict[str, Any], k: int) -> float:
    expected = set(expected_endpoint_ids(task))
    if not expected:
        return 0.0
    return 1.0 if expected <= set(candidate_ids[:k]) else 0.0


def followup_type(decision_type: str) -> str:
    return decision_type if decision_type.startswith("ASK_") or decision_type == "BLOCK_UNSAFE" else ""


def split_by_task_from_splits(tasks: list[dict[str, Any]], splits: dict[str, Any] | None) -> dict[str, str]:
    if not splits:
        return {str(task["id"]): "all" for task in tasks}
    by_task: dict[str, str] = {}
    for split, ids in splits.get("primary", {}).items():
        for task_id in ids:
            by_task[str(task_id)] = str(split)
    for task in tasks:
        by_task.setdefault(str(task["id"]), "all")
    return by_task


def dev_ids_from_splits(tasks: list[dict[str, Any]], splits: dict[str, Any] | None) -> set[str]:
    if splits:
        dev_ids = set(str(task_id) for task_id in splits.get("primary", {}).get("dev", []))
        if dev_ids:
            return dev_ids
    return {str(task["id"]) for task in tasks}


def build_product_contexts(
    tasks: list[dict[str, Any]],
    bundle: NormalizedBundle,
    indices: RetrievalIndices,
    feedback_log: Path | None,
    feedback_model: Path | dict[str, Any] | None,
    feedback_stats: dict[str, dict[str, int]],
    config: DecisionConfig,
) -> dict[str, dict[str, Any]]:
    model_payload = load_feedback_ranker(feedback_model) if isinstance(feedback_model, Path) else feedback_model
    contexts: dict[str, dict[str, Any]] = {}
    for task in tasks:
        query = str(task.get("router_query") or task.get("query") or "")
        contexts[str(task["id"])] = product_ranking_context(
            query,
            bundle,
            indices,
            feedback_stats=feedback_stats,
            feedback_log=feedback_log,
            feedback_model=model_payload,
            config=config,
        )
    return contexts


def product_detail_row(
    task: dict[str, Any],
    decision: ProductDecision,
    split: str = "all",
) -> dict[str, Any]:
    expected = expected_decision(task)
    expected_ids = expected_endpoint_ids(task)
    missing_expected = list(task.get("expected_missing_params", []) or [])
    validation_pass = 1.0 if decision.selected_endpoint in expected_ids or not expected_ids else 0.0
    row = {
        "task_id": task.get("id"),
        "track": task.get("track", "natural_routing"),
        "split": split,
        "query": decision.query,
        "expected_decision_type": expected,
        "decision_type": decision.decision_type,
        "correct_decision_type": 1.0 if decision.decision_type == expected else 0.0,
        "correct_followup_type": 1.0 if followup_type(decision.decision_type) == followup_type(expected) else 0.0,
        "expected_endpoint_sequence": expected_ids,
        "selected_endpoint": decision.selected_endpoint,
        "top_candidate_ids": decision.candidate_endpoint_ids,
        "natural_top1_route_accuracy": route_hit(decision.candidate_endpoint_ids, task, 1),
        "natural_top3_recoverability": route_hit(decision.candidate_endpoint_ids, task, 3),
        "natural_top10_candidate_recall": route_hit(decision.candidate_endpoint_ids, task, 10),
        "required_param_question_accuracy": (
            1.0
            if not missing_expected
            else float(all(param in decision.follow_up_question for param in missing_expected))
        ),
        "policy_gap_detection_accuracy": 1.0 if expected != "ASK_POLICY" else float(decision.decision_type == "ASK_POLICY"),
        "false_execution": 1.0 if decision.decision_type == "ROUTE" and expected != "ROUTE" else 0.0,
        "false_overclarification": 1.0 if expected == "ROUTE" and decision.decision_type != "ROUTE" else 0.0,
        "validation_pass": validation_pass,
        "validation_result": {
            "validation_pass": validation_pass,
            "status": "dry_run_match" if validation_pass else "route_mismatch",
        },
        "latency_ms": decision.latency_ms,
        "confidence": decision.confidence,
        "margin": decision.margin,
        "unsafe_flag": decision.unsafe_flag,
        "decision_reason": decision.decision_reason,
        "missing_params": decision.missing_params,
        "follow_up_question": decision.follow_up_question,
        "top_candidates": decision.top_candidates,
    }
    return row


def product_details_for_config(
    tasks: list[dict[str, Any]],
    bundle: NormalizedBundle,
    contexts: dict[str, dict[str, Any]],
    config: DecisionConfig,
    split_by_task: dict[str, str],
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for task in tasks:
        task_id = str(task["id"])
        decision = decide_from_ranking_context(
            contexts[task_id],
            bundle,
            provided_params=task.get("provided_params", {}) if isinstance(task.get("provided_params", {}), dict) else {},
            confirmed=bool(task.get("confirmed", False)),
            config=config,
        )
        rows.append(product_detail_row(task, decision, split=split_by_task.get(task_id, "all")))
    return rows


def summarize_product_details(details: list[dict[str, Any]]) -> list[dict[str, Any]]:
    summary: list[dict[str, Any]] = []
    scopes = [("all", details)]
    for split in sorted({str(row.get("split", "all")) for row in details} - {"all"}):
        scopes.append((split, [row for row in details if row.get("split") == split]))
    for split, split_rows in scopes:
        for track in sorted({str(row.get("track", "unknown")) for row in split_rows}):
            rows = [row for row in split_rows if row.get("track") == track]
            routing_rows = [row for row in rows if row.get("expected_endpoint_sequence")]
            followup_rows = [
                row
                for row in rows
                if str(row.get("expected_decision_type", "")).startswith("ASK_") or row.get("expected_decision_type") == "BLOCK_UNSAFE"
            ]
            summary.append(
                {
                    "split": split,
                    "track": track,
                    "task_count": len(rows),
                    "routing_task_count": len(routing_rows),
                    "followup_task_count": len(followup_rows),
                    "natural_top1_route_accuracy": mean(row["natural_top1_route_accuracy"] for row in routing_rows) if routing_rows else 0.0,
                    "natural_top3_recoverability": mean(row["natural_top3_recoverability"] for row in routing_rows) if routing_rows else 0.0,
                    "natural_top10_candidate_recall": mean(row["natural_top10_candidate_recall"] for row in routing_rows) if routing_rows else 0.0,
                    "correct_decision_type": mean(row["correct_decision_type"] for row in rows) if rows else 0.0,
                    "correct_followup_type": mean(row["correct_followup_type"] for row in followup_rows) if followup_rows else 0.0,
                    "required_param_question_accuracy": mean(row["required_param_question_accuracy"] for row in followup_rows) if followup_rows else 0.0,
                    "policy_gap_detection_accuracy": mean(row["policy_gap_detection_accuracy"] for row in rows) if rows else 0.0,
                    "false_execution_rate": mean(row["false_execution"] for row in rows) if rows else 0.0,
                    "false_overclarification_rate": mean(row["false_overclarification"] for row in rows) if rows else 0.0,
                    "feedback_recovery_rate": 0.0,
                    "validation_pass_rate": mean(row["validation_pass"] for row in rows) if rows else 0.0,
                    "latency_ms": mean(row["latency_ms"] for row in rows) if rows else 0.0,
                }
            )
    return summary


def evaluate_product_readiness(
    tasks: list[dict[str, Any]],
    bundle: NormalizedBundle,
    indices: RetrievalIndices,
    feedback_log: Path | None = None,
    feedback_model: Path | dict[str, Any] | None = None,
    write_feedback_log: Path | None = None,
    splits: dict[str, Any] | None = None,
    decision_config: DecisionConfig | None = None,
    tune_decision: bool = True,
    synthetic_feedback_out: Path | None = None,
    synthetic_feedback_model: Path | None = None,
) -> dict[str, Any]:
    from .product_calibration import (
        config_record,
        decision_calibration_rows,
        decision_confusion_rows,
        decision_config_grid,
        select_decision_config_from_rows,
        synthetic_feedback_experiment_record,
        train_synthetic_feedback,
        write_synthetic_feedback_events,
    )
    from .splits import build_task_splits

    if splits is None:
        splits = build_task_splits(tasks)
    split_by_task = split_by_task_from_splits(tasks, splits)
    dev_ids = dev_ids_from_splits(tasks, splits)
    feedback_stats = feedback_adjustments(feedback_log)
    model_payload = load_feedback_ranker(feedback_model) if isinstance(feedback_model, Path) else feedback_model
    base_config = decision_config or DecisionConfig()
    contexts = build_product_contexts(tasks, bundle, indices, feedback_log, model_payload, feedback_stats, base_config)
    config_ablation: list[dict[str, Any]] = []
    selected_from = "provided"
    selected_config = decision_config or base_config
    if decision_config is None and tune_decision:
        configs = decision_config_grid()
        rows_by_config = {
            config.name: product_details_for_config(tasks, bundle, contexts, config, split_by_task)
            for config in configs
        }
        selected_config, config_ablation = select_decision_config_from_rows(configs, rows_by_config, dev_ids)
        selected_from = "dev"
    details = product_details_for_config(tasks, bundle, contexts, selected_config, split_by_task)

    for row in details:
        if write_feedback_log is not None:
            write_feedback_event(
                write_feedback_log,
                FeedbackEvent(
                    query=str(row["query"]),
                    decision_type=str(row["decision_type"]),
                    top_candidates=list(row["top_candidates"]),
                    selected_endpoint=row["selected_endpoint"],
                    confidence=float(row["confidence"]),
                    missing_params=list(row["missing_params"]),
                    follow_up_question=str(row["follow_up_question"]),
                    validation_result={"validation_pass": row["validation_pass"]},
                    execution_result={"status": "dry_run"},
                    source="benchmark",
                ),
            )

    summary = summarize_product_details(details)
    synthetic_experiment: dict[str, Any] | None = None
    if synthetic_feedback_out is not None:
        synthetic_feedback_model = synthetic_feedback_model or synthetic_feedback_out.with_name("synthetic_feedback_ranker.joblib")
        events = write_synthetic_feedback_events(synthetic_feedback_out, details)
        manifest = train_synthetic_feedback(synthetic_feedback_out, synthetic_feedback_model, bundle)
        after_results = evaluate_product_readiness(
            tasks,
            bundle,
            indices,
            feedback_log=synthetic_feedback_out,
            feedback_model=synthetic_feedback_model if synthetic_feedback_model.exists() else None,
            splits=splits,
            decision_config=selected_config,
            tune_decision=False,
        )
        synthetic_experiment = synthetic_feedback_experiment_record(
            summary,
            after_results["product_summary"],
            synthetic_feedback_out,
            synthetic_feedback_model,
            manifest,
            len(events),
        )

    result = {
        "mode": "product_readiness",
        "product_summary": summary,
        "product_details": details,
        "selected_decision_config": {
            "selected_from": selected_from,
            "dev_task_ids": sorted(dev_ids),
            **config_record(selected_config),
        },
        "decision_config_ablation": config_ablation,
        "decision_calibration": decision_calibration_rows(details),
        "decision_confusion": decision_confusion_rows(details),
        "feedback_learning": {
            "feedback_event_count": len(feedback_adjustments(feedback_log)) if feedback_log else 0,
            "model_status": "loaded" if model_payload else "not_loaded",
            "feature_names": [
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
            ],
        },
    }
    if synthetic_experiment is not None:
        result["synthetic_feedback_experiment"] = synthetic_experiment
        result["feedback_learning"]["synthetic_feedback_experiment"] = synthetic_experiment
    return result
