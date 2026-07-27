from __future__ import annotations

import json
import re
from difflib import SequenceMatcher
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

from .openapi_loader import NormalizedBundle, slugify
from .leakage_audit import bucket_for_overlap, endpoint_overlap


READ_OPERATION_CLASSES = {"list", "get", "search"}
WRITE_OPERATION_CLASSES = {"create", "update", "delete"}
TASK_OPERATION_ORDER = ["list", "get", "create", "update", "delete", "search", "custom"]
NATURAL_QUERY_MAX_WORDS = 18
NATURAL_QUERY_MAX_CHARS = 140
BANNED_NATURAL_PHRASES = [
    "with required parameters",
    "with a valid request body",
    "as a dry run",
]


def endpoint_terms(endpoint: Any) -> list[str]:
    terms: list[str] = []
    terms.extend(str(item) for item in getattr(endpoint, "resources", []) if item)
    terms.extend(slugify(str(item)) for item in getattr(endpoint, "tags", []) if item)
    terms.extend(slugify(segment) for segment in str(endpoint.path).strip("/").split("/") if segment and not segment.startswith("{"))
    return [term for term in dict.fromkeys(terms) if term]


def term_matches(candidate: str, terms: list[str]) -> bool:
    candidate = slugify(candidate)
    if not candidate:
        return False
    candidate_forms = {candidate}
    if candidate.endswith("s") and len(candidate) > 1:
        candidate_forms.add(candidate[:-1])
    candidate_tokens = set(candidate.split("_"))
    for term in terms:
        term_forms = {term}
        if term.endswith("s") and len(term) > 1:
            term_forms.add(term[:-1])
        term_tokens = set(term.split("_"))
        if candidate_forms & term_forms or candidate_forms & term_tokens or candidate_tokens & term_forms:
            return True
    return False


def derive_coverage_terms(bundle: NormalizedBundle, limit: int = 12) -> list[str]:
    counts: Counter[str] = Counter()
    operation_classes: dict[str, set[str]] = defaultdict(set)
    for endpoint in bundle.endpoints:
        for term in endpoint_terms(endpoint):
            counts[term] += 1
            operation_classes[term].add(endpoint.operation_class)
    ranked = sorted(
        counts,
        key=lambda term: (
            len(operation_classes[term] & set(TASK_OPERATION_ORDER)),
            counts[term],
            term,
        ),
        reverse=True,
    )
    return ranked[:limit]


def endpoint_domain(endpoint: Any, coverage_terms: list[str] | None = None) -> str:
    terms = endpoint_terms(endpoint)
    for candidate in coverage_terms or []:
        if term_matches(candidate, terms):
            return slugify(candidate)
    return terms[0] if terms else "general"


def readable_endpoint_label(endpoint: Any) -> str:
    for value in [getattr(endpoint, "summary", ""), getattr(endpoint, "operation_id", ""), getattr(endpoint, "path", "")]:
        text = " ".join(str(value).replace("_", " ").replace("-", " ").split())
        if text:
            return text
    return getattr(endpoint, "id", "endpoint")


def endpoint_provenance(endpoint: Any) -> dict[str, Any]:
    return {
        "source": endpoint.source,
        "method": endpoint.method,
        "path": endpoint.path,
        "operationId": endpoint.operation_id,
        "summary": endpoint.summary,
        "description": endpoint.description,
        "tags": endpoint.tags,
        "request_schemas": endpoint.request_schemas,
        "response_schemas": endpoint.response_schemas,
        "resources": endpoint.resources,
    }


def schema_required_fields(bundle: NormalizedBundle, schema_name: str) -> list[str]:
    schema = bundle.schemas.get(schema_name, {}) or {}
    required = schema.get("required", [])
    if isinstance(required, list):
        return [str(item) for item in required if str(item)]
    return []


def endpoint_required_body_fields(bundle: NormalizedBundle, endpoint: Any) -> list[str]:
    fields: list[str] = []
    for schema_name in getattr(endpoint, "request_schemas", []) or []:
        fields.extend(schema_required_fields(bundle, schema_name))
    return list(dict.fromkeys(fields))


def provided_inputs_for_endpoint(bundle: NormalizedBundle, endpoint: Any) -> dict[str, str]:
    provided = {param: "sample" for param in getattr(endpoint, "required_params", [])}
    for field_name in endpoint_required_body_fields(bundle, endpoint):
        provided[field_name] = "sample"
    return provided


def normalized_path_segments(path: str) -> list[str]:
    return [slugify(segment) for segment in path.strip("/").split("/") if segment and not segment.startswith("{")]


def path_similarity(left: str, right: str) -> float:
    left_segments = normalized_path_segments(left)
    right_segments = normalized_path_segments(right)
    left_set = set(left_segments)
    right_set = set(right_segments)
    if not left_set and not right_set:
        jaccard = 1.0
    elif not left_set or not right_set:
        jaccard = 0.0
    else:
        jaccard = len(left_set & right_set) / len(left_set | right_set)
    sequence = SequenceMatcher(None, "/".join(left_segments), "/".join(right_segments)).ratio()
    return (jaccard + sequence) / 2


def allowed_alternatives_for_endpoint(
    endpoint: Any,
    endpoints: list[Any],
    coverage_terms: list[str] | None,
    threshold: float = 0.55,
    limit: int = 3,
) -> list[list[str]]:
    resource = endpoint_domain(endpoint, coverage_terms)
    candidates: list[tuple[float, str]] = []
    for other in endpoints:
        if other.id == endpoint.id:
            continue
        if other.operation_class != endpoint.operation_class:
            continue
        if endpoint_domain(other, coverage_terms) != resource:
            continue
        score = path_similarity(endpoint.path, other.path)
        if score >= threshold:
            candidates.append((score, other.id))
    candidates.sort(key=lambda item: (item[0], item[1]), reverse=True)
    return [[endpoint_id] for _score, endpoint_id in candidates[:limit]]


def query_for_endpoint(endpoint: Any, domain: str) -> str:
    label = readable_endpoint_label(endpoint)
    if endpoint.required_params:
        return f"{label} with required parameters for {domain}"
    if endpoint.request_schemas:
        return f"{label} with a valid request body for {domain}"
    return f"{label} for {domain}"


def humanize_identifier(value: str) -> str:
    spaced = re.sub(r"([a-z0-9])([A-Z])", r"\1 \2", str(value or ""))
    spaced = re.sub(r"[^a-zA-Z0-9]+", " ", spaced)
    return " ".join(spaced.split()).lower()


def endpoint_path_terms(endpoint: Any) -> set[str]:
    terms: set[str] = set()
    for segment in str(endpoint.path).strip("/").split("/"):
        if not segment or segment.startswith("{"):
            continue
        terms.update(humanize_identifier(segment).split())
    return {term for term in terms if term}


def natural_source_text(endpoint: Any) -> str:
    source = endpoint.summary or endpoint.description or humanize_identifier(endpoint.operation_id)
    source = re.split(r"[.;]\s+", str(source), maxsplit=1)[0]
    source = re.sub(r"\b(GET|POST|PUT|PATCH|DELETE|HEAD|OPTIONS)\b", "", source)
    source = source.replace(endpoint.operation_id, "")
    source = " ".join(source.split())
    if not source:
        source = humanize_identifier(endpoint.operation_id)
    return source


def natural_query_for_endpoint(endpoint: Any, variant: int = 0) -> str:
    text = humanize_identifier(natural_source_text(endpoint))
    text = re.sub(r"\bstore\b|\badmin\b", "", text)
    text = " ".join(text.split()) or humanize_identifier(endpoint.summary or endpoint.operation_id)
    templates = [
        "I need to {text}",
        "Can you help me {text}",
        "Please {text}",
        "A user wants to {text}",
    ]
    query = templates[variant % len(templates)].format(text=text)
    for phrase in BANNED_NATURAL_PHRASES:
        query = query.replace(phrase, "")
    query = re.sub(r"/[a-zA-Z0-9_/{}/-]+", "", query)
    query = " ".join(query.split())
    words = query.split()
    if len(words) > NATURAL_QUERY_MAX_WORDS:
        query = " ".join(words[:NATURAL_QUERY_MAX_WORDS])
    if len(query) > NATURAL_QUERY_MAX_CHARS:
        query = query[:NATURAL_QUERY_MAX_CHARS].rsplit(" ", 1)[0]
    return query


def natural_task_from_endpoint(
    bundle: NormalizedBundle,
    endpoint: Any,
    index: int,
    coverage_terms: list[str] | None,
    endpoints: list[Any],
    task_prefix: str,
    track: str = "natural_routing",
) -> dict[str, Any]:
    domain = endpoint_domain(endpoint, coverage_terms)
    query = natural_query_for_endpoint(endpoint, index)
    return {
        "id": f"{task_prefix}_{index:03d}",
        "query": query,
        "router_query": query,
        "track": track,
        "resource": domain,
        "operation_class": endpoint.operation_class,
        "expected_decision_type": "ROUTE",
        "expected_endpoint_sequence": [endpoint.id],
        "expected_required_params": {endpoint.id: endpoint.required_params} if endpoint.required_params else {},
        "provided_params": provided_inputs_for_endpoint(bundle, endpoint),
        "allowed_alternatives": allowed_alternatives_for_endpoint(endpoint, endpoints, coverage_terms),
        "task_type": "single_step",
        "notes": f"track={track}; generated_natural_query_from_openapi_metadata",
        "provenance": endpoint_provenance(endpoint),
    }


def task_from_endpoint(
    endpoint: Any,
    index: int,
    coverage_terms: list[str] | None = None,
    endpoints: list[Any] | None = None,
    task_type: str = "single_step",
    task_prefix: str = "task",
) -> dict[str, Any]:
    domain = endpoint_domain(endpoint, coverage_terms)
    query = query_for_endpoint(endpoint, domain)
    return {
        "id": f"{task_prefix}_{index:03d}",
        "query": query,
        "router_query": query,
        "resource": domain,
        "operation_class": endpoint.operation_class,
        "track": "spec_close_smoke",
        "expected_decision_type": "ROUTE",
        "expected_endpoint_sequence": [endpoint.id],
        "expected_required_params": {endpoint.id: endpoint.required_params} if endpoint.required_params else {},
        "allowed_alternatives": allowed_alternatives_for_endpoint(endpoint, endpoints or [], coverage_terms),
        "task_type": task_type,
        "notes": f"resource={domain}; operation_class={endpoint.operation_class}; generated_from={endpoint.id}",
        "provenance": endpoint_provenance(endpoint),
    }


def make_policy_task(domain: str, index: int, task_prefix: str) -> dict[str, Any]:
    query = f"determine whether an external authorization source permits the requested workflow for {domain}"
    return {
        "id": f"{task_prefix}_{index:03d}",
        "query": query,
        "router_query": query,
        "resource": domain,
        "operation_class": "policy_required",
        "track": "spec_close_smoke",
        "expected_decision_type": "ASK_POLICY",
        "expected_endpoint_sequence": [],
        "expected_required_params": {},
        "allowed_alternatives": [],
        "task_type": "policy_required",
        "notes": f"resource={domain}; expected_behavior=abstain_policy_not_in_openapi",
        "provenance": {},
    }


def structural_query_for_endpoint(endpoint: Any, domain: str, variant: int = 0) -> str:
    param_names = "_".join(param.name for param in getattr(endpoint, "params", []) if getattr(param, "name", "")) or "none"
    param_locations = "_".join(param.location for param in getattr(endpoint, "params", []) if getattr(param, "location", "")) or "none"
    request_schemas = "_".join(getattr(endpoint, "request_schemas", []) or ["none"])
    response_schemas = "_".join(getattr(endpoint, "response_schemas", []) or ["none"])
    auth_shape = "secured" if getattr(endpoint, "security", []) else "public"
    dry_run_shape = "body_payload" if getattr(endpoint, "request_schemas", []) else "no_body"
    templates = [
        "contract route class {operation} resource_bucket {domain} input_slots {params} locations {locations} request_model {request} response_model {response} auth_shape {auth} dry_run_shape {dry}",
        "tool candidate class {operation} resource_bucket {domain} parameter_slots {params} parameter_locations {locations} request_contract {request} response_contract {response} security_shape {auth} execution_shape {dry}",
        "api plan class {operation} resource_bucket {domain} inputs {params} input_locations {locations} body_contract {request} output_contract {response} access_shape {auth} dry_run_contract {dry}",
    ]
    return templates[variant % len(templates)].format(
        operation=getattr(endpoint, "operation_class", "custom"),
        domain=domain,
        params=param_names,
        locations=param_locations,
        request=request_schemas,
        response=response_schemas,
        auth=auth_shape,
        dry=dry_run_shape,
    )


def low_overlap_query_for_endpoint(endpoint: Any, domain: str) -> str | None:
    for variant in range(12):
        query = structural_query_for_endpoint(endpoint, domain, variant)
        if bucket_for_overlap(endpoint_overlap(query, endpoint)["max_overlap"]) == "low":
            return query
    return None


def low_overlap_task_from_endpoint(
    endpoint: Any,
    index: int,
    coverage_terms: list[str] | None,
    endpoints: list[Any],
    task_prefix: str,
) -> dict[str, Any] | None:
    domain = endpoint_domain(endpoint, coverage_terms)
    router_query = low_overlap_query_for_endpoint(endpoint, domain)
    if router_query is None:
        return None
    task = task_from_endpoint(endpoint, index, coverage_terms, endpoints, task_prefix=task_prefix)
    task["track"] = "low_overlap_stress"
    task["expected_decision_type"] = "ROUTE"
    task["router_query"] = router_query
    task["notes"] = f"{task['notes']}; suite=low_overlap; query_generation=structural_openapi_fields"
    return task


def make_ambiguous_task(
    endpoints: list[Any],
    index: int,
    coverage_terms: list[str] | None,
    task_prefix: str,
) -> dict[str, Any]:
    primary = endpoints[0]
    domain = endpoint_domain(primary, coverage_terms)
    operation_class = primary.operation_class
    request_schemas = "_".join(sorted({schema for endpoint in endpoints for schema in getattr(endpoint, "request_schemas", [])}) or ["none"])
    response_schemas = "_".join(sorted({schema for endpoint in endpoints for schema in getattr(endpoint, "response_schemas", [])}) or ["none"])
    required_slots = "_".join(sorted({param for endpoint in endpoints for param in getattr(endpoint, "required_params", [])}) or ["none"])
    query = (
        f"candidate choice class {operation_class} resource_bucket {domain} required_slots {required_slots} "
        f"request_contracts {request_schemas} response_contracts {response_schemas} multiple_api_candidates"
    )
    return {
        "id": f"{task_prefix}_{index:03d}",
        "query": query,
        "router_query": query,
        "resource": domain,
        "operation_class": operation_class,
        "track": "low_overlap_stress",
        "expected_decision_type": "ASK_DISAMBIGUATE",
        "expected_endpoint_sequence": [],
        "expected_required_params": {},
        "allowed_alternatives": [[endpoint.id] for endpoint in endpoints],
        "task_type": "ambiguous",
        "notes": f"resource={domain}; operation_class={operation_class}; generated_ambiguous_candidates={','.join(endpoint.id for endpoint in endpoints)}",
        "provenance": {"candidates": [endpoint_provenance(endpoint) for endpoint in endpoints]},
    }


def make_low_overlap_policy_task(domain: str, index: int, task_prefix: str) -> dict[str, Any]:
    query = (
        f"external governance review resource_bucket {domain} compliance_source missing "
        "approval_evidence required before api candidate selection"
    )
    return {
        "id": f"{task_prefix}_{index:03d}",
        "query": query,
        "router_query": query,
        "resource": domain,
        "operation_class": "policy_required",
        "track": "low_overlap_stress",
        "expected_decision_type": "ASK_POLICY",
        "expected_endpoint_sequence": [],
        "expected_required_params": {},
        "allowed_alternatives": [],
        "task_type": "policy_required",
        "notes": f"resource={domain}; expected_behavior=threshold_abstention_external_source_required",
        "provenance": {},
    }


def make_recovery_policy_task(domain: str, index: int, task_prefix: str) -> dict[str, Any]:
    query = f"Can we proceed only if the merchant policy allows this workflow?"
    return {
        "id": f"{task_prefix}_{index:03d}",
        "query": query,
        "router_query": query,
        "track": "recovery_followup",
        "resource": domain,
        "operation_class": "policy_required",
        "expected_decision_type": "ASK_POLICY",
        "expected_endpoint_sequence": [],
        "expected_required_params": {},
        "expected_follow_up": "OpenAPI defines possible actions but not the business rule or policy source needed to decide this.",
        "allowed_alternatives": [],
        "task_type": "policy_required",
        "notes": f"resource={domain}; expected_behavior=ask_policy_source",
        "provenance": {},
    }


def recovery_missing_param_task_from_endpoint(
    bundle: NormalizedBundle,
    endpoint: Any,
    index: int,
    coverage_terms: list[str] | None,
    endpoints: list[Any],
    task_prefix: str,
) -> dict[str, Any]:
    domain = endpoint_domain(endpoint, coverage_terms)
    query = natural_query_for_endpoint(endpoint, index)
    missing = list(dict.fromkeys(list(endpoint.required_params) + endpoint_required_body_fields(bundle, endpoint)))
    return {
        "id": f"{task_prefix}_{index:03d}",
        "query": query,
        "router_query": query,
        "track": "recovery_followup",
        "resource": domain,
        "operation_class": endpoint.operation_class,
        "expected_decision_type": "ASK_PARAM",
        "expected_endpoint_sequence": [endpoint.id],
        "expected_required_params": {endpoint.id: missing},
        "expected_missing_params": missing,
        "provided_params": {},
        "expected_follow_up": f"Ask for: {', '.join(missing)}",
        "allowed_alternatives": allowed_alternatives_for_endpoint(endpoint, endpoints, coverage_terms),
        "task_type": "missing_param",
        "notes": f"resource={domain}; expected_behavior=ask_missing_openapi_param",
        "provenance": endpoint_provenance(endpoint),
    }


def make_recovery_ambiguous_task(
    endpoints: list[Any],
    index: int,
    coverage_terms: list[str] | None,
    task_prefix: str,
) -> dict[str, Any]:
    primary = endpoints[0]
    domain = endpoint_domain(primary, coverage_terms)
    query = f"I need help with {humanize_identifier(domain)} work"
    return {
        "id": f"{task_prefix}_{index:03d}",
        "query": query,
        "router_query": query,
        "track": "recovery_followup",
        "resource": domain,
        "operation_class": primary.operation_class,
        "expected_decision_type": "ASK_DISAMBIGUATE",
        "expected_endpoint_sequence": [],
        "expected_required_params": {},
        "allowed_alternatives": [[endpoint.id] for endpoint in endpoints],
        "expected_follow_up": "Ask the user to choose among plausible endpoint candidates.",
        "task_type": "ambiguous",
        "notes": f"resource={domain}; generated_ambiguous_candidates={','.join(endpoint.id for endpoint in endpoints)}",
        "provenance": {"candidates": [endpoint_provenance(endpoint) for endpoint in endpoints]},
    }


def recovery_unsafe_task_from_endpoint(
    bundle: NormalizedBundle,
    endpoint: Any,
    index: int,
    coverage_terms: list[str] | None,
    task_prefix: str,
) -> dict[str, Any]:
    domain = endpoint_domain(endpoint, coverage_terms)
    query = natural_query_for_endpoint(endpoint, index)
    return {
        "id": f"{task_prefix}_{index:03d}",
        "query": query,
        "router_query": query,
        "track": "recovery_followup",
        "resource": domain,
        "operation_class": endpoint.operation_class,
        "expected_decision_type": "BLOCK_UNSAFE",
        "expected_endpoint_sequence": [endpoint.id],
        "expected_required_params": {endpoint.id: endpoint.required_params} if endpoint.required_params else {},
        "provided_params": provided_inputs_for_endpoint(bundle, endpoint),
        "expected_follow_up": "Ask for explicit confirmation before any destructive write.",
        "allowed_alternatives": [],
        "task_type": "unsafe_write",
        "notes": f"resource={domain}; expected_behavior=block_without_confirmation",
        "provenance": endpoint_provenance(endpoint),
    }


def ambiguous_endpoint_groups(
    endpoints: list[Any],
    coverage_terms: list[str] | None,
    limit: int,
) -> list[list[Any]]:
    groups: list[list[Any]] = []
    by_key: dict[tuple[str, str], list[Any]] = defaultdict(list)
    for endpoint in endpoints:
        by_key[(endpoint_domain(endpoint, coverage_terms), endpoint.operation_class)].append(endpoint)
    for (_domain, _operation_class), candidates in sorted(by_key.items()):
        if len(candidates) < 2:
            continue
        ordered = sorted(candidates, key=lambda endpoint: endpoint.id)
        for idx, endpoint in enumerate(ordered):
            scored = [
                (path_similarity(endpoint.path, other.path), other)
                for other in ordered
                if other.id != endpoint.id
            ]
            scored.sort(key=lambda item: (item[0], item[1].id), reverse=True)
            if scored:
                groups.append([endpoint, scored[0][1]])
            if len(groups) >= limit:
                return groups
    return groups


def generate_natural_tasks(
    bundle: NormalizedBundle,
    min_count: int = 100,
    coverage_terms: list[str] | None = None,
    task_prefix: str = "natural",
) -> list[dict[str, Any]]:
    coverage = [slugify(term) for term in (coverage_terms or derive_coverage_terms(bundle)) if slugify(term)]
    endpoints = sorted(
        bundle.endpoints,
        key=lambda endpoint: (
            endpoint_domain(endpoint, coverage) not in coverage,
            endpoint_domain(endpoint, coverage),
            endpoint.operation_class,
            endpoint.id,
        ),
    )
    tasks: list[dict[str, Any]] = []
    index = 1
    for endpoint in endpoints:
        tasks.append(natural_task_from_endpoint(bundle, endpoint, index, coverage, endpoints, task_prefix))
        index += 1
        if len(tasks) >= min_count:
            break
    while len(tasks) < min_count and endpoints:
        endpoint = endpoints[len(tasks) % len(endpoints)]
        tasks.append(natural_task_from_endpoint(bundle, endpoint, index, coverage, endpoints, task_prefix))
        index += 1
    return tasks


def conversation_context_for_endpoint(bundle: NormalizedBundle, endpoint: Any, coverage_terms: list[str] | None = None) -> dict[str, Any]:
    context = provided_inputs_for_endpoint(bundle, endpoint)
    context.update(
        {
            "resource": endpoint_domain(endpoint, coverage_terms),
            "resource_terms": list(getattr(endpoint, "resources", []) or []),
            "operation_class": getattr(endpoint, "operation_class", ""),
            "operation_terms": [getattr(endpoint, "operation_class", "")],
            "selected_endpoint_id": getattr(endpoint, "id", ""),
            "selected_endpoint_summary": readable_endpoint_label(endpoint),
        }
    )
    return context


def context_task_from_endpoint(
    bundle: NormalizedBundle,
    endpoint: Any,
    index: int,
    coverage_terms: list[str] | None,
    endpoints: list[Any],
    task_prefix: str,
) -> dict[str, Any]:
    domain = endpoint_domain(endpoint, coverage_terms)
    query_templates = [
        "do that for this one",
        f"same thing for this {domain}",
        "now use the item we discussed",
        "run that lookup with the current context",
    ]
    return {
        "id": f"{task_prefix}_{index:03d}",
        "query": query_templates[(index - 1) % len(query_templates)],
        "router_query": query_templates[(index - 1) % len(query_templates)],
        "resource": domain,
        "operation_class": endpoint.operation_class,
        "track": "conversation_context",
        "expected_decision_type": "ROUTE",
        "expected_endpoint_sequence": [endpoint.id],
        "expected_required_params": {endpoint.id: list(endpoint.required_params)} if endpoint.required_params else {},
        "provided_params": {},
        "conversation_context": conversation_context_for_endpoint(bundle, endpoint, coverage_terms),
        "allowed_alternatives": allowed_alternatives_for_endpoint(endpoint, endpoints, coverage_terms),
        "task_type": "context_followup",
        "notes": f"resource={domain}; expected_behavior=resolve_from_conversation_context",
        "provenance": endpoint_provenance(endpoint),
    }


def generate_context_tasks(
    bundle: NormalizedBundle,
    min_count: int = 50,
    coverage_terms: list[str] | None = None,
    task_prefix: str = "context",
) -> list[dict[str, Any]]:
    coverage = coverage_terms or derive_coverage_terms(bundle)
    endpoints = [
        endpoint
        for endpoint in bundle.endpoints
        if endpoint.operation_class in {"get", "update", "delete", "custom", "create", "list", "search"}
    ]
    prioritized = sorted(
        endpoints,
        key=lambda endpoint: (
            endpoint.operation_class != "get",
            endpoint_domain(endpoint, coverage),
            endpoint.operation_class,
            endpoint.path,
            endpoint.operation_id,
        ),
    )
    tasks: list[dict[str, Any]] = []
    index = 1
    for endpoint in prioritized:
        tasks.append(context_task_from_endpoint(bundle, endpoint, index, coverage, endpoints, task_prefix))
        index += 1
        if len(tasks) >= min_count:
            break
    while len(tasks) < min_count and prioritized:
        endpoint = prioritized[len(tasks) % len(prioritized)]
        tasks.append(context_task_from_endpoint(bundle, endpoint, index, coverage, endpoints, task_prefix))
        index += 1
    return tasks


def generate_recovery_tasks(
    bundle: NormalizedBundle,
    min_missing_param: int = 25,
    min_ambiguous: int = 25,
    min_policy: int = 25,
    min_unsafe: int = 10,
    coverage_terms: list[str] | None = None,
    task_prefix: str = "recovery",
) -> list[dict[str, Any]]:
    coverage = [slugify(term) for term in (coverage_terms or derive_coverage_terms(bundle)) if slugify(term)]
    endpoints = sorted(
        bundle.endpoints,
        key=lambda endpoint: (
            endpoint_domain(endpoint, coverage) not in coverage,
            endpoint_domain(endpoint, coverage),
            endpoint.operation_class,
            endpoint.id,
        ),
    )
    tasks: list[dict[str, Any]] = []
    index = 1

    missing_candidates = [
        endpoint
        for endpoint in endpoints
        if endpoint.required_params or endpoint_required_body_fields(bundle, endpoint)
    ]
    for endpoint in missing_candidates:
        tasks.append(recovery_missing_param_task_from_endpoint(bundle, endpoint, index, coverage, endpoints, task_prefix))
        index += 1
        if sum(1 for task in tasks if task["expected_decision_type"] == "ASK_PARAM") >= min_missing_param:
            break

    ambiguous_groups = ambiguous_endpoint_groups(endpoints, coverage, min_ambiguous)
    if len(ambiguous_groups) < min_ambiguous:
        by_domain: dict[str, list[Any]] = defaultdict(list)
        for endpoint in endpoints:
            by_domain[endpoint_domain(endpoint, coverage)].append(endpoint)
        for _domain, candidates in sorted(by_domain.items()):
            if len(candidates) >= 2:
                ambiguous_groups.append(candidates[:2])
            if len(ambiguous_groups) >= min_ambiguous:
                break

    for group in ambiguous_groups:
        tasks.append(make_recovery_ambiguous_task(group, index, coverage, task_prefix))
        index += 1
        if sum(1 for task in tasks if task["expected_decision_type"] == "ASK_DISAMBIGUATE") >= min_ambiguous:
            break

    unsafe_candidates = [
        endpoint
        for endpoint in endpoints
        if endpoint.method.upper() == "DELETE" or endpoint.operation_class == "delete"
    ]
    for endpoint in unsafe_candidates:
        tasks.append(recovery_unsafe_task_from_endpoint(bundle, endpoint, index, coverage, task_prefix))
        index += 1
        if sum(1 for task in tasks if task["expected_decision_type"] == "BLOCK_UNSAFE") >= min_unsafe:
            break

    domains = coverage or sorted({endpoint_domain(endpoint, coverage) for endpoint in endpoints}) or ["general"]
    while sum(1 for task in tasks if task["expected_decision_type"] == "ASK_POLICY") < min_policy:
        domain = domains[(index - 1) % len(domains)]
        tasks.append(make_recovery_policy_task(domain, index, task_prefix))
        index += 1

    return tasks


def generate_low_overlap_tasks(
    bundle: NormalizedBundle,
    min_routing: int = 100,
    min_ambiguous: int = 50,
    min_policy: int = 50,
    coverage_terms: list[str] | None = None,
    task_prefix: str = "low",
) -> list[dict[str, Any]]:
    coverage = [slugify(term) for term in (coverage_terms or derive_coverage_terms(bundle)) if slugify(term)]
    endpoints = sorted(
        bundle.endpoints,
        key=lambda endpoint: (
            endpoint_domain(endpoint, coverage) not in coverage,
            endpoint_domain(endpoint, coverage),
            endpoint.operation_class,
            endpoint.id,
        ),
    )
    tasks: list[dict[str, Any]] = []
    index = 1

    for endpoint in endpoints:
        task = low_overlap_task_from_endpoint(endpoint, index, coverage, endpoints, task_prefix)
        if task is None:
            continue
        tasks.append(task)
        index += 1
        if sum(1 for item in tasks if item["task_type"] == "single_step") >= min_routing:
            break
    routing_count = sum(1 for item in tasks if item["task_type"] == "single_step")
    if routing_count < min_routing:
        raise ValueError(f"Could only generate {routing_count} low-overlap routing tasks; required {min_routing}")

    for group in ambiguous_endpoint_groups(endpoints, coverage, min_ambiguous):
        tasks.append(make_ambiguous_task(group, index, coverage, task_prefix))
        index += 1
        if sum(1 for item in tasks if item["task_type"] == "ambiguous") >= min_ambiguous:
            break
    ambiguous_count = sum(1 for item in tasks if item["task_type"] == "ambiguous")
    if ambiguous_count < min_ambiguous:
        raise ValueError(f"Could only generate {ambiguous_count} ambiguous tasks; required {min_ambiguous}")

    domains = coverage or sorted({endpoint_domain(endpoint, coverage) for endpoint in endpoints})
    while sum(1 for item in tasks if item["task_type"] == "policy_required") < min_policy:
        domain = domains[(index - 1) % len(domains)] if domains else "general"
        tasks.append(make_low_overlap_policy_task(domain, index, task_prefix))
        index += 1

    return tasks


def generate_tasks(
    bundle: NormalizedBundle,
    min_count: int = 100,
    coverage_terms: list[str] | None = None,
    task_prefix: str = "task",
) -> list[dict[str, Any]]:
    coverage = [slugify(term) for term in (coverage_terms or derive_coverage_terms(bundle)) if slugify(term)]
    endpoints = sorted(
        bundle.endpoints,
        key=lambda endpoint: (
            endpoint_domain(endpoint, coverage) not in coverage,
            endpoint_domain(endpoint, coverage),
            endpoint.operation_class,
            endpoint.id,
        ),
    )
    tasks: list[dict[str, Any]] = []
    index = 1

    for domain in coverage:
        domain_endpoints = [endpoint for endpoint in endpoints if endpoint_domain(endpoint, coverage) == domain]
        for operation_class in TASK_OPERATION_ORDER:
            selected = next((endpoint for endpoint in domain_endpoints if endpoint.operation_class == operation_class), None)
            if selected:
                tasks.append(task_from_endpoint(selected, index, coverage, endpoints, task_prefix=task_prefix))
                index += 1

    for endpoint in endpoints:
        if len(tasks) >= min_count - 10:
            break
        tasks.append(task_from_endpoint(endpoint, index, coverage, endpoints, task_prefix=task_prefix))
        index += 1

    read_by_domain = {}
    write_by_domain = {}
    for endpoint in endpoints:
        domain = endpoint_domain(endpoint, coverage)
        if endpoint.operation_class in READ_OPERATION_CLASSES and domain not in read_by_domain:
            read_by_domain[domain] = endpoint
        if endpoint.operation_class in WRITE_OPERATION_CLASSES and domain not in write_by_domain:
            write_by_domain[domain] = endpoint
    for domain, first in read_by_domain.items():
        second = write_by_domain.get(domain)
        if not second:
            continue
        tasks.append(
            {
                "id": f"{task_prefix}_{index:03d}",
                "query": f"{readable_endpoint_label(first)} then prepare {readable_endpoint_label(second)} as a dry run for {domain}",
                "router_query": f"{readable_endpoint_label(first)} then prepare {readable_endpoint_label(second)} as a dry run for {domain}",
                "resource": domain,
                "operation_class": "multi_step",
                "track": "spec_close_smoke",
                "expected_decision_type": "ROUTE",
                "expected_endpoint_sequence": [first.id, second.id],
                "expected_required_params": {
                    endpoint.id: endpoint.required_params
                    for endpoint in [first, second]
                    if endpoint.required_params
                },
                "allowed_alternatives": [],
                "task_type": "multi_step",
                "notes": f"resource={domain}; generated_multi_step_from={first.id},{second.id}",
                "provenance": {
                    "steps": [endpoint_provenance(first), endpoint_provenance(second)],
                },
            }
        )
        index += 1
        if len(tasks) >= min_count - 4:
            break

    for domain in coverage[:4]:
        tasks.append(make_policy_task(domain, index, task_prefix))
        index += 1

    while len(tasks) < min_count and endpoints:
        endpoint = endpoints[(len(tasks) - 1) % len(endpoints)]
        task = task_from_endpoint(endpoint, index, coverage, endpoints, task_prefix=task_prefix)
        task["query"] = f"{task['query']} for workflow coverage"
        task["router_query"] = task["query"]
        tasks.append(task)
        index += 1

    return tasks


def read_coverage_terms(path: Path | None) -> list[str] | None:
    if not path:
        return None
    payload = json.loads(path.read_text(encoding="utf-8"))
    if isinstance(payload, list):
        return [str(item) for item in payload]
    if isinstance(payload, dict) and isinstance(payload.get("coverage_terms"), list):
        return [str(item) for item in payload["coverage_terms"]]
    raise ValueError("coverage file must be a JSON list or an object with coverage_terms")


def write_tasks(tasks: list[dict[str, Any]], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(tasks, indent=2), encoding="utf-8")


def read_tasks(path: Path) -> list[dict[str, Any]]:
    return json.loads(path.read_text(encoding="utf-8"))
