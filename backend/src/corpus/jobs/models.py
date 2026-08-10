from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any

from sqlalchemy import DateTime, Enum, ForeignKey, Index, Integer, JSON, String, Uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship

from corpus.persistence.models import Base

from .domain import DurableJobState


class DurableJob(Base):
    __tablename__ = "durable_jobs"
    __table_args__ = (
        Index("ix_durable_jobs_owner_updated", "owner_id", "updated_at"),
        Index("ix_durable_jobs_state_updated", "state", "updated_at"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    owner_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False
    )
    job_type: Mapped[str] = mapped_column(String(80), nullable=False)
    state: Mapped[DurableJobState] = mapped_column(
        Enum(DurableJobState, native_enum=False, length=16), nullable=False
    )
    payload: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False)
    attempt_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    max_attempts: Mapped[int] = mapped_column(Integer, nullable=False)
    error_code: Mapped[str | None] = mapped_column(String(80), nullable=True)
    error_message: Mapped[str | None] = mapped_column(String(500), nullable=True)
    result: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    events: Mapped[list[DurableJobEvent]] = relationship(
        back_populates="job", cascade="all, delete-orphan"
    )


class DurableJobEvent(Base):
    __tablename__ = "durable_job_events"
    __table_args__ = (Index("ix_durable_job_events_job_created", "job_id", "created_at"),)

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    job_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("durable_jobs.id", ondelete="CASCADE"), nullable=False
    )
    event_type: Mapped[str] = mapped_column(String(40), nullable=False)
    state: Mapped[DurableJobState] = mapped_column(
        Enum(DurableJobState, native_enum=False, length=16), nullable=False
    )
    details: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    job: Mapped[DurableJob] = relationship(back_populates="events")


__all__ = ["DurableJob", "DurableJobEvent"]
