"""Prevent Agent deletion from cascading through Source attachments.

Revision ID: 0006_restrict_agent_attachment_delete
Revises: 0005_remove_agent_attachment_display_name
"""

from alembic import op


revision = "0006_restrict_agent_attachment_delete"
down_revision = "0005_remove_agent_attachment_display_name"
branch_labels = None
depends_on = None


_NAMING_CONVENTION = {
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
}
_FOREIGN_KEY_NAME = "fk_agent_source_attachments_agent_id_agents"


def upgrade() -> None:
    with op.batch_alter_table(
        "agent_source_attachments",
        naming_convention=_NAMING_CONVENTION,
    ) as batch_op:
        batch_op.drop_constraint(_FOREIGN_KEY_NAME, type_="foreignkey")
        batch_op.create_foreign_key(
            _FOREIGN_KEY_NAME,
            "agents",
            ["agent_id"],
            ["id"],
            ondelete="RESTRICT",
        )


def downgrade() -> None:
    with op.batch_alter_table(
        "agent_source_attachments",
        naming_convention=_NAMING_CONVENTION,
    ) as batch_op:
        batch_op.drop_constraint(_FOREIGN_KEY_NAME, type_="foreignkey")
        batch_op.create_foreign_key(
            _FOREIGN_KEY_NAME,
            "agents",
            ["agent_id"],
            ["id"],
            ondelete="CASCADE",
        )
