from __future__ import annotations

import uuid
from collections.abc import Mapping
from typing import Any

from fastapi import HTTPException, status
from sqlalchemy import select

from backend.core.models import SaaSAgent, SaaSAgentMember, SaaSAgentRole
from backend.core.schemas import CorpusGraphState, EntryGraphMessage
from backend.core.tenancy import create_tenant_schema
from backend.services.corpus.manifest import CorpusActionIds, CorpusNodeIds

from .types import CorpusActionContext, CorpusActionResult


async def open_saas_agent(state: CorpusGraphState, payload: Mapping[str, Any], context: CorpusActionContext) -> CorpusActionResult:
    if context.user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Authentication required")
    raw_id = payload.get("saas_agent_id") or state.active_saas_agent_id
    if not raw_id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="saas_agent_id is required")
    state.active_saas_agent_id = uuid.UUID(str(raw_id))
    await context.queries.require_member(state.active_saas_agent_id, context.user, context.db)
    state.node = CorpusNodeIds.AGENT_HOME
    return CorpusActionResult(
        state=state,
        messages=[EntryGraphMessage(content="I opened that SaaS Agent.")],
        evidence=[{"type": "saas_agent_selected", "saas_agent_id": str(state.active_saas_agent_id)}],
    )


async def create_saas_agent(state: CorpusGraphState, payload: Mapping[str, Any], context: CorpusActionContext) -> CorpusActionResult:
    if context.user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Authentication required")
    name = str(payload.get("name") or "").strip()
    slug = str(payload.get("slug") or "").strip()
    if not name or not slug:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="name and slug are required")
    if (await context.db.execute(select(SaaSAgent).where(SaaSAgent.slug == slug))).scalar_one_or_none():
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="SaaS Agent slug already taken")
    agent = SaaSAgent(id=uuid.uuid4(), name=name, slug=slug, created_by=context.user.id)
    context.db.add(agent)
    context.db.add(SaaSAgentMember(user_id=context.user.id, saas_agent_id=agent.id, role=SaaSAgentRole.owner))
    await context.db.commit()
    await context.db.refresh(agent)
    await create_tenant_schema(agent.id)
    state.active_saas_agent_id = agent.id
    state.node = CorpusNodeIds.AGENT_HOME
    return CorpusActionResult(
        state=state,
        messages=[EntryGraphMessage(content=f"Created {agent.name}. Next we can connect its API.")],
        evidence=[{"type": "saas_agent_created", "saas_agent_id": str(agent.id)}],
    )


async def navigate_agent_home(state: CorpusGraphState, payload: Mapping[str, Any], context: CorpusActionContext) -> CorpusActionResult:
    state.node = CorpusNodeIds.AGENT_HOME
    return CorpusActionResult(state=state)


def build_agent_handlers():
    return {
        CorpusActionIds.SAAS_AGENT_OPEN: open_saas_agent,
        CorpusActionIds.SAAS_AGENT_CREATE: create_saas_agent,
        CorpusActionIds.AGENT_HOME: navigate_agent_home,
    }
