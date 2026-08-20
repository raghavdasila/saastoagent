from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import CheckConstraint, DateTime, ForeignKey, Index, String, UniqueConstraint, Uuid, text
from sqlalchemy.orm import Mapped, mapped_column

from corpus.persistence.models import Base


class AgentDeployment(Base):
    __tablename__ = "agent_deployments"
    __table_args__ = (
        UniqueConstraint("job_id", name="uq_agent_deployment_job"),
        UniqueConstraint(
            "organization_id", "active_channel_id",
            name="uq_agent_deployment_active_channel",
        ),
        UniqueConstraint(
            "target_id", "request_key", name="uq_agent_deployment_target_request"
        ),
        UniqueConstraint(
            "organization_id", "active_target_id",
            name="uq_agent_deployment_active_target",
        ),
        CheckConstraint(
            "status IN ('queued', 'running', 'ready', 'failed')",
            name="ck_agent_deployment_status",
        ),
        CheckConstraint(
            "mode IN ('sandbox', 'delivery')",
            name="ck_agent_deployment_mode",
        ),
        CheckConstraint(
            "(mode = 'sandbox' AND channel_id IS NULL AND eligibility_id IS NULL) OR "
            "(mode = 'delivery' AND channel_id IS NOT NULL AND eligibility_id IS NOT NULL)",
            name="ck_agent_deployment_mode_fields",
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True)
    organization_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False)
    agent_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("agents.id", ondelete="RESTRICT"), nullable=False)
    target_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("agent_deployment_targets.id", ondelete="RESTRICT"), nullable=False)
    mode: Mapped[str] = mapped_column(String(24), nullable=False)
    channel_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("agent_channels.id", ondelete="RESTRICT"), nullable=True)
    build_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("agent_runnable_builds.id", ondelete="RESTRICT"), nullable=False)
    eligibility_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("agent_evaluation_eligibility.id", ondelete="RESTRICT"), nullable=True)
    request_key: Mapped[str | None] = mapped_column(String(160), nullable=True)
    runtime_deployment_id: Mapped[str | None] = mapped_column(String(64), unique=True, nullable=True)
    job_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("durable_jobs.id", ondelete="SET NULL"), nullable=True
    )
    retry_of_deployment_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("agent_deployments.id", ondelete="RESTRICT"), nullable=True
    )
    active_channel_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("agent_channels.id", ondelete="RESTRICT"), nullable=True
    )
    active_target_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("agent_deployment_targets.id", ondelete="RESTRICT"), nullable=True
    )
    status: Mapped[str] = mapped_column(String(24), nullable=False)
    bundle_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    failure_code: Mapped[str | None] = mapped_column(String(80), nullable=True)
    failure_message: Mapped[str | None] = mapped_column(String(500), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)


class AgentDeploymentTarget(Base):
    __tablename__ = "agent_deployment_targets"
    __table_args__ = (
        UniqueConstraint("channel_id", name="uq_agent_deployment_target_channel"),
        CheckConstraint(
            "mode IN ('sandbox', 'delivery')",
            name="ck_agent_deployment_target_mode",
        ),
        CheckConstraint(
            "(mode = 'sandbox' AND channel_id IS NULL) OR "
            "(mode = 'delivery' AND channel_id IS NOT NULL)",
            name="ck_agent_deployment_target_channel_mode",
        ),
        Index(
            "uq_agent_deployment_target_sandbox_owner_agent",
            "organization_id",
            "agent_id",
            unique=True,
            postgresql_where=text("mode = 'sandbox'"),
            sqlite_where=text("mode = 'sandbox'"),
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True)
    organization_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False)
    agent_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("agents.id", ondelete="RESTRICT"), nullable=False)
    mode: Mapped[str] = mapped_column(String(24), nullable=False)
    channel_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("agent_channels.id", ondelete="RESTRICT"), nullable=True)
    active_deployment_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("agent_deployments.id", ondelete="RESTRICT"), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)


__all__ = ["AgentDeployment", "AgentDeploymentTarget"]
