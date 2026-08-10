from __future__ import annotations

import uuid
from datetime import UTC, datetime
from pathlib import Path

import pytest
from sqlalchemy import select

from corpus.auth.models import Organization
from corpus.credentials import (
    CredentialAuthenticationError,
    CredentialNotFound,
    SecretBoxCredentialVault,
)
from corpus.credentials.models import StoredCredential
from corpus.persistence import CorpusDatabase


async def _database(tmp_path: Path) -> tuple[CorpusDatabase, uuid.UUID, uuid.UUID]:
    database = CorpusDatabase(
        f"sqlite+aiosqlite:///{(tmp_path / 'corpus.sqlite3').as_posix()}"
    )
    await database.create_schema_for_tests()
    first = uuid.uuid4()
    second = uuid.uuid4()
    async with database.session() as session:
        async with session.begin():
            session.add_all(
                (
                    Organization(
                        id=first,
                        name="First",
                        slug=f"first-{first}",
                        created_at=datetime.now(UTC),
                    ),
                    Organization(
                        id=second,
                        name="Second",
                        slug=f"second-{second}",
                        created_at=datetime.now(UTC),
                    ),
                )
            )
    return database, first, second


@pytest.mark.asyncio
async def test_secretbox_vault_is_write_only_encrypted_and_owner_scoped(
    tmp_path: Path,
) -> None:
    database, owner_id, other_owner = await _database(tmp_path)
    vault = SecretBoxCredentialVault(database, b"k" * 32)
    try:
        reference = await vault.create(
            owner_id=owner_id,
            label="Medusa",
            kind="api_headers",
            values={"x-publishable-api-key": "super-secret-value"},
        )

        assert not hasattr(reference, "values")
        assert reference.owner_id == owner_id
        resolved = await vault.resolve(
            owner_id=owner_id, credential_id=reference.id
        )
        assert resolved.values == {
            "x-publishable-api-key": "super-secret-value"
        }
        assert "super-secret-value" not in repr(resolved)
        with pytest.raises(CredentialNotFound):
            await vault.resolve(
                owner_id=other_owner, credential_id=reference.id
            )

        async with database.session() as session:
            ciphertext = await session.scalar(
                select(StoredCredential.ciphertext).where(
                    StoredCredential.id == reference.id
                )
            )
        assert ciphertext is not None
        assert b"super-secret-value" not in ciphertext
        assert b"x-publishable-api-key" not in ciphertext
    finally:
        await database.close()


@pytest.mark.asyncio
async def test_replace_rotates_version_and_wrong_key_or_tamper_fails_closed(
    tmp_path: Path,
) -> None:
    database, owner_id, _ = await _database(tmp_path)
    vault = SecretBoxCredentialVault(database, b"1" * 32)
    try:
        reference = await vault.create(
            owner_id=owner_id,
            label="Medusa",
            kind="api_headers",
            values={"authorization": "first-secret"},
        )
        replaced = await vault.replace(
            owner_id=owner_id,
            credential_id=reference.id,
            values={"authorization": "second-secret"},
        )
        assert replaced.version == 2
        assert (
            await vault.resolve(owner_id=owner_id, credential_id=reference.id)
        ).values["authorization"] == "second-secret"

        wrong_key = SecretBoxCredentialVault(database, b"2" * 32)
        with pytest.raises(CredentialAuthenticationError):
            await wrong_key.resolve(owner_id=owner_id, credential_id=reference.id)

        async with database.session() as session:
            async with session.begin():
                row = await session.get(StoredCredential, reference.id)
                assert row is not None
                row.ciphertext = bytes([row.ciphertext[0] ^ 1]) + row.ciphertext[1:]
        with pytest.raises(CredentialAuthenticationError):
            await vault.resolve(owner_id=owner_id, credential_id=reference.id)
    finally:
        await database.close()
