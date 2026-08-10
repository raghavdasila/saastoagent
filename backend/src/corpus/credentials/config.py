from __future__ import annotations

import base64
from pathlib import Path

from pydantic import BaseModel, ConfigDict, SecretStr

from corpus.shared.environment import read_environment


_DEFAULT_ENV_PATH = Path(__file__).resolve().parents[4] / ".env.local"


class CredentialVaultSettings(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    encoded_key: SecretStr

    @classmethod
    def from_env(
        cls, env_file: Path = _DEFAULT_ENV_PATH
    ) -> CredentialVaultSettings:
        values = read_environment(env_file, {"CORPUS_CREDENTIAL_VAULT_KEY"})
        encoded = values.get("CORPUS_CREDENTIAL_VAULT_KEY")
        if not encoded:
            raise ValueError("CORPUS_CREDENTIAL_VAULT_KEY is required.")
        settings = cls(encoded_key=encoded)
        settings.key_bytes()
        return settings

    def key_bytes(self) -> bytes:
        encoded = self.encoded_key.get_secret_value()
        try:
            key = base64.b64decode(encoded, altchars=b"-_", validate=True)
        except (ValueError, TypeError) as error:
            raise ValueError(
                "CORPUS_CREDENTIAL_VAULT_KEY must be URL-safe base64."
            ) from error
        if len(key) != 32:
            raise ValueError(
                "CORPUS_CREDENTIAL_VAULT_KEY must decode to exactly 32 bytes."
            )
        return key


__all__ = ["CredentialVaultSettings"]
