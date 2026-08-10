"""Add durable jobs, lifecycle records, and encrypted credential references.

Revision ID: 0003_shared_infrastructure
Revises: 0002_agents
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa


revision = "0003_shared_infrastructure"
down_revision = "0002_agents"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "durable_jobs",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("owner_id", sa.Uuid(), nullable=False),
        sa.Column("job_type", sa.String(80), nullable=False),
        sa.Column("state", sa.String(16), nullable=False),
        sa.Column("payload", sa.JSON(), nullable=False),
        sa.Column("attempt_count", sa.Integer(), nullable=False),
        sa.Column("max_attempts", sa.Integer(), nullable=False),
        sa.Column("error_code", sa.String(80), nullable=True),
        sa.Column("error_message", sa.String(500), nullable=True),
        sa.Column("result", sa.JSON(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(
            ["owner_id"], ["organizations.id"], ondelete="CASCADE"
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_durable_jobs_owner_updated",
        "durable_jobs",
        ["owner_id", "updated_at"],
    )
    op.create_index(
        "ix_durable_jobs_state_updated",
        "durable_jobs",
        ["state", "updated_at"],
    )
    op.create_table(
        "durable_job_events",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("job_id", sa.Uuid(), nullable=False),
        sa.Column("event_type", sa.String(40), nullable=False),
        sa.Column("state", sa.String(16), nullable=False),
        sa.Column("details", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(
            ["job_id"], ["durable_jobs.id"], ondelete="CASCADE"
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_durable_job_events_job_created",
        "durable_job_events",
        ["job_id", "created_at"],
    )
    op.create_table(
        "credential_references",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("owner_id", sa.Uuid(), nullable=False),
        sa.Column("label", sa.String(120), nullable=False),
        sa.Column("kind", sa.String(80), nullable=False),
        sa.Column("version", sa.Integer(), nullable=False),
        sa.Column("ciphertext", sa.LargeBinary(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(
            ["owner_id"], ["organizations.id"], ondelete="CASCADE"
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_credential_references_owner_updated",
        "credential_references",
        ["owner_id", "updated_at"],
    )


def downgrade() -> None:
    op.drop_index(
        "ix_credential_references_owner_updated",
        table_name="credential_references",
    )
    op.drop_table("credential_references")
    op.drop_index(
        "ix_durable_job_events_job_created", table_name="durable_job_events"
    )
    op.drop_table("durable_job_events")
    op.drop_index("ix_durable_jobs_state_updated", table_name="durable_jobs")
    op.drop_index("ix_durable_jobs_owner_updated", table_name="durable_jobs")
    op.drop_table("durable_jobs")
