from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, String, Uuid
from sqlalchemy.orm import Mapped, mapped_column

from corpus.persistence.models import Base


class AgentChannel(Base):
    __tablename__ = "agent_channels"

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True)
    organization_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False)
    agent_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("agents.id", ondelete="RESTRICT"), nullable=False)
    runtime_channel_id: Mapped[str | None] = mapped_column(String(64), unique=True, nullable=True)
    name: Mapped[str] = mapped_column(String(160), nullable=False)
    slug: Mapped[str] = mapped_column(String(120), unique=True, nullable=False)
    status: Mapped[str] = mapped_column(String(24), nullable=False)
    enabled: Mapped[bool] = mapped_column(Boolean, nullable=False)
    active_deployment_id: Mapped[uuid.UUID | None] = mapped_column(Uuid(as_uuid=True), nullable=True)
    failure_code: Mapped[str | None] = mapped_column(String(80), nullable=True)
    failure_message: Mapped[str | None] = mapped_column(String(500), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)


__all__ = ["AgentChannel"]
