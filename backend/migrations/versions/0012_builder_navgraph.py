"""Persist immutable per-build RouteDeck NavGraph contracts.

Revision ID: 0012_builder_navgraph
Revises: 0011_channels_deployment
"""

from alembic import op
import sqlalchemy as sa


revision = "0012_builder_navgraph"
down_revision = "0011_channels_deployment"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("agent_runnable_builds", sa.Column("navgraph_hash", sa.String(64), nullable=True))
    op.add_column("agent_runnable_builds", sa.Column("compiled_navgraph", sa.JSON(), nullable=False, server_default="{}"))
    op.add_column("agent_runnable_builds", sa.Column("frontend_contract", sa.JSON(), nullable=False, server_default="{}"))
    op.add_column("agent_sandbox_runs", sa.Column("routedeck_projection", sa.JSON(), nullable=False, server_default="{}"))


def downgrade() -> None:
    op.drop_column("agent_sandbox_runs", "routedeck_projection")
    op.drop_column("agent_runnable_builds", "frontend_contract")
    op.drop_column("agent_runnable_builds", "compiled_navgraph")
    op.drop_column("agent_runnable_builds", "navgraph_hash")
