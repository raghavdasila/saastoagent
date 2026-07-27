from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping, Sequence

from .evalset_factory_contracts import ContextStrategy
from .evalset_factory_experiment import ExperimentConfig, ExperimentInputs
from .openapi_loader import NormalizedEndpoint, read_normalized_bundle


@dataclass(frozen=True)
class IsolatedExperimentInputs:
    inputs: ExperimentInputs
    manifest: Mapping[str, Any]


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def _path_key(path: Path, repo_root: Path) -> str:
    try:
        return str(path.relative_to(repo_root))
    except ValueError:
        return str(path)


def _resolved(path: Path, repo_root: Path) -> Path:
    return (path if path.is_absolute() else repo_root / path).resolve()


def _require_object_list(path: Path) -> list[Mapping[str, Any]]:
    value = _read_json(path)
    if not isinstance(value, list) or any(not isinstance(row, Mapping) for row in value):
        raise ValueError(f"Expected a JSON object list at {path}")
    return list(value)


def _task_id(task: Mapping[str, Any], *, origin: Path) -> str:
    value = str(task.get("id") or "")
    if not value:
        raise ValueError(f"Every explicit task requires an ID: {origin}")
    return value


def _register_task(
    values: dict[str, Mapping[str, Any]],
    origins: dict[str, Path],
    task: Mapping[str, Any],
    *,
    origin: Path,
) -> None:
    task_id = _task_id(task, origin=origin)
    previous = values.get(task_id)
    if previous is not None and previous != task:
        raise ValueError(
            f"Conflicting explicit task ID {task_id!r}: {origins[task_id]} versus {origin}"
        )
    values[task_id] = task
    origins[task_id] = origin


def _expected_endpoint_ids(task: Mapping[str, Any]) -> tuple[str, ...]:
    values: list[str] = []
    for endpoint_id in task.get("expected_endpoint_sequence") or []:
        if str(endpoint_id):
            values.append(str(endpoint_id))
    for sequence in task.get("allowed_alternatives") or []:
        if isinstance(sequence, list):
            values.extend(str(endpoint_id) for endpoint_id in sequence if str(endpoint_id))
    return tuple(dict.fromkeys(values))


def _assert_allowed_paths(
    *,
    allowed_paths: Sequence[Path],
    forbidden_paths: Sequence[Path],
) -> None:
    for allowed in allowed_paths:
        for forbidden in forbidden_paths:
            if allowed == forbidden or forbidden in allowed.parents:
                raise ValueError(
                    f"Input path is both allowed and forbidden: {allowed} conflicts with {forbidden}"
                )


def build_isolated_experiment_inputs(
    *,
    repo_root: Path,
    target_id: str,
    target_artifacts_dir: Path,
    target_tasks_path: Path,
    reference_tasks_by_id: Mapping[str, Path],
    reference_artifacts_by_target: Mapping[str, Path],
    source_locations_by_target: Mapping[str, str],
    source_evidence_paths: Sequence[Path],
    forbidden_paths: Sequence[Path],
    implementation_paths: Sequence[Path],
) -> IsolatedExperimentInputs:
    """Build factory inputs from an explicit allow-list without repository task scans."""

    repo_root = repo_root.resolve()
    if not target_id.strip():
        raise ValueError("Isolated factory target_id cannot be empty")
    target_artifacts_dir = _resolved(target_artifacts_dir, repo_root)
    target_tasks_path = _resolved(target_tasks_path, repo_root)
    reference_tasks_by_id = {
        str(task_id): _resolved(path, repo_root)
        for task_id, path in reference_tasks_by_id.items()
    }
    reference_artifacts_by_target = {
        str(reference_target): _resolved(path, repo_root)
        for reference_target, path in reference_artifacts_by_target.items()
    }
    source_evidence_paths = tuple(_resolved(path, repo_root) for path in source_evidence_paths)
    forbidden_paths = tuple(_resolved(path, repo_root) for path in forbidden_paths)
    implementation_paths = tuple(_resolved(path, repo_root) for path in implementation_paths)

    target_normalized_path = target_artifacts_dir / "openapi_normalized.json"
    reference_normalized_paths = {
        reference_target: artifacts_dir / "openapi_normalized.json"
        for reference_target, artifacts_dir in reference_artifacts_by_target.items()
    }
    allowed_paths = (
        target_normalized_path,
        target_tasks_path,
        *reference_tasks_by_id.values(),
        *reference_normalized_paths.values(),
        *source_evidence_paths,
        *implementation_paths,
    )
    _assert_allowed_paths(allowed_paths=allowed_paths, forbidden_paths=forbidden_paths)
    missing = [path for path in allowed_paths if not path.is_file()]
    if missing:
        raise FileNotFoundError(
            "Missing explicit factory inputs: " + ", ".join(str(path) for path in missing)
        )

    target_bundle = read_normalized_bundle(target_artifacts_dir)
    target_endpoint_ids = {endpoint.id for endpoint in target_bundle.endpoints}
    target_tasks = _require_object_list(target_tasks_path)
    source_tasks_by_id: dict[str, Mapping[str, Any]] = {}
    source_task_origins: dict[str, Path] = {}
    for task in target_tasks:
        validation = task.get("validation") or {}
        task_target = str(validation.get("target_id") or "")
        if task_target and task_target != target_id:
            raise ValueError(
                f"Explicit target task {_task_id(task, origin=target_tasks_path)!r} names "
                f"target {task_target!r}, expected {target_id!r}"
            )
        missing_truth = sorted(set(_expected_endpoint_ids(task)) - target_endpoint_ids)
        if missing_truth:
            raise ValueError(
                f"Explicit target task {_task_id(task, origin=target_tasks_path)!r} references "
                f"unknown target endpoints: {missing_truth}"
            )
        _register_task(
            source_tasks_by_id,
            source_task_origins,
            task,
            origin=target_tasks_path,
        )

    reference_endpoints_by_id: dict[str, NormalizedEndpoint] = {
        endpoint.id: endpoint for endpoint in target_bundle.endpoints
    }
    for reference_target, artifacts_dir in reference_artifacts_by_target.items():
        bundle = read_normalized_bundle(artifacts_dir)
        for endpoint in bundle.endpoints:
            previous = reference_endpoints_by_id.get(endpoint.id)
            if previous is not None and previous != endpoint:
                raise ValueError(f"Conflicting explicit reference endpoint ID: {endpoint.id}")
            reference_endpoints_by_id[endpoint.id] = endpoint
        if reference_target not in source_locations_by_target:
            raise ValueError(
                f"Explicit reference target {reference_target!r} requires a source location"
            )

    for requested_task_id, path in reference_tasks_by_id.items():
        matches = [
            task
            for task in _require_object_list(path)
            if str(task.get("id") or "") == requested_task_id
        ]
        if len(matches) != 1:
            raise ValueError(
                f"Expected exactly one explicit reference task {requested_task_id!r} in {path}; "
                f"found {len(matches)}"
            )
        missing_truth = sorted(
            set(_expected_endpoint_ids(matches[0])) - set(reference_endpoints_by_id)
        )
        if missing_truth:
            raise ValueError(
                f"Explicit reference task {requested_task_id!r} references unknown endpoints: "
                f"{missing_truth}"
            )
        _register_task(
            source_tasks_by_id,
            source_task_origins,
            matches[0],
            origin=path,
        )

    source_hashes = {
        _path_key(path, repo_root): _sha256(path)
        for path in dict.fromkeys(allowed_paths)
    }
    inputs = ExperimentInputs(
        bundles={target_id: target_bundle},
        tasks_by_target={target_id: tuple(target_tasks)},
        source_tasks_by_id=source_tasks_by_id,
        source_locations_by_target=dict(source_locations_by_target),
        source_hashes=source_hashes,
        bundle_hashes={target_id: _sha256(target_normalized_path)},
        reference_endpoints_by_id=reference_endpoints_by_id,
    )
    manifest = {
        "schema_version": 1,
        "input_mode": "explicit_allowlist",
        "target_id": target_id,
        "target_tasks_path": str(target_tasks_path),
        "target_task_count": len(target_tasks),
        "reference_task_ids": sorted(reference_tasks_by_id),
        "reference_targets": sorted(reference_artifacts_by_target),
        "allowed_paths": [str(path) for path in dict.fromkeys(allowed_paths)],
        "forbidden_paths": [str(path) for path in forbidden_paths],
        "source_hashes": dict(sorted(source_hashes.items())),
        "bundle_hashes": dict(inputs.bundle_hashes),
    }
    return IsolatedExperimentInputs(inputs=inputs, manifest=manifest)


def experiment_config_from_frozen(
    frozen: Mapping[str, Any],
    *,
    run_id: str,
    target_id: str,
) -> ExperimentConfig:
    values = dict(frozen.get("frozen_runtime_config") or {})
    if not values:
        raise ValueError("Frozen factory configuration lacks frozen_runtime_config")
    return ExperimentConfig(
        run_id=run_id,
        targets=(target_id,),
        generator_model_digest=str(values["generator_model_digest"]),
        reviewer_model_digest=str(values["reviewer_model_digest"]),
        categories=tuple(str(value) for value in values["categories"]),
        context_strategies=tuple(ContextStrategy(str(value)) for value in values["context_strategies"]),
        tasks_per_category=int(values["tasks_per_category"]),
        generator_model=str(values["generator_model"]),
        reviewer_model=str(values["reviewer_model"]),
        ollama_url=str(values["ollama_url"]),
        seed=int(values["seed"]),
        generation_temperature=float(values["generation_temperature"]),
        num_ctx=int(values["num_ctx"]),
        generation_num_predict=int(values["generation_num_predict"]),
        review_num_predict=int(values["review_num_predict"]),
        generation_keep_alive=str(values["generation_keep_alive"]),
        review_keep_alive=str(values["review_keep_alive"]),
        timeout_seconds=float(values["timeout_seconds"]),
        max_generation_attempts=int(values["max_generation_attempts"]),
        max_review_attempts=int(values["max_review_attempts"]),
        endpoint_truth_floor=float(values["endpoint_truth_floor"]),
        category_fidelity_floor=float(values["category_fidelity_floor"]),
        coverage_floor=float(values["coverage_floor"]),
    )


def verify_frozen_factory_sources(
    frozen: Mapping[str, Any],
    *,
    repo_root: Path,
    recipe_path: Path,
    required_source_paths: Sequence[Path],
) -> None:
    repo_root = repo_root.resolve()
    recipe_path = _resolved(recipe_path, repo_root)
    expected_recipe_hash = str(frozen.get("recipe_pack_hash") or "")
    actual_recipe_hash = _sha256(recipe_path)
    if actual_recipe_hash != expected_recipe_hash:
        raise ValueError(
            f"Frozen recipe hash mismatch: {actual_recipe_hash} != {expected_recipe_hash}"
        )
    frozen_sources = dict(frozen.get("source_hashes") or {})
    for source_path in required_source_paths:
        source_path = _resolved(source_path, repo_root)
        key = _path_key(source_path, repo_root)
        expected = str(frozen_sources.get(key) or "")
        if not expected:
            raise ValueError(f"Frozen configuration does not register implementation source: {key}")
        actual = _sha256(source_path)
        if actual != expected:
            raise ValueError(
                f"Frozen implementation hash mismatch for {key}: {actual} != {expected}"
            )
