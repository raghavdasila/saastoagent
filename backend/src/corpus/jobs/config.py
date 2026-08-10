from __future__ import annotations

from pathlib import Path

from pydantic import BaseModel, ConfigDict

from corpus.shared.environment import read_environment


_DEFAULT_ENV_PATH = Path(__file__).resolve().parents[4] / ".env.local"


class DurableJobSettings(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    sqlite_path: Path

    @classmethod
    def from_env(cls, env_file: Path = _DEFAULT_ENV_PATH) -> DurableJobSettings:
        values = read_environment(env_file, {"CORPUS_JOB_QUEUE_PATH"})
        raw = values.get("CORPUS_JOB_QUEUE_PATH")
        if not raw:
            raise ValueError("CORPUS_JOB_QUEUE_PATH is required.")
        return cls(sqlite_path=Path(raw).expanduser().resolve())


__all__ = ["DurableJobSettings"]
