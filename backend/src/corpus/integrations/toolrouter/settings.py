from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Literal

from pydantic import SecretStr

from corpus.shared.environment import read_environment


@dataclass(frozen=True)
class ToolRouterSettings:
    embedding_model: str = "sentence-transformers/all-MiniLM-L6-v2"
    embedding_revision: str = "1110a243fdf4706b3f48f1d95db1a4f5529b4d41"
    embedding_device: str = "cpu"
    embedding_batch_size: int = 64
    embedding_local_files_only: bool = True
    model_provider: Literal["ollama", "openai"] = "ollama"
    ollama_url: str = "http://127.0.0.1:11434"
    generator_model: str = "gemma4:latest"
    reviewer_model: str = "qwen2.5-coder:7b"
    openai_api_key: SecretStr | None = None
    openai_reasoning_effort: Literal[
        "none", "low", "medium", "high", "xhigh", "max"
    ] = "low"
    evalset_timeout_seconds: float = 240.0

    @classmethod
    def from_env(cls, env_file: Path) -> ToolRouterSettings:
        values = read_environment(env_file, _TOOLROUTER_ENV_FIELDS)
        payload = {
            field_name: values[environment_name]
            for environment_name, field_name in _TOOLROUTER_ENV_FIELDS.items()
            if environment_name in values and not field_name.startswith("_")
        }
        if "embedding_batch_size" in payload:
            payload["embedding_batch_size"] = int(payload["embedding_batch_size"])
        if "embedding_local_files_only" in payload:
            payload["embedding_local_files_only"] = _parse_bool(
                str(payload["embedding_local_files_only"]),
                name="CORPUS_TOOLROUTER_EMBEDDING_LOCAL_FILES_ONLY",
            )
        if "evalset_timeout_seconds" in payload:
            payload["evalset_timeout_seconds"] = float(
                payload["evalset_timeout_seconds"]
            )
        provider = str(payload.get("model_provider") or "ollama").strip()
        if provider == "openai":
            openai_model = values.get("CORPUS_OPENAI_MODEL")
            if openai_model:
                payload.setdefault("generator_model", openai_model)
                payload.setdefault("reviewer_model", openai_model)
        return cls(**payload)

    def __post_init__(self) -> None:
        if isinstance(self.openai_api_key, str):
            object.__setattr__(self, "openai_api_key", SecretStr(self.openai_api_key))
        for field in (
            "embedding_model",
            "embedding_revision",
            "embedding_device",
            "generator_model",
            "reviewer_model",
        ):
            if not str(getattr(self, field)).strip():
                raise ValueError(f"ToolRouter setting {field} cannot be empty")
        if self.embedding_batch_size <= 0:
            raise ValueError("ToolRouter embedding_batch_size must be positive")
        if self.evalset_timeout_seconds <= 0:
            raise ValueError("ToolRouter evalset_timeout_seconds must be positive")
        if self.model_provider == "ollama" and not self.ollama_url.strip():
            raise ValueError("ToolRouter setting ollama_url cannot be empty")
        if (
            self.model_provider == "ollama"
            and self.generator_model == self.reviewer_model
        ):
            raise ValueError("Evalset generator and reviewer models must be independent")


def _parse_bool(value: str, *, name: str) -> bool:
    normalized = value.strip().casefold()
    if normalized == "true":
        return True
    if normalized == "false":
        return False
    raise ValueError(f"{name} must be true or false")


_TOOLROUTER_ENV_FIELDS = {
    "CORPUS_TOOLROUTER_EMBEDDING_MODEL": "embedding_model",
    "CORPUS_TOOLROUTER_EMBEDDING_REVISION": "embedding_revision",
    "CORPUS_TOOLROUTER_EMBEDDING_DEVICE": "embedding_device",
    "CORPUS_TOOLROUTER_EMBEDDING_BATCH_SIZE": "embedding_batch_size",
    "CORPUS_TOOLROUTER_EMBEDDING_LOCAL_FILES_ONLY": "embedding_local_files_only",
    "CORPUS_MODEL_PROVIDER": "model_provider",
    "CORPUS_TOOLROUTER_OLLAMA_URL": "ollama_url",
    "CORPUS_TOOLROUTER_GENERATOR_MODEL": "generator_model",
    "CORPUS_TOOLROUTER_REVIEWER_MODEL": "reviewer_model",
    "OPENAI_API_KEY": "openai_api_key",
    "CORPUS_OPENAI_MODEL": "_selected_openai_model",
    "CORPUS_OPENAI_REASONING_EFFORT": "openai_reasoning_effort",
    "CORPUS_TOOLROUTER_EVALSET_TIMEOUT_SECONDS": "evalset_timeout_seconds",
}


__all__ = ["ToolRouterSettings"]
