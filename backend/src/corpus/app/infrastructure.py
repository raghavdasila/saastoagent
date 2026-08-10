from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable

from huey import SqliteHuey

from corpus.credentials import CredentialVaultSettings, SecretBoxCredentialVault
from corpus.jobs import (
    DurableJobSettings,
    HueyDurableJobPort,
    SqlAlchemyDurableJobRepository,
)
from corpus.persistence import CorpusDatabase


@dataclass(frozen=True)
class SharedInfrastructureSettings:
    jobs: DurableJobSettings
    credentials: CredentialVaultSettings

    @classmethod
    def from_env(cls, env_file: Path) -> SharedInfrastructureSettings:
        return cls(
            jobs=DurableJobSettings.from_env(env_file),
            credentials=CredentialVaultSettings.from_env(env_file),
        )


@dataclass(frozen=True)
class SharedInfrastructure:
    huey: SqliteHuey
    jobs: HueyDurableJobPort
    job_repository: SqlAlchemyDurableJobRepository
    credentials: SecretBoxCredentialVault


def create_shared_infrastructure(
    *,
    database: CorpusDatabase,
    settings: SharedInfrastructureSettings,
    job_task_factory: Callable[[SqliteHuey], Any],
) -> SharedInfrastructure:
    settings.jobs.sqlite_path.parent.mkdir(parents=True, exist_ok=True)
    huey = SqliteHuey(
        "corpus",
        filename=str(settings.jobs.sqlite_path),
        fsync=True,
        results=True,
        store_none=True,
    )
    job_repository = SqlAlchemyDurableJobRepository(database)
    job_task = job_task_factory(huey)
    return SharedInfrastructure(
        huey=huey,
        jobs=HueyDurableJobPort(job_repository, huey, job_task),
        job_repository=job_repository,
        credentials=SecretBoxCredentialVault(
            database, settings.credentials.key_bytes()
        ),
    )


__all__ = [
    "SharedInfrastructure",
    "SharedInfrastructureSettings",
    "create_shared_infrastructure",
]
