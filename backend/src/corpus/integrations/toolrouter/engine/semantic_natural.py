from __future__ import annotations

import json
import re
import time
from pathlib import Path
from typing import Any

from .ladder_llm import stable_hash, write_llm_audit
from .ladder_runtime import LadderRuntimeConfig
from .openapi_loader import NormalizedBundle, normalize_text, slugify
from .tasks import (
    allowed_alternatives_for_endpoint,
    derive_coverage_terms,
    endpoint_domain,
    endpoint_provenance,
    endpoint_required_body_fields,
    humanize_identifier,
    provided_inputs_for_endpoint,
    readable_endpoint_label,
)


SEMANTIC_NO_EXACT_TRACK = "semantic_natural_no_exact"

GENERIC_FORBIDDEN_ALLOWLIST = {
    "api",
    "app",
    "body",
    "data",
    "from",
    "http",
    "into",
    "json",
    "one",
    "page",
    "post",
    "put",
    "the",
    "this",
    "that",
    "using",
    "with",
}


def _word_tokens(value: str) -> list[str]:
    return re.findall(r"[a-z0-9]+", normalize_text(value))


def _surface_texts(endpoint: Any) -> list[str]:
    texts = [
        str(getattr(endpoint, "operation_id", "") or ""),
        str(getattr(endpoint, "path", "") or ""),
        str(getattr(endpoint, "summary", "") or ""),
        str(getattr(endpoint, "description", "") or ""),
        " ".join(str(item) for item in getattr(endpoint, "tags", []) or []),
        " ".join(str(item) for item in getattr(endpoint, "resources", []) or []),
        " ".join(str(item) for item in getattr(endpoint, "request_schemas", []) or []),
        " ".join(str(item) for item in getattr(endpoint, "response_schemas", []) or []),
        " ".join(str(item) for item in getattr(endpoint, "required_params", []) or []),
    ]
    return [text for text in texts if text.strip()]


def forbidden_surface_terms(bundle: NormalizedBundle, endpoint: Any) -> list[str]:
    tokens: set[str] = set()
    for text in _surface_texts(endpoint):
        for token in _word_tokens(humanize_identifier(text)):
            if len(token) >= 3 and token not in GENERIC_FORBIDDEN_ALLOWLIST:
                tokens.add(token)
    for field_name in endpoint_required_body_fields(bundle, endpoint):
        for token in _word_tokens(humanize_identifier(field_name)):
            if len(token) >= 3 and token not in GENERIC_FORBIDDEN_ALLOWLIST:
                tokens.add(token)
    return sorted(tokens)


def query_forbidden_hits(query: str, forbidden_terms: list[str]) -> list[str]:
    query_tokens = set(_word_tokens(query))
    return sorted(query_tokens & set(forbidden_terms))


def validate_semantic_query(query: str, forbidden_terms: list[str]) -> tuple[bool, list[str], str]:
    cleaned = " ".join(str(query or "").split())
    if not cleaned:
        return False, [], "empty_query"
    word_count = len(cleaned.split())
    if word_count < 5:
        return False, [], "too_short"
    if word_count > 24:
        return False, [], "too_long"
    if "/" in cleaned or "{" in cleaned or "}" in cleaned:
        return False, [], "contains_api_path_syntax"
    hits = query_forbidden_hits(cleaned, forbidden_terms)
    if hits:
        return False, hits, "contains_forbidden_api_terms"
    return True, [], "ok"


def semantic_task_from_endpoint(
    bundle: NormalizedBundle,
    endpoint: Any,
    *,
    index: int,
    query: str,
    coverage_terms: list[str] | None,
    endpoints: list[Any],
    task_prefix: str,
    model: str,
    forbidden_terms: list[str],
    generation_attempts: int,
    strategy: str = "",
) -> dict[str, Any]:
    domain = endpoint_domain(endpoint, coverage_terms)
    cleaned_query = " ".join(query.split())
    return {
        "id": f"{task_prefix}_{index:03d}",
        "query": cleaned_query,
        "router_query": cleaned_query,
        "track": SEMANTIC_NO_EXACT_TRACK,
        "resource": domain,
        "operation_class": endpoint.operation_class,
        "expected_decision_type": "ROUTE",
        "expected_endpoint_sequence": [endpoint.id],
        "expected_required_params": {endpoint.id: endpoint.required_params} if endpoint.required_params else {},
        "provided_params": provided_inputs_for_endpoint(bundle, endpoint),
        "allowed_alternatives": allowed_alternatives_for_endpoint(endpoint, endpoints, coverage_terms),
        "task_type": "single_step",
        "notes": "track=semantic_natural_no_exact; generator=gpt-5-mini; exact_api_surface_terms_forbidden",
        "semantic_generation": {
            "model": model,
            "strategy": strategy,
            "forbidden_terms": forbidden_terms,
            "forbidden_term_hits": [],
            "attempts": generation_attempts,
        },
        "provenance": endpoint_provenance(endpoint),
    }


def _endpoint_payload(bundle: NormalizedBundle, endpoint: Any) -> dict[str, Any]:
    forbidden = forbidden_surface_terms(bundle, endpoint)
    return {
        "endpoint_id": endpoint.id,
        "method": endpoint.method,
        "path": endpoint.path,
        "operation_id": endpoint.operation_id,
        "summary": endpoint.summary,
        "description": endpoint.description[:900] if endpoint.description else "",
        "operation_class": endpoint.operation_class,
        "required_params": list(endpoint.required_params),
        "request_schemas": list(endpoint.request_schemas),
        "response_schemas": list(endpoint.response_schemas),
        "resources": list(endpoint.resources),
        "forbidden_terms": forbidden,
    }


def _cache_path(runtime: LadderRuntimeConfig, model: str, endpoint_payload: dict[str, Any]) -> Path:
    key = stable_hash({"task": "semantic_no_exact_query", "model": model, "endpoint": endpoint_payload, "version": 1})
    return runtime.cache_dir / "semantic_no_exact" / f"{key}.json"


def _call_openai_batch(
    endpoint_payloads: list[dict[str, Any]],
    *,
    runtime: LadderRuntimeConfig,
    audit_path: Path,
    attempt: int,
) -> list[dict[str, Any]]:
    if not runtime.openai_api_key_available:
        raise RuntimeError(f"{runtime.openai_key_env} is required for semantic no-exact query generation.")

    from openai import OpenAI

    payload = {
        "task": "generate_semantic_no_exact_toolrouter_queries",
        "rules": [
            "Return one natural user request per endpoint.",
            "Do not copy any forbidden term for that endpoint.",
            "Use everyday language and synonyms instead of API, path, schema, tag, or operation words.",
            "Do not mention endpoint IDs, paths, HTTP methods, parameter names, schema names, or product-specific API nouns.",
            "Keep each query between 5 and 24 words.",
            "The query must still imply the same endpoint intent.",
        ],
        "items": endpoint_payloads,
        "output_schema": {
            "items": [
                {
                    "endpoint_id": "string copied from input",
                    "query": "natural language user request",
                    "strategy": "short explanation of the synonym strategy",
                }
            ]
        },
    }
    started = time.perf_counter()
    client = OpenAI(api_key=runtime.openai_api_key, timeout=180.0)
    response = client.responses.create(
        model=runtime.llm_model,
        input=[
            {
                "role": "system",
                "content": "You create hard OpenAPI router evaluation queries. Output valid JSON only.",
            },
            {"role": "user", "content": json.dumps(payload, sort_keys=True)},
        ],
        text={"format": {"type": "json_object"}},
    max_output_tokens=8000,
    )
    text = getattr(response, "output_text", "") or "{}"
    try:
        parsed = json.loads(text)
    except json.JSONDecodeError as exc:
        raise ValueError(f"GPT response was not valid JSON: {exc}") from exc
    rows = parsed.get("items", [])
    if not isinstance(rows, list):
        raise ValueError("GPT response did not contain an items list.")
    write_llm_audit(
        audit_path,
        stage_component="semantic_no_exact_query_generation",
        model=runtime.llm_model,
        mode="openai",
        input_hash=stable_hash(payload),
        output_hash=stable_hash(parsed),
        endpoint_ids_visible=True,
        latency_ms=(time.perf_counter() - started) * 1000.0,
        cache_hit=False,
        status=f"attempt_{attempt}",
    )
    return [row for row in rows if isinstance(row, dict)]


def _load_cached_query(cache_path: Path, forbidden_terms: list[str]) -> dict[str, Any] | None:
    if not cache_path.exists():
        return None
    cached = json.loads(cache_path.read_text(encoding="utf-8"))
    query = str(cached.get("query") or "")
    valid, hits, reason = validate_semantic_query(query, forbidden_terms)
    if valid:
        return cached
    cached["invalid_reason"] = reason
    cached["forbidden_term_hits"] = hits
    return None


def generate_semantic_natural_tasks(
    bundle: NormalizedBundle,
    *,
    runtime: LadderRuntimeConfig,
    min_count: int = 100,
    task_prefix: str = "semantic",
    coverage_terms: list[str] | None = None,
    audit_path: Path,
    batch_size: int = 2,
    max_retries: int = 5,
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
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
    failures: list[dict[str, Any]] = []
    index = 1

    pending = endpoints[:]
    attempts_by_endpoint: dict[str, int] = {endpoint.id: 0 for endpoint in endpoints}

    while pending and len(tasks) < min_count:
        batch_endpoints = pending[:batch_size]
        pending = pending[batch_size:]
        payloads: list[dict[str, Any]] = []
        payload_by_id: dict[str, dict[str, Any]] = {}
        endpoint_by_id: dict[str, Any] = {}
        cached_rows: dict[str, dict[str, Any]] = {}

        for endpoint in batch_endpoints:
            payload = _endpoint_payload(bundle, endpoint)
            cache_path = _cache_path(runtime, runtime.llm_model, payload)
            cached = _load_cached_query(cache_path, payload["forbidden_terms"])
            if cached is not None:
                cached_rows[endpoint.id] = cached
                continue
            payloads.append(payload)
            payload_by_id[endpoint.id] = payload
            endpoint_by_id[endpoint.id] = endpoint

        rows_by_id = {endpoint_id: row for endpoint_id, row in cached_rows.items()}
        batch_error = ""
        if payloads:
            try:
                rows = _call_openai_batch(payloads, runtime=runtime, audit_path=audit_path, attempt=1)
            except Exception as exc:
                batch_error = f"{type(exc).__name__}: {exc}"
                rows = []
            rows_by_id.update({str(row.get("endpoint_id")): row for row in rows if row.get("endpoint_id")})

        retry_endpoints: list[Any] = []
        retry_reasons: dict[str, dict[str, Any]] = {}
        for endpoint in batch_endpoints:
            payload = payload_by_id.get(endpoint.id) or _endpoint_payload(bundle, endpoint)
            forbidden = payload["forbidden_terms"]
            if batch_error and endpoint.id in payload_by_id:
                retry_endpoints.append(endpoint)
                retry_reasons[endpoint.id] = {"query": "", "reason": "batch_generation_error", "error": batch_error}
                continue
            row = rows_by_id.get(endpoint.id, {})
            query = str(row.get("query") or "")
            valid, hits, reason = validate_semantic_query(query, forbidden)
            if not valid:
                retry_endpoints.append(endpoint)
                retry_reasons[endpoint.id] = {"query": query, "reason": reason, "hits": hits}
                continue
            cache_path = _cache_path(runtime, runtime.llm_model, payload)
            cache_path.parent.mkdir(parents=True, exist_ok=True)
            cache_path.write_text(json.dumps(row, indent=2, sort_keys=True), encoding="utf-8")
            tasks.append(
                semantic_task_from_endpoint(
                    bundle,
                    endpoint,
                    index=index,
                    query=query,
                    coverage_terms=coverage,
                    endpoints=endpoints,
                    task_prefix=task_prefix,
                    model=runtime.llm_model,
                    forbidden_terms=forbidden,
                    generation_attempts=max(1, attempts_by_endpoint.get(endpoint.id, 0) + 1),
                    strategy=str(row.get("strategy") or ""),
                )
            )
            index += 1
            if len(tasks) >= min_count:
                break

        for endpoint in retry_endpoints:
            attempts_by_endpoint[endpoint.id] += 1
            if attempts_by_endpoint[endpoint.id] < max_retries:
                pending.append(endpoint)
            else:
                failures.append(
                    {
                        "endpoint_id": endpoint.id,
                        "label": readable_endpoint_label(endpoint),
                        "attempts": attempts_by_endpoint[endpoint.id],
                        **retry_reasons.get(endpoint.id, {}),
                    }
                )

    if len(tasks) < min_count:
        raise RuntimeError(
            f"Generated {len(tasks)} valid semantic no-exact tasks, below required {min_count}. "
            f"Failures: {json.dumps(failures[:20], sort_keys=True)}"
        )

    manifest = {
        "track": SEMANTIC_NO_EXACT_TRACK,
        "model": runtime.llm_model,
        "task_count": len(tasks),
        "requested_min_count": min_count,
        "candidate_endpoint_count": len(endpoints),
        "failure_count": len(failures),
        "failures": failures,
    }
    return tasks[:min_count], manifest
