from __future__ import annotations

import json
import math
from collections import Counter
from pathlib import Path
from typing import Any, Mapping, Sequence


def _read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def _read_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for line_number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        if not line.strip():
            continue
        value = json.loads(line)
        if not isinstance(value, dict):
            raise ValueError(f"{path}:{line_number} must contain a JSON object")
        rows.append(value)
    return rows


def _completion_scope(completion_key: str) -> tuple[str, str]:
    parts = completion_key.split("/")
    if len(parts) != 5 or not parts[0] or not parts[3]:
        raise ValueError(f"Malformed factory completion key: {completion_key!r}")
    return parts[0], parts[3]


def _pareto_frontier(configurations: Mapping[str, Mapping[str, Any]]) -> list[str]:
    frontier: list[str] = []
    for name, point in configurations.items():
        point_tokens = point.get("tokens_per_accepted_correct")
        if point_tokens is None:
            continue
        dominated = False
        for other_name, other in configurations.items():
            if other_name == name or other.get("tokens_per_accepted_correct") is None:
                continue
            no_worse = (
                other["endpoint_truth_precision"] >= point["endpoint_truth_precision"]
                and other["category_fidelity"] >= point["category_fidelity"]
                and other["coverage"] >= point["coverage"]
                and other["tokens_per_accepted_correct"] <= point_tokens
            )
            strictly_better = (
                other["endpoint_truth_precision"] > point["endpoint_truth_precision"]
                or other["category_fidelity"] > point["category_fidelity"]
                or other["coverage"] > point["coverage"]
                or other["tokens_per_accepted_correct"] < point_tokens
            )
            if no_worse and strictly_better:
                dominated = True
                break
        if not dominated:
            frontier.append(name)
    return sorted(frontier)


def _strategy_metrics(
    *,
    targets: set[str],
    strategy: str,
    completed: Mapping[str, Mapping[str, Any]],
    reviews_by_candidate: Mapping[str, Mapping[str, Any]],
    token_rows: Sequence[Mapping[str, Any]],
    endpoint_truth_floor: float,
    category_fidelity_floor: float,
    coverage_floor: float,
) -> dict[str, Any]:
    scoped = {
        key: value
        for key, value in completed.items()
        if _completion_scope(key)[0] in targets and _completion_scope(key)[1] == strategy
    }
    accepted = [value for value in scoped.values() if value.get("status") == "accepted"]
    accepted_reviews: list[Mapping[str, Any]] = []
    for terminal in accepted:
        candidate_id = str(terminal.get("candidate_id") or "")
        review = reviews_by_candidate.get(candidate_id)
        if review is None:
            raise ValueError(f"Accepted candidate {candidate_id!r} lacks semantic review evidence")
        accepted_reviews.append(review)
    endpoint_correct = sum(bool(row.get("endpoint_truth_correct")) for row in accepted_reviews)
    category_correct = sum(
        bool((row.get("semantic_review") or {}).get("category_fidelity"))
        for row in accepted_reviews
    )
    offline_tokens = sum(
        int((row.get("usage") or {}).get("total_tokens") or 0)
        for row in token_rows
        if str(row.get("target_id") or "") in targets
        and str(row.get("context_strategy") or "") == strategy
    )
    incurred_tokens = sum(
        int((row.get("incurred_usage") or {}).get("total_tokens") or 0)
        for row in token_rows
        if str(row.get("target_id") or "") in targets
        and str(row.get("context_strategy") or "") == strategy
    )
    accepted_count = len(accepted)
    expected_count = len(scoped)
    endpoint_precision = endpoint_correct / accepted_count if accepted_count else 0.0
    category_fidelity = category_correct / accepted_count if accepted_count else 0.0
    coverage = accepted_count / expected_count if expected_count else 0.0
    metrics = {
        "targets": sorted(targets),
        "expected_keys": expected_count,
        "accepted_keys": accepted_count,
        "terminal_status_counts": dict(
            sorted(Counter(str(value.get("status") or "unknown") for value in scoped.values()).items())
        ),
        "endpoint_truth_precision": endpoint_precision,
        "category_fidelity": category_fidelity,
        "coverage": coverage,
        "offline_tokens": offline_tokens,
        "offline_tokens_incurred": incurred_tokens,
        "tokens_per_accepted_correct": (
            offline_tokens / endpoint_correct if endpoint_correct else None
        ),
    }
    metrics["passes_registered_floors"] = (
        endpoint_precision >= endpoint_truth_floor
        and category_fidelity >= category_fidelity_floor
        and coverage >= coverage_floor
    )
    return metrics


def build_collection_folds(run_dir: Path) -> dict[str, Any]:
    manifest = _read_json(run_dir / "run_manifest.json")
    progress = _read_json(run_dir / "progress.json")
    summary = _read_json(run_dir / "summary.json")
    if not all(isinstance(value, dict) for value in (manifest, progress, summary)):
        raise ValueError("Factory manifest, progress, and summary must be JSON objects")
    completed_count = int(summary.get("completed_keys") or 0)
    expected_count = int(summary.get("expected_completion_keys") or 0)
    if expected_count < 1 or completed_count != expected_count:
        raise ValueError(
            f"Factory run is incomplete: completed {completed_count} of {expected_count} keys"
        )
    config = dict(manifest.get("config") or {})
    targets = [str(value) for value in config.get("targets") or []]
    strategies = [str(value) for value in config.get("context_strategies") or []]
    if len(targets) < 3:
        raise ValueError("Collection-level pseudo-blind calibration requires at least three targets")
    if not strategies:
        raise ValueError("Factory run has no configured context strategies")
    completed = dict(progress.get("completed") or {})
    review_rows = _read_jsonl(run_dir / "reviews.jsonl")
    reviews_by_candidate: dict[str, Mapping[str, Any]] = {}
    for row in review_rows:
        candidate_id = str(row.get("candidate_id") or "")
        if not candidate_id:
            continue
        if candidate_id in reviews_by_candidate:
            raise ValueError(f"Duplicate semantic review candidate ID: {candidate_id}")
        reviews_by_candidate[candidate_id] = row
    token_rows = _read_jsonl(run_dir / "token_ledger.jsonl")
    endpoint_floor = float(config.get("endpoint_truth_floor"))
    category_floor = float(config.get("category_fidelity_floor"))
    coverage_floor = float(config.get("coverage_floor"))

    folds: dict[str, Any] = {}
    selected_counts: Counter[str] = Counter()
    for held_out in targets:
        train_targets = set(targets) - {held_out}
        training = {
            strategy: _strategy_metrics(
                targets=train_targets,
                strategy=strategy,
                completed=completed,
                reviews_by_candidate=reviews_by_candidate,
                token_rows=token_rows,
                endpoint_truth_floor=endpoint_floor,
                category_fidelity_floor=category_floor,
                coverage_floor=coverage_floor,
            )
            for strategy in strategies
        }
        pareto = _pareto_frontier(training)
        eligible = [name for name in pareto if training[name]["passes_registered_floors"]]
        selected = min(
            eligible,
            key=lambda name: (
                training[name]["tokens_per_accepted_correct"]
                if training[name]["tokens_per_accepted_correct"] is not None
                else math.inf,
                name,
            ),
            default=None,
        )
        held_out_metrics = {
            strategy: _strategy_metrics(
                targets={held_out},
                strategy=strategy,
                completed=completed,
                reviews_by_candidate=reviews_by_candidate,
                token_rows=token_rows,
                endpoint_truth_floor=endpoint_floor,
                category_fidelity_floor=category_floor,
                coverage_floor=coverage_floor,
            )
            for strategy in strategies
        }
        if selected is not None:
            selected_counts[selected] += 1
        folds[held_out] = {
            "held_out_target": held_out,
            "training_targets": sorted(train_targets),
            "training_configurations": training,
            "training_pareto_frontier": pareto,
            "selected_configuration_without_held_out": selected,
            "held_out_configurations": held_out_metrics,
            "selected_held_out_metrics": held_out_metrics.get(selected) if selected else None,
        }
    return {
        "schema_version": 1,
        "run_id": str(manifest.get("run_id") or ""),
        "configuration_hash": str(manifest.get("configuration_hash") or ""),
        "targets": targets,
        "strategies": strategies,
        "registered_floors": {
            "endpoint_truth_precision": endpoint_floor,
            "category_fidelity": category_floor,
            "coverage": coverage_floor,
        },
        "method": (
            "For each held-out catalog, select the lowest-token eligible Pareto strategy using only "
            "the other catalogs, then expose the already-recorded metrics for that strategy on the held-out catalog."
        ),
        "selected_configuration_counts": dict(sorted(selected_counts.items())),
        "all_folds_selected": sum(selected_counts.values()) == len(targets),
        "folds": folds,
    }
