from __future__ import annotations

from pathlib import Path

from pydantic import BaseModel, ConfigDict, field_validator

from corpus.shared.environment import read_environment


class SourceSettings(BaseModel):
    """Connector-neutral persistence settings for Sources."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    data_root: Path

    @field_validator("data_root")
    @classmethod
    def resolve_data_root(cls, value: Path) -> Path:
        return value.expanduser().resolve()

    @classmethod
    def from_env(cls, env_file: Path) -> SourceSettings:
        values = read_environment(env_file, _SOURCE_ENV_FIELDS)
        return cls.model_validate(
            {
                field_name: values[environment_name]
                for environment_name, field_name in _SOURCE_ENV_FIELDS.items()
                if environment_name in values
            }
        )


_SOURCE_ENV_FIELDS = {
    "CORPUS_SOURCE_DATA_ROOT": "data_root",
}


__all__ = ["SourceSettings"]
