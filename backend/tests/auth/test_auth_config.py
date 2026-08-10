from __future__ import annotations

from pathlib import Path

from corpus.auth.config import AuthSettings
from corpus.persistence import CorpusDatabaseSettings


def test_auth_settings_load_explicit_bearer_lifetimes(tmp_path: Path) -> None:
    env = tmp_path / ".env.local"
    env.write_text(
        "\n".join(
            (
                "CORPUS_DATABASE_URL=sqlite+aiosqlite:///./corpus.sqlite3",
                "CORPUS_MIGRATION_REVISION=0006_restrict_agent_attachment_delete",
                "CORPUS_RESET_SECRET=r" * 1 + "r" * 39,
                "CORPUS_VERIFICATION_SECRET=v" * 1 + "v" * 39,
                "CORPUS_AUTH_ACCESS_TOKEN_MINUTES=15",
                "CORPUS_PUBLIC_FRONTEND_URL=http://127.0.0.1:5199",
                "CORPUS_TRUSTED_PROXIES=127.0.0.1,10.0.0.1",
            )
        ),
        encoding="utf-8",
    )

    settings = AuthSettings.from_env(env)
    database = CorpusDatabaseSettings.from_env(env)

    assert database.url.endswith("corpus.sqlite3")
    assert database.migration_revision == "0006_restrict_agent_attachment_delete"
    assert settings.access_token_minutes == 15
    assert settings.idle_session_days == 7
    assert settings.absolute_session_days == 30
    assert settings.trusted_proxies == ("127.0.0.1", "10.0.0.1")
    assert settings.smtp_app_password is None
    assert settings.smtp_username == "no-reply@saastoagent.com"
    assert settings.smtp_from_address == "no-reply@saastoagent.com"
