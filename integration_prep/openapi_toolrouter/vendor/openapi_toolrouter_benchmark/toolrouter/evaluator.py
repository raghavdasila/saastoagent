from __future__ import annotations

import json
from collections import defaultdict
from pathlib import Path
from statistics import mean
from typing import Any

from .planner import construct_plan, validate_dry_run_shape
from .validation import ValidationContext


def expected_set(task: dict[str, Any]) -> set[str]:
    return set(task.get("expected_endpoint_sequence", []))


def allowed_sets(task: dict[str, Any]) -> list[set[str]]:
    groups = [expected_set(task)]
    for alt in task.get("allowed_alternatives", []) or []:
        groups.append(set(alt))
    return groups


def endpoint_recall(top_ids: list[str], task: dict[str, Any]) -> float:
    expected = expected_set(task)
    if not expected:
        return 1.0 if not top_ids else 0.0
    return len(expected & set(top_ids)) / len(expected)


def complete_plan(top_ids: list[str], task: dict[str, Any]) -> float:
    if not task.get("expected_endpoint_sequence"):
        return 1.0 if not top_ids else 0.0
    top = set(top_ids)
    return 1.0 if any(group <= top for group in allowed_sets(task)) else 0.0


def first_step_accuracy(top_ids: list[str], task: dict[str, Any]) -> float:
    expected = task.get("expected_endpoint_sequence", [])
    if task.get("task_type") in {"policy_required", "ambiguous"} and not expected:
        return 1.0 if not top_ids else 0.0
    return 1.0 if top_ids and expected and top_ids[0] == expected[0] else 0.0


def param_coverage(plan: list[dict[str, Any]], task: dict[str, Any]) -> float:
    expected = task.get("expected_required_params", {}) or {}
    total = sum(len(params) for params in expected.values())
    if total == 0:
        return 1.0
    covered = 0
    by_id = {step["endpoint_id"]: step for step in plan}
    for endpoint_id, params in expected.items():
        known = set(by_id.get(endpoint_id, {}).get("required_params", []))
        covered += len(set(params) & known)
    return covered / total


def schema_pass_rate(plan: list[dict[str, Any]], task: dict[str, Any]) -> float:
    if not plan:
        return 1.0 if task.get("task_type") in {"policy_required", "ambiguous"} else 0.0
    checks = [validate_dry_run_shape(step, task.get("expected_required_params", {}) or {}) for step in plan]
    return sum(1 for item in checks if item) / len(checks)


def route_selected(top_ids: list[str], task: dict[str, Any]) -> float:
    return complete_plan(top_ids, task)


def plan_validation_metrics(
    plan: list[dict[str, Any]],
    task: dict[str, Any],
    validation_context: ValidationContext | None,
) -> dict[str, Any]:
    if not plan:
        passed = 1.0 if task.get("task_type") in {"policy_required", "ambiguous"} else 0.0
        return {
            "request_body_schema_pass": passed,
            "validation_pass": passed,
            "response_validation_status": "unknown_no_fixture",
            "validation_statuses": [],
        }
    if validation_context is None:
        shape = schema_pass_rate(plan, task)
        return {
            "request_body_schema_pass": shape,
            "validation_pass": shape,
            "response_validation_status": "unknown_no_fixture",
            "validation_statuses": ["shape_check_only"],
        }
    checks = [validation_context.validate_step(step) for step in plan]
    return {
        "request_body_schema_pass": mean(float(check["request_body_schema_pass"]) for check in checks),
        "validation_pass": mean(float(check["validation_pass"]) for check in checks),
        "response_validation_status": "unknown_no_fixture",
        "validation_statuses": [str(check.get("validation_status", "")) for check in checks],
    }


def abstention_accuracy(top_ids: list[str], task: dict[str, Any]) -> float:
    should_abstain = task.get("task_type") in {"policy_required", "ambiguous"} and not task.get("expected_endpoint_sequence")
    if not should_abstain:
        return 1.0
    return 1.0 if not top_ids else 0.0


def failure_category(detail: dict[str, Any]) -> str:
    if detail["abstention_accuracy"] < 1.0:
        return "abstention_failure"
    if detail.get("route_selected", detail["complete_plan_recall_at_k"]) < 1.0:
        return "route_miss"
    if detail.get("required_params_covered", detail["param_coverage"]) < 1.0:
        return "required_param_issue"
    if detail.get("request_body_schema_pass", 1.0) < 1.0:
        return "request_body_schema_failure"
    if detail.get("validation_pass", detail["schema_validation_pass_rate"]) < 1.0:
        return "validation_failure"
    return "none"


def track_metrics(rows: list[dict[str, Any]]) -> dict[str, Any]:
    routing_rows = [row for row in rows if row.get("expected_endpoint_sequence")]
    ambiguous_rows = [row for row in rows if row.get("task_type") == "ambiguous" and not row.get("expected_endpoint_sequence")]
    policy_rows = [row for row in rows if row.get("task_type") == "policy_required" and not row.get("expected_endpoint_sequence")]
    routing_complete = mean(row["complete_plan_recall_at_k"] for row in routing_rows) if routing_rows else 0.0
    ambiguous_abstention = mean(row["abstention_accuracy"] for row in ambiguous_rows) if ambiguous_rows else 0.0
    policy_abstention = mean(row["abstention_accuracy"] for row in policy_rows) if policy_rows else 0.0
    return {
        "routing_task_count": len(routing_rows),
        "ambiguous_task_count": len(ambiguous_rows),
        "policy_task_count": len(policy_rows),
        "routing_only_complete_at_1": routing_complete,
        "routing_only_complete_at_10": routing_complete,
        "ambiguous_abstention_accuracy": ambiguous_abstention,
        "policy_abstention_accuracy": policy_abstention,
        "macro_average_by_track": mean([routing_complete, ambiguous_abstention, policy_abstention]),
    }


def track_metrics_by_group(rows: list[dict[str, Any]], keys: tuple[str, ...]) -> dict[tuple[Any, ...], dict[str, Any]]:
    grouped: dict[tuple[Any, ...], list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        grouped[tuple(row.get(key) for key in keys)].append(row)

    metrics: dict[tuple[Any, ...], dict[str, Any]] = {}
    for key, group_rows in grouped.items():
        rows_at_1 = [row for row in group_rows if int(row.get("k", 0)) == 1]
        rows_at_10 = [row for row in group_rows if int(row.get("k", 0)) == 10]
        count_rows = rows_at_1 or group_rows
        routing_at_1_rows = [row for row in rows_at_1 if row.get("expected_endpoint_sequence")]
        routing_at_10_rows = [row for row in rows_at_10 if row.get("expected_endpoint_sequence")]
        ambiguous_rows = [
            row
            for row in count_rows
            if row.get("task_type") == "ambiguous" and not row.get("expected_endpoint_sequence")
        ]
        policy_rows = [
            row
            for row in count_rows
            if row.get("task_type") == "policy_required" and not row.get("expected_endpoint_sequence")
        ]
        routing_at_1 = mean(row["complete_plan_recall_at_k"] for row in routing_at_1_rows) if routing_at_1_rows else 0.0
        routing_at_10 = (
            mean(row["complete_plan_recall_at_k"] for row in routing_at_10_rows)
            if routing_at_10_rows
            else routing_at_1
        )
        ambiguous_abstention = mean(row["abstention_accuracy"] for row in ambiguous_rows) if ambiguous_rows else 0.0
        policy_abstention = mean(row["abstention_accuracy"] for row in policy_rows) if policy_rows else 0.0
        metrics[key] = {
            "routing_task_count": len({row["task_id"] for row in count_rows if row.get("expected_endpoint_sequence")}),
            "ambiguous_task_count": len({row["task_id"] for row in ambiguous_rows}),
            "policy_task_count": len({row["task_id"] for row in policy_rows}),
            "routing_only_complete_at_1": routing_at_1,
            "routing_only_complete_at_10": routing_at_10,
            "ambiguous_abstention_accuracy": ambiguous_abstention,
            "policy_abstention_accuracy": policy_abstention,
            "macro_average_by_track": mean([routing_at_1, ambiguous_abstention, policy_abstention]),
        }
    return metrics


def evaluate_rankings(
    tasks: list[dict[str, Any]],
    rankings: dict[str, Any],
    split_task_ids: dict[str, set[str]] | None = None,
    k_values: list[int] | None = None,
    validation_context: ValidationContext | None = None,
) -> dict[str, Any]:
    k_values = k_values or [1, 3, 5, 10]
    split_task_ids = split_task_ids or {"all": {task["id"] for task in tasks}}
    tasks_by_id = {task["id"]: task for task in tasks}
    details: list[dict[str, Any]] = []
    summary: list[dict[str, Any]] = []
    for baseline, by_scope in rankings.items():
        if by_scope and all(isinstance(value, list) for value in by_scope.values()):
            by_scope = {"all": by_scope}
        for split, task_ids in split_task_ids.items():
            by_task = by_scope.get(split, {})
            split_tasks = [tasks_by_id[task_id] for task_id in sorted(task_ids) if task_id in tasks_by_id]
            if not split_tasks:
                continue
            for k in k_values:
                rows = []
                for task in split_tasks:
                    ranked = by_task.get(task["id"], [])
                    top = ranked[:k]
                    top_ids = [item["endpoint_id"] for item in top]
                    plan = construct_plan(top)
                    validation_metrics = plan_validation_metrics(plan, task, validation_context)
                    row = {
                        "baseline": baseline,
                        "split": split,
                        "k": k,
                        "task_id": task["id"],
                        "query": task.get("query", ""),
                        "router_query": task.get("router_query", task.get("query", "")),
                        "task_type": task.get("task_type"),
                        "resource": task.get("resource", ""),
                        "leakage_bucket": task.get("leakage_bucket", "unknown"),
                        "leakage_max_overlap": task.get("leakage_max_overlap", 0.0),
                        "expected_endpoint_sequence": task.get("expected_endpoint_sequence", []),
                        "top_endpoint_ids": top_ids,
                        "endpoint_recall_at_k": endpoint_recall(top_ids, task),
                        "complete_plan_recall_at_k": complete_plan(top_ids, task),
                        "first_step_top1_accuracy": first_step_accuracy(top_ids, task),
                        "param_coverage": param_coverage(plan, task),
                        "schema_validation_pass_rate": schema_pass_rate(plan, task),
                        "route_selected": route_selected(top_ids, task),
                        "required_params_covered": param_coverage(plan, task),
                        "request_body_schema_pass": validation_metrics["request_body_schema_pass"],
                        "validation_pass": validation_metrics["validation_pass"],
                        "response_validation_status": validation_metrics["response_validation_status"],
                        "validation_statuses": validation_metrics["validation_statuses"],
                        "abstention_accuracy": abstention_accuracy(top_ids, task),
                        "latency_ms": mean([float(item.get("latency_ms", 0.0)) for item in top]) if top else 0.0,
                    }
                    row["failure_category"] = failure_category(row)
                    details.append(row)
                    rows.append(row)
                summary.append(
                    {
                        "baseline": baseline,
                        "split": split,
                        "k": k,
                        "endpoint_recall_at_k": mean(row["endpoint_recall_at_k"] for row in rows),
                        "complete_plan_recall_at_k": mean(row["complete_plan_recall_at_k"] for row in rows),
                        "first_step_top1_accuracy": mean(row["first_step_top1_accuracy"] for row in rows),
                        "param_coverage": mean(row["param_coverage"] for row in rows),
                        "schema_validation_pass_rate": mean(row["schema_validation_pass_rate"] for row in rows),
                        "route_selected": mean(row["route_selected"] for row in rows),
                        "required_params_covered": mean(row["required_params_covered"] for row in rows),
                        "request_body_schema_pass": mean(row["request_body_schema_pass"] for row in rows),
                        "validation_pass": mean(row["validation_pass"] for row in rows),
                        "response_validation_known_rate": mean(
                            0.0 if row["response_validation_status"] == "unknown_no_fixture" else 1.0
                            for row in rows
                        ),
                        "abstention_accuracy": mean(row["abstention_accuracy"] for row in rows),
                        "latency_ms_mean": mean(row["latency_ms"] for row in rows),
                        **track_metrics(rows),
                    }
                )
    split_track_metrics = track_metrics_by_group(details, ("baseline", "split"))
    for row in summary:
        row.update(split_track_metrics.get((row["baseline"], row["split"]), track_metrics([])))

    leakage_summary = []
    grouped: dict[tuple[str, str, int, str], list[dict[str, Any]]] = {}
    for row in details:
        key = (row["baseline"], row["split"], int(row["k"]), str(row.get("leakage_bucket", "unknown")))
        grouped.setdefault(key, []).append(row)
    leakage_track_metrics = track_metrics_by_group(details, ("baseline", "split", "leakage_bucket"))
    for (baseline, split, k, leakage_bucket), rows in sorted(grouped.items()):
        leakage_summary.append(
            {
                "baseline": baseline,
                "split": split,
                "k": k,
                "leakage_bucket": leakage_bucket,
                "task_count": len(rows),
                "endpoint_recall_at_k": mean(row["endpoint_recall_at_k"] for row in rows),
                "complete_plan_recall_at_k": mean(row["complete_plan_recall_at_k"] for row in rows),
                "first_step_top1_accuracy": mean(row["first_step_top1_accuracy"] for row in rows),
                "route_selected": mean(row["route_selected"] for row in rows),
                "required_params_covered": mean(row["required_params_covered"] for row in rows),
                "request_body_schema_pass": mean(row["request_body_schema_pass"] for row in rows),
                "validation_pass": mean(row["validation_pass"] for row in rows),
                "abstention_accuracy": mean(row["abstention_accuracy"] for row in rows),
                **leakage_track_metrics.get((baseline, split, leakage_bucket), track_metrics(rows)),
            }
        )
    return {"summary": summary, "details": details, "leakage_summary": leakage_summary}


def write_results(results: dict[str, Any], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(results, indent=2), encoding="utf-8")


def read_results(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))
