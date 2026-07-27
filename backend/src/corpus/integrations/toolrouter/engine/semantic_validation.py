from __future__ import annotations

import hashlib
import re
import unicodedata
from collections import Counter, defaultdict
from copy import deepcopy
from dataclasses import dataclass
from typing import Any, Iterable

from .semantic_outcomes import TOOLROUTER_OUTCOMES


SCHEMA_VERSION = 1

EXPECTED_BEHAVIOR_BY_DECISION = {
    "ROUTE": "route",
    "ASK_DISAMBIGUATE": "ask_disambiguation",
    "ASK_PARAM": "ask_required_input",
    "NO_TOOL": "no_tool",
    "ABSTAIN": "abstain_insufficient_evidence",
    "BLOCK_UNSAFE": "block_unsafe",
    "ASK_POLICY": "ask_policy",
}

SEMANTIC_RESPONSIBILITY_BY_DECISION = {
    "ROUTE": "route_and_rank",
    "ASK_DISAMBIGUATE": "abstain_and_surface_candidates",
    "ASK_PARAM": "ask_required_input",
    "NO_TOOL": "no_tool",
    "ABSTAIN": "abstain_insufficient_evidence",
    "BLOCK_UNSAFE": "downstream_only",
    "ASK_POLICY": "downstream_only",
}

SPLIT_NAMES = ("train", "dev", "holdout")
SPLIT_WEIGHTS = {"train": 0.6, "dev": 0.2, "holdout": 0.2}
EVALUATION_ONLY_SPLIT_WEIGHTS = {"train": 0.0, "dev": 0.5, "holdout": 0.5}

REQUIRED_TAXONOMY_VALUES = {
    "language_form": (
        "exact_spec_like",
        "paraphrase",
        "no_exact_natural_language",
        "low_overlap_natural_language",
        "contextual_natural_language",
        "ordinary_natural_language",
        "verbose_or_indirect",
        "typo_or_noisy",
        "negation_or_exclusion",
    ),
    "intent_shape": (
        "single_concrete_intent",
        "underspecified_intent",
        "ambiguous_sibling_intents",
        "conflicting_constraints",
        "independent_multi_intent",
        "ordered_multi_intent",
        "policy_conditional_intent",
        "destructive_intent",
        "out_of_domain_intent",
        "insufficient_evidence",
    ),
    "conversation_state": (
        "standalone",
        "contextual_followup",
        "pronoun_or_reference",
        "correction_or_changed_constraint",
        "recovery_missing_information",
    ),
    "expected_behavior": (
        "route",
        "ask_disambiguation",
        "no_tool",
        "ask_required_input",
        "abstain_insufficient_evidence",
    ),
}

ALLOWED_TAXONOMY_VALUES = {
    **REQUIRED_TAXONOMY_VALUES,
    "expected_behavior": (
        *REQUIRED_TAXONOMY_VALUES["expected_behavior"],
        "block_unsafe",
        "ask_policy",
    ),
}


@dataclass(frozen=True)
class ValidationTaxonomy:
    language_form: str
    intent_shape: str
    conversation_state: str
    expected_behavior: str
    structural_pressures: tuple[str, ...]

    def to_dict(self) -> dict[str, Any]:
        return {
            "language_form": self.language_form,
            "intent_shape": self.intent_shape,
            "conversation_state": self.conversation_state,
            "expected_behavior": self.expected_behavior,
            "structural_pressures": list(self.structural_pressures),
        }


def task_query(task: dict[str, Any]) -> str:
    return str(task.get("router_query") or task.get("query") or "").strip()


def normalize_query(query: str) -> str:
    normalized = unicodedata.normalize("NFKC", str(query or "")).casefold()
    return " ".join(re.findall(r"\w+", normalized, flags=re.UNICODE))


def query_fingerprint(query: str) -> str:
    normalized = normalize_query(query)
    return hashlib.sha256(normalized.encode("utf-8")).hexdigest()


def _string_list(values: Iterable[Any]) -> list[str]:
    return [str(value) for value in values if str(value)]


def expected_endpoint_sequences(task: dict[str, Any]) -> list[list[str]]:
    sequences: list[list[str]] = []
    expected = _string_list(task.get("expected_endpoint_sequence", []) or [])
    if expected:
        sequences.append(expected)
    for value in task.get("allowed_alternatives", []) or []:
        sequence = _string_list(value if isinstance(value, list) else [value])
        if sequence and sequence not in sequences:
            sequences.append(sequence)
    return sequences


def _source_task_ids(task: dict[str, Any]) -> list[str]:
    source = task.get("semantic_graph_source")
    values: list[str] = []
    if isinstance(source, dict):
        if source.get("source_task_id"):
            values.append(str(source["source_task_id"]))
        values.extend(_string_list(source.get("source_task_ids", []) or []))
    validation = task.get("validation")
    if isinstance(validation, dict):
        values.extend(_string_list(validation.get("source_task_ids", []) or []))
    if not values and task.get("id"):
        values.append(str(task["id"]))
    return list(dict.fromkeys(values))


def _source_keys(task: dict[str, Any], *, target_id: str, source_name: str) -> list[str]:
    source = task.get("semantic_graph_source")
    if isinstance(source, dict):
        explicit_source_keys = _string_list(source.get("source_keys", []) or [])
        if explicit_source_keys:
            return list(dict.fromkeys(explicit_source_keys))
    values = [f"{target_id}|{source_name}|{task_id}" for task_id in _source_task_ids(task)]
    if values:
        return values
    provenance = task.get("provenance")
    if isinstance(provenance, dict):
        endpoint_key = "|".join(
            str(provenance.get(name) or "")
            for name in ("source", "method", "path", "operationId")
        )
        if endpoint_key.strip("|"):
            return [f"{target_id}|openapi|{endpoint_key}"]
    raise ValueError(f"Task {task.get('id')!r} has no source identity")


def _taxonomy_with_overrides(
    taxonomy: ValidationTaxonomy,
    overrides: dict[str, Any] | None,
) -> ValidationTaxonomy:
    if not overrides:
        return taxonomy
    unsupported = sorted(
        set(overrides) - {"language_form", "intent_shape", "conversation_state", "structural_pressures"}
    )
    if unsupported:
        raise ValueError(f"Unsupported validation taxonomy overrides: {unsupported}")
    values = taxonomy.to_dict()
    for dimension in ("language_form", "intent_shape", "conversation_state"):
        if dimension not in overrides:
            continue
        value = str(overrides[dimension])
        if value not in ALLOWED_TAXONOMY_VALUES[dimension]:
            raise ValueError(f"Unsupported {dimension} taxonomy value: {value}")
        values[dimension] = value
    if "structural_pressures" in overrides:
        values["structural_pressures"] = sorted(set(_string_list(overrides["structural_pressures"])))
    return ValidationTaxonomy(
        language_form=str(values["language_form"]),
        intent_shape=str(values["intent_shape"]),
        conversation_state=str(values["conversation_state"]),
        expected_behavior=taxonomy.expected_behavior,
        structural_pressures=tuple(values["structural_pressures"]),
    )


def infer_taxonomy(task: dict[str, Any]) -> ValidationTaxonomy:
    lane = str(task.get("lane") or "").casefold()
    track = str(task.get("track") or "").casefold()
    task_type = str(task.get("task_type") or "").casefold()
    decision = str(task.get("expected_decision_type") or "ROUTE").upper()

    if lane == "exact_api_term":
        language_form = "exact_spec_like"
    elif lane == "no_exact_natural_language":
        language_form = "no_exact_natural_language"
    elif lane == "paraphrase":
        language_form = "paraphrase"
    elif "low_overlap" in lane or "low_overlap" in track:
        language_form = "low_overlap_natural_language"
    elif task_type == "context_followup":
        language_form = "contextual_natural_language"
    else:
        language_form = "ordinary_natural_language"

    if task_type == "multi_step" or lane == "multi_step":
        intent_shape = "ordered_multi_intent"
    elif decision == "ASK_DISAMBIGUATE" or task_type == "ambiguous":
        intent_shape = "ambiguous_sibling_intents"
    elif decision == "ASK_PARAM" or task_type == "missing_param":
        intent_shape = "underspecified_intent"
    elif decision == "ASK_POLICY" or task_type == "policy_required":
        intent_shape = "policy_conditional_intent"
    elif decision == "BLOCK_UNSAFE" or task_type == "unsafe_write":
        intent_shape = "destructive_intent"
    elif decision == "NO_TOOL":
        intent_shape = "out_of_domain_intent"
    elif decision == "ABSTAIN":
        intent_shape = "insufficient_evidence"
    else:
        intent_shape = "single_concrete_intent"

    if task_type == "context_followup" or "conversation_context" in track:
        conversation_state = "contextual_followup"
    elif decision == "ASK_PARAM" or task_type == "missing_param":
        conversation_state = "recovery_missing_information"
    else:
        conversation_state = "standalone"

    pressures: set[str] = set()
    sequences = expected_endpoint_sequences(task)
    endpoint_sources = {
        endpoint_id.split(":", 1)[0]
        for sequence in sequences
        for endpoint_id in sequence
        if ":" in endpoint_id
    }
    if len(sequences) > 1:
        pressures.add("equivalent_or_competing_alternatives")
    if len(endpoint_sources) > 1:
        pressures.add("cross_surface_competition")
    if task_type == "multi_step" or lane == "multi_step":
        pressures.add("multi_step_sequence")
    notes = str(task.get("notes") or "").casefold()
    if "ambiguous_candidates" in notes:
        pressures.add("sibling_endpoint_competition")
    if not pressures:
        pressures.add("general")

    expected_behavior = EXPECTED_BEHAVIOR_BY_DECISION.get(decision)
    if expected_behavior is None:
        raise ValueError(f"Unsupported expected decision type: {decision}")
    return ValidationTaxonomy(
        language_form=language_form,
        intent_shape=intent_shape,
        conversation_state=conversation_state,
        expected_behavior=expected_behavior,
        structural_pressures=tuple(sorted(pressures)),
    )


def annotate_validation_task(
    task: dict[str, Any],
    *,
    target_id: str,
    source_name: str,
) -> dict[str, Any]:
    annotated = deepcopy(task)
    query = task_query(annotated)
    if not query:
        raise ValueError(f"Task {annotated.get('id')!r} has no query")
    decision = str(annotated.get("expected_decision_type") or "ROUTE").upper()
    taxonomy = _taxonomy_with_overrides(
        infer_taxonomy(annotated),
        annotated.get("validation_taxonomy_override"),
    )
    annotated["query"] = query
    annotated["router_query"] = query
    annotated["expected_decision_type"] = decision
    annotated["validation"] = {
        "schema_version": SCHEMA_VERSION,
        "target_id": target_id,
        "source_name": source_name,
        "source_task_ids": _source_task_ids(annotated),
        "source_keys": _source_keys(annotated, target_id=target_id, source_name=source_name),
        "query_fingerprint": query_fingerprint(query),
        "taxonomy": taxonomy.to_dict(),
        "semantic_responsibility": SEMANTIC_RESPONSIBILITY_BY_DECISION[decision],
        "toolrouter_outcome_scope": (
            "active" if decision in TOOLROUTER_OUTCOMES else "downstream_excluded"
        ),
    }
    return annotated


def validation_errors(task: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    task_id = str(task.get("id") or "")
    query = task_query(task)
    decision = str(task.get("expected_decision_type") or "").upper()
    validation = task.get("validation")
    if not task_id:
        errors.append("missing task id")
    if not query:
        errors.append(f"{task_id or '<unknown>'}: missing query")
    if decision not in EXPECTED_BEHAVIOR_BY_DECISION:
        errors.append(f"{task_id or '<unknown>'}: unsupported expected decision {decision!r}")
    if not isinstance(validation, dict):
        errors.append(f"{task_id or '<unknown>'}: missing validation metadata")
        return errors
    if validation.get("schema_version") != SCHEMA_VERSION:
        errors.append(f"{task_id}: unexpected validation schema version")
    if not validation.get("target_id"):
        errors.append(f"{task_id}: missing target id")
    if not validation.get("source_keys"):
        errors.append(f"{task_id}: missing source keys")
    if validation.get("query_fingerprint") != query_fingerprint(query):
        errors.append(f"{task_id}: stale query fingerprint")
    taxonomy = validation.get("taxonomy")
    if not isinstance(taxonomy, dict):
        errors.append(f"{task_id}: missing taxonomy")
    elif taxonomy.get("expected_behavior") != EXPECTED_BEHAVIOR_BY_DECISION.get(decision):
        errors.append(f"{task_id}: taxonomy behavior does not match expected decision")
    else:
        for dimension, allowed_values in ALLOWED_TAXONOMY_VALUES.items():
            if taxonomy.get(dimension) not in allowed_values:
                errors.append(
                    f"{task_id}: unsupported {dimension} taxonomy value {taxonomy.get(dimension)!r}"
                )

    sequences = expected_endpoint_sequences(task)
    if decision in {"ROUTE", "ASK_PARAM", "BLOCK_UNSAFE"} and not sequences:
        errors.append(f"{task_id}: {decision} requires endpoint ground truth")
    if decision == "ASK_DISAMBIGUATE" and len(sequences) < 2:
        errors.append(f"{task_id}: ASK_DISAMBIGUATE requires at least two candidate alternatives")
    return errors


def assert_valid_tasks(tasks: Iterable[dict[str, Any]]) -> None:
    errors = [error for task in tasks for error in validation_errors(task)]
    if errors:
        raise ValueError("Invalid semantic validation tasks:\n- " + "\n- ".join(errors))


class _UnionFind:
    def __init__(self) -> None:
        self.parent: dict[str, str] = {}

    def find(self, value: str) -> str:
        self.parent.setdefault(value, value)
        if self.parent[value] != value:
            self.parent[value] = self.find(self.parent[value])
        return self.parent[value]

    def union(self, left: str, right: str) -> None:
        left_root = self.find(left)
        right_root = self.find(right)
        if left_root != right_root:
            self.parent[right_root] = left_root


def _task_group_components(
    tasks: list[dict[str, Any]],
    *,
    linked_task_pairs: Iterable[tuple[str, str]] = (),
) -> list[list[dict[str, Any]]]:
    union_find = _UnionFind()
    key_to_task_ids: dict[str, list[str]] = defaultdict(list)
    tasks_by_id: dict[str, dict[str, Any]] = {}
    for task in tasks:
        task_id = str(task["id"])
        if task_id in tasks_by_id:
            raise ValueError(f"Duplicate task id: {task_id}")
        tasks_by_id[task_id] = task
        validation = task["validation"]
        keys = [
            *[f"source:{value}" for value in validation.get("source_keys", [])],
            f"query:{validation['query_fingerprint']}",
        ]
        for key in keys:
            key_to_task_ids[key].append(task_id)
    for task_ids in key_to_task_ids.values():
        for task_id in task_ids[1:]:
            union_find.union(task_ids[0], task_id)
    for left_task_id, right_task_id in linked_task_pairs:
        if left_task_id not in tasks_by_id or right_task_id not in tasks_by_id:
            raise ValueError(
                f"Linked task pair references an unknown task: {(left_task_id, right_task_id)}"
            )
        union_find.union(left_task_id, right_task_id)
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for task_id, task in tasks_by_id.items():
        grouped[union_find.find(task_id)].append(task)
    return [sorted(group, key=lambda task: str(task["id"])) for group in grouped.values()]


def _stable_group_score(group: list[dict[str, Any]]) -> str:
    material = "|".join(str(task["id"]) for task in group)
    return hashlib.sha256(material.encode("utf-8")).hexdigest()


def _group_stratum(group: list[dict[str, Any]]) -> tuple[str, str, str]:
    keys = []
    for task in group:
        validation = task["validation"]
        taxonomy = validation["taxonomy"]
        keys.append(
            (
                str(validation["target_id"]),
                str(taxonomy["language_form"]),
                str(taxonomy["expected_behavior"]),
            )
        )
    return Counter(keys).most_common(1)[0][0]


def _allocation_stratum(group: list[dict[str, Any]]) -> tuple[str, str, str, str]:
    """Stratify evaluation-critical taxonomy across targets without splitting components."""
    taxonomies = [task["validation"]["taxonomy"] for task in group]
    language_form = Counter(
        str(taxonomy["language_form"]) for taxonomy in taxonomies
    ).most_common(1)[0][0]
    expected_behavior = Counter(
        str(taxonomy["expected_behavior"]) for taxonomy in taxonomies
    ).most_common(1)[0][0]
    intent_shapes = [str(taxonomy["intent_shape"]) for taxonomy in taxonomies]
    conversation_states = [str(taxonomy["conversation_state"]) for taxonomy in taxonomies]
    critical_intents = (
        "ordered_multi_intent",
        "independent_multi_intent",
        "conflicting_constraints",
        "out_of_domain_intent",
    )
    critical_conversation_states = (
        "pronoun_or_reference",
        "correction_or_changed_constraint",
        "contextual_followup",
        "recovery_missing_information",
    )
    intent_shape = next(
        (value for value in critical_intents if value in intent_shapes),
        Counter(intent_shapes).most_common(1)[0][0],
    )
    conversation_state = next(
        (value for value in critical_conversation_states if value in conversation_states),
        Counter(conversation_states).most_common(1)[0][0],
    )
    return language_form, intent_shape, conversation_state, expected_behavior


def _component_split_weights(group: list[dict[str, Any]]) -> dict[str, float]:
    expected_behaviors = {
        str(task["validation"]["taxonomy"]["expected_behavior"])
        for task in group
    }
    if expected_behaviors == {"route"}:
        return SPLIT_WEIGHTS
    return EVALUATION_ONLY_SPLIT_WEIGHTS


def split_component_summary(
    tasks: list[dict[str, Any]],
    *,
    linked_task_pairs: Iterable[tuple[str, str]] = (),
) -> dict[str, Any]:
    components = _task_group_components(tasks, linked_task_pairs=linked_task_pairs)
    ordered = sorted(components, key=lambda group: (-len(group), _stable_group_score(group)))
    rows = []
    cross_stratum_count = 0
    for group in ordered:
        strata = sorted({_group_stratum([task]) for task in group})
        if len(strata) > 1:
            cross_stratum_count += 1
        rows.append(
            {
                "size": len(group),
                "majority_stratum": list(_group_stratum(group)),
                "distinct_stratum_count": len(strata),
                "task_id_sample": [str(task["id"]) for task in group[:10]],
            }
        )
    sizes = [len(group) for group in ordered]
    return {
        "component_count": len(components),
        "singleton_component_count": sum(size == 1 for size in sizes),
        "linked_component_count": sum(size > 1 for size in sizes),
        "cross_stratum_component_count": cross_stratum_count,
        "largest_component_size": max(sizes, default=0),
        "largest_components": rows[:10],
    }


def _assign_component_splits(
    components: list[list[dict[str, Any]]],
) -> dict[str, list[str]]:
    """Balance query counts while treating each leakage component as indivisible."""
    by_stratum: dict[tuple[str, str, str, str], list[list[dict[str, Any]]]] = defaultdict(list)
    for group in components:
        by_stratum[_allocation_stratum(group)].append(group)

    global_targets = {
        split: sum(
            len(group) * _component_split_weights(group)[split]
            for group in components
        )
        for split in SPLIT_NAMES
    }
    global_loads = {split: 0 for split in SPLIT_NAMES}
    split_ids = {split: [] for split in SPLIT_NAMES}

    for stratum in sorted(by_stratum):
        groups = sorted(
            by_stratum[stratum],
            key=lambda group: (-len(group), _stable_group_score(group)),
        )
        stratum_targets = {
            split: sum(
                len(group) * _component_split_weights(group)[split]
                for group in groups
            )
            for split in SPLIT_NAMES
        }
        stratum_loads = {split: 0 for split in SPLIT_NAMES}
        for group in groups:
            group_size = len(group)
            group_weights = _component_split_weights(group)
            candidates = []
            for split_index, split in enumerate(SPLIT_NAMES):
                if group_weights[split] <= 0.0:
                    continue
                projected_stratum = {
                    name: stratum_loads[name] + (group_size if name == split else 0)
                    for name in SPLIT_NAMES
                }
                projected_global = {
                    name: global_loads[name] + (group_size if name == split else 0)
                    for name in SPLIT_NAMES
                }
                stratum_error = sum(
                    (projected_stratum[name] - stratum_targets[name]) ** 2
                    for name in SPLIT_NAMES
                )
                global_error = sum(
                    (projected_global[name] - global_targets[name]) ** 2
                    for name in SPLIT_NAMES
                )
                candidates.append((stratum_error, global_error, split_index, split))
            split = min(candidates)[-1]
            stratum_loads[split] += group_size
            global_loads[split] += group_size
            split_ids[split].extend(str(task["id"]) for task in group)

    for values in split_ids.values():
        values.sort()
    return split_ids


def build_blind_split_manifest(
    tasks: list[dict[str, Any]],
    *,
    linked_task_pairs: Iterable[tuple[str, str]] = (),
) -> dict[str, Any]:
    assert_valid_tasks(tasks)
    components = _task_group_components(tasks, linked_task_pairs=linked_task_pairs)
    split_ids = _assign_component_splits(components)
    train_task_ids = set(split_ids["train"])
    example_card_task_ids = sorted(
        str(task["id"])
        for task in tasks
        if str(task["id"]) in train_task_ids
        and str(task.get("expected_decision_type") or "") == "ROUTE"
        and expected_endpoint_sequences(task)
    )
    return {
        "version": 3,
        "split_policy": {
            "name": "pure_route_train_taxonomy_stratified_leakage_component_greedy",
            "route_weights": SPLIT_WEIGHTS,
            "evaluation_only_weights": EVALUATION_ONLY_SPLIT_WEIGHTS,
            "training_eligible_expected_behaviors": ["route"],
            "mixed_behavior_components": "evaluation_only",
        },
        "component_summary": split_component_summary(
            tasks,
            linked_task_pairs=linked_task_pairs,
        ),
        "splits": split_ids,
        "example_card_task_ids": example_card_task_ids,
    }


def audit_split_integrity(tasks: list[dict[str, Any]], manifest: dict[str, Any]) -> dict[str, Any]:
    tasks_by_id = {str(task["id"]): task for task in tasks}
    violations: list[dict[str, Any]] = []
    assigned: dict[str, str] = {}
    key_splits: dict[tuple[str, str], set[str]] = defaultdict(set)
    for split in SPLIT_NAMES:
        for task_id in manifest.get("splits", {}).get(split, []):
            if task_id not in tasks_by_id:
                violations.append({"type": "unknown_task_id", "split": split, "task_id": task_id})
                continue
            if task_id in assigned:
                violations.append(
                    {
                        "type": "task_in_multiple_splits",
                        "task_id": task_id,
                        "splits": sorted({assigned[task_id], split}),
                    }
                )
            assigned[task_id] = split
            validation = tasks_by_id[task_id]["validation"]
            key_splits[("query", str(validation["query_fingerprint"]))].add(split)
            for source_key in validation.get("source_keys", []):
                key_splits[("source", str(source_key))].add(split)
    for (kind, value), splits in sorted(key_splits.items()):
        if len(splits) > 1:
            violations.append(
                {
                    "type": f"{kind}_leakage",
                    "value": value,
                    "splits": sorted(splits),
                }
            )
    unassigned = sorted(set(tasks_by_id) - set(assigned))
    for task_id in unassigned:
        violations.append({"type": "unassigned_task", "task_id": task_id})

    example_ids = set(manifest.get("example_card_task_ids", []))
    non_train_examples = sorted(example_ids - set(manifest.get("splits", {}).get("train", [])))
    for task_id in non_train_examples:
        violations.append({"type": "example_card_not_train", "task_id": task_id})
    return {
        "task_count": len(tasks),
        "split_counts": {
            split: len(manifest.get("splits", {}).get(split, []))
            for split in SPLIT_NAMES
        },
        "example_card_count": len(example_ids),
        "violation_count": len(violations),
        "violations": violations,
    }


def assert_split_integrity(tasks: list[dict[str, Any]], manifest: dict[str, Any]) -> dict[str, Any]:
    audit = audit_split_integrity(tasks, manifest)
    if audit["violations"]:
        details = "\n".join(f"- {value}" for value in audit["violations"])
        raise ValueError(f"Semantic validation split integrity failed:\n{details}")
    return audit


def coverage_counts(tasks: list[dict[str, Any]], manifest: dict[str, Any] | None = None) -> dict[str, Any]:
    split_by_task: dict[str, str] = {}
    if manifest:
        for split in SPLIT_NAMES:
            for task_id in manifest.get("splits", {}).get(split, []):
                split_by_task[str(task_id)] = split
    counts: dict[str, Counter[str]] = {
        "target": Counter(),
        "language_form": Counter(),
        "intent_shape": Counter(),
        "conversation_state": Counter(),
        "expected_behavior": Counter(),
        "structural_pressure": Counter(),
        "split": Counter(),
    }
    for task in tasks:
        validation = task["validation"]
        taxonomy = validation["taxonomy"]
        counts["target"][str(validation["target_id"])] += 1
        for axis in ("language_form", "intent_shape", "conversation_state", "expected_behavior"):
            counts[axis][str(taxonomy[axis])] += 1
        for pressure in taxonomy.get("structural_pressures", []):
            counts["structural_pressure"][str(pressure)] += 1
        if split_by_task:
            counts["split"][split_by_task.get(str(task["id"]), "unassigned")] += 1
    return {name: dict(sorted(values.items())) for name, values in counts.items()}


def coverage_gaps(counts: dict[str, Any]) -> dict[str, list[str]]:
    gaps: dict[str, list[str]] = {}
    for axis, required_values in REQUIRED_TAXONOMY_VALUES.items():
        observed = set((counts.get(axis) or {}).keys())
        missing = [value for value in required_values if value not in observed]
        if missing:
            gaps[axis] = missing
    return gaps
