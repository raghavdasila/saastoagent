from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import CheckConstraint, DateTime, ForeignKey, JSON, String, UniqueConstraint, Uuid
from sqlalchemy.orm import Mapped, mapped_column

from corpus.persistence.models import Base


class AgentRunnableBuild(Base):
    __tablename__ = "agent_runnable_builds"
    __table_args__ = (
        UniqueConstraint(
            "organization_id", "build_request_id", "attempt_number",
            name="uq_runnable_build_request_attempt",
        ),
        UniqueConstraint("runtime_build_hash", name="uq_runnable_build_hash"),
        CheckConstraint(
            "runtime_lifecycle IN ('stopped', 'running', 'removed')",
            name="ck_runnable_build_runtime_lifecycle",
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True)
    organization_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False)
    agent_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("agents.id", ondelete="RESTRICT"), nullable=False)
    build_request_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("agent_build_requests.id", ondelete="RESTRICT"), nullable=False)
    design_revision_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("agent_design_revisions.id", ondelete="RESTRICT"), nullable=False)
    agent_version: Mapped[int]
    attempt_number: Mapped[int]
    status: Mapped[str] = mapped_column(String(24), nullable=False)
    runtime_lifecycle: Mapped[str] = mapped_column(String(16), nullable=False)
    runtime_build_hash: Mapped[str | None] = mapped_column(String(64), nullable=True)
    model: Mapped[str | None] = mapped_column(String(255), nullable=True)
    model_digest: Mapped[str | None] = mapped_column(String(255), nullable=True)
    source_bindings: Mapped[list[dict[str, object]]] = mapped_column(JSON, nullable=False)
    allowed_operation_ids: Mapped[list[str]] = mapped_column(JSON, nullable=False)
    navgraph_hash: Mapped[str | None] = mapped_column(String(64), nullable=True)
    compiled_navgraph: Mapped[dict[str, object]] = mapped_column(JSON, nullable=False)
    frontend_contract: Mapped[dict[str, object]] = mapped_column(JSON, nullable=False)
    failure_code: Mapped[str | None] = mapped_column(String(80), nullable=True)
    failure_message: Mapped[str | None] = mapped_column(String(500), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)


__all__ = ["AgentRunnableBuild"]
