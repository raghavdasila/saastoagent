from __future__ import annotations

import json

from pydantic import field_validator
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    database_url: str = "postgresql+asyncpg://postgres:postgres@db:5432/saastoagent_v0_1"
    auth_secret: str = "CHANGE-ME-IN-PRODUCTION"
    auth_token_lifetime_seconds: int = 31_536_000
    encryption_key: str = ""
    cors_origins: list[str] = ["http://localhost:3005"]

    # OpenAI / agent runtime
    openai_api_key: str = ""
    default_model: str = "gpt-5-mini"
    embedding_model: str = "text-embedding-3-small"
    embedding_dimensions: int = 1536

    # Uploads (RAG attachments)
    upload_dir: str = "./uploads"

    # Chat streaming
    max_tool_iterations: int = 10
    keepalive_interval: float = 0.5
    anonymous_chat_messages_per_hour: int = 10
    anonymous_chat_rate_limit_window_seconds: int = 3600

    @field_validator("cors_origins", mode="before")
    @classmethod
    def _parse_cors(cls, v):
        if isinstance(v, str):
            try:
                return json.loads(v)
            except json.JSONDecodeError:
                return [v]
        return v

    model_config = {"env_prefix": "STA_", "env_file": ".env", "extra": "ignore"}


settings = Settings()
