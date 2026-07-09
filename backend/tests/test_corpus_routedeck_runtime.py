from __future__ import annotations

import asyncio

from routedeck_core import RouteDeckDispatchInput, RouteDeckRuntime, RouteDeckRuntimeState

from backend.core.schemas import CorpusGraphRequest, CorpusGraphState
from backend.routes.corpus_graph import (
    _corpus_action_response_from_routedeck_result,
    _corpus_state_response_from_routedeck_state,
)
from backend.services.corpus.corpus_app import corpus_route_deck_app


def _runtime():
    return corpus_route_deck_app.compile()


def test_corpus_routedeck_runtime_implements_protocol():
    runtime = _runtime()

    assert isinstance(runtime, RouteDeckRuntime)


def test_corpus_routedeck_runtime_snapshot_preserves_current_state_contract():
    runtime = _runtime()

    state = asyncio.run(runtime.snapshot({"request": CorpusGraphRequest(), "user": None, "db": None}))

    assert isinstance(state, RouteDeckRuntimeState)
    assert state.projection.current_context == "lounge"
    assert state.graph_state["node"] == "home"
    assert state.location == "/app/home"


def test_corpus_routedeck_runtime_projects_context_lens_as_first_class_projection_context():
    runtime = _runtime()

    state = asyncio.run(runtime.snapshot({"request": CorpusGraphRequest(), "user": None, "db": None}))

    assert state.projection.context_lens is not None
    assert state.projection.context_lens.current_node == "home"
    assert state.projection.context_lens.active_surface_id == state.projection.navigation.current.surface_id
    assert state.projection.context_lens.legal_operation_ids == [
        operation.id for operation in state.projection.legal_operations
    ]


def test_corpus_routedeck_runtime_dispatch_preserves_current_contract():
    runtime = _runtime()

    result = asyncio.run(
        runtime.dispatch(
            RouteDeckDispatchInput(
                operation_id="auth.register",
                graph_state=CorpusGraphState(node="home").model_dump(mode="json"),
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
    runtime = _runtime()

    introspection = asyncio.run(runtime.inspect(context={"request": CorpusGraphRequest(), "user": None, "db": None}))

    assert introspection.current_node == "home"
    assert "auth_register" in introspection.reachable_nodes
    assert introspection.legal_operations
    assert introspection.surfaces


def test_corpus_routedeck_runtime_stream_emits_projection_update():
    runtime = _runtime()

    async def collect():
        return [event async for event in runtime.stream({"request": CorpusGraphRequest(), "user": None, "db": None})]

    events = asyncio.run(collect())

    assert [event.event_type for event in events] == ["projection_update"]
    assert events[0].payload["projection"]["graph_node"] == "home"


def test_corpus_routedeck_runtime_stream_turn_dispatches_operation_via_routedeck_runtime():
    runtime = _runtime()

    async def fake_plan(*, api_key, user_input, planning_context):
        return {
            "intent": "propose_operation",
            "message": "Opening registration.",
            "operation_id": "auth.register",
            "args": {},
            "surface_intent": {},
            "confidence": 1.0,
            "preamble": None,
        }

    async def fake_operation_message(**kwargs):
        yield "Registration is ready."

    runtime._corpus_turn_plan = fake_plan
    runtime._stream_corpus_operation_message = fake_operation_message

    async def collect():
        return [
            event
            async for event in runtime.stream_corpus_turn(
                request=CorpusGraphRequest(user_input="create account"),
                user=None,
                db=None,
                projection_version=1,
                openai_api_key="test-key",
            )
        ]

    events = asyncio.run(collect())

    assert [event["event_type"] for event in events] == [
        "corpus_status",
        "operation_completed",
        "message_delta",
        "corpus_done",
    ]
    assert events[1]["payload"]["state"]["node"] == "auth_register"
    assert events[1]["payload"]["active_surface"]["component"] == "CorpusAuthSurface"
    assert (
        events[1]["payload"]["state"]["active_surface_id"]
        == events[1]["payload"]["projection"]["navigation"]["current"]["surface_id"]
    )


def test_corpus_state_route_conversion_preserves_routedeck_runtime_state():
    runtime = _runtime()
    state = asyncio.run(runtime.snapshot({"request": CorpusGraphRequest(), "user": None, "db": None}))

    response = _corpus_state_response_from_routedeck_state(state)

    assert response.state.node == "home"
    assert response.projection.graph_node == "home"
    assert response.projection.projection_version == state.projection.projection_version
    assert response.replace_path == "/app/home"


def test_corpus_action_route_conversion_preserves_routedeck_dispatch_result():
    runtime = _runtime()
    result = asyncio.run(
        runtime.dispatch(
            RouteDeckDispatchInput(
                operation_id="auth.register",
                graph_state=CorpusGraphState(node="home").model_dump(mode="json"),
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
