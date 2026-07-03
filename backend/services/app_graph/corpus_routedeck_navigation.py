from __future__ import annotations

import uuid
from collections.abc import Mapping
from typing import Any

from backend.core.schemas import AppGraphNavigationLocation, AppGraphState
from backend.services.app_graph.corpus_surfaces import CorpusSurfaceRegistry
from routedeck_core import (
    ROUTEDECK_PENDING_OPERATION_ARGS_PARAM,
    ROUTEDECK_PENDING_OPERATION_ID_PARAM,
    RouteDeckGraphNavigationController,
    RouteDeckNavigationPolicy,
)


NAV_PARAM_PENDING_OPERATION_ID = ROUTEDECK_PENDING_OPERATION_ID_PARAM
NAV_PARAM_PENDING_OPERATION_ARGS = ROUTEDECK_PENDING_OPERATION_ARGS_PARAM
NAV_PARAM_SAAS_AGENT_ID = "saas_agent_id"


class CorpusRouteDeckNavigation(RouteDeckGraphNavigationController):
    """Corpus-specific history params on top of RouteDeck navigation."""

    def __init__(
        self,
        *,
        surface_registry: CorpusSurfaceRegistry,
        node_by_id: Mapping[str, Any],
        policy: RouteDeckNavigationPolicy | None = None,
    ) -> None:
        super().__init__(
            surface_registry=surface_registry,
            node_by_id=node_by_id,
            policy=policy,
            location_factory=AppGraphNavigationLocation,
        )

    def extra_history_params(self, state: AppGraphState) -> Mapping[str, Any]:
        if not state.active_saas_agent_id:
            return {}
        return {NAV_PARAM_SAAS_AGENT_ID: str(state.active_saas_agent_id)}

    def apply_extra_history_params(self, state: AppGraphState, params: dict[str, Any]) -> None:
        raw_saas_agent_id = params.pop(NAV_PARAM_SAAS_AGENT_ID, None)
        if not raw_saas_agent_id:
            return
        try:
            state.active_saas_agent_id = uuid.UUID(str(raw_saas_agent_id))
        except (TypeError, ValueError):
            return

    def cancel_target_location(self, state: AppGraphState) -> AppGraphNavigationLocation | None:
        node = self._node_by_id.get(state.node)
        cancel_target_node = getattr(node, "cancel_target_node", None) if node else None
        if cancel_target_node:
            params: dict[str, Any] = {}
            if state.active_saas_agent_id:
                params[NAV_PARAM_SAAS_AGENT_ID] = str(state.active_saas_agent_id)
            return self.make_location(
                node_id=cancel_target_node,
                surface_id=self._surface_registry.default_surface_id_for(cancel_target_node),
                params=params,
            )
        return state.navigation_back_stack[-1] if state.navigation_back_stack else None
