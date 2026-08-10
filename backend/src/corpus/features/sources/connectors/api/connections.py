from __future__ import annotations

import json
import secrets
import uuid
from dataclasses import dataclass
from datetime import UTC, datetime
from enum import StrEnum
from pathlib import Path

from pydantic import BaseModel, ConfigDict, Field, HttpUrl, SecretStr, ValidationError, model_validator

from corpus.credentials import CredentialVaultPort

from ...repository import LocalSourceRepository, SourceNotReady


class ApiAuthenticationMethod(StrEnum):
    NONE = "none"
    API_KEY = "api_key"
    BEARER = "bearer"


class ApiConnectionPrivateForm(BaseModel):
    model_config = ConfigDict(extra="forbid")

    source_id: str = Field(min_length=16, max_length=16)
    profile_name: str = Field(min_length=1, max_length=80)
    environment: str = Field(min_length=1, max_length=80)
    base_url: HttpUrl
    authentication_method: ApiAuthenticationMethod
    credential_name: str | None = Field(default=None, max_length=128)
    credential_value: SecretStr | None = None

    @model_validator(mode="after")
    def validate_authentication_fields(self) -> ApiConnectionPrivateForm:
        if self.base_url.username or self.base_url.password:
            raise ValueError("The API base URL cannot contain credentials.")
        if self.base_url.query or self.base_url.fragment:
            raise ValueError("The API base URL cannot contain a query or fragment.")
        value = (
            self.credential_value.get_secret_value()
            if self.credential_value is not None
            else ""
        )
        if self.authentication_method is ApiAuthenticationMethod.NONE:
            if self.credential_name or value:
                raise ValueError("No credential is accepted for unauthenticated APIs.")
        elif self.authentication_method is ApiAuthenticationMethod.API_KEY:
            if not self.credential_name or not self.credential_name.strip() or not value:
                raise ValueError("API-key authentication requires a header name and value.")
        elif not value:
            raise ValueError("Bearer authentication requires a token.")
        return self


class ApiConnectionProfile(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    id: str = Field(min_length=16, max_length=16)
    source_id: str = Field(min_length=16, max_length=16)
    revision_id: str = Field(min_length=16, max_length=16)
    profile_name: str
    environment: str
    base_url: str
    authentication_method: ApiAuthenticationMethod
    credential_name: str | None = None
    credential_reference_id: uuid.UUID | None = None
    credential_version: int | None = Field(default=None, ge=1)
    created_at: datetime
    updated_at: datetime


class ApiConnectionCollection(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    profiles: tuple[ApiConnectionProfile, ...] = ()


class ApiConnectionError(RuntimeError):
    pass


class ApiConnectionConflict(ApiConnectionError):
    pass


@dataclass(frozen=True)
class ApiConnectionProfileRepository:
    sources: LocalSourceRepository

    def list(self, *, owner_key: str, source_id: str) -> tuple[ApiConnectionProfile, ...]:
        source = self.sources.get(owner_key=owner_key, source_id=source_id)
        return self.list_exact(
            owner_key=owner_key,
            source_id=source_id,
            revision_id=source.revision.revision_id,
        )

    def list_exact(
        self, *, owner_key: str, source_id: str, revision_id: str
    ) -> tuple[ApiConnectionProfile, ...]:
        with self.sources.locked_revision(
            owner_key=owner_key,
            source_id=source_id,
            revision_id=revision_id,
        ) as (source, revision_dir):
            if source.connector_key != "api":
                raise SourceNotReady("The selected source is not an API source.")
            collection = self._read_path(revision_dir / "connections.json")
            return tuple(
                sorted(
                    collection.profiles,
                    key=lambda item: (item.profile_name.casefold(), item.id),
                )
            )

    def get_exact(
        self,
        *,
        owner_key: str,
        source_id: str,
        revision_id: str,
        profile_id: str,
    ) -> ApiConnectionProfile:
        matches = tuple(
            item
            for item in self.list_exact(
                owner_key=owner_key,
                source_id=source_id,
                revision_id=revision_id,
            )
            if item.id == profile_id
        )
        if len(matches) != 1:
            raise ApiConnectionError("The selected API connection profile is unavailable.")
        return matches[0]

    def get_exact_locked(
        self,
        *,
        source_id: str,
        revision_id: str,
        profile_id: str,
        revision_dir: Path,
    ) -> ApiConnectionProfile:
        """Read an exact profile while the caller holds the Source revision lock."""

        collection = self._read_path(revision_dir / "connections.json")
        matches = tuple(
            item
            for item in collection.profiles
            if item.id == profile_id
            and item.source_id == source_id
            and item.revision_id == revision_id
        )
        if len(matches) != 1:
            raise ApiConnectionError("The selected API connection profile is unavailable.")
        return matches[0]

    def create(
        self,
        *,
        owner_key: str,
        source_id: str,
        profile_name: str,
        environment: str,
        base_url: str,
        authentication_method: ApiAuthenticationMethod,
        credential_name: str | None,
        credential_reference_id: uuid.UUID | None,
        credential_version: int | None,
    ) -> ApiConnectionProfile:
        with self.sources.locked_revision(
            owner_key=owner_key, source_id=source_id
        ) as (source, revision_dir):
            if source.connector_key != "api":
                raise SourceNotReady("The selected source is not an API source.")
            path = revision_dir / "connections.json"
            collection = self._read_path(path)
            normalized_name = profile_name.strip()
            if any(
                profile.profile_name.casefold() == normalized_name.casefold()
                for profile in collection.profiles
            ):
                raise ApiConnectionConflict("A connection profile with this name already exists.")
            now = datetime.now(UTC)
            profile = ApiConnectionProfile(
                id=secrets.token_urlsafe(12),
                source_id=source.source_id,
                revision_id=source.revision.revision_id,
                profile_name=normalized_name,
                environment=environment.strip(),
                base_url=base_url,
                authentication_method=authentication_method,
                credential_name=credential_name.strip() if credential_name else None,
                credential_reference_id=credential_reference_id,
                credential_version=credential_version,
                created_at=now,
                updated_at=now,
            )
            self._write_path(
                path,
                ApiConnectionCollection(profiles=(*collection.profiles, profile)),
            )
            return profile

    def _path(self, *, owner_key: str, source_id: str) -> Path:
        return self.sources.revision_dir(owner_key=owner_key, source_id=source_id) / "connections.json"

    def _read(self, *, owner_key: str, source_id: str) -> ApiConnectionCollection:
        return self._read_path(self._path(owner_key=owner_key, source_id=source_id))

    def _read_path(self, path: Path) -> ApiConnectionCollection:
        if not path.is_file():
            return ApiConnectionCollection()
        try:
            return ApiConnectionCollection.model_validate_json(path.read_text(encoding="utf-8"))
        except (OSError, ValidationError) as error:
            raise ApiConnectionError("The API connection profiles are unavailable.") from error

    def _write(
        self,
        *,
        owner_key: str,
        source_id: str,
        collection: ApiConnectionCollection,
    ) -> None:
        self._write_path(
            self._path(owner_key=owner_key, source_id=source_id), collection
        )

    def _write_path(self, path: Path, collection: ApiConnectionCollection) -> None:
        temporary = path.with_suffix(path.suffix + ".tmp")
        try:
            temporary.write_text(collection.model_dump_json(indent=2), encoding="utf-8")
            temporary.replace(path)
        except OSError as error:
            raise ApiConnectionError("The API connection profile could not be persisted.") from error


@dataclass(frozen=True)
class ApiConnectionService:
    profiles: ApiConnectionProfileRepository
    credentials: CredentialVaultPort

    async def save(
        self,
        *,
        owner_id: uuid.UUID,
        value: ApiConnectionPrivateForm,
    ) -> ApiConnectionProfile:
        owner_key = str(owner_id)
        self.profiles.list(owner_key=owner_key, source_id=value.source_id)
        credential_id: uuid.UUID | None = None
        credential_version: int | None = None
        credential_name = value.credential_name.strip() if value.credential_name else None
        if value.authentication_method is not ApiAuthenticationMethod.NONE:
            secret = value.credential_value
            assert secret is not None
            credential = await self.credentials.create(
                owner_id=owner_id,
                label=f"API connection {value.profile_name.strip()}",
                kind=f"api_connection_{value.authentication_method.value}",
                values=(
                    {
                        "header_name": credential_name or "",
                        "value": secret.get_secret_value(),
                    }
                    if value.authentication_method is ApiAuthenticationMethod.API_KEY
                    else {"token": secret.get_secret_value()}
                ),
            )
            credential_id = credential.id
            credential_version = credential.version
        try:
            return self.profiles.create(
                owner_key=owner_key,
                source_id=value.source_id,
                profile_name=value.profile_name,
                environment=value.environment,
                base_url=str(value.base_url).rstrip("/"),
                authentication_method=value.authentication_method,
                credential_name=credential_name,
                credential_reference_id=credential_id,
                credential_version=credential_version,
            )
        except Exception:
            if credential_id is not None:
                try:
                    await self.credentials.delete(
                        owner_id=owner_id,
                        credential_id=credential_id,
                    )
                except Exception as cleanup_error:
                    raise ApiConnectionError(
                        "The connection was not saved and credential cleanup failed."
                    ) from cleanup_error
            raise


__all__ = [
    "ApiAuthenticationMethod",
    "ApiConnectionConflict",
    "ApiConnectionError",
    "ApiConnectionPrivateForm",
    "ApiConnectionProfile",
    "ApiConnectionProfileRepository",
    "ApiConnectionService",
]
