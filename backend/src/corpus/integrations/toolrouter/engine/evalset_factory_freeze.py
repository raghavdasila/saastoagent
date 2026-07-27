from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping


MANUAL_DIMENSIONS = (
    "endpoint_truth_correct",
    "category_fidelity",
    "naturalness",
    "evidence_sufficient",
)


def _read_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"Expected a JSON object at {path}")
    return value


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _require_same_identity(
    *,
    label: str,
    value: Mapping[str, Any],
    run_id: str,
    configuration_hash: str,
) -> None:
    if str(value.get("run_id") or "") != run_id:
        raise ValueError(f"{label} run_id does not match calibration manifest")
    if str(value.get("configuration_hash") or "") != configuration_hash:
        raise ValueError(f"{label} configuration_hash does not match calibration manifest")


def build_frozen_config(
    *,
    run_dir: Path,
    manual_audit_path: Path,
    collection_folds_path: Path,
    manual_precision_floor: float = 0.90,
) -> dict[str, Any]:
    if not 0 <= manual_precision_floor <= 1:
        raise ValueError("manual_precision_floor must be between zero and one")
    manifest_path = run_dir / "run_manifest.json"
    summary_path = run_dir / "summary.json"
    progress_path = run_dir / "progress.json"
    candidates_path = run_dir / "candidates.jsonl"
    reviews_path = run_dir / "reviews.jsonl"
    token_path = run_dir / "token_ledger.jsonl"
    manifest = _read_json(manifest_path)
    summary = _read_json(summary_path)
    audit = _read_json(manual_audit_path)
    folds = _read_json(collection_folds_path)
    run_id = str(manifest.get("run_id") or "")
    configuration_hash = str(manifest.get("configuration_hash") or "")
    if not run_id or not configuration_hash:
        raise ValueError("Calibration manifest lacks run_id or configuration_hash")
    _require_same_identity(
        label="Calibration summary",
        value=summary,
        run_id=run_id,
        configuration_hash=configuration_hash,
    )
    _require_same_identity(
        label="Manual audit",
        value=audit,
        run_id=run_id,
        configuration_hash=configuration_hash,
    )
    _require_same_identity(
        label="Collection folds",
        value=folds,
        run_id=run_id,
        configuration_hash=configuration_hash,
    )
    completed = int(summary.get("completed_keys") or 0)
    expected = int(summary.get("expected_completion_keys") or 0)
    if expected < 1 or completed != expected:
        raise ValueError(f"Calibration run is incomplete: completed {completed} of {expected} keys")
    selected = str(summary.get("selected_configuration") or "")
    if not selected:
        raise ValueError("Calibration summary has no automatically eligible selected configuration")
    configurations = dict(summary.get("configurations") or {})
    selected_metrics = dict(configurations.get(selected) or {})
    if not selected_metrics.get("passes_registered_floors"):
        raise ValueError(f"Selected configuration {selected!r} does not pass registered floors")
    if str(audit.get("strategy") or "") != selected:
        raise ValueError("Manual audit strategy does not match selected configuration")
    accepted_keys = int(selected_metrics.get("accepted_keys") or 0)
    if not audit.get("fully_covered") or int(audit.get("reviewed_rows") or 0) != accepted_keys:
        raise ValueError(
            "Manual audit must cover every accepted row in the selected configuration "
            f"({audit.get('reviewed_rows')} reviewed versus {accepted_keys} accepted)"
        )
    dimension_precision = dict(audit.get("dimension_precision") or {})
    failing_dimensions = {
        name: float(dimension_precision.get(name) or 0.0)
        for name in MANUAL_DIMENSIONS
        if float(dimension_precision.get(name) or 0.0) < manual_precision_floor
    }
    if failing_dimensions:
        raise ValueError(
            f"Manual audit dimensions fall below {manual_precision_floor:.3f}: {failing_dimensions}"
        )
    final_pass_precision = float(audit.get("final_pass_precision") or 0.0)
    if final_pass_precision < manual_precision_floor:
        raise ValueError(
            f"Manual final-pass precision {final_pass_precision:.3f} is below "
            f"{manual_precision_floor:.3f}"
        )
    if not folds.get("all_folds_selected"):
        raise ValueError("At least one collection pseudo-blind fold had no eligible training selection")
    fold_failures: dict[str, Any] = {}
    for held_out, fold in dict(folds.get("folds") or {}).items():
        metrics = dict((fold.get("held_out_configurations") or {}).get(selected) or {})
        if not metrics.get("passes_registered_floors"):
            fold_failures[str(held_out)] = metrics
    if fold_failures:
        raise ValueError(
            f"Selected configuration fails registered floors on held-out catalogs: "
            f"{sorted(fold_failures)}"
        )
    config = dict(manifest.get("config") or {})
    frozen_runtime_config = dict(config)
    frozen_runtime_config["run_id"] = "assigned_per_run"
    frozen_runtime_config["context_strategies"] = [selected]
    evidence_paths = {
        "run_manifest": manifest_path,
        "summary": summary_path,
        "progress": progress_path,
        "candidates": candidates_path,
        "reviews": reviews_path,
        "token_ledger": token_path,
        "manual_audit": manual_audit_path,
        "collection_folds": collection_folds_path,
    }
    return {
        "schema_version": 1,
        "frozen_at": datetime.now(timezone.utc).isoformat(),
        "runtime_location": "local",
        "calibration_run_id": run_id,
        "configuration_hash": configuration_hash,
        "selected_context_strategy": selected,
        "selection_rule": str(summary.get("selection_rule") or ""),
        "registered_metrics": selected_metrics,
        "manual_precision_floor": manual_precision_floor,
        "manual_audit_metrics": {
            "reviewed_rows": int(audit.get("reviewed_rows") or 0),
            "final_pass_precision": final_pass_precision,
            "dimension_precision": dimension_precision,
        },
        "collection_fold_selection_counts": dict(
            folds.get("selected_configuration_counts") or {}
        ),
        "frozen_runtime_config": frozen_runtime_config,
        "recipe_pack_id": str(manifest.get("recipe_pack_id") or ""),
        "recipe_pack_hash": str(manifest.get("recipe_pack_hash") or ""),
        "bundle_hashes": dict(manifest.get("bundle_hashes") or {}),
        "source_hashes": dict(manifest.get("source_hashes") or {}),
        "evidence": {
            name: {"path": str(path.resolve()), "sha256": _sha256(path)}
            for name, path in evidence_paths.items()
        },
        "blind_boundary": (
            "Use this configuration unchanged for one source-disjoint blind collection. "
            "Do not tune prompts, recipes, validators, thresholds, models, or runtime controls after "
            "observing the blind result."
        ),
    }
