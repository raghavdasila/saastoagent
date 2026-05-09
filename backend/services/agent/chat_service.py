"""Workspace-scoped chat service. Streams SSE events from a LangGraph agent."""

from __future__ import annotations

import asyncio
import re
import uuid
from typing import Any, AsyncGenerator

import structlog
from langchain_core.messages import AIMessage, HumanMessage
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.core.config import settings
from backend.core.models import AgentMessage, AgentSession, Workspace
from backend.core.protocol import (
    agent_end,
    agent_start,
    error,
    follow_ups,
    keepalive,
    message_delta,
    source_citations,
    stream_end,
    stream_start,
    thinking_delta,
    tool_end,
    tool_start,
)
from backend.services.agent.graph_builder import build_agent_graph
from backend.services.agent.memory_service import memory_service
from backend.services.agent.rag_service import rag_service

logger = structlog.get_logger()

_STREAM_DONE = object()
_THINK_PATTERN = re.compile(r"<think>(.*?)</think>", re.DOTALL)


class ChatService:
    async def run(
        self,
        *,
        message: str,
        workspace_id: uuid.UUID,
        user_id: uuid.UUID | None,
        session_id: uuid.UUID | None,
        reasoning_mode: str,
        handoff_context: dict[str, Any] | None,
        db: AsyncSession,
    ) -> AsyncGenerator[str, None]:
        session = await self._resolve_session(session_id, workspace_id, user_id, db, handoff_context=handoff_context)
        session_id = session.id

        # Resolve workspace name for prompt context
        ws = await db.get(Workspace, workspace_id)
        workspace_name = ws.name if ws else "this workspace"

        # Persist user message
        db.add(
            AgentMessage(
                session_id=session_id,
                workspace_id=workspace_id,
                role="user",
                content=message,
            )
        )
        await db.commit()

        memory_context = await memory_service.get_session_context(
            session_id, workspace_id, db
        )
        handoff_summary = _handoff_summary(session.metadata_ or {})
        if handoff_summary:
            memory_context = f"{handoff_summary}\n\n{memory_context}".strip()

        history_result = await db.execute(
            select(AgentMessage)
            .where(AgentMessage.session_id == session_id)
            .order_by(AgentMessage.created_at.desc())
            .limit(20)
        )
        history = list(reversed(history_result.scalars().all()))

        lc_messages = []
        for msg in history:
            if msg.role == "user":
                lc_messages.append(HumanMessage(content=msg.content))
            elif msg.role == "assistant" and msg.content:
                lc_messages.append(AIMessage(content=msg.content))

        queue: asyncio.Queue = asyncio.Queue()

        yield stream_start(session_id)
        yield agent_start()

        task = asyncio.create_task(
            self._run_agent(
                queue=queue,
                workspace_id=workspace_id,
                workspace_name=workspace_name,
                user_id=user_id,
                messages=lc_messages,
                reasoning_mode=reasoning_mode,
                session_id=session_id,
                memory_context=memory_context,
                db=db,
            )
        )

        try:
            while True:
                try:
                    event = await asyncio.wait_for(
                        queue.get(), timeout=settings.keepalive_interval
                    )
                    if event is _STREAM_DONE:
                        break
                    yield event
                except asyncio.TimeoutError:
                    yield keepalive()
        except Exception as e:  # pragma: no cover - defensive
            logger.error("stream_error", error=str(e))
            yield error(str(e))
        finally:
            if not task.done():
                task.cancel()

        yield agent_end()
        yield stream_end()

    async def _run_agent(
        self,
        *,
        queue: asyncio.Queue,
        workspace_id: uuid.UUID,
        workspace_name: str,
        user_id: uuid.UUID | None,
        messages: list,
        reasoning_mode: str,
        session_id: uuid.UUID,
        memory_context: str,
        db: AsyncSession,
    ) -> None:
        try:
            graph = build_agent_graph(
                workspace_id=workspace_id,
                workspace_name=workspace_name,
                reasoning_mode=reasoning_mode,
                memory_context=memory_context,
                rag_svc=rag_service,
                memory_svc=memory_service,
                session_id=session_id,
                user_id=user_id,
            )

            full_content = ""
            full_thinking = ""
            tool_calls_data: list[dict] = []
            sources_data: list[dict] = []

            async for event in graph.astream_events({"messages": messages}, version="v2"):
                kind = event.get("event", "")
                data = event.get("data", {})

                if kind == "on_chat_model_stream":
                    chunk = data.get("chunk")
                    if chunk and getattr(chunk, "content", None):
                        content = chunk.content
                        if reasoning_mode == "thorough" and (
                            "<think>" in content or "</think>" in content
                        ):
                            await queue.put(thinking_delta(content))
                            full_thinking += content
                        else:
                            clean = _THINK_PATTERN.sub("", content)
                            if clean:
                                await queue.put(message_delta(clean))
                                full_content += clean

                elif kind == "on_tool_start":
                    tool_name = event.get("name", "unknown")
                    run_id = event.get("run_id", str(uuid.uuid4()))
                    inputs = data.get("input", {})
                    call_id = str(run_id)[:8]
                    await queue.put(tool_start(tool_name, call_id, inputs))
                    tool_calls_data.append(
                        {"tool_name": tool_name, "call_id": call_id, "inputs": inputs}
                    )
                    if tool_name == "rag_search":
                        sources_data.append(inputs)

                elif kind == "on_tool_end":
                    run_id = event.get("run_id", "")
                    call_id = str(run_id)[:8]
                    output = data.get("output", "")
                    if hasattr(output, "content"):
                        output = output.content
                    await queue.put(tool_end(call_id, str(output)[:5000]))

            # Extract follow-ups
            follow_up_lines: list[str] = []
            clean_lines: list[str] = []
            for line in full_content.split("\n"):
                stripped = line.strip()
                if stripped.startswith(">>>"):
                    follow_up_lines.append(stripped.lstrip(">>> ").strip())
                else:
                    clean_lines.append(line)
            if follow_up_lines:
                full_content = "\n".join(clean_lines).strip()
                await queue.put(follow_ups(follow_up_lines))

            persisted_sources: list[dict] | None = None
            if sources_data:
                rag_results = await rag_service.search(
                    sources_data[0].get("query", ""),
                    workspace_id=workspace_id,
                    top_k=3,
                )
                if rag_results:
                    payload = [
                        {
                            "title": r["document_name"],
                            "chunk": r["content"][:200],
                            "score": r["score"],
                            "document_id": r["document_id"],
                        }
                        for r in rag_results
                    ]
                    await queue.put(source_citations(payload))
                    persisted_sources = [
                        {"title": r["document_name"], "document_id": r["document_id"]}
                        for r in rag_results
                    ]

            db.add(
                AgentMessage(
                    session_id=session_id,
                    workspace_id=workspace_id,
                    role="assistant",
                    content=full_content,
                    thinking=full_thinking or None,
                    tool_calls=tool_calls_data or None,
                    sources=persisted_sources,
                    follow_ups=follow_up_lines or None,
                )
            )
            await db.commit()

            session_obj = await db.get(AgentSession, session_id)
            if session_obj and not session_obj.title and full_content:
                session_obj.title = full_content[:80].split("\n")[0]
                await db.commit()

        except Exception as e:
            logger.error("agent_error", error=str(e), session_id=str(session_id))
            await queue.put(error(str(e)))
        finally:
            await queue.put(_STREAM_DONE)

    async def _resolve_session(
        self,
        session_id: uuid.UUID | None,
        workspace_id: uuid.UUID,
        user_id: uuid.UUID | None,
        db: AsyncSession,
        handoff_context: dict[str, Any] | None = None,
    ) -> AgentSession:
        if session_id:
            session = await db.get(AgentSession, session_id)
            if session and session.workspace_id == workspace_id:
                if session.user_id != user_id:
                    session = None
                else:
                    if handoff_context and not (session.metadata_ or {}).get("handoff_context"):
                        session.metadata_ = {**(session.metadata_ or {}), "handoff_context": handoff_context}
                        await db.commit()
                    return session
        session = AgentSession(
            workspace_id=workspace_id,
            user_id=user_id,
            metadata_={"handoff_context": handoff_context} if handoff_context else None,
        )
        db.add(session)
        await db.commit()
        await db.refresh(session)
        return session


chat_service = ChatService()


def _handoff_summary(metadata: dict[str, Any]) -> str:
    handoff = metadata.get("handoff_context")
    if not isinstance(handoff, dict):
        return ""
    workspace_name = handoff.get("workspace_name") or "this workspace"
    entry_draft = handoff.get("entry_draft") if isinstance(handoff.get("entry_draft"), dict) else {}
    connection_draft = handoff.get("connection_draft") if isinstance(handoff.get("connection_draft"), dict) else {}
    recent_messages = handoff.get("recent_entry_messages") if isinstance(handoff.get("recent_entry_messages"), list) else []
    parts = [f"Entry handoff: user reached operator chat from the setup flow for {workspace_name}."]
    workspace_job = entry_draft.get("workspace_job")
    if workspace_job:
        parts.append(f"Intended workspace job: {workspace_job}.")
    api_draft = entry_draft.get("api_draft") if isinstance(entry_draft.get("api_draft"), dict) else {}
    base_url = connection_draft.get("base_url") or api_draft.get("base_url")
    spec_url = connection_draft.get("spec_url") or api_draft.get("spec_url")
    if base_url:
        parts.append(f"Draft API base URL: {base_url}.")
    if spec_url:
        parts.append(f"Draft API spec URL: {spec_url}.")
    if recent_messages:
        compact = " | ".join(str(message)[:160] for message in recent_messages[-4:])
        parts.append(f"Recent entry conversation: {compact}")
    return "\n".join(parts)
