from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import Boolean, CheckConstraint, DateTime, ForeignKey, Integer, JSON, String, UniqueConstraint, Uuid
from sqlalchemy.orm import Mapped, mapped_column

from corpus.persistence.models import Base


class AgentEvaluationSet(Base):
    __tablename__ = "agent_evaluation_sets"
    __table_args__ = (UniqueConstraint("organization_id", "build_id", "name", name="uq_agent_evaluation_set_name"),)
    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True)
    organization_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False)
    agent_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("agents.id", ondelete="RESTRICT"), nullable=False)
    build_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("agent_runnable_builds.id", ondelete="RESTRICT"), nullable=False)
    name: Mapped[str] = mapped_column(String(160), nullable=False)
    generation_job_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("durable_jobs.id", ondelete="SET NULL"), nullable=True
    )
    generation_status: Mapped[str] = mapped_column(
        String(24), nullable=False, default="manual"
    )
    generation_failure_code: Mapped[str | None] = mapped_column(String(80), nullable=True)
    generation_failure_message: Mapped[str | None] = mapped_column(String(500), nullable=True)
    generation_summary: Mapped[dict[str, object] | None] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)


class AgentEvaluationCase(Base):
    __tablename__ = "agent_evaluation_cases"
    __table_args__ = (UniqueConstraint("runtime_case_id", name="uq_agent_runtime_evaluation_case"),)
    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True)
    organization_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False)
    evaluation_set_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("agent_evaluation_sets.id", ondelete="CASCADE"), nullable=False)
    build_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("agent_runnable_builds.id", ondelete="RESTRICT"), nullable=False)
    runtime_case_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
    generation_task_id: Mapped[str | None] = mapped_column(String(120), nullable=True)
    source_kind: Mapped[str] = mapped_column(String(24), nullable=False)
    source_record_id: Mapped[str] = mapped_column(String(80), nullable=False)
    title: Mapped[str] = mapped_column(String(160), nullable=False)
    message: Mapped[str] = mapped_column(String(4000), nullable=False)
    category: Mapped[str] = mapped_column(String(80), nullable=False)
    difficulty: Mapped[str] = mapped_column(String(24), nullable=False)
    expected_operation_ids: Mapped[list[str]] = mapped_column(JSON, nullable=False)
    required_response_fields: Mapped[list[str]] = mapped_column(JSON, nullable=False)
    require_write_verification: Mapped[bool] = mapped_column(Boolean, nullable=False)
    mandatory: Mapped[bool] = mapped_column(Boolean, nullable=False)
    current_revision: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    removed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)


class AgentEvaluationCaseRevision(Base):
    __tablename__ = "agent_evaluation_case_revisions"
    __table_args__ = (
        UniqueConstraint("case_id", "revision", name="uq_agent_evaluation_case_revision"),
    )
    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True)
    organization_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False)
    case_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("agent_evaluation_cases.id", ondelete="RESTRICT"), nullable=False)
    revision: Mapped[int] = mapped_column(Integer, nullable=False)
    title: Mapped[str] = mapped_column(String(160), nullable=False)
    category: Mapped[str] = mapped_column(String(80), nullable=False)
    difficulty: Mapped[str] = mapped_column(String(24), nullable=False)
    mandatory: Mapped[bool] = mapped_column(Boolean, nullable=False)
    changed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)


class AgentEvaluationRun(Base):
    __tablename__ = "agent_evaluation_runs"
    __table_args__ = (UniqueConstraint("runtime_evaluation_run_id", name="uq_agent_runtime_evaluation_run"),)
    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True)
    organization_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False)
    case_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("agent_evaluation_cases.id", ondelete="RESTRICT"), nullable=False)
    build_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("agent_runnable_builds.id", ondelete="RESTRICT"), nullable=False)
    runtime_evaluation_run_id: Mapped[str] = mapped_column(String(64), nullable=False)
    status: Mapped[str] = mapped_column(String(24), nullable=False)
    deterministic_pass: Mapped[bool] = mapped_column(Boolean, nullable=False)
    review_pass: Mapped[bool] = mapped_column(Boolean, nullable=False)
    case_revision: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    reasons: Mapped[list[str]] = mapped_column(JSON, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)


class AgentEvaluationRunAttempt(Base):
    __tablename__ = "agent_evaluation_run_attempts"
    __table_args__ = (
        UniqueConstraint("job_id", name="uq_agent_evaluation_run_attempt_job"),
        UniqueConstraint(
            "organization_id", "active_case_id",
            name="uq_agent_evaluation_active_case_attempt",
        ),
        CheckConstraint(
            "status IN ('queued', 'running', 'succeeded', 'failed')",
            name="ck_agent_evaluation_run_attempt_status",
        ),
    )
    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True)
    organization_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False
    )
    agent_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("agents.id", ondelete="RESTRICT"), nullable=False
    )
    evaluation_set_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("agent_evaluation_sets.id", ondelete="RESTRICT"), nullable=False
    )
    case_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("agent_evaluation_cases.id", ondelete="RESTRICT"), nullable=False
    )
    build_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("agent_runnable_builds.id", ondelete="RESTRICT"), nullable=False
    )
    case_revision: Mapped[int] = mapped_column(Integer, nullable=False)
    job_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("durable_jobs.id", ondelete="SET NULL"), nullable=True
    )
    retry_of_attempt_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("agent_evaluation_run_attempts.id", ondelete="RESTRICT"), nullable=True
    )
    active_case_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("agent_evaluation_cases.id", ondelete="RESTRICT"), nullable=True
    )
    status: Mapped[str] = mapped_column(String(24), nullable=False)
    failure_code: Mapped[str | None] = mapped_column(String(80), nullable=True)
    failure_message: Mapped[str | None] = mapped_column(String(500), nullable=True)
    runtime_evaluation_run_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class AgentEvaluationEligibility(Base):
    __tablename__ = "agent_evaluation_eligibility"
    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True)
    organization_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False)
    agent_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("agents.id", ondelete="RESTRICT"), nullable=False)
    build_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("agent_runnable_builds.id", ondelete="RESTRICT"), nullable=False)
    runtime_build_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    eligible: Mapped[bool] = mapped_column(Boolean, nullable=False)
    supporting_evaluation_run_ids: Mapped[list[str]] = mapped_column(JSON, nullable=False)
    reasons: Mapped[list[str]] = mapped_column(JSON, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)


__all__ = [
    "AgentEvaluationCase",
    "AgentEvaluationCaseRevision",
    "AgentEvaluationEligibility",
    "AgentEvaluationRun",
    "AgentEvaluationRunAttempt",
    "AgentEvaluationSet",
]
