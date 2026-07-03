"""SaaSAgent-scoped chat service. Streams SSE events from a LangGraph agent."""

from __future__ import annotations

import asyncio
import json
import re
import uuid
from typing import Any, AsyncGenerator

import structlog
from langchain_core.messages import AIMessage, HumanMessage
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.core.config import settings
from backend.core.database import async_session
from backend.core.models import AgentMessage, AgentSession, SaaSAgent
from backend.core.protocol import (
    SSEEvent,
    agent_end,
    agent_start,
    debug_timing,
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
from backend.services.agent.rest_operator import run_rest_operator_turn
from backend.services.agent.timing import RequestTiming

logger = structlog.get_logger()

_STREAM_DONE = object()
_THINK_PATTERN = re.compile(r"<think>(.*?)</think>", re.DOTALL)

REST_OPERATOR_STREAM_PROMPT = """You write the user-facing reply for a deployed SaaS agent after a deterministic API operation has already run.
The operation_result is the source of truth. Preserve exact ids, product names, variants, prices, totals, currencies, statuses, and trace tokens.
Do not invent actions, orders, inventory, or approvals. Do not say you will do something that the operation_result says is already done.
Be concise and conversational."""


class ChatService:
    async def run(
        self,
        *,
        message: str,
        saas_agent_id: uuid.UUID,
        user_id: uuid.UUID | None,
        session_id: uuid.UUID | None,
        reasoning_mode: str,
        handoff_context: dict[str, Any] | None,
        db: AsyncSession,
    ) -> AsyncGenerator[str, None]:
        timing = RequestTiming()
        timing.mark("chat.request_received")
        with timing.span("chat.resolve_session"):
            session = await self._resolve_session(session_id, saas_agent_id, user_id, db, handoff_context=handoff_context)
        session_id = session.id
        public_response = _is_deployed_channel(session.metadata_ or {})

        # Resolve SaaSAgent name for prompt context
        with timing.span("chat.load_saas_agent"):
            ws = await db.get(SaaSAgent, saas_agent_id)
        saas_agent_name = ws.name if ws else "this SaaS Agent"
        custom_system_prompt = ws.system_prompt if ws and ws.system_prompt else ""
        custom_instructions = ws.instructions if ws and ws.instructions else ""

        # Persist user message
        with timing.span("chat.persist_user_message"):
            db.add(
                AgentMessage(
                    session_id=session_id,
                    saas_agent_id=saas_agent_id,
                    role="user",
                    content=message,
                )
            )
            await db.commit()

        with timing.span("chat.load_memory_context"):
            memory_context = await memory_service.get_session_context(
                session_id, saas_agent_id, db
            )
        handoff_summary = _handoff_summary(session.metadata_ or {})
        if handoff_summary:
            memory_context = f"{handoff_summary}\n\n{memory_context}".strip()

        with timing.span("chat.load_history"):
            history_result = await db.execute(
                select(AgentMessage)
                .where(AgentMessage.session_id == session_id)
                .order_by(AgentMessage.created_at.desc())
                .limit(20)
            )
            history = list(reversed(history_result.scalars().all()))

        with timing.span("chat.build_langchain_messages"):
            lc_messages = []
            for msg in history:
                if msg.role == "user":
                    lc_messages.append(HumanMessage(content=msg.content))
                elif msg.role == "assistant" and msg.content:
                    lc_messages.append(AIMessage(content=msg.content))

        queue: asyncio.Queue = asyncio.Queue()

        timing.mark("sse.stream_start")
        yield stream_start(session_id)
        yield agent_start()

        task = asyncio.create_task(
            self._run_agent(
                queue=queue,
                saas_agent_id=saas_agent_id,
                saas_agent_name=saas_agent_name,
                custom_system_prompt=custom_system_prompt,
                custom_instructions=custom_instructions,
                user_id=user_id,
                messages=lc_messages,
                reasoning_mode=reasoning_mode,
                session_id=session_id,
                session=session,
                memory_context=memory_context,
                public_response=public_response,
                db=db,
                timing=timing,
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
            logger.exception("stream_error", error=str(e) or repr(e), error_type=e.__class__.__name__)
            yield error(str(e) or "The agent hit an internal error while streaming the response.")
        finally:
            if not task.done():
                task.cancel()

        yield agent_end()
        yield stream_end()

    async def _run_agent(
        self,
        *,
        queue: asyncio.Queue,
        saas_agent_id: uuid.UUID,
        saas_agent_name: str,
        custom_system_prompt: str,
        custom_instructions: str,
        user_id: uuid.UUID | None,
        messages: list,
        reasoning_mode: str,
        session_id: uuid.UUID,
        session: AgentSession,
        memory_context: str,
        public_response: bool,
        db: AsyncSession,
        timing: RequestTiming,
    ) -> None:
        try:
            with timing.span("agent.build_graph"):
                graph = build_agent_graph(
                    saas_agent_id=saas_agent_id,
                    saas_agent_name=saas_agent_name,
                    reasoning_mode=reasoning_mode,
                    memory_context=memory_context,
                    custom_system_prompt=custom_system_prompt,
                    custom_instructions=custom_instructions,
                    rag_svc=rag_service,
                    memory_svc=memory_service,
                    session_id=session_id,
                    user_id=user_id,
                )

            full_content = ""
            full_thinking = ""
            tool_calls_data: list[dict] = []
            sources_data: list[dict] = []

            async def emit_runtime_event(event_name: str, payload: dict[str, Any]) -> None:
                if public_response and event_name in {"tool_start", "tool_end"}:
                    return
                if event_name == "tool_start":
                    await queue.put(tool_start(payload["tool_name"], payload["call_id"], payload.get("inputs") or {}))
                    tool_calls_data.append(
                        {
                            "tool_name": payload["tool_name"],
                            "call_id": payload["call_id"],
                            "inputs": payload.get("inputs") or {},
                        }
                    )
                    return
                if event_name == "tool_end":
                    await queue.put(tool_end(payload["call_id"], str(payload.get("output") or "")[:5000]))
                    return
                await queue.put(SSEEvent(event=event_name, data=payload).encode())

            with timing.span("agent.memory_command_check"):
                memory_content = await self._maybe_handle_memory_command(
                    message=messages[-1].content if messages else "",
                    saas_agent_id=saas_agent_id,
                    session_id=session_id,
                    user_id=user_id,
                    db=db,
                )
            if memory_content is not None:
                full_content = memory_content
                with timing.span("sse.enqueue_first_message"):
                    await queue.put(message_delta(full_content))
                memory_follow_ups = ["Show saved memories", "Recall memory for this SaaS Agent"]
                await queue.put(follow_ups(memory_follow_ups))
                assistant_message = AgentMessage(
                    session_id=session_id,
                    saas_agent_id=saas_agent_id,
                    role="assistant",
                    content=full_content,
                    follow_ups=memory_follow_ups,
                    metadata_={"timing": timing.snapshot()},
                )
                with timing.span("chat.persist_assistant_message"):
                    db.add(assistant_message)
                    await db.commit()
                final_timing = timing.snapshot()
                schedule_message_metadata_update(assistant_message.id, {"timing": final_timing})
                if not public_response:
                    await queue.put(debug_timing(final_timing))
                return

            with timing.span("rest_operator.total"):
                rest_content = await run_rest_operator_turn(
                    message=messages[-1].content if messages else "",
                    saas_agent_id=saas_agent_id,
                    session_id=session_id,
                    user_id=user_id,
                    session=session,
                    db=db,
                    emit=emit_runtime_event,
                    public_response=public_response,
                    timing=timing,
                )
            if rest_content is not None:
                with timing.span("agent.rest_operator_response_stream"):
                    async for delta in self._stream_rest_operator_message(
                        message=messages[-1].content if messages else "",
                        operation_result=rest_content,
                        saas_agent_name=saas_agent_name,
                        public_response=public_response,
                        reasoning_mode=reasoning_mode,
                        memory_context=memory_context,
                    ):
                        if not delta:
                            continue
                        full_content += delta
                        await queue.put(message_delta(delta))
                if not full_content.strip():
                    raise RuntimeError("Model stream returned no deployed-agent response content.")
                rest_follow_ups = _rest_follow_ups(f"{rest_content}\n{full_content}")
                if rest_follow_ups:
                    await queue.put(follow_ups(rest_follow_ups))
                assistant_message = AgentMessage(
                    session_id=session_id,
                    saas_agent_id=saas_agent_id,
                    role="assistant",
                    content=full_content,
                    thinking=None,
                    tool_calls=tool_calls_data or None,
                    sources=None,
                    follow_ups=rest_follow_ups
                    or [
                        "Inspect the generated actions",
                        "Connect or activate another API",
                        "Ask me to run a read-only API action",
                    ],
                    metadata_={"timing": timing.snapshot()},
                )
                with timing.span("chat.persist_assistant_message"):
                    db.add(assistant_message)
                    await db.commit()
                final_timing = timing.snapshot()
                schedule_message_metadata_update(assistant_message.id, {"timing": final_timing})
                if not public_response:
                    await queue.put(debug_timing(final_timing))
                return

            with timing.span("agent.langgraph_stream"):
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
                        if public_response:
                            continue
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
                        if public_response:
                            continue
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
                    saas_agent_id=saas_agent_id,
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

            assistant_message = AgentMessage(
                session_id=session_id,
                saas_agent_id=saas_agent_id,
                role="assistant",
                content=full_content,
                thinking=full_thinking or None,
                tool_calls=tool_calls_data or None,
                sources=persisted_sources,
                follow_ups=follow_up_lines or None,
                metadata_={"timing": timing.snapshot()},
            )
            with timing.span("chat.persist_assistant_message"):
                db.add(assistant_message)
                await db.commit()
            final_timing = timing.snapshot()
            schedule_message_metadata_update(assistant_message.id, {"timing": final_timing})
            if not public_response:
                await queue.put(debug_timing(final_timing))

            session_obj = await db.get(AgentSession, session_id)
            if session_obj and not session_obj.title and full_content:
                session_obj.title = full_content[:80].split("\n")[0]
                await db.commit()

        except Exception as e:
            logger.exception("agent_error", error=str(e) or repr(e), error_type=e.__class__.__name__, session_id=str(session_id))
            await queue.put(error(str(e) or "The agent hit an internal error while handling that request."))
        finally:
            await queue.put(_STREAM_DONE)

    async def _resolve_session(
        self,
        session_id: uuid.UUID | None,
        saas_agent_id: uuid.UUID,
        user_id: uuid.UUID | None,
        db: AsyncSession,
        handoff_context: dict[str, Any] | None = None,
    ) -> AgentSession:
        if session_id:
            session = await db.get(AgentSession, session_id)
            if session and session.saas_agent_id == saas_agent_id:
                if session.user_id != user_id:
                    session = None
                else:
                    if handoff_context and not (session.metadata_ or {}).get("handoff_context"):
                        session.metadata_ = {**(session.metadata_ or {}), "handoff_context": handoff_context}
                        await db.commit()
                    return session
        session = AgentSession(
            saas_agent_id=saas_agent_id,
            user_id=user_id,
            metadata_={"handoff_context": handoff_context} if handoff_context else None,
        )
        db.add(session)
        await db.commit()
        await db.refresh(session)
        return session

    async def _maybe_handle_memory_command(
        self,
        *,
        message: str,
        saas_agent_id: uuid.UUID,
        session_id: uuid.UUID,
        user_id: uuid.UUID | None,
        db: AsyncSession,
    ) -> str | None:
        save_match = re.search(r"\bremember(?: that| this|:)?\s+(.+)$", message.strip(), re.IGNORECASE | re.DOTALL)
        if save_match:
            content = save_match.group(1).strip()
            if not content:
                return "Tell me what to remember for this SaaS Agent."
            category = "instruction" if "always" in content.lower() or "prefer" in content.lower() else "fact"
            memory = await memory_service.save(
                content,
                saas_agent_id=saas_agent_id,
                category=category,
                session_id=session_id,
                user_id=user_id,
                db=db,
            )
            return f"Saved memory `{str(memory.id)[:8]}` for this SaaS Agent.\n\n{content}"

        lowered = message.lower()
        if "what do you remember" in lowered or lowered.startswith("recall memory") or lowered.startswith("show saved memories"):
            query = message
            memories = await memory_service.recall(query, saas_agent_id=saas_agent_id, db=db, limit=8)
            if not memories:
                return "No saved memories found for this SaaS Agent yet."
            lines = ["Saved memories for this SaaS Agent:"]
            for memory in memories:
                lines.append(f"- ({memory['category']}) {memory['content']}")
            return "\n".join(lines)

        return None

    async def _stream_rest_operator_message(
        self,
        *,
        message: str,
        operation_result: str,
        saas_agent_name: str,
        public_response: bool,
        reasoning_mode: str,
        memory_context: str,
    ) -> AsyncGenerator[str, None]:
        from openai import AsyncOpenAI

        from backend.core.langsmith import wrap_openai_client

        client = wrap_openai_client(AsyncOpenAI(api_key=settings.openai_api_key))
        stream = await client.chat.completions.create(
            model=settings.default_model,
            messages=[
                {"role": "system", "content": REST_OPERATOR_STREAM_PROMPT},
                {
                    "role": "user",
                    "content": json.dumps(
                        {
                            "user_input": message,
                            "saas_agent_name": saas_agent_name,
                            "public_response": public_response,
                            "reasoning_mode": reasoning_mode,
                            "memory_context": memory_context,
                            "operation_result": operation_result,
                        }
                    ),
                },
            ],
            stream=True,
            **_openai_latency_options(),
        )
        async for chunk in stream:
            content = chunk.choices[0].delta.content if chunk.choices else None
            if content:
                yield content


chat_service = ChatService()


def schedule_message_metadata_update(message_id: uuid.UUID | None, metadata: dict[str, Any]) -> None:
    if message_id is None:
        return
    try:
        asyncio.get_running_loop().create_task(
            _update_message_metadata(message_id=message_id, metadata=metadata)
        )
    except RuntimeError:
        logger.warning("message_metadata_update_not_scheduled", message_id=str(message_id))


async def _update_message_metadata(*, message_id: uuid.UUID, metadata: dict[str, Any]) -> None:
    try:
        async with async_session() as update_db:
            message = await update_db.get(AgentMessage, message_id)
            if message is None:
                return
            message.metadata_ = {**(message.metadata_ or {}), **metadata}
            await update_db.commit()
    except Exception:
        logger.exception("message_metadata_update_failed", message_id=str(message_id))


def _handoff_summary(metadata: dict[str, Any]) -> str:
    handoff = metadata.get("handoff_context")
    if not isinstance(handoff, dict):
        return ""
    saas_agent_name = handoff.get("saas_agent_name") or "this SaaS Agent"
    entry_draft = handoff.get("entry_draft") if isinstance(handoff.get("entry_draft"), dict) else {}
    connection_draft = handoff.get("connection_draft") if isinstance(handoff.get("connection_draft"), dict) else {}
    recent_messages = handoff.get("recent_entry_messages") if isinstance(handoff.get("recent_entry_messages"), list) else []
    parts = [f"Entry handoff: user reached operator chat from the setup flow for {saas_agent_name}."]
    draft_saas_agent_name = entry_draft.get("saas_agent_name")
    if draft_saas_agent_name:
        parts.append(f"Draft SaaSAgent name: {draft_saas_agent_name}.")
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


def _is_deployed_channel(metadata: dict[str, Any]) -> bool:
    handoff = metadata.get("handoff_context")
    return isinstance(handoff, dict) and handoff.get("channel") == "deployed_web"


def _rest_follow_ups(content: str) -> list[str]:
    match = re.search(r"Trace:\s*`([a-f0-9]{8})`", content, re.IGNORECASE)
    if not match:
        return []
    token = match.group(1)
    if "needs approval" in content.lower():
        return [f"approve {token}", f"cancel {token}", "Inspect the generated actions"]
    if "needs more inputs" in content.lower():
        return ["Inspect the generated actions", "Tell me the missing inputs"]
    return ["Inspect the generated actions", "Ask me to run another read-only API action"]


def _openai_latency_options() -> dict[str, Any]:
    effort = settings.openai_reasoning_effort.strip()
    return {"reasoning_effort": effort} if effort else {}
