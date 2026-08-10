from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String, Uuid
from sqlalchemy.orm import Mapped, mapped_column

from corpus.persistence.models import Base


class AgentDeployment(Base):
    __tablename__ = "agent_deployments"

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True)
    organization_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False)
    agent_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("agents.id", ondelete="RESTRICT"), nullable=False)
    channel_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("agent_channels.id", ondelete="RESTRICT"), nullable=False)
    build_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("agent_runnable_builds.id", ondelete="RESTRICT"), nullable=False)
    eligibility_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("agent_evaluation_eligibility.id", ondelete="RESTRICT"), nullable=False)
    runtime_deployment_id: Mapped[str | None] = mapped_column(String(64), unique=True, nullable=True)
    status: Mapped[str] = mapped_column(String(24), nullable=False)
    bundle_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    failure_code: Mapped[str | None] = mapped_column(String(80), nullable=True)
    failure_message: Mapped[str | None] = mapped_column(String(500), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)


__all__ = ["AgentDeployment"]
