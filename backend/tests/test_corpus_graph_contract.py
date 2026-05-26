from __future__ import annotations

import asyncio
import uuid
from types import SimpleNamespace

import pytest
from fastapi import HTTPException
from routedeck_core import RouteDeckOperation, RouteDeckSurface, build_projection

from backend.core.schemas import AppGraphContextLens, AppGraphNavigationLocation, AppGraphRequest, AppGraphState, EntryGraphMessage
from backend.services.app_graph import corpus_graph_runtime
from backend.services.app_graph.manifest import AppActionIds, route_action_to_card
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
    operation_ids = {operation.id for operation in projection.legal_operations}
    assert {"auth.sign_in", "auth.register"} <= operation_ids
    assert {"route.open_node", "route.switch_surface"} <= operation_ids
    register = next(operation for operation in projection.legal_operations if operation.id == "auth.register")
    assert register.category == "auth"
    assert register.kind == "button"
    assert register.placement == "next_best"
    assert register.emphasis == "secondary"


def test_authenticated_projection_does_not_offer_auth_actions():
    lens = AppGraphContextLens(current_node="home", working_on="Home")
    state = AppGraphState(node="home")
    user = object()

    assert not corpus_graph_runtime._is_action_eligible(AppActionIds.AUTH_SIGN_IN, state, user, lens)
    assert not corpus_graph_runtime._is_action_eligible(AppActionIds.AUTH_REGISTER, state, user, lens)
    assert corpus_graph_runtime._is_action_eligible(AppActionIds.SAAS_AGENT_CREATE, state, user, lens)


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


def test_route_deck_projection_carries_capability_rail_contract():
    projection = asyncio.run(
        corpus_graph_runtime.route_deck_projection(
            request=AppGraphRequest(),
            user=None,
            db=None,
        )
    )

    capability_rail = projection.diagnostics["capability_rail"]
    assert capability_rail[0]["id"] == "home"
    assert any(item["id"] == "learning" and "learning.policy_candidate" in item["child_nodes"] for item in capability_rail)
    assert all("nodes" in item and "label" in item for item in capability_rail)


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


def test_corpus_state_does_not_rehydrate_review_surface_from_surface_query_alone():
    state = asyncio.run(
        corpus_graph_runtime.corpus_state(
            request=corpus_graph_runtime.request_from_location(
                node_id="home",
                surface_id="operation_review.saas_agent.create",
            ),
            user=None,
            db=None,
        )
    )

    assert state.state.pending_operation_id is None
    assert state.projection.navigation.current.surface_id is None
    assert state.replace_path == "/app/home"


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


def test_turn_router_decides_before_reply_stream(monkeypatch):
    plan_finished = False

    async def fake_stream_message(*, api_key, user_input, planning_context):
        assert plan_finished is True
        assert all("id" not in operation for operation in planning_context.get("legal_operations", []))
        assert all("operation_id" not in entity for entity in planning_context.get("visible_entities", []))
        yield "Hello"
        yield " from Corpus"

    async def forbidden_legacy_decision(*, api_key, user_input, projection):
        raise AssertionError("Corpus should use the structured turn router")

    async def fake_turn_plan(*, api_key, user_input, planning_context):
        nonlocal plan_finished
        plan_finished = True
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


def test_turn_router_waits_for_slow_product_action_instead_of_streaming_reply(monkeypatch):
    async def forbidden_stream_message(*, api_key, user_input, planning_context):
        raise AssertionError("product action turns must not stream a reply before the router decides")
        yield ""

    async def fake_turn_plan(*, api_key, user_input, planning_context):
        await asyncio.sleep(0.7)
        return {
            "intent": "propose_operation",
            "message": "Saving deployment.",
            "operation_id": AppActionIds.DEPLOYMENT_SAVE,
            "args": {"enabled": True, "visitor_auth_mode": "anonymous"},
            "surface_intent": {},
            "confidence": 0.98,
        }

    async def fake_projection(*, request, user, db, projection_version=1):
        return build_projection(
            corpus_graph_runtime.manifest,
            current_node="agent_home",
            operations=[
                RouteDeckOperation(
                    id=AppActionIds.DEPLOYMENT_SAVE,
                    label="Save deployment",
                    execution_mode="review",
                    invocation_kind="form",
                    can_dispatch_now=False,
                    input_schema={
                        "fields": [
                            {"key": "enabled", "label": "Enabled"},
                            {"key": "visitor_auth_mode", "label": "Visitor access"},
                        ]
                    },
                    target_node="agent_home",
                )
            ],
            surfaces=[
                RouteDeckSurface(
                    name="active",
                    component="AgentHomeSurface",
                    role="active",
                    slot="active",
                    surface_id="agent_home.active",
                )
            ],
            navigation={"current": {"node_id": "agent_home", "surface_id": "agent_home.active", "params": {}}},
            projection_version=projection_version,
        )

    async def fake_handler(state, payload, user, db):
        state.node = "agent_home"
        return state, [EntryGraphMessage(content="Deployment settings saved.")], [{"type": "deployment_saved"}]

    async def fake_require_member(saas_agent_id, user, db):
        return SimpleNamespace(role="owner")

    async def fake_valid_actions(state, user, db):
        return [route_action_to_card(corpus_graph_runtime._action_by_id[AppActionIds.DEPLOYMENT_SAVE])]

    async def fake_context_lens(state, user, db):
        return AppGraphContextLens(current_node=state.node, working_on="Agent home")

    async def fake_list_saas_agents(user, db):
        return []

    monkeypatch.setattr(corpus_graph_runtime, "_stream_corpus_message", forbidden_stream_message, raising=False)
    monkeypatch.setattr(corpus_graph_runtime, "_corpus_turn_plan", fake_turn_plan, raising=False)
    monkeypatch.setattr(corpus_graph_runtime, "route_deck_projection", fake_projection)
    monkeypatch.setattr(corpus_graph_runtime, "_handle_deployment_save", fake_handler, raising=False)
    monkeypatch.setattr(corpus_graph_runtime, "_require_member", fake_require_member, raising=False)
    monkeypatch.setattr(corpus_graph_runtime, "_valid_actions", fake_valid_actions, raising=False)
    monkeypatch.setattr(corpus_graph_runtime, "_context_lens", fake_context_lens, raising=False)
    monkeypatch.setattr(corpus_graph_runtime, "_list_saas_agents", fake_list_saas_agents, raising=False)

    agent_id = uuid.uuid4()

    async def collect():
        return [
            event
            async for event in corpus_graph_runtime.stream_corpus_turn(
                request=AppGraphRequest(
                    user_input="publish this agent",
                    state=AppGraphState(node="agent_home", active_saas_agent_id=agent_id),
                    node_id="agent_home",
                    saas_agent_id=agent_id,
                ),
                user=SimpleNamespace(id=uuid.uuid4()),
                db=None,
                openai_api_key="test-key",
            )
        ]

    events = asyncio.run(collect())

    assert not any(event["event_type"] == "message_delta" for event in events)
    assert not any(event["event_type"] == "corpus_error" for event in events)
    completion = next(event for event in events if event["event_type"] == "operation_completed")
    assert completion["payload"]["operation_id"] == AppActionIds.DEPLOYMENT_SAVE
    assert completion["payload"]["messages"][0]["content"] == "Deployment settings saved."


def test_corpus_surface_intent_updates_ephemeral_presentation_state(monkeypatch):
    async def forbidden_stream_message(*, api_key, user_input, planning_context):
        raise AssertionError("surface-only reply should not call the slower response stream model")
        yield ""

    async def fake_turn_plan(*, api_key, user_input, planning_context):
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


def test_corpus_graph_turn_opens_review_surface_for_non_auto_operation(monkeypatch):
    async def forbidden_stream_message(*, api_key, user_input, planning_context):
        raise AssertionError("operation routing should not call the slower response stream model")
        yield ""

    async def fake_turn_plan(*, api_key, user_input, planning_context):
        return {
            "intent": "propose_operation",
            "message": "I can take that next step.",
            "operation_id": "execution.plan",
            "args": {"goal": "list products"},
        }

    async def fake_projection(*, request, user, db, projection_version=1):
        review_surface_open = getattr(request.state, "pending_operation_id", None) == "execution.plan"
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
                *(
                    [
                        RouteDeckSurface(
                            name="review",
                            component="CorpusOperationReviewSurface",
                            variant="operation_review",
                            role="active",
                            slot="active",
                            surface_id="operation_review.execution.plan",
                            props={"operation_id": "execution.plan"},
                        )
                    ]
                    if review_surface_open
                    else []
                ),
            ],
            navigation={
                "current": {
                    "node_id": "execution_planning",
                    "surface_id": "operation_review.execution.plan" if review_surface_open else None,
                    "params": {},
                },
                "back_stack": [],
                "forward_stack": [],
            },
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
    assert not any(event["event_type"] == "proposal" for event in events)
    completion = next(event for event in events if event["event_type"] == "operation_completed")
    assert completion["payload"]["operation_id"] == "execution.plan"
    assert completion["payload"]["state"]["pending_operation_id"] == "execution.plan"
    assert completion["payload"]["projection"]["navigation"]["current"]["surface_id"] == "operation_review.execution.plan"
    assert completion["payload"]["active_surface"]["component"] == "CorpusOperationReviewSurface"


def test_corpus_state_path_includes_surface_query_for_active_surface():
    response = asyncio.run(
        corpus_graph_runtime.corpus_state(
            request=AppGraphRequest(
                state=AppGraphState(node="auth_sign_in", active_surface_id="auth_sign_in.active"),
                node_id="auth_sign_in",
            ),
            user=None,
            db=None,
        )
    )

    assert response.replace_path == "/app/auth_sign_in?surface_id=auth_sign_in.active"


def test_corpus_action_route_back_uses_runtime_navigation_stack():
    response = asyncio.run(
        corpus_graph_runtime.corpus_action(
            request=AppGraphRequest(
                state=AppGraphState(
                    node="home",
                    navigation_back_stack=[
                        {
                            "node_id": "auth_sign_in",
                            "surface_id": "auth_sign_in.active",
                            "params": {},
                        }
                    ],
                ),
                node_id="home",
            ),
            operation_id="route.back",
            args={},
            user=None,
            db=None,
        )
    )

    assert response.state.node == "auth_sign_in"
    assert response.projection.navigation.current.surface_id == "auth_sign_in.active"


def test_action_clears_stale_review_surface_after_non_route_node_transition(monkeypatch):
    agent_id = uuid.uuid4()

    async def fake_valid_actions(state, user, db):
        return [route_action_to_card(corpus_graph_runtime._action_by_id[AppActionIds.SAAS_AGENT_CREATE])]

    async def fake_handler(state, payload, user, db):
        state.node = "agent_home"
        state.active_saas_agent_id = agent_id
        return state, [], []

    async def passthrough_eligible(node_id, state, user, db):
        return node_id

    async def fake_context_lens(state, user, db):
        return AppGraphContextLens(current_node=state.node, working_on="Agent home")

    async def fake_list_saas_agents(user, db):
        return []

    monkeypatch.setattr(corpus_graph_runtime, "_valid_actions", fake_valid_actions, raising=False)
    monkeypatch.setattr(corpus_graph_runtime, "_handle_saas_agent_create", fake_handler, raising=False)
    monkeypatch.setattr(corpus_graph_runtime, "_eligible_node_or_recovery", passthrough_eligible, raising=False)
    monkeypatch.setattr(corpus_graph_runtime, "_context_lens", fake_context_lens, raising=False)
    monkeypatch.setattr(corpus_graph_runtime, "_list_saas_agents", fake_list_saas_agents, raising=False)

    response = asyncio.run(
        corpus_graph_runtime.action(
            request=AppGraphRequest(
                state=AppGraphState(
                    node="saas_agent_select",
                    active_surface_id="operation_review.saas_agent.create",
                    pending_operation_id="saas_agent.create",
                ),
                node_id="saas_agent_select",
                selected_action_id=AppActionIds.SAAS_AGENT_CREATE,
                action_payload={"name": "Navgraph Smoke Agent", "slug": "navgraph-smoke-agent"},
            ),
            user=object(),
            db=None,
        )
    )

    assert response.state.pending_operation_id is None
    assert response.state.active_surface_id is None
    assert response.replace_path == f"/app/agents/{agent_id}"


def test_apply_location_clears_stale_review_surface_before_defaulting():
    state = AppGraphState(
        node="saas_agent_select",
        active_surface_id="operation_review.saas_agent.create",
        pending_operation_id="saas_agent.create",
    )

    corpus_graph_runtime._apply_location(
        state,
        AppGraphNavigationLocation(node_id="home", surface_id=None, params={}),
    )

    assert state.node == "home"
    assert state.pending_operation_id is None
    assert state.active_surface_id is None


@pytest.mark.parametrize(
    ("user_input", "operation_id", "target_node", "label"),
    [
        ("sign me up", "auth.register", "auth_register", "Create account"),
        ("sign in", "auth.sign_in", "auth_sign_in", "Sign in"),
    ],
)
def test_open_surface_turn_commits_projection_without_prompt_bridge(monkeypatch, user_input, operation_id, target_node, label):
    plan_called = False

    async def forbidden_stream_message(*, api_key, user_input, planning_context):
        raise AssertionError("surface opening should not call the slower response stream model")
        yield ""

    async def fake_turn_plan(*, api_key, user_input, planning_context):
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

    assert "surface_opening" not in event_types
    assert "operation_completed" in event_types
    assert "message_delta" not in event_types[: event_types.index("operation_completed")]
    assert plan_called

    completion = next(event for event in events if event["event_type"] == "operation_completed")
    assert completion["payload"]["operation_id"] == operation_id
    assert completion["payload"]["active_surface"]["component"] == "CorpusAuthSurface"
    assert completion["payload"]["active_surface"]["variant"] == target_node
    assert "surface_prompt" not in completion["payload"]
    assert completion["payload"]["projection"]["navigation"]["current"]["node_id"] == target_node


def test_open_surface_intent_requires_llm_router_configuration():
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


def test_stream_corpus_turn_passes_structured_planning_context_to_router(monkeypatch):
    captured: dict[str, object] = {}

    async def forbidden_stream_message(*, api_key, user_input, planning_context):
        raise AssertionError("clarification path should not call the slower response stream model")
        yield ""

    async def fake_turn_plan(*, api_key, user_input, planning_context):
        captured["planning_context"] = planning_context
        return {
            "intent": "clarify",
            "message": "Need a bit more detail.",
            "operation_id": None,
            "args": {},
            "surface_intent": {},
        }

    async def fake_projection(*, request, user, db, projection_version=1):
        return build_projection(
            corpus_graph_runtime.manifest,
            current_node="learning",
            operations=[
                RouteDeckOperation(
                    id=AppActionIds.ROUTE_SWITCH_SURFACE,
                    label="Switch surface",
                    description="Switch the current learning view.",
                    execution_mode="auto",
                    invocation_kind="surface",
                    can_dispatch_now=True,
                    target_node="learning",
                ),
                RouteDeckOperation(
                    id=AppActionIds.LEARNING_OPEN,
                    label="Open learning",
                    description="Open the learning workspace.",
                    execution_mode="auto",
                    invocation_kind="surface",
                    can_dispatch_now=True,
                    target_node="learning",
                ),
            ],
            surfaces=[
                RouteDeckSurface(name="main", component="CorpusNodeFrame", variant="learning", role="frame"),
                RouteDeckSurface(name="side", component="CorpusContextLens", variant="default", role="frame"),
                RouteDeckSurface(
                    name="policy_gaps",
                    component="LearningSurface",
                    variant="policy_gaps",
                    role="active",
                    slot="active",
                    surface_id="learning.policy_gaps",
                    surface_kind="peer",
                    label="Policy gaps",
                ),
                RouteDeckSurface(
                    name="failed_executions",
                    component="LearningSurface",
                    variant="failed_executions",
                    role="active",
                    slot="active",
                    surface_id="learning.failed_executions",
                    surface_kind="peer",
                    label="Failed executions",
                ),
            ],
            navigation={
                "current": {"node_id": "learning", "surface_id": "learning.policy_gaps", "params": {}},
                "back_stack": [],
                "forward_stack": [],
            },
            projection_version=projection_version,
        )

    async def passthrough_eligible(node_id, state, user, db):
        return node_id

    monkeypatch.setattr(corpus_graph_runtime, "_stream_corpus_message", forbidden_stream_message, raising=False)
    monkeypatch.setattr(corpus_graph_runtime, "_corpus_turn_plan", fake_turn_plan, raising=False)
    monkeypatch.setattr(corpus_graph_runtime, "route_deck_projection", fake_projection)
    monkeypatch.setattr(corpus_graph_runtime, "_eligible_node_or_recovery", passthrough_eligible, raising=False)

    async def collect():
        return [
            event
            async for event in corpus_graph_runtime.stream_corpus_turn(
                request=AppGraphRequest(
                    user_input="show failed executions",
                    state=AppGraphState(node="learning", active_surface_id="learning.policy_gaps"),
                    node_id="learning",
                ),
                user=None,
                db=None,
                openai_api_key="test-key",
            )
        ]

    events = asyncio.run(collect())
    planning_context = captured["planning_context"]

    assert isinstance(planning_context, dict)
    assert planning_context["current"]["node_id"] == "learning"
    assert planning_context["current"]["surface_id"] == "learning.policy_gaps"
    assert any(
        surface["surface_id"] == "learning.failed_executions"
        for surface in planning_context["active_surfaces"]
    )
    assert all(
        operation["id"] != AppActionIds.ROUTE_SWITCH_SURFACE
        for operation in planning_context["legal_operations"]
    )
    assert {
        option["surface_id"]
        for option in planning_context["surface_options"]
    } == {"learning.policy_gaps", "learning.failed_executions"}
    assert events[-1]["event_type"] == "corpus_done"
    assert events[-1]["payload"]["status"] == "clarify"


def test_corpus_graph_turn_maps_surface_intent_to_internal_route_switch(monkeypatch):
    async def forbidden_stream_message(*, api_key, user_input, planning_context):
        raise AssertionError("surface switch should not call the slower response stream model")
        yield ""

    async def fake_turn_plan(*, api_key, user_input, planning_context):
        assert all(
            operation["id"] != AppActionIds.ROUTE_SWITCH_SURFACE
            for operation in planning_context["legal_operations"]
        )
        assert any(
            option["surface_id"] == "learning.failed_executions"
            for option in planning_context["surface_options"]
        )
        return {
            "intent": "open_surface",
            "message": "Opening failed executions.",
            "operation_id": None,
            "args": {},
            "surface_intent": {"surface_id": "learning.failed_executions"},
        }

    async def fake_projection(*, request, user, db, projection_version=1):
        active_surface_id = request.state.active_surface_id or "learning.policy_gaps"
        return build_projection(
            corpus_graph_runtime.manifest,
            current_node="learning",
            operations=[
                RouteDeckOperation(
                    id=AppActionIds.ROUTE_SWITCH_SURFACE,
                    label="Switch surface",
                    description="Switch the current learning view.",
                    execution_mode="auto",
                    invocation_kind="hidden",
                    can_dispatch_now=True,
                    target_node="learning",
                ),
                RouteDeckOperation(
                    id=AppActionIds.LEARNING_OPEN,
                    label="Open learning",
                    description="Open the learning workspace.",
                    execution_mode="auto",
                    invocation_kind="surface",
                    can_dispatch_now=True,
                    target_node="learning",
                ),
            ],
            surfaces=[
                RouteDeckSurface(name="main", component="CorpusNodeFrame", variant="learning", role="frame"),
                RouteDeckSurface(
                    name="policy_gaps",
                    component="LearningSurface",
                    variant="policy_gaps",
                    role="active",
                    slot="active",
                    surface_id="learning.policy_gaps",
                    surface_kind="peer",
                    label="Policy gaps",
                ),
                RouteDeckSurface(
                    name="failed_executions",
                    component="LearningSurface",
                    variant="failed_executions",
                    role="active",
                    slot="active",
                    surface_id="learning.failed_executions",
                    surface_kind="peer",
                    label="Failed executions",
                ),
            ],
            navigation={
                "current": {"node_id": "learning", "surface_id": active_surface_id, "params": {}},
                "back_stack": [],
                "forward_stack": [],
            },
            projection_version=projection_version,
        )

    async def passthrough_eligible(node_id, state, user, db):
        return node_id

    monkeypatch.setattr(corpus_graph_runtime, "_stream_corpus_message", forbidden_stream_message, raising=False)
    monkeypatch.setattr(corpus_graph_runtime, "_corpus_turn_plan", fake_turn_plan, raising=False)
    monkeypatch.setattr(corpus_graph_runtime, "route_deck_projection", fake_projection)
    monkeypatch.setattr(corpus_graph_runtime, "_eligible_node_or_recovery", passthrough_eligible, raising=False)

    async def collect():
        return [
            event
            async for event in corpus_graph_runtime.stream_corpus_turn(
                request=AppGraphRequest(
                    user_input="show failed executions",
                    state=AppGraphState(node="learning", active_surface_id="learning.policy_gaps"),
                    node_id="learning",
                ),
                user=None,
                db=None,
                openai_api_key="test-key",
            )
        ]

    events = asyncio.run(collect())
    completed = next(event for event in events if event["event_type"] == "operation_completed")

    assert completed["payload"]["operation_id"] == AppActionIds.ROUTE_SWITCH_SURFACE
    assert completed["payload"]["projection"]["navigation"]["current"]["surface_id"] == "learning.failed_executions"
    assert events[-1]["event_type"] == "corpus_done"
    assert events[-1]["payload"]["status"] == "committed"


def test_corpus_action_review_operation_stages_review_surface_without_route_injection(monkeypatch):
    async def fake_projection(*, request, user, db, projection_version=1):
        review_surface_open = getattr(request.state, "pending_operation_id", None) == AppActionIds.SAAS_AGENT_CREATE
        return build_projection(
            corpus_graph_runtime.manifest,
            current_node="home",
            operations=[
                RouteDeckOperation(
                    id=AppActionIds.SAAS_AGENT_CREATE,
                    label="Create SaaS Agent",
                    execution_mode="review",
                    invocation_kind="form",
                    can_dispatch_now=False,
                    input_schema={
                        "fields": [
                            {"key": "name", "label": "Name", "required": True},
                            {"key": "slug", "label": "Slug", "required": True},
                        ]
                    },
                    target_node="agent_home",
                )
            ],
            surfaces=[
                RouteDeckSurface(name="main", component="CorpusDashboardSurface", variant="dashboard", role="frame"),
                *(
                    [
                        RouteDeckSurface(
                            name="review",
                            component="CorpusOperationReviewSurface",
                            variant="operation_review",
                            role="active",
                            slot="active",
                            surface_id="operation_review.saas_agent.create",
                            props={"operation_id": AppActionIds.SAAS_AGENT_CREATE},
                        )
                    ]
                    if review_surface_open
                    else []
                ),
            ],
            navigation={
                "current": {
                    "node_id": "home",
                    "surface_id": "operation_review.saas_agent.create" if review_surface_open else None,
                    "params": {},
                },
                "back_stack": [],
                "forward_stack": [],
            },
            projection_version=projection_version,
        )

    monkeypatch.setattr(corpus_graph_runtime, "route_deck_projection", fake_projection)

    response = asyncio.run(
        corpus_graph_runtime.corpus_action(
            request=AppGraphRequest(
                state=AppGraphState(node="home"),
                node_id="home",
            ),
            operation_id=AppActionIds.SAAS_AGENT_CREATE,
            args={"name": "Architect Agent", "slug": "architect-agent"},
            user=None,
            db=None,
        )
    )

    assert response.state.node == "home"
    assert response.state.pending_operation_id == AppActionIds.SAAS_AGENT_CREATE
    assert response.state.pending_operation_args == {"name": "Architect Agent", "slug": "architect-agent"}
    assert response.projection.navigation.current.surface_id == "operation_review.saas_agent.create"
    assert response.active_surface.component == "CorpusOperationReviewSurface"


def test_corpus_action_surface_hosted_form_operation_commits_without_generic_review(monkeypatch):
    async def fake_projection(*, request, user, db, projection_version=1):
        current_node = request.state.node
        return build_projection(
            corpus_graph_runtime.manifest,
            current_node=current_node,
            operations=[
                RouteDeckOperation(
                    id=AppActionIds.CONNECTION_ACTIVATE,
                    label="Save and activate API",
                    execution_mode="review",
                    invocation_kind="form",
                    can_dispatch_now=False,
                    input_schema={
                        "fields": [
                            {"key": "name", "label": "Connection name", "required": True},
                            {"key": "base_url", "label": "Base URL", "required": True},
                        ]
                    },
                    target_node="catalog",
                )
            ],
            surfaces=[
                RouteDeckSurface(name="main", component="CorpusNodeFrame", variant=current_node, role="frame"),
                RouteDeckSurface(
                    name="active",
                    component="CatalogSurface" if current_node == "catalog" else "ConnectionSetupSurface",
                    variant=current_node,
                    role="active",
                    slot="active",
                    surface_id=f"{current_node}.active",
                    label="Catalog" if current_node == "catalog" else "Connection Configure",
                ),
            ],
            navigation={
                "current": {
                    "node_id": current_node,
                    "surface_id": f"{current_node}.active",
                    "params": {},
                },
                "back_stack": [],
                "forward_stack": [],
            },
            projection_version=projection_version,
        )

    async def fake_valid_actions(state, user, db):
        return [route_action_to_card(corpus_graph_runtime._action_by_id[AppActionIds.CONNECTION_ACTIVATE])]

    async def fake_handler(state, payload, user, db):
        state.node = "catalog"
        state.graph_context["activation"] = payload
        return state, [], []

    async def passthrough_eligible(node_id, state, user, db):
        return node_id

    async def fake_context_lens(state, user, db):
        return AppGraphContextLens(current_node=state.node, working_on="Catalog")

    async def fake_list_saas_agents(user, db):
        return []

    monkeypatch.setattr(corpus_graph_runtime, "route_deck_projection", fake_projection)
    monkeypatch.setattr(corpus_graph_runtime, "_valid_actions", fake_valid_actions, raising=False)
    monkeypatch.setattr(corpus_graph_runtime, "_handle_connection_activate", fake_handler, raising=False)
    monkeypatch.setattr(corpus_graph_runtime, "_eligible_node_or_recovery", passthrough_eligible, raising=False)
    monkeypatch.setattr(corpus_graph_runtime, "_context_lens", fake_context_lens, raising=False)
    monkeypatch.setattr(corpus_graph_runtime, "_list_saas_agents", fake_list_saas_agents, raising=False)

    response = asyncio.run(
        corpus_graph_runtime.corpus_action(
            request=AppGraphRequest(
                state=AppGraphState(node="connection_configure", active_surface_id="connection_configure.active"),
                node_id="connection_configure",
            ),
            operation_id=AppActionIds.CONNECTION_ACTIVATE,
            args={"name": "Primary API", "base_url": "https://api.example.com"},
            user=object(),
            db=None,
        )
    )

    assert response.state.node == "catalog"
    assert response.state.pending_operation_id is None
    assert response.state.graph_context["activation"] == {
        "name": "Primary API",
        "base_url": "https://api.example.com",
    }
    assert response.projection.navigation.current.surface_id == "catalog.active"


def test_corpus_action_executes_deployment_publish_from_agent_home(monkeypatch):
    captured: dict[str, object] = {}

    async def fake_projection(*, request, user, db, projection_version=1):
        return build_projection(
            corpus_graph_runtime.manifest,
            current_node="agent_home",
            operations=[
                RouteDeckOperation(
                    id=AppActionIds.DEPLOYMENT_SAVE,
                    label="Save deployment",
                    execution_mode="review",
                    invocation_kind="form",
                    can_dispatch_now=False,
                    input_schema={
                        "fields": [
                            {"key": "enabled", "label": "Enabled"},
                            {"key": "visitor_auth_mode", "label": "Visitor access"},
                        ]
                    },
                    target_node="agent_home",
                )
            ],
            surfaces=[
                RouteDeckSurface(
                    name="active",
                    component="AgentHomeSurface",
                    role="active",
                    slot="active",
                    surface_id="agent_home.active",
                    props={"operation_id": AppActionIds.DEPLOYMENT_SAVE},
                )
            ],
            navigation={
                "current": {
                    "node_id": "agent_home",
                    "surface_id": "agent_home.active",
                    "params": {},
                },
                "back_stack": [],
                "forward_stack": [],
            },
            projection_version=projection_version,
        )

    monkeypatch.setattr(corpus_graph_runtime, "route_deck_projection", fake_projection)

    async def fake_handler(state, payload, user, db):
        captured["payload"] = dict(payload)
        state.node = "agent_home"
        return state, [EntryGraphMessage(content="Deployment settings saved.")], [{"type": "deployment_saved"}]

    async def fake_require_member(saas_agent_id, user, db):
        return SimpleNamespace(role="owner")

    async def fake_valid_actions(state, user, db):
        return [route_action_to_card(corpus_graph_runtime._action_by_id[AppActionIds.DEPLOYMENT_SAVE])]

    async def fake_context_lens(state, user, db):
        return AppGraphContextLens(current_node=state.node, working_on="Agent home")

    async def fake_list_saas_agents(user, db):
        return []

    monkeypatch.setattr(corpus_graph_runtime, "_handle_deployment_save", fake_handler, raising=False)
    monkeypatch.setattr(corpus_graph_runtime, "_require_member", fake_require_member, raising=False)
    monkeypatch.setattr(corpus_graph_runtime, "_valid_actions", fake_valid_actions, raising=False)
    monkeypatch.setattr(corpus_graph_runtime, "_context_lens", fake_context_lens, raising=False)
    monkeypatch.setattr(corpus_graph_runtime, "_list_saas_agents", fake_list_saas_agents, raising=False)

    agent_id = uuid.uuid4()
    response = asyncio.run(
        corpus_graph_runtime.corpus_action(
            request=AppGraphRequest(
                state=AppGraphState(node="agent_home", active_saas_agent_id=agent_id),
                node_id="agent_home",
                saas_agent_id=agent_id,
            ),
            operation_id=AppActionIds.DEPLOYMENT_SAVE,
            args={"enabled": True, "visitor_auth_mode": "anonymous"},
            user=object(),
            db=None,
        )
    )

    assert captured["payload"] == {"enabled": True, "visitor_auth_mode": "anonymous"}
    assert response.state.pending_operation_id is None
    assert response.projection.navigation.current.surface_id == "agent_home.active"
    assert response.messages[0].content == "Deployment settings saved."


def test_corpus_action_route_switch_surface_rejects_unknown_surface(monkeypatch):
    async def fake_projection(*, request, user, db, projection_version=1):
        return build_projection(
            corpus_graph_runtime.manifest,
            current_node="learning",
            operations=[
                RouteDeckOperation(
                    id=AppActionIds.ROUTE_SWITCH_SURFACE,
                    label="Switch surface",
                    execution_mode="auto",
                    invocation_kind="surface",
                    can_dispatch_now=True,
                    target_node="learning",
                )
            ],
            surfaces=[
                RouteDeckSurface(name="main", component="CorpusNodeFrame", variant="learning", role="frame"),
                RouteDeckSurface(
                    name="policy_gaps",
                    component="LearningSurface",
                    variant="policy_gaps",
                    role="active",
                    slot="active",
                    surface_id="learning.policy_gaps",
                    label="Policy gaps",
                ),
            ],
            navigation={
                "current": {"node_id": "learning", "surface_id": "learning.policy_gaps", "params": {}},
                "back_stack": [],
                "forward_stack": [],
            },
            projection_version=projection_version,
        )

    monkeypatch.setattr(corpus_graph_runtime, "route_deck_projection", fake_projection)

    with pytest.raises(HTTPException) as exc:
        asyncio.run(
            corpus_graph_runtime.corpus_action(
                request=AppGraphRequest(
                    state=AppGraphState(node="learning", active_surface_id="learning.policy_gaps"),
                    node_id="learning",
                ),
                operation_id=AppActionIds.ROUTE_SWITCH_SURFACE,
                args={"surface_id": "learning.rejected"},
                user=None,
                db=None,
            )
        )

    assert exc.value.status_code == 400
    assert "projected active surface_id" in exc.value.detail


def test_corpus_action_route_open_node_rejects_review_surface_injection(monkeypatch):
    async def fake_projection(*, request, user, db, projection_version=1):
        return build_projection(
            corpus_graph_runtime.manifest,
            current_node="home",
            operations=[
                RouteDeckOperation(
                    id=AppActionIds.ROUTE_OPEN_NODE,
                    label="Open node",
                    execution_mode="auto",
                    invocation_kind="hidden",
                    can_dispatch_now=True,
                    target_node="home",
                )
            ],
            surfaces=[RouteDeckSurface(name="main", component="CorpusDashboardSurface", variant="dashboard", role="frame")],
            navigation={
                "current": {"node_id": "home", "surface_id": None, "params": {}},
                "back_stack": [],
                "forward_stack": [],
            },
            projection_version=projection_version,
        )

    monkeypatch.setattr(corpus_graph_runtime, "route_deck_projection", fake_projection)

    with pytest.raises(HTTPException) as exc:
        asyncio.run(
            corpus_graph_runtime.corpus_action(
                request=AppGraphRequest(
                    state=AppGraphState(node="home"),
                    node_id="home",
                ),
                operation_id=AppActionIds.ROUTE_OPEN_NODE,
                args={
                    "node_id": "home",
                    "surface_id": "operation_review.saas_agent.create",
                    "pending_operation_id": AppActionIds.SAAS_AGENT_CREATE,
                },
                user=None,
                db=None,
            )
        )

    assert exc.value.status_code == 400
    assert "surface_id is not legal" in exc.value.detail


def test_corpus_public_routes_are_registered_without_raw_routedeck_routes():
    routes = {route.path for route in app.routes}

    assert "/api/corpus/state" in routes
    assert "/api/corpus/stream" in routes
    assert "/api/corpus/action" in routes
    assert "/api/diagnostics/stream" in routes
    assert "/api/routedeck/projection" not in routes
    assert "/api/routedeck/stream" not in routes
    assert not any(route.startswith("/api/app/graph") for route in routes)
    assert not any(route.startswith("/api/entry") for route in routes)
