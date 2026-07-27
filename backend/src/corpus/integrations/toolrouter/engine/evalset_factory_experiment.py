from __future__ import annotations

import hashlib
import json
import math
from collections import Counter
from dataclasses import asdict, dataclass, field, replace
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable, Mapping, Sequence

from .evalset_factory_contracts import (
    QUERY_CATEGORIES,
    ContextStrategy,
    FactoryCandidate,
    RecipePack,
    ReviewVerdict,
    TokenUsage,
)
from .evalset_factory_generation import GenerationResult, GenerationTruth
from .evalset_factory_validation import (
    SemanticReviewResult,
    validate_candidate,
    validate_deterministically,
)
from .ladder_llm import append_jsonl, stable_hash
from .openapi_loader import NormalizedBundle, NormalizedEndpoint, read_normalized_bundle
from .semantic_validation import normalize_query
from .semantic_validation_io import write_json_atomic


EXPERIMENT_SCHEMA_VERSION = 1


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def _read_jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    rows: list[dict[str, Any]] = []
    for line_number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        if not line.strip():
            continue
        value = json.loads(line)
        if not isinstance(value, dict):
            raise ValueError(f"{path}:{line_number} must contain a JSON object")
        rows.append(value)
    return rows


def _register_source_task(
    index: dict[str, Mapping[str, Any]],
    origins: dict[str, str],
    row: Mapping[str, Any],
    *,
    origin: str,
) -> None:
    task_id = str(row.get("id") or "")
    if not task_id:
        return
    existing = index.get(task_id)
    if existing is not None and stable_hash(existing) != stable_hash(row):
        raise ValueError(
            f"Conflicting source task ID {task_id!r} in {origins[task_id]} and {origin}"
        )
    if existing is None:
        index[task_id] = row
        origins[task_id] = origin


@dataclass(frozen=True)
class ExperimentConfig:
    run_id: str
    targets: tuple[str, ...]
    generator_model_digest: str
    reviewer_model_digest: str
    categories: tuple[str, ...] = QUERY_CATEGORIES
    context_strategies: tuple[ContextStrategy, ...] = (
        ContextStrategy.MINIMAL,
        ContextStrategy.ENDPOINT_NEIGHBORHOOD,
        ContextStrategy.FULL_ENDPOINT,
    )
    tasks_per_category: int = 1
    generator_model: str = "gemma4:latest"
    reviewer_model: str = "qwen2.5-coder:7b"
    ollama_url: str = "http://127.0.0.1:11434"
    seed: int = 0
    generation_temperature: float = 0.6
    num_ctx: int = 8192
    generation_num_predict: int = 320
    review_num_predict: int = 480
    generation_keep_alive: str = "0s"
    review_keep_alive: str = "0s"
    timeout_seconds: float = 240.0
    max_generation_attempts: int = 2
    max_review_attempts: int = 2
    endpoint_truth_floor: float = 0.90
    category_fidelity_floor: float = 0.90
    coverage_floor: float = 0.80

    def __post_init__(self) -> None:
        if not self.run_id.strip():
            raise ValueError("Experiment run_id cannot be empty")
        if not self.targets or any(not target.strip() for target in self.targets):
            raise ValueError("Experiment requires at least one non-empty target")
        if not self.categories:
            raise ValueError("Experiment requires at least one category")
        unknown = sorted(set(self.categories) - set(QUERY_CATEGORIES))
        if unknown:
            raise ValueError(f"Unknown evalset categories: {unknown}")
        if not self.context_strategies:
            raise ValueError("Experiment requires at least one context strategy")
        if self.tasks_per_category <= 0:
            raise ValueError("tasks_per_category must be positive")
        if self.max_generation_attempts <= 0 or self.max_review_attempts <= 0:
            raise ValueError("Generation and review attempt limits must be positive")
        if not self.generator_model.strip() or not self.reviewer_model.strip():
            raise ValueError("Generator and reviewer model tags are required")
        if not self.generator_model_digest.strip() or not self.reviewer_model_digest.strip():
            raise ValueError("Generator and reviewer model digests are required")
        if self.generator_model == self.reviewer_model:
            raise ValueError("Generator and reviewer models must be independent")
        if not self.ollama_url.strip():
            raise ValueError("Ollama URL is required")
        if self.generation_temperature < 0:
            raise ValueError("generation_temperature cannot be negative")
        if self.num_ctx <= 0 or self.generation_num_predict <= 0 or self.review_num_predict <= 0:
            raise ValueError("Ollama context and output-token limits must be positive")
        if not self.generation_keep_alive.strip() or not self.review_keep_alive.strip():
            raise ValueError("Ollama keep-alive settings cannot be empty")
        if self.timeout_seconds <= 0:
            raise ValueError("timeout_seconds must be positive")
        for name in ("endpoint_truth_floor", "category_fidelity_floor", "coverage_floor"):
            value = getattr(self, name)
            if not 0 <= value <= 1:
                raise ValueError(f"{name} must be between 0 and 1")

    def to_dict(self) -> dict[str, Any]:
        return {
            "run_id": self.run_id,
            "targets": list(self.targets),
            "categories": list(self.categories),
            "context_strategies": [strategy.value for strategy in self.context_strategies],
            "tasks_per_category": self.tasks_per_category,
            "generator_model": self.generator_model,
            "reviewer_model": self.reviewer_model,
            "generator_model_digest": self.generator_model_digest,
            "reviewer_model_digest": self.reviewer_model_digest,
            "ollama_url": self.ollama_url,
            "seed": self.seed,
            "generation_temperature": self.generation_temperature,
            "num_ctx": self.num_ctx,
            "generation_num_predict": self.generation_num_predict,
            "review_num_predict": self.review_num_predict,
            "generation_keep_alive": self.generation_keep_alive,
            "review_keep_alive": self.review_keep_alive,
            "timeout_seconds": self.timeout_seconds,
            "max_generation_attempts": self.max_generation_attempts,
            "max_review_attempts": self.max_review_attempts,
            "endpoint_truth_floor": self.endpoint_truth_floor,
            "category_fidelity_floor": self.category_fidelity_floor,
            "coverage_floor": self.coverage_floor,
        }


@dataclass(frozen=True)
class ExperimentInputs:
    bundles: Mapping[str, NormalizedBundle]
    tasks_by_target: Mapping[str, tuple[Mapping[str, Any], ...]]
    source_tasks_by_id: Mapping[str, Mapping[str, Any]]
    source_locations_by_target: Mapping[str, str]
    source_hashes: Mapping[str, str]
    bundle_hashes: Mapping[str, str]
    reference_endpoints_by_id: Mapping[str, NormalizedEndpoint] = field(default_factory=dict)

    @classmethod
    def from_repository(cls, repo_root: Path, targets: Sequence[str]) -> "ExperimentInputs":
        bundles: dict[str, NormalizedBundle] = {}
        tasks_by_target: dict[str, tuple[Mapping[str, Any], ...]] = {}
        source_tasks_by_id: dict[str, Mapping[str, Any]] = {}
        source_task_origins: dict[str, str] = {}
        source_hashes: dict[str, str] = {}
        bundle_hashes: dict[str, str] = {}
        for target_id in targets:
            bundle_path = repo_root / "artifacts" / "targets" / target_id / "openapi_normalized.json"
            task_path = repo_root / "data" / "toolrouter_evalset" / "v1" / target_id / "tasks.json"
            if not bundle_path.exists():
                raise FileNotFoundError(f"Missing normalized bundle for {target_id}: {bundle_path}")
            if not task_path.exists():
                raise FileNotFoundError(f"Missing ToolRouter evalset for {target_id}: {task_path}")
            bundles[target_id] = read_normalized_bundle(bundle_path.parent)
            task_rows = _read_json(task_path)
            if not isinstance(task_rows, list):
                raise ValueError(f"Expected a task list in {task_path}")
            if any(not isinstance(row, Mapping) for row in task_rows):
                raise ValueError(f"Every task in {task_path} must be a JSON object")
            tasks_by_target[target_id] = tuple(task_rows)
            for row in task_rows:
                _register_source_task(
                    source_tasks_by_id,
                    source_task_origins,
                    row,
                    origin=str(task_path),
                )
            bundle_hashes[target_id] = _sha256_file(bundle_path)
            source_hashes[str(task_path.relative_to(repo_root))] = _sha256_file(task_path)
            source_hashes[str(bundle_path.relative_to(repo_root))] = bundle_hashes[target_id]

        source_root = repo_root / "data" / "semantic_grag_validation" / "v3"
        for source_task_path in sorted(source_root.glob("*/tasks.json")):
            rows = _read_json(source_task_path)
            if not isinstance(rows, list):
                raise ValueError(f"Expected a task list in {source_task_path}")
            for row in rows:
                if not isinstance(row, Mapping):
                    raise ValueError(f"Every task in {source_task_path} must be a JSON object")
                _register_source_task(
                    source_tasks_by_id,
                    source_task_origins,
                    row,
                    origin=str(source_task_path),
                )
            source_hashes[str(source_task_path.relative_to(repo_root))] = _sha256_file(source_task_path)

        for implementation_path in (
            repo_root / "toolrouter" / "evalset_factory_contracts.py",
            repo_root / "toolrouter" / "evalset_factory_generation.py",
            repo_root / "toolrouter" / "evalset_factory_validation.py",
            repo_root / "toolrouter" / "evalset_factory_experiment.py",
            repo_root / "scripts" / "run_evalset_factory_experiment.py",
        ):
            if not implementation_path.exists():
                raise FileNotFoundError(f"Missing evalset factory implementation owner: {implementation_path}")
            source_hashes[str(implementation_path.relative_to(repo_root))] = _sha256_file(implementation_path)

        source_locations: dict[str, str] = {}
        source_manifest_root = repo_root / "data" / "openapi_targets" / "specs"
        for target_dir in sorted(source_manifest_root.glob("*")):
            manifest_path = target_dir / "source_manifest.json"
            if not manifest_path.exists():
                continue
            manifest = _read_json(manifest_path)
            specs = manifest.get("specs") or []
            if specs:
                location = str(specs[0].get("url") or specs[0].get("path") or "")
                if location:
                    source_locations[target_dir.name] = location
            source_hashes[str(manifest_path.relative_to(repo_root))] = _sha256_file(manifest_path)
        source_locations.setdefault("medusa", "data/openapi/medusa_admin.yaml")

        reference_endpoints_by_id: dict[str, NormalizedEndpoint] = {}
        for normalized_path in sorted(
            (repo_root / "artifacts" / "targets").glob("*/openapi_normalized.json")
        ):
            reference_target = normalized_path.parent.name
            reference_bundle = bundles.get(reference_target)
            if reference_bundle is None:
                reference_bundle = read_normalized_bundle(normalized_path.parent)
            for endpoint in reference_bundle.endpoints:
                reference_endpoints_by_id[endpoint.id] = endpoint
            source_hashes[str(normalized_path.relative_to(repo_root))] = _sha256_file(
                normalized_path
            )

        return cls(
            bundles=bundles,
            tasks_by_target=tasks_by_target,
            source_tasks_by_id=source_tasks_by_id,
            source_locations_by_target=source_locations,
            source_hashes=source_hashes,
            bundle_hashes=bundle_hashes,
            reference_endpoints_by_id=reference_endpoints_by_id,
        )


@dataclass(frozen=True)
class ExperimentPaths:
    run_dir: Path

    @property
    def manifest(self) -> Path:
        return self.run_dir / "run_manifest.json"

    @property
    def progress(self) -> Path:
        return self.run_dir / "progress.json"

    @property
    def candidates(self) -> Path:
        return self.run_dir / "candidates.jsonl"

    @property
    def reviews(self) -> Path:
        return self.run_dir / "reviews.jsonl"

    @property
    def token_ledger(self) -> Path:
        return self.run_dir / "token_ledger.jsonl"

    @property
    def summary_json(self) -> Path:
        return self.run_dir / "summary.json"

    @property
    def summary_markdown(self) -> Path:
        return self.run_dir / "summary.md"


def _task_category(task: Mapping[str, Any]) -> str:
    evalset = task.get("evalset") or {}
    return str(evalset.get("query_category") or "")


def _source_target(task: Mapping[str, Any]) -> str:
    validation = task.get("validation") or {}
    return str(validation.get("target_id") or "")


def _string_sequence(value: Any) -> tuple[str, ...]:
    if not isinstance(value, list):
        return ()
    return tuple(str(item) for item in value if str(item))


def _alternatives(value: Any) -> tuple[tuple[str, ...], ...]:
    if not isinstance(value, list):
        return ()
    return tuple(_string_sequence(item) for item in value if isinstance(item, list))


def _required_params(value: Any) -> dict[str, tuple[str, ...]]:
    if not isinstance(value, Mapping):
        return {}
    return {
        str(endpoint_id): _string_sequence(names)
        for endpoint_id, names in value.items()
        if str(endpoint_id)
    }


def _source_ids(task: Mapping[str, Any]) -> tuple[str, ...]:
    generated = task.get("generated_stress") or {}
    values = generated.get("source_task_ids") or []
    return _string_sequence(values)


def _catalog_evidence(
    *,
    target_id: str,
    scope: str,
    inputs: ExperimentInputs,
) -> dict[str, Any]:
    if scope == "target_catalog":
        return {
            "catalog_complete": True,
            "catalog_scope": scope,
            "checked_target_ids": [target_id],
            "checked_endpoint_count": len(inputs.bundles[target_id].endpoints),
            "normalized_bundle_sha256": {target_id: inputs.bundle_hashes[target_id]},
            "matched_endpoint_ids": [],
        }
    return {
        "catalog_complete": True,
        "catalog_scope": "benchmark_registry",
        "checked_target_ids": sorted(inputs.bundles),
        "checked_endpoint_count": sum(len(bundle.endpoints) for bundle in inputs.bundles.values()),
        "normalized_bundle_sha256": dict(sorted(inputs.bundle_hashes.items())),
        "matched_endpoint_ids": [],
    }


def _endpoint_from_source_task(
    source_task_id: str,
    inputs: ExperimentInputs,
) -> tuple[str, Mapping[str, Any]] | None:
    task = inputs.source_tasks_by_id.get(source_task_id)
    if not task:
        return None
    sequence = _string_sequence(task.get("expected_endpoint_sequence"))
    if not sequence:
        return None
    return sequence[0], task


def task_to_generation_truth(
    *,
    task: Mapping[str, Any],
    target_id: str,
    candidate_id: str,
    inputs: ExperimentInputs,
) -> GenerationTruth:
    category = _task_category(task)
    sequence = _string_sequence(task.get("expected_endpoint_sequence"))
    alternatives = _alternatives(task.get("allowed_alternatives"))
    context = dict(task.get("conversation_context") or {})
    evidence: dict[str, Any] = {
        "source_evalset_task_id": str(task.get("id") or ""),
        "source_evalset_origin": str((task.get("evalset") or {}).get("origin") or ""),
        "source_evalset_freshness": str((task.get("evalset") or {}).get("freshness") or ""),
    }

    if category == "low_lexical_overlap":
        evidence["max_lexical_overlap"] = 0.35
    elif category == "verbose_or_indirect":
        evidence["minimum_words"] = 16
    elif category == "dependent_multi_hop":
        evidence["dependency_fields"] = list(task.get("dependency_fields") or [])
    elif category == "negation_or_exclusion":
        source_ids = _source_ids(task)
        excluded = _endpoint_from_source_task(source_ids[-1], inputs) if source_ids else None
        if excluded:
            evidence["excluded_endpoint_id"] = excluded[0]
            evidence["excluded_capability_query"] = str(excluded[1].get("query") or "")
    elif category in {"context_followup", "pronoun_or_reference", "correction_or_changed_constraint"}:
        if sequence:
            context.setdefault("selected_endpoint_id", sequence[0])
        if category == "correction_or_changed_constraint":
            source_ids = _source_ids(task)
            superseded = _endpoint_from_source_task(source_ids[0], inputs) if source_ids else None
            if superseded:
                context.setdefault("superseded_endpoint_id", superseded[0])
    elif category == "no_tool_target_isolation":
        evidence.update(_catalog_evidence(target_id=target_id, scope="target_catalog", inputs=inputs))
        source_ids = _source_ids(task)
        source = _endpoint_from_source_task(source_ids[0], inputs) if source_ids else None
        if source:
            source_endpoint_id, source_task = source
            foreign_target = _source_target(source_task) or source_endpoint_id.split(":", 1)[0]
            foreign_endpoint = inputs.reference_endpoints_by_id.get(source_endpoint_id)
            capability_description = str(source_task.get("query") or "")
            endpoint_evidence: dict[str, Any] = {}
            if foreign_endpoint is not None:
                capability_description = " ".join(
                    value
                    for value in (
                        f"{foreign_target} {foreign_endpoint.operation_class} capability",
                        foreign_endpoint.summary,
                        foreign_endpoint.description,
                    )
                    if value
                )
                endpoint_evidence = {
                    "source_endpoint_summary": foreign_endpoint.summary,
                    "source_endpoint_description": foreign_endpoint.description,
                    "source_endpoint_operation_class": foreign_endpoint.operation_class,
                    "source_endpoint_resources": list(foreign_endpoint.resources),
                }
            evidence.update(
                {
                    "source_task_id": source_ids[0],
                    "source_endpoint_id": source_endpoint_id,
                    "source_target_id": foreign_target,
                    "source_url": inputs.source_locations_by_target.get(foreign_target, ""),
                    "capability_description": capability_description,
                    **endpoint_evidence,
                }
            )
    elif category == "no_tool_global_catalog":
        catalog_truth = dict(task.get("catalog_ground_truth") or {})
        evidence.update(catalog_truth)
        evidence["catalog_scope"] = "benchmark_registry"
        evidence["catalog_complete"] = bool(catalog_truth.get("catalog_complete"))
        evidence["matched_endpoint_ids"] = []
        capability = catalog_truth.get("external_capability_source") or {}
        evidence["source_url"] = str(capability.get("url") or "")
        evidence["capability_description"] = str(capability.get("capability") or "")

    return GenerationTruth(
        candidate_id=candidate_id,
        target_id=target_id,
        expected_decision=str(task.get("expected_decision_type") or ""),
        expected_endpoint_sequence=sequence,
        allowed_alternatives=alternatives,
        expected_required_params=_required_params(task.get("expected_required_params")),
        provided_params=dict(task.get("provided_params") or {}),
        conversation_context=context,
        external_evidence=evidence,
    )


def _candidate_dict(candidate: FactoryCandidate) -> dict[str, Any]:
    return {
        "candidate_id": candidate.candidate_id,
        "target_id": candidate.target_id,
        "category": candidate.category,
        "query": candidate.query,
        "expected_decision": candidate.expected_decision,
        "expected_endpoint_sequence": list(candidate.expected_endpoint_sequence),
        "allowed_alternatives": [list(value) for value in candidate.allowed_alternatives],
        "expected_required_params": {
            endpoint_id: list(values)
            for endpoint_id, values in candidate.expected_required_params.items()
        },
        "provided_params": dict(candidate.provided_params),
        "conversation_context": dict(candidate.conversation_context),
        "truth_evidence": dict(candidate.truth_evidence),
        "source_endpoint_ids": list(candidate.source_endpoint_ids),
        "generator_model": candidate.generator_model,
        "recipe_hash": candidate.recipe_hash,
        "context_strategy": candidate.context_strategy.value,
        "generation_usage": candidate.generation_usage.to_dict(),
    }


def _verdict_dict(verdict: ReviewVerdict) -> dict[str, Any]:
    return {
        "candidate_id": verdict.candidate_id,
        "deterministic_pass": verdict.deterministic_pass,
        "semantic_pass": verdict.semantic_pass,
        "accepted": verdict.accepted,
        "reasons": list(verdict.reasons),
        "selected_endpoint_ids": list(verdict.selected_endpoint_ids),
        "category_fidelity": verdict.category_fidelity,
        "naturalness": verdict.naturalness,
        "reviewer_model": verdict.reviewer_model,
        "review_usage": verdict.review_usage.to_dict(),
        "review_input_hash": verdict.review_input_hash,
        "review_output_hash": verdict.review_output_hash,
    }


def _semantic_dict(result: SemanticReviewResult) -> dict[str, Any]:
    return {
        "candidate_id": result.candidate_id,
        "passed": result.passed,
        "selected_endpoint_ids": list(result.selected_endpoint_ids),
        "category_fidelity": result.category_fidelity,
        "naturalness": result.naturalness,
        "truth_supported": result.truth_supported,
        "ambiguous": result.ambiguous,
        "reasons": list(result.reasons),
        "reviewer_model": result.reviewer_model,
        "usage": result.usage.to_dict(),
        "incurred_usage": result.incurred_usage.to_dict(),
        "input_hash": result.input_hash,
        "output_hash": result.output_hash,
        "cache_hit": result.cache_hit,
    }


def _endpoint_truth_correct(candidate: FactoryCandidate, result: SemanticReviewResult) -> bool:
    selected = set(result.selected_endpoint_ids)
    if candidate.expected_decision == "ASK_DISAMBIGUATE":
        alternatives = {
            endpoint_id
            for sequence in candidate.allowed_alternatives
            for endpoint_id in sequence
        }
        return result.truth_supported and result.ambiguous and selected == alternatives and len(selected) >= 2
    if candidate.expected_decision in {"NO_TOOL", "ABSTAIN"}:
        return result.truth_supported and not selected
    return result.truth_supported and selected == set(candidate.expected_endpoint_sequence)


class EvalsetFactoryExperiment:
    def __init__(
        self,
        *,
        config: ExperimentConfig,
        recipe_pack: RecipePack,
        recipe_pack_hash: str,
        inputs: ExperimentInputs,
        generator: Any,
        reviewer: Any,
        run_dir: Path,
    ) -> None:
        self.config = config
        self.recipe_pack = recipe_pack
        self.recipe_pack_hash = recipe_pack_hash
        self.inputs = inputs
        self.generator = generator
        self.reviewer = reviewer
        self.paths = ExperimentPaths(run_dir)
        self.configuration_hash = stable_hash(
            {
                "schema_version": EXPERIMENT_SCHEMA_VERSION,
                "config": config.to_dict(),
                "recipe_pack_hash": recipe_pack_hash,
                "source_hashes": dict(sorted(inputs.source_hashes.items())),
                "bundle_hashes": dict(sorted(inputs.bundle_hashes.items())),
            }
        )
        self._initialize_or_verify()

    def _initialize_or_verify(self) -> None:
        self.paths.run_dir.mkdir(parents=True, exist_ok=True)
        manifest = {
            "schema_version": EXPERIMENT_SCHEMA_VERSION,
            "run_id": self.config.run_id,
            "created_at": _utc_now(),
            "runtime_location": "local",
            "ollama_url": self.config.ollama_url,
            "config": self.config.to_dict(),
            "recipe_pack_id": self.recipe_pack.pack_id,
            "recipe_pack_hash": self.recipe_pack_hash,
            "source_hashes": dict(sorted(self.inputs.source_hashes.items())),
            "bundle_hashes": dict(sorted(self.inputs.bundle_hashes.items())),
            "configuration_hash": self.configuration_hash,
            "claim_boundary": (
                "Known-catalog calibration using consumed regression evidence; "
                "not a fresh generalization result."
            ),
        }
        if self.paths.manifest.exists():
            existing = _read_json(self.paths.manifest)
            if existing.get("configuration_hash") != self.configuration_hash:
                raise ValueError(
                    "Cannot resume evalset factory run: configuration/source hash changed "
                    f"({existing.get('configuration_hash')} != {self.configuration_hash})"
                )
        else:
            write_json_atomic(self.paths.manifest, manifest)
        if self.paths.progress.exists():
            progress = _read_json(self.paths.progress)
            if progress.get("configuration_hash") != self.configuration_hash:
                raise ValueError("Cannot resume evalset factory run with mismatched progress hash")
        else:
            self._write_progress({})

    def _write_progress(self, completed: Mapping[str, Any]) -> None:
        write_json_atomic(
            self.paths.progress,
            {
                "schema_version": EXPERIMENT_SCHEMA_VERSION,
                "run_id": self.config.run_id,
                "configuration_hash": self.configuration_hash,
                "updated_at": _utc_now(),
                "completed": dict(completed),
            },
        )

    def _selected_tasks(self) -> list[tuple[str, str, Mapping[str, Any]]]:
        selected: list[tuple[str, str, Mapping[str, Any]]] = []
        for target_id in self.config.targets:
            rows = self.inputs.tasks_by_target.get(target_id)
            if rows is None:
                raise KeyError(f"No evalset tasks loaded for target {target_id!r}")
            for category in self.config.categories:
                matches = sorted(
                    (task for task in rows if _task_category(task) == category),
                    key=lambda task: str(task.get("id") or ""),
                )
                for task in matches[: self.config.tasks_per_category]:
                    selected.append((target_id, category, task))
        return selected

    def expected_keys(self) -> list[str]:
        values: list[str] = []
        for target_id, category, task in self._selected_tasks():
            for strategy in self.config.context_strategies:
                values.append(self._completion_key(target_id, category, task, strategy))
        return values

    def _completion_key(
        self,
        target_id: str,
        category: str,
        task: Mapping[str, Any],
        strategy: ContextStrategy,
    ) -> str:
        source_task_id = str(task.get("id") or "")
        recipe = self.recipe_pack.by_category(category)
        identity = {
            "target_id": target_id,
            "category": category,
            "source_task_id": source_task_id,
            "source_task_hash": stable_hash(task),
            "strategy": strategy.value,
            "recipe_hash": stable_hash(asdict(recipe)),
            "generator_model": self.config.generator_model,
            "generator_model_digest": self.config.generator_model_digest,
            "reviewer_model": self.config.reviewer_model,
            "reviewer_model_digest": self.config.reviewer_model_digest,
            "seed": self.config.seed,
            "generation_temperature": self.config.generation_temperature,
            "num_ctx": self.config.num_ctx,
            "generation_num_predict": self.config.generation_num_predict,
            "review_num_predict": self.config.review_num_predict,
            "generation_keep_alive": self.config.generation_keep_alive,
            "review_keep_alive": self.config.review_keep_alive,
            "timeout_seconds": self.config.timeout_seconds,
            "max_generation_attempts": self.config.max_generation_attempts,
            "max_review_attempts": self.config.max_review_attempts,
            "bundle_hash": self.inputs.bundle_hashes[target_id],
        }
        return f"{target_id}/{category}/{source_task_id}/{strategy.value}/{stable_hash(identity)[:12]}"

    def run(self, *, stop_after_completed_keys: int | None = None) -> dict[str, Any]:
        progress = _read_json(self.paths.progress)
        completed: dict[str, Any] = dict(progress.get("completed") or {})
        newly_completed = 0
        for target_id, category, task in self._selected_tasks():
            for strategy in self.config.context_strategies:
                key = self._completion_key(target_id, category, task, strategy)
                if key in completed:
                    continue
                terminal = self._run_key(
                    completion_key=key,
                    target_id=target_id,
                    category=category,
                    task=task,
                    strategy=strategy,
                )
                completed[key] = terminal
                self._write_progress(completed)
                newly_completed += 1
                self.write_summary()
                if stop_after_completed_keys is not None and newly_completed >= stop_after_completed_keys:
                    return self.write_summary()
        return self.write_summary()

    def _run_key(
        self,
        *,
        completion_key: str,
        target_id: str,
        category: str,
        task: Mapping[str, Any],
        strategy: ContextStrategy,
    ) -> dict[str, Any]:
        bundle = self.inputs.bundles[target_id]
        recipe = self.recipe_pack.by_category(category)
        recipe_hash = stable_hash(asdict(recipe))
        source_task_id = str(task.get("id") or "")
        last_status = "generation_failed"
        last_error = ""
        prior_feedback: tuple[str, ...] = ()
        prior_query = ""
        candidate_identity = stable_hash(
            {
                "target_id": target_id,
                "category": category,
                "source_task_id": source_task_id,
                "source_task_hash": stable_hash(task),
                "strategy": strategy.value,
                "recipe_hash": recipe_hash,
                "generator_model": self.config.generator_model,
                "generator_model_digest": self.config.generator_model_digest,
                "seed": self.config.seed,
                "generation_temperature": self.config.generation_temperature,
                "num_ctx": self.config.num_ctx,
                "generation_num_predict": self.config.generation_num_predict,
                "generation_keep_alive": self.config.generation_keep_alive,
            }
        )[:20]
        for generation_attempt in range(1, self.config.max_generation_attempts + 1):
            candidate_id = f"efc_{candidate_identity}__a{generation_attempt}"
            truth = task_to_generation_truth(
                task=task,
                target_id=target_id,
                candidate_id=candidate_id,
                inputs=self.inputs,
            )
            if prior_feedback:
                evidence = dict(truth.external_evidence or {})
                evidence["prior_attempt_query"] = prior_query
                evidence["prior_attempt_rejection_reasons"] = [
                    reason[:300] for reason in prior_feedback[:5]
                ]
                truth = replace(truth, external_evidence=evidence)
            try:
                generation: GenerationResult = self.generator.generate_candidate(
                    recipe=recipe,
                    bundle=bundle,
                    truth=truth,
                    strategy=strategy,
                    recipe_hash=recipe_hash,
                )
            except Exception as exc:  # terminal evidence is more useful than aborting independent rows
                last_error = f"{type(exc).__name__}: {exc}"
                append_jsonl(
                    self.paths.candidates,
                    {
                        "schema_version": EXPERIMENT_SCHEMA_VERSION,
                        "recorded_at": _utc_now(),
                        "completion_key": completion_key,
                        "target_id": target_id,
                        "category": category,
                        "source_task_id": source_task_id,
                        "context_strategy": strategy.value,
                        "generation_attempt": generation_attempt,
                        "candidate_id": candidate_id,
                        "status": "generation_error",
                        "error": last_error,
                    },
                )
                continue

            candidate = generation.candidate
            deterministic = validate_deterministically(candidate, recipe, bundle)
            append_jsonl(
                self.paths.candidates,
                {
                    "schema_version": EXPERIMENT_SCHEMA_VERSION,
                    "recorded_at": _utc_now(),
                    "completion_key": completion_key,
                    "target_id": target_id,
                    "category": category,
                    "source_task_id": source_task_id,
                    "context_strategy": strategy.value,
                    "generation_attempt": generation_attempt,
                    "status": "generated",
                    "candidate": _candidate_dict(candidate),
                    "generation": {
                        "input_hash": generation.input_hash,
                        "output_hash": generation.output_hash,
                        "cache_hit": generation.cache_hit,
                        "strategy_note": generation.strategy_note,
                        "usage": generation.usage.to_dict(),
                        "incurred_usage": generation.incurred_usage.to_dict(),
                    },
                    "deterministic_validation": {
                        "passed": deterministic.passed,
                        "reasons": list(deterministic.reasons),
                    },
                },
            )
            self._append_token_row(
                completion_key=completion_key,
                candidate_id=candidate_id,
                target_id=target_id,
                category=category,
                strategy=strategy,
                stage="generation",
                attempt=generation_attempt,
                usage=generation.usage,
                incurred_usage=generation.incurred_usage,
                cache_hit=generation.cache_hit,
            )
            if not deterministic.passed:
                verdict = validate_candidate(
                    candidate,
                    recipe,
                    bundle,
                    semantic_review=None,
                )
                append_jsonl(
                    self.paths.reviews,
                    {
                        "schema_version": EXPERIMENT_SCHEMA_VERSION,
                        "recorded_at": _utc_now(),
                        "completion_key": completion_key,
                        "target_id": target_id,
                        "category": category,
                        "source_task_id": source_task_id,
                        "context_strategy": strategy.value,
                        "generation_attempt": generation_attempt,
                        "candidate_id": candidate_id,
                        "status": "deterministic_reject",
                        "endpoint_truth_correct": False,
                        "verdict": _verdict_dict(verdict),
                    },
                )
                last_status = "deterministic_reject"
                last_error = "; ".join(deterministic.reasons)
                prior_feedback = deterministic.reasons
                prior_query = candidate.query
                continue

            semantic: SemanticReviewResult | None = None
            for review_attempt in range(1, self.config.max_review_attempts + 1):
                try:
                    semantic = self.reviewer.review_candidate(
                        candidate=candidate,
                        recipe=recipe,
                        bundle=bundle,
                    )
                except Exception as exc:
                    last_error = f"{type(exc).__name__}: {exc}"
                    append_jsonl(
                        self.paths.reviews,
                        {
                            "schema_version": EXPERIMENT_SCHEMA_VERSION,
                            "recorded_at": _utc_now(),
                            "completion_key": completion_key,
                            "target_id": target_id,
                            "category": category,
                            "source_task_id": source_task_id,
                            "context_strategy": strategy.value,
                            "generation_attempt": generation_attempt,
                            "review_attempt": review_attempt,
                            "candidate_id": candidate_id,
                            "status": "semantic_review_error",
                            "error": last_error,
                        },
                    )
                    continue
                self._append_token_row(
                    completion_key=completion_key,
                    candidate_id=candidate_id,
                    target_id=target_id,
                    category=category,
                    strategy=strategy,
                    stage="semantic_review",
                    attempt=review_attempt,
                    usage=semantic.usage,
                    incurred_usage=semantic.incurred_usage,
                    cache_hit=semantic.cache_hit,
                )
                break

            if semantic is None:
                last_status = "semantic_review_failed"
                continue
            verdict = validate_candidate(
                candidate,
                recipe,
                bundle,
                semantic_review=semantic,
            )
            endpoint_truth_correct = _endpoint_truth_correct(candidate, semantic)
            append_jsonl(
                self.paths.reviews,
                {
                    "schema_version": EXPERIMENT_SCHEMA_VERSION,
                    "recorded_at": _utc_now(),
                    "completion_key": completion_key,
                    "target_id": target_id,
                    "category": category,
                    "source_task_id": source_task_id,
                    "context_strategy": strategy.value,
                    "generation_attempt": generation_attempt,
                    "candidate_id": candidate_id,
                    "status": "accepted" if verdict.accepted else "semantic_reject",
                    "endpoint_truth_correct": endpoint_truth_correct,
                    "semantic_review": _semantic_dict(semantic),
                    "verdict": _verdict_dict(verdict),
                },
            )
            last_status = "accepted" if verdict.accepted else "semantic_reject"
            last_error = "; ".join(verdict.reasons)
            if verdict.accepted:
                return {
                    "status": "accepted",
                    "candidate_id": candidate_id,
                    "attempts": generation_attempt,
                    "completed_at": _utc_now(),
                }
            prior_feedback = verdict.reasons or ("semantic_endpoint_or_category_truth_mismatch",)
            prior_query = candidate.query

        return {
            "status": last_status,
            "attempts": self.config.max_generation_attempts,
            "error": last_error,
            "completed_at": _utc_now(),
        }

    def _append_token_row(
        self,
        *,
        completion_key: str,
        candidate_id: str,
        target_id: str,
        category: str,
        strategy: ContextStrategy,
        stage: str,
        attempt: int,
        usage: TokenUsage,
        incurred_usage: TokenUsage,
        cache_hit: bool,
    ) -> None:
        append_jsonl(
            self.paths.token_ledger,
            {
                "schema_version": EXPERIMENT_SCHEMA_VERSION,
                "recorded_at": _utc_now(),
                "completion_key": completion_key,
                "candidate_id": candidate_id,
                "target_id": target_id,
                "category": category,
                "context_strategy": strategy.value,
                "stage": stage,
                "attempt": attempt,
                "model": (
                    self.config.generator_model if stage == "generation" else self.config.reviewer_model
                ),
                "cache_hit": cache_hit,
                "usage": usage.to_dict(),
                "incurred_usage": incurred_usage.to_dict(),
            },
        )

    def write_summary(self) -> dict[str, Any]:
        expected_keys = self.expected_keys()
        progress = _read_json(self.paths.progress)
        completed = dict(progress.get("completed") or {})
        candidates = _read_jsonl(self.paths.candidates)
        reviews = _read_jsonl(self.paths.reviews)
        tokens = _read_jsonl(self.paths.token_ledger)
        configurations: dict[str, dict[str, Any]] = {}
        for strategy in self.config.context_strategies:
            strategy_name = strategy.value
            strategy_expected = [
                key for key in expected_keys if f"/{strategy_name}/" in key
            ]
            strategy_completed = {
                key: value
                for key, value in completed.items()
                if f"/{strategy_name}/" in key
            }
            strategy_candidates = [
                row
                for row in candidates
                if row.get("context_strategy") == strategy_name and row.get("status") == "generated"
            ]
            strategy_reviews = [
                row
                for row in reviews
                if row.get("context_strategy") == strategy_name
                and row.get("status") in {"accepted", "semantic_reject"}
            ]
            strategy_tokens = [
                row for row in tokens if row.get("context_strategy") == strategy_name
            ]
            accepted_keys = {
                key for key, value in strategy_completed.items() if value.get("status") == "accepted"
            }
            accepted_candidate_ids = {
                key: str(value.get("candidate_id") or "")
                for key, value in strategy_completed.items()
                if value.get("status") == "accepted"
            }
            accepted_reviews = [
                row
                for row in strategy_reviews
                if row.get("status") == "accepted"
                and str(row.get("candidate_id") or "")
                == accepted_candidate_ids.get(str(row.get("completion_key") or ""))
            ]
            reviewed_attempts = len(strategy_reviews)
            attempt_endpoint_correct = sum(
                bool(row.get("endpoint_truth_correct")) for row in strategy_reviews
            )
            attempt_category_correct = sum(
                bool((row.get("semantic_review") or {}).get("category_fidelity"))
                for row in strategy_reviews
            )
            accepted_reviewed = len(accepted_reviews)
            endpoint_correct = sum(bool(row.get("endpoint_truth_correct")) for row in accepted_reviews)
            category_correct = sum(
                bool((row.get("semantic_review") or {}).get("category_fidelity"))
                for row in accepted_reviews
            )
            accepted_queries = [
                str((row.get("candidate") or {}).get("query") or "")
                for row in strategy_candidates
                if row.get("completion_key") in accepted_keys
                and str((row.get("candidate") or {}).get("candidate_id") or "")
                == str(strategy_completed[row.get("completion_key")].get("candidate_id") or "")
            ]
            normalized_queries = [normalize_query(value) for value in accepted_queries]
            duplicate_count = sum(count - 1 for count in Counter(normalized_queries).values() if count > 1)
            generation_tokens = sum(
                int((row.get("usage") or {}).get("total_tokens") or 0)
                for row in strategy_tokens
                if row.get("stage") == "generation"
            )
            review_tokens = sum(
                int((row.get("usage") or {}).get("total_tokens") or 0)
                for row in strategy_tokens
                if row.get("stage") == "semantic_review"
            )
            incurred_generation = sum(
                int((row.get("incurred_usage") or {}).get("total_tokens") or 0)
                for row in strategy_tokens
                if row.get("stage") == "generation"
            )
            incurred_review = sum(
                int((row.get("incurred_usage") or {}).get("total_tokens") or 0)
                for row in strategy_tokens
                if row.get("stage") == "semantic_review"
            )
            total_tokens = generation_tokens + review_tokens
            total_incurred = incurred_generation + incurred_review
            completed_count = len(strategy_completed)
            accepted_count = len(accepted_keys)
            retry_keys = sum(
                int(value.get("attempts") or 0) > 1 for value in strategy_completed.values()
            )
            metrics = {
                "expected_keys": len(strategy_expected),
                "completed_keys": completed_count,
                "accepted_keys": accepted_count,
                "candidate_attempts": len(strategy_candidates),
                "semantic_reviews": reviewed_attempts,
                "accepted_semantic_reviews": accepted_reviewed,
                "accepted_correct_keys": endpoint_correct,
                "endpoint_truth_precision": (
                    endpoint_correct / accepted_reviewed if accepted_reviewed else 0.0
                ),
                "category_fidelity": (
                    category_correct / accepted_reviewed if accepted_reviewed else 0.0
                ),
                "semantic_attempt_endpoint_precision": (
                    attempt_endpoint_correct / reviewed_attempts if reviewed_attempts else 0.0
                ),
                "semantic_attempt_category_fidelity": (
                    attempt_category_correct / reviewed_attempts if reviewed_attempts else 0.0
                ),
                "acceptance_yield": accepted_count / len(strategy_candidates) if strategy_candidates else 0.0,
                "coverage": accepted_count / len(strategy_expected) if strategy_expected else 0.0,
                "duplication_rate": duplicate_count / accepted_count if accepted_count else 0.0,
                "retry_rate": retry_keys / completed_count if completed_count else 0.0,
                "generation_tokens": generation_tokens,
                "review_tokens": review_tokens,
                "offline_tokens": total_tokens,
                "generation_tokens_incurred": incurred_generation,
                "review_tokens_incurred": incurred_review,
                "offline_tokens_incurred": total_incurred,
                "tokens_per_candidate": total_tokens / len(strategy_candidates) if strategy_candidates else None,
                "tokens_per_accepted": total_tokens / accepted_count if accepted_count else None,
                "tokens_per_accepted_correct": total_tokens / endpoint_correct if endpoint_correct else None,
            }
            metrics["passes_registered_floors"] = (
                metrics["endpoint_truth_precision"] >= self.config.endpoint_truth_floor
                and metrics["category_fidelity"] >= self.config.category_fidelity_floor
                and metrics["coverage"] >= self.config.coverage_floor
            )
            configurations[strategy_name] = metrics

        pareto = _pareto_frontier(configurations)
        eligible = [
            name for name in pareto if configurations[name]["passes_registered_floors"]
        ]
        chosen = min(
            eligible,
            key=lambda name: (
                configurations[name]["tokens_per_accepted_correct"]
                if configurations[name]["tokens_per_accepted_correct"] is not None
                else math.inf,
                name,
            ),
            default=None,
        )
        summary = {
            "schema_version": EXPERIMENT_SCHEMA_VERSION,
            "run_id": self.config.run_id,
            "configuration_hash": self.configuration_hash,
            "updated_at": _utc_now(),
            "expected_completion_keys": len(expected_keys),
            "completed_keys": len(completed),
            "terminal_status_counts": dict(
                sorted(Counter(str(value.get("status") or "unknown") for value in completed.values()).items())
            ),
            "configurations": configurations,
            "pareto_frontier": pareto,
            "selected_configuration": chosen,
            "selection_rule": (
                "Lowest offline tokens per accepted-correct row among Pareto configurations "
                "whose final accepted set passes endpoint-truth, category-fidelity, and coverage floors. "
                "Rejected semantic attempts are reported separately as generator diagnostics."
            ),
            "metric_definitions": {
                "endpoint_truth_precision": (
                    "Endpoint-truth precision on terminal candidates in the final accepted set."
                ),
                "category_fidelity": (
                    "Category-fidelity precision on terminal candidates in the final accepted set."
                ),
                "semantic_attempt_endpoint_precision": (
                    "Endpoint-truth precision across all semantically reviewed generation attempts, "
                    "including attempts later rejected or retried."
                ),
                "tokens_per_accepted_correct": (
                    "All intrinsic generation and semantic-review tokens divided by final accepted "
                    "endpoint-correct candidates."
                ),
            },
            "claim_boundary": (
                "Automated calibration on consumed regression evidence. Final accepted-set precision means "
                "deterministic gates plus independent local semantic review; it is not human gold and still "
                "requires a manual audit before freezing."
            ),
            "per_target_category": _group_metrics(expected_keys, completed, reviews, tokens),
        }
        write_json_atomic(self.paths.summary_json, summary)
        self.paths.summary_markdown.write_text(_summary_markdown(summary), encoding="utf-8")
        return summary


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


def _group_metrics(
    expected_keys: Sequence[str],
    completed: Mapping[str, Mapping[str, Any]],
    reviews: Sequence[Mapping[str, Any]],
    token_rows: Sequence[Mapping[str, Any]],
) -> dict[str, Any]:
    expected: Counter[tuple[str, str]] = Counter()
    for key in expected_keys:
        parts = key.split("/")
        expected[(parts[0], parts[1])] += 1
    completed_groups: Counter[tuple[str, str]] = Counter()
    accepted_groups: Counter[tuple[str, str]] = Counter()
    accepted_candidate_ids: dict[str, str] = {}
    for key, value in completed.items():
        parts = key.split("/")
        group = (parts[0], parts[1])
        completed_groups[group] += 1
        if value.get("status") == "accepted":
            accepted_groups[group] += 1
            accepted_candidate_ids[key] = str(value.get("candidate_id") or "")
    reviewed_attempt_groups: Counter[tuple[str, str]] = Counter()
    attempt_endpoint_groups: Counter[tuple[str, str]] = Counter()
    attempt_fidelity_groups: Counter[tuple[str, str]] = Counter()
    accepted_review_groups: Counter[tuple[str, str]] = Counter()
    accepted_endpoint_groups: Counter[tuple[str, str]] = Counter()
    accepted_fidelity_groups: Counter[tuple[str, str]] = Counter()
    for row in reviews:
        if row.get("status") not in {"accepted", "semantic_reject"}:
            continue
        group = (str(row.get("target_id")), str(row.get("category")))
        reviewed_attempt_groups[group] += 1
        attempt_endpoint_groups[group] += bool(row.get("endpoint_truth_correct"))
        attempt_fidelity_groups[group] += bool(
            (row.get("semantic_review") or {}).get("category_fidelity")
        )
        completion_key = str(row.get("completion_key") or "")
        if (
            row.get("status") == "accepted"
            and str(row.get("candidate_id") or "") == accepted_candidate_ids.get(completion_key)
        ):
            accepted_review_groups[group] += 1
            accepted_endpoint_groups[group] += bool(row.get("endpoint_truth_correct"))
            accepted_fidelity_groups[group] += bool(
                (row.get("semantic_review") or {}).get("category_fidelity")
            )
    token_groups: Counter[tuple[str, str]] = Counter()
    incurred_token_groups: Counter[tuple[str, str]] = Counter()
    for row in token_rows:
        group = (str(row.get("target_id")), str(row.get("category")))
        token_groups[group] += int((row.get("usage") or {}).get("total_tokens") or 0)
        incurred_token_groups[group] += int(
            (row.get("incurred_usage") or {}).get("total_tokens") or 0
        )
    result: dict[str, Any] = {}
    for group in sorted(expected):
        target_id, category = group
        reviewed_attempts = reviewed_attempt_groups[group]
        accepted_reviews = accepted_review_groups[group]
        accepted = accepted_groups[group]
        result[f"{target_id}/{category}"] = {
            "expected": expected[group],
            "completed": completed_groups[group],
            "accepted": accepted,
            "coverage": accepted / expected[group],
            "endpoint_truth_precision": (
                accepted_endpoint_groups[group] / accepted_reviews if accepted_reviews else 0.0
            ),
            "category_fidelity": (
                accepted_fidelity_groups[group] / accepted_reviews if accepted_reviews else 0.0
            ),
            "semantic_attempt_endpoint_precision": (
                attempt_endpoint_groups[group] / reviewed_attempts if reviewed_attempts else 0.0
            ),
            "semantic_attempt_category_fidelity": (
                attempt_fidelity_groups[group] / reviewed_attempts if reviewed_attempts else 0.0
            ),
            "offline_tokens": token_groups[group],
            "offline_tokens_incurred": incurred_token_groups[group],
        }
    return result


def _summary_markdown(summary: Mapping[str, Any]) -> str:
    lines = [
        f"# Evalset Factory Run `{summary['run_id']}`",
        "",
        f"- Completed: {summary['completed_keys']} / {summary['expected_completion_keys']} keys",
        f"- Selected configuration: {summary.get('selected_configuration') or 'none yet'}",
        f"- Pareto frontier: {', '.join(summary.get('pareto_frontier') or []) or 'none yet'}",
        f"- Configuration hash: `{summary['configuration_hash']}`",
        "",
        "## Configuration metrics",
        "",
        "| Strategy | Accepted truth | Accepted category | Attempt truth | Coverage | Accepted | Offline tokens | Tokens / accepted-correct | Floors |",
        "|---|---:|---:|---:|---:|---:|---:|---:|---|",
    ]
    for name, metrics in summary.get("configurations", {}).items():
        token_ratio = metrics.get("tokens_per_accepted_correct")
        lines.append(
            "| {name} | {truth:.3f} | {fidelity:.3f} | {attempt_truth:.3f} | {coverage:.3f} | {accepted} | "
            "{tokens} | {ratio} | {floors} |".format(
                name=name,
                truth=metrics["endpoint_truth_precision"],
                fidelity=metrics["category_fidelity"],
                attempt_truth=metrics["semantic_attempt_endpoint_precision"],
                coverage=metrics["coverage"],
                accepted=metrics["accepted_keys"],
                tokens=metrics["offline_tokens"],
                ratio=f"{token_ratio:.1f}" if token_ratio is not None else "n/a",
                floors="pass" if metrics["passes_registered_floors"] else "fail",
            )
        )
    lines.extend(
        [
            "",
            "## Claim boundary",
            "",
            str(summary["claim_boundary"]),
            "",
        ]
    )
    return "\n".join(lines)
