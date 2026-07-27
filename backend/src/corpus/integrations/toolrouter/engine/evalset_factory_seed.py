from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import Any

from .evalset_factory_contracts import QUERY_CATEGORIES
from .openapi_loader import NormalizedBundle, NormalizedEndpoint


def _schema_fields(bundle: NormalizedBundle, schema_names: Sequence[str]) -> set[str]:
    fields: set[str] = set()
    for schema_name in schema_names:
        schema = bundle.schemas.get(schema_name)
        if not isinstance(schema, Mapping):
            continue
        properties = schema.get("properties")
        if isinstance(properties, Mapping):
            fields.update(str(name).casefold() for name in properties)
        required = schema.get("required")
        if isinstance(required, list):
            fields.update(str(name).casefold() for name in required)
    return fields


def required_input_fields(bundle: NormalizedBundle, endpoint: NormalizedEndpoint) -> tuple[str, ...]:
    values = {str(name).casefold() for name in endpoint.required_params}
    for schema_name in endpoint.request_schemas:
        schema = bundle.schemas.get(schema_name)
        if not isinstance(schema, Mapping):
            continue
        required = schema.get("required")
        if isinstance(required, list):
            values.update(str(name).casefold() for name in required)
    return tuple(sorted(values))


def dependency_fields(
    bundle: NormalizedBundle,
    left_endpoint_id: str,
    right_endpoint_id: str,
) -> tuple[str, ...]:
    left = bundle.endpoint_by_id(left_endpoint_id)
    right = bundle.endpoint_by_id(right_endpoint_id)
    outputs = _schema_fields(bundle, left.response_schemas)
    inputs = set(required_input_fields(bundle, right))
    direct = sorted((outputs & inputs) - {"id"})
    if direct:
        return tuple(direct)
    shared_resources = {
        value.casefold()
        for value in left.resources
        if value.casefold() in {item.casefold() for item in right.resources}
    }
    if "id" in outputs and "id" in inputs and shared_resources:
        return ("id",)
    if "id" in outputs:
        resource_tokens = {
            value.rstrip("s").casefold()
            for value in left.resources
            if len(value) >= 3
        }
        for input_name in sorted(inputs):
            if not input_name.endswith("_id"):
                continue
            if input_name[:-3].casefold() in resource_tokens:
                return (input_name,)
    return ()


def _resource_overlap(left: NormalizedEndpoint, right: NormalizedEndpoint) -> float:
    left_values = {value.casefold() for value in left.resources}
    right_values = {value.casefold() for value in right.resources}
    union = left_values | right_values
    return len(left_values & right_values) / len(union) if union else 0.0


def _endpoint_rank(endpoint: NormalizedEndpoint) -> tuple[int, int, int, str]:
    return (
        int(bool(endpoint.summary)),
        len(endpoint.resources),
        len(endpoint.description),
        endpoint.id,
    )


def _sibling_pair(endpoints: Sequence[NormalizedEndpoint]) -> tuple[NormalizedEndpoint, NormalizedEndpoint]:
    candidates: list[tuple[float, int, str, str, NormalizedEndpoint, NormalizedEndpoint]] = []
    for index, left in enumerate(endpoints):
        for right in endpoints[index + 1 :]:
            candidates.append(
                (
                    _resource_overlap(left, right),
                    int(left.operation_class != right.operation_class),
                    left.id,
                    right.id,
                    left,
                    right,
                )
            )
    if not candidates:
        raise ValueError("At least two endpoints are required to construct sibling boundaries")
    winner = max(candidates, key=lambda value: value[:4])
    return winner[4], winner[5]


def _independent_pair(endpoints: Sequence[NormalizedEndpoint]) -> tuple[NormalizedEndpoint, NormalizedEndpoint]:
    pairs: list[tuple[float, str, str, NormalizedEndpoint, NormalizedEndpoint]] = []
    for index, left in enumerate(endpoints):
        for right in endpoints[index + 1 :]:
            pairs.append((_resource_overlap(left, right), left.id, right.id, left, right))
    if not pairs:
        raise ValueError("At least two endpoints are required to construct independent intents")
    winner = min(pairs, key=lambda value: value[:3])
    return winner[3], winner[4]


def _dependent_pair(
    bundle: NormalizedBundle,
    endpoints: Sequence[NormalizedEndpoint],
) -> tuple[NormalizedEndpoint, NormalizedEndpoint, tuple[str, ...]]:
    candidates: list[tuple[int, float, str, str, NormalizedEndpoint, NormalizedEndpoint, tuple[str, ...]]] = []
    for left in endpoints:
        for right in endpoints:
            if left.id == right.id:
                continue
            fields = dependency_fields(bundle, left.id, right.id)
            if not fields:
                continue
            candidates.append(
                (
                    int(left.method.upper() == "POST"),
                    _resource_overlap(left, right),
                    left.id,
                    right.id,
                    left,
                    right,
                    fields,
                )
            )
    if not candidates:
        raise ValueError("OpenAPI schemas cannot prove a dependent response-to-input endpoint pair")
    winner = max(candidates, key=lambda value: value[:4])
    return winner[4], winner[5], winner[6]


def _task_id(target_id: str, category: str) -> str:
    return f"{target_id}_seedv1_{category}_001"


def _base_task(
    *,
    target_id: str,
    category: str,
    decision: str,
    sequence: Sequence[str] = (),
    alternatives: Sequence[Sequence[str]] = (),
    query: str,
) -> dict[str, Any]:
    return {
        "id": _task_id(target_id, category),
        "lane": category,
        "track": "evalset_factory_openapi_seed_v1",
        "query": query,
        "router_query": query,
        "expected_decision_type": decision,
        "expected_endpoint_sequence": list(sequence),
        "allowed_alternatives": [list(value) for value in alternatives],
        "expected_required_params": {},
        "evalset": {
            "schema_version": 1,
            "query_category": category,
            "score_scope": "factory_truth_seed",
            "origin": "deterministic_openapi_seed_v1",
            "freshness": "unseen_before_generation",
            "authoritative_user_traffic": False,
        },
        "validation": {"target_id": target_id},
    }


def _endpoint_query(endpoint: NormalizedEndpoint) -> str:
    return endpoint.summary or f"{endpoint.operation_class} {' '.join(endpoint.resources[:2])}"


def build_openapi_seed_tasks(
    *,
    target_id: str,
    bundle: NormalizedBundle,
    foreign_source_task_id: str,
    global_capability: Mapping[str, Any],
) -> list[dict[str, Any]]:
    if not target_id.strip():
        raise ValueError("Seed target_id cannot be empty")
    if len(bundle.endpoints) < 2:
        raise ValueError("At least two endpoints are required to build the 17-category seed set")
    if not foreign_source_task_id.strip():
        raise ValueError("A source-backed foreign task ID is required for target-isolation truth")
    for field in ("url", "capability", "license"):
        if not str(global_capability.get(field) or "").strip():
            raise ValueError(f"Global no-tool capability evidence requires {field!r}")

    endpoints = sorted(bundle.endpoints, key=_endpoint_rank, reverse=True)
    sibling_left, sibling_right = _sibling_pair(endpoints)
    independent_left, independent_right = _independent_pair(endpoints)
    dependent_left, dependent_right, dependent_proof = _dependent_pair(bundle, endpoints)
    ask_candidates = [endpoint for endpoint in endpoints if required_input_fields(bundle, endpoint)]
    if not ask_candidates:
        raise ValueError("OpenAPI has no endpoint with provable required inputs for ASK_PARAM")
    ask_endpoint = max(
        ask_candidates,
        key=lambda endpoint: (len(required_input_fields(bundle, endpoint)), _endpoint_rank(endpoint)),
    )

    single_categories = (
        "exact_spec_reference",
        "paraphrase",
        "non_exact_wording",
        "low_lexical_overlap",
        "typo_or_noisy",
        "verbose_or_indirect",
        "context_followup",
        "pronoun_or_reference",
    )
    selected = {
        category: endpoints[index % len(endpoints)]
        for index, category in enumerate(single_categories)
    }
    selected["exact_spec_reference"] = sibling_right
    tasks: list[dict[str, Any]] = []
    for category in single_categories:
        endpoint = selected[category]
        task = _base_task(
            target_id=target_id,
            category=category,
            decision="ROUTE",
            sequence=(endpoint.id,),
            query=_endpoint_query(endpoint),
        )
        if category in {"context_followup", "pronoun_or_reference"}:
            task["conversation_context"] = {
                "selected_endpoint_id": endpoint.id,
                "selected_endpoint_summary": endpoint.summary,
                "operation_class": endpoint.operation_class,
                "operation_terms": [endpoint.operation_class],
                "resource_terms": list(endpoint.resources),
                "prior_user_request": _endpoint_query(endpoint),
            }
        tasks.append(task)

    exact_task = next(
        task for task in tasks if task["evalset"]["query_category"] == "exact_spec_reference"
    )
    negation = _base_task(
        target_id=target_id,
        category="negation_or_exclusion",
        decision="ROUTE",
        sequence=(sibling_left.id,),
        query=f"{_endpoint_query(sibling_left)}, not {_endpoint_query(sibling_right)}",
    )
    negation["generated_stress"] = {"source_task_ids": [exact_task["id"]]}
    tasks.append(negation)

    correction = _base_task(
        target_id=target_id,
        category="correction_or_changed_constraint",
        decision="ROUTE",
        sequence=(sibling_left.id,),
        query=f"Actually, {_endpoint_query(sibling_left)}",
    )
    correction["conversation_context"] = {
        "selected_endpoint_id": sibling_left.id,
        "selected_endpoint_summary": sibling_left.summary,
        "superseded_endpoint_id": sibling_right.id,
        "superseded_query": _endpoint_query(sibling_right),
        "corrected_query": _endpoint_query(sibling_left),
    }
    correction["generated_stress"] = {"source_task_ids": [exact_task["id"]]}
    tasks.append(correction)

    tasks.append(
        _base_task(
            target_id=target_id,
            category="ambiguous_conflicting_intents",
            decision="ASK_DISAMBIGUATE",
            alternatives=((sibling_left.id,), (sibling_right.id,)),
            query=f"Either {_endpoint_query(sibling_left)} or {_endpoint_query(sibling_right)}",
        )
    )

    ask = _base_task(
        target_id=target_id,
        category="ask_param",
        decision="ASK_PARAM",
        sequence=(ask_endpoint.id,),
        query=_endpoint_query(ask_endpoint),
    )
    ask["expected_required_params"] = {
        ask_endpoint.id: list(required_input_fields(bundle, ask_endpoint))
    }
    ask["provided_params"] = {}
    tasks.append(ask)

    independent = _base_task(
        target_id=target_id,
        category="independent_multi_intent",
        decision="ROUTE",
        sequence=(independent_left.id, independent_right.id),
        alternatives=((independent_right.id, independent_left.id),),
        query=f"{_endpoint_query(independent_left)} and {_endpoint_query(independent_right)}",
    )
    independent["evalset"]["dependent_steps"] = False
    tasks.append(independent)

    dependent = _base_task(
        target_id=target_id,
        category="dependent_multi_hop",
        decision="ROUTE",
        sequence=(dependent_left.id, dependent_right.id),
        query=(
            f"{_endpoint_query(dependent_left)}, then use returned "
            f"{', '.join(dependent_proof)} to {_endpoint_query(dependent_right)}"
        ),
    )
    dependent["dependency_fields"] = list(dependent_proof)
    dependent["evalset"]["dependent_steps"] = True
    tasks.append(dependent)

    target_no_tool = _base_task(
        target_id=target_id,
        category="no_tool_target_isolation",
        decision="NO_TOOL",
        query="Source-backed foreign capability",
    )
    target_no_tool["generated_stress"] = {"source_task_ids": [foreign_source_task_id]}
    target_no_tool["evalset"]["catalog_scope"] = "target_catalog"
    tasks.append(target_no_tool)

    global_no_tool = _base_task(
        target_id=target_id,
        category="no_tool_global_catalog",
        decision="NO_TOOL",
        query=str(global_capability["capability"]),
    )
    global_no_tool["catalog_ground_truth"] = {
        "catalog_complete": True,
        "catalog_scope": "benchmark_registry",
        "checked_target_ids": [target_id],
        "checked_endpoint_count": len(bundle.endpoints),
        "matched_endpoint_ids": [],
        "external_capability_source": dict(global_capability),
    }
    global_no_tool["evalset"]["catalog_scope"] = "benchmark_registry"
    tasks.append(global_no_tool)

    tasks.append(
        _base_task(
            target_id=target_id,
            category="abstain_insufficient_evidence",
            decision="ABSTAIN",
            query="Can you handle that for me?",
        )
    )

    by_category = {task["evalset"]["query_category"]: task for task in tasks}
    missing = sorted(set(QUERY_CATEGORIES) - set(by_category))
    duplicates = len(tasks) != len(by_category)
    if missing or duplicates:
        raise RuntimeError(
            f"Seed builder did not create exactly one task per category: missing={missing}, duplicates={duplicates}"
        )
    return [by_category[category] for category in QUERY_CATEGORIES]
