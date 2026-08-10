"""Add owner-scoped evaluation sets, cases, runs, and eligibility records.

Revision ID: 0010_agent_evaluation
Revises: 0009_builder_sandbox
"""

from alembic import op
import sqlalchemy as sa


revision = "0010_agent_evaluation"
down_revision = "0009_builder_sandbox"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "agent_evaluation_sets",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("organization_id", sa.Uuid(), nullable=False),
        sa.Column("agent_id", sa.Uuid(), nullable=False),
        sa.Column("build_id", sa.Uuid(), nullable=False),
        sa.Column("name", sa.String(160), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["agent_id"], ["agents.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["build_id"], ["agent_runnable_builds.id"], ondelete="RESTRICT"),
        sa.UniqueConstraint("organization_id", "build_id", "name", name="uq_agent_evaluation_set_name"),
    )
    op.create_table(
        "agent_evaluation_cases",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("organization_id", sa.Uuid(), nullable=False),
        sa.Column("evaluation_set_id", sa.Uuid(), nullable=False),
        sa.Column("build_id", sa.Uuid(), nullable=False),
        sa.Column("runtime_case_id", sa.String(64), nullable=False),
        sa.Column("source_kind", sa.String(24), nullable=False),
        sa.Column("source_record_id", sa.String(80), nullable=False),
        sa.Column("title", sa.String(160), nullable=False),
        sa.Column("message", sa.String(4000), nullable=False),
        sa.Column("category", sa.String(80), nullable=False),
        sa.Column("difficulty", sa.String(24), nullable=False),
        sa.Column("expected_operation_ids", sa.JSON(), nullable=False),
        sa.Column("required_response_fields", sa.JSON(), nullable=False),
        sa.Column("require_write_verification", sa.Boolean(), nullable=False),
        sa.Column("mandatory", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["evaluation_set_id"], ["agent_evaluation_sets.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["build_id"], ["agent_runnable_builds.id"], ondelete="RESTRICT"),
        sa.UniqueConstraint("runtime_case_id", name="uq_agent_runtime_evaluation_case"),
    )
    op.create_table(
        "agent_evaluation_runs",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("organization_id", sa.Uuid(), nullable=False),
        sa.Column("case_id", sa.Uuid(), nullable=False),
        sa.Column("build_id", sa.Uuid(), nullable=False),
        sa.Column("runtime_evaluation_run_id", sa.String(64), nullable=False),
        sa.Column("status", sa.String(24), nullable=False),
        sa.Column("deterministic_pass", sa.Boolean(), nullable=False),
        sa.Column("review_pass", sa.Boolean(), nullable=False),
        sa.Column("reasons", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["case_id"], ["agent_evaluation_cases.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["build_id"], ["agent_runnable_builds.id"], ondelete="RESTRICT"),
        sa.UniqueConstraint("runtime_evaluation_run_id", name="uq_agent_runtime_evaluation_run"),
    )
    op.create_table(
        "agent_evaluation_eligibility",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("organization_id", sa.Uuid(), nullable=False),
        sa.Column("agent_id", sa.Uuid(), nullable=False),
        sa.Column("build_id", sa.Uuid(), nullable=False),
        sa.Column("runtime_build_hash", sa.String(64), nullable=False),
        sa.Column("eligible", sa.Boolean(), nullable=False),
        sa.Column("supporting_evaluation_run_ids", sa.JSON(), nullable=False),
        sa.Column("reasons", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["agent_id"], ["agents.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["build_id"], ["agent_runnable_builds.id"], ondelete="RESTRICT"),
    )


def downgrade() -> None:
    op.drop_table("agent_evaluation_eligibility")
    op.drop_table("agent_evaluation_runs")
    op.drop_table("agent_evaluation_cases")
    op.drop_table("agent_evaluation_sets")
