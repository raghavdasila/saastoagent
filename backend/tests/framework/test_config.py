from __future__ import annotations

from pathlib import Path

import pytest
from pydantic import ValidationError

from corpus.app.config import RouteDeckHostSettings


def test_host_settings_load_every_runtime_value_explicitly(tmp_path: Path) -> None:
    env_file = tmp_path / ".env.local"
    env_file.write_text(
        "\n".join(
            (
                "ROUTEDECK_DATABASE_URL=sqlite+pysqlite:///./runtime.sqlite3",
                "ROUTEDECK_STATE_ENCRYPTION_KEY=explicit-test-key",
                "ROUTEDECK_INSTANCE_ID=framework-contract",
                "ROUTEDECK_REVIEW_TTL_SECONDS=300",
                "ROUTEDECK_RESUME_CAPABILITY_TTL_SECONDS=600",
                "ROUTEDECK_WORKER_COUNT=1",
                "ROUTEDECK_GUEST_COOKIE_NAME=framework_guest",
                "ROUTEDECK_GUEST_COOKIE_SECURE=false",
                "ROUTEDECK_GUEST_COOKIE_PATH=/",
                "ROUTEDECK_BROWSER_ORIGINS=http://127.0.0.1:5199",
            )
        ),
        encoding="utf-8",
    )

    settings = RouteDeckHostSettings.from_env(env_file)

    assert settings.routedeck_database_url.endswith("runtime.sqlite3")
    assert settings.routedeck_instance_id == "framework-contract"
    assert settings.routedeck_worker_count == 1
    assert settings.routedeck_guest_cookie_secure is False
    assert tuple(map(str, settings.routedeck_browser_origins)) == (
        "http://127.0.0.1:5199/",
    )


def test_host_settings_fail_when_a_required_runtime_value_is_missing(
    tmp_path: Path,
) -> None:
    env_file = tmp_path / ".env.local"
    env_file.write_text(
        "ROUTEDECK_BROWSER_ORIGINS=http://127.0.0.1:5199\n",
        encoding="utf-8",
    )

    with pytest.raises(ValidationError):
        RouteDeckHostSettings.from_env(env_file)
