from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import DateTime, Enum, ForeignKey, Integer, String, Text, UniqueConstraint, Uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship

from corpus.persistence.models import Base

from .domain import AgentLifecycle


class Agent(Base):
    __tablename__ = "agents"
    __table_args__ = (
        UniqueConstraint(
            "organization_id",
            "name_key",
            name="uq_agents_organization_name",
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    organization_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False
    )
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    name_key: Mapped[str] = mapped_column(String(120), nullable=False)
    lifecycle: Mapped[AgentLifecycle] = mapped_column(
        Enum(AgentLifecycle, native_enum=False, length=16), nullable=False
    )
    current_version: Mapped[int] = mapped_column(Integer, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    versions: Mapped[list[AgentVersion]] = relationship(
        back_populates="agent",
        cascade="all, delete-orphan",
    )
    source_attachments: Mapped[list[AgentSourceAttachment]] = relationship(
        back_populates="agent",
        passive_deletes=True,
    )
    build_lineages: Mapped[list[AgentBuildLineage]] = relationship(
        back_populates="agent",
        passive_deletes=True,
    )


class AgentVersion(Base):
    __tablename__ = "agent_versions"
    __table_args__ = (
        UniqueConstraint("agent_id", "version", name="uq_agent_version"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    agent_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("agents.id", ondelete="CASCADE"), nullable=False
    )
    version: Mapped[int] = mapped_column(Integer, nullable=False)
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    description: Mapped[str] = mapped_column(String(500), nullable=False)
    instructions: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    agent: Mapped[Agent] = relationship(back_populates="versions")


class AgentSourceAttachment(Base):
    __tablename__ = "agent_source_attachments"
    __table_args__ = (
        UniqueConstraint("agent_id", "source_id", name="uq_agent_source_attachment"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    organization_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False
    )
    agent_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("agents.id", ondelete="RESTRICT"), nullable=False
    )
    source_id: Mapped[str] = mapped_column(String(16), nullable=False)
    source_revision_id: Mapped[str] = mapped_column(String(16), nullable=False)
    attached_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    agent: Mapped[Agent] = relationship(back_populates="source_attachments")


class AgentBuildLineage(Base):
    __tablename__ = "agent_build_lineages"
    __table_args__ = (
        UniqueConstraint("organization_id", "build_id", name="uq_agent_build_lineage_build"),
    )

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    organization_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False
    )
    agent_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("agents.id", ondelete="RESTRICT"), nullable=False
    )
    build_id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), nullable=False)
    agent_version: Mapped[int] = mapped_column(Integer, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    agent: Mapped[Agent] = relationship(back_populates="build_lineages")
    source_references: Mapped[list[AgentBuildSourceReference]] = relationship(
        back_populates="lineage",
        cascade="all, delete-orphan",
    )


class AgentBuildSourceReference(Base):
    __tablename__ = "agent_build_source_references"
    __table_args__ = (
        UniqueConstraint("build_lineage_id", "source_id", name="uq_agent_build_source_reference"),
    )

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    build_lineage_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("agent_build_lineages.id", ondelete="CASCADE"), nullable=False
    )
    source_id: Mapped[str] = mapped_column(String(16), nullable=False)
    source_revision_id: Mapped[str] = mapped_column(String(16), nullable=False)
    lineage: Mapped[AgentBuildLineage] = relationship(back_populates="source_references")


__all__ = [
    "Agent",
    "AgentBuildLineage",
    "AgentBuildSourceReference",
    "AgentSourceAttachment",
    "AgentVersion",
]
