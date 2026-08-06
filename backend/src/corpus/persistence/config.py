from __future__ import annotations

import os
from pathlib import Path

from pydantic import BaseModel, ConfigDict, Field


_DEFAULT_ENV_PATH = Path(__file__).resolve().parents[4] / ".env.local"


class CorpusDatabaseSettings(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    url: str = Field(min_length=1)
    migration_revision: str = Field(min_length=1)

    @classmethod
    def from_env(
        cls,
        env_file: Path = _DEFAULT_ENV_PATH,
    ) -> CorpusDatabaseSettings:
        values = _read_environment(env_file)
        return cls.model_validate(
            {
                "url": values.get("CORPUS_DATABASE_URL"),
                "migration_revision": values.get(
                    "CORPUS_MIGRATION_REVISION"
                ),
            }
        )


def _read_environment(path: Path) -> dict[str, str]:
    names = {"CORPUS_DATABASE_URL", "CORPUS_MIGRATION_REVISION"}
    values: dict[str, str] = {}
    if path.is_file():
        for raw_line in path.read_text(encoding="utf-8").splitlines():
            line = raw_line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            name, value = line.split("=", 1)
            name = name.strip()
            if name in names:
                values[name] = value.strip().strip('"').strip("'")
    values.update(
        {name: value for name, value in os.environ.items() if name in names}
    )
    return values


__all__ = ["CorpusDatabaseSettings"]
