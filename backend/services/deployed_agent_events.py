from __future__ import annotations

import asyncio
import json
import uuid
from collections import defaultdict
from contextlib import asynccontextmanager
from typing import Any, AsyncIterator

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.core.models import AgentMessage


class DeployedAgentSessionEventBus:
    def __init__(self) -> None:
        self._subscribers: dict[uuid.UUID, set[asyncio.Queue[dict[str, Any]]]] = defaultdict(set)

    @asynccontextmanager
    async def subscribe(self, session_id: uuid.UUID) -> AsyncIterator[asyncio.Queue[dict[str, Any]]]:
        queue: asyncio.Queue[dict[str, Any]] = asyncio.Queue()
        self._subscribers[session_id].add(queue)
        try:
            yield queue
        finally:
            subscribers = self._subscribers.get(session_id)
            if subscribers is not None:
                subscribers.discard(queue)
                if not subscribers:
                    self._subscribers.pop(session_id, None)

    async def publish(self, session_id: uuid.UUID, payload: dict[str, Any]) -> None:
        for queue in list(self._subscribers.get(session_id, set())):
            await queue.put(payload)


deployed_agent_session_events = DeployedAgentSessionEventBus()


def public_agent_message_event_payload(
    *,
    message_id: str,
    session_id: str,
    content: str,
    metadata: dict[str, Any] | None = None,
) -> dict[str, Any]:
    return {
        "message_id": str(message_id),
        "session_id": str(session_id),
        "role": "assistant",
        "content": content,
    }


def encode_public_agent_message_event(payload: dict[str, Any]) -> str:
    event_id = payload.get("message_id") or ""
    return f"id: {event_id}\nevent: assistant_message\ndata: {json.dumps(payload, default=str)}\n\n"


async def public_approval_messages_after(
    *,
    session_id: uuid.UUID,
    db: AsyncSession,
    after_message_id: uuid.UUID | None = None,
) -> list[AgentMessage]:
    stmt = (
        select(AgentMessage)
        .where(
            AgentMessage.session_id == session_id,
            AgentMessage.role == "assistant",
            AgentMessage.metadata_["approval_event"].as_boolean() == True,  # noqa: E712
        )
        .order_by(AgentMessage.created_at.asc())
    )
    if after_message_id:
        cursor_message = await db.get(AgentMessage, after_message_id)
        if cursor_message is not None:
            stmt = stmt.where(AgentMessage.created_at > cursor_message.created_at)
    result = await db.execute(stmt)
    return list(result.scalars().all())


async def publish_public_agent_message(message: AgentMessage) -> None:
    payload = public_agent_message_event_payload(
        message_id=str(message.id),
        session_id=str(message.session_id),
        content=message.content,
        metadata=message.metadata_ or {},
    )
    await deployed_agent_session_events.publish(message.session_id, payload)
