import uuid


async def get_workspace_stats(workspace_id: uuid.UUID) -> dict:
    _ = workspace_id
    return {
        "connections_count": 0,
        "tools_count": 0,
        "learnings_count": 0,
        "active_learnings_count": 0,
        "systems_count": 1,
        "connections_with_learnings": 0,
        "tools_with_learnings": 0,
        "avg_confidence": 0.0,
        "maturity": 0.0,
    }
