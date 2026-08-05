from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from langchain.agents import create_agent
from langchain.agents.middleware import ModelRequest
from langchain_core.language_models import BaseChatModel
from routedeck_core.contracts.operations import (
    OperationDisposition,
    OperationRequest,
    OperationSource,
)
from routedeck_core.contracts.projection import FrozenJsonObject
from routedeck_langgraph import (
    RouteDeckInvocationContext,
    RouteDeckInvocationTraceRecorder,
    RouteDeckMiddleware,
    RouteDeckRunnerRuntime,
    RouteDeckToolWrapper,
)

from .prompt import CORPUS_AGENT_PROMPT


def should_enter_product_help(current_node: str) -> bool:
    return current_node == "lounge.home"


class CorpusRouteDeckMiddleware(RouteDeckMiddleware):
    """Apply Corpus-owned model behavior after RouteDeck resolves legal context."""

    async def prepare_model_request(
        self,
        request: ModelRequest[RouteDeckInvocationContext],
    ):
        await self._enter_product_help(request)
        return await super().prepare_model_request(request)

    async def _enter_product_help(
        self,
        request: ModelRequest[RouteDeckInvocationContext],
    ) -> None:
        runtime_context = getattr(request.runtime, "context", None)
        session_id = self.tool_wrapper.session_id(runtime_context)
        snapshot = await self.tool_wrapper.runner.store.load(session_id)
        if not should_enter_product_help(snapshot.state.current.node_id):
            return
        if not isinstance(runtime_context, Mapping):
            raise RuntimeError("Corpus agent runtime context is unavailable")
        request_id_prefix = runtime_context.get("request_id_prefix")
        if not isinstance(request_id_prefix, str) or not request_id_prefix:
            raise RuntimeError("Corpus agent request prefix is unavailable")
        result = await self.tool_wrapper.runner.run(
            OperationRequest(
                session_id=session_id,
                request_id=f"{request_id_prefix}:enter-product-help",
                expected_session_version=snapshot.session_version,
                operation_id="lounge.open_product_help",
                source=OperationSource.AGENT,
                arguments=FrozenJsonObject({}),
            ),
            turn=runtime_context.get("turn"),
        )
        if (
            result.disposition is not OperationDisposition.COMPLETED
            or result.outcome != "opened"
        ):
            raise RuntimeError(
                "Corpus could not enter product help before answering the visitor"
            )


def create_corpus_agent(
    *,
    model: BaseChatModel,
    runtime: RouteDeckRunnerRuntime,
    invocation_traces: RouteDeckInvocationTraceRecorder,
) -> Any:
    wrapper = RouteDeckToolWrapper(runtime)
    middleware = CorpusRouteDeckMiddleware(runtime, invocation_traces)
    return create_agent(
        model=model,
        tools=wrapper.tools,
        middleware=(middleware,),
        system_prompt=CORPUS_AGENT_PROMPT,
        context_schema=RouteDeckInvocationContext,
        name="corpus_agent",
    )


def create_corpus_entry_agent(
    *,
    model: BaseChatModel,
    runtime: RouteDeckRunnerRuntime,
    invocation_traces: RouteDeckInvocationTraceRecorder,
) -> Any:
    middleware = RouteDeckMiddleware(runtime, invocation_traces)
    return create_agent(
        model=model,
        tools=(),
        middleware=(middleware,),
        system_prompt=CORPUS_AGENT_PROMPT,
        context_schema=RouteDeckInvocationContext,
        name="corpus_entry_agent",
    )


__all__ = [
    "CorpusRouteDeckMiddleware",
    "create_corpus_agent",
    "create_corpus_entry_agent",
    "should_enter_product_help",
]
