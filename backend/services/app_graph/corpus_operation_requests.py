from __future__ import annotations

from typing import Any

from fastapi import HTTPException, status

from backend.core.schemas import AppGraphNavigationLocation, AppGraphState
from backend.services.app_graph.corpus_routedeck_navigation import (
    NAV_PARAM_PENDING_OPERATION_ARGS,
    NAV_PARAM_PENDING_OPERATION_ID,
    CorpusRouteDeckNavigation,
)
from backend.services.app_graph.corpus_surfaces import CorpusSurfaceRegistry
from backend.services.app_graph.manifest import AppActionIds
from routedeck_core import RouteDeckOperation, RouteDeckProjection


class CorpusOperationRequests:
    """Validates operation request payloads and builds review-operation state."""

    def __init__(
        self,
        *,
        navigation: CorpusRouteDeckNavigation,
        surface_registry: CorpusSurfaceRegistry,
    ) -> None:
        self._navigation = navigation
        self._surface_registry = surface_registry

    def validated_payload(
        self,
        *,
        state: AppGraphState,
        operation: RouteDeckOperation,
        args: dict[str, Any] | None,
        projection: RouteDeckProjection,
    ) -> dict[str, Any]:
        if operation.id == AppActionIds.ROUTE_OPEN_NODE:
            return self._validated_route_open_node_args(
                state=state,
                projection=projection,
                args=args,
            )
        if operation.id == AppActionIds.ROUTE_SWITCH_SURFACE:
            return self._validated_route_switch_surface_args(
                state=state,
                projection=projection,
                args=args,
            )
        if operation.id in {AppActionIds.ROUTE_BACK, AppActionIds.ROUTE_FORWARD, AppActionIds.ROUTE_CANCEL}:
            return {}
        return self._sanitize_operation_args(operation, args)

    def review_state_for_operation(
        self,
        *,
        state: AppGraphState,
        operation: RouteDeckOperation,
        args: dict[str, Any],
    ) -> AppGraphState:
        review_state = state.model_copy(deep=True)
        current_location = self._navigation.current_location(review_state)
        review_params = dict(current_location.params)
        review_params[NAV_PARAM_PENDING_OPERATION_ID] = operation.id
        if args:
            review_params[NAV_PARAM_PENDING_OPERATION_ARGS] = dict(args)
        else:
            review_params.pop(NAV_PARAM_PENDING_OPERATION_ARGS, None)
        review_location = AppGraphNavigationLocation(
            node_id=review_state.node,
            surface_id=self._surface_registry.operation_review_surface_id(operation.id),
            params=review_params,
        )
        self._navigation.apply_location(review_state, review_location)
        self._navigation.push_navigation(review_state, current_location)
        if review_state.node not in review_state.executed_nodes:
            review_state.executed_nodes.append(review_state.node)
        return review_state

    def _sanitize_operation_args(
        self,
        operation: RouteDeckOperation,
        args: dict[str, Any] | None,
    ) -> dict[str, Any]:
        if not isinstance(args, dict):
            return {}
        input_schema = operation.input_schema if isinstance(operation.input_schema, dict) else {}
        fields = input_schema.get("fields")
        if not isinstance(fields, list):
            return {}
        accepted_keys = [
            field.get("key")
            for field in fields
            if isinstance(field, dict) and isinstance(field.get("key"), str)
        ]
        return {
            key: args[key]
            for key in accepted_keys
            if isinstance(key, str) and key in args
        }

    def _validated_route_open_node_args(
        self,
        *,
        state: AppGraphState,
        projection: RouteDeckProjection,
        args: dict[str, Any] | None,
    ) -> dict[str, Any]:
        payload = args if isinstance(args, dict) else {}
        node_id = payload.get("node_id")
        if not isinstance(node_id, str) or not node_id:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="route.open_node requires a legal node_id")

        allowed_node_ids = self._navigation.legal_target_node_ids_from_projection(projection, state)
        if node_id not in allowed_node_ids:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="route.open_node target is not legal from the current graph state")

        normalized: dict[str, Any] = {"node_id": node_id}
        current_location = self._navigation.current_location(state)
        known_location = self._navigation.known_navigation_location(state, node_id)
        surface_id = payload.get("surface_id")

        if node_id == current_location.node_id:
            normalized["params"] = dict(current_location.params)
            if surface_id is None:
                return normalized
            if not isinstance(surface_id, str) or surface_id not in self._navigation.active_surface_ids(projection):
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="route.open_node surface_id is not legal on the current node")
            normalized["surface_id"] = surface_id
            return normalized

        normalized["params"] = dict(known_location.params) if known_location else {}
        if surface_id is None:
            if known_location and known_location.surface_id:
                normalized["surface_id"] = known_location.surface_id
            return normalized

        if not isinstance(surface_id, str):
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="route.open_node surface_id must be a string")
        expected_surface_id = known_location.surface_id if known_location else self._surface_registry.default_surface_id(
            AppGraphState(
                node=node_id,
                active_saas_agent_id=state.active_saas_agent_id,
            )
        )
        if not expected_surface_id or surface_id != expected_surface_id:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="route.open_node surface_id is not legal for the requested node")
        normalized["surface_id"] = surface_id
        return normalized

    def _validated_route_switch_surface_args(
        self,
        *,
        state: AppGraphState,
        projection: RouteDeckProjection,
        args: dict[str, Any] | None,
    ) -> dict[str, Any]:
        payload = args if isinstance(args, dict) else {}
        surface_id = payload.get("surface_id")
        if not isinstance(surface_id, str) or surface_id not in self._navigation.active_surface_ids(projection):
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="route.switch_surface requires a projected active surface_id")
        node_id = payload.get("node_id")
        if node_id is not None and node_id != state.node:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="route.switch_surface must stay on the current node")
        return {
            "node_id": state.node,
            "surface_id": surface_id,
            "params": dict(self._navigation.current_location(state).params),
        }
