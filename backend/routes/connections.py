from __future__ import annotations

import json
import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.core.auth import current_active_user
from backend.core.credentials import encrypt_value
from backend.core.database import get_async_session
from backend.core.models import (
    ActionNode,
    AuthType,
    Connection,
    ConnectionActivationState,
    ConnectionType,
    EncryptedCredential,
    GeneratedTool,
    User,
    WorkspaceMember,
)
from backend.core.schemas import (
    ActionCatalogRead,
    ActionNodeRead,
    ActivationStateRead,
    ConnectionCreate,
    ConnectionPreviewRead,
    ConnectionPreviewRequest,
    ConnectionRead,
    EntityRead,
    ToolRead,
)
from backend.services.catalog import (
    infer_entities,
    list_workspace_actions,
    list_workspace_tools,
    preview_openapi_spec,
    workspace_catalog,
)
from backend.services.discovery.activation import ActivationService
from backend.providers import AdapterRegistry

router = APIRouter(prefix="/api/workspaces/{workspace_id}", tags=["connections"])


async def _require_member(workspace_id: uuid.UUID, user: User, db: AsyncSession) -> None:
    result = await db.execute(
        select(WorkspaceMember).where(
            WorkspaceMember.workspace_id == workspace_id,
            WorkspaceMember.user_id == user.id,
        )
    )
    if result.scalar_one_or_none() is None:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not a member of this workspace")


@router.get("/providers")
async def list_workspace_providers(
    workspace_id: uuid.UUID,
    user: User = Depends(current_active_user),
    db: AsyncSession = Depends(get_async_session),
):
    await _require_member(workspace_id, user, db)
    return AdapterRegistry.get_provider_catalog()


@router.post("/connections/preview", response_model=ConnectionPreviewRead)
async def preview_connection(
    workspace_id: uuid.UUID,
    body: ConnectionPreviewRequest,
    user: User = Depends(current_active_user),
    db: AsyncSession = Depends(get_async_session),
):
    await _require_member(workspace_id, user, db)
    try:
        return await preview_openapi_spec(spec_url=body.spec_url, raw_spec=body.raw_spec)
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get("/catalog", response_model=ActionCatalogRead)
async def get_workspace_catalog(
    workspace_id: uuid.UUID,
    user: User = Depends(current_active_user),
    db: AsyncSession = Depends(get_async_session),
):
    await _require_member(workspace_id, user, db)
    return await workspace_catalog(db, workspace_id)


@router.get("/actions", response_model=list[ActionNodeRead])
async def list_workspace_actions_route(
    workspace_id: uuid.UUID,
    user: User = Depends(current_active_user),
    db: AsyncSession = Depends(get_async_session),
):
    await _require_member(workspace_id, user, db)
    return await list_workspace_actions(db, workspace_id)


@router.get("/tools", response_model=list[ToolRead])
async def list_workspace_tools_route(
    workspace_id: uuid.UUID,
    user: User = Depends(current_active_user),
    db: AsyncSession = Depends(get_async_session),
):
    await _require_member(workspace_id, user, db)
    return await list_workspace_tools(db, workspace_id)


@router.get("/entities", response_model=list[EntityRead])
async def list_workspace_entities(
    workspace_id: uuid.UUID,
    user: User = Depends(current_active_user),
    db: AsyncSession = Depends(get_async_session),
):
    await _require_member(workspace_id, user, db)
    actions = await list_workspace_actions(db, workspace_id)
    return infer_entities(actions)


def _activation_steps(state: ConnectionActivationState | None) -> dict | None:
    if state is None:
        return None
    return {
        "generate": {"status": state.generate_status},
        "embed": {"status": state.embed_status},
        "tools": {"status": state.tools_status},
    }


async def _connection_counts(db: AsyncSession, connection_id: uuid.UUID) -> tuple[int, int]:
    action_count = (await db.execute(select(func.count(ActionNode.id)).where(ActionNode.connection_id == connection_id))).scalar_one()
    tool_count = (await db.execute(select(func.count(GeneratedTool.id)).where(GeneratedTool.connection_id == connection_id))).scalar_one()
    return int(action_count), int(tool_count)


async def _to_read(db: AsyncSession, connection: Connection) -> ConnectionRead:
    action_count, tool_count = await _connection_counts(db, connection.id)
    state = connection.activation_state
    return ConnectionRead(
        id=connection.id,
        workspace_id=connection.workspace_id,
        name=connection.name,
        type=connection.type.value if hasattr(connection.type, "value") else connection.type,
        provider=connection.provider,
        config=connection.config or {},
        auth_type=connection.auth_type.value if connection.auth_type and hasattr(connection.auth_type, "value") else connection.auth_type,
        has_credentials=bool(connection.credentials),
        action_nodes_count=action_count,
        tools_count=tool_count,
        activation_status=state.overall_status if state else None,
        activation_steps=_activation_steps(state),
        created_at=connection.created_at,
        updated_at=connection.updated_at,
    )


@router.post("/connections", status_code=status.HTTP_201_CREATED, response_model=ConnectionRead)
async def create_connection(
    workspace_id: uuid.UUID,
    body: ConnectionCreate,
    user: User = Depends(current_active_user),
    db: AsyncSession = Depends(get_async_session),
):
    await _require_member(workspace_id, user, db)
    auth_type = body.auth_type or body.config.get("auth_type") or "none"
    connection = Connection(
        workspace_id=workspace_id,
        name=body.name,
        type=ConnectionType.rest_api,
        provider=body.provider or "rest_api",
        config=body.config,
        auth_type=AuthType(auth_type),
    )
    db.add(connection)
    await db.flush()

    credentials = body.credentials or {}
    credential_value = credentials.get("credential_value")
    if credential_value:
        db.add(
            EncryptedCredential(
                connection_id=connection.id,
                credential_type="credential_value",
                encrypted_value=encrypt_value(credential_value),
                metadata_={
                    key: value
                    for key, value in credentials.items()
                    if key in {"header_name", "query_param_name", "token_url"} and value
                },
            )
        )
    db.add(ConnectionActivationState(connection_id=connection.id, workspace_id=workspace_id))
    await db.commit()
    await db.refresh(connection, attribute_names=["credentials", "activation_state"])
    return await _to_read(db, connection)


@router.get("/connections", response_model=list[ConnectionRead])
async def list_connections(
    workspace_id: uuid.UUID,
    user: User = Depends(current_active_user),
    db: AsyncSession = Depends(get_async_session),
):
    await _require_member(workspace_id, user, db)
    result = await db.execute(
        select(Connection).where(Connection.workspace_id == workspace_id).order_by(Connection.created_at.desc())
    )
    return [await _to_read(db, connection) for connection in result.scalars().all()]


@router.post("/connections/{connection_id}/activate")
async def activate_connection(
    workspace_id: uuid.UUID,
    connection_id: uuid.UUID,
    user: User = Depends(current_active_user),
    db: AsyncSession = Depends(get_async_session),
):
    await _require_member(workspace_id, user, db)
    service = ActivationService()

    async def generate():
        async for event in service.activate(connection_id=connection_id, workspace_id=workspace_id, session=db):
            yield f"event: {event['type']}\ndata: {json.dumps(event, default=str)}\n\n"

    return StreamingResponse(
        generate(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "Connection": "keep-alive", "X-Accel-Buffering": "no"},
    )


@router.get("/connections/{connection_id}/activation-state", response_model=ActivationStateRead)
async def get_activation_state(
    workspace_id: uuid.UUID,
    connection_id: uuid.UUID,
    user: User = Depends(current_active_user),
    db: AsyncSession = Depends(get_async_session),
):
    await _require_member(workspace_id, user, db)
    result = await db.execute(
        select(ConnectionActivationState).where(
            ConnectionActivationState.workspace_id == workspace_id,
            ConnectionActivationState.connection_id == connection_id,
        )
    )
    state = result.scalar_one_or_none()
    if state is None:
        raise HTTPException(status_code=404, detail="Activation state not found")
    return ActivationStateRead(
        connection_id=state.connection_id,
        workspace_id=state.workspace_id,
        overall_status=state.overall_status,
        steps=_activation_steps(state) or {},
        current_step=state.current_step,
        blocked_reason=state.blocked_reason,
        started_at=state.started_at,
        completed_at=state.completed_at,
        updated_at=state.updated_at,
    )


@router.get("/connections/{connection_id}/action-nodes", response_model=list[ActionNodeRead])
async def list_action_nodes(
    workspace_id: uuid.UUID,
    connection_id: uuid.UUID,
    user: User = Depends(current_active_user),
    db: AsyncSession = Depends(get_async_session),
):
    await _require_member(workspace_id, user, db)
    result = await db.execute(
        select(ActionNode)
        .where(ActionNode.workspace_id == workspace_id, ActionNode.connection_id == connection_id)
        .order_by(ActionNode.source_index)
    )
    return [ActionNodeRead.model_validate(node, from_attributes=True) for node in result.scalars().all()]


@router.get("/connections/{connection_id}/tools", response_model=list[ToolRead])
async def list_tools(
    workspace_id: uuid.UUID,
    connection_id: uuid.UUID,
    user: User = Depends(current_active_user),
    db: AsyncSession = Depends(get_async_session),
):
    await _require_member(workspace_id, user, db)
    result = await db.execute(
        select(GeneratedTool)
        .where(GeneratedTool.workspace_id == workspace_id, GeneratedTool.connection_id == connection_id)
        .order_by(GeneratedTool.name)
    )
    return [ToolRead.model_validate(tool, from_attributes=True) for tool in result.scalars().all()]
