from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping, Sequence

from .semantic_validation_io import write_json_atomic


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


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _unique_by_id(
    rows: Sequence[Mapping[str, Any]],
    *,
    id_getter,
    label: str,
) -> dict[str, Mapping[str, Any]]:
    indexed: dict[str, Mapping[str, Any]] = {}
    for row in rows:
        row_id = str(id_getter(row) or "")
        if not row_id:
            continue
        if row_id in indexed:
            raise ValueError(f"Duplicate {label} ID in factory evidence: {row_id}")
        indexed[row_id] = row
    return indexed


def _task_from_candidate(
    *,
    candidate_row: Mapping[str, Any],
    review_row: Mapping[str, Any],
    run_id: str,
    configuration_hash: str,
) -> dict[str, Any]:
    candidate = dict(candidate_row.get("candidate") or {})
    candidate_id = str(candidate.get("candidate_id") or "")
    source_task_id = str(candidate_row.get("source_task_id") or "")
    target_id = str(candidate.get("target_id") or candidate_row.get("target_id") or "")
    category = str(candidate.get("category") or candidate_row.get("category") or "")
    query = " ".join(str(candidate.get("query") or "").split())
    decision = str(candidate.get("expected_decision") or "")
    strategy = str(candidate.get("context_strategy") or candidate_row.get("context_strategy") or "")
    completion_key = str(candidate_row.get("completion_key") or "")
    semantic_review = dict(review_row.get("semantic_review") or {})
    required = {
        "candidate_id": candidate_id,
        "target_id": target_id,
        "category": category,
        "query": query,
        "expected_decision": decision,
        "context_strategy": strategy,
        "completion_key": completion_key,
    }
    missing = sorted(name for name, value in required.items() if not value)
    if missing:
        raise ValueError(f"Accepted candidate is missing required export fields: {missing}")
    if review_row.get("status") != "accepted" or not semantic_review.get("passed"):
        raise ValueError(f"Candidate {candidate_id} does not have a passing accepted review")
    return {
        "id": candidate_id,
        "query": query,
        "router_query": query,
        "expected_decision_type": decision,
        "expected_endpoint_sequence": [
            str(value) for value in candidate.get("expected_endpoint_sequence") or []
        ],
        "allowed_alternatives": [
            [str(value) for value in sequence]
            for sequence in candidate.get("allowed_alternatives") or []
        ],
        "expected_required_params": dict(candidate.get("expected_required_params") or {}),
        "provided_params": dict(candidate.get("provided_params") or {}),
        "conversation_context": dict(candidate.get("conversation_context") or {}),
        "evalset": {
            "schema_version": 1,
            "query_category": category,
            "origin": "evalset_factory_accepted",
            "freshness": "generated_for_run",
            "run_id": run_id,
            "context_strategy": strategy,
            "source_task_id": source_task_id,
        },
        "provenance": {
            "target_id": target_id,
            "candidate_id": candidate_id,
            "completion_key": completion_key,
            "configuration_hash": configuration_hash,
            "recipe_hash": str(candidate.get("recipe_hash") or ""),
            "generator_model": str(candidate.get("generator_model") or ""),
            "reviewer_model": str(semantic_review.get("reviewer_model") or ""),
            "generation_input_hash": str((candidate_row.get("generation") or {}).get("input_hash") or ""),
            "generation_output_hash": str((candidate_row.get("generation") or {}).get("output_hash") or ""),
            "review_input_hash": str(semantic_review.get("input_hash") or ""),
            "review_output_hash": str(semantic_review.get("output_hash") or ""),
            "truth_evidence": dict(candidate.get("truth_evidence") or {}),
        },
        "validation": {
            "schema_version": 1,
            "target_id": target_id,
            "semantic_responsibility": "route_and_rank",
            "source_task_ids": [source_task_id] if source_task_id else [],
            "factory_deterministic_validation_passed": True,
            "factory_semantic_review_passed": True,
        },
    }


def build_export(
    *,
    run_dir: Path,
    strategy: str,
    target_id: str | None = None,
    manual_audit_summary_path: Path | None = None,
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    manifest_path = run_dir / "run_manifest.json"
    progress_path = run_dir / "progress.json"
    summary_path = run_dir / "summary.json"
    candidates_path = run_dir / "candidates.jsonl"
    reviews_path = run_dir / "reviews.jsonl"
    manifest = _read_json(manifest_path)
    progress = _read_json(progress_path)
    summary = _read_json(summary_path)
    if not all(isinstance(value, dict) for value in (manifest, progress, summary)):
        raise ValueError("Factory manifest, progress, and summary must be JSON objects")
    completed_count = int(summary.get("completed_keys") or 0)
    expected_count = int(summary.get("expected_completion_keys") or 0)
    if expected_count < 1 or completed_count != expected_count:
        raise ValueError(
            f"Factory run is incomplete: completed {completed_count} of {expected_count} keys"
        )
    run_id = str(manifest.get("run_id") or summary.get("run_id") or "")
    configuration_hash = str(manifest.get("configuration_hash") or "")
    if not run_id or not configuration_hash:
        raise ValueError("Factory run manifest lacks run_id or configuration_hash")
    configured_strategies = [
        str(value) for value in (manifest.get("config") or {}).get("context_strategies") or []
    ]
    if strategy not in configured_strategies:
        raise ValueError(
            f"Strategy {strategy!r} is absent from run configuration: {configured_strategies}"
        )

    manual_verdicts: dict[str, Mapping[str, Any]] | None = None
    if manual_audit_summary_path is not None:
        manual_audit = _read_json(manual_audit_summary_path)
        if not isinstance(manual_audit, dict):
            raise ValueError("Manual audit summary must be a JSON object")
        for field, expected in (
            ("run_id", run_id),
            ("configuration_hash", configuration_hash),
            ("strategy", strategy),
        ):
            if str(manual_audit.get(field) or "") != expected:
                raise ValueError(f"Manual audit summary disagrees on {field}")
        if manual_audit.get("fully_covered") is not True:
            raise ValueError("Manual audit summary is not fully covered")
        audit_rows = list(manual_audit.get("rows") or [])
        manual_verdicts = _unique_by_id(
            audit_rows,
            id_getter=lambda row: row.get("candidate_id"),
            label="manual audit candidate",
        )

    candidate_rows = _read_jsonl(candidates_path)
    review_rows = _read_jsonl(reviews_path)
    candidates = _unique_by_id(
        [row for row in candidate_rows if row.get("status") == "generated"],
        id_getter=lambda row: (row.get("candidate") or {}).get("candidate_id"),
        label="candidate",
    )
    accepted_reviews = _unique_by_id(
        [row for row in review_rows if row.get("status") == "accepted"],
        id_getter=lambda row: row.get("candidate_id"),
        label="accepted review",
    )

    completed = dict(progress.get("completed") or {})
    tasks: list[dict[str, Any]] = []
    for completion_key, terminal in sorted(completed.items()):
        if not isinstance(terminal, Mapping) or terminal.get("status") != "accepted":
            continue
        candidate_id = str(terminal.get("candidate_id") or "")
        candidate_row = candidates.get(candidate_id)
        review_row = accepted_reviews.get(candidate_id)
        if candidate_row is None or review_row is None:
            raise ValueError(
                f"Accepted terminal candidate {candidate_id!r} lacks generated or accepted-review evidence"
            )
        candidate = dict(candidate_row.get("candidate") or {})
        if candidate_row.get("completion_key") != completion_key:
            raise ValueError(f"Candidate {candidate_id} completion key does not match progress")
        if str(candidate.get("context_strategy") or "") != strategy:
            continue
        if target_id is not None and str(candidate.get("target_id") or "") != target_id:
            continue
        if manual_verdicts is not None:
            manual_row = manual_verdicts.get(candidate_id)
            if manual_row is None:
                raise ValueError(f"Accepted candidate {candidate_id} is absent from manual audit")
            if str(manual_row.get("verdict") or "") != "pass":
                continue
        task = _task_from_candidate(
            candidate_row=candidate_row,
            review_row=review_row,
            run_id=run_id,
            configuration_hash=configuration_hash,
        )
        if manual_verdicts is not None:
            task["validation"]["factory_manual_audit_passed"] = True
        tasks.append(task)
    if not tasks:
        scope = f"strategy={strategy!r}" + (f", target={target_id!r}" if target_id else "")
        raise ValueError(f"Factory run contains no accepted terminal tasks for {scope}")
    ids = [str(task["id"]) for task in tasks]
    if len(ids) != len(set(ids)):
        raise ValueError("Export would contain duplicate task IDs")
    export_manifest = {
        "schema_version": 1,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "runtime_location": "local",
        "run_id": run_id,
        "configuration_hash": configuration_hash,
        "strategy": strategy,
        "target_id": target_id,
        "factory_run_complete": True,
        "factory_completed_keys": completed_count,
        "factory_expected_completion_keys": expected_count,
        "manual_audit_required": manual_audit_summary_path is not None,
        "exported_task_count": len(tasks),
        "decision_counts": {
            decision: sum(task["expected_decision_type"] == decision for task in tasks)
            for decision in sorted({str(task["expected_decision_type"]) for task in tasks})
        },
        "category_counts": {
            category: sum(task["evalset"]["query_category"] == category for task in tasks)
            for category in sorted({str(task["evalset"]["query_category"]) for task in tasks})
        },
        "evidence_sha256": {
            "run_manifest.json": _sha256(manifest_path),
            "progress.json": _sha256(progress_path),
            "summary.json": _sha256(summary_path),
            "candidates.jsonl": _sha256(candidates_path),
            "reviews.jsonl": _sha256(reviews_path),
        },
    }
    if manual_audit_summary_path is not None:
        export_manifest["evidence_sha256"]["manual_audit_summary.json"] = _sha256(
            manual_audit_summary_path
        )
    return tasks, export_manifest


def write_export(
    *,
    tasks_path: Path,
    manifest_path: Path,
    tasks: Sequence[Mapping[str, Any]],
    manifest: Mapping[str, Any],
) -> dict[str, Any]:
    write_json_atomic(tasks_path, list(tasks))
    finalized_manifest = dict(manifest)
    finalized_manifest["tasks_path"] = str(tasks_path.resolve())
    finalized_manifest["tasks_sha256"] = _sha256(tasks_path)
    write_json_atomic(manifest_path, finalized_manifest)
    return finalized_manifest
