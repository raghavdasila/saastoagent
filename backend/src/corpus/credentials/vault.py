from __future__ import annotations

import json
import uuid
from datetime import UTC, datetime
from typing import Mapping

from nacl.exceptions import CryptoError
from nacl.secret import SecretBox
from sqlalchemy import select

from corpus.persistence import CorpusDatabase

from .domain import CredentialReference, ResolvedCredential
from .models import StoredCredential


class CredentialNotFound(LookupError):
    pass


class CredentialAuthenticationError(RuntimeError):
    pass


class SecretBoxCredentialVault:
    """Owner-scoped, write-only credential storage backed by Corpus SQLAlchemy."""

    def __init__(self, database: CorpusDatabase, key: bytes) -> None:
        if len(key) != SecretBox.KEY_SIZE:
            raise ValueError("Credential vault key must be exactly 32 bytes.")
        self.database = database
        self._box = SecretBox(key)

    async def create(
        self,
        *,
        owner_id: uuid.UUID,
        label: str,
        kind: str,
        values: Mapping[str, str],
    ) -> CredentialReference:
        normalized = _validate(label=label, kind=kind, values=values)
        credential_id = uuid.uuid4()
        now = datetime.now(UTC)
        row = StoredCredential(
            id=credential_id,
            owner_id=owner_id,
            label=label.strip(),
            kind=kind.strip(),
            version=1,
            ciphertext=self._encrypt(
                owner_id=owner_id,
                credential_id=credential_id,
                version=1,
                values=normalized,
            ),
            created_at=now,
            updated_at=now,
        )
        async with self.database.session() as session:
            async with session.begin():
                session.add(row)
        return _reference(row)

    async def metadata(
        self, *, owner_id: uuid.UUID, credential_id: uuid.UUID
    ) -> CredentialReference:
        return _reference(await self._row(owner_id, credential_id))

    async def resolve(
        self, *, owner_id: uuid.UUID, credential_id: uuid.UUID
    ) -> ResolvedCredential:
        row = await self._row(owner_id, credential_id)
        try:
            plaintext = self._box.decrypt(row.ciphertext)
            envelope = json.loads(plaintext.decode("utf-8"))
            expected_binding = _binding(owner_id, credential_id, row.version)
            if envelope.get("binding") != expected_binding:
                raise ValueError("credential binding mismatch")
            values = envelope["values"]
            if not isinstance(values, dict) or not all(
                isinstance(key, str) and isinstance(value, str)
                for key, value in values.items()
            ):
                raise ValueError("credential payload is invalid")
        except (CryptoError, KeyError, TypeError, ValueError, UnicodeDecodeError) as error:
            raise CredentialAuthenticationError(
                "Credential ciphertext authentication failed."
            ) from error
        return ResolvedCredential(reference=_reference(row), values=values)

    async def replace(
        self,
        *,
        owner_id: uuid.UUID,
        credential_id: uuid.UUID,
        values: Mapping[str, str],
    ) -> CredentialReference:
        normalized = _validate(values=values)
        async with self.database.session() as session:
            async with session.begin():
                row = await session.scalar(
                    select(StoredCredential)
                    .where(
                        StoredCredential.id == credential_id,
                        StoredCredential.owner_id == owner_id,
                    )
                    .with_for_update()
                )
                if row is None:
                    raise CredentialNotFound(
                        "The requested credential does not exist."
                    )
                row.version += 1
                row.updated_at = datetime.now(UTC)
                row.ciphertext = self._encrypt(
                    owner_id=owner_id,
                    credential_id=credential_id,
                    version=row.version,
                    values=normalized,
                )
        return _reference(row)

    async def delete(
        self, *, owner_id: uuid.UUID, credential_id: uuid.UUID
    ) -> None:
        async with self.database.session() as session:
            async with session.begin():
                row = await session.scalar(
                    select(StoredCredential).where(
                        StoredCredential.id == credential_id,
                        StoredCredential.owner_id == owner_id,
                    )
                )
                if row is None:
                    raise CredentialNotFound(
                        "The requested credential does not exist."
                    )
                await session.delete(row)

    async def _row(
        self, owner_id: uuid.UUID, credential_id: uuid.UUID
    ) -> StoredCredential:
        async with self.database.session() as session:
            row = await session.scalar(
                select(StoredCredential).where(
                    StoredCredential.id == credential_id,
                    StoredCredential.owner_id == owner_id,
                )
            )
        if row is None:
            raise CredentialNotFound("The requested credential does not exist.")
        return row

    def _encrypt(
        self,
        *,
        owner_id: uuid.UUID,
        credential_id: uuid.UUID,
        version: int,
        values: Mapping[str, str],
    ) -> bytes:
        plaintext = json.dumps(
            {
                "binding": _binding(owner_id, credential_id, version),
                "values": dict(values),
            },
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")
        return bytes(self._box.encrypt(plaintext))


def _validate(
    *,
    values: Mapping[str, str],
    label: str | None = None,
    kind: str | None = None,
) -> dict[str, str]:
    if label is not None and not label.strip():
        raise ValueError("Credential label cannot be empty.")
    if kind is not None and not kind.strip():
        raise ValueError("Credential kind cannot be empty.")
    normalized = dict(values)
    if not normalized or not all(
        isinstance(key, str)
        and bool(key.strip())
        and isinstance(value, str)
        and bool(value)
        for key, value in normalized.items()
    ):
        raise ValueError("Credential values must contain non-empty strings.")
    return normalized


def _binding(owner_id: uuid.UUID, credential_id: uuid.UUID, version: int) -> str:
    return f"corpus-credential-v1:{owner_id}:{credential_id}:{version}"


def _reference(row: StoredCredential) -> CredentialReference:
    return CredentialReference(
        id=row.id,
        owner_id=row.owner_id,
        label=row.label,
        kind=row.kind,
        version=row.version,
        created_at=row.created_at,
        updated_at=row.updated_at,
    )


__all__ = [
    "CredentialAuthenticationError",
    "CredentialNotFound",
    "SecretBoxCredentialVault",
]
