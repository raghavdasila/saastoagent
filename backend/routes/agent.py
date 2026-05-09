"""Workspace-scoped agent endpoints.

All routes live under `/api/workspaces/{workspace_id}/agent/...` and require
that the requesting user is a member of the workspace. Admin endpoints
additionally require `owner` or `admin` role.
"""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException, Request, UploadFile, status
from fastapi.responses import StreamingResponse
from sqlalchemy import delete, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.core.auth import current_active_user, current_optional_active_user
from backend.core.config import settings
from backend.core.database import get_async_session
from backend.core.models import (
    AgentDocument,
    AgentDocumentChunk,
    AgentMemory,
    AgentMessage,
    AgentSession,
    User,
    Workspace,
    WorkspaceMember,
    WorkspaceRole,
)
from backend.core.schemas import (
    AgentAdminStats,
    AgentDocumentChunkRead,
    AgentDocumentRead,
    AgentMemoryRead,
    AgentMessageRead,
    AgentSessionList,
    AgentSessionRead,
    ChatRequest,
)
from backend.services.agent.chat_service import chat_service
from backend.services.agent.anonymous_rate_limit import anonymous_chat_rate_limiter
from backend.services.agent.rag_service import rag_service

router = APIRouter(prefix="/api/workspaces/{workspace_id}/agent", tags=["agent"])

ALLOWED_TYPES = {
    "application/pdf",
    "text/plain",
    "text/markdown",
    "text/csv",
    "application/csv",
    "application/octet-stream",
}
ALLOWED_EXTS = {"pdf", "txt", "md", "csv", "markdown", "text"}
MAX_FILE_SIZE = 50 * 1024 * 1024  # 50 MB


def _client_ip(request: Request) -> str:
    forwarded_for = request.headers.get("x-forwarded-for")
    if forwarded_for:
        return forwarded_for.split(",", 1)[0].strip()
    if request.client and request.client.host:
        return request.client.host
    return "unknown"


# ── Membership helpers ─────────────────────────────────────────────


async def _require_member(
    workspace_id: uuid.UUID,
    user: User,
    db: AsyncSession,
) -> WorkspaceMember:
    res = await db.execute(
        select(WorkspaceMember).where(
            WorkspaceMember.workspace_id == workspace_id,
            WorkspaceMember.user_id == user.id,
        )
    )
    member = res.scalar_one_or_none()
    if member is None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not a member of this workspace",
        )
    return member


async def _require_admin(
    workspace_id: uuid.UUID,
    user: User,
    db: AsyncSession,
) -> WorkspaceMember:
    member = await _require_member(workspace_id, user, db)
    if member.role not in (WorkspaceRole.owner, WorkspaceRole.admin):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Workspace admin role required",
        )
    return member


# ── Chat (SSE) ─────────────────────────────────────────────────────


@router.post("/chat")
async def agent_chat(
    workspace_id: uuid.UUID,
    body: ChatRequest,
    request: Request,
    user: User | None = Depends(current_optional_active_user),
    db: AsyncSession = Depends(get_async_session),
):
    if user is not None:
        await _require_member(workspace_id, user, db)
    else:
        workspace = await db.get(Workspace, workspace_id)
        if workspace is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Workspace not found")
        rate = anonymous_chat_rate_limiter.check(
            _client_ip(request),
            limit=settings.anonymous_chat_messages_per_hour,
            window_seconds=settings.anonymous_chat_rate_limit_window_seconds,
        )
        if not rate.allowed:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail=f"Anonymous chat limit reached. Try again in {rate.reset_seconds} seconds.",
                headers={"Retry-After": str(rate.reset_seconds)},
            )

    async def generate():
        async for event in chat_service.run(
            message=body.message,
            workspace_id=workspace_id,
            user_id=user.id if user else None,
            session_id=body.session_id,
            reasoning_mode=body.reasoning_mode,
            handoff_context=body.handoff_context,
            db=db,
        ):
            yield event

    return StreamingResponse(
        generate(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


# ── Sessions ───────────────────────────────────────────────────────


@router.get("/sessions", response_model=AgentSessionList)
async def list_sessions(
    workspace_id: uuid.UUID,
    user: User = Depends(current_active_user),
    db: AsyncSession = Depends(get_async_session),
):
    await _require_member(workspace_id, user, db)
    stmt = (
        select(AgentSession, func.count(AgentMessage.id).label("message_count"))
        .outerjoin(AgentMessage, AgentMessage.session_id == AgentSession.id)
        .where(AgentSession.workspace_id == workspace_id)
        .group_by(AgentSession.id)
        .order_by(AgentSession.updated_at.desc())
    )
    rows = (await db.execute(stmt)).all()
    sessions = [
        AgentSessionRead(
            id=s.id,
            workspace_id=s.workspace_id,
            user_id=s.user_id,
            title=s.title,
            created_at=s.created_at,
            updated_at=s.updated_at,
            message_count=count,
        )
        for s, count in rows
    ]
    return AgentSessionList(sessions=sessions, total=len(sessions))


@router.get("/sessions/{session_id}/messages", response_model=list[AgentMessageRead])
async def get_session_messages(
    workspace_id: uuid.UUID,
    session_id: uuid.UUID,
    user: User = Depends(current_active_user),
    db: AsyncSession = Depends(get_async_session),
):
    await _require_member(workspace_id, user, db)
    session = await db.get(AgentSession, session_id)
    if not session or session.workspace_id != workspace_id:
        raise HTTPException(status_code=404, detail="Session not found")
    res = await db.execute(
        select(AgentMessage)
        .where(AgentMessage.session_id == session_id)
        .order_by(AgentMessage.created_at)
    )
    return [AgentMessageRead.model_validate(m) for m in res.scalars().all()]


@router.delete("/sessions/{session_id}")
async def delete_session(
    workspace_id: uuid.UUID,
    session_id: uuid.UUID,
    user: User = Depends(current_active_user),
    db: AsyncSession = Depends(get_async_session),
):
    await _require_member(workspace_id, user, db)
    session = await db.get(AgentSession, session_id)
    if not session or session.workspace_id != workspace_id:
        raise HTTPException(status_code=404, detail="Session not found")
    await db.delete(session)
    await db.commit()
    return {"status": "deleted"}


# ── Documents (attachments) ────────────────────────────────────────


@router.post("/documents", response_model=AgentDocumentRead)
async def upload_document(
    workspace_id: uuid.UUID,
    file: UploadFile,
    user: User = Depends(current_active_user),
    db: AsyncSession = Depends(get_async_session),
):
    await _require_member(workspace_id, user, db)

    if not file.filename:
        raise HTTPException(status_code=400, detail="No filename provided")
    content = await file.read()
    if len(content) > MAX_FILE_SIZE:
        raise HTTPException(status_code=413, detail="File too large (max 50MB)")
    content_type = file.content_type or "application/octet-stream"
    ext = file.filename.rsplit(".", 1)[-1].lower() if "." in file.filename else ""
    if content_type not in ALLOWED_TYPES and ext not in ALLOWED_EXTS:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file type: {content_type}. Allowed: PDF, TXT, MD, CSV",
        )

    doc = await rag_service.ingest_document(
        workspace_id=workspace_id,
        uploaded_by=user.id,
        file_content=content,
        original_name=file.filename,
        content_type=content_type,
        db=db,
    )
    return AgentDocumentRead.model_validate(doc)


@router.get("/documents", response_model=list[AgentDocumentRead])
async def list_documents(
    workspace_id: uuid.UUID,
    user: User = Depends(current_active_user),
    db: AsyncSession = Depends(get_async_session),
):
    await _require_member(workspace_id, user, db)
    res = await db.execute(
        select(AgentDocument)
        .where(AgentDocument.workspace_id == workspace_id)
        .order_by(AgentDocument.created_at.desc())
    )
    return [AgentDocumentRead.model_validate(d) for d in res.scalars().all()]


@router.delete("/documents/{document_id}")
async def delete_document(
    workspace_id: uuid.UUID,
    document_id: uuid.UUID,
    user: User = Depends(current_active_user),
    db: AsyncSession = Depends(get_async_session),
):
    await _require_member(workspace_id, user, db)
    deleted = await rag_service.delete_document(document_id, workspace_id, db)
    if not deleted:
        raise HTTPException(status_code=404, detail="Document not found")
    return {"status": "deleted"}


# ── Memories ──────────────────────────────────────────────────────


@router.get("/memories", response_model=list[AgentMemoryRead])
async def list_memories(
    workspace_id: uuid.UUID,
    user: User = Depends(current_active_user),
    db: AsyncSession = Depends(get_async_session),
):
    await _require_member(workspace_id, user, db)
    res = await db.execute(
        select(AgentMemory)
        .where(AgentMemory.workspace_id == workspace_id)
        .order_by(AgentMemory.created_at.desc())
    )
    return [AgentMemoryRead.model_validate(m) for m in res.scalars().all()]


@router.delete("/memories/{memory_id}")
async def delete_memory(
    workspace_id: uuid.UUID,
    memory_id: uuid.UUID,
    user: User = Depends(current_active_user),
    db: AsyncSession = Depends(get_async_session),
):
    await _require_admin(workspace_id, user, db)
    mem = await db.get(AgentMemory, memory_id)
    if not mem or mem.workspace_id != workspace_id:
        raise HTTPException(status_code=404, detail="Memory not found")
    await db.delete(mem)
    await db.commit()
    return {"status": "deleted"}


# ── Workspace admin (owner/admin only) ─────────────────────────────


@router.get("/admin/stats", response_model=AgentAdminStats)
async def admin_stats(
    workspace_id: uuid.UUID,
    user: User = Depends(current_active_user),
    db: AsyncSession = Depends(get_async_session),
):
    await _require_admin(workspace_id, user, db)
    sessions = (
        await db.execute(
            select(func.count(AgentSession.id)).where(
                AgentSession.workspace_id == workspace_id
            )
        )
    ).scalar() or 0
    messages = (
        await db.execute(
            select(func.count(AgentMessage.id)).where(
                AgentMessage.workspace_id == workspace_id
            )
        )
    ).scalar() or 0
    documents = (
        await db.execute(
            select(func.count(AgentDocument.id)).where(
                AgentDocument.workspace_id == workspace_id
            )
        )
    ).scalar() or 0
    memories = (
        await db.execute(
            select(func.count(AgentMemory.id)).where(
                AgentMemory.workspace_id == workspace_id
            )
        )
    ).scalar() or 0
    return AgentAdminStats(
        total_sessions=sessions,
        total_messages=messages,
        total_documents=documents,
        total_memories=memories,
    )


@router.get(
    "/admin/documents/{document_id}/chunks",
    response_model=list[AgentDocumentChunkRead],
)
async def admin_get_document_chunks(
    workspace_id: uuid.UUID,
    document_id: uuid.UUID,
    user: User = Depends(current_active_user),
    db: AsyncSession = Depends(get_async_session),
):
    await _require_admin(workspace_id, user, db)
    doc = await db.get(AgentDocument, document_id)
    if not doc or doc.workspace_id != workspace_id:
        raise HTTPException(status_code=404, detail="Document not found")
    res = await db.execute(
        select(AgentDocumentChunk)
        .where(AgentDocumentChunk.document_id == document_id)
        .order_by(AgentDocumentChunk.chunk_index)
    )
    return [
        AgentDocumentChunkRead(
            id=c.id,
            document_id=c.document_id,
            chunk_index=c.chunk_index,
            content=c.content,
            has_embedding=c.embedding is not None,
        )
        for c in res.scalars().all()
    ]


@router.delete("/admin/sessions/{session_id}")
async def admin_delete_session(
    workspace_id: uuid.UUID,
    session_id: uuid.UUID,
    user: User = Depends(current_active_user),
    db: AsyncSession = Depends(get_async_session),
):
    await _require_admin(workspace_id, user, db)
    session = await db.get(AgentSession, session_id)
    if not session or session.workspace_id != workspace_id:
        raise HTTPException(status_code=404, detail="Session not found")
    await db.delete(session)
    await db.commit()
    return {"status": "deleted"}


@router.delete("/admin/sessions")
async def admin_clear_sessions(
    workspace_id: uuid.UUID,
    user: User = Depends(current_active_user),
    db: AsyncSession = Depends(get_async_session),
):
    """Wipe all chat sessions for this workspace."""
    await _require_admin(workspace_id, user, db)
    await db.execute(
        delete(AgentSession).where(AgentSession.workspace_id == workspace_id)
    )
    await db.commit()
    return {"status": "cleared"}
