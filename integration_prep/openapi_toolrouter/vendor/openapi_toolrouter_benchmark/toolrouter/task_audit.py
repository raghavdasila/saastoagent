from __future__ import annotations

import csv
import json
from pathlib import Path
from typing import Any

from .openapi_loader import NormalizedBundle


AUDIT_COLUMNS = [
    "task_id",
    "split",
    "resource",
    "task_type",
    "operation_class",
    "endpoint_id",
    "method",
    "path",
    "operationId",
    "required_params",
    "request_schemas",
    "response_schemas",
    "tags",
    "allowed_alternatives",
]


def join_values(values: Any) -> str:
    if not values:
        return ""
    if isinstance(values, list):
        return ";".join(str(value) for value in values)
    return str(values)


def audit_rows(
    tasks: list[dict[str, Any]],
    bundle: NormalizedBundle,
    split_by_task: dict[str, str] | None = None,
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    split_by_task = split_by_task or {}
    for task in tasks:
        alternatives = task.get("allowed_alternatives", []) or []
        for endpoint_id in task.get("expected_endpoint_sequence", []) or [""]:
            endpoint = bundle.endpoint_by_id(endpoint_id) if endpoint_id else None
            rows.append(
                {
                    "task_id": task["id"],
                    "split": split_by_task.get(task["id"], ""),
                    "resource": task.get("resource", ""),
                    "task_type": task.get("task_type", ""),
                    "operation_class": task.get("operation_class", endpoint.operation_class if endpoint else ""),
                    "endpoint_id": endpoint_id,
                    "method": endpoint.method if endpoint else "",
                    "path": endpoint.path if endpoint else "",
                    "operationId": endpoint.operation_id if endpoint else "",
                    "required_params": join_values(task.get("expected_required_params", {}).get(endpoint_id, [])),
                    "request_schemas": join_values(endpoint.request_schemas if endpoint else []),
                    "response_schemas": join_values(endpoint.response_schemas if endpoint else []),
                    "tags": join_values(endpoint.tags if endpoint else []),
                    "allowed_alternatives": join_values(["|".join(alt) for alt in alternatives]),
                }
            )
    return rows


def write_task_audit(
    tasks: list[dict[str, Any]],
    bundle: NormalizedBundle,
    out_dir: Path,
    split_by_task: dict[str, str] | None = None,
) -> list[dict[str, Any]]:
    rows = audit_rows(tasks, bundle, split_by_task)
    out_dir.mkdir(parents=True, exist_ok=True)
    with (out_dir / "task_audit.csv").open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=AUDIT_COLUMNS)
        writer.writeheader()
        writer.writerows(rows)
    (out_dir / "task_audit.json").write_text(json.dumps(rows, indent=2), encoding="utf-8")
    lines = [
        "# Task Audit",
        "",
        "| Task | Split | Resource | Type | Operation | Endpoint | Method | Path | Required Params | Schemas | Alternatives |",
        "|---|---|---|---|---|---|---|---|---|---|---|",
    ]
    for row in rows:
        schemas = ";".join(value for value in [row["request_schemas"], row["response_schemas"]] if value)
        lines.append(
            "| {task_id} | {split} | {resource} | {task_type} | {operation_class} | `{endpoint_id}` | {method} | `{path}` | {required_params} | {schemas} | {allowed_alternatives} |".format(
                schemas=schemas,
                **row,
            )
        )
    (out_dir / "task_audit.md").write_text("\n".join(lines), encoding="utf-8")
    return rows
