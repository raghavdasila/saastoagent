from __future__ import annotations

from pathlib import Path

from pydantic import BaseModel, ConfigDict, Field

from corpus.shared.environment import read_environment


class ApiSourceSettings(BaseModel):
    """Runtime limits owned by the API collection connector."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    max_upload_bytes: int = Field(default=20 * 1024 * 1024, gt=0)

    @classmethod
    def from_env(cls, env_file: Path) -> ApiSourceSettings:
        values = read_environment(env_file, _API_SOURCE_ENV_FIELDS)
        return cls.model_validate(
            {
                field_name: values[environment_name]
                for environment_name, field_name in _API_SOURCE_ENV_FIELDS.items()
                if environment_name in values
            }
        )


_API_SOURCE_ENV_FIELDS = {
    "CORPUS_API_SOURCE_MAX_UPLOAD_BYTES": "max_upload_bytes",
}


__all__ = ["ApiSourceSettings"]
