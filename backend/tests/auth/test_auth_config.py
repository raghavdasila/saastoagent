from __future__ import annotations

from pathlib import Path

from corpus.auth.config import AuthSettings


def test_auth_settings_load_explicit_security_and_cookie_boundaries(tmp_path: Path) -> None:
    env = tmp_path / ".env.local"
    env.write_text(
        "\n".join(
            (
                "CORPUS_AUTH_DATABASE_URL=sqlite+aiosqlite:///./auth.sqlite3",
                "CORPUS_AUTH_MIGRATION_REVISION=0001_owner_auth",
                "CORPUS_RESET_SECRET=r" * 1 + "r" * 39,
                "CORPUS_VERIFICATION_SECRET=v" * 1 + "v" * 39,
                "CORPUS_AUTH_COOKIE_NAME=corpus_auth",
                "CORPUS_OWNER_ROUTE_COOKIE_NAME=corpus_owner_route",
                "CORPUS_AUTH_COOKIE_SECURE=false",
                "CORPUS_AUTH_COOKIE_PATH=/",
                "CORPUS_PUBLIC_FRONTEND_URL=http://127.0.0.1:5199",
                "CORPUS_TRUSTED_PROXIES=127.0.0.1,10.0.0.1",
            )
        ),
        encoding="utf-8",
    )

    settings = AuthSettings.from_env(env)

    assert settings.database_url.endswith("auth.sqlite3")
    assert settings.auth_cookie_name == "corpus_auth"
    assert settings.auth_cookie_secure is False
    assert settings.idle_session_days == 7
    assert settings.absolute_session_days == 30
    assert settings.trusted_proxies == ("127.0.0.1", "10.0.0.1")
    assert settings.smtp_app_password is None
    assert settings.smtp_username == "no-reply@saastoagent.com"
    assert settings.smtp_from_address == "no-reply@saastoagent.com"
