from __future__ import annotations

import uuid
from typing import Mapping, Protocol

from .domain import CredentialReference, ResolvedCredential


class CredentialVaultPort(Protocol):
    async def create(
        self,
        *,
        owner_id: uuid.UUID,
        label: str,
        kind: str,
        values: Mapping[str, str],
    ) -> CredentialReference: ...

    async def metadata(
        self, *, owner_id: uuid.UUID, credential_id: uuid.UUID
    ) -> CredentialReference: ...

    async def resolve(
        self, *, owner_id: uuid.UUID, credential_id: uuid.UUID
    ) -> ResolvedCredential: ...

    async def replace(
        self,
        *,
        owner_id: uuid.UUID,
        credential_id: uuid.UUID,
        values: Mapping[str, str],
    ) -> CredentialReference: ...

    async def delete(
        self, *, owner_id: uuid.UUID, credential_id: uuid.UUID
    ) -> None: ...


__all__ = ["CredentialVaultPort"]
