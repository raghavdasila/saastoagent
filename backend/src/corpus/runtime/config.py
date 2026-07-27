from __future__ import annotations

from pathlib import Path

from pydantic import AnyHttpUrl, BaseModel, ConfigDict, Field

from corpus.app.config import RouteDeckHostSettings
from corpus.auth.config import AuthSettings
from corpus.features.sources.config import SourceSettings
from corpus.features.sources.connectors.api.config import ApiSourceSettings
from corpus.integrations.toolrouter import ToolRouterSettings
from corpus.shared.environment import read_environment


_DEFAULT_ENV_PATH = Path(__file__).resolve().parents[4] / ".env.local"


class CorpusRuntimeSettings(BaseModel):
    """Product runtime settings composed with the reusable host settings."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    host: RouteDeckHostSettings
    auth: AuthSettings
    sources: SourceSettings
    api_sources: ApiSourceSettings = Field(default_factory=ApiSourceSettings)
    toolrouter: ToolRouterSettings = Field(default_factory=ToolRouterSettings)
    ollama_base_url: AnyHttpUrl
    ollama_model: str = Field(min_length=1)

    @classmethod
    def from_env(cls, env_file: Path = _DEFAULT_ENV_PATH) -> CorpusRuntimeSettings:
        host = RouteDeckHostSettings.from_env(env_file)
        auth = AuthSettings.from_env(env_file)
        values = read_environment(env_file, _MODEL_ENV_FIELDS)
        return cls.model_validate(
            {
                "host": host,
                "auth": auth,
                "sources": SourceSettings.from_env(env_file),
                "api_sources": ApiSourceSettings.from_env(env_file),
                "toolrouter": ToolRouterSettings.from_env(env_file),
                "ollama_base_url": values.get("OLLAMA_BASE_URL"),
                "ollama_model": values.get("OLLAMA_MODEL"),
            }
        )

_MODEL_ENV_FIELDS = frozenset({"OLLAMA_BASE_URL", "OLLAMA_MODEL"})


__all__ = ["CorpusRuntimeSettings"]
