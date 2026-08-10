"""Remove duplicated Source display data from Agent attachments.

Revision ID: 0005_remove_agent_attachment_display_name
Revises: 0004_agent_source_attachments
"""

from alembic import op
import sqlalchemy as sa


revision = "0005_remove_agent_attachment_display_name"
down_revision = "0004_agent_source_attachments"
branch_labels = None
depends_on = None


def upgrade() -> None:
    with op.batch_alter_table("agent_source_attachments") as batch_op:
        batch_op.drop_column("source_display_name")


def downgrade() -> None:
    with op.batch_alter_table("agent_source_attachments") as batch_op:
        batch_op.add_column(
            sa.Column(
                "source_display_name",
                sa.String(128),
                nullable=False,
                server_default="",
            )
        )
    with op.batch_alter_table("agent_source_attachments") as batch_op:
        batch_op.alter_column("source_display_name", server_default=None)
