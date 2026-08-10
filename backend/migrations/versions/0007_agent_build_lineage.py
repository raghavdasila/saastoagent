"""Add immutable Agent build-to-Source revision lineage.

Revision ID: 0007_agent_build_lineage
Revises: 0006_restrict_agent_attachment_delete
"""

from alembic import op
import sqlalchemy as sa


revision = "0007_agent_build_lineage"
down_revision = "0006_restrict_agent_attachment_delete"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "agent_build_lineages",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("organization_id", sa.Uuid(), nullable=False),
        sa.Column("agent_id", sa.Uuid(), nullable=False),
        sa.Column("build_id", sa.Uuid(), nullable=False),
        sa.Column("agent_version", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["agent_id"], ["agents.id"], ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("organization_id", "build_id", name="uq_agent_build_lineage_build"),
    )
    op.create_table(
        "agent_build_source_references",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("build_lineage_id", sa.Uuid(), nullable=False),
        sa.Column("source_id", sa.String(length=16), nullable=False),
        sa.Column("source_revision_id", sa.String(length=16), nullable=False),
        sa.ForeignKeyConstraint(["build_lineage_id"], ["agent_build_lineages.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("build_lineage_id", "source_id", name="uq_agent_build_source_reference"),
    )


def downgrade() -> None:
    op.drop_table("agent_build_source_references")
    op.drop_table("agent_build_lineages")
