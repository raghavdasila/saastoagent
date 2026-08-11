"""Add durable Evaluation run attempts.

Revision ID: 0017_evaluation_run_lifecycle
Revises: 0016_builder_pause_lifecycle
"""

from alembic import op
import sqlalchemy as sa


revision = "0017_evaluation_run_lifecycle"
down_revision = "0016_builder_pause_lifecycle"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "agent_evaluation_run_attempts",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("organization_id", sa.Uuid(), nullable=False),
        sa.Column("agent_id", sa.Uuid(), nullable=False),
        sa.Column("evaluation_set_id", sa.Uuid(), nullable=False),
        sa.Column("case_id", sa.Uuid(), nullable=False),
        sa.Column("build_id", sa.Uuid(), nullable=False),
        sa.Column("case_revision", sa.Integer(), nullable=False),
        sa.Column("job_id", sa.Uuid(), nullable=True),
        sa.Column("retry_of_attempt_id", sa.Uuid(), nullable=True),
        sa.Column("active_case_id", sa.Uuid(), nullable=True),
        sa.Column("status", sa.String(length=24), nullable=False),
        sa.Column("failure_code", sa.String(length=80), nullable=True),
        sa.Column("failure_message", sa.String(length=500), nullable=True),
        sa.Column("runtime_evaluation_run_id", sa.String(length=64), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.CheckConstraint(
            "status IN ('queued', 'running', 'succeeded', 'failed')",
            name="ck_agent_evaluation_run_attempt_status",
        ),
        sa.ForeignKeyConstraint(
            ["organization_id"], ["organizations.id"], ondelete="CASCADE"
        ),
        sa.ForeignKeyConstraint(
            ["agent_id"], ["agents.id"], ondelete="RESTRICT"
        ),
        sa.ForeignKeyConstraint(
            ["evaluation_set_id"], ["agent_evaluation_sets.id"], ondelete="RESTRICT"
        ),
        sa.ForeignKeyConstraint(
            ["case_id"], ["agent_evaluation_cases.id"], ondelete="RESTRICT"
        ),
        sa.ForeignKeyConstraint(
            ["active_case_id"], ["agent_evaluation_cases.id"], ondelete="RESTRICT"
        ),
        sa.ForeignKeyConstraint(
            ["build_id"], ["agent_runnable_builds.id"], ondelete="RESTRICT"
        ),
        sa.ForeignKeyConstraint(
            ["job_id"], ["durable_jobs.id"], ondelete="SET NULL"
        ),
        sa.ForeignKeyConstraint(
            ["retry_of_attempt_id"],
            ["agent_evaluation_run_attempts.id"],
            ondelete="RESTRICT",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("job_id", name="uq_agent_evaluation_run_attempt_job"),
        sa.UniqueConstraint(
            "organization_id",
            "active_case_id",
            name="uq_agent_evaluation_active_case_attempt",
        ),
    )


def downgrade() -> None:
    op.drop_table("agent_evaluation_run_attempts")
