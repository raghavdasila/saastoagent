import uuid
from contextlib import asynccontextmanager

from fastapi import Depends, Header, HTTPException, status
from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession

from backend.core.auth import current_active_user
from backend.core.database import async_session, engine
from backend.core.models import User, WorkspaceMember


def tenant_schema_name(workspace_id: uuid.UUID) -> str:
    clean = str(workspace_id).replace("-", "")
    return f"tenant_{clean}"


async def create_tenant_schema(workspace_id: uuid.UUID) -> str:
    schema = tenant_schema_name(workspace_id)
    async with engine.begin() as conn:
        await conn.execute(text(f'CREATE SCHEMA IF NOT EXISTS "{schema}"'))
    return schema


@asynccontextmanager
async def open_tenant_session(workspace_id: uuid.UUID):
    schema = await create_tenant_schema(workspace_id)
    async with engine.connect() as raw_conn:
        await raw_conn.execute(text(f'SET search_path TO "{schema}", public'))
        await raw_conn.commit()
        async with AsyncSession(bind=raw_conn, expire_on_commit=False) as session:
            yield session


async def get_workspace_id(
    x_workspace_id: uuid.UUID = Header(..., alias="X-Workspace-ID"),
) -> uuid.UUID:
    return x_workspace_id


async def _resolve_workspace(
    workspace_id: uuid.UUID,
    user: User,
    session: AsyncSession,
) -> WorkspaceMember:
    stmt = select(WorkspaceMember).where(
        WorkspaceMember.workspace_id == workspace_id,
        WorkspaceMember.user_id == user.id,
    )
    result = await session.execute(stmt)
    member = result.scalar_one_or_none()
    if member is None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not a member of this workspace",
        )
    return member


async def verify_workspace_access(
    workspace_id: uuid.UUID = Depends(get_workspace_id),
    user: User = Depends(current_active_user),
) -> uuid.UUID:
    async with async_session() as membership_session:
        await _resolve_workspace(workspace_id, user, membership_session)
    return workspace_id


async def get_tenant_session(
    workspace_id: uuid.UUID = Depends(get_workspace_id),
    user: User = Depends(current_active_user),
):
    async with async_session() as membership_session:
        await _resolve_workspace(workspace_id, user, membership_session)

    async with open_tenant_session(workspace_id) as session:
        yield session
