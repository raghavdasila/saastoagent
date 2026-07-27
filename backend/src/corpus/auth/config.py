from __future__ import annotations

import os
from pathlib import Path

from pydantic import AnyHttpUrl, BaseModel, ConfigDict, Field, SecretStr


_DEFAULT_ENV_PATH = Path(__file__).resolve().parents[4] / ".env.local"


class AuthSettings(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    database_url: str = Field(min_length=1)
    migration_revision: str = Field(min_length=1)
    reset_secret: SecretStr = Field(min_length=32)
    verification_secret: SecretStr = Field(min_length=32)
    auth_cookie_name: str = Field(min_length=1)
    owner_route_cookie_name: str = Field(min_length=1)
    auth_cookie_secure: bool
    auth_cookie_path: str = Field(pattern=r"^/")
    idle_session_days: int = Field(default=7, gt=0)
    absolute_session_days: int = Field(default=30, gt=0)
    verification_token_hours: int = Field(default=24, gt=0)
    reset_token_hours: int = Field(default=1, gt=0)
    public_frontend_url: AnyHttpUrl
    trusted_proxies: tuple[str, ...] = ()
    smtp_host: str = "smtp.gmail.com"
    smtp_port: int = 587
    smtp_starttls: bool = True
    smtp_username: str = "no-reply@saastoagent.com"
    smtp_from_address: str = "no-reply@saastoagent.com"
    smtp_app_password: SecretStr | None = None
    smtp_timeout_seconds: float = Field(default=5.0, gt=0)

    @classmethod
    def from_env(cls, env_file: Path = _DEFAULT_ENV_PATH) -> AuthSettings:
        values = _read_auth_environment(env_file)
        payload: dict[str, object] = {
            field_name: values[environment_name]
            for environment_name, field_name in _FIELD_BY_ENV.items()
            if environment_name in values
        }
        proxies = payload.get("trusted_proxies")
        if isinstance(proxies, str):
            payload["trusted_proxies"] = tuple(
                value.strip() for value in proxies.split(",") if value.strip()
            )
        return cls.model_validate(payload)


_FIELD_BY_ENV = {
    "CORPUS_AUTH_DATABASE_URL": "database_url",
    "CORPUS_AUTH_MIGRATION_REVISION": "migration_revision",
    "CORPUS_RESET_SECRET": "reset_secret",
    "CORPUS_VERIFICATION_SECRET": "verification_secret",
    "CORPUS_AUTH_COOKIE_NAME": "auth_cookie_name",
    "CORPUS_OWNER_ROUTE_COOKIE_NAME": "owner_route_cookie_name",
    "CORPUS_AUTH_COOKIE_SECURE": "auth_cookie_secure",
    "CORPUS_AUTH_COOKIE_PATH": "auth_cookie_path",
    "CORPUS_AUTH_IDLE_SESSION_DAYS": "idle_session_days",
    "CORPUS_AUTH_ABSOLUTE_SESSION_DAYS": "absolute_session_days",
    "CORPUS_VERIFICATION_TOKEN_HOURS": "verification_token_hours",
    "CORPUS_RESET_TOKEN_HOURS": "reset_token_hours",
    "CORPUS_PUBLIC_FRONTEND_URL": "public_frontend_url",
    "CORPUS_TRUSTED_PROXIES": "trusted_proxies",
    "CORPUS_SMTP_HOST": "smtp_host",
    "CORPUS_SMTP_PORT": "smtp_port",
    "CORPUS_SMTP_STARTTLS": "smtp_starttls",
    "CORPUS_SMTP_USERNAME": "smtp_username",
    "CORPUS_SMTP_FROM_ADDRESS": "smtp_from_address",
    "CORPUS_SMTP_APP_PASSWORD": "smtp_app_password",
    "CORPUS_SMTP_TIMEOUT_SECONDS": "smtp_timeout_seconds",
}
_AUTH_ENV_FIELDS = frozenset(_FIELD_BY_ENV)


def _read_auth_environment(path: Path) -> dict[str, str]:
    values: dict[str, str] = {}
    if path.is_file():
        for raw_line in path.read_text(encoding="utf-8").splitlines():
            line = raw_line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            name, value = line.split("=", 1)
            name = name.strip()
            if name in _AUTH_ENV_FIELDS:
                values[name] = value.strip().strip('"').strip("'")
    values.update(
        {
            name: value
            for name, value in os.environ.items()
            if name in _AUTH_ENV_FIELDS
        }
    )
    return values


__all__ = ["AuthSettings"]
