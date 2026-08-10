from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Index, Integer, LargeBinary, String, Uuid
from sqlalchemy.orm import Mapped, mapped_column

from corpus.persistence.models import Base


class StoredCredential(Base):
    __tablename__ = "credential_references"
    __table_args__ = (
        Index("ix_credential_references_owner_updated", "owner_id", "updated_at"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    owner_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False
    )
    label: Mapped[str] = mapped_column(String(120), nullable=False)
    kind: Mapped[str] = mapped_column(String(80), nullable=False)
    version: Mapped[int] = mapped_column(Integer, nullable=False)
    ciphertext: Mapped[bytes] = mapped_column(LargeBinary, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)


__all__ = ["StoredCredential"]
