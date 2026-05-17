from __future__ import annotations

from typing import Any

from routedeck_langgraph import build_route_deck_state_graph

from .action_gate import route_action_error
from .graph_runtime import EntryRuntimeState
from .route_conditions import EDGE_CONDITION_RESOLVERS, assert_route_deck_transition
from .stage_auth import bootstrap_node, display_name_node, email_node, intent_node, password_node
from .stage_io import StageHandler, execute_stage
from .stage_saas_agent import (
    connection_confirm_node,
    operator_ready_node,
    setup_intro_node,
    saas_agent_confirm_node,
    saas_agent_job_node,
    saas_agent_select_node,
)
from backend.services.route_deck import build_route_deck_manifest

NODE_HANDLERS = {
    "bootstrap": bootstrap_node,
    "intent": intent_node,
    "display_name": display_name_node,
    "email": email_node,
    "password": password_node,
    "saas_agent_select": saas_agent_select_node,
    "saas_agent_job": saas_agent_job_node,
    "saas_agent_confirm": saas_agent_confirm_node,
    "setup_intro": setup_intro_node,
    "connection_confirm": connection_confirm_node,
    "operator_ready": operator_ready_node,
}

ENTRY_GRAPH_GROUPS = {
    "public_entry": {"bootstrap", "intent"},
    "auth": {"display_name", "email", "password"},
    "saas_agent": {"saas_agent_select", "saas_agent_job", "saas_agent_confirm"},
    "setup": {"setup_intro", "connection_confirm"},
    "terminal": {"operator_ready"},
}

NODE_TO_GROUP = {
    stage_id: group_id
    for group_id, stage_ids in ENTRY_GRAPH_GROUPS.items()
    for stage_id in stage_ids
}


def _resolve_graph_node(state: EntryRuntimeState) -> str:
    stage_id = state.get("active_stage_id") or state.get("node") or "bootstrap"
    if stage_id not in NODE_HANDLERS:
        return "bootstrap"
    return stage_id


def _turn_start_node(state: EntryRuntimeState) -> dict[str, Any]:
    stage_id = state.get("node") or "bootstrap"
    if stage_id not in NODE_HANDLERS:
        stage_id = "bootstrap"
    return {
        "active_stage_id": stage_id,
        "route_group": NODE_TO_GROUP[stage_id],
        "route_error": None,
        "transition_diagnostics": {
            "phase": "turn_start",
            "active_stage_id": stage_id,
            "route_group": NODE_TO_GROUP[stage_id],
        },
    }


def _route_action_node(state: EntryRuntimeState) -> dict[str, Any]:
    stage_id = _resolve_graph_node(state)
    return {
        "active_stage_id": stage_id,
        "route_group": NODE_TO_GROUP[stage_id],
        "route_error": route_action_error(stage_id, state),
    }


def _finalize_turn_node(state: EntryRuntimeState) -> dict[str, Any]:
    from_stage = state.get("active_stage_id") or "bootstrap"
    to_stage = state.get("node") or from_stage
    transition = assert_route_deck_transition(
        from_stage=from_stage,
        to_stage=to_stage,
        state=state,
    )
    return {
        "transition_diagnostics": {
            **(state.get("transition_diagnostics") or {}),
            **transition,
            "phase": "finalize_turn",
        }
    }


def build_entry_graph():
    stage_nodes = {}
    for stage_id, handler in NODE_HANDLERS.items():
        def _async_stage_node(stage_id: str, handler: StageHandler) -> StageHandler:
            async def node(state: EntryRuntimeState) -> dict[str, Any]:
                return await execute_stage(stage_id, handler, state)

            return node
        stage_nodes[stage_id] = _async_stage_node(stage_id, handler)

    graph = build_route_deck_state_graph(
        manifest=build_route_deck_manifest(),
        state_schema=EntryRuntimeState,
        handlers=stage_nodes,
        condition_resolvers=EDGE_CONDITION_RESOLVERS,
        groups=ENTRY_GRAPH_GROUPS,
        active_node_resolver=_resolve_graph_node,
        turn_start_node=_turn_start_node,
        route_action_node=_route_action_node,
        finalize_node=_finalize_turn_node,
    )

    return graph.compile()


entry_graph_executor = build_entry_graph()
