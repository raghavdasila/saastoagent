"""Add durable asynchronous Builder assembly lifecycle.

Revision ID: 0019_builder_assembly_lifecycle
Revises: 0018_deployment_lifecycle
"""

from alembic import op
import sqlalchemy as sa


revision = "0019_builder_assembly_lifecycle"
down_revision = "0018_deployment_lifecycle"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(
        "UPDATE agent_runnable_builds "
        "SET status = 'failed', "
        "failure_code = COALESCE(failure_code, 'builder_interrupted'), "
        "failure_message = COALESCE(failure_message, 'The earlier Agent build attempt was interrupted.') "
        "WHERE status = 'assembling'"
    )
    with op.batch_alter_table("agent_runnable_builds") as batch:
        batch.add_column(sa.Column("job_id", sa.Uuid(), nullable=True))
        batch.create_foreign_key(
            "fk_agent_runnable_build_job", "durable_jobs", ["job_id"], ["id"],
            ondelete="SET NULL",
        )
        batch.create_unique_constraint("uq_agent_runnable_build_job", ["job_id"])
        batch.create_check_constraint(
            "ck_agent_runnable_build_status",
            "status IN ('queued', 'running', 'ready', 'failed')",
        )


def downgrade() -> None:
    with op.batch_alter_table("agent_runnable_builds") as batch:
        batch.drop_constraint("ck_agent_runnable_build_status", type_="check")
        batch.drop_constraint("uq_agent_runnable_build_job", type_="unique")
        batch.drop_constraint("fk_agent_runnable_build_job", type_="foreignkey")
        batch.drop_column("job_id")
