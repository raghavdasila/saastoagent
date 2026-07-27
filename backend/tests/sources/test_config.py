from __future__ import annotations

from pathlib import Path

import pytest
from pydantic import ValidationError

from corpus.features.sources.config import SourceSettings
from corpus.features.sources.connectors.api.config import ApiSourceSettings


def test_source_settings_own_only_explicit_source_storage(
    tmp_path: Path,
    monkeypatch,
) -> None:
    source_root = tmp_path / "owner-sources"
    monkeypatch.setenv("CORPUS_SOURCE_DATA_ROOT", str(source_root))
    monkeypatch.setenv("CORPUS_API_SOURCE_MAX_UPLOAD_BYTES", "4096")
    monkeypatch.setenv("CORPUS_TOOLROUTER_GENERATOR_MODEL", "custom-generator")

    settings = SourceSettings.from_env(tmp_path / "missing.env")

    assert settings.data_root == source_root.resolve()
    assert set(SourceSettings.model_fields) == {"data_root"}


def test_source_settings_require_an_explicit_data_root(tmp_path: Path) -> None:
    with pytest.raises(ValidationError):
        SourceSettings.from_env(tmp_path / "missing.env")


def test_api_source_settings_own_the_api_upload_limit(
    tmp_path: Path,
    monkeypatch,
) -> None:
    monkeypatch.setenv("CORPUS_API_SOURCE_MAX_UPLOAD_BYTES", "4096")

    settings = ApiSourceSettings.from_env(tmp_path / "missing.env")

    assert settings.max_upload_bytes == 4096
