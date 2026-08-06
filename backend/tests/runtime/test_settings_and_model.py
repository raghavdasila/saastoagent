from __future__ import annotations

from pathlib import Path

import pytest
from langchain_openai import ChatOpenAI
from pydantic import ValidationError

from corpus.runtime.config import CorpusRuntimeSettings
from corpus.runtime.model import create_chat_model


def write_runtime_env(path: Path, *, include_model: bool = True) -> None:
    values = [
        "ROUTEDECK_DATABASE_URL=sqlite+pysqlite:///./runtime.sqlite3",
        "ROUTEDECK_STATE_ENCRYPTION_KEY=explicit-test-key",
        "ROUTEDECK_INSTANCE_ID=corpus-runtime-test",
        "ROUTEDECK_REVIEW_TTL_SECONDS=300",
        "ROUTEDECK_RESUME_CAPABILITY_TTL_SECONDS=600",
        "ROUTEDECK_WORKER_COUNT=1",
        "ROUTEDECK_BROWSER_ORIGINS=http://127.0.0.1:5199",
        "CORPUS_DATABASE_URL=sqlite+aiosqlite:///./corpus.sqlite3",
        "CORPUS_MIGRATION_REVISION=0002_agents",
        f"CORPUS_RESET_SECRET={'r' * 40}",
        f"CORPUS_VERIFICATION_SECRET={'v' * 40}",
        "CORPUS_AUTH_ACCESS_TOKEN_MINUTES=15",
        "CORPUS_AUTH_REFRESH_IDLE_DAYS=7",
        "CORPUS_AUTH_REFRESH_ABSOLUTE_DAYS=30",
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
    assert settings.database.url.endswith("corpus.sqlite3")
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

    model = create_chat_model(settings)

    assert model.model == "gemma4:latest"
    assert model.base_url == "http://127.0.0.1:11434"
    assert model.disable_streaming is False


def test_openai_provider_requires_its_own_explicit_configuration(
    tmp_path: Path,
) -> None:
    env_file = tmp_path / ".env.local"
    write_runtime_env(env_file)
    env_file.write_text(
        env_file.read_text(encoding="utf-8")
        + "\nCORPUS_MODEL_PROVIDER=openai\nCORPUS_OPENAI_MODEL=gpt-5.6-luna",
        encoding="utf-8",
    )

    with pytest.raises(ValidationError, match="OPENAI_API_KEY"):
        CorpusRuntimeSettings.from_env(env_file)


def test_openai_model_uses_responses_api_and_selected_reasoning_effort(
    tmp_path: Path,
) -> None:
    env_file = tmp_path / ".env.local"
    write_runtime_env(env_file)
    env_file.write_text(
        env_file.read_text(encoding="utf-8")
        + "\nCORPUS_MODEL_PROVIDER=openai"
        + "\nOPENAI_API_KEY=test-key"
        + "\nCORPUS_OPENAI_MODEL=gpt-5.6-luna"
        + "\nCORPUS_OPENAI_REASONING_EFFORT=medium",
        encoding="utf-8",
    )

    settings = CorpusRuntimeSettings.from_env(env_file)
    model = create_chat_model(settings)

    assert isinstance(model, ChatOpenAI)
    assert model.model_name == "gpt-5.6-luna"
    assert model.use_responses_api is True
    assert model.reasoning_effort == "medium"
