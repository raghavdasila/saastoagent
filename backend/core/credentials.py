"""Credential encryption and REST auth injection helpers."""

from __future__ import annotations

import base64
import json

import httpx
from cryptography.fernet import Fernet

from backend.core.config import settings

_fernet: Fernet | None = None


def _get_fernet() -> Fernet:
    global _fernet
    if _fernet is None:
        key = settings.encryption_key or Fernet.generate_key().decode()
        _fernet = Fernet(key.encode() if isinstance(key, str) else key)
    return _fernet


def encrypt_value(plaintext: str) -> bytes:
    return _get_fernet().encrypt(plaintext.encode())


def decrypt_value(ciphertext: bytes) -> str:
    return _get_fernet().decrypt(ciphertext).decode()


async def inject_credentials(
    *,
    auth_type: str | None,
    decrypted_value: str,
    metadata: dict | None = None,
) -> dict[str, dict[str, str]]:
    headers: dict[str, str] = {}
    params: dict[str, str] = {}
    meta = metadata or {}
    auth = auth_type or "none"

    if auth == "bearer":
        headers["Authorization"] = f"Bearer {decrypted_value}"
    elif auth == "api_key_header":
        headers[meta.get("header_name") or "X-API-Key"] = decrypted_value
    elif auth == "api_key_query":
        params[meta.get("query_param_name") or "api_key"] = decrypted_value
    elif auth == "basic":
        token = base64.b64encode(decrypted_value.encode()).decode()
        headers["Authorization"] = f"Basic {token}"
    elif auth == "oauth_client_credentials":
        token_url = meta.get("token_url")
        if not token_url:
            raise ValueError("token_url required for OAuth client credentials")
        creds = json.loads(decrypted_value)
        async with httpx.AsyncClient(timeout=10) as client:
            resp = await client.post(
                token_url,
                data={
                    "grant_type": "client_credentials",
                    "client_id": creds["client_id"],
                    "client_secret": creds["client_secret"],
                },
            )
            resp.raise_for_status()
            headers["Authorization"] = f"Bearer {resp.json()['access_token']}"
    elif auth == "custom_header":
        headers[meta.get("header_name") or "X-Custom-Auth"] = decrypted_value

    return {"headers": headers, "params": params}
