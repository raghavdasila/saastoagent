import uuid
import asyncio

from fastapi import APIRouter, Depends, Request, Response
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession

from backend.core.auth import current_optional_active_user
from backend.core.database import get_async_session
from backend.core.models import User
from backend.core.protocol import SSEEvent, error, stream_end, stream_start
from backend.core.schemas import EntryGraphTurnRequest, EntryGraphTurnResponse, EntryPersistentActionsResponse
from backend.services.entry_runtime import (
    ENTRY_SESSION_COOKIE,
    ENTRY_SESSION_COOKIE_MAX_AGE,
    run_entry_turn,
)
from backend.services.entry_runtime.runtime_store import EntryRuntimeStore
from backend.services.entry_runtime.ui_actions import persistent_entry_actions

router = APIRouter(prefix="/api/entry", tags=["entry"])


def _session_id_from_cookie(request: Request) -> uuid.UUID | None:
    raw_session_id = request.cookies.get(ENTRY_SESSION_COOKIE)
    if not raw_session_id:
        return None
    try:
        return uuid.UUID(raw_session_id)
    except ValueError:
        return None


def _session_id_from_request(body: EntryGraphTurnRequest, request: Request) -> uuid.UUID | None:
    return body.session_id or _session_id_from_cookie(request)


@router.get("/persistent-actions", response_model=EntryPersistentActionsResponse)
async def entry_persistent_actions(
    workspace_id: uuid.UUID | None = None,
    user: User | None = Depends(current_optional_active_user),
):
    return EntryPersistentActionsResponse(
        persistent_actions=persistent_entry_actions(
            node="operator_ready" if workspace_id else None,
            current_user=user,
            active_workspace_id=workspace_id,
        )
    )


@router.post("/turn", response_model=EntryGraphTurnResponse)
async def entry_turn(
    body: EntryGraphTurnRequest,
    request: Request,
    response: Response,
    user: User | None = Depends(current_optional_active_user),
    db: AsyncSession = Depends(get_async_session),
):
    session_id = _session_id_from_request(body, request)

    result = await run_entry_turn(
        body=body,
        current_user=user,
        db=db,
        session_id=session_id,
    )
    response.set_cookie(
        ENTRY_SESSION_COOKIE,
        str(result.session_id),
        httponly=True,
        max_age=ENTRY_SESSION_COOKIE_MAX_AGE,
        samesite="lax",
        path="/",
    )
    return result.payload


@router.post("/stream")
async def entry_stream(
    body: EntryGraphTurnRequest,
    request: Request,
    user: User | None = Depends(current_optional_active_user),
    db: AsyncSession = Depends(get_async_session),
):
    store = EntryRuntimeStore(db)
    session_record, _ = await store.ensure_session(
        session_id=_session_id_from_request(body, request),
        current_user=user,
        initial_state=body.state.model_dump(mode="json") if body.state else None,
    )

    async def generate():
        queue: asyncio.Queue[str | None] = asyncio.Queue()

        async def emit(event: str, data: dict[str, object]) -> None:
            await queue.put(SSEEvent(event=event, data=data).encode())

        async def run_and_queue() -> None:
            try:
                await run_entry_turn(
                    body=body,
                    current_user=user,
                    db=db,
                    session_id=session_record.id,
                    event_sink=emit,
                )
            except Exception as exc:
                await queue.put(error(str(exc)))
            finally:
                await queue.put(stream_end())
                await queue.put(None)

        yield stream_start(session_record.id)
        task = asyncio.create_task(run_and_queue())
        try:
            while True:
                chunk = await queue.get()
                if chunk is None:
                    break
                yield chunk
        finally:
            if not task.done():
                task.cancel()

    response = StreamingResponse(
        generate(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )
    response.set_cookie(
        ENTRY_SESSION_COOKIE,
        str(session_record.id),
        httponly=True,
        max_age=ENTRY_SESSION_COOKIE_MAX_AGE,
        samesite="lax",
        path="/",
    )
    return response
