"""Add immutable Agent Designer revisions and build requests.

Revision ID: 0008_agent_designer
Revises: 0007_agent_build_lineage
"""

from alembic import op
import sqlalchemy as sa


revision = "0008_agent_designer"
down_revision = "0007_agent_build_lineage"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "agent_designs",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("organization_id", sa.Uuid(), nullable=False),
        sa.Column("agent_id", sa.Uuid(), nullable=False),
        sa.Column("current_revision_id", sa.Uuid(), nullable=False),
        sa.Column("current_revision", sa.Integer(), nullable=False),
        sa.Column("accepted_revision_id", sa.Uuid(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["agent_id"], ["agents.id"], ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("organization_id", "agent_id", name="uq_agent_design_owner_agent"),
    )
    op.create_table(
        "agent_design_revisions",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("design_id", sa.Uuid(), nullable=False),
        sa.Column("revision", sa.Integer(), nullable=False),
        sa.Column("agent_version", sa.Integer(), nullable=False),
        sa.Column("input_fingerprint", sa.String(length=64), nullable=False),
        sa.Column("content", sa.JSON(), nullable=False),
        sa.Column("source_inputs", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["design_id"], ["agent_designs.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("design_id", "revision", name="uq_agent_design_revision"),
    )
    op.create_table(
        "agent_build_requests",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("organization_id", sa.Uuid(), nullable=False),
        sa.Column("agent_id", sa.Uuid(), nullable=False),
        sa.Column("design_revision_id", sa.Uuid(), nullable=False),
        sa.Column("status", sa.String(length=24), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["agent_id"], ["agents.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["design_revision_id"], ["agent_design_revisions.id"], ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("organization_id", "design_revision_id", name="uq_agent_build_request_revision"),
    )


def downgrade() -> None:
    op.drop_table("agent_build_requests")
    op.drop_table("agent_design_revisions")
    op.drop_table("agent_designs")
