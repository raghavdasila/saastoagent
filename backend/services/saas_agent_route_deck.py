from __future__ import annotations

import uuid
from dataclasses import dataclass, replace
from typing import Any

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.core.models import ActionNode, AgentExecutionTrace, Connection, ConnectionActivationState, GeneratedTool, SaaSAgent
from backend.core.schemas import EntryActionCard, EntryActionField
from routedeck_core import build_runtime_snapshot as build_core_runtime_snapshot
from routedeck_core import reachable_nodes as core_reachable_nodes
from routedeck_core import validate_manifest

from routedeck_core import (
    RouteDeckActionSpec,
    RouteDeckEdgeSpec,
    RouteDeckFieldSpec,
    RouteDeckManifest,
    RouteDeckNodeSpec,
    RouteDeckSensitivePolicy,
)

ROUTE_DECK_VERSION = "route_deck_saas_agent_v1"
MASKED_PAYLOAD_KEYS = ["credential_value", "token", "api_key", "password"]


class SaaSAgentRouteNodeIds:
    AGENT_BOOTSTRAP = "agent_bootstrap"
    NEEDS_CONNECTION = "needs_connection"
    CONNECTION_TYPE = "connection_type"
    SCHEMA_PREVIEW = "schema_preview"
    CATALOG_ACTIVATION = "catalog_activation"
    CATALOG_READY = "catalog_ready"
    ACTION_INSPECTION = "action_inspection"
    EXECUTION_PLANNING = "execution_planning"
    NEEDS_INPUT = "needs_input"
    APPROVAL_REQUIRED = "approval_required"
    EXECUTING = "executing"
    RESULT_REVIEW = "result_review"
    LEARNING_REVIEW = "learning_review"


class SaaSAgentRouteActionIds:
    CONNECTION_START = "agent.connection.start"
    CONNECTION_CONFIGURE_REST = "agent.connection.configure_rest"
    CONNECTION_PREVIEW_SCHEMA = "agent.connection.preview_schema"
    CONNECTION_ACTIVATE = "agent.connection.activate"
    CATALOG_INSPECT = "agent.catalog.inspect"
    ACTION_INSPECT = "agent.action.inspect"
    EXECUTION_PLAN = "agent.execution.plan"
    INPUT_PROVIDE = "agent.execution.provide_input"
    APPROVAL_APPROVE = "agent.approval.approve"
    APPROVAL_REJECT = "agent.approval.reject"
    EXECUTION_REVIEW = "agent.execution.review_result"
    LEARNING_REVIEW = "agent.learning.review"


def _field(**kwargs: Any) -> RouteDeckFieldSpec:
    return RouteDeckFieldSpec(**kwargs)


REST_CONNECTION_FIELDS = [
    _field(
        key="name",
        label="Connection name",
        required=True,
        placeholder="Production API",
        validation_hint="Short name for this SaaS Agent API connection.",
    ),
    _field(
        key="base_url",
        label="Base URL",
        field_type="url",
        required=True,
        placeholder="https://api.example.com",
        validation_hint="Must start with http:// or https://.",
    ),
    _field(
        key="spec_url",
        label="OpenAPI spec URL",
        field_type="url",
        required=True,
        placeholder="https://api.example.com/openapi.json",
        validation_hint="Must point to a reachable OpenAPI JSON or YAML document.",
    ),
    _field(
        key="auth_type",
        label="Auth type",
        field_type="select",
        required=True,
        default="none",
        options=[
            {"value": "none", "label": "No auth"},
            {"value": "bearer", "label": "Bearer token"},
            {"value": "api_key_header", "label": "API key header"},
            {"value": "api_key_query", "label": "API key query param"},
            {"value": "basic", "label": "Basic auth"},
            {"value": "custom_header", "label": "Custom header"},
        ],
    ),
    _field(
        key="credential_value",
        label="Credential",
        field_type="password",
        placeholder="Token, API key, or user:pass",
        help_text="Leave empty when auth type is No auth.",
        sensitive=True,
    ),
    _field(key="header_name", label="Header name", placeholder="Authorization"),
    _field(key="query_param_name", label="Query param name", placeholder="api_key"),
]


NODE_SPECS: dict[str, RouteDeckNodeSpec] = {
    SaaSAgentRouteNodeIds.AGENT_BOOTSTRAP: RouteDeckNodeSpec(
        id=SaaSAgentRouteNodeIds.AGENT_BOOTSTRAP,
        label="Agent Bootstrap",
        lane="system",
        description="Resolve the selected SaaS Agent and derive its operator runtime state.",
        allowed_actions=[SaaSAgentRouteActionIds.CONNECTION_START],
        recovery_prompt="Select or create a SaaS Agent, then connect the API it should operate.",
    ),
    SaaSAgentRouteNodeIds.NEEDS_CONNECTION: RouteDeckNodeSpec(
        id=SaaSAgentRouteNodeIds.NEEDS_CONNECTION,
        label="Needs Connection",
        lane="saas_agent",
        description="The selected SaaS Agent has no API connection yet.",
        allowed_actions=[SaaSAgentRouteActionIds.CONNECTION_START],
        recovery_prompt="Add a REST API connection before catalog, execution, memory, or learning can run.",
    ),
    SaaSAgentRouteNodeIds.CONNECTION_TYPE: RouteDeckNodeSpec(
        id=SaaSAgentRouteNodeIds.CONNECTION_TYPE,
        label="Connection Type",
        lane="saas_agent",
        description="Choose the connection provider. REST API is the first supported provider.",
        allowed_actions=[SaaSAgentRouteActionIds.CONNECTION_CONFIGURE_REST],
        expected_input="REST API connection details.",
        recovery_prompt="Choose REST API and provide name, base URL, OpenAPI spec URL, and auth type.",
    ),
    SaaSAgentRouteNodeIds.SCHEMA_PREVIEW: RouteDeckNodeSpec(
        id=SaaSAgentRouteNodeIds.SCHEMA_PREVIEW,
        label="Schema Preview",
        lane="saas_agent",
        description="Preview the OpenAPI schema before activating catalog generation.",
        allowed_actions=[
            SaaSAgentRouteActionIds.CONNECTION_PREVIEW_SCHEMA,
            SaaSAgentRouteActionIds.CONNECTION_ACTIVATE,
        ],
        recovery_prompt="Preview or activate the saved OpenAPI connection.",
    ),
    SaaSAgentRouteNodeIds.CATALOG_ACTIVATION: RouteDeckNodeSpec(
        id=SaaSAgentRouteNodeIds.CATALOG_ACTIVATION,
        label="Catalog Activation",
        lane="saas_agent",
        description="Generate action nodes, embeddings, and callable tools from the API schema.",
        allowed_actions=[SaaSAgentRouteActionIds.CONNECTION_ACTIVATE, SaaSAgentRouteActionIds.CATALOG_INSPECT],
        recovery_prompt="Activate the connection, then inspect the generated action catalog.",
    ),
    SaaSAgentRouteNodeIds.CATALOG_READY: RouteDeckNodeSpec(
        id=SaaSAgentRouteNodeIds.CATALOG_READY,
        label="Catalog Ready",
        lane="saas_agent",
        description="The SaaS Agent has a generated API catalog and can inspect available actions.",
        allowed_actions=[SaaSAgentRouteActionIds.CATALOG_INSPECT, SaaSAgentRouteActionIds.ACTION_INSPECT],
        recovery_prompt="Inspect catalog actions or ask the agent what it can do.",
    ),
    SaaSAgentRouteNodeIds.ACTION_INSPECTION: RouteDeckNodeSpec(
        id=SaaSAgentRouteNodeIds.ACTION_INSPECTION,
        label="Action Inspection",
        lane="saas_agent",
        description="Inspect generated tools, parameters, risk levels, and approval requirements.",
        allowed_actions=[SaaSAgentRouteActionIds.EXECUTION_PLAN, SaaSAgentRouteActionIds.CATALOG_INSPECT],
        recovery_prompt="Choose an action to plan execution or return to the catalog.",
    ),
    SaaSAgentRouteNodeIds.EXECUTION_PLANNING: RouteDeckNodeSpec(
        id=SaaSAgentRouteNodeIds.EXECUTION_PLANNING,
        label="Execution Planning",
        lane="saas_agent",
        description="Turn a user request into a concrete tool plan with needed inputs and approvals.",
        allowed_actions=[SaaSAgentRouteActionIds.INPUT_PROVIDE, SaaSAgentRouteActionIds.APPROVAL_APPROVE],
        expected_input="Execution goal and required parameters.",
        recovery_prompt="Provide missing inputs or approve the prepared plan.",
    ),
    SaaSAgentRouteNodeIds.NEEDS_INPUT: RouteDeckNodeSpec(
        id=SaaSAgentRouteNodeIds.NEEDS_INPUT,
        label="Needs Input",
        lane="saas_agent",
        description="Execution is blocked until the user supplies required tool parameters.",
        allowed_actions=[SaaSAgentRouteActionIds.INPUT_PROVIDE],
        expected_input="Missing API action inputs.",
        recovery_prompt="Supply the missing values requested by the agent.",
    ),
    SaaSAgentRouteNodeIds.APPROVAL_REQUIRED: RouteDeckNodeSpec(
        id=SaaSAgentRouteNodeIds.APPROVAL_REQUIRED,
        label="Approval Required",
        lane="saas_agent",
        description="A planned action requires explicit approval before execution.",
        allowed_actions=[SaaSAgentRouteActionIds.APPROVAL_APPROVE, SaaSAgentRouteActionIds.APPROVAL_REJECT],
        recovery_prompt="Approve or reject the planned action.",
    ),
    SaaSAgentRouteNodeIds.EXECUTING: RouteDeckNodeSpec(
        id=SaaSAgentRouteNodeIds.EXECUTING,
        label="Executing",
        lane="saas_agent",
        description="A tool execution is in flight against the connected API.",
        allowed_actions=[SaaSAgentRouteActionIds.EXECUTION_REVIEW],
        recovery_prompt="Wait for the execution result, then review it.",
    ),
    SaaSAgentRouteNodeIds.RESULT_REVIEW: RouteDeckNodeSpec(
        id=SaaSAgentRouteNodeIds.RESULT_REVIEW,
        label="Result Review",
        lane="saas_agent",
        description="Review tool outputs, evidence, and any follow-up actions.",
        allowed_actions=[SaaSAgentRouteActionIds.LEARNING_REVIEW, SaaSAgentRouteActionIds.EXECUTION_PLAN],
        recovery_prompt="Review the result, save learning if useful, or plan the next action.",
    ),
    SaaSAgentRouteNodeIds.LEARNING_REVIEW: RouteDeckNodeSpec(
        id=SaaSAgentRouteNodeIds.LEARNING_REVIEW,
        label="Learning Review",
        lane="saas_agent",
        description="Promote verified observations into memory or sandbox learning candidates.",
        allowed_actions=[SaaSAgentRouteActionIds.LEARNING_REVIEW, SaaSAgentRouteActionIds.CATALOG_INSPECT],
        recovery_prompt="Review learning candidates or return to catalog inspection.",
    ),
}


ACTION_SPECS: dict[str, RouteDeckActionSpec] = {
    SaaSAgentRouteActionIds.CONNECTION_START: RouteDeckActionSpec(
        id=SaaSAgentRouteActionIds.CONNECTION_START,
        label="Add API",
        description="Open the REST API connection setup for this SaaS Agent.",
        emphasis="primary",
        kind="nav",
        category="setup",
        placement="next_best",
        allowed_nodes=[SaaSAgentRouteNodeIds.AGENT_BOOTSTRAP, SaaSAgentRouteNodeIds.NEEDS_CONNECTION],
        payload={"target_surface": "connect"},
    ),
    SaaSAgentRouteActionIds.CONNECTION_CONFIGURE_REST: RouteDeckActionSpec(
        id=SaaSAgentRouteActionIds.CONNECTION_CONFIGURE_REST,
        label="Configure REST API",
        description="Configure name, base URL, spec URL, and auth for a REST API connection.",
        emphasis="primary",
        kind="form",
        category="setup",
        placement="next_best",
        fields=REST_CONNECTION_FIELDS,
        allowed_nodes=[SaaSAgentRouteNodeIds.CONNECTION_TYPE],
        payload={"provider": "rest_api", "target_surface": "connect"},
    ),
    SaaSAgentRouteActionIds.CONNECTION_PREVIEW_SCHEMA: RouteDeckActionSpec(
        id=SaaSAgentRouteActionIds.CONNECTION_PREVIEW_SCHEMA,
        label="Preview Schema",
        description="Preview OpenAPI operations before catalog generation.",
        kind="button",
        category="setup",
        placement="rail",
        allowed_nodes=[SaaSAgentRouteNodeIds.SCHEMA_PREVIEW],
        payload={"target_surface": "connect"},
    ),
    SaaSAgentRouteActionIds.CONNECTION_ACTIVATE: RouteDeckActionSpec(
        id=SaaSAgentRouteActionIds.CONNECTION_ACTIVATE,
        label="Activate Catalog",
        description="Generate action nodes, embeddings, and tools from the saved schema.",
        emphasis="primary",
        kind="button",
        category="setup",
        placement="next_best",
        allowed_nodes=[SaaSAgentRouteNodeIds.SCHEMA_PREVIEW, SaaSAgentRouteNodeIds.CATALOG_ACTIVATION],
        payload={"target_surface": "connect"},
    ),
    SaaSAgentRouteActionIds.CATALOG_INSPECT: RouteDeckActionSpec(
        id=SaaSAgentRouteActionIds.CATALOG_INSPECT,
        label="Inspect Catalog",
        description="Open generated entities, actions, and tools for this SaaS Agent.",
        kind="nav",
        category="navigation",
        placement="rail",
        allowed_nodes=[
            SaaSAgentRouteNodeIds.CATALOG_ACTIVATION,
            SaaSAgentRouteNodeIds.CATALOG_READY,
            SaaSAgentRouteNodeIds.ACTION_INSPECTION,
            SaaSAgentRouteNodeIds.LEARNING_REVIEW,
        ],
        payload={"target_surface": "actions"},
    ),
    SaaSAgentRouteActionIds.ACTION_INSPECT: RouteDeckActionSpec(
        id=SaaSAgentRouteActionIds.ACTION_INSPECT,
        label="Inspect Actions",
        description="Review generated tools and risk metadata.",
        kind="nav",
        category="navigation",
        placement="next_best",
        allowed_nodes=[SaaSAgentRouteNodeIds.CATALOG_READY],
        payload={"target_surface": "actions"},
    ),
    SaaSAgentRouteActionIds.EXECUTION_PLAN: RouteDeckActionSpec(
        id=SaaSAgentRouteActionIds.EXECUTION_PLAN,
        label="Plan Execution",
        description="Prepare a tool plan from the current request and catalog.",
        emphasis="primary",
        kind="button",
        category="execution",
        placement="next_best",
        allowed_nodes=[SaaSAgentRouteNodeIds.ACTION_INSPECTION, SaaSAgentRouteNodeIds.RESULT_REVIEW],
        payload={"target_surface": "chat"},
    ),
    SaaSAgentRouteActionIds.INPUT_PROVIDE: RouteDeckActionSpec(
        id=SaaSAgentRouteActionIds.INPUT_PROVIDE,
        label="Provide Inputs",
        description="Supply missing execution parameters.",
        kind="button",
        category="execution",
        placement="next_best",
        allowed_nodes=[SaaSAgentRouteNodeIds.EXECUTION_PLANNING, SaaSAgentRouteNodeIds.NEEDS_INPUT],
        payload={"target_surface": "chat"},
    ),
    SaaSAgentRouteActionIds.APPROVAL_APPROVE: RouteDeckActionSpec(
        id=SaaSAgentRouteActionIds.APPROVAL_APPROVE,
        label="Approve",
        description="Approve the planned action for execution.",
        emphasis="primary",
        kind="button",
        category="execution",
        placement="next_best",
        allowed_nodes=[SaaSAgentRouteNodeIds.EXECUTION_PLANNING, SaaSAgentRouteNodeIds.APPROVAL_REQUIRED],
        payload={"target_surface": "chat"},
    ),
    SaaSAgentRouteActionIds.APPROVAL_REJECT: RouteDeckActionSpec(
        id=SaaSAgentRouteActionIds.APPROVAL_REJECT,
        label="Reject",
        description="Reject the planned action and return to planning.",
        kind="button",
        category="execution",
        placement="rail",
        allowed_nodes=[SaaSAgentRouteNodeIds.APPROVAL_REQUIRED],
        payload={"target_surface": "chat"},
    ),
    SaaSAgentRouteActionIds.EXECUTION_REVIEW: RouteDeckActionSpec(
        id=SaaSAgentRouteActionIds.EXECUTION_REVIEW,
        label="Review Result",
        description="Inspect the latest execution result and evidence.",
        kind="nav",
        category="feedback",
        placement="next_best",
        allowed_nodes=[SaaSAgentRouteNodeIds.EXECUTING],
        payload={"target_surface": "chat"},
    ),
    SaaSAgentRouteActionIds.LEARNING_REVIEW: RouteDeckActionSpec(
        id=SaaSAgentRouteActionIds.LEARNING_REVIEW,
        label="Review Learning",
        description="Inspect memory and sandbox learning candidates.",
        kind="nav",
        category="learning",
        placement="rail",
        allowed_nodes=[SaaSAgentRouteNodeIds.RESULT_REVIEW, SaaSAgentRouteNodeIds.LEARNING_REVIEW],
        payload={"target_surface": "learn"},
    ),
}


EDGE_SPECS = [
    RouteDeckEdgeSpec(from_stage=SaaSAgentRouteNodeIds.AGENT_BOOTSTRAP, to_stage=SaaSAgentRouteNodeIds.NEEDS_CONNECTION, type="conditional", condition="no_connection"),
    RouteDeckEdgeSpec(from_stage=SaaSAgentRouteNodeIds.AGENT_BOOTSTRAP, to_stage=SaaSAgentRouteNodeIds.CATALOG_READY, type="conditional", condition="catalog_ready"),
    RouteDeckEdgeSpec(from_stage=SaaSAgentRouteNodeIds.NEEDS_CONNECTION, to_stage=SaaSAgentRouteNodeIds.CONNECTION_TYPE, type="sequence", action_id=SaaSAgentRouteActionIds.CONNECTION_START),
    RouteDeckEdgeSpec(from_stage=SaaSAgentRouteNodeIds.CONNECTION_TYPE, to_stage=SaaSAgentRouteNodeIds.SCHEMA_PREVIEW, type="sequence", action_id=SaaSAgentRouteActionIds.CONNECTION_CONFIGURE_REST),
    RouteDeckEdgeSpec(from_stage=SaaSAgentRouteNodeIds.SCHEMA_PREVIEW, to_stage=SaaSAgentRouteNodeIds.CATALOG_ACTIVATION, type="sequence", action_id=SaaSAgentRouteActionIds.CONNECTION_ACTIVATE),
    RouteDeckEdgeSpec(from_stage=SaaSAgentRouteNodeIds.CATALOG_ACTIVATION, to_stage=SaaSAgentRouteNodeIds.CATALOG_READY, type="conditional", condition="activation_ready"),
    RouteDeckEdgeSpec(from_stage=SaaSAgentRouteNodeIds.CATALOG_READY, to_stage=SaaSAgentRouteNodeIds.ACTION_INSPECTION, type="sequence", action_id=SaaSAgentRouteActionIds.ACTION_INSPECT),
    RouteDeckEdgeSpec(from_stage=SaaSAgentRouteNodeIds.ACTION_INSPECTION, to_stage=SaaSAgentRouteNodeIds.EXECUTION_PLANNING, type="sequence", action_id=SaaSAgentRouteActionIds.EXECUTION_PLAN),
    RouteDeckEdgeSpec(from_stage=SaaSAgentRouteNodeIds.EXECUTION_PLANNING, to_stage=SaaSAgentRouteNodeIds.NEEDS_INPUT, type="conditional", condition="missing_inputs"),
    RouteDeckEdgeSpec(from_stage=SaaSAgentRouteNodeIds.NEEDS_INPUT, to_stage=SaaSAgentRouteNodeIds.EXECUTION_PLANNING, type="sequence", action_id=SaaSAgentRouteActionIds.INPUT_PROVIDE),
    RouteDeckEdgeSpec(from_stage=SaaSAgentRouteNodeIds.EXECUTION_PLANNING, to_stage=SaaSAgentRouteNodeIds.APPROVAL_REQUIRED, type="conditional", condition="approval_needed"),
    RouteDeckEdgeSpec(from_stage=SaaSAgentRouteNodeIds.APPROVAL_REQUIRED, to_stage=SaaSAgentRouteNodeIds.EXECUTING, type="sequence", action_id=SaaSAgentRouteActionIds.APPROVAL_APPROVE),
    RouteDeckEdgeSpec(from_stage=SaaSAgentRouteNodeIds.APPROVAL_REQUIRED, to_stage=SaaSAgentRouteNodeIds.EXECUTION_PLANNING, type="conditional", action_id=SaaSAgentRouteActionIds.APPROVAL_REJECT),
    RouteDeckEdgeSpec(from_stage=SaaSAgentRouteNodeIds.EXECUTING, to_stage=SaaSAgentRouteNodeIds.RESULT_REVIEW, type="sequence", action_id=SaaSAgentRouteActionIds.EXECUTION_REVIEW),
    RouteDeckEdgeSpec(from_stage=SaaSAgentRouteNodeIds.RESULT_REVIEW, to_stage=SaaSAgentRouteNodeIds.LEARNING_REVIEW, type="sequence", action_id=SaaSAgentRouteActionIds.LEARNING_REVIEW),
    RouteDeckEdgeSpec(from_stage=SaaSAgentRouteNodeIds.RESULT_REVIEW, to_stage=SaaSAgentRouteNodeIds.EXECUTION_PLANNING, type="sequence", action_id=SaaSAgentRouteActionIds.EXECUTION_PLAN),
    RouteDeckEdgeSpec(from_stage=SaaSAgentRouteNodeIds.LEARNING_REVIEW, to_stage=SaaSAgentRouteNodeIds.CATALOG_READY, type="sequence", action_id=SaaSAgentRouteActionIds.CATALOG_INSPECT),
]


TEST_PATHS = [
    {
        "id": "new_agent_connection_setup",
        "start": SaaSAgentRouteNodeIds.AGENT_BOOTSTRAP,
        "actions": [SaaSAgentRouteActionIds.CONNECTION_START, SaaSAgentRouteActionIds.CONNECTION_CONFIGURE_REST, SaaSAgentRouteActionIds.CONNECTION_ACTIVATE],
        "expected_nodes": [SaaSAgentRouteNodeIds.NEEDS_CONNECTION, SaaSAgentRouteNodeIds.CONNECTION_TYPE, SaaSAgentRouteNodeIds.SCHEMA_PREVIEW, SaaSAgentRouteNodeIds.CATALOG_ACTIVATION],
    },
    {
        "id": "catalog_to_execution",
        "start": SaaSAgentRouteNodeIds.CATALOG_READY,
        "actions": [SaaSAgentRouteActionIds.ACTION_INSPECT, SaaSAgentRouteActionIds.EXECUTION_PLAN, SaaSAgentRouteActionIds.APPROVAL_APPROVE],
        "expected_nodes": [SaaSAgentRouteNodeIds.ACTION_INSPECTION, SaaSAgentRouteNodeIds.EXECUTION_PLANNING, SaaSAgentRouteNodeIds.APPROVAL_REQUIRED, SaaSAgentRouteNodeIds.EXECUTING],
    },
]


@dataclass(frozen=True)
class SaaSAgentRouteDeckFacts:
    connection_count: int
    ready_connection_count: int
    action_count: int
    tool_count: int
    latest_connection_id: uuid.UUID | None = None
    latest_connection_name: str | None = None
    latest_activation_status: str | None = None
    latest_activation_step: str | None = None
    blocked_reason: str | None = None
    latest_execution_id: uuid.UUID | None = None
    latest_execution_status: str | None = None
    latest_execution_approval_state: str | None = None
    latest_execution_tool_name: str | None = None
    latest_execution_risk: str | None = None


def _field_card(field: RouteDeckFieldSpec, draft: dict[str, Any] | None = None) -> EntryActionField:
    draft = draft or {}
    default = draft.get(field.key, field.default)
    if field.sensitive:
        default = ""
    return EntryActionField(
        key=field.key,
        label=field.label,
        field_type=field.field_type,
        required=field.required,
        placeholder=field.placeholder,
        default=default,
        options=field.options,
        help_text=field.help_text,
        validation_hint=field.validation_hint,
        sensitive=field.sensitive,
    )


def action_card(action_id: str, *, disabled_reason: str | None = None) -> EntryActionCard:
    spec = ACTION_SPECS[action_id]
    return EntryActionCard(
        id=spec.id,
        label=spec.label,
        capability_id=spec.capability_id,
        description=spec.description,
        emphasis=spec.emphasis,
        kind=spec.kind,
        category=spec.category,
        placement=spec.placement,
        fields=[_field_card(field) for field in spec.fields],
        payload=dict(spec.payload),
        disabled_reason=disabled_reason,
    )


def build_saas_agent_route_deck_manifest() -> RouteDeckManifest:
    sensitive_policy = RouteDeckSensitivePolicy(
        masked_payload_keys=MASKED_PAYLOAD_KEYS,
        chat_secret_fields=[],
        url_or_modal_only_fields=["credential_value"],
        note="Secrets can only be sent through controlled connection fields and must remain masked in logs and UI echoes.",
    )
    return RouteDeckManifest(
        version=ROUTE_DECK_VERSION,
        nodes=list(NODE_SPECS.values()),
        edges=EDGE_SPECS,
        actions=list(ACTION_SPECS.values()),
        policies={"sensitive": sensitive_policy.model_dump(mode="json")},
        test_paths=TEST_PATHS,
    )


def validate_saas_agent_route_deck_manifest() -> list[str]:
    return validate_manifest(build_saas_agent_route_deck_manifest(), masked_payload_keys=MASKED_PAYLOAD_KEYS)


def infer_current_node(facts: SaaSAgentRouteDeckFacts) -> str:
    if facts.latest_execution_status == "approval_required" and facts.latest_execution_approval_state == "pending":
        return SaaSAgentRouteNodeIds.APPROVAL_REQUIRED
    if facts.latest_execution_status == "needs_input":
        return SaaSAgentRouteNodeIds.NEEDS_INPUT
    if facts.latest_execution_status == "executing":
        return SaaSAgentRouteNodeIds.EXECUTING
    if facts.latest_execution_status in {"succeeded", "failed", "canceled"}:
        return SaaSAgentRouteNodeIds.RESULT_REVIEW
    if facts.connection_count == 0:
        return SaaSAgentRouteNodeIds.NEEDS_CONNECTION
    if facts.ready_connection_count > 0 and facts.tool_count > 0:
        return SaaSAgentRouteNodeIds.CATALOG_READY
    if facts.action_count > 0 or facts.latest_activation_status in {"running", "ready"}:
        return SaaSAgentRouteNodeIds.CATALOG_ACTIVATION
    return SaaSAgentRouteNodeIds.SCHEMA_PREVIEW


def contextual_actions_for_node(node: str) -> list[EntryActionCard]:
    node_spec = NODE_SPECS[node]
    return [action_card(action_id) for action_id in node_spec.allowed_actions]


def blocked_actions_for_node(node: str) -> list[dict[str, str]]:
    blocked: list[dict[str, str]] = []
    for action_id, spec in ACTION_SPECS.items():
        if node not in spec.allowed_nodes:
            blocked.append({"id": action_id, "reason": f"Only valid in: {', '.join(spec.allowed_nodes)}"})
    return blocked


async def collect_saas_agent_route_deck_facts(db: AsyncSession, saas_agent_id: uuid.UUID) -> SaaSAgentRouteDeckFacts:
    connection_count = int(
        (await db.execute(select(func.count(Connection.id)).where(Connection.saas_agent_id == saas_agent_id))).scalar_one()
    )
    ready_connection_count = int(
        (
            await db.execute(
                select(func.count(ConnectionActivationState.connection_id)).where(
                    ConnectionActivationState.saas_agent_id == saas_agent_id,
                    ConnectionActivationState.overall_status == "ready",
                )
            )
        ).scalar_one()
    )
    action_count = int((await db.execute(select(func.count(ActionNode.id)).where(ActionNode.saas_agent_id == saas_agent_id))).scalar_one())
    tool_count = int((await db.execute(select(func.count(GeneratedTool.id)).where(GeneratedTool.saas_agent_id == saas_agent_id))).scalar_one())

    latest = (
        await db.execute(
            select(Connection, ConnectionActivationState)
            .outerjoin(ConnectionActivationState, ConnectionActivationState.connection_id == Connection.id)
            .where(Connection.saas_agent_id == saas_agent_id)
            .order_by(Connection.created_at.desc())
            .limit(1)
        )
    ).first()
    if latest is None:
        facts = SaaSAgentRouteDeckFacts(
            connection_count=connection_count,
            ready_connection_count=ready_connection_count,
            action_count=action_count,
            tool_count=tool_count,
        )
    else:
        connection, state = latest
        facts = SaaSAgentRouteDeckFacts(
            connection_count=connection_count,
            ready_connection_count=ready_connection_count,
            action_count=action_count,
            tool_count=tool_count,
            latest_connection_id=connection.id,
            latest_connection_name=connection.name,
            latest_activation_status=state.overall_status if state else None,
            latest_activation_step=state.current_step if state else None,
            blocked_reason=state.blocked_reason if state else None,
        )

    trace = (
        await db.execute(
            select(AgentExecutionTrace)
            .where(AgentExecutionTrace.saas_agent_id == saas_agent_id)
            .order_by(AgentExecutionTrace.created_at.desc())
            .limit(1)
        )
    ).scalar_one_or_none()
    if trace is None:
        return facts
    return replace(
        facts,
        latest_execution_id=trace.id,
        latest_execution_status=trace.status,
        latest_execution_approval_state=trace.approval_state,
        latest_execution_tool_name=trace.tool_name,
        latest_execution_risk=trace.risk_level,
    )


async def build_saas_agent_route_deck_response(db: AsyncSession, saas_agent_id: uuid.UUID) -> dict[str, Any]:
    agent = (await db.execute(select(SaaSAgent).where(SaaSAgent.id == saas_agent_id))).scalar_one_or_none()
    facts = await collect_saas_agent_route_deck_facts(db, saas_agent_id)
    current_node = infer_current_node(facts)
    manifest = build_saas_agent_route_deck_manifest()
    valid_actions = contextual_actions_for_node(current_node)
    snapshot = build_core_runtime_snapshot(
        manifest,
        current_node=current_node,
        valid_actions=[action.model_dump(mode="json") for action in valid_actions],
        blocked_actions=blocked_actions_for_node(current_node),
        executed_nodes=[SaaSAgentRouteNodeIds.AGENT_BOOTSTRAP] if current_node != SaaSAgentRouteNodeIds.AGENT_BOOTSTRAP else [],
        diagnostics={
            "source": "saas_agent_route_deck",
            "state_basis": "connection_catalog_counts",
            "connection_count": facts.connection_count,
            "ready_connection_count": facts.ready_connection_count,
            "action_count": facts.action_count,
            "tool_count": facts.tool_count,
            "latest_execution_status": facts.latest_execution_status,
            "latest_execution_approval_state": facts.latest_execution_approval_state,
        },
    )
    working_on = {
        SaaSAgentRouteNodeIds.NEEDS_CONNECTION: "Connect a REST API before this SaaS Agent can inspect or execute work.",
        SaaSAgentRouteNodeIds.SCHEMA_PREVIEW: "Review the saved API schema and activate catalog generation.",
        SaaSAgentRouteNodeIds.CATALOG_ACTIVATION: "Generate and verify action nodes, embeddings, and tools from the API schema.",
        SaaSAgentRouteNodeIds.CATALOG_READY: "Inspect generated actions or ask the agent to plan API work.",
        SaaSAgentRouteNodeIds.NEEDS_INPUT: "Supply missing parameters for the latest generated REST action plan.",
        SaaSAgentRouteNodeIds.APPROVAL_REQUIRED: "Approve or cancel the latest risky generated REST action before it can execute.",
        SaaSAgentRouteNodeIds.EXECUTING: "Wait for the current generated REST action to finish.",
        SaaSAgentRouteNodeIds.RESULT_REVIEW: "Review the latest execution result and trace evidence.",
    }.get(current_node, NODE_SPECS[current_node].description)

    return {
        "manifest": manifest.model_dump(mode="json", by_alias=True),
        "snapshot": snapshot,
        "context": {
            "saas_agent_id": str(saas_agent_id),
            "saas_agent_name": agent.name if agent else None,
            "saas_agent_slug": agent.slug if agent else None,
            "current_node": current_node,
            "current_label": NODE_SPECS[current_node].label,
            "working_on": working_on,
            "connection_count": facts.connection_count,
            "ready_connection_count": facts.ready_connection_count,
            "action_count": facts.action_count,
            "tool_count": facts.tool_count,
            "latest_connection_id": str(facts.latest_connection_id) if facts.latest_connection_id else None,
            "latest_connection_name": facts.latest_connection_name,
            "latest_activation_status": facts.latest_activation_status,
            "latest_activation_step": facts.latest_activation_step,
            "blocked_reason": facts.blocked_reason,
            "latest_execution_id": str(facts.latest_execution_id) if facts.latest_execution_id else None,
            "latest_execution_status": facts.latest_execution_status,
            "latest_execution_approval_state": facts.latest_execution_approval_state,
            "latest_execution_tool_name": facts.latest_execution_tool_name,
            "latest_execution_risk": facts.latest_execution_risk,
            "reachable_nodes": core_reachable_nodes(manifest, current_node),
        },
    }
