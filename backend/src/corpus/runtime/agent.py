from __future__ import annotations

from typing import Any

from langchain.agents import create_agent
from langchain_core.language_models import BaseChatModel
from routedeck_langgraph import (
    RouteDeckInvocationContext,
    RouteDeckMiddleware,
    RouteDeckRunnerRuntime,
    RouteDeckToolWrapper,
)

from corpus.features.workspace.prompt import WORKSPACE_AGENT_PROMPT


def create_corpus_agent(
    *,
    model: BaseChatModel,
    runtime: RouteDeckRunnerRuntime,
) -> Any:
    wrapper = RouteDeckToolWrapper(runtime)
    middleware = RouteDeckMiddleware(runtime)
    return create_agent(
        model=model,
        tools=wrapper.tools,
        middleware=(middleware,),
        system_prompt=WORKSPACE_AGENT_PROMPT,
        context_schema=RouteDeckInvocationContext,
        name="corpus_agent",
    )


def create_corpus_entry_agent(*, model: BaseChatModel) -> Any:
    return create_agent(
        model=model,
        tools=(),
        system_prompt=WORKSPACE_AGENT_PROMPT,
        name="corpus_entry_agent",
    )


__all__ = ["create_corpus_agent", "create_corpus_entry_agent"]
