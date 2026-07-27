from __future__ import annotations

from pathlib import Path

import pytest
from pydantic import ValidationError

from corpus.runtime.config import CorpusRuntimeSettings
from corpus.runtime.model import create_ollama_chat_model


def write_runtime_env(path: Path, *, include_model: bool = True) -> None:
    values = [
        "ROUTEDECK_DATABASE_URL=sqlite+pysqlite:///./runtime.sqlite3",
        "ROUTEDECK_STATE_ENCRYPTION_KEY=explicit-test-key",
        "ROUTEDECK_INSTANCE_ID=corpus-runtime-test",
        "ROUTEDECK_REVIEW_TTL_SECONDS=300",
        "ROUTEDECK_RESUME_CAPABILITY_TTL_SECONDS=600",
        "ROUTEDECK_WORKER_COUNT=1",
        "ROUTEDECK_GUEST_COOKIE_NAME=corpus_guest",
        "ROUTEDECK_GUEST_COOKIE_SECURE=false",
        "ROUTEDECK_GUEST_COOKIE_PATH=/",
        "ROUTEDECK_BROWSER_ORIGINS=http://127.0.0.1:5199",
        "CORPUS_AUTH_DATABASE_URL=sqlite+aiosqlite:///./auth.sqlite3",
        "CORPUS_AUTH_MIGRATION_REVISION=0001_owner_auth",
        f"CORPUS_RESET_SECRET={'r' * 40}",
        f"CORPUS_VERIFICATION_SECRET={'v' * 40}",
        "CORPUS_AUTH_COOKIE_NAME=corpus_auth",
        "CORPUS_OWNER_ROUTE_COOKIE_NAME=corpus_owner_route",
        "CORPUS_AUTH_COOKIE_SECURE=false",
        "CORPUS_AUTH_COOKIE_PATH=/",
        "CORPUS_PUBLIC_FRONTEND_URL=http://127.0.0.1:5199",
        f"CORPUS_SOURCE_DATA_ROOT={(path.parent / 'sources').as_posix()}",
        "OLLAMA_BASE_URL=http://127.0.0.1:11434",
    ]
    if include_model:
        values.append("OLLAMA_MODEL=gemma4:latest")
    path.write_text("\n".join(values), encoding="utf-8")


def test_runtime_settings_combine_host_and_explicit_ollama_configuration(
    tmp_path: Path,
) -> None:
    env_file = tmp_path / ".env.local"
    write_runtime_env(env_file)

    settings = CorpusRuntimeSettings.from_env(env_file)

    assert settings.host.routedeck_instance_id == "corpus-runtime-test"
    assert str(settings.ollama_base_url).rstrip("/") == "http://127.0.0.1:11434"
    assert settings.ollama_model == "gemma4:latest"


def test_runtime_settings_fail_without_an_explicit_model(tmp_path: Path) -> None:
    env_file = tmp_path / ".env.local"
    write_runtime_env(env_file, include_model=False)

    with pytest.raises(ValidationError):
        CorpusRuntimeSettings.from_env(env_file)


def test_ollama_model_uses_the_native_provider_endpoint(
    tmp_path: Path,
) -> None:
    env_file = tmp_path / ".env.local"
    write_runtime_env(env_file)
    settings = CorpusRuntimeSettings.from_env(env_file)

    model = create_ollama_chat_model(settings)

    assert model.model == "gemma4:latest"
    assert model.base_url == "http://127.0.0.1:11434"
    assert model.disable_streaming is False
