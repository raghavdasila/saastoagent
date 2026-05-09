"""Long-term memory tool — bound to active workspace at graph build time."""

from __future__ import annotations

import uuid

from langchain_core.tools import tool

_memory_service = None
_workspace_id: uuid.UUID | None = None
_session_id: uuid.UUID | None = None
_user_id: uuid.UUID | None = None


def set_memory_context(
    service,
    *,
    workspace_id: uuid.UUID,
    session_id: uuid.UUID | None = None,
    user_id: uuid.UUID | None = None,
) -> None:
    global _memory_service, _workspace_id, _session_id, _user_id
    _memory_service = service
    _workspace_id = workspace_id
    _session_id = session_id
    _user_id = user_id


@tool
async def save_memory(content: str, category: str = "fact") -> str:
    """Save a piece of information to this workspace's long-term memory.

    Use when the user asks you to remember something, or shares an
    important preference / instruction worth keeping across sessions.

    Args:
        content: Information to remember.
        category: 'fact', 'preference', or 'instruction'.
    """
    if _memory_service is None or _workspace_id is None:
        return "Memory service is not initialised for this workspace."
    if category not in ("fact", "preference", "instruction"):
        category = "fact"
    await _memory_service.save(
        content,
        workspace_id=_workspace_id,
        category=category,
        session_id=_session_id,
        user_id=_user_id,
    )
    return f"Remembered: {content} (category: {category})"


@tool
async def recall_memory(query: str, limit: int = 5) -> str:
    """Search this workspace's long-term memory for previously saved information.

    Args:
        query: What to search for.
        limit: Max memories to return (default 5).
    """
    if _memory_service is None or _workspace_id is None:
        return "Memory service is not initialised for this workspace."
    results = await _memory_service.recall(
        query, workspace_id=_workspace_id, limit=limit
    )
    if not results:
        return "No relevant memories found."
    parts = ["Retrieved memories:\n"]
    for i, m in enumerate(results, 1):
        parts.append(f"[{i}] ({m['category']}) {m['content']}")
    return "\n".join(parts)
