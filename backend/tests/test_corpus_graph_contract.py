from __future__ import annotations

import asyncio

from routedeck_core import RouteDeckDispatchInput, RouteDeckRuntime

import backend.corpus.graph as app_graph
from backend.corpus.schemas import CorpusGraphRequest, CorpusGraphState
from backend.corpus.graph import route_deck_runtime
from backend.corpus.graph.definitions import CorpusActionIds


def test_corpus_runtime_owner_is_routedeck_runtime_not_legacy_graph_runtime():
    assert isinstance(route_deck_runtime, RouteDeckRuntime)
    assert app_graph.route_deck_runtime is route_deck_runtime
    assert not hasattr(app_graph, "corpus_graph_runtime")
    assert not hasattr(route_deck_runtime, "corpus_state")
    assert not hasattr(route_deck_runtime, "corpus_action")
    assert not hasattr(route_deck_runtime, "route_deck_projection")


def test_corpus_home_projection_is_route_deck_runtime_projection():
    projection = asyncio.run(
        route_deck_runtime.projection(
            {"request": CorpusGraphRequest(), "user": None, "db": None}
        )
    )

    assert projection.current_context == "lounge"
    assert projection.graph_node == "home"
    assert projection.surfaces["main"].component == "CorpusLoungeSurface"
    assert "side" not in projection.surfaces
    assert projection.context_lens is not None
    assert projection.context_lens.current_node == "home"
    assert {operation.id for operation in projection.legal_operations} >= {
        CorpusActionIds.AUTH_SIGN_IN,
        CorpusActionIds.AUTH_REGISTER,
        CorpusActionIds.ROUTE_OPEN_NODE,
        CorpusActionIds.ROUTE_SWITCH_SURFACE,
    }


def test_routedeck_dispatch_owns_route_navigation():
    state = CorpusGraphState(node="home")

    result = asyncio.run(
        route_deck_runtime.dispatch(
            RouteDeckDispatchInput(
                operation_id=CorpusActionIds.ROUTE_OPEN_NODE,
                args={"node_id": "auth_sign_in"},
                graph_state=state.model_dump(mode="json"),
                projection_version=1,
            ),
            {"user": None, "db": None},
        )
    )

    assert result.accepted is True
    assert result.operation_id == CorpusActionIds.ROUTE_OPEN_NODE
    assert result.state.graph_state["node"] == "auth_sign_in"
    assert result.active_surface is not None
    assert result.active_surface.component == "CorpusAuthSurface"
    assert result.state.graph_state["navigation_back_stack"][-1]["node_id"] == "home"


def test_routedeck_dispatch_owns_business_action_surface_and_navigation_cleanup():
    state = CorpusGraphState(node="home")

    result = asyncio.run(
        route_deck_runtime.dispatch(
            RouteDeckDispatchInput(
                operation_id=CorpusActionIds.AUTH_REGISTER,
                graph_state=state.model_dump(mode="json"),
                projection_version=1,
            ),
            {"user": None, "db": None},
        )
    )

    assert result.accepted is True
    assert result.operation_id == CorpusActionIds.AUTH_REGISTER
    assert result.state.graph_state["node"] == "auth_register"
    assert result.state.graph_state["pending_operation_id"] is None
    assert result.state.graph_state["pending_operation_args"] == {}
    assert result.active_surface is not None
    assert result.active_surface.component == "CorpusAuthSurface"
    assert result.state.graph_state["navigation_back_stack"][-1]["node_id"] == "home"


def test_review_surface_ids_are_not_rehydrated_without_pending_operation_state():
    stale_review_state = CorpusGraphState(
        node="home",
        active_surface_id="operation_review.saas_agent.create",
    )

    runtime_state = asyncio.run(
        route_deck_runtime.snapshot(
            {
                "request": CorpusGraphRequest(state=stale_review_state),
                "user": None,
                "db": None,
            }
        )
    )

    assert runtime_state.projection.navigation.current.surface_id != "operation_review.saas_agent.create"
    assert runtime_state.graph_state["pending_operation_id"] is None


def test_corpus_stream_turn_commits_selected_operation_through_routedeck_dispatch():
    async def fake_plan(*, api_key, user_input, planning_context):
        return {
            "intent": "propose_operation",
            "message": "Opening registration.",
            "operation_id": CorpusActionIds.AUTH_REGISTER,
            "args": {},
            "surface_intent": {},
            "confidence": 1.0,
            "preamble": None,
        }

    async def fake_operation_message(**kwargs):
        yield "Registration is ready."

    original_plan = route_deck_runtime._corpus_turn_plan
    original_operation_message = route_deck_runtime._stream_corpus_operation_message
    route_deck_runtime._corpus_turn_plan = fake_plan
    route_deck_runtime._stream_corpus_operation_message = fake_operation_message
    try:
        async def collect():
            return [
                event
                async for event in route_deck_runtime.stream_corpus_turn(
                    request=CorpusGraphRequest(user_input="create account"),
                    user=None,
                    db=None,
                    projection_version=1,
                    openai_api_key="test-key",
                )
            ]

        events = asyncio.run(collect())
    finally:
        route_deck_runtime._corpus_turn_plan = original_plan
        route_deck_runtime._stream_corpus_operation_message = original_operation_message

    assert [event["event_type"] for event in events] == [
        "corpus_status",
        "operation_completed",
        "message_delta",
        "corpus_done",
    ]
    assert events[1]["payload"]["state"]["node"] == "auth_register"
    assert events[1]["payload"]["active_surface"]["component"] == "CorpusAuthSurface"
