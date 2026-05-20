from __future__ import annotations

from typing import Any


def construct_plan(ranked: list[dict[str, Any]], max_steps: int = 6) -> list[dict[str, Any]]:
    plan: list[dict[str, Any]] = []
    seen: set[str] = set()
    for item in ranked:
        endpoint_id = item["endpoint_id"]
        if endpoint_id in seen:
            continue
        seen.add(endpoint_id)
        plan.append(item)
        if len(plan) >= max_steps:
            break
    return plan


def validate_dry_run_shape(step: dict[str, Any], expected_required_params: dict[str, list[str]]) -> bool:
    expected = set(expected_required_params.get(step["endpoint_id"], []))
    known = set(step.get("required_params", []))
    return expected <= known
