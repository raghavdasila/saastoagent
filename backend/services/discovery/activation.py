from __future__ import annotations

from datetime import datetime, timezone
from typing import AsyncGenerator

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from backend.core.models import (
    ActivationOverallStatus,
    ActivationStepStatus,
    Connection,
    ConnectionActivationState,
)
from backend.services.discovery.engine import generate_action_nodes
from backend.services.agent.rag_service import rag_service
from backend.services.tools.generator import generate_tools_for_connection


class ActivationService:
    async def activate(
        self,
        *,
        connection_id,
        saas_agent_id,
        session: AsyncSession,
    ) -> AsyncGenerator[dict, None]:
        connection = await self._load_connection(connection_id, saas_agent_id, session)
        if connection is None:
            yield {"type": "error", "message": "Connection not found"}
            return

        state = await self._get_or_create_state(connection, session)
        state.overall_status = ActivationOverallStatus.running.value
        state.current_step = "generate"
        state.started_at = datetime.now(timezone.utc)
        state.completed_at = None
        state.blocked_reason = None
        state.generate_status = ActivationStepStatus.running.value
        state.embed_status = ActivationStepStatus.skipped.value
        state.tools_status = ActivationStepStatus.pending.value
        await session.commit()
        yield {"type": "step", "step": "generate", "status": "running", "message": "Reading the OpenAPI spec"}

        try:
            generate_counts = await generate_action_nodes(connection, session)
            state.generate_status = ActivationStepStatus.succeeded.value
            await session.commit()
            yield {"type": "step", "step": "generate", "status": "done", **generate_counts}

            yield {
                "type": "step",
                "step": "embed",
                "status": "skipped",
                "message": "Semantic embeddings are deferred for this setup slice",
            }

            state.current_step = "tools"
            state.tools_status = ActivationStepStatus.running.value
            await session.commit()
            yield {"type": "step", "step": "tools", "status": "running", "message": "Generating callable tools"}

            tool_counts = await generate_tools_for_connection(connection.id, saas_agent_id, session)
            state.tools_status = ActivationStepStatus.succeeded.value
            state.current_step = None
            state.overall_status = ActivationOverallStatus.ready.value
            state.completed_at = datetime.now(timezone.utc)
            await session.commit()
            yield {"type": "step", "step": "tools", "status": "done", **tool_counts}
            yield {"type": "step", "step": "rag", "status": "running", "message": "Generating catalog retrieval knowledge"}
            rag_counts = await rag_service.ingest_generated_knowledge(saas_agent_id=saas_agent_id, db=session)
            yield {"type": "step", "step": "rag", "status": "done", **rag_counts}
            yield {
                "type": "complete",
                "status": "activated",
                "overall_status": state.overall_status,
                "connection_id": str(connection.id),
                "action_nodes_count": generate_counts.get("new", 0)
                + generate_counts.get("updated", 0)
                + generate_counts.get("unchanged", 0),
                "tools_count": tool_counts["total"],
                "rag_chunks_count": rag_counts["chunks"],
            }
        except Exception as exc:
            state.current_step = None
            state.overall_status = ActivationOverallStatus.blocked.value
            state.blocked_reason = str(exc)
            if state.generate_status == ActivationStepStatus.running.value:
                state.generate_status = ActivationStepStatus.failed.value
            elif state.tools_status == ActivationStepStatus.running.value:
                state.tools_status = ActivationStepStatus.failed.value
            await session.commit()
            yield {"type": "error", "message": str(exc)}

    async def _load_connection(self, connection_id, saas_agent_id, session: AsyncSession) -> Connection | None:
        result = await session.execute(
            select(Connection)
            .options(selectinload(Connection.credentials))
            .where(Connection.id == connection_id, Connection.saas_agent_id == saas_agent_id)
        )
        return result.scalar_one_or_none()

    async def _get_or_create_state(
        self,
        connection: Connection,
        session: AsyncSession,
    ) -> ConnectionActivationState:
        result = await session.execute(
            select(ConnectionActivationState).where(ConnectionActivationState.connection_id == connection.id)
        )
        state = result.scalar_one_or_none()
        if state is not None:
            return state
        state = ConnectionActivationState(
            connection_id=connection.id,
            saas_agent_id=connection.saas_agent_id,
        )
        session.add(state)
        await session.flush()
        return state
