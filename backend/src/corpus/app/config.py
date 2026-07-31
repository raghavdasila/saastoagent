from __future__ import annotations

import os
from pathlib import Path

from pydantic import AnyHttpUrl, BaseModel, ConfigDict, Field, SecretStr


_DEFAULT_ENV_PATH = Path(__file__).resolve().parents[4] / ".env.local"


class RouteDeckHostSettings(BaseModel):
    """Explicit infrastructure settings shared by fresh RouteDeck hosts."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    routedeck_database_url: str = Field(min_length=1)
    routedeck_state_encryption_key: SecretStr
    routedeck_instance_id: str = Field(min_length=1)
    routedeck_review_ttl_seconds: int = Field(gt=0)
    routedeck_resume_capability_ttl_seconds: int = Field(gt=0)
    routedeck_worker_count: int = Field(ge=1)
    routedeck_browser_origins: tuple[AnyHttpUrl, ...] = Field(min_length=1)

    @classmethod
    def from_env(cls, env_file: Path = _DEFAULT_ENV_PATH) -> RouteDeckHostSettings:
        values = _read_env_file(env_file)
        values.update(
            {name: value for name, value in os.environ.items() if name in _ENV_FIELDS}
        )
        payload: dict[str, object] = {
            field_name: values[environment_name]
            for environment_name, field_name in _FIELD_BY_ENV.items()
            if environment_name in values
        }
        origins = payload.get("routedeck_browser_origins")
        if isinstance(origins, str):
            payload["routedeck_browser_origins"] = tuple(
                item.strip() for item in origins.split(",") if item.strip()
            )
        return cls.model_validate(payload)


_FIELD_BY_ENV = {
    "ROUTEDECK_DATABASE_URL": "routedeck_database_url",
    "ROUTEDECK_STATE_ENCRYPTION_KEY": "routedeck_state_encryption_key",
    "ROUTEDECK_INSTANCE_ID": "routedeck_instance_id",
    "ROUTEDECK_REVIEW_TTL_SECONDS": "routedeck_review_ttl_seconds",
    "ROUTEDECK_RESUME_CAPABILITY_TTL_SECONDS": (
        "routedeck_resume_capability_ttl_seconds"
    ),
    "ROUTEDECK_WORKER_COUNT": "routedeck_worker_count",
    "ROUTEDECK_BROWSER_ORIGINS": "routedeck_browser_origins",
}
_ENV_FIELDS = frozenset(_FIELD_BY_ENV)


def _read_env_file(path: Path) -> dict[str, str]:
    if not path.is_file():
        return {}
    values: dict[str, str] = {}
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        name, value = line.split("=", 1)
        name = name.strip()
        if name in _ENV_FIELDS:
            values[name] = value.strip().strip('"').strip("'")
    return values


__all__ = ["RouteDeckHostSettings"]
