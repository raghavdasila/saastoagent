from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, JSON, String, UniqueConstraint, Uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship

from corpus.persistence.models import Base


class AgentDesign(Base):
    __tablename__ = "agent_designs"
    __table_args__ = (UniqueConstraint("organization_id", "agent_id", name="uq_agent_design_owner_agent"),)

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    organization_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False)
    agent_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("agents.id", ondelete="RESTRICT"), nullable=False)
    current_revision_id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), nullable=False)
    current_revision: Mapped[int] = mapped_column(Integer, nullable=False)
    accepted_revision_id: Mapped[uuid.UUID | None] = mapped_column(Uuid(as_uuid=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    revisions: Mapped[list[AgentDesignRevision]] = relationship(back_populates="design", cascade="all, delete-orphan")


class AgentDesignRevision(Base):
    __tablename__ = "agent_design_revisions"
    __table_args__ = (UniqueConstraint("design_id", "revision", name="uq_agent_design_revision"),)

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    design_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("agent_designs.id", ondelete="CASCADE"), nullable=False)
    revision: Mapped[int] = mapped_column(Integer, nullable=False)
    agent_version: Mapped[int] = mapped_column(Integer, nullable=False)
    input_fingerprint: Mapped[str] = mapped_column(String(64), nullable=False)
    content: Mapped[dict[str, object]] = mapped_column(JSON, nullable=False)
    source_inputs: Mapped[list[dict[str, object]]] = mapped_column(JSON, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    design: Mapped[AgentDesign] = relationship(back_populates="revisions")


class AgentBuildRequest(Base):
    __tablename__ = "agent_build_requests"
    __table_args__ = (UniqueConstraint("organization_id", "design_revision_id", name="uq_agent_build_request_revision"),)

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    organization_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False)
    agent_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("agents.id", ondelete="RESTRICT"), nullable=False)
    design_revision_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("agent_design_revisions.id", ondelete="RESTRICT"), nullable=False)
    status: Mapped[str] = mapped_column(String(24), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)


__all__ = ["AgentBuildRequest", "AgentDesign", "AgentDesignRevision"]
