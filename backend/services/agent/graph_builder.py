"""LangGraph builder for the SaaSAgent agent.

Each call rebinds tool-module-level singletons with the active SaaSAgent
so that RAG search / memory writes target the right tenant.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any
import uuid

from langchain_core.messages import SystemMessage
from langchain_openai import ChatOpenAI
from langgraph.graph import END, MessagesState, StateGraph
from langgraph.prebuilt import ToolNode

from backend.core.config import settings
from backend.tools.web_search import web_search
from backend.tools.read_file import read_file
from backend.tools.open_link import open_link
from backend.tools.rag_search import rag_search, set_rag_context
from backend.tools.memory_tool import save_memory, recall_memory, set_memory_context

SYSTEM_PROMPT = """\
You are the agent that owns this SaaS Agent. The user wants real outcomes from
their connected systems, not just answers. You have tools for: searching the
SaaSAgent knowledge base, browsing the web, reading uploaded documents, and
managing per-SaaSAgent memory.

Guidelines:
- Be concise and helpful. Answer directly.
- Use rag_search when the user asks about uploaded docs or SaaSAgent knowledge.
- Use web_search for current events / fresh info.
- Use open_link when the user shares a URL.
- Use save_memory when the user asks you to remember something important.
- Use recall_memory to recall previously saved information.
- Use read_file when the user asks to view a specific uploaded document.
- When you cite a document, name it.
- After answering, suggest 2-3 follow-ups on separate lines starting with ">>>".

Current date: {current_date}
SaaSAgent: {saas_agent_name}

{memory_context}
"""

REASONING_CONFIGS = {
    "fast": {"model": settings.default_model, "temperature": 0.3},
    "balanced": {"model": settings.default_model, "temperature": 0.5},
    "thorough": {"model": settings.default_model, "temperature": 0.7},
}


def get_all_tools():
    return [web_search, read_file, open_link, rag_search, save_memory, recall_memory]


def build_agent_graph(
    *,
    saas_agent_id: uuid.UUID,
    saas_agent_name: str = "this SaaS Agent",
    reasoning_mode: str = "balanced",
    memory_context: str = "",
    rag_svc=None,
    memory_svc=None,
    session_id=None,
    user_id: uuid.UUID | None = None,
):
    if rag_svc:
        set_rag_context(rag_svc, saas_agent_id=saas_agent_id)
    if memory_svc:
        set_memory_context(
            memory_svc,
            saas_agent_id=saas_agent_id,
            session_id=session_id,
            user_id=user_id,
        )

    config = REASONING_CONFIGS.get(reasoning_mode, REASONING_CONFIGS["balanced"])
    tools = get_all_tools()

    llm = ChatOpenAI(
        model=config["model"],
        temperature=config["temperature"],
        api_key=settings.openai_api_key,
        streaming=True,
    ).bind_tools(tools)

    system_prompt = SYSTEM_PROMPT.format(
        current_date=datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC"),
        saas_agent_name=saas_agent_name,
        memory_context=memory_context,
    )

    def agent_node(state: MessagesState) -> dict[str, Any]:
        messages = state["messages"]
        if not messages or not isinstance(messages[0], SystemMessage):
            messages = [SystemMessage(content=system_prompt)] + list(messages)
        response = llm.invoke(messages)
        return {"messages": [response]}

    def should_continue(state: MessagesState) -> str:
        last = state["messages"][-1]
        if hasattr(last, "tool_calls") and last.tool_calls:
            return "tools"
        return END

    tool_node = ToolNode(tools)

    graph = StateGraph(MessagesState)
    graph.add_node("agent", agent_node)
    graph.add_node("tools", tool_node)
    graph.set_entry_point("agent")
    graph.add_conditional_edges("agent", should_continue, {"tools": "tools", END: END})
    graph.add_edge("tools", "agent")

    return graph.compile()
