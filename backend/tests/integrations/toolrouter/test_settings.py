from __future__ import annotations

from pathlib import Path

from corpus.integrations.toolrouter import ToolRouterSettings


def test_toolrouter_settings_own_and_load_all_toolrouter_values(
    tmp_path: Path,
    monkeypatch,
) -> None:
    values = {
        "CORPUS_TOOLROUTER_EMBEDDING_MODEL": "local/embedding-model",
        "CORPUS_TOOLROUTER_EMBEDDING_REVISION": "revision-1",
        "CORPUS_TOOLROUTER_EMBEDDING_DEVICE": "cuda",
        "CORPUS_TOOLROUTER_EMBEDDING_BATCH_SIZE": "32",
        "CORPUS_TOOLROUTER_EMBEDDING_LOCAL_FILES_ONLY": "false",
        "CORPUS_TOOLROUTER_OLLAMA_URL": "http://127.0.0.1:22434",
        "CORPUS_TOOLROUTER_GENERATOR_MODEL": "generator:1",
        "CORPUS_TOOLROUTER_REVIEWER_MODEL": "reviewer:1",
        "CORPUS_TOOLROUTER_EVALSET_TIMEOUT_SECONDS": "90",
    }
    for name, value in values.items():
        monkeypatch.setenv(name, value)

    settings = ToolRouterSettings.from_env(tmp_path / "missing.env")

    assert settings.embedding_model == "local/embedding-model"
    assert settings.embedding_revision == "revision-1"
    assert settings.embedding_device == "cuda"
    assert settings.embedding_batch_size == 32
    assert settings.embedding_local_files_only is False
    assert settings.ollama_url == "http://127.0.0.1:22434"
    assert settings.generator_model == "generator:1"
    assert settings.reviewer_model == "reviewer:1"
    assert settings.evalset_timeout_seconds == 90


def test_toolrouter_settings_reuse_selected_openai_runtime_configuration(
    tmp_path: Path,
    monkeypatch,
) -> None:
    monkeypatch.setenv("CORPUS_MODEL_PROVIDER", "openai")
    monkeypatch.setenv("OPENAI_API_KEY", "deployment-key")
    monkeypatch.setenv("CORPUS_OPENAI_MODEL", "gpt-5.6-luna")
    monkeypatch.setenv("CORPUS_OPENAI_REASONING_EFFORT", "low")

    settings = ToolRouterSettings.from_env(tmp_path / "missing.env")

    assert settings.model_provider == "openai"
    assert settings.openai_api_key is not None
    assert settings.openai_api_key.get_secret_value() == "deployment-key"
    assert settings.generator_model == "gpt-5.6-luna"
    assert settings.reviewer_model == "gpt-5.6-luna"
    assert settings.openai_reasoning_effort == "low"


def test_toolrouter_adapter_requires_an_api_key_for_openai() -> None:
    import pytest

    from corpus.integrations.toolrouter import ToolRouterAdapter

    with pytest.raises(ValueError, match="OPENAI_API_KEY"):
        ToolRouterAdapter(
            ToolRouterSettings(
                model_provider="openai",
                openai_api_key=None,
                generator_model="gpt-5.6-luna",
                reviewer_model="gpt-5.6-luna",
            )
        )
