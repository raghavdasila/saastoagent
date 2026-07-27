from __future__ import annotations

import hashlib
import json
import threading
import time
from pathlib import Path
from typing import Any

from .ladder_runtime import LadderRuntimeConfig


_JSONL_APPEND_LOCK = threading.Lock()


def stable_hash(payload: Any) -> str:
    encoded = json.dumps(payload, sort_keys=True, ensure_ascii=True).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def append_jsonl(path: Path, row: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with _JSONL_APPEND_LOCK:
        with path.open("a", encoding="utf-8") as fh:
            fh.write(json.dumps(row, sort_keys=True) + "\n")


def read_llm_audit_rows(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def fake_canonical_response(query: str, conversation_context: dict[str, Any] | None = None) -> dict[str, Any]:
    context = conversation_context or {}
    terms = [query.strip()]
    for key in ["last_resource", "resource", "last_operation_class", "operation_class"]:
        value = context.get(key)
        if value:
            terms.append(str(value))
    lowered = " ".join(terms).lower()
    return {
        "canonical_query": " ".join(terms).strip(),
        "likely_resource_terms": [str(context[key]) for key in ["last_resource", "resource"] if context.get(key)],
        "likely_operation_terms": [str(context[key]) for key in ["last_operation_class", "operation_class"] if context.get(key)],
        "missing_information": [],
        "policy_gap": any(term in lowered for term in ["policy", "allowed", "eligible", "qualify"]),
        "safety_concern": any(term in lowered for term in ["delete", "remove", "irreversible"]),
    }


def write_llm_audit(
    audit_path: Path,
    *,
    stage_component: str,
    model: str,
    mode: str,
    input_hash: str,
    output_hash: str,
    endpoint_ids_visible: bool,
    latency_ms: float,
    cache_hit: bool,
    cost_estimate_usd: float = 0.0,
    status: str = "ok",
) -> None:
    append_jsonl(
        audit_path,
        {
            "stage_component": stage_component,
            "model": model,
            "mode": mode,
            "input_hash": input_hash,
            "output_hash": output_hash,
            "endpoint_ids_visible": endpoint_ids_visible,
            "latency_ms": latency_ms,
            "cache_hit": cache_hit,
            "cost_estimate_usd": cost_estimate_usd,
            "status": status,
        },
    )


def canonicalize_query(
    query: str,
    *,
    conversation_context: dict[str, Any] | None,
    runtime: LadderRuntimeConfig,
    audit_path: Path,
) -> dict[str, Any]:
    started = time.perf_counter()
    payload = {
        "task": "canonicalize_query",
        "query": query,
        "conversation_context": conversation_context or {},
        "schema": {
            "canonical_query": "string",
            "likely_resource_terms": "list[string]",
            "likely_operation_terms": "list[string]",
            "missing_information": "list[string]",
            "policy_gap": "boolean",
            "safety_concern": "boolean",
        },
    }
    key = stable_hash({"model": runtime.llm_model, "payload": payload, "version": 1})
    cache_path = runtime.cache_dir / "llm" / f"{key}.json"
    cache_hit = cache_path.exists()
    mode = runtime.llm_mode
    if cache_hit:
        result = json.loads(cache_path.read_text(encoding="utf-8"))
    elif mode == "fake" or not runtime.openai_api_key_available:
        result = fake_canonical_response(query, conversation_context)
        cache_path.parent.mkdir(parents=True, exist_ok=True)
        cache_path.write_text(json.dumps(result, indent=2, sort_keys=True), encoding="utf-8")
        mode = "fake" if mode == "fake" else "fallback_fake_no_key"
    else:
        try:
            from openai import OpenAI

            client = OpenAI(api_key=runtime.openai_api_key, timeout=60.0)
            response = client.responses.create(
                model=runtime.llm_model,
                input=[
                    {
                        "role": "system",
                        "content": "Rewrite the user request into OpenAPI routing intent JSON. Do not choose endpoint IDs.",
                    },
                    {"role": "user", "content": json.dumps(payload, sort_keys=True)},
                ],
                text={"format": {"type": "json_object"}},
                max_output_tokens=500,
            )
            text = getattr(response, "output_text", "") or "{}"
            result = json.loads(text)
            cache_path.parent.mkdir(parents=True, exist_ok=True)
            cache_path.write_text(json.dumps(result, indent=2, sort_keys=True), encoding="utf-8")
            mode = "openai"
        except Exception:
            if runtime.openai_api_key_available and runtime.llm_mode != "fake":
                raise
            result = fake_canonical_response(query, conversation_context)
            mode = "fallback_fake_error"
    latency_ms = (time.perf_counter() - started) * 1000.0
    write_llm_audit(
        audit_path,
        stage_component="canonicalization",
        model=runtime.llm_model,
        mode=mode,
        input_hash=stable_hash(payload),
        output_hash=stable_hash(result),
        endpoint_ids_visible=False,
        latency_ms=latency_ms,
        cache_hit=cache_hit,
    )
    return result


def rerank_candidate_ids(
    query: str,
    candidates: list[dict[str, Any]],
    *,
    runtime: LadderRuntimeConfig,
    audit_path: Path,
    require_live_or_cache: bool = False,
) -> list[str]:
    started = time.perf_counter()
    allowed = [str(candidate.get("endpoint_id")) for candidate in candidates if candidate.get("endpoint_id")]
    payload = {
        "task": "rerank_candidates",
        "query": query,
        "candidates": [
            {
                "endpoint_id": candidate.get("endpoint_id"),
                "method": candidate.get("method"),
                "path": candidate.get("path"),
                "summary": candidate.get("summary"),
                "required_params": candidate.get("required_params", []),
            }
            for candidate in candidates
        ],
    }
    key = stable_hash({"model": runtime.llm_model, "payload": payload, "version": 1})
    cache_path = runtime.cache_dir / "llm" / f"{key}.json"
    cache_hit = cache_path.exists()
    mode = runtime.llm_mode
    if cache_hit:
        ranked = json.loads(cache_path.read_text(encoding="utf-8")).get("ranked_endpoint_ids", allowed)
    elif require_live_or_cache and (mode == "fake" or not runtime.openai_api_key_available):
        raise RuntimeError("LLM reranking requires an OpenAI API key or an existing live cache entry; fake fallback is disabled for this stage.")
    elif mode == "fake" or not runtime.openai_api_key_available:
        ranked = allowed
        cache_path.parent.mkdir(parents=True, exist_ok=True)
        cache_path.write_text(json.dumps({"ranked_endpoint_ids": ranked}, indent=2), encoding="utf-8")
        mode = "fake" if mode == "fake" else "fallback_fake_no_key"
    else:
        try:
            from openai import OpenAI

            output_text = "{}"
            for attempt in range(3):
                try:
                    client = OpenAI(api_key=runtime.openai_api_key, timeout=60.0)
                    response = client.responses.create(
                        model=runtime.llm_model,
                        input=[
                            {
                                "role": "system",
                                "content": "Rerank only the provided endpoint IDs. Return JSON with ranked_endpoint_ids.",
                            },
                            {"role": "user", "content": json.dumps(payload, sort_keys=True)},
                        ],
                        text={"format": {"type": "json_object"}},
                        max_output_tokens=1500,
                    )
                    output_text = getattr(response, "output_text", "") or "{}"
                    break
                except Exception:
                    if attempt >= 2:
                        raise
                    time.sleep(2.0 * (attempt + 1))
            try:
                data = json.loads(output_text)
                ranked = [endpoint_id for endpoint_id in data.get("ranked_endpoint_ids", []) if endpoint_id in allowed]
            except json.JSONDecodeError:
                visible = [(output_text.find(endpoint_id), endpoint_id) for endpoint_id in allowed if endpoint_id in output_text]
                if visible:
                    ranked = [endpoint_id for _index, endpoint_id in sorted(visible)]
                    mode = "openai_repaired_text"
                else:
                    ranked = list(allowed)
                    mode = "openai_unusable_original_order"
            ranked.extend(endpoint_id for endpoint_id in allowed if endpoint_id not in ranked)
            cache_path.parent.mkdir(parents=True, exist_ok=True)
            cache_path.write_text(json.dumps({"ranked_endpoint_ids": ranked}, indent=2), encoding="utf-8")
            mode = "openai"
        except Exception:
            if runtime.openai_api_key_available and runtime.llm_mode != "fake":
                raise
            ranked = allowed
            mode = "fallback_fake_error"
    write_llm_audit(
        audit_path,
        stage_component="candidate_rerank",
        model=runtime.llm_model,
        mode=mode,
        input_hash=stable_hash(payload),
        output_hash=stable_hash(ranked),
        endpoint_ids_visible=True,
        latency_ms=(time.perf_counter() - started) * 1000.0,
        cache_hit=cache_hit,
    )
    return ranked
