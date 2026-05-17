import uuid
from contextlib import asynccontextmanager

from fastapi import Depends, Header, HTTPException, status
from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession

from backend.core.auth import current_active_user
from backend.core.database import async_session, engine
from backend.core.models import User, SaaSAgentMember


def tenant_schema_name(saas_agent_id: uuid.UUID) -> str:
    clean = str(saas_agent_id).replace("-", "")
    return f"tenant_{clean}"


async def create_tenant_schema(saas_agent_id: uuid.UUID) -> str:
    schema = tenant_schema_name(saas_agent_id)
    async with engine.begin() as conn:
        await conn.execute(text(f'CREATE SCHEMA IF NOT EXISTS "{schema}"'))
    return schema


@asynccontextmanager
async def open_tenant_session(saas_agent_id: uuid.UUID):
    schema = await create_tenant_schema(saas_agent_id)
    async with engine.connect() as raw_conn:
        await raw_conn.execute(text(f'SET search_path TO "{schema}", public'))
        await raw_conn.commit()
        async with AsyncSession(bind=raw_conn, expire_on_commit=False) as session:
            yield session


async def get_saas_agent_id(
    x_saas_agent_id: uuid.UUID = Header(..., alias="X-SaaSAgent-ID"),
) -> uuid.UUID:
    return x_saas_agent_id


async def _resolve_SaaSAgent(
    saas_agent_id: uuid.UUID,
    user: User,
    session: AsyncSession,
) -> SaaSAgentMember:
    stmt = select(SaaSAgentMember).where(
        SaaSAgentMember.saas_agent_id == saas_agent_id,
        SaaSAgentMember.user_id == user.id,
    )
    result = await session.execute(stmt)
    member = result.scalar_one_or_none()
    if member is None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not a member of this SaaS Agent",
        )
    return member


async def verify_SaaSAgent_access(
    saas_agent_id: uuid.UUID = Depends(get_saas_agent_id),
    user: User = Depends(current_active_user),
) -> uuid.UUID:
    async with async_session() as membership_session:
        await _resolve_SaaSAgent(saas_agent_id, user, membership_session)
    return saas_agent_id


async def get_tenant_session(
    saas_agent_id: uuid.UUID = Depends(get_saas_agent_id),
    user: User = Depends(current_active_user),
):
    async with async_session() as membership_session:
        await _resolve_SaaSAgent(saas_agent_id, user, membership_session)

    async with open_tenant_session(saas_agent_id) as session:
        yield session
