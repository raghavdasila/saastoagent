from __future__ import annotations

import uuid as uuid_pkg

from sqlalchemy import Column, DateTime, ForeignKey, Index, Integer, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import relationship

from .base import Base


class EntrySession(Base):
    __tablename__ = "entry_sessions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid_pkg.uuid4)
    user_id = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    status = Column(String(20), nullable=False, default="active")
    graph_version = Column(String(64), nullable=False, default="entry_v1")
    current_state = Column(JSONB, nullable=True)
    metadata_ = Column("metadata", JSONB, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    runs = relationship(
        "EntryRun",
        back_populates="session",
        cascade="all, delete-orphan",
        order_by="EntryRun.started_at",
    )

    __table_args__ = (
        Index("ix_entry_sessions_user_updated", "user_id", "updated_at"),
    )


class EntryRun(Base):
    __tablename__ = "entry_runs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid_pkg.uuid4)
    session_id = Column(
        UUID(as_uuid=True),
        ForeignKey("entry_sessions.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    user_id = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    status = Column(String(20), nullable=False, default="running")
    graph_version = Column(String(64), nullable=False, default="entry_v1")
    graph_manifest = Column(JSONB, nullable=False)
    request_input = Column(JSONB, nullable=True)
    final_state = Column(JSONB, nullable=True)
    metadata_ = Column("metadata", JSONB, nullable=True)
    started_at = Column(DateTime(timezone=True), server_default=func.now())
    completed_at = Column(DateTime(timezone=True), nullable=True)

    session = relationship("EntrySession", back_populates="runs")
    stages = relationship(
        "EntryStage",
        back_populates="run",
        cascade="all, delete-orphan",
        order_by="EntryStage.sequence",
    )
    outputs = relationship(
        "EntryOutput",
        back_populates="run",
        cascade="all, delete-orphan",
        order_by="EntryOutput.sequence",
    )
    artifacts = relationship(
        "EntryArtifact",
        back_populates="run",
        cascade="all, delete-orphan",
        order_by="EntryArtifact.created_at",
    )

    __table_args__ = (
        Index("ix_entry_runs_session_started", "session_id", "started_at"),
    )


class EntryStage(Base):
    __tablename__ = "entry_stages"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid_pkg.uuid4)
    run_id = Column(
        UUID(as_uuid=True),
        ForeignKey("entry_runs.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    session_id = Column(
        UUID(as_uuid=True),
        ForeignKey("entry_sessions.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    stage_id = Column(String(120), nullable=False)
    parent_stage_id = Column(String(120), nullable=True)
    depends_on = Column(JSONB, nullable=True)
    sequence = Column(Integer, nullable=False)
    lane = Column(String(60), nullable=False)
    status = Column(String(20), nullable=False, default="running")
    started_at = Column(DateTime(timezone=True), server_default=func.now())
    completed_at = Column(DateTime(timezone=True), nullable=True)
    duration_ms = Column(Integer, nullable=True)
    input_payload = Column(JSONB, nullable=True)
    output_payload = Column(JSONB, nullable=True)
    error = Column(Text, nullable=True)

    run = relationship("EntryRun", back_populates="stages")

    __table_args__ = (
        Index("ix_entry_stages_run_sequence", "run_id", "sequence"),
        Index("ix_entry_stages_session_stage", "session_id", "stage_id"),
    )


class EntryOutput(Base):
    __tablename__ = "entry_outputs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid_pkg.uuid4)
    run_id = Column(
        UUID(as_uuid=True),
        ForeignKey("entry_runs.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    session_id = Column(
        UUID(as_uuid=True),
        ForeignKey("entry_sessions.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    stage_id = Column(String(120), nullable=True)
    sequence = Column(Integer, nullable=False)
    lane = Column(String(60), nullable=False, default="entry")
    content = Column(Text, nullable=False, default="")
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    run = relationship("EntryRun", back_populates="outputs")

    __table_args__ = (
        Index("ix_entry_outputs_run_sequence", "run_id", "sequence"),
    )


class EntryArtifact(Base):
    __tablename__ = "entry_artifacts"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid_pkg.uuid4)
    run_id = Column(
        UUID(as_uuid=True),
        ForeignKey("entry_runs.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    session_id = Column(
        UUID(as_uuid=True),
        ForeignKey("entry_sessions.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    stage_id = Column(String(120), nullable=True)
    artifact_type = Column(String(80), nullable=False)
    name = Column(String(120), nullable=False)
    payload = Column(JSONB, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    run = relationship("EntryRun", back_populates="artifacts")

    __table_args__ = (
        Index("ix_entry_artifacts_run_created", "run_id", "created_at"),
    )