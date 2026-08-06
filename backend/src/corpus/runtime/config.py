from __future__ import annotations

from pathlib import Path
from typing import Literal

from pydantic import AnyHttpUrl, BaseModel, ConfigDict, Field, SecretStr, model_validator

from corpus.app.config import RouteDeckHostSettings
from corpus.auth.config import AuthSettings
from corpus.features.sources.config import SourceSettings
from corpus.features.sources.connectors.api.config import ApiSourceSettings
from corpus.integrations.toolrouter import ToolRouterSettings
from corpus.persistence.config import CorpusDatabaseSettings
from corpus.shared.environment import read_environment


_DEFAULT_ENV_PATH = Path(__file__).resolve().parents[4] / ".env.local"


class CorpusRuntimeSettings(BaseModel):
    """Product runtime settings composed with the reusable host settings."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    host: RouteDeckHostSettings
    database: CorpusDatabaseSettings
    auth: AuthSettings
    sources: SourceSettings
    api_sources: ApiSourceSettings = Field(default_factory=ApiSourceSettings)
    toolrouter: ToolRouterSettings = Field(default_factory=ToolRouterSettings)
    model_provider: Literal["ollama", "openai"] = "ollama"
    ollama_base_url: AnyHttpUrl | None = None
    ollama_model: str | None = Field(default=None, min_length=1)
    openai_api_key: SecretStr | None = None
    openai_model: str | None = Field(default=None, min_length=1)
    openai_reasoning_effort: Literal[
        "none", "low", "medium", "high", "xhigh", "max"
    ] = "low"

    @model_validator(mode="after")
    def validate_selected_model_provider(self) -> CorpusRuntimeSettings:
        if self.model_provider == "ollama":
            if self.ollama_base_url is None or self.ollama_model is None:
                raise ValueError(
                    "OLLAMA_BASE_URL and OLLAMA_MODEL are required when "
                    "CORPUS_MODEL_PROVIDER=ollama"
                )
        elif self.openai_api_key is None or self.openai_model is None:
            raise ValueError(
                "OPENAI_API_KEY and CORPUS_OPENAI_MODEL are required when "
                "CORPUS_MODEL_PROVIDER=openai"
            )
        return self

    @property
    def selected_model_name(self) -> str:
        model = self.ollama_model if self.model_provider == "ollama" else self.openai_model
        assert model is not None
        return model

    @classmethod
    def from_env(cls, env_file: Path = _DEFAULT_ENV_PATH) -> CorpusRuntimeSettings:
        host = RouteDeckHostSettings.from_env(env_file)
        database = CorpusDatabaseSettings.from_env(env_file)
        auth = AuthSettings.from_env(env_file)
        values = read_environment(env_file, _MODEL_ENV_FIELDS)
        return cls.model_validate(
            {
                "host": host,
                "database": database,
                "auth": auth,
                "sources": SourceSettings.from_env(env_file),
                "api_sources": ApiSourceSettings.from_env(env_file),
                "toolrouter": ToolRouterSettings.from_env(env_file),
                "model_provider": values.get("CORPUS_MODEL_PROVIDER", "ollama"),
                "ollama_base_url": values.get("OLLAMA_BASE_URL"),
                "ollama_model": values.get("OLLAMA_MODEL"),
                "openai_api_key": values.get("OPENAI_API_KEY"),
                "openai_model": values.get("CORPUS_OPENAI_MODEL"),
                "openai_reasoning_effort": values.get(
                    "CORPUS_OPENAI_REASONING_EFFORT", "low"
                ),
            }
        )

_MODEL_ENV_FIELDS = frozenset(
    {
        "CORPUS_MODEL_PROVIDER",
        "OLLAMA_BASE_URL",
        "OLLAMA_MODEL",
        "OPENAI_API_KEY",
        "CORPUS_OPENAI_MODEL",
        "CORPUS_OPENAI_REASONING_EFFORT",
    }
)


__all__ = ["CorpusRuntimeSettings"]
