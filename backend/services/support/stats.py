import uuid

from sqlalchemy import func, select

from backend.core.database import async_session
from backend.core.models import Connection, GeneratedTool


async def get_saas_agent_stats(saas_agent_id: uuid.UUID) -> dict:
    async with async_session() as session:
        connections_count = (
            await session.execute(
                select(func.count(Connection.id)).where(Connection.saas_agent_id == saas_agent_id)
            )
        ).scalar_one()
        tools_count = (
            await session.execute(
                select(func.count(GeneratedTool.id)).where(GeneratedTool.saas_agent_id == saas_agent_id)
            )
        ).scalar_one()
    return {
        "connections_count": int(connections_count),
        "tools_count": int(tools_count),
        "learnings_count": 0,
        "active_learnings_count": 0,
        "systems_count": 1,
        "connections_with_learnings": 0,
        "tools_with_learnings": 0,
        "avg_confidence": 0.0,
        "maturity": 0.0,
    }
