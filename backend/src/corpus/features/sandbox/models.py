from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, JSON, String, UniqueConstraint, Uuid
from sqlalchemy.orm import Mapped, mapped_column

from corpus.persistence.models import Base


class AgentSandboxSession(Base):
    __tablename__ = "agent_sandbox_sessions"
    __table_args__ = (UniqueConstraint("runtime_session_id", name="uq_sandbox_runtime_session"),)
    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True)
    organization_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False)
    agent_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("agents.id", ondelete="RESTRICT"), nullable=False)
    build_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("agent_runnable_builds.id", ondelete="RESTRICT"), nullable=False)
    runtime_session_id: Mapped[str] = mapped_column(String(64), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)


class AgentSandboxRun(Base):
    __tablename__ = "agent_sandbox_runs"
    __table_args__ = (UniqueConstraint("runtime_run_id", name="uq_sandbox_runtime_run"),)
    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True)
    session_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("agent_sandbox_sessions.id", ondelete="CASCADE"), nullable=False)
    organization_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False)
    agent_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("agents.id", ondelete="RESTRICT"), nullable=False)
    build_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("agent_runnable_builds.id", ondelete="RESTRICT"), nullable=False)
    runtime_build_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    runtime_run_id: Mapped[str] = mapped_column(String(64), nullable=False)
    status: Mapped[str] = mapped_column(String(24), nullable=False)
    message: Mapped[str] = mapped_column(String(4000), nullable=False)
    awaiting: Mapped[str | None] = mapped_column(String(80), nullable=True)
    final_response: Mapped[str | None] = mapped_column(String(12_000), nullable=True)
    api_call_count: Mapped[int] = mapped_column(Integer, nullable=False)
    safe_events: Mapped[list[dict[str, object]]] = mapped_column(JSON, nullable=False)
    routedeck_projection: Mapped[dict[str, object]] = mapped_column(JSON, nullable=False)
    failure_code: Mapped[str | None] = mapped_column(String(80), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)


__all__ = ["AgentSandboxRun", "AgentSandboxSession"]
