"""Add owner-scoped hosted Web channels and immutable deployments.

Revision ID: 0011_channels_deployment
Revises: 0010_agent_evaluation
"""

from alembic import op
import sqlalchemy as sa


revision = "0011_channels_deployment"
down_revision = "0010_agent_evaluation"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "agent_channels",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("organization_id", sa.Uuid(), nullable=False),
        sa.Column("agent_id", sa.Uuid(), nullable=False),
        sa.Column("runtime_channel_id", sa.String(64), nullable=True, unique=True),
        sa.Column("name", sa.String(160), nullable=False),
        sa.Column("slug", sa.String(120), nullable=False, unique=True),
        sa.Column("status", sa.String(24), nullable=False),
        sa.Column("enabled", sa.Boolean(), nullable=False),
        sa.Column("active_deployment_id", sa.Uuid(), nullable=True),
        sa.Column("failure_code", sa.String(80), nullable=True),
        sa.Column("failure_message", sa.String(500), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["agent_id"], ["agents.id"], ondelete="RESTRICT"),
    )
    op.create_table(
        "agent_deployments",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("organization_id", sa.Uuid(), nullable=False),
        sa.Column("agent_id", sa.Uuid(), nullable=False),
        sa.Column("channel_id", sa.Uuid(), nullable=False),
        sa.Column("build_id", sa.Uuid(), nullable=False),
        sa.Column("eligibility_id", sa.Uuid(), nullable=False),
        sa.Column("runtime_deployment_id", sa.String(64), nullable=True, unique=True),
        sa.Column("status", sa.String(24), nullable=False),
        sa.Column("bundle_hash", sa.String(64), nullable=False),
        sa.Column("failure_code", sa.String(80), nullable=True),
        sa.Column("failure_message", sa.String(500), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["agent_id"], ["agents.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["channel_id"], ["agent_channels.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["build_id"], ["agent_runnable_builds.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["eligibility_id"], ["agent_evaluation_eligibility.id"], ondelete="RESTRICT"),
    )


def downgrade() -> None:
    op.drop_table("agent_deployments")
    op.drop_table("agent_channels")
