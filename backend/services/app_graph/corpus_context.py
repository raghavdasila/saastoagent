from __future__ import annotations

import uuid

from fastapi import HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.core.models import (
    ActionNode,
    AgentExecutionTrace,
    Connection,
    ConnectionActivationState,
    GeneratedTool,
    SaaSAgent,
    SaaSAgentMember,
    User,
)
from backend.core.schemas import AppGraphContextLens, AppGraphState, SaaSAgentRead
from backend.services.toolrouter import latest_ready_index, router_index_stats


class CorpusContextQueries:
    """Database-backed context and membership queries for Corpus graph runtime."""

    def __init__(self, *, node_by_id: dict[str, object]) -> None:
        self._node_by_id = node_by_id

    async def context_lens(self, state: AppGraphState, user: User | None, db: AsyncSession) -> AppGraphContextLens:
        selected = await db.get(SaaSAgent, state.active_saas_agent_id) if state.active_saas_agent_id and user else None
        connection_count = ready_connection_count = action_count = tool_count = 0
        router_summary = None
        pending_status = None
        if selected is not None:
            connection_count = int((await db.execute(select(func.count(Connection.id)).where(Connection.saas_agent_id == selected.id))).scalar_one() or 0)
            ready_connection_count = int((await db.execute(select(func.count(ConnectionActivationState.connection_id)).where(ConnectionActivationState.saas_agent_id == selected.id, ConnectionActivationState.overall_status == "ready"))).scalar_one() or 0)
            action_count = int((await db.execute(select(func.count(ActionNode.id)).where(ActionNode.saas_agent_id == selected.id))).scalar_one() or 0)
            tool_count = int((await db.execute(select(func.count(GeneratedTool.id)).where(GeneratedTool.saas_agent_id == selected.id))).scalar_one() or 0)
            router_summary = router_index_stats(await latest_ready_index(session=db, saas_agent_id=selected.id))
            if state.pending_trace_id:
                trace = await db.get(AgentExecutionTrace, state.pending_trace_id)
                pending_status = trace.status if trace else None
        node = self._node_by_id.get(state.node)
        return AppGraphContextLens(
            selected_saas_agent_id=selected.id if selected else None,
            selected_saas_agent_name=selected.name if selected else None,
            selected_saas_agent_slug=selected.slug if selected else None,
            current_node=state.node,
            working_on=getattr(node, "label", None) if node else "Recovery",
            connection_count=connection_count,
            ready_connection_count=ready_connection_count,
            action_count=action_count,
            tool_count=tool_count,
            router_index_status=router_summary.get("status") if router_summary else None,
            router_documents_count=int(router_summary.get("document_count", 0)) if router_summary else 0,
            router_endpoint_count=int(router_summary.get("endpoint_count", 0)) if router_summary else 0,
            router_version=router_summary.get("router_version") if router_summary else None,
            pending_trace_id=state.pending_trace_id,
            pending_trace_status=pending_status,
        )

    async def list_saas_agents(self, user: User | None, db: AsyncSession) -> list[SaaSAgentRead]:
        if user is None:
            return []
        result = await db.execute(select(SaaSAgent, SaaSAgentMember.role).join(SaaSAgentMember, SaaSAgentMember.saas_agent_id == SaaSAgent.id).where(SaaSAgentMember.user_id == user.id).order_by(SaaSAgent.created_at.desc()))
        return [
            SaaSAgentRead(
                id=agent.id,
                name=agent.name,
                slug=agent.slug,
                system_prompt=agent.system_prompt,
                instructions=agent.instructions,
                created_by=agent.created_by,
                created_at=agent.created_at,
                role=role.value if hasattr(role, "value") else str(role),
            )
            for agent, role in result.all()
        ]

    async def require_member(self, saas_agent_id: uuid.UUID, user: User, db: AsyncSession) -> SaaSAgentMember:
        member = (await db.execute(select(SaaSAgentMember).where(SaaSAgentMember.saas_agent_id == saas_agent_id, SaaSAgentMember.user_id == user.id))).scalar_one_or_none()
        if member is None:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not a member of this SaaS Agent")
        return member
