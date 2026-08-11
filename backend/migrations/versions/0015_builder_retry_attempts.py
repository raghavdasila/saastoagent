"""Retain every explicit Agent build retry as a durable attempt.

Revision ID: 0015_builder_retry_attempts
Revises: 0014_evaluation_authoring_lifecycle
"""

from alembic import op
import sqlalchemy as sa


revision = "0015_builder_retry_attempts"
down_revision = "0014_evaluation_authoring_lifecycle"
branch_labels = None
depends_on = None


def upgrade() -> None:
    with op.batch_alter_table("agent_runnable_builds") as batch:
        batch.add_column(
            sa.Column(
                "attempt_number",
                sa.Integer(),
                nullable=False,
                server_default="1",
            )
        )
        batch.drop_constraint("uq_runnable_build_request", type_="unique")
        batch.create_unique_constraint(
            "uq_runnable_build_request_attempt",
            ["organization_id", "build_request_id", "attempt_number"],
        )


def downgrade() -> None:
    # Downgrade is intentionally fail-closed if multiple retained attempts now
    # exist for one request; collapsing them would destroy failure history.
    connection = op.get_bind()
    duplicates = connection.execute(sa.text(
        "SELECT organization_id, build_request_id FROM agent_runnable_builds "
        "GROUP BY organization_id, build_request_id HAVING COUNT(*) > 1 LIMIT 1"
    )).first()
    if duplicates is not None:
        raise RuntimeError(
            "Cannot downgrade while a build request has retained retry attempts."
        )
    with op.batch_alter_table("agent_runnable_builds") as batch:
        batch.drop_constraint(
            "uq_runnable_build_request_attempt", type_="unique"
        )
        batch.create_unique_constraint(
            "uq_runnable_build_request",
            ["organization_id", "build_request_id"],
        )
        batch.drop_column("attempt_number")
