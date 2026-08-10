"""Add immutable runnable builds and owner-scoped Sandbox sessions.

Revision ID: 0009_builder_sandbox
Revises: 0008_agent_designer
"""

from alembic import op
import sqlalchemy as sa


revision = "0009_builder_sandbox"
down_revision = "0008_agent_designer"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "agent_runnable_builds",
        sa.Column("id", sa.Uuid(), nullable=False), sa.Column("organization_id", sa.Uuid(), nullable=False),
        sa.Column("agent_id", sa.Uuid(), nullable=False), sa.Column("build_request_id", sa.Uuid(), nullable=False),
        sa.Column("design_revision_id", sa.Uuid(), nullable=False), sa.Column("agent_version", sa.Integer(), nullable=False),
        sa.Column("status", sa.String(length=24), nullable=False), sa.Column("runtime_build_hash", sa.String(length=64), nullable=True),
        sa.Column("model", sa.String(length=255), nullable=True), sa.Column("model_digest", sa.String(length=255), nullable=True),
        sa.Column("source_bindings", sa.JSON(), nullable=False), sa.Column("allowed_operation_ids", sa.JSON(), nullable=False),
        sa.Column("failure_code", sa.String(length=80), nullable=True), sa.Column("failure_message", sa.String(length=500), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False), sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["agent_id"], ["agents.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["build_request_id"], ["agent_build_requests.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["design_revision_id"], ["agent_design_revisions.id"], ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("organization_id", "build_request_id", name="uq_runnable_build_request"),
        sa.UniqueConstraint("runtime_build_hash", name="uq_runnable_build_hash"),
    )
    op.create_table(
        "agent_sandbox_sessions",
        sa.Column("id", sa.Uuid(), nullable=False), sa.Column("organization_id", sa.Uuid(), nullable=False),
        sa.Column("agent_id", sa.Uuid(), nullable=False), sa.Column("build_id", sa.Uuid(), nullable=False),
        sa.Column("runtime_session_id", sa.String(length=64), nullable=False), sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["agent_id"], ["agents.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["build_id"], ["agent_runnable_builds.id"], ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id"), sa.UniqueConstraint("runtime_session_id", name="uq_sandbox_runtime_session"),
    )
    op.create_table(
        "agent_sandbox_runs",
        sa.Column("id", sa.Uuid(), nullable=False), sa.Column("session_id", sa.Uuid(), nullable=False),
        sa.Column("organization_id", sa.Uuid(), nullable=False), sa.Column("agent_id", sa.Uuid(), nullable=False),
        sa.Column("build_id", sa.Uuid(), nullable=False), sa.Column("runtime_build_hash", sa.String(length=64), nullable=False),
        sa.Column("runtime_run_id", sa.String(length=64), nullable=False), sa.Column("status", sa.String(length=24), nullable=False),
        sa.Column("message", sa.String(length=4000), nullable=False),
        sa.Column("awaiting", sa.String(length=80), nullable=True), sa.Column("final_response", sa.String(length=12000), nullable=True),
        sa.Column("api_call_count", sa.Integer(), nullable=False), sa.Column("safe_events", sa.JSON(), nullable=False),
        sa.Column("failure_code", sa.String(length=80), nullable=True), sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["session_id"], ["agent_sandbox_sessions.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["agent_id"], ["agents.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["build_id"], ["agent_runnable_builds.id"], ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id"), sa.UniqueConstraint("runtime_run_id", name="uq_sandbox_runtime_run"),
    )


def downgrade() -> None:
    op.drop_table("agent_sandbox_runs")
    op.drop_table("agent_sandbox_sessions")
    op.drop_table("agent_runnable_builds")
