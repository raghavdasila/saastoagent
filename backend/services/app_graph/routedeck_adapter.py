from __future__ import annotations

from typing import Any, AsyncIterator

from backend.core.models import User
from backend.core.schemas import AppGraphRequest, AppGraphState
from backend.services.app_graph.runtime import CorpusGraphRuntime
from routedeck_core import (
    RouteDeckDispatchInput,
    RouteDeckDispatchResult,
    RouteDeckEvent,
    RouteDeckIntrospection,
    RouteDeckProjection,
    RouteDeckRuntimeState,
    RouteDeckSurface,
)
from sqlalchemy.ext.asyncio import AsyncSession


class SaaStoAgentRouteDeckAdapter:
    def __init__(self, runtime: CorpusGraphRuntime) -> None:
        self._runtime = runtime

    @property
    def manifest(self):
        return self._runtime.manifest

    async def snapshot(self, context: dict[str, Any] | None = None) -> RouteDeckRuntimeState:
        ctx = context or {}
        corpus_state = await self._runtime.corpus_state(
            request=self._request_from_context(ctx),
            user=self._user_from_context(ctx),
            db=self._db_from_context(ctx),
            projection_version=self._projection_version_from_context(ctx),
        )
        return RouteDeckRuntimeState(
            projection=corpus_state.projection,
            status="idle",
            graph_state=corpus_state.state.model_dump(mode="json"),
            location=corpus_state.replace_path,
            diagnostics=corpus_state.projection.diagnostics,
        )

    async def projection(self, context: dict[str, Any] | None = None) -> RouteDeckProjection:
        return (await self.snapshot(context)).projection

    async def dispatch(
        self,
        request: RouteDeckDispatchInput,
        context: dict[str, Any] | None = None,
    ) -> RouteDeckDispatchResult:
        ctx = context or {}
        graph_request = self._request_from_dispatch(request, ctx)
        response = await self._runtime.corpus_action(
            request=graph_request,
            operation_id=request.operation_id,
            args=request.args,
            user=self._user_from_context(ctx),
            db=self._db_from_context(ctx),
            projection_version=request.projection_version or self._projection_version_from_context(ctx),
        )
        runtime_state = RouteDeckRuntimeState(
            projection=response.projection,
            status="idle",
            graph_state=response.state.model_dump(mode="json"),
            location=response.replace_path,
            diagnostics=response.projection.diagnostics,
        )
        return RouteDeckDispatchResult(
            operation_id=request.operation_id,
            accepted=True,
            state=runtime_state,
            active_surface=response.active_surface,
            messages=[message.model_dump(mode="json") for message in response.messages],
            events=[
                RouteDeckEvent(
                    event_type="operation_completed",
                    projection_version=response.projection.projection_version,
                    payload={
                        "operation_id": request.operation_id,
                        "projection": response.projection.model_dump(mode="json"),
                    },
                )
            ],
            metadata={"replace_path": response.replace_path},
        )

    async def inspect(
        self,
        query: dict[str, Any] | None = None,
        context: dict[str, Any] | None = None,
    ) -> RouteDeckIntrospection:
        ctx = {**(context or {}), **(query or {})}
        snapshot = await self._runtime.diagnostics_snapshot(
            request=self._request_from_context(ctx),
            user=self._user_from_context(ctx),
            db=self._db_from_context(ctx),
            projection_version=self._projection_version_from_context(ctx),
        )
        raw = snapshot.introspection
        return RouteDeckIntrospection(
            current_node=raw.get("current_node"),
            reachable_nodes=list(raw.get("reachable_nodes") or []),
            legal_operations=list(raw.get("legal_operations") or []),
            blocked_operations=list(raw.get("blocked_operations") or []),
            guard_explanations=[
                explanation if isinstance(explanation, str) else str(explanation.get("reason") or explanation)
                for explanation in raw.get("guard_explanations") or []
            ],
            surfaces=dict(raw.get("surface_projection") or {}),
            route_traces=[raw.get("route_trace") or {}],
            diagnostics={
                "runtime_snapshot": raw.get("runtime_snapshot") or {},
                "context_lens": raw.get("context_lens") or {},
            },
        )

    async def stream(self, context: dict[str, Any] | None = None) -> AsyncIterator[RouteDeckEvent]:
        state = await self.snapshot(context)
        yield RouteDeckEvent(
            event_type="projection_update",
            projection_version=state.projection.projection_version,
            payload={
                "projection": state.projection.model_dump(mode="json"),
                "state": state.model_dump(mode="json"),
            },
        )

    def _request_from_context(self, context: dict[str, Any]) -> AppGraphRequest:
        request = context.get("request")
        if isinstance(request, AppGraphRequest):
            return request
        return AppGraphRequest(
            node_id=context.get("node_id"),
            saas_agent_id=context.get("saas_agent_id"),
            user_input=context.get("user_input"),
        )

    def _request_from_dispatch(self, request: RouteDeckDispatchInput, context: dict[str, Any]) -> AppGraphRequest:
        state = self._state_from_graph_state(request.graph_state)
        return AppGraphRequest(
            state=state,
            node_id=context.get("node_id") or state.node,
            saas_agent_id=context.get("saas_agent_id") or state.active_saas_agent_id,
        )

    def _state_from_graph_state(self, graph_state: dict[str, Any]) -> AppGraphState:
        if graph_state:
            return AppGraphState.model_validate(graph_state)
        return AppGraphState()

    def _user_from_context(self, context: dict[str, Any]) -> User | None:
        user = context.get("user")
        return user if isinstance(user, User) else None

    def _db_from_context(self, context: dict[str, Any]) -> AsyncSession:
        return context.get("db")

    def _projection_version_from_context(self, context: dict[str, Any]) -> int:
        raw = context.get("projection_version")
        return raw if isinstance(raw, int) and raw >= 1 else 1
