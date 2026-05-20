from __future__ import annotations

import json
import os
import re
from typing import Any
from urllib.request import Request, urlopen

from .schemas import ChatRouteInput


DEFAULT_ROUTER_MODEL = "gpt-5-nano"
ASSIGNMENT_RE = re.compile(r"(?P<key>[A-Za-z_][A-Za-z0-9_.-]*)=(?P<value>[^\s,]+)")


def _extract_assignments(text: str) -> dict[str, str]:
    return {match.group("key"): match.group("value").strip("'\"") for match in ASSIGNMENT_RE.finditer(text or "")}


def _context_params(conversation_context: list[dict[str, Any]] | None) -> tuple[dict[str, Any], bool, str]:
    params: dict[str, Any] = {}
    confirmed = False
    policy_text = ""
    for item in conversation_context or []:
        if not isinstance(item, dict):
            continue
        if isinstance(item.get("provided_params"), dict):
            params.update(item["provided_params"])
        if item.get("confirmed") is True or str(item.get("confirmation", "")).casefold() in {"yes", "confirmed", "approve"}:
            confirmed = True
        if item.get("policy_text"):
            policy_text = str(item["policy_text"])
    return params, confirmed, policy_text


def deterministic_normalize(user_query: str, conversation_context: list[dict[str, Any]] | None = None) -> ChatRouteInput:
    params, confirmed, policy_text = _context_params(conversation_context)
    params.update(_extract_assignments(user_query))
    lowered = user_query.casefold()
    if any(token in lowered for token in ("confirm", "approved", "go ahead", "yes execute")):
        confirmed = True
    router_query = ASSIGNMENT_RE.sub("", user_query).strip()
    return ChatRouteInput(
        router_query=router_query or user_query,
        provided_params=params,
        confirmed=confirmed,
        policy_text=policy_text,
    )


def _coerce_normalized(payload: dict[str, Any], fallback_query: str, conversation_context: list[dict[str, Any]] | None) -> ChatRouteInput:
    deterministic = deterministic_normalize(fallback_query, conversation_context)
    allowed = {
        "router_query": str(payload.get("router_query") or deterministic.router_query),
        "provided_params": payload.get("provided_params") if isinstance(payload.get("provided_params"), dict) else deterministic.provided_params,
        "confirmed": bool(payload.get("confirmed", deterministic.confirmed)),
        "policy_text": str(payload.get("policy_text") or deterministic.policy_text),
    }
    return ChatRouteInput(**allowed)


def normalize_chat_request(
    *,
    user_query: str,
    conversation_context: list[dict[str, Any]] | None,
    model: str | None = None,
    openai_api_key: str | None = None,
    client: Any | None = None,
    use_model: bool = False,
) -> ChatRouteInput:
    if client is not None:
        return _coerce_normalized(client.normalize(user_query=user_query, conversation_context=conversation_context), user_query, conversation_context)
    api_key = openai_api_key or os.getenv("OPENAI_API_KEY")
    if not use_model or not api_key:
        return deterministic_normalize(user_query, conversation_context)
    payload = {
        "model": model or os.getenv("OPENAI_ROUTER_MODEL") or DEFAULT_ROUTER_MODEL,
        "input": [
            {
                "role": "system",
                "content": (
                    "Normalize a SaaS API-routing chat turn. Return only JSON with router_query, "
                    "provided_params, confirmed, and policy_text. Do not choose endpoints, invent "
                    "business policy, or override guardrails."
                ),
            },
            {"role": "user", "content": json.dumps({"query": user_query, "context": conversation_context or []}, default=str)},
        ],
    }
    request = Request(
        "https://api.openai.com/v1/responses",
        data=json.dumps(payload).encode("utf-8"),
        headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
        method="POST",
    )
    with urlopen(request, timeout=30) as response:
        raw = json.loads(response.read().decode("utf-8"))
    text = raw.get("output_text", "")
    if not text and isinstance(raw.get("output"), list):
        parts: list[str] = []
        for item in raw["output"]:
            for content in item.get("content", []) if isinstance(item, dict) else []:
                if isinstance(content, dict) and content.get("text"):
                    parts.append(str(content["text"]))
        text = "\n".join(parts)
    try:
        parsed = json.loads(text)
    except Exception:
        parsed = {}
    return _coerce_normalized(parsed, user_query, conversation_context)
