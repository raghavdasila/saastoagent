"""Add durable Deployment attempt lifecycle.

Revision ID: 0018_deployment_lifecycle
Revises: 0017_evaluation_run_lifecycle
"""

from alembic import op
import sqlalchemy as sa


revision = "0018_deployment_lifecycle"
down_revision = "0017_evaluation_run_lifecycle"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(
        "UPDATE agent_deployments "
        "SET status = 'failed', "
        "failure_code = COALESCE(failure_code, 'deployment_interrupted'), "
        "failure_message = COALESCE(failure_message, 'The earlier deployment attempt was interrupted.') "
        "WHERE status = 'verifying'"
    )
    with op.batch_alter_table("agent_deployments") as batch:
        batch.add_column(sa.Column("job_id", sa.Uuid(), nullable=True))
        batch.add_column(sa.Column("retry_of_deployment_id", sa.Uuid(), nullable=True))
        batch.add_column(sa.Column("active_channel_id", sa.Uuid(), nullable=True))
        batch.create_foreign_key(
            "fk_agent_deployment_job", "durable_jobs", ["job_id"], ["id"],
            ondelete="SET NULL",
        )
        batch.create_foreign_key(
            "fk_agent_deployment_retry", "agent_deployments",
            ["retry_of_deployment_id"], ["id"], ondelete="RESTRICT",
        )
        batch.create_foreign_key(
            "fk_agent_deployment_active_channel", "agent_channels",
            ["active_channel_id"], ["id"], ondelete="RESTRICT",
        )
        batch.create_unique_constraint("uq_agent_deployment_job", ["job_id"])
        batch.create_unique_constraint(
            "uq_agent_deployment_active_channel",
            ["organization_id", "active_channel_id"],
        )
        batch.create_check_constraint(
            "ck_agent_deployment_status",
            "status IN ('queued', 'running', 'ready', 'failed')",
        )


def downgrade() -> None:
    with op.batch_alter_table("agent_deployments") as batch:
        batch.drop_constraint("ck_agent_deployment_status", type_="check")
        batch.drop_constraint("uq_agent_deployment_active_channel", type_="unique")
        batch.drop_constraint("uq_agent_deployment_job", type_="unique")
        batch.drop_constraint("fk_agent_deployment_active_channel", type_="foreignkey")
        batch.drop_constraint("fk_agent_deployment_retry", type_="foreignkey")
        batch.drop_constraint("fk_agent_deployment_job", type_="foreignkey")
        batch.drop_column("active_channel_id")
        batch.drop_column("retry_of_deployment_id")
        batch.drop_column("job_id")
