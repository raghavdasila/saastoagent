from __future__ import annotations

import asyncio

import pytest
from fastapi import HTTPException
from routedeck_core import RouteDeckOperation, RouteDeckSurface, build_projection

from backend.core.schemas import AppGraphRequest, AppGraphState
from backend.services.app_graph import corpus_graph_runtime
from backend.services.app_graph.runtime import CorpusGraphRuntime
from backend.main import app


def test_corpus_graph_is_the_central_runtime_not_a_wrapper():
    assert isinstance(corpus_graph_runtime, CorpusGraphRuntime)


def test_corpus_graph_projects_lounge_through_routedeck():
    projection = asyncio.run(
        corpus_graph_runtime.route_deck_projection(
            request=AppGraphRequest(),
            user=None,
            db=None,
        )
    )

    assert projection.current_context == "lounge"
    assert projection.graph_node == "home"
    assert projection.surfaces["main"].component == "CorpusLoungeSurface"
    assert projection.surfaces["main"].role == "frame"
    assert projection.surfaces["side"].component == "CorpusContextLens"
    assert projection.surfaces["side"].role == "frame"
    assert {operation.id for operation in projection.legal_operations} == {"auth.sign_in", "auth.register"}


def test_route_deck_projection_diagnostics_do_not_carry_product_runtime_state():
    projection = asyncio.run(
        corpus_graph_runtime.route_deck_projection(
            request=AppGraphRequest(),
            user=None,
            db=None,
        )
    )

    assert "graph_state" not in projection.diagnostics
    assert "replace_path" not in projection.diagnostics


def test_corpus_state_exposes_product_state_outside_diagnostics():
    state = asyncio.run(
        corpus_graph_runtime.corpus_state(
            request=AppGraphRequest(),
            user=None,
            db=None,
        )
    )

    assert state.state.node == "home"
    assert state.replace_path == "/app/home"
    assert state.projection.current_context == "lounge"
    assert "graph_state" not in state.projection.diagnostics


def test_corpus_graph_turn_stream_requires_llm_configuration():
    with pytest.raises(HTTPException) as exc:
        asyncio.run(
            corpus_graph_runtime.stream_corpus_turn(
                request=AppGraphRequest(user_input="hello"),
                user=None,
                db=None,
                openai_api_key="",
            ).__anext__()
        )

    assert exc.value.status_code == 503
    assert "Corpus graph requires a configured LLM" in exc.value.detail


def test_turn_router_reply_now_starts_real_model_stream_before_router_completes(monkeypatch):
    stream_started = asyncio.Event()

    async def fake_stream_message(*, api_key, user_input, projection):
        stream_started.set()
        yield "Hello"
        yield " from Corpus"

    async def forbidden_legacy_decision(*, api_key, user_input, projection):
        raise AssertionError("Corpus should use the structured turn router")

    async def fake_turn_plan(*, api_key, user_input, projection):
        await stream_started.wait()
        return {
            "intent": "reply_now",
            "message": "",
            "operation_id": None,
            "args": {},
            "surface_intent": {},
            "confidence": 0.98,
        }

    monkeypatch.setattr(corpus_graph_runtime, "_stream_corpus_message", fake_stream_message, raising=False)
    monkeypatch.setattr(corpus_graph_runtime, "_corpus_decision", forbidden_legacy_decision, raising=False)
    monkeypatch.setattr(corpus_graph_runtime, "_corpus_turn_plan", fake_turn_plan, raising=False)

    async def collect():
        return [
            event
            async for event in corpus_graph_runtime.stream_corpus_turn(
                request=AppGraphRequest(user_input="hi"),
                user=None,
                db=None,
                openai_api_key="test-key",
            )
        ]

    events = asyncio.run(asyncio.wait_for(collect(), timeout=1))
    deltas = [event for event in events if event["event_type"] == "message_delta"]

    assert [event["payload"]["delta"] for event in deltas] == ["Hello", " from Corpus"]
    assert all("content" not in event["payload"] for event in deltas)
    assert events[-1]["event_type"] == "corpus_done"
    assert events[-1]["payload"]["status"] == "reply_now"


def test_corpus_surface_intent_updates_ephemeral_presentation_state(monkeypatch):
    async def forbidden_stream_message(*, api_key, user_input, projection):
        raise AssertionError("surface-only reply should not call the slower response stream model")
        yield ""

    async def fake_turn_plan(*, api_key, user_input, projection):
        return {
            "intent": "reply_now",
            "message": "I will keep this view compact.",
            "operation_id": None,
            "args": {},
            "surface_intent": {"main": "compact"},
        }

    monkeypatch.setattr(corpus_graph_runtime, "_stream_corpus_message", forbidden_stream_message, raising=False)
    monkeypatch.setattr(corpus_graph_runtime, "_corpus_turn_plan", fake_turn_plan, raising=False)

    request = AppGraphRequest(user_input="make this compact", state=AppGraphState(node="auth_sign_in"), node_id="auth_sign_in")

    async def collect():
        return [
            event
            async for event in corpus_graph_runtime.stream_corpus_turn(
                request=request,
                user=None,
                db=None,
                openai_api_key="test-key",
            )
        ]

    events = asyncio.run(collect())
    projection_event = next(event for event in events if event["event_type"] == "projection_update")
    projection = projection_event["payload"]["projection"]

    assert projection["presentation_state"]["surface_variants"]["main"] == "compact"
    assert projection["surfaces"]["main"]["variant"] == "compact"


def test_corpus_graph_turn_emits_review_proposal_for_non_auto_operation(monkeypatch):
    async def forbidden_stream_message(*, api_key, user_input, projection):
        raise AssertionError("operation routing should not call the slower response stream model")
        yield ""

    async def fake_turn_plan(*, api_key, user_input, projection):
        return {
            "intent": "propose_operation",
            "message": "I can take that next step.",
            "operation_id": "execution.plan",
            "args": {"goal": "list products"},
        }

    async def fake_projection(*, request, user, db, projection_version=1):
        return build_projection(
            corpus_graph_runtime.manifest,
            current_node="execution_planning",
            operations=[
                RouteDeckOperation(
                    id="execution.plan",
                    label="Plan execution",
                    safety_class="write_external",
                    execution_mode="review",
                    input_schema={"fields": [{"key": "goal", "label": "Goal", "required": True}]},
                    target_node="execution_planning",
                )
            ],
            surfaces=[
                RouteDeckSurface(name="main", component="CorpusNodeFrame", variant="execution_planning", role="frame"),
                RouteDeckSurface(name="side", component="CorpusContextLens", variant="default", role="frame"),
            ],
            projection_version=projection_version,
        )

    monkeypatch.setattr(corpus_graph_runtime, "_stream_corpus_message", forbidden_stream_message, raising=False)
    monkeypatch.setattr(corpus_graph_runtime, "_corpus_turn_plan", fake_turn_plan, raising=False)
    monkeypatch.setattr(corpus_graph_runtime, "route_deck_projection", fake_projection)

    async def collect():
        return [
            event
            async for event in corpus_graph_runtime.stream_corpus_turn(
                request=AppGraphRequest(
                    user_input="run list products",
                    state=AppGraphState(node="execution_planning"),
                    node_id="execution_planning",
                ),
                user=None,
                db=None,
                openai_api_key="test-key",
            )
        ]

    events = asyncio.run(collect())
    assert any(event["event_type"] == "proposal" for event in events)
    proposal = next(event for event in events if event["event_type"] == "proposal")
    assert proposal["payload"]["operation_id"] == "execution.plan"
    assert proposal["payload"]["execution_mode"] == "review"


@pytest.mark.parametrize(
    ("user_input", "operation_id", "target_node", "label"),
    [
        ("sign me up", "auth.register", "auth_register", "Create account"),
        ("sign in", "auth.sign_in", "auth_sign_in", "Sign in"),
    ],
)
def test_surface_opening_turn_commits_surface_before_prompt(monkeypatch, user_input, operation_id, target_node, label):
    plan_called = False

    async def forbidden_stream_message(*, api_key, user_input, projection):
        raise AssertionError("surface opening should not call the slower response stream model")
        yield ""

    async def fake_turn_plan(*, api_key, user_input, projection):
        nonlocal plan_called
        plan_called = True
        return {
            "intent": "open_surface",
            "message": "What is your email address?",
            "operation_id": operation_id,
            "args": {},
            "surface_intent": {},
        }

    monkeypatch.setattr(corpus_graph_runtime, "_stream_corpus_message", forbidden_stream_message, raising=False)
    monkeypatch.setattr(corpus_graph_runtime, "_corpus_turn_plan", fake_turn_plan, raising=False)

    async def collect():
        return [
            event
            async for event in corpus_graph_runtime.stream_corpus_turn(
                request=AppGraphRequest(user_input=user_input),
                user=None,
                db=None,
                openai_api_key="test-key",
            )
        ]

    events = asyncio.run(collect())
    event_types = [event["event_type"] for event in events]

    assert "surface_opening" in event_types
    assert "operation_completed" in event_types
    assert "message_delta" not in event_types[: event_types.index("operation_completed")]
    assert plan_called

    opening = next(event for event in events if event["event_type"] == "surface_opening")
    assert opening["payload"]["operation_id"] == operation_id
    assert opening["payload"]["label"] == label
    assert opening["payload"]["target_node"] == target_node
    assert opening["payload"]["expected_active_surface"]["component"] == "CorpusAuthSurface"

    completion = next(event for event in events if event["event_type"] == "operation_completed")
    assert completion["payload"]["operation_id"] == operation_id
    assert completion["payload"]["active_surface"]["component"] == "CorpusAuthSurface"
    assert completion["payload"]["active_surface"]["variant"] == target_node
    assert completion["payload"]["surface_prompt"]["content"] == "What is your email address?"


def test_surface_opening_intent_requires_llm_router_configuration():
    with pytest.raises(HTTPException) as exc:
        asyncio.run(
            corpus_graph_runtime.stream_corpus_turn(
                request=AppGraphRequest(user_input="sign me up"),
                user=None,
                db=None,
                openai_api_key="",
            ).__anext__()
        )

    assert exc.value.status_code == 503
    assert "Corpus graph requires a configured LLM" in exc.value.detail


def test_corpus_and_routedeck_public_routes_are_registered():
    routes = {route.path for route in app.routes}

    assert "/api/routedeck/projection" in routes
    assert "/api/routedeck/stream" in routes
    assert "/api/corpus/state" in routes
    assert "/api/corpus/stream" in routes
    assert "/api/corpus/action" in routes
    assert "/api/diagnostics/stream" in routes
    assert not any(route.startswith("/api/app/graph") for route in routes)
    assert not any(route.startswith("/api/entry") for route in routes)
