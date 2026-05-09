from __future__ import annotations

from typing import Any

from langgraph.graph import END, StateGraph

from .graph_runtime import EntryRuntimeState
from .graph_spec import ENTRY_NODE_SPECS
from .stage_auth import bootstrap_node, display_name_node, email_node, intent_node, password_node
from .stage_io import execute_stage
from .stage_workspace import (
    connection_confirm_node,
    operator_ready_node,
    setup_intro_node,
    workspace_confirm_node,
    workspace_job_node,
    workspace_select_node,
)

NODE_HANDLERS = {
    "bootstrap": bootstrap_node,
    "intent": intent_node,
    "display_name": display_name_node,
    "email": email_node,
    "password": password_node,
    "workspace_select": workspace_select_node,
    "workspace_job": workspace_job_node,
    "workspace_confirm": workspace_confirm_node,
    "setup_intro": setup_intro_node,
    "connection_confirm": connection_confirm_node,
    "operator_ready": operator_ready_node,
}


def _resolve_graph_node(state: EntryRuntimeState) -> str:
    return state.get("node") or "bootstrap"


def _dispatch_node(_: EntryRuntimeState) -> dict[str, Any]:
    return {}


def build_entry_graph():
    graph = StateGraph(EntryRuntimeState)
    graph.add_node("dispatch", _dispatch_node)

    for stage_id, handler in NODE_HANDLERS.items():
        def _async_stage_node(stage_id: str, handler: StageHandler) -> StageHandler:
            async def node(state: EntryRuntimeState) -> dict[str, Any]:
                return await execute_stage(stage_id, handler, state)

            return node
        graph.add_node(stage_id, _async_stage_node(stage_id, handler))

    graph.set_entry_point("dispatch")
    graph.add_conditional_edges(
        "dispatch",
        _resolve_graph_node,
        {stage_id.value: stage_id.value for stage_id in ENTRY_NODE_SPECS.keys()},
    )

    for stage_id in ENTRY_NODE_SPECS.keys():
        graph.add_edge(stage_id.value, END)

    return graph.compile()


entry_graph_executor = build_entry_graph()
