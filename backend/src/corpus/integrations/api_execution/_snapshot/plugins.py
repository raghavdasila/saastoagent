from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any, Mapping, Protocol

from .errors import CredentialError, UnsupportedPluginError


class MediaPlugin(Protocol):
    id: str

    def encode(self, body: Any) -> tuple[bytes, str]: ...

    def decode(self, body: bytes, content_type: str) -> Any: ...


class AuthPlugin(Protocol):
    id: str

    def apply(
        self,
        headers: dict[str, str],
        query: dict[str, Any],
        cookies: dict[str, str],
        credential: Mapping[str, str] | None,
    ) -> None: ...


@dataclass(frozen=True)
class JsonMediaPlugin:
    id: str = "application/json"

    def encode(self, body: Any) -> tuple[bytes, str]:
        return (
            json.dumps(body, separators=(",", ":"), ensure_ascii=False).encode("utf-8"),
            self.id,
        )

    def decode(self, body: bytes, content_type: str) -> Any:
        if not body:
            return None
        return json.loads(body.decode("utf-8"))


@dataclass(frozen=True)
class NoAuthPlugin:
    id: str = "none"

    def apply(self, headers, query, cookies, credential) -> None:
        if credential:
            raise CredentialError(
                "unexpected_credential",
                "This connection does not accept credentials.",
            )


@dataclass(frozen=True)
class ApiKeyHeaderPlugin:
    id: str = "api_key_header"

    def apply(self, headers, query, cookies, credential) -> None:
        if credential is None:
            raise CredentialError("credential_missing", "The API credential is unavailable.")
        header_name = credential.get("header_name", "").strip()
        value = credential.get("value", "")
        if not header_name or not value:
            raise CredentialError(
                "credential_invalid",
                "The API credential configuration is invalid.",
            )
        headers[header_name] = value


class PluginRegistry:
    def __init__(
        self,
        *,
        media: tuple[MediaPlugin, ...] = (JsonMediaPlugin(),),
        auth: tuple[AuthPlugin, ...] = (NoAuthPlugin(), ApiKeyHeaderPlugin()),
    ) -> None:
        self._media = {plugin.id.lower(): plugin for plugin in media}
        self._auth = {plugin.id: plugin for plugin in auth}

    def media(self, media_type: str) -> MediaPlugin:
        normalized = media_type.split(";", 1)[0].strip().lower()
        try:
            return self._media[normalized]
        except KeyError as error:
            raise UnsupportedPluginError(
                "unsupported_media_type",
                f"No installed plugin supports media type {normalized}.",
            ) from error

    def auth(self, plugin_id: str) -> AuthPlugin:
        try:
            return self._auth[plugin_id]
        except KeyError as error:
            raise UnsupportedPluginError(
                "unsupported_auth_scheme",
                f"No installed plugin supports authentication scheme {plugin_id}.",
            ) from error

