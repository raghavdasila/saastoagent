from __future__ import annotations

import asyncio

from routedeck_core import RouteDeckDispatchInput, RouteDeckRuntime, RouteDeckRuntimeState

from backend.core.schemas import AppGraphRequest, AppGraphState
from backend.services.app_graph import corpus_graph_runtime
from backend.services.app_graph.routedeck_adapter import SaaStoAgentRouteDeckAdapter


def test_saastoagent_adapter_implements_routedeck_runtime_protocol():
    adapter = SaaStoAgentRouteDeckAdapter(corpus_graph_runtime)

    assert isinstance(adapter, RouteDeckRuntime)


def test_adapter_snapshot_returns_runtime_state_with_graph_state_and_projection():
    adapter = SaaStoAgentRouteDeckAdapter(corpus_graph_runtime)

    state = asyncio.run(
        adapter.snapshot(
            {
                "request": AppGraphRequest(),
                "user": None,
                "db": None,
            }
        )
    )

    assert isinstance(state, RouteDeckRuntimeState)
    assert state.projection.current_context == "lounge"
    assert state.graph_state["node"] == "home"
    assert state.location == "/app/home"


def test_adapter_dispatch_delegates_to_graph_runtime_and_returns_new_projection():
    adapter = SaaStoAgentRouteDeckAdapter(corpus_graph_runtime)

    result = asyncio.run(
        adapter.dispatch(
            RouteDeckDispatchInput(
                operation_id="auth.register",
                graph_state=AppGraphState(node="home").model_dump(mode="json"),
                projection_version=1,
            ),
            {
                "user": None,
                "db": None,
            },
        )
    )

    assert result.accepted is True
    assert result.operation_id == "auth.register"
    assert result.state.graph_state["node"] == "auth_register"
    assert result.state.projection.graph_node == "auth_register"
    assert result.active_surface is not None


def test_adapter_inspect_exposes_read_only_introspection():
    adapter = SaaStoAgentRouteDeckAdapter(corpus_graph_runtime)

    introspection = asyncio.run(
        adapter.inspect(
            context={
                "request": AppGraphRequest(),
                "user": None,
                "db": None,
            }
        )
    )

    assert introspection.current_node == "home"
    assert "auth_register" in introspection.reachable_nodes
    assert introspection.legal_operations
    assert introspection.surfaces
