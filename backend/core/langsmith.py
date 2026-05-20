from __future__ import annotations

import os
from typing import TypeVar


T = TypeVar("T")


def configure_langsmith_environment(
    *,
    tracing: bool,
    api_key: str,
    project: str,
    endpoint: str,
) -> None:
    if tracing:
        os.environ["LANGSMITH_TRACING"] = "true"
        os.environ["LANGCHAIN_TRACING_V2"] = "true"
    if api_key:
        os.environ.setdefault("LANGSMITH_API_KEY", api_key)
    if project:
        os.environ.setdefault("LANGSMITH_PROJECT", project)
    if endpoint:
        os.environ.setdefault("LANGSMITH_ENDPOINT", endpoint)


def langsmith_tracing_enabled() -> bool:
    value = os.environ.get("LANGSMITH_TRACING") or os.environ.get("LANGCHAIN_TRACING_V2") or ""
    return value.strip().lower() in {"1", "true", "yes", "on"}


def wrap_openai_client(client: T) -> T:
    if not langsmith_tracing_enabled():
        return client
    try:
        from langsmith.wrappers import wrap_openai
    except ImportError:
        return client
    return wrap_openai(client)
