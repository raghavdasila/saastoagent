from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from backend.core.auth import current_optional_active_user
from backend.core.database import get_async_session
from backend.core.models import User
from backend.core.schemas import AppGraphRequest, AppGraphResponse
from backend.services.app_graph import app_graph_runtime

router = APIRouter(prefix="/api/app/graph", tags=["app-graph"])


@router.get("/snapshot", response_model=AppGraphResponse, deprecated=True)
async def get_app_graph_snapshot(
    node_id: str | None = None,
    saas_agent_id: uuid.UUID | None = None,
    user: User | None = Depends(current_optional_active_user),
    db: AsyncSession = Depends(get_async_session),
):
    return await app_graph_runtime.snapshot(
        request=AppGraphRequest(node_id=node_id, saas_agent_id=saas_agent_id),
        user=user,
        db=db,
    )


@router.post("/turn", response_model=AppGraphResponse, deprecated=True)
async def app_graph_turn(
    body: AppGraphRequest,
    user: User | None = Depends(current_optional_active_user),
    db: AsyncSession = Depends(get_async_session),
):
    return await app_graph_runtime.turn(request=body, user=user, db=db)


@router.post("/action", response_model=AppGraphResponse, deprecated=True)
async def app_graph_action(
    body: AppGraphRequest,
    user: User | None = Depends(current_optional_active_user),
    db: AsyncSession = Depends(get_async_session),
):
    return await app_graph_runtime.action(request=body, user=user, db=db)
