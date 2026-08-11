"""Add durable generated-evalset and revisioned case authoring truth.

Revision ID: 0014_evaluation_authoring_lifecycle
Revises: 0013_builder_runtime_lifecycle
"""

from alembic import op
import sqlalchemy as sa


revision = "0014_evaluation_authoring_lifecycle"
down_revision = "0013_builder_runtime_lifecycle"
branch_labels = None
depends_on = None


def upgrade() -> None:
    with op.batch_alter_table("agent_evaluation_sets") as batch:
        batch.add_column(sa.Column("generation_job_id", sa.Uuid(), nullable=True))
        batch.add_column(sa.Column("generation_status", sa.String(24), nullable=False, server_default="manual"))
        batch.add_column(sa.Column("generation_failure_code", sa.String(80), nullable=True))
        batch.add_column(sa.Column("generation_failure_message", sa.String(500), nullable=True))
        batch.add_column(sa.Column("generation_summary", sa.JSON(), nullable=True))
        batch.create_foreign_key(
            "fk_agent_evaluation_sets_generation_job",
            "durable_jobs",
            ["generation_job_id"],
            ["id"],
            ondelete="SET NULL",
        )
    with op.batch_alter_table("agent_evaluation_cases") as batch:
        batch.alter_column("runtime_case_id", existing_type=sa.String(64), nullable=True)
        batch.add_column(sa.Column("generation_task_id", sa.String(120), nullable=True))
        batch.add_column(sa.Column("current_revision", sa.Integer(), nullable=False, server_default="1"))
        batch.add_column(sa.Column("removed_at", sa.DateTime(timezone=True), nullable=True))
    with op.batch_alter_table("agent_evaluation_runs") as batch:
        batch.add_column(sa.Column("case_revision", sa.Integer(), nullable=False, server_default="1"))
    op.create_table(
        "agent_evaluation_case_revisions",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("organization_id", sa.Uuid(), nullable=False),
        sa.Column("case_id", sa.Uuid(), nullable=False),
        sa.Column("revision", sa.Integer(), nullable=False),
        sa.Column("title", sa.String(160), nullable=False),
        sa.Column("category", sa.String(80), nullable=False),
        sa.Column("difficulty", sa.String(24), nullable=False),
        sa.Column("mandatory", sa.Boolean(), nullable=False),
        sa.Column("changed_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["case_id"], ["agent_evaluation_cases.id"], ondelete="RESTRICT"),
        sa.UniqueConstraint("case_id", "revision", name="uq_agent_evaluation_case_revision"),
    )


def downgrade() -> None:
    op.drop_table("agent_evaluation_case_revisions")
    with op.batch_alter_table("agent_evaluation_runs") as batch:
        batch.drop_column("case_revision")
    with op.batch_alter_table("agent_evaluation_cases") as batch:
        batch.drop_column("removed_at")
        batch.drop_column("current_revision")
        batch.drop_column("generation_task_id")
        batch.alter_column("runtime_case_id", existing_type=sa.String(64), nullable=False)
    with op.batch_alter_table("agent_evaluation_sets") as batch:
        batch.drop_constraint("fk_agent_evaluation_sets_generation_job", type_="foreignkey")
        batch.drop_column("generation_summary")
        batch.drop_column("generation_failure_message")
        batch.drop_column("generation_failure_code")
        batch.drop_column("generation_status")
        batch.drop_column("generation_job_id")
