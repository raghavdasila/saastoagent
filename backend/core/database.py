from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from backend.core.config import settings
from backend.core.models import Base

engine = create_async_engine(
    settings.database_url,
    echo=False,
    pool_pre_ping=True,
    connect_args={"prepared_statement_cache_size": 0},
)
async_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


async def create_tables():
    async with engine.begin() as conn:
        await conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
        await _migrate_workspace_columns(conn)
        await conn.run_sync(Base.metadata.create_all)


async def get_async_session():
    async with async_session() as session:
        yield session


# Alias used by agent routes for parity with foundation-agent naming.
get_db = get_async_session


async def _migrate_workspace_columns(conn) -> None:
    """Best-effort local dev migration from the pre-SaaS-Agent schema.

    This project intentionally does not have Alembic yet. The Docker dev DB can
    still contain tables created before the workspace -> SaaS Agent rename, so
    create_all alone is not enough because it never renames existing columns.
    """
    tables = [
        "connections",
        "action_nodes",
        "generated_tools",
        "connection_activation_state",
        "agent_sessions",
        "agent_messages",
        "agent_documents",
        "agent_document_chunks",
        "agent_memories",
        "workspace_members",
        "saas_agent_members",
        "qa_runs",
        "qa_artifacts",
    ]
    for table_name in tables:
        exists = (
            await conn.execute(
                text(
                    """
                    SELECT EXISTS (
                        SELECT 1 FROM information_schema.tables
                        WHERE table_schema = 'public' AND table_name = :table_name
                    )
                    """
                ),
                {"table_name": table_name},
            )
        ).scalar()
        if not exists:
            continue

        columns = set(
            (
                await conn.execute(
                    text(
                        """
                        SELECT column_name FROM information_schema.columns
                        WHERE table_schema = 'public' AND table_name = :table_name
                        """
                    ),
                    {"table_name": table_name},
                )
            ).scalars()
        )
        if "workspace_id" in columns and "saas_agent_id" not in columns:
            constraints = (
                await conn.execute(
                    text(
                        """
                        SELECT tc.constraint_name
                        FROM information_schema.table_constraints tc
                        JOIN information_schema.key_column_usage kcu
                          ON tc.constraint_name = kcu.constraint_name
                         AND tc.table_schema = kcu.table_schema
                        WHERE tc.table_schema = 'public'
                          AND tc.table_name = :table_name
                          AND tc.constraint_type = 'FOREIGN KEY'
                          AND kcu.column_name = 'workspace_id'
                        """
                    ),
                    {"table_name": table_name},
                )
            ).scalars()
            for constraint_name in constraints:
                await conn.execute(text(f'ALTER TABLE "{table_name}" DROP CONSTRAINT IF EXISTS "{constraint_name}"'))
            await conn.execute(text(f'ALTER TABLE "{table_name}" RENAME COLUMN workspace_id TO saas_agent_id'))

    table_renames = {
        "workspaces": "saas_agents",
        "workspace_members": "saas_agent_members",
    }
    for old_name, new_name in table_renames.items():
        old_exists = (
            await conn.execute(
                text(
                    """
                    SELECT EXISTS (
                        SELECT 1 FROM information_schema.tables
                        WHERE table_schema = 'public' AND table_name = :table_name
                    )
                    """
                ),
                {"table_name": old_name},
            )
        ).scalar()
        new_exists = (
            await conn.execute(
                text(
                    """
                    SELECT EXISTS (
                        SELECT 1 FROM information_schema.tables
                        WHERE table_schema = 'public' AND table_name = :table_name
                    )
                    """
                ),
                {"table_name": new_name},
            )
        ).scalar()
        if old_exists and not new_exists:
            await conn.execute(text(f'ALTER TABLE "{old_name}" RENAME TO "{new_name}"'))
