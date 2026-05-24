from __future__ import annotations

import asyncio

from routedeck_core import RouteDeckDispatchInput, RouteDeckRuntime, RouteDeckRuntimeState

from backend.core.schemas import AppGraphRequest, AppGraphState
from backend.routes.corpus_graph import (
    _corpus_action_response_from_routedeck_result,
    _corpus_state_response_from_routedeck_state,
)
from backend.services.app_graph import corpus_graph_runtime
from backend.services.app_graph.corpus_routedeck_runtime import CorpusRouteDeckRuntime


def test_corpus_routedeck_runtime_implements_protocol():
    runtime = CorpusRouteDeckRuntime(corpus_graph_runtime)

    assert isinstance(runtime, RouteDeckRuntime)


def test_corpus_routedeck_runtime_snapshot_preserves_current_state_contract():
    runtime = CorpusRouteDeckRuntime(corpus_graph_runtime)

    state = asyncio.run(runtime.snapshot({"request": AppGraphRequest(), "user": None, "db": None}))

    assert isinstance(state, RouteDeckRuntimeState)
    assert state.projection.current_context == "lounge"
    assert state.graph_state["node"] == "home"
    assert state.location == "/app/home"


def test_corpus_routedeck_runtime_dispatch_preserves_current_contract():
    runtime = CorpusRouteDeckRuntime(corpus_graph_runtime)

    result = asyncio.run(
        runtime.dispatch(
            RouteDeckDispatchInput(
                operation_id="auth.register",
                graph_state=AppGraphState(node="home").model_dump(mode="json"),
                projection_version=1,
            ),
            {"user": None, "db": None},
        )
    )

    assert result.accepted is True
    assert result.operation_id == "auth.register"
    assert result.state.graph_state["node"] == "auth_register"
    assert result.active_surface is not None
    assert result.active_surface.component == "CorpusAuthSurface"


def test_corpus_routedeck_runtime_inspect_preserves_read_only_introspection():
    runtime = CorpusRouteDeckRuntime(corpus_graph_runtime)

    introspection = asyncio.run(runtime.inspect(context={"request": AppGraphRequest(), "user": None, "db": None}))

    assert introspection.current_node == "home"
    assert "auth_register" in introspection.reachable_nodes
    assert introspection.legal_operations
    assert introspection.surfaces


def test_corpus_routedeck_runtime_stream_emits_projection_update():
    runtime = CorpusRouteDeckRuntime(corpus_graph_runtime)

    async def collect():
        return [event async for event in runtime.stream({"request": AppGraphRequest(), "user": None, "db": None})]

    events = asyncio.run(collect())

    assert [event.event_type for event in events] == ["projection_update"]
    assert events[0].payload["projection"]["graph_node"] == "home"


def test_corpus_state_route_conversion_preserves_routedeck_runtime_state():
    runtime = CorpusRouteDeckRuntime(corpus_graph_runtime)
    state = asyncio.run(runtime.snapshot({"request": AppGraphRequest(), "user": None, "db": None}))

    response = _corpus_state_response_from_routedeck_state(state)

    assert response.state.node == "home"
    assert response.projection.graph_node == "home"
    assert response.projection.projection_version == state.projection.projection_version
    assert response.replace_path == "/app/home"


def test_corpus_action_route_conversion_preserves_routedeck_dispatch_result():
    runtime = CorpusRouteDeckRuntime(corpus_graph_runtime)
    result = asyncio.run(
        runtime.dispatch(
            RouteDeckDispatchInput(
                operation_id="auth.register",
                graph_state=AppGraphState(node="home").model_dump(mode="json"),
                projection_version=1,
            ),
            {"user": None, "db": None},
        )
    )

    response = _corpus_action_response_from_routedeck_result(result)

    assert response.state.node == "auth_register"
    assert response.projection.graph_node == "auth_register"
    assert response.projection.projection_version == result.state.projection.projection_version
    assert response.replace_path == result.metadata["replace_path"]
    assert response.active_surface == result.active_surface
    assert [message.model_dump(mode="json") for message in response.messages] == result.messages
