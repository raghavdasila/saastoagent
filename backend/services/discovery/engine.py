from __future__ import annotations

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.core.models import ActionNode, ActionNodeStatus, Connection
from backend.providers import AdapterRegistry


async def generate_action_nodes(connection: Connection, session: AsyncSession) -> dict[str, int]:
    adapter_cls = AdapterRegistry.get(connection.provider or "rest_api")
    adapter = adapter_cls()
    nodes_data = await adapter.discover(connection, session)
    counts = await _persist_action_nodes(
        connection,
        session,
        nodes_data,
        source_type=adapter_cls.source_type(),
    )
    connection.last_generated_at = func.now()
    await session.commit()
    return counts


async def _persist_action_nodes(
    connection: Connection,
    session: AsyncSession,
    nodes_data: list[dict],
    *,
    source_type: str,
) -> dict[str, int]:
    existing_result = await session.execute(
        select(ActionNode).where(ActionNode.connection_id == connection.id)
    )
    existing = {(node.path, node.method): node for node in existing_result.scalars().all()}
    seen: set[tuple[str, str]] = set()
    counts = {"new": 0, "updated": 0, "unchanged": 0, "removed": 0}

    compare_fields = (
        "name",
        "description",
        "parameters",
        "request_body",
        "responses",
        "security",
        "tags",
        "embedding_text",
        "risk_level",
        "source_index",
    )

    for data in nodes_data:
        key = (data["path"], data["method"])
        seen.add(key)
        node = existing.get(key)
        if node is None:
            session.add(
                ActionNode(
                    **data,
                    source_type=source_type,
                    status=ActionNodeStatus.discovered,
                )
            )
            counts["new"] += 1
            continue

        changed = any(getattr(node, field) != data.get(field) for field in compare_fields if field in data)
        if changed:
            for field in compare_fields:
                if field in data:
                    setattr(node, field, data[field])
            node.status = ActionNodeStatus.discovered
            node.source_type = source_type
            counts["updated"] += 1
        else:
            counts["unchanged"] += 1

    for key, node in existing.items():
        if key not in seen and node.status != ActionNodeStatus.deprecated:
            node.status = ActionNodeStatus.deprecated
            counts["removed"] += 1

    return counts
