from __future__ import annotations

import uuid

from routedeck_core import RouteDeckOperation, RouteDeckProjection, RouteDeckSurface

from backend.core.schemas import AppGraphState
from backend.services.app_graph.corpus_turn_planning import (
    build_corpus_turn_planning_context,
    normalize_corpus_turn_plan,
)
from backend.services.app_graph.manifest import AppActionIds


def _projection(
    *,
    current_surface_id: str | None = "connection_configure.active",
) -> RouteDeckProjection:
    return RouteDeckProjection(
        current_context="connection_configure",
        graph_node="connection_configure",
        legal_operations=[
            RouteDeckOperation(
                id="connection.configure",
                label="Configure connection",
                description="Open the connection setup surface.",
                invocation_kind="surface",
                can_dispatch_now=True,
                target_node="connection_configure",
                required_args=[],
                missing_args=[],
                execution_mode="auto",
                safety_class="navigation",
                input_schema={"fields": []},
            ),
            RouteDeckOperation(
                id="knowledge.generate",
                label="Generate knowledge",
                description="Review a generated knowledge draft.",
                invocation_kind="form",
                can_dispatch_now=False,
                target_node="knowledge",
                required_args=["prompt"],
                missing_args=["prompt"],
                execution_mode="review",
                safety_class="draft",
                input_schema={
                    "fields": [
                        {"key": "prompt", "label": "Prompt", "required": True},
                        {"key": "tone", "label": "Tone", "required": False},
                    ]
                },
            ),
            RouteDeckOperation(
                id=AppActionIds.ROUTE_SWITCH_SURFACE,
                label="Switch surface",
                description="Switch between current node surfaces.",
                invocation_kind="hidden",
                can_dispatch_now=True,
                target_node="connection_configure",
                required_args=[],
                missing_args=[],
                execution_mode="auto",
                safety_class="navigation",
            ),
            RouteDeckOperation(
                id=AppActionIds.ROUTE_OPEN_NODE,
                label="Open node",
                description="Open another legal node.",
                invocation_kind="hidden",
                can_dispatch_now=True,
                target_node="knowledge",
                required_args=[],
                missing_args=[],
                execution_mode="auto",
                safety_class="navigation",
            ),
        ],
        surfaces={
            "lens": RouteDeckSurface(
                name="side",
                component="CorpusContextLens",
                role="frame",
                props={
                    "selected_saas_agent_name": "Billing Agent",
                    "selected_saas_agent_slug": "billing-agent",
                },
            ),
            "connection_configure.active": RouteDeckSurface(
                name="active",
                surface_id="connection_configure.active",
                component="ConnectionSetupSurface",
                role="active",
                slot="active",
                surface_kind="embedded",
                label="Connection setup",
                default=True,
                props={"title": "Connection setup"},
            ),
            "knowledge.active": RouteDeckSurface(
                name="active",
                surface_id="knowledge.active",
                component="KnowledgeSurface",
                role="active",
                slot="active",
                surface_kind="embedded",
                label="Knowledge",
                props={"title": "Knowledge"},
            ),
        },
        navigation={
            "current": {
                "node_id": "connection_configure",
                "surface_id": current_surface_id,
                "params": {},
            }
        },
        diagnostics={
            "introspection": {
                "blocked_actions": [
                    {
                        "id": "approval.approve",
                        "label": "Approve",
                        "reason": "Waiting for a completed draft.",
                    }
                ]
            }
        },
    )


def _saas_agent_select_projection(*, saas_agent_id: str = "22222222-2222-2222-2222-222222222222") -> RouteDeckProjection:
    return RouteDeckProjection(
        current_context="saas_agent_select",
        graph_node="saas_agent_select",
        legal_operations=[
            RouteDeckOperation(
                id=AppActionIds.SAAS_AGENT_OPEN,
                label="Open SaaS Agent",
                description="Open the selected SaaS Agent.",
                invocation_kind="entity_selector",
                can_dispatch_now=True,
                target_node="agent_home",
                required_args=["saas_agent_id"],
                missing_args=[],
                execution_mode="auto",
                safety_class="navigation",
                input_schema={
                    "fields": [
                        {"key": "saas_agent_id", "label": "SaaS Agent ID", "required": True},
                    ]
                },
            )
        ],
        surfaces={
            "saas_agent_select.active": RouteDeckSurface(
                name="active",
                surface_id="saas_agent_select.active",
                component="SaaSAgentListSurface",
                role="active",
                slot="active",
                surface_kind="embedded",
                label="SaaS Agent Select",
                default=True,
                props={
                    "planning_description": "Shows the selectable SaaS Agents currently visible in the list.",
                    "planning_entities": [
                        {
                            "entity_type": "saas_agent",
                            "id": saas_agent_id,
                            "label": "Live Commerce",
                            "slug": "live-commerce",
                            "description": "live-commerce",
                            "operation_id": AppActionIds.SAAS_AGENT_OPEN,
                            "args": {"saas_agent_id": saas_agent_id},
                        }
                    ],
                    "planning_entity_count": 1,
                },
            )
        },
        navigation={
            "current": {
                "node_id": "saas_agent_select",
                "surface_id": "saas_agent_select.active",
                "params": {},
            }
        },
        diagnostics={},
    )


def test_build_turn_planning_context_summarizes_bound_agent_surface_and_operations():
    state = AppGraphState(
        node="connection_configure",
        active_saas_agent_id=uuid.UUID("11111111-1111-1111-1111-111111111111"),
        active_surface_id="connection_configure.active",
    )

    context = build_corpus_turn_planning_context(
        projection=_projection(),
        state=state,
    )

    assert context["current"] == {
        "node_id": "connection_configure",
        "surface_id": "connection_configure.active",
    }
    assert context["active_saas_agent"] == {
        "id": "11111111-1111-1111-1111-111111111111",
        "name": "Billing Agent",
        "slug": "billing-agent",
    }
    assert context["active_surface"] == {
        "surface_id": "connection_configure.active",
        "label": "Connection setup",
        "component": "ConnectionSetupSurface",
        "variant": "default",
        "role": "active",
        "surface_kind": "embedded",
    }
    assert [surface["surface_id"] for surface in context["active_surfaces"]] == [
        "connection_configure.active",
        "knowledge.active",
    ]
    operations = {operation["id"]: operation for operation in context["legal_operations"]}
    assert AppActionIds.ROUTE_SWITCH_SURFACE not in operations
    assert AppActionIds.ROUTE_OPEN_NODE not in operations
    assert operations["connection.configure"] == {
        "id": "connection.configure",
        "label": "Configure connection",
        "description": "Open the connection setup surface.",
        "invocation_kind": "surface",
        "can_dispatch_now": True,
        "target_node": "connection_configure",
        "required_args": [],
        "missing_args": [],
        "execution_mode": "auto",
        "safety_class": "navigation",
        "input_schema": {"fields": []},
        "accepted_arg_keys": [],
    }
    assert operations["knowledge.generate"] == {
        "id": "knowledge.generate",
        "label": "Generate knowledge",
        "description": "Review a generated knowledge draft.",
        "invocation_kind": "form",
        "can_dispatch_now": False,
        "target_node": "knowledge",
        "required_args": ["prompt"],
        "missing_args": ["prompt"],
        "execution_mode": "review",
        "safety_class": "draft",
        "input_schema": {
            "fields": [
                {"key": "prompt", "label": "Prompt", "required": True},
                {"key": "tone", "label": "Tone", "required": False},
            ]
        },
        "accepted_arg_keys": ["prompt", "tone"],
    }
    assert {
        option["surface_id"]
        for option in context["surface_options"]
    } == {"connection_configure.active", "knowledge.active"}
    assert "blocked_operations" not in context


def test_build_turn_planning_context_exposes_visible_entities_for_selectable_surface():
    saas_agent_id = "33333333-3333-3333-3333-333333333333"
    context = build_corpus_turn_planning_context(
        projection=_saas_agent_select_projection(saas_agent_id=saas_agent_id),
        state=AppGraphState(node="saas_agent_select", active_surface_id="saas_agent_select.active"),
    )

    assert context["active_surface"] == {
        "surface_id": "saas_agent_select.active",
        "label": "SaaS Agent Select",
        "component": "SaaSAgentListSurface",
        "variant": "default",
        "role": "active",
        "surface_kind": "embedded",
        "description": "Shows the selectable SaaS Agents currently visible in the list.",
        "selectable_entities": [
            {
                "entity_type": "saas_agent",
                "id": saas_agent_id,
                "label": "Live Commerce",
                "slug": "live-commerce",
                "description": "live-commerce",
                "operation_id": AppActionIds.SAAS_AGENT_OPEN,
                "args": {"saas_agent_id": saas_agent_id},
            }
        ],
        "selectable_entity_count": 1,
    }
    assert context["visible_entities"] == [
        {
            "entity_type": "saas_agent",
            "id": saas_agent_id,
            "label": "Live Commerce",
            "slug": "live-commerce",
            "description": "live-commerce",
            "operation_id": AppActionIds.SAAS_AGENT_OPEN,
            "args": {"saas_agent_id": saas_agent_id},
        }
    ]


def test_build_turn_planning_context_falls_back_to_default_active_surface():
    state = AppGraphState(node="connection_configure")

    context = build_corpus_turn_planning_context(
        projection=_projection(current_surface_id="missing.surface"),
        state=state,
    )

    assert context["current"]["surface_id"] == "connection_configure.active"
    assert context["active_surface"]["surface_id"] == "connection_configure.active"


def test_normalize_turn_plan_keeps_legal_operation_and_defaults_object_fields():
    context = build_corpus_turn_planning_context(
        projection=_projection(),
        state=AppGraphState(node="connection_configure"),
    )

    plan = normalize_corpus_turn_plan(
        {
            "intent": "open_surface",
            "message": "Open connection setup.",
            "operation_id": "connection.configure",
            "confidence": 0.92,
            "preamble": "Routing now.",
        },
        planning_context=context,
    )

    assert plan == {
        "intent": "open_surface",
        "message": "Open connection setup.",
        "operation_id": "connection.configure",
        "args": {},
        "surface_intent": {},
        "confidence": 0.92,
        "preamble": "Routing now.",
    }


def test_normalize_turn_plan_keeps_declared_operation_fields_only():
    context = build_corpus_turn_planning_context(
        projection=_projection(),
        state=AppGraphState(node="connection_configure"),
    )

    plan = normalize_corpus_turn_plan(
        {
            "intent": "propose_operation",
            "message": "I can prepare that draft.",
            "operation_id": "knowledge.generate",
            "args": {
                "prompt": "Summarize catalog",
                "tone": "concise",
                "force": True,
            },
        },
        planning_context=context,
    )

    assert plan["args"] == {
        "prompt": "Summarize catalog",
        "tone": "concise",
    }


def test_normalize_turn_plan_treats_valid_operation_id_as_action_even_with_reply_intent():
    context = build_corpus_turn_planning_context(
        projection=_projection(),
        state=AppGraphState(node="connection_configure"),
    )

    plan = normalize_corpus_turn_plan(
        {
            "intent": "reply_now",
            "message": "I will prepare that draft.",
            "operation_id": "knowledge.generate",
            "args": {
                "prompt": "Summarize catalog",
                "tone": "concise",
            },
        },
        planning_context=context,
    )

    assert plan["intent"] == "propose_operation"
    assert plan["operation_id"] == "knowledge.generate"
    assert plan["args"] == {
        "prompt": "Summarize catalog",
        "tone": "concise",
    }


def test_normalize_turn_plan_accepts_valid_product_surface_intent():
    context = build_corpus_turn_planning_context(
        projection=_projection(),
        state=AppGraphState(node="connection_configure", active_surface_id="connection_configure.active"),
    )

    plan = normalize_corpus_turn_plan(
        {
            "intent": "open_surface",
            "message": "Switch to knowledge.",
            "operation_id": None,
            "args": {},
            "surface_intent": {"surface_id": "knowledge.active"},
        },
        planning_context=context,
    )

    assert plan["operation_id"] is None
    assert plan["args"] == {}
    assert plan["surface_intent"] == {"surface_id": "knowledge.active"}


def test_normalize_turn_plan_rejects_invalid_product_surface_intent():
    context = build_corpus_turn_planning_context(
        projection=_projection(),
        state=AppGraphState(node="connection_configure", active_surface_id="connection_configure.active"),
    )

    plan = normalize_corpus_turn_plan(
        {
            "intent": "open_surface",
            "message": "Switch elsewhere.",
            "operation_id": None,
            "args": {},
            "surface_intent": {"surface_id": "learning.failed_executions"},
        },
        planning_context=context,
    )

    assert plan["intent"] == "clarify"


def test_normalize_turn_plan_rejects_hidden_route_operation():
    context = build_corpus_turn_planning_context(
        projection=_projection(),
        state=AppGraphState(node="connection_configure", active_surface_id="connection_configure.active"),
    )

    plan = normalize_corpus_turn_plan(
        {
            "intent": "open_surface",
            "message": "Open knowledge review.",
            "operation_id": AppActionIds.ROUTE_OPEN_NODE,
            "args": {"node_id": "knowledge"},
        },
        planning_context=context,
    )

    assert plan["intent"] == "clarify"


def test_normalize_turn_plan_downgrades_illegal_operation_to_clarify():
    context = build_corpus_turn_planning_context(
        projection=_projection(),
        state=AppGraphState(node="connection_configure"),
    )

    plan = normalize_corpus_turn_plan(
        {
            "intent": "propose_operation",
            "message": "I can queue that action.",
            "operation_id": "recovery.reset_everything",
            "args": {"force": True},
            "surface_intent": {"surface_id": "recovery.active"},
            "confidence": 1.8,
            "preamble": 12,
        },
        planning_context=context,
    )

    assert plan == {
        "intent": "clarify",
        "message": "I need a clearer next step from the currently available options.",
        "operation_id": None,
        "args": {},
        "surface_intent": {},
        "confidence": 0.0,
        "preamble": None,
    }


def test_normalize_turn_plan_rejects_unknown_intent_and_non_object_payloads():
    context = build_corpus_turn_planning_context(
        projection=_projection(),
        state=AppGraphState(node="connection_configure"),
    )

    plan = normalize_corpus_turn_plan(
        {
            "intent": "jump_somewhere",
            "message": ["not", "a", "string"],
            "operation_id": "connection.configure",
            "args": "bad",
            "surface_intent": ["bad"],
            "confidence": -0.5,
        },
        planning_context=context,
    )

    assert plan == {
        "intent": "clarify",
        "message": "I need a clearer next step from the currently available options.",
        "operation_id": None,
        "args": {},
        "surface_intent": {},
        "confidence": 0.0,
        "preamble": None,
    }
