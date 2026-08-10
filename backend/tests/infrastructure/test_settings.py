from __future__ import annotations

import base64
from pathlib import Path

import pytest

from corpus.app.infrastructure import (
    SharedInfrastructureSettings,
    create_shared_infrastructure,
)
from corpus.credentials import CredentialVaultSettings
from corpus.jobs import DurableJobSettings
from corpus.persistence import CorpusDatabase


def test_shared_infrastructure_settings_require_explicit_queue_and_key(
    tmp_path: Path,
) -> None:
    missing = tmp_path / "missing.env"
    with pytest.raises(ValueError, match="CORPUS_JOB_QUEUE_PATH"):
        DurableJobSettings.from_env(missing)
    with pytest.raises(ValueError, match="CORPUS_CREDENTIAL_VAULT_KEY"):
        CredentialVaultSettings.from_env(missing)


def test_shared_infrastructure_settings_decode_exact_32_byte_key(
    tmp_path: Path,
) -> None:
    env_file = tmp_path / ".env.local"
    encoded = base64.urlsafe_b64encode(b"k" * 32).decode("ascii")
    env_file.write_text(
        f"CORPUS_JOB_QUEUE_PATH={tmp_path / 'jobs.sqlite3'}\n"
        f"CORPUS_CREDENTIAL_VAULT_KEY={encoded}\n",
        encoding="utf-8",
    )

    settings = SharedInfrastructureSettings.from_env(env_file)

    assert settings.jobs.sqlite_path == (tmp_path / "jobs.sqlite3").resolve()
    assert settings.credentials.key_bytes() == b"k" * 32
    assert "k" * 10 not in str(settings.credentials)


@pytest.mark.parametrize(
    "value",
    ["not-base64!", base64.urlsafe_b64encode(b"short").decode("ascii")],
)
def test_credential_key_configuration_fails_closed(
    tmp_path: Path, value: str
) -> None:
    env_file = tmp_path / ".env.local"
    env_file.write_text(
        f"CORPUS_CREDENTIAL_VAULT_KEY={value}\n", encoding="utf-8"
    )
    with pytest.raises(ValueError, match="CORPUS_CREDENTIAL_VAULT_KEY"):
        CredentialVaultSettings.from_env(env_file)


@pytest.mark.asyncio
async def test_composition_registers_feature_task_on_the_owned_huey_instance(
    tmp_path: Path,
) -> None:
    database = CorpusDatabase(
        f"sqlite+aiosqlite:///{(tmp_path / 'corpus.sqlite3').as_posix()}"
    )
    await database.create_schema_for_tests()
    settings = SharedInfrastructureSettings(
        jobs=DurableJobSettings(sqlite_path=tmp_path / "jobs.sqlite3"),
        credentials=CredentialVaultSettings(
            encoded_key=base64.urlsafe_b64encode(b"k" * 32).decode("ascii")
        ),
    )

    def register(huey):
        @huey.task(retries=0)
        def execute(job_id: str) -> str:
            return job_id

        return execute

    try:
        infrastructure = create_shared_infrastructure(
            database=database,
            settings=settings,
            job_task_factory=register,
        )
        assert infrastructure.huey._registry._registry
        assert infrastructure.jobs.huey is infrastructure.huey
        assert infrastructure.credentials.database is database
    finally:
        await database.close()
