"""Persist the explicit draft runtime lifecycle for immutable Agent builds.

Revision ID: 0013_builder_runtime_lifecycle
Revises: 0012_builder_navgraph
"""

from alembic import op
import sqlalchemy as sa


revision = "0013_builder_runtime_lifecycle"
down_revision = "0012_builder_navgraph"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Existing builds were executable before this explicit lifecycle existed.
    # Backfill them as running so a migration never disables deployed/current use.
    with op.batch_alter_table("agent_runnable_builds") as batch:
        batch.add_column(
            sa.Column(
                "runtime_lifecycle",
                sa.String(16),
                nullable=False,
                server_default="running",
            )
        )
        batch.create_check_constraint(
            "ck_runnable_build_runtime_lifecycle",
            "runtime_lifecycle IN ('stopped', 'running', 'removed')",
        )


def downgrade() -> None:
    with op.batch_alter_table("agent_runnable_builds") as batch:
        batch.drop_constraint(
            "ck_runnable_build_runtime_lifecycle", type_="check"
        )
        batch.drop_column("runtime_lifecycle")
