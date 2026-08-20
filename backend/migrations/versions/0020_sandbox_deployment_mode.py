"""Generalize Agent deployments for Sandbox and Delivery modes.

Revision ID: 0020_sandbox_deployment_mode
Revises: 0019_builder_assembly_lifecycle
"""

from alembic import op
import sqlalchemy as sa


revision = "0020_sandbox_deployment_mode"
down_revision = "0019_builder_assembly_lifecycle"
branch_labels = None
depends_on = None


def upgrade() -> None:
    inspector = sa.inspect(op.get_bind())
    target_table_exists = inspector.has_table("agent_deployment_targets")
    if not target_table_exists:
        op.create_table(
        "agent_deployment_targets",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("organization_id", sa.Uuid(), nullable=False),
        sa.Column("agent_id", sa.Uuid(), nullable=False),
        sa.Column("mode", sa.String(24), nullable=False),
        sa.Column("channel_id", sa.Uuid(), nullable=True),
        sa.Column("active_deployment_id", sa.Uuid(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["agent_id"], ["agents.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["channel_id"], ["agent_channels.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["active_deployment_id"], ["agent_deployments.id"], ondelete="RESTRICT"),
        sa.UniqueConstraint("channel_id", name="uq_agent_deployment_target_channel"),
        sa.CheckConstraint("mode IN ('sandbox', 'delivery')", name="ck_agent_deployment_target_mode"),
        sa.CheckConstraint(
            "(mode = 'sandbox' AND channel_id IS NULL) OR "
            "(mode = 'delivery' AND channel_id IS NOT NULL)",
            name="ck_agent_deployment_target_channel_mode",
        ),
        )
        op.create_index(
            "uq_agent_deployment_target_sandbox_owner_agent",
            "agent_deployment_targets",
            ["organization_id", "agent_id"],
            unique=True,
            postgresql_where=sa.text("mode = 'sandbox'"),
            sqlite_where=sa.text("mode = 'sandbox'"),
        )
        op.execute(
            """INSERT INTO agent_deployment_targets
               (id, organization_id, agent_id, mode, channel_id, active_deployment_id, created_at)
               SELECT id, organization_id, agent_id, 'delivery', id, active_deployment_id, created_at
               FROM agent_channels"""
        )
    with op.batch_alter_table("agent_deployments") as batch:
        batch.add_column(sa.Column("target_id", sa.Uuid(), nullable=True))
        batch.add_column(sa.Column("mode", sa.String(24), nullable=True))
        batch.add_column(sa.Column("request_key", sa.String(160), nullable=True))
        batch.add_column(sa.Column("active_target_id", sa.Uuid(), nullable=True))
    op.execute(
        "UPDATE agent_deployments SET target_id = channel_id, mode = 'delivery', "
        "active_target_id = active_channel_id"
    )
    with op.batch_alter_table("agent_deployments") as batch:
        batch.alter_column("target_id", nullable=False)
        batch.alter_column("mode", nullable=False)
        batch.alter_column("channel_id", nullable=True)
        batch.alter_column("eligibility_id", nullable=True)
        batch.create_foreign_key(
            "fk_agent_deployment_target", "agent_deployment_targets",
            ["target_id"], ["id"], ondelete="RESTRICT",
        )
        batch.create_foreign_key(
            "fk_agent_deployment_active_target", "agent_deployment_targets",
            ["active_target_id"], ["id"], ondelete="RESTRICT",
        )
        batch.create_unique_constraint(
            "uq_agent_deployment_target_request", ["target_id", "request_key"]
        )
        batch.create_unique_constraint(
            "uq_agent_deployment_active_target", ["organization_id", "active_target_id"]
        )
        batch.create_check_constraint(
            "ck_agent_deployment_mode", "mode IN ('sandbox', 'delivery')"
        )
        batch.create_check_constraint(
            "ck_agent_deployment_mode_fields",
            "(mode = 'sandbox' AND channel_id IS NULL AND eligibility_id IS NULL) OR "
            "(mode = 'delivery' AND channel_id IS NOT NULL AND eligibility_id IS NOT NULL)",
        )
    with op.batch_alter_table("agent_evaluation_run_attempts") as batch:
        batch.add_column(sa.Column("sandbox_deployment_id", sa.Uuid(), nullable=True))
        batch.add_column(sa.Column("sandbox_session_id", sa.String(64), nullable=True))
        batch.add_column(sa.Column("runtime_agent_run_id", sa.String(160), nullable=True))
        batch.create_foreign_key(
            "fk_evaluation_attempt_sandbox_deployment",
            "agent_deployments",
            ["sandbox_deployment_id"],
            ["id"],
            ondelete="RESTRICT",
        )


def downgrade() -> None:
    with op.batch_alter_table("agent_evaluation_run_attempts") as batch:
        batch.drop_constraint(
            "fk_evaluation_attempt_sandbox_deployment", type_="foreignkey"
        )
        batch.drop_column("runtime_agent_run_id")
        batch.drop_column("sandbox_session_id")
        batch.drop_column("sandbox_deployment_id")
    with op.batch_alter_table("agent_deployments") as batch:
        batch.drop_constraint("ck_agent_deployment_mode_fields", type_="check")
        batch.drop_constraint("ck_agent_deployment_mode", type_="check")
        batch.drop_constraint("uq_agent_deployment_active_target", type_="unique")
        batch.drop_constraint("uq_agent_deployment_target_request", type_="unique")
        batch.drop_constraint("fk_agent_deployment_active_target", type_="foreignkey")
        batch.drop_constraint("fk_agent_deployment_target", type_="foreignkey")
        batch.alter_column("eligibility_id", nullable=False)
        batch.alter_column("channel_id", nullable=False)
        batch.drop_column("active_target_id")
        batch.drop_column("request_key")
        batch.drop_column("mode")
        batch.drop_column("target_id")
    op.drop_index(
        "uq_agent_deployment_target_sandbox_owner_agent",
        table_name="agent_deployment_targets",
    )
    op.drop_table("agent_deployment_targets")
