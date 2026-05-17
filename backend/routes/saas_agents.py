import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.core.auth import current_active_user
from backend.core.database import get_async_session
from backend.core.models import User, SaaSAgent, SaaSAgentMember, SaaSAgentRole
from backend.core.schemas import SaaSAgentCreate, SaaSAgentRead, SaaSAgentStats
from backend.core.tenancy import create_tenant_schema
from backend.services.support.stats import get_saas_agent_stats

router = APIRouter(prefix="/api/saas-agents", tags=["saas-agents"])


@router.post("", status_code=status.HTTP_201_CREATED, response_model=SaaSAgentRead)
async def create_saas_agent(
    body: SaaSAgentCreate,
    user: User = Depends(current_active_user),
    session: AsyncSession = Depends(get_async_session),
):
    existing = await session.execute(select(SaaSAgent).where(SaaSAgent.slug == body.slug))
    if existing.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="SaaS Agent slug already taken",
        )

    saas_agent = SaaSAgent(
        id=uuid.uuid4(),
        name=body.name,
        slug=body.slug,
        created_by=user.id,
    )
    session.add(saas_agent)

    member = SaaSAgentMember(
        user_id=user.id,
        saas_agent_id=saas_agent.id,
        role=SaaSAgentRole.owner,
    )
    session.add(member)

    await session.commit()
    await session.refresh(saas_agent)
    await create_tenant_schema(saas_agent.id)

    return SaaSAgentRead(
        id=saas_agent.id,
        name=saas_agent.name,
        slug=saas_agent.slug,
        created_by=saas_agent.created_by,
        created_at=saas_agent.created_at,
        role=SaaSAgentRole.owner.value,
    )


@router.get("", response_model=list[SaaSAgentRead])
async def list_saas_agents(
    user: User = Depends(current_active_user),
    session: AsyncSession = Depends(get_async_session),
):
    stmt = (
        select(SaaSAgent, SaaSAgentMember.role)
        .join(SaaSAgentMember, SaaSAgentMember.saas_agent_id == SaaSAgent.id)
        .where(SaaSAgentMember.user_id == user.id)
        .order_by(SaaSAgent.created_at.desc())
    )
    result = await session.execute(stmt)
    rows = result.all()

    return [
        SaaSAgentRead(
            id=saas_agent.id,
            name=saas_agent.name,
            slug=saas_agent.slug,
            created_by=saas_agent.created_by,
            created_at=saas_agent.created_at,
            role=role.value,
        )
        for saas_agent, role in rows
    ]


@router.get("/{saas_agent_id}", response_model=SaaSAgentRead)
async def get_saas_agent(
    saas_agent_id: uuid.UUID,
    user: User = Depends(current_active_user),
    session: AsyncSession = Depends(get_async_session),
):
    stmt = (
        select(SaaSAgent, SaaSAgentMember.role)
        .join(SaaSAgentMember, SaaSAgentMember.saas_agent_id == SaaSAgent.id)
        .where(SaaSAgent.id == saas_agent_id, SaaSAgentMember.user_id == user.id)
    )
    result = await session.execute(stmt)
    row = result.first()
    if not row:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not a member of this SaaS Agent",
        )

    saas_agent, role = row
    return SaaSAgentRead(
        id=saas_agent.id,
        name=saas_agent.name,
        slug=saas_agent.slug,
        created_by=saas_agent.created_by,
        created_at=saas_agent.created_at,
        role=role.value,
    )


@router.get("/{saas_agent_id}/stats", response_model=SaaSAgentStats)
async def get_saas_agent_stats_route(
    saas_agent_id: uuid.UUID,
    user: User = Depends(current_active_user),
    session: AsyncSession = Depends(get_async_session),
):
    stmt = select(SaaSAgentMember).where(
        SaaSAgentMember.saas_agent_id == saas_agent_id,
        SaaSAgentMember.user_id == user.id,
    )
    result = await session.execute(stmt)
    if not result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not a member of this SaaS Agent",
        )

    stats = await get_saas_agent_stats(saas_agent_id)
    return SaaSAgentStats(**stats)
