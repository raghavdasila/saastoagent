import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.core.auth import current_active_user
from backend.core.database import get_async_session
from backend.core.models import User, Workspace, WorkspaceMember, WorkspaceRole
from backend.core.schemas import WorkspaceCreate, WorkspaceRead, WorkspaceStats
from backend.core.tenancy import create_tenant_schema
from backend.services.support.stats import get_workspace_stats

router = APIRouter(prefix="/api/workspaces", tags=["workspaces"])


@router.post("", status_code=status.HTTP_201_CREATED, response_model=WorkspaceRead)
async def create_workspace(
    body: WorkspaceCreate,
    user: User = Depends(current_active_user),
    session: AsyncSession = Depends(get_async_session),
):
    existing = await session.execute(select(Workspace).where(Workspace.slug == body.slug))
    if existing.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Workspace slug already taken",
        )

    workspace = Workspace(
        id=uuid.uuid4(),
        name=body.name,
        slug=body.slug,
        created_by=user.id,
    )
    session.add(workspace)

    member = WorkspaceMember(
        user_id=user.id,
        workspace_id=workspace.id,
        role=WorkspaceRole.owner,
    )
    session.add(member)

    await session.commit()
    await session.refresh(workspace)
    await create_tenant_schema(workspace.id)

    return WorkspaceRead(
        id=workspace.id,
        name=workspace.name,
        slug=workspace.slug,
        created_by=workspace.created_by,
        created_at=workspace.created_at,
        role=WorkspaceRole.owner.value,
    )


@router.get("", response_model=list[WorkspaceRead])
async def list_workspaces(
    user: User = Depends(current_active_user),
    session: AsyncSession = Depends(get_async_session),
):
    stmt = (
        select(Workspace, WorkspaceMember.role)
        .join(WorkspaceMember, WorkspaceMember.workspace_id == Workspace.id)
        .where(WorkspaceMember.user_id == user.id)
        .order_by(Workspace.created_at.desc())
    )
    result = await session.execute(stmt)
    rows = result.all()

    return [
        WorkspaceRead(
            id=workspace.id,
            name=workspace.name,
            slug=workspace.slug,
            created_by=workspace.created_by,
            created_at=workspace.created_at,
            role=role.value,
        )
        for workspace, role in rows
    ]


@router.get("/{workspace_id}", response_model=WorkspaceRead)
async def get_workspace(
    workspace_id: uuid.UUID,
    user: User = Depends(current_active_user),
    session: AsyncSession = Depends(get_async_session),
):
    stmt = (
        select(Workspace, WorkspaceMember.role)
        .join(WorkspaceMember, WorkspaceMember.workspace_id == Workspace.id)
        .where(Workspace.id == workspace_id, WorkspaceMember.user_id == user.id)
    )
    result = await session.execute(stmt)
    row = result.first()
    if not row:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not a member of this workspace",
        )

    workspace, role = row
    return WorkspaceRead(
        id=workspace.id,
        name=workspace.name,
        slug=workspace.slug,
        created_by=workspace.created_by,
        created_at=workspace.created_at,
        role=role.value,
    )


@router.get("/{workspace_id}/stats", response_model=WorkspaceStats)
async def get_workspace_stats_route(
    workspace_id: uuid.UUID,
    user: User = Depends(current_active_user),
    session: AsyncSession = Depends(get_async_session),
):
    stmt = select(WorkspaceMember).where(
        WorkspaceMember.workspace_id == workspace_id,
        WorkspaceMember.user_id == user.id,
    )
    result = await session.execute(stmt)
    if not result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not a member of this workspace",
        )

    stats = await get_workspace_stats(workspace_id)
    return WorkspaceStats(**stats)
