from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime
from typing import Mapping


@dataclass(frozen=True)
class CredentialReference:
    id: uuid.UUID
    owner_id: uuid.UUID
    label: str
    kind: str
    version: int
    created_at: datetime
    updated_at: datetime


@dataclass(frozen=True)
class ResolvedCredential:
    reference: CredentialReference
    values: Mapping[str, str] = field(repr=False)


__all__ = ["CredentialReference", "ResolvedCredential"]
