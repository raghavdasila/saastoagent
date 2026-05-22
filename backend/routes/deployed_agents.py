from __future__ import annotations

import asyncio
import uuid

from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession

from backend.core.auth import current_optional_active_user
from backend.core.config import settings
from backend.core.database import get_async_session
from backend.core.models import AgentSession, User
from backend.core.protocol import keepalive
from backend.core.schemas import ChatRequest, DeployedAgentProfile
from backend.routes.agent import _client_ip
from backend.services.agent.anonymous_rate_limit import anonymous_chat_rate_limiter
from backend.services.agent.chat_service import chat_service
from backend.services.deployed_agents import (
    build_deployed_handoff_context,
    deployment_profile_for_slug,
)
from backend.services.deployed_agent_events import (
    deployed_agent_session_events,
    encode_public_agent_message_event,
    public_agent_message_event_payload,
    public_approval_messages_after,
)

router = APIRouter(prefix="/api/deployed-agents", tags=["deployed-agents"])


@router.get("/{slug}", response_model=DeployedAgentProfile)
async def get_deployed_agent_profile(
    slug: str,
    db: AsyncSession = Depends(get_async_session),
):
    resolved = await deployment_profile_for_slug(slug=slug, db=db)
    if resolved is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Deployed agent not found")
    _, _, profile = resolved
    if not profile.enabled:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Deployed agent is not enabled")
    return profile


@router.post("/{slug}/chat")
async def deployed_agent_chat(
    slug: str,
    body: ChatRequest,
    request: Request,
    user: User | None = Depends(current_optional_active_user),
    db: AsyncSession = Depends(get_async_session),
):
    resolved = await deployment_profile_for_slug(slug=slug, db=db)
    if resolved is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Deployed agent not found")
    _, deployment, profile = resolved
    if not deployment.enabled:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Deployed agent is not enabled")
    if profile.auth_required and user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Sign in to chat with this agent")
    if user is None:
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

    handoff_context = build_deployed_handoff_context(
        slug=profile.slug,
        auth_required=profile.auth_required,
        visitor_auth_mode=profile.visitor_auth_mode,
        execution_mode=profile.execution_mode,
        default_write_policy=profile.default_write_policy,
    )
    if body.handoff_context:
        handoff_context = {**body.handoff_context, **handoff_context}

    async def generate():
        async for event in chat_service.run(
            message=body.message,
            saas_agent_id=profile.saas_agent_id,
            user_id=user.id if user else None,
            session_id=body.session_id,
            reasoning_mode=body.reasoning_mode,
            handoff_context=handoff_context,
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


@router.get("/{slug}/sessions/{session_id}/events")
async def deployed_agent_session_events_stream(
    slug: str,
    session_id: uuid.UUID,
    request: Request,
    after_message_id: uuid.UUID | None = None,
    user: User | None = Depends(current_optional_active_user),
    db: AsyncSession = Depends(get_async_session),
):
    resolved = await deployment_profile_for_slug(slug=slug, db=db)
    if resolved is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Deployed agent not found")
    _, deployment, profile = resolved
    if not deployment.enabled:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Deployed agent is not enabled")
    if profile.auth_required and user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Sign in to chat with this agent")

    session = await db.get(AgentSession, session_id)
    if session is None or session.saas_agent_id != profile.saas_agent_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Deployed chat session not found")
    if session.user_id != (user.id if user else None):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Session does not belong to this visitor")

    last_event_id = request.headers.get("last-event-id")
    cursor_id = after_message_id
    if cursor_id is None and last_event_id:
        try:
            cursor_id = uuid.UUID(last_event_id)
        except ValueError:
            cursor_id = None

    async def generate():
        for message in await public_approval_messages_after(session_id=session_id, db=db, after_message_id=cursor_id):
            yield encode_public_agent_message_event(
                public_agent_message_event_payload(
                    message_id=str(message.id),
                    session_id=str(message.session_id),
                    content=message.content,
                    metadata=message.metadata_ or {},
                )
            )
        async with deployed_agent_session_events.subscribe(session_id) as queue:
            while True:
                if await request.is_disconnected():
                    break
                try:
                    payload = await asyncio.wait_for(queue.get(), timeout=settings.keepalive_interval)
                    yield encode_public_agent_message_event(payload)
                except asyncio.TimeoutError:
                    yield keepalive()

    return StreamingResponse(
        generate(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )
