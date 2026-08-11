"""Add the durable paused state to draft Agent runtimes.

Revision ID: 0016_builder_pause_lifecycle
Revises: 0015_builder_retry_attempts
"""

from alembic import op


revision = "0016_builder_pause_lifecycle"
down_revision = "0015_builder_retry_attempts"
branch_labels = None
depends_on = None


def upgrade() -> None:
    with op.batch_alter_table("agent_runnable_builds") as batch:
        batch.drop_constraint(
            "ck_runnable_build_runtime_lifecycle", type_="check"
        )
        batch.create_check_constraint(
            "ck_runnable_build_runtime_lifecycle",
            "runtime_lifecycle IN ('stopped', 'running', 'paused', 'removed')",
        )


def downgrade() -> None:
    # Downgrade is fail-closed because mapping paused runtimes to another state
    # would silently change the owner's explicit lifecycle decision.
    connection = op.get_bind()
    paused = connection.exec_driver_sql(
        "SELECT id FROM agent_runnable_builds "
        "WHERE runtime_lifecycle = 'paused' LIMIT 1"
    ).first()
    if paused is not None:
        raise RuntimeError(
            "Cannot downgrade while an Agent build runtime is paused."
        )
    with op.batch_alter_table("agent_runnable_builds") as batch:
        batch.drop_constraint(
            "ck_runnable_build_runtime_lifecycle", type_="check"
        )
        batch.create_check_constraint(
            "ck_runnable_build_runtime_lifecycle",
            "runtime_lifecycle IN ('stopped', 'running', 'removed')",
        )
