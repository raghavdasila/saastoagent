from __future__ import annotations

import uuid
from typing import Any, Mapping

from backend.core.schemas import AppGraphNavigationLocation, AppGraphState
from backend.services.app_graph.corpus_surfaces import CorpusSurfaceRegistry
from routedeck_core import (
    RouteDeckLocation,
    RouteDeckNavigationPolicy,
    RouteDeckProjection,
    RouteDeckSurface,
)


NAV_PARAM_PENDING_OPERATION_ID = "__pending_operation_id"
NAV_PARAM_PENDING_OPERATION_ARGS = "__pending_operation_args"
NAV_PARAM_SAAS_AGENT_ID = "saas_agent_id"


class CorpusRouteDeckNavigation:
    """Corpus adapter around reusable RouteDeck navigation mechanics."""

    def __init__(
        self,
        *,
        surface_registry: CorpusSurfaceRegistry,
        node_by_id: Mapping[str, Any],
        policy: RouteDeckNavigationPolicy | None = None,
    ) -> None:
        self._surface_registry = surface_registry
        self._node_by_id = node_by_id
        self._policy = policy or RouteDeckNavigationPolicy()

    def active_surface_ids(self, projection: RouteDeckProjection) -> set[str]:
        return self._policy.active_surface_ids(projection)

    def legal_target_node_ids_from_projection(self, projection: RouteDeckProjection, state: AppGraphState) -> set[str]:
        return self._policy.legal_target_node_ids(
            projection=projection,
            current_node=state.node,
            back_stack=state.navigation_back_stack,
            forward_stack=state.navigation_forward_stack,
        )

    def known_navigation_location(
        self,
        state: AppGraphState,
        node_id: str,
    ) -> AppGraphNavigationLocation | None:
        location = self._policy.known_navigation_location(
            node_id=node_id,
            back_stack=state.navigation_back_stack,
            forward_stack=state.navigation_forward_stack,
        )
        return self.app_location_from_route_deck(location) if location else None

    def resolved_surface_id(self, state: AppGraphState) -> str | None:
        review_surface_id = self._surface_registry.operation_id_from_surface_id(state.active_surface_id)
        if review_surface_id and state.pending_operation_id != review_surface_id:
            return self._surface_registry.default_surface_id(state)
        return state.active_surface_id or self._surface_registry.default_surface_id(state)

    def history_params_for_state(self, state: AppGraphState) -> dict[str, Any]:
        params = dict(state.route_params or {})
        if state.active_saas_agent_id:
            params[NAV_PARAM_SAAS_AGENT_ID] = str(state.active_saas_agent_id)
        if state.pending_operation_id:
            params[NAV_PARAM_PENDING_OPERATION_ID] = state.pending_operation_id
        if state.pending_operation_args:
            params[NAV_PARAM_PENDING_OPERATION_ARGS] = dict(state.pending_operation_args)
        return params

    def current_location(self, state: AppGraphState) -> AppGraphNavigationLocation:
        return AppGraphNavigationLocation(
            node_id=state.node,
            surface_id=self.resolved_surface_id(state),
            params=self.history_params_for_state(state),
        )

    def app_location_from_route_deck(self, location: RouteDeckLocation) -> AppGraphNavigationLocation:
        return AppGraphNavigationLocation(
            node_id=location.node_id,
            surface_id=location.surface_id,
            params=dict(location.params),
        )

    def app_locations_from_route_deck(self, locations: list[RouteDeckLocation]) -> list[AppGraphNavigationLocation]:
        return [self.app_location_from_route_deck(location) for location in locations]

    def location_from_payload(
        self,
        state: AppGraphState,
        payload: Mapping[str, Any],
        *,
        preserve_current_params: bool = False,
    ) -> AppGraphNavigationLocation:
        return self.app_location_from_route_deck(
            self._policy.location_from_payload(
                current=self.current_location(state),
                payload=payload,
                preserve_current_params=preserve_current_params,
            )
        )

    def apply_location(self, state: AppGraphState, location: AppGraphNavigationLocation) -> None:
        params = dict(location.params or {})
        pending_operation_id = params.pop(NAV_PARAM_PENDING_OPERATION_ID, None)
        pending_operation_args = params.pop(NAV_PARAM_PENDING_OPERATION_ARGS, {})
        raw_saas_agent_id = params.pop(NAV_PARAM_SAAS_AGENT_ID, None)

        state.node = location.node_id
        state.route_params = params
        state.pending_operation_id = str(pending_operation_id) if pending_operation_id else None
        state.pending_operation_args = pending_operation_args if isinstance(pending_operation_args, dict) else {}
        state.active_surface_id = location.surface_id or self._surface_registry.default_surface_id(state)
        if raw_saas_agent_id:
            try:
                state.active_saas_agent_id = uuid.UUID(str(raw_saas_agent_id))
            except (ValueError, TypeError):
                pass

    def push_navigation(self, state: AppGraphState, previous: AppGraphNavigationLocation) -> None:
        current_stack = [
            self._policy.location_from(location)
            for location in state.navigation_back_stack
        ]
        updated_stack = self._policy.pushed_back_stack(
            current=self.current_location(state),
            previous=previous,
            back_stack=state.navigation_back_stack,
        )
        if updated_stack == current_stack:
            return
        state.navigation_back_stack = self.app_locations_from_route_deck(updated_stack)
        state.navigation_forward_stack = []

    def cancel_target_location(self, state: AppGraphState) -> AppGraphNavigationLocation | None:
        node = self._node_by_id.get(state.node)
        cancel_target_node = getattr(node, "cancel_target_node", None) if node else None
        if cancel_target_node:
            params: dict[str, Any] = {}
            if state.active_saas_agent_id:
                params[NAV_PARAM_SAAS_AGENT_ID] = str(state.active_saas_agent_id)
            return AppGraphNavigationLocation(
                node_id=cancel_target_node,
                surface_id=self._surface_registry.default_surface_id(AppGraphState(node=cancel_target_node)),
                params=params,
            )
        return state.navigation_back_stack[-1] if state.navigation_back_stack else None

    def active_surface_from_projection(self, projection: RouteDeckProjection) -> RouteDeckSurface | None:
        return self._policy.active_surface_from_projection(projection)

    def apply_transition(self, state: AppGraphState, transition) -> None:
        state.navigation_back_stack = self.app_locations_from_route_deck(transition.back_stack)
        state.navigation_forward_stack = self.app_locations_from_route_deck(transition.forward_stack)
        self.apply_location(state, self.app_location_from_route_deck(transition.target))

    def move_back(self, state: AppGraphState) -> bool:
        transition = self._policy.back_transition(
            current=self.current_location(state),
            back_stack=state.navigation_back_stack,
            forward_stack=state.navigation_forward_stack,
        )
        if transition is None:
            return False
        self.apply_transition(state, transition)
        return True

    def move_forward(self, state: AppGraphState) -> bool:
        transition = self._policy.forward_transition(
            current=self.current_location(state),
            back_stack=state.navigation_back_stack,
            forward_stack=state.navigation_forward_stack,
        )
        if transition is None:
            return False
        self.apply_transition(state, transition)
        return True

    def cancel(self, state: AppGraphState) -> bool:
        transition = self._policy.cancel_transition(
            current=self.current_location(state),
            target=self.cancel_target_location(state),
            back_stack=state.navigation_back_stack,
            forward_stack=state.navigation_forward_stack,
        )
        if transition is None:
            return False
        self.apply_transition(state, transition)
        return True

    def open_node(self, state: AppGraphState, payload: Mapping[str, Any]) -> None:
        transition = self._policy.open_transition(
            current=self.current_location(state),
            target=self.location_from_payload(state, payload, preserve_current_params=False),
            back_stack=state.navigation_back_stack,
        )
        self.apply_transition(state, transition)

    def switch_surface(self, state: AppGraphState, payload: Mapping[str, Any]) -> None:
        target = self.location_from_payload(state, payload, preserve_current_params=True)
        if state.pending_operation_id and target.surface_id != self._surface_registry.operation_review_surface_id(state.pending_operation_id):
            target.params.pop(NAV_PARAM_PENDING_OPERATION_ID, None)
            target.params.pop(NAV_PARAM_PENDING_OPERATION_ARGS, None)
        transition = self._policy.open_transition(
            current=self.current_location(state),
            target=target,
            back_stack=state.navigation_back_stack,
        )
        self.apply_transition(state, transition)
