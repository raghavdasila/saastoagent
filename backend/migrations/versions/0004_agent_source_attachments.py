"""Create immutable Agent to Source revision attachments.

Revision ID: 0004_agent_source_attachments
Revises: 0003_shared_infrastructure
"""

from alembic import op
import sqlalchemy as sa


revision = "0004_agent_source_attachments"
down_revision = "0003_shared_infrastructure"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "agent_source_attachments",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("organization_id", sa.Uuid(), nullable=False),
        sa.Column("agent_id", sa.Uuid(), nullable=False),
        sa.Column("source_id", sa.String(16), nullable=False),
        sa.Column("source_revision_id", sa.String(16), nullable=False),
        sa.Column("source_display_name", sa.String(128), nullable=False),
        sa.Column("attached_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["agent_id"], ["agents.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("agent_id", "source_id", name="uq_agent_source_attachment"),
    )
    op.create_index(
        "ix_agent_source_attachments_owner_agent",
        "agent_source_attachments",
        ["organization_id", "agent_id", "attached_at"],
    )


def downgrade() -> None:
    op.drop_index(
        "ix_agent_source_attachments_owner_agent",
        table_name="agent_source_attachments",
    )
    op.drop_table("agent_source_attachments")
