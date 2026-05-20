from __future__ import annotations

import csv
import json
import re
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

from .openapi_loader import NormalizedBundle, NormalizedEndpoint, normalize_text


def tokens(value: str) -> set[str]:
    return set(re.findall(r"[a-z0-9_]+", normalize_text(value)))


def path_token_text(path: str) -> str:
    return " ".join(segment for segment in path.strip("/").split("/") if segment and not segment.startswith("{"))


def token_coverage(query_tokens: set[str], metadata: str) -> float:
    if not query_tokens:
        return 0.0
    metadata_tokens = tokens(metadata)
    if not metadata_tokens:
        return 0.0
    return len(query_tokens & metadata_tokens) / len(query_tokens)


def bucket_for_overlap(value: float) -> str:
    if value < 0.15:
        return "low"
    if value < 0.35:
        return "medium"
    return "high"


def endpoint_overlap(query: str, endpoint: NormalizedEndpoint) -> dict[str, float]:
    query_tokens = tokens(query)
    overlaps = {
        "operation_id_overlap": token_coverage(query_tokens, endpoint.operation_id),
        "summary_overlap": token_coverage(query_tokens, endpoint.summary),
        "description_overlap": token_coverage(query_tokens, endpoint.description),
        "tags_overlap": token_coverage(query_tokens, " ".join(endpoint.tags)),
        "path_overlap": token_coverage(query_tokens, path_token_text(endpoint.path)),
    }
    overlaps["max_overlap"] = max(overlaps.values()) if overlaps else 0.0
    return overlaps


def task_endpoint_ids(task: dict[str, Any]) -> list[str]:
    ids = list(task.get("expected_endpoint_sequence", []) or [])
    for group in task.get("allowed_alternatives", []) or []:
        ids.extend(str(endpoint_id) for endpoint_id in group)
    return list(dict.fromkeys(ids))


def compute_task_leakage(tasks: list[dict[str, Any]], bundle: NormalizedBundle) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for task in tasks:
        query = str(task.get("router_query") or task.get("query") or "")
        endpoint_ids = task_endpoint_ids(task)
        endpoint_rows = []
        for endpoint_id in endpoint_ids:
            try:
                endpoint = bundle.endpoint_by_id(endpoint_id)
            except KeyError:
                continue
            endpoint_rows.append(endpoint_overlap(query, endpoint))
        if endpoint_rows:
            combined = {
                key: max(row[key] for row in endpoint_rows)
                for key in [
                    "operation_id_overlap",
                    "summary_overlap",
                    "description_overlap",
                    "tags_overlap",
                    "path_overlap",
                    "max_overlap",
                ]
            }
        else:
            combined = {
                "operation_id_overlap": 0.0,
                "summary_overlap": 0.0,
                "description_overlap": 0.0,
                "tags_overlap": 0.0,
                "path_overlap": 0.0,
                "max_overlap": 0.0,
            }
        rows.append(
            {
                "task_id": task["id"],
                "router_query": query,
                "resource": task.get("resource", ""),
                "task_type": task.get("task_type", ""),
                "operation_class": task.get("operation_class", ""),
                "expected_endpoint_sequence": endpoint_ids,
                **combined,
                "overlap_bucket": bucket_for_overlap(float(combined["max_overlap"])),
            }
        )
    return rows


def attach_leakage_to_tasks(tasks: list[dict[str, Any]], bundle: NormalizedBundle) -> list[dict[str, Any]]:
    rows = compute_task_leakage(tasks, bundle)
    by_id = {row["task_id"]: row for row in rows}
    attached: list[dict[str, Any]] = []
    for task in tasks:
        row = by_id.get(task["id"], {})
        attached.append(
            {
                **task,
                "leakage_bucket": row.get("overlap_bucket", "unknown"),
                "leakage_max_overlap": row.get("max_overlap", 0.0),
            }
        )
    return attached


def write_leakage_audit(tasks: list[dict[str, Any]], bundle: NormalizedBundle, out_dir: Path) -> list[dict[str, Any]]:
    out_dir.mkdir(parents=True, exist_ok=True)
    rows = compute_task_leakage(tasks, bundle)
    fieldnames = [
        "task_id",
        "router_query",
        "resource",
        "task_type",
        "operation_class",
        "expected_endpoint_sequence",
        "operation_id_overlap",
        "summary_overlap",
        "description_overlap",
        "tags_overlap",
        "path_overlap",
        "max_overlap",
        "overlap_bucket",
    ]
    with (out_dir / "leakage_audit.csv").open("w", encoding="utf-8", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow({**row, "expected_endpoint_sequence": json.dumps(row["expected_endpoint_sequence"])})
    (out_dir / "leakage_audit.json").write_text(json.dumps(rows, indent=2), encoding="utf-8")
    lines = [
        "# Leakage Audit",
        "",
        "| Task | Bucket | Max overlap | OperationId | Summary | Description | Tags | Path |",
        "|---|---|---:|---:|---:|---:|---:|---:|",
    ]
    for row in rows:
        lines.append(
            "| {task_id} | {bucket} | {max:.3f} | {op:.3f} | {summary:.3f} | {desc:.3f} | {tags:.3f} | {path:.3f} |".format(
                task_id=row["task_id"],
                bucket=row["overlap_bucket"],
                max=row["max_overlap"],
                op=row["operation_id_overlap"],
                summary=row["summary_overlap"],
                desc=row["description_overlap"],
                tags=row["tags_overlap"],
                path=row["path_overlap"],
            )
        )
    bucket_by_type: dict[str, Counter[str]] = defaultdict(Counter)
    bucket_by_resource: dict[str, Counter[str]] = defaultdict(Counter)
    for row in rows:
        bucket = str(row["overlap_bucket"])
        bucket_by_type[str(row.get("task_type") or "unknown")][bucket] += 1
        bucket_by_resource[str(row.get("resource") or "unknown")][bucket] += 1
    lines.extend(
        [
            "",
            "## Bucket Counts By Task Type",
            "",
            "| Task type | Low | Medium | High |",
            "|---|---:|---:|---:|",
        ]
    )
    for task_type, counts in sorted(bucket_by_type.items()):
        lines.append(f"| {task_type} | {counts['low']} | {counts['medium']} | {counts['high']} |")
    lines.extend(
        [
            "",
            "## Bucket Counts By Resource",
            "",
            "| Resource | Low | Medium | High |",
            "|---|---:|---:|---:|",
        ]
    )
    for resource, counts in sorted(bucket_by_resource.items()):
        lines.append(f"| {resource} | {counts['low']} | {counts['medium']} | {counts['high']} |")
    (out_dir / "leakage_audit.md").write_text("\n".join(lines), encoding="utf-8")
    return rows
