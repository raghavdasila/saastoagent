"""Workspace-scoped long-term memory."""

from __future__ import annotations

import uuid

from openai import AsyncOpenAI
from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession

from backend.core.config import settings
from backend.core.models import AgentMemory


class MemoryService:
    def __init__(self):
        self._client: AsyncOpenAI | None = None

    @property
    def client(self) -> AsyncOpenAI:
        if self._client is None:
            self._client = AsyncOpenAI(api_key=settings.openai_api_key)
        return self._client

    async def _embed(self, content: str) -> list[float]:
        resp = await self.client.embeddings.create(
            input=[content], model=settings.embedding_model
        )
        return resp.data[0].embedding

    async def save(
        self,
        content: str,
        *,
        workspace_id: uuid.UUID,
        category: str = "fact",
        session_id: uuid.UUID | None = None,
        user_id: uuid.UUID | None = None,
        db: AsyncSession | None = None,
    ) -> AgentMemory:
        from backend.core.database import async_session as session_factory

        embedding = await self._embed(content)

        async def _do(session: AsyncSession) -> AgentMemory:
            mem = AgentMemory(
                workspace_id=workspace_id,
                session_id=session_id,
                user_id=user_id,
                content=content,
                category=category,
                embedding=embedding,
            )
            session.add(mem)
            await session.commit()
            await session.refresh(mem)
            return mem

        if db is None:
            async with session_factory() as session:
                return await _do(session)
        return await _do(db)

    async def recall(
        self,
        query: str,
        *,
        workspace_id: uuid.UUID,
        limit: int = 5,
        db: AsyncSession | None = None,
    ) -> list[dict]:
        from backend.core.database import async_session as session_factory

        embedding = await self._embed(query)
        if db is None:
            async with session_factory() as session:
                return await self._do_recall(session, workspace_id, embedding, limit)
        return await self._do_recall(db, workspace_id, embedding, limit)

    async def _do_recall(
        self,
        db: AsyncSession,
        workspace_id: uuid.UUID,
        embedding: list[float],
        limit: int,
    ) -> list[dict]:
        embedding_str = "[" + ",".join(str(x) for x in embedding) + "]"
        query = text(
            """
            SELECT id, content, category, created_at,
                   embedding <=> CAST(:embedding AS vector) AS distance
            FROM agent_memories
            WHERE embedding IS NOT NULL AND workspace_id = :workspace_id
            ORDER BY embedding <=> CAST(:embedding AS vector)
            LIMIT :limit
            """
        )
        result = await db.execute(
            query,
            {
                "embedding": embedding_str,
                "limit": limit,
                "workspace_id": str(workspace_id),
            },
        )
        rows = result.fetchall()
        return [
            {
                "id": str(row.id),
                "content": row.content,
                "category": row.category,
                "created_at": row.created_at.isoformat() if row.created_at else None,
                "score": round(1 - row.distance, 3),
            }
            for row in rows
        ]

    async def get_session_context(
        self,
        session_id: uuid.UUID,
        workspace_id: uuid.UUID,
        db: AsyncSession,
    ) -> str:
        """Return memory snippet for system-prompt injection."""
        session_q = await db.execute(
            select(AgentMemory)
            .where(
                AgentMemory.session_id == session_id,
                AgentMemory.workspace_id == workspace_id,
            )
            .order_by(AgentMemory.created_at.desc())
            .limit(10)
        )
        per_session = list(session_q.scalars().all())

        ws_q = await db.execute(
            select(AgentMemory)
            .where(
                AgentMemory.workspace_id == workspace_id,
                AgentMemory.session_id.is_(None),
            )
            .order_by(AgentMemory.created_at.desc())
            .limit(10)
        )
        per_ws = list(ws_q.scalars().all())

        all_memories = per_ws + per_session
        if not all_memories:
            return ""
        lines = ["Remembered information:"]
        for m in all_memories:
            lines.append(f"- ({m.category}) {m.content}")
        return "\n".join(lines)


memory_service = MemoryService()
