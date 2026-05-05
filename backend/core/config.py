from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    database_url: str = "postgresql+asyncpg://postgres:postgres@db:5432/saastoagent_v0_1"
    auth_secret: str = "CHANGE-ME-IN-PRODUCTION"
    auth_token_lifetime_seconds: int = 31_536_000
    cors_origins: list[str] = ["http://localhost:3005"]

    model_config = {"env_prefix": "STA_", "env_file": ".env", "extra": "ignore"}


settings = Settings()
