from __future__ import annotations

from typing import Any

from routedeck_langgraph import assert_route_transition, matching_route_deck_edge as adapter_matching_edge

from backend.services.route_deck import build_route_deck_manifest
from backend.services.route_deck.models import RouteDeckEdgeSpec

from .graph_runtime import EntryRuntimeState


def _resolved_transition(edge: RouteDeckEdgeSpec, state: EntryRuntimeState) -> bool:
    return (state.get("node") or edge.from_stage) == edge.to_stage


EDGE_CONDITION_RESOLVERS: dict[str, Any] = {
    "anonymous_start": _resolved_transition,
    "login_initial_intent": _resolved_transition,
    "register_initial_intent": _resolved_transition,
    "authenticated_many_workspaces": _resolved_transition,
    "authenticated_no_workspaces": _resolved_transition,
    "authenticated_no_workspaces_with_draft": _resolved_transition,
    "authenticated_single_workspace": _resolved_transition,
    "register": _resolved_transition,
    "login": _resolved_transition,
    "cancel_or_back": _resolved_transition,
    "switch_to_login": _resolved_transition,
    "display_name_collected": _resolved_transition,
    "cancel_or_login_back": _resolved_transition,
    "switch_to_register": _resolved_transition,
    "valid_email": _resolved_transition,
    "back_to_email": _resolved_transition,
    "cancel_auth": _resolved_transition,
    "auth_retry": _resolved_transition,
    "workspace_select_canceled": _resolved_transition,
    "workspace_select_back": _resolved_transition,
    "existing_workspace_selected": _resolved_transition,
    "new_workspace_requested": _resolved_transition,
    "workspace_job_canceled": _resolved_transition,
    "workspace_job_back": _resolved_transition,
    "workspace_job_collected": _resolved_transition,
    "back_to_workspace_select": _resolved_transition,
    "back_to_workspace_job": _resolved_transition,
    "workspace_creation_canceled": _resolved_transition,
    "workspace_created": _resolved_transition,
    "setup_requested": _resolved_transition,
    "setup_canceled": _resolved_transition,
    "rest_details_ready": _resolved_transition,
    "setup_skipped": _resolved_transition,
    "back_to_setup": _resolved_transition,
    "connection_activated": _resolved_transition,
    "workspace_context_lost": _resolved_transition,
    "auth_requested_from_operator": _resolved_transition,
}


def missing_route_deck_condition_resolvers() -> list[str]:
    missing: set[str] = set()
    for edge in build_route_deck_manifest().edges:
        if edge.condition and edge.condition not in EDGE_CONDITION_RESOLVERS:
            missing.add(edge.condition)
    return sorted(missing)


def matching_route_deck_edge(
    *,
    from_stage: str,
    to_stage: str,
    state: EntryRuntimeState,
) -> RouteDeckEdgeSpec | None:
    return adapter_matching_edge(
        build_route_deck_manifest(),
        from_node=from_stage,
        to_node=to_stage,
        state=state,
        condition_resolvers=EDGE_CONDITION_RESOLVERS,
    )


def assert_route_deck_transition(
    *,
    from_stage: str,
    to_stage: str,
    state: EntryRuntimeState,
) -> dict[str, Any]:
    diagnostics = assert_route_transition(
        build_route_deck_manifest(),
        from_node=from_stage,
        to_node=to_stage,
        state=state,
        condition_resolvers=EDGE_CONDITION_RESOLVERS,
    )
    return diagnostics.model_dump()
