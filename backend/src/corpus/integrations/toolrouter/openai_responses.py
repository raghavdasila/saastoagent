from __future__ import annotations

import hashlib
from importlib.metadata import PackageNotFoundError, version as package_version
from typing import Any, Mapping


class OpenAIResponsesTransport:
    """Adapt the OpenAI Responses API to ToolRouter's structured-output contract."""

    def __init__(
        self,
        *,
        api_key: str,
        timeout_seconds: float,
        reasoning_effort: str,
        client: Any | None = None,
    ) -> None:
        if not api_key.strip():
            raise ValueError("OpenAI ToolRouter transport requires an API key")
        if timeout_seconds <= 0:
            raise ValueError("OpenAI ToolRouter timeout must be positive")
        if client is None:
            from openai import OpenAI

            client = OpenAI(api_key=api_key, timeout=timeout_seconds)
        self._client = client
        self._reasoning_effort = reasoning_effort

    def __call__(self, payload: dict[str, Any]) -> dict[str, Any]:
        model = str(payload.get("model") or "").strip()
        prompt = payload.get("prompt")
        schema = payload.get("format")
        options = payload.get("options") or {}
        if not model or not isinstance(prompt, str) or not prompt:
            raise ValueError("OpenAI ToolRouter request requires model and prompt")
        if not isinstance(schema, Mapping):
            raise ValueError("OpenAI ToolRouter request requires a JSON schema")
        if not isinstance(options, Mapping):
            raise ValueError("OpenAI ToolRouter options must be an object")

        response = self._client.responses.create(
            model=model,
            input=prompt,
            reasoning={"effort": self._reasoning_effort},
            max_output_tokens=int(options.get("num_predict") or 320),
            text={
                "format": {
                    "type": "json_schema",
                    "name": "toolrouter_structured_output",
                    "schema": dict(schema),
                    "strict": True,
                }
            },
            store=False,
        )
        output_text = getattr(response, "output_text", None)
        usage = getattr(response, "usage", None)
        input_tokens = getattr(usage, "input_tokens", None)
        output_tokens = getattr(usage, "output_tokens", None)
        if not isinstance(output_text, str) or not output_text:
            raise ValueError("OpenAI ToolRouter response is missing structured output")
        if input_tokens is None or output_tokens is None:
            raise ValueError("OpenAI ToolRouter response is missing token usage")
        return {
            "response": output_text,
            "prompt_eval_count": int(input_tokens),
            "eval_count": int(output_tokens),
        }


def resolve_openai_model_digest(model: str) -> str:
    normalized = model.strip()
    if not normalized:
        raise ValueError("OpenAI model cannot be empty")
    try:
        adapter_version = package_version("openai")
    except PackageNotFoundError:
        adapter_version = "unknown"
    identity = f"openai:{normalized}:openai:{adapter_version}"
    return hashlib.sha256(identity.encode("utf-8")).hexdigest()


__all__ = ["OpenAIResponsesTransport", "resolve_openai_model_digest"]
