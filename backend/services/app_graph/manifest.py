from __future__ import annotations

from typing import Any

from backend.core.schemas import EntryActionCard, EntryActionField
from backend.services.route_deck.models import (
    RouteDeckActionSpec,
    RouteDeckEdgeSpec,
    RouteDeckFieldSpec,
    RouteDeckManifest,
    RouteDeckNodeSpec,
    RouteDeckSensitivePolicy,
)
from routedeck_core import validate_manifest

APP_GRAPH_VERSION = "app_graph_routedeck_v1"


class AppNodeIds:
    HOME = "home"
    AUTH_SIGN_IN = "auth_sign_in"
    AUTH_REGISTER = "auth_register"
    SAAS_AGENT_SELECT = "saas_agent_select"
    SAAS_AGENT_CREATE = "saas_agent_create"
    AGENT_HOME = "agent_home"
    INSTRUCTIONS = "instructions"
    CONNECTION_CONFIGURE = "connection_configure"
    SCHEMA_PREVIEW = "schema_preview"
    CATALOG_ACTIVATION = "catalog_activation"
    CATALOG = "catalog"
    ENTITIES = "entities"
    ACTIONS = "actions"
    EXECUTION_PLANNING = "execution_planning"
    NEEDS_INPUT = "needs_input"
    APPROVAL_REQUIRED = "approval_required"
    EXECUTING = "executing"
    RESULT_REVIEW = "result_review"
    KNOWLEDGE = "knowledge"
    MEMORY = "memory"
    LEARNING = "learning"
    LEARNING_POLICY_CANDIDATE = "learning.policy_candidate"
    LEARNING_EXECUTION_TRACE = "learning.execution_trace"
    LEARNING_ACTIVE_POLICY = "learning.active_policy"
    QA = "qa"
    RECOVERY = "recovery"


class AppActionIds:
    HOME = "navigate.home"
    AUTH_SIGN_IN = "auth.sign_in"
    AUTH_REGISTER = "auth.register"
    SAAS_AGENT_LIST = "saas_agent.list"
    SAAS_AGENT_OPEN = "saas_agent.open"
    SAAS_AGENT_CREATE = "saas_agent.create"
    AGENT_HOME = "navigate.agent_home"
    INSTRUCTIONS_OPEN = "instructions.open"
    INSTRUCTIONS_SAVE = "instructions.save"
    CONNECTION_CONFIGURE = "navigate.connection_configure"
    CONNECTION_PREVIEW = "connection.preview"
    CONNECTION_ACTIVATE = "connection.activate"
    CATALOG_OPEN = "catalog.open"
    ENTITIES_OPEN = "entities.open"
    ACTIONS_OPEN = "actions.open"
    EXECUTION_OPEN = "execution.open"
    EXECUTION_PLAN = "execution.plan"
    EXECUTION_INPUT = "execution.provide_input"
    APPROVAL_APPROVE = "approval.approve"
    APPROVAL_REJECT = "approval.reject"
    RESULT_REVIEW = "result.review"
    KNOWLEDGE_OPEN = "knowledge.open"
    KNOWLEDGE_GENERATE = "knowledge.generate"
    MEMORY_OPEN = "memory.open"
    MEMORY_SAVE = "memory.save"
    LEARNING_OPEN = "learning.open"
    LEARNING_POLICY_CANDIDATE_OPEN = "learning.policy_candidate.open"
    LEARNING_EXECUTION_TRACE_OPEN = "learning.execution_trace.open"
    LEARNING_ACTIVE_POLICY_OPEN = "learning.active_policy.open"
    LEARNING_APPROVE = "learning.approve"
    LEARNING_REJECT = "learning.reject"
    ROUTE_BACK = "route.back"
    ROUTE_FORWARD = "route.forward"
    ROUTE_CANCEL = "route.cancel"
    ROUTE_OPEN_NODE = "route.open_node"
    ROUTE_SWITCH_SURFACE = "route.switch_surface"
    QA_OPEN = "qa.open"
    QA_RUN = "qa.run"
    RECOVERY_HOME = "recovery.home"


APP_GRAPH_GROUPS = {
    "home": {AppNodeIds.HOME},
    "auth": {AppNodeIds.AUTH_SIGN_IN, AppNodeIds.AUTH_REGISTER},
    "saas_agent": {AppNodeIds.SAAS_AGENT_SELECT, AppNodeIds.SAAS_AGENT_CREATE, AppNodeIds.AGENT_HOME, AppNodeIds.INSTRUCTIONS},
    "connection": {
        AppNodeIds.CONNECTION_CONFIGURE,
        AppNodeIds.SCHEMA_PREVIEW,
        AppNodeIds.CATALOG_ACTIVATION,
        AppNodeIds.CATALOG,
        AppNodeIds.ENTITIES,
        AppNodeIds.ACTIONS,
    },
    "execution": {
        AppNodeIds.EXECUTION_PLANNING,
        AppNodeIds.NEEDS_INPUT,
        AppNodeIds.APPROVAL_REQUIRED,
        AppNodeIds.EXECUTING,
        AppNodeIds.RESULT_REVIEW,
    },
    "knowledge": {
        AppNodeIds.KNOWLEDGE,
        AppNodeIds.MEMORY,
        AppNodeIds.LEARNING,
        AppNodeIds.LEARNING_POLICY_CANDIDATE,
        AppNodeIds.LEARNING_EXECUTION_TRACE,
        AppNodeIds.LEARNING_ACTIVE_POLICY,
    },
    "qa": {AppNodeIds.QA},
    "recovery": {AppNodeIds.RECOVERY},
}

CAPABILITY_RAIL_ITEMS = [
    {
        "id": "home",
        "label": "Home",
        "icon_key": "home",
        "nodes": [AppNodeIds.HOME],
        "operation_id": AppActionIds.HOME,
    },
    {
        "id": "agent",
        "label": "Create Agent",
        "icon_key": "sparkles",
        "nodes": [AppNodeIds.SAAS_AGENT_SELECT, AppNodeIds.SAAS_AGENT_CREATE, AppNodeIds.AGENT_HOME, AppNodeIds.INSTRUCTIONS],
        "operation_id": AppActionIds.SAAS_AGENT_CREATE,
    },
    {
        "id": "connect",
        "label": "Connect API",
        "icon_key": "plug",
        "nodes": [AppNodeIds.CONNECTION_CONFIGURE, AppNodeIds.SCHEMA_PREVIEW],
        "operation_id": AppActionIds.CONNECTION_CONFIGURE,
    },
    {
        "id": "catalog",
        "label": "Catalog",
        "icon_key": "database",
        "nodes": [AppNodeIds.CATALOG_ACTIVATION, AppNodeIds.CATALOG],
        "operation_id": AppActionIds.CATALOG_OPEN,
    },
    {
        "id": "actions",
        "label": "Actions",
        "icon_key": "wrench",
        "nodes": [AppNodeIds.ENTITIES, AppNodeIds.ACTIONS],
        "operation_id": AppActionIds.ACTIONS_OPEN,
    },
    {
        "id": "execution",
        "label": "Execution",
        "icon_key": "play",
        "nodes": [
            AppNodeIds.EXECUTION_PLANNING,
            AppNodeIds.NEEDS_INPUT,
            AppNodeIds.APPROVAL_REQUIRED,
            AppNodeIds.EXECUTING,
            AppNodeIds.RESULT_REVIEW,
        ],
        "operation_id": AppActionIds.EXECUTION_OPEN,
    },
    {
        "id": "knowledge",
        "label": "Knowledge",
        "icon_key": "book",
        "nodes": [AppNodeIds.KNOWLEDGE],
        "operation_id": AppActionIds.KNOWLEDGE_OPEN,
    },
    {
        "id": "memory",
        "label": "Memory",
        "icon_key": "brain",
        "nodes": [AppNodeIds.MEMORY],
        "operation_id": AppActionIds.MEMORY_OPEN,
    },
    {
        "id": "learning",
        "label": "Learning",
        "icon_key": "graduation",
        "nodes": [AppNodeIds.LEARNING],
        "child_nodes": [
            AppNodeIds.LEARNING_POLICY_CANDIDATE,
            AppNodeIds.LEARNING_EXECUTION_TRACE,
            AppNodeIds.LEARNING_ACTIVE_POLICY,
        ],
        "operation_id": AppActionIds.LEARNING_OPEN,
    },
    {
        "id": "qa",
        "label": "QA",
        "icon_key": "clipboard",
        "nodes": [AppNodeIds.QA],
        "operation_id": AppActionIds.QA_OPEN,
    },
]

ACTION_TARGETS = {
    AppActionIds.HOME: AppNodeIds.HOME,
    AppActionIds.AUTH_SIGN_IN: AppNodeIds.AUTH_SIGN_IN,
    AppActionIds.AUTH_REGISTER: AppNodeIds.AUTH_REGISTER,
    AppActionIds.SAAS_AGENT_LIST: AppNodeIds.SAAS_AGENT_SELECT,
    AppActionIds.SAAS_AGENT_OPEN: AppNodeIds.AGENT_HOME,
    AppActionIds.SAAS_AGENT_CREATE: AppNodeIds.AGENT_HOME,
    AppActionIds.AGENT_HOME: AppNodeIds.AGENT_HOME,
    AppActionIds.INSTRUCTIONS_OPEN: AppNodeIds.INSTRUCTIONS,
    AppActionIds.INSTRUCTIONS_SAVE: AppNodeIds.INSTRUCTIONS,
    AppActionIds.CONNECTION_CONFIGURE: AppNodeIds.CONNECTION_CONFIGURE,
    AppActionIds.CONNECTION_PREVIEW: AppNodeIds.SCHEMA_PREVIEW,
    AppActionIds.CONNECTION_ACTIVATE: AppNodeIds.CATALOG,
    AppActionIds.CATALOG_OPEN: AppNodeIds.CATALOG,
    AppActionIds.ENTITIES_OPEN: AppNodeIds.ENTITIES,
    AppActionIds.ACTIONS_OPEN: AppNodeIds.ACTIONS,
    AppActionIds.EXECUTION_OPEN: AppNodeIds.EXECUTION_PLANNING,
    AppActionIds.EXECUTION_PLAN: AppNodeIds.EXECUTION_PLANNING,
    AppActionIds.EXECUTION_INPUT: AppNodeIds.EXECUTION_PLANNING,
    AppActionIds.APPROVAL_APPROVE: AppNodeIds.RESULT_REVIEW,
    AppActionIds.APPROVAL_REJECT: AppNodeIds.RESULT_REVIEW,
    AppActionIds.RESULT_REVIEW: AppNodeIds.RESULT_REVIEW,
    AppActionIds.KNOWLEDGE_OPEN: AppNodeIds.KNOWLEDGE,
    AppActionIds.KNOWLEDGE_GENERATE: AppNodeIds.KNOWLEDGE,
    AppActionIds.MEMORY_OPEN: AppNodeIds.MEMORY,
    AppActionIds.MEMORY_SAVE: AppNodeIds.MEMORY,
    AppActionIds.LEARNING_OPEN: AppNodeIds.LEARNING,
    AppActionIds.LEARNING_POLICY_CANDIDATE_OPEN: AppNodeIds.LEARNING_POLICY_CANDIDATE,
    AppActionIds.LEARNING_EXECUTION_TRACE_OPEN: AppNodeIds.LEARNING_EXECUTION_TRACE,
    AppActionIds.LEARNING_ACTIVE_POLICY_OPEN: AppNodeIds.LEARNING_ACTIVE_POLICY,
    AppActionIds.LEARNING_APPROVE: AppNodeIds.LEARNING,
    AppActionIds.LEARNING_REJECT: AppNodeIds.LEARNING,
    AppActionIds.ROUTE_BACK: AppNodeIds.HOME,
    AppActionIds.ROUTE_FORWARD: AppNodeIds.HOME,
    AppActionIds.ROUTE_CANCEL: AppNodeIds.HOME,
    AppActionIds.ROUTE_OPEN_NODE: AppNodeIds.HOME,
    AppActionIds.ROUTE_SWITCH_SURFACE: AppNodeIds.HOME,
    AppActionIds.QA_OPEN: AppNodeIds.QA,
    AppActionIds.QA_RUN: AppNodeIds.QA,
    AppActionIds.RECOVERY_HOME: AppNodeIds.HOME,
}


def _field(**kwargs: Any) -> RouteDeckFieldSpec:
    return RouteDeckFieldSpec(**kwargs)


def _node(
    node_id: str,
    label: str,
    *,
    lane: str = "saas_agent",
    description: str,
    actions: list[str],
    expected_input: str | None = None,
    recovery: str | None = None,
    allowed_surfaces: dict[str, list[str]] | None = None,
    default_surfaces: dict[str, str] | None = None,
    parent: str | None = None,
    node_kind: str = "workflow",
    capability_id: str | None = None,
    show_in_navgraph: bool = True,
    show_in_capability_rail: bool = True,
    cancel_target_node: str | None = None,
    dirty_policy: str = "none",
) -> RouteDeckNodeSpec:
    return RouteDeckNodeSpec(
        id=node_id,
        label=label,
        lane=lane,
        description=description,
        allowed_actions=actions,
        expected_input=expected_input,
        recovery_prompt=recovery,
        parent=parent,
        node_kind=node_kind,
        capability_id=capability_id,
        show_in_navgraph=show_in_navgraph,
        show_in_capability_rail=show_in_capability_rail,
        cancel_target_node=cancel_target_node,
        dirty_policy=dirty_policy,
        allowed_surfaces=allowed_surfaces or {"main": [node_id, "compact"], "active": [node_id]},
        default_surfaces=default_surfaces or {"main": node_id, "active": node_id},
    )


def _action(
    action_id: str,
    label: str,
    *,
    description: str | None = None,
    kind: str = "button",
    category: str = "navigation",
    emphasis: str = "secondary",
    fields: list[RouteDeckFieldSpec] | None = None,
    invocation_kind: str | None = None,
    allowed_nodes: list[str] | None = None,
    placement: str = "next_best",
) -> RouteDeckActionSpec:
    return RouteDeckActionSpec(
        id=action_id,
        label=label,
        description=description,
        kind=kind,
        category=category,
        emphasis=emphasis,
        fields=fields or [],
        invocation_kind=invocation_kind,
        allowed_nodes=allowed_nodes or [],
        placement=placement,
    )


AGENT_REQUIRED_ACTIONS = [
    AppActionIds.AGENT_HOME,
    AppActionIds.INSTRUCTIONS_OPEN,
    AppActionIds.CONNECTION_CONFIGURE,
    AppActionIds.CATALOG_OPEN,
    AppActionIds.ENTITIES_OPEN,
    AppActionIds.ACTIONS_OPEN,
    AppActionIds.EXECUTION_OPEN,
    AppActionIds.KNOWLEDGE_OPEN,
    AppActionIds.MEMORY_OPEN,
    AppActionIds.LEARNING_OPEN,
    AppActionIds.QA_OPEN,
]
ALL_NAV_ACTIONS = [AppActionIds.HOME, *AGENT_REQUIRED_ACTIONS]
ROUTE_ACTIONS = [AppActionIds.ROUTE_BACK, AppActionIds.ROUTE_FORWARD, AppActionIds.ROUTE_CANCEL]

NODE_SPECS = [
    _node(AppNodeIds.HOME, "Home", lane="system", description="Root application node. Lists eligible SaaS Agents and creates the next graph-owned action.", actions=[AppActionIds.AUTH_SIGN_IN, AppActionIds.AUTH_REGISTER, AppActionIds.SAAS_AGENT_LIST, AppActionIds.SAAS_AGENT_CREATE], recovery="Sign in, create an account, list SaaS Agents, or create a SaaS Agent.", allowed_surfaces={"main": ["lounge", "dashboard", "compact"], "active": ["home"]}, default_surfaces={"main": "dashboard", "active": "home"}),
    _node(AppNodeIds.AUTH_SIGN_IN, "Sign In", lane="auth", description="Authentication surface for existing users.", actions=[AppActionIds.HOME], recovery="Use the sign-in form or return home."),
    _node(AppNodeIds.AUTH_REGISTER, "Register", lane="auth", description="Authentication surface for account creation.", actions=[AppActionIds.HOME], recovery="Use the registration form or return home."),
    _node(AppNodeIds.SAAS_AGENT_SELECT, "SaaS Agent Select", description="Select an eligible SaaS Agent.", actions=[AppActionIds.HOME, AppActionIds.SAAS_AGENT_OPEN, AppActionIds.SAAS_AGENT_CREATE]),
    _node(AppNodeIds.SAAS_AGENT_CREATE, "Create SaaS Agent", description="Create a SaaS Agent from name and slug only.", actions=[AppActionIds.HOME, AppActionIds.SAAS_AGENT_CREATE]),
    _node(AppNodeIds.AGENT_HOME, "SaaS Agent Home", description="Current SaaS Agent overview and graph route map.", actions=ALL_NAV_ACTIONS),
    _node(AppNodeIds.INSTRUCTIONS, "Instructions", description="Manage this SaaS Agent's system prompt and operating instructions.", actions=[*ALL_NAV_ACTIONS, AppActionIds.INSTRUCTIONS_SAVE], dirty_policy="confirm"),
    _node(AppNodeIds.CONNECTION_CONFIGURE, "Connection Configure", description="Configure an API connection from graph-provided fields.", actions=[*ALL_NAV_ACTIONS, AppActionIds.CONNECTION_PREVIEW, AppActionIds.CONNECTION_ACTIVATE]),
    _node(AppNodeIds.SCHEMA_PREVIEW, "Schema Preview", description="Preview OpenAPI schema metadata before activation.", actions=[*ALL_NAV_ACTIONS, AppActionIds.CONNECTION_ACTIVATE]),
    _node(AppNodeIds.CATALOG_ACTIVATION, "Catalog Activation", description="Run catalog, tool, RAG activation through graph handlers.", actions=ALL_NAV_ACTIONS),
    _node(AppNodeIds.CATALOG, "Catalog", description="Inspect generated catalog totals and readiness.", actions=ALL_NAV_ACTIONS),
    _node(AppNodeIds.ENTITIES, "Entities", description="Inspect graph-authored entity surface.", actions=ALL_NAV_ACTIONS),
    _node(AppNodeIds.ACTIONS, "Actions", description="Inspect generated action/tool surface.", actions=ALL_NAV_ACTIONS),
    _node(AppNodeIds.EXECUTION_PLANNING, "Execution Planning", description="Plan a typed API execution candidate.", actions=[*ALL_NAV_ACTIONS, AppActionIds.EXECUTION_PLAN], expected_input="An execution goal may be submitted through the graph turn endpoint."),
    _node(AppNodeIds.NEEDS_INPUT, "Needs Input", description="Collect missing inputs for a planned trace.", actions=[*ALL_NAV_ACTIONS, AppActionIds.EXECUTION_INPUT]),
    _node(AppNodeIds.APPROVAL_REQUIRED, "Approval Required", description="Approve or reject a pending risky execution trace.", actions=[*ALL_NAV_ACTIONS, AppActionIds.APPROVAL_APPROVE, AppActionIds.APPROVAL_REJECT]),
    _node(AppNodeIds.EXECUTING, "Executing", description="Graph-owned transient execution node.", actions=ALL_NAV_ACTIONS),
    _node(AppNodeIds.RESULT_REVIEW, "Result Review", description="Review execution result evidence.", actions=[*ALL_NAV_ACTIONS, AppActionIds.RESULT_REVIEW, AppActionIds.EXECUTION_PLAN]),
    _node(AppNodeIds.KNOWLEDGE, "Knowledge", description="Graph surface for attachments and generated catalog RAG.", actions=[*ALL_NAV_ACTIONS, AppActionIds.KNOWLEDGE_GENERATE]),
    _node(AppNodeIds.MEMORY, "Memory", description="Graph surface for persistent agent memory.", actions=[*ALL_NAV_ACTIONS, AppActionIds.MEMORY_SAVE]),
    _node(
        AppNodeIds.LEARNING,
        "Learning",
        description="Graph surface for sandbox learning proposals.",
        actions=[
            *ALL_NAV_ACTIONS,
            *ROUTE_ACTIONS,
            AppActionIds.ROUTE_SWITCH_SURFACE,
            AppActionIds.LEARNING_POLICY_CANDIDATE_OPEN,
            AppActionIds.LEARNING_EXECUTION_TRACE_OPEN,
            AppActionIds.LEARNING_ACTIVE_POLICY_OPEN,
        ],
        node_kind="section",
        capability_id="learning",
        allowed_surfaces={"main": ["learning", "compact"], "active": ["policy_gaps", "failed_executions", "active_policies", "rejected"]},
        default_surfaces={"main": "learning", "active": "policy_gaps"},
    ),
    _node(
        AppNodeIds.LEARNING_POLICY_CANDIDATE,
        "Policy Candidate",
        description="Review one sandbox learning policy candidate.",
        actions=[*ALL_NAV_ACTIONS, *ROUTE_ACTIONS, AppActionIds.LEARNING_APPROVE, AppActionIds.LEARNING_REJECT],
        parent=AppNodeIds.LEARNING,
        node_kind="detail",
        capability_id="learning",
        show_in_capability_rail=False,
        cancel_target_node=AppNodeIds.LEARNING,
        allowed_surfaces={"main": ["learning.policy_candidate", "compact"], "active": ["policy_candidate_review"]},
        default_surfaces={"main": "learning.policy_candidate", "active": "policy_candidate_review"},
    ),
    _node(
        AppNodeIds.LEARNING_EXECUTION_TRACE,
        "Execution Trace",
        description="Review one execution trace produced by public chat or owner execution.",
        actions=[*ALL_NAV_ACTIONS, *ROUTE_ACTIONS],
        parent=AppNodeIds.LEARNING,
        node_kind="detail",
        capability_id="learning",
        show_in_capability_rail=False,
        cancel_target_node=AppNodeIds.LEARNING,
        allowed_surfaces={"main": ["learning.execution_trace", "compact"], "active": ["execution_trace_review"]},
        default_surfaces={"main": "learning.execution_trace", "active": "execution_trace_review"},
    ),
    _node(
        AppNodeIds.LEARNING_ACTIVE_POLICY,
        "Active Policy",
        description="Review one approved learning policy.",
        actions=[*ALL_NAV_ACTIONS, *ROUTE_ACTIONS],
        parent=AppNodeIds.LEARNING,
        node_kind="detail",
        capability_id="learning",
        show_in_capability_rail=False,
        cancel_target_node=AppNodeIds.LEARNING,
        allowed_surfaces={"main": ["learning.active_policy", "compact"], "active": ["active_policy_review"]},
        default_surfaces={"main": "learning.active_policy", "active": "active_policy_review"},
    ),
    _node(AppNodeIds.QA, "QA", description="Graph-authored QA scenario surface.", actions=[*ALL_NAV_ACTIONS, AppActionIds.QA_RUN]),
    _node(AppNodeIds.RECOVERY, "Recovery", lane="system", description="Recovery node for invalid or ineligible graph requests.", actions=[AppActionIds.RECOVERY_HOME], recovery="Return home or choose an available next step."),
]

ACTION_SPECS = [
    _action(AppActionIds.HOME, "Home", allowed_nodes=["*"]),
    _action(AppActionIds.AUTH_SIGN_IN, "Sign in", category="auth", emphasis="primary", allowed_nodes=[AppNodeIds.HOME]),
    _action(AppActionIds.AUTH_REGISTER, "Create account", category="auth", allowed_nodes=[AppNodeIds.HOME]),
    _action(AppActionIds.SAAS_AGENT_LIST, "List agents", category="setup", invocation_kind="surface", allowed_nodes=[AppNodeIds.HOME, AppNodeIds.SAAS_AGENT_SELECT]),
    _action(AppActionIds.SAAS_AGENT_OPEN, "Open SaaS Agent", category="setup", invocation_kind="entity_selector", fields=[_field(key="saas_agent_id", label="SaaS Agent ID", required=True)], allowed_nodes=[AppNodeIds.SAAS_AGENT_SELECT]),
    _action(AppActionIds.SAAS_AGENT_CREATE, "Create SaaS Agent", category="setup", kind="form", emphasis="primary", fields=[_field(key="name", label="Name", required=True, placeholder="Customer Support Agent"), _field(key="slug", label="Slug", required=True, placeholder="customer-support-agent")], allowed_nodes=[AppNodeIds.HOME, AppNodeIds.SAAS_AGENT_SELECT, AppNodeIds.SAAS_AGENT_CREATE]),
    _action(AppActionIds.AGENT_HOME, "Agent home", allowed_nodes=["*"]),
    _action(AppActionIds.INSTRUCTIONS_OPEN, "Instructions", category="setup", allowed_nodes=["*"]),
    _action(AppActionIds.INSTRUCTIONS_SAVE, "Save instructions", category="setup", kind="form", emphasis="primary", fields=[_field(key="system_prompt", label="System prompt", field_type="textarea"), _field(key="instructions", label="Operating instructions", field_type="textarea")], allowed_nodes=[AppNodeIds.INSTRUCTIONS]),
    _action(AppActionIds.CONNECTION_CONFIGURE, "Configure connection", category="setup", allowed_nodes=["*"]),
    _action(AppActionIds.CONNECTION_PREVIEW, "Preview schema", category="setup", kind="form", fields=[_field(key="spec_url", label="OpenAPI URL", field_type="url", placeholder="https://api.example.com/openapi.json"), _field(key="raw_spec", label="Paste OpenAPI schema", field_type="textarea", placeholder="Paste OpenAPI JSON or YAML when the schema is not publicly hosted.")], allowed_nodes=[AppNodeIds.CONNECTION_CONFIGURE]),
    _action(AppActionIds.CONNECTION_ACTIVATE, "Save and activate API", category="setup", kind="form", emphasis="primary", fields=[_field(key="name", label="Connection name", required=True, placeholder="Production API"), _field(key="base_url", label="Base URL", field_type="url", required=True, placeholder="https://api.example.com"), _field(key="spec_url", label="OpenAPI URL", field_type="url", placeholder="https://api.example.com/openapi.json"), _field(key="raw_spec", label="Paste OpenAPI schema", field_type="textarea", placeholder="Paste OpenAPI JSON or YAML when the schema is not publicly hosted."), _field(key="auth_type", label="Auth type", field_type="select", required=True, default="none", options=[{"value": "none", "label": "No auth"}, {"value": "bearer", "label": "Bearer token"}, {"value": "api_key_header", "label": "API key header"}, {"value": "api_key_query", "label": "API key query param"}, {"value": "basic", "label": "Basic auth"}, {"value": "custom_header", "label": "Custom header"}]), _field(key="credential_value", label="Credential", field_type="password", sensitive=True), _field(key="header_name", label="Header name", placeholder="X-API-Key"), _field(key="query_param_name", label="Query param name", placeholder="api_key")], allowed_nodes=[AppNodeIds.CONNECTION_CONFIGURE, AppNodeIds.SCHEMA_PREVIEW]),
    _action(AppActionIds.CATALOG_OPEN, "Catalog", category="setup", allowed_nodes=["*"]),
    _action(AppActionIds.ENTITIES_OPEN, "Entities", category="setup", allowed_nodes=["*"]),
    _action(AppActionIds.ACTIONS_OPEN, "Actions", category="setup", allowed_nodes=["*"]),
    _action(AppActionIds.EXECUTION_OPEN, "Execution", category="execution", allowed_nodes=["*"]),
    _action(AppActionIds.EXECUTION_PLAN, "Plan execution", category="execution", kind="form", emphasis="primary", fields=[_field(key="goal", label="Goal", required=True, placeholder="List products")], allowed_nodes=[AppNodeIds.EXECUTION_PLANNING, AppNodeIds.RESULT_REVIEW]),
    _action(AppActionIds.EXECUTION_INPUT, "Provide input", category="execution", kind="form", fields=[_field(key="inputs_json", label="Inputs JSON", required=True, placeholder='{"id":"..."}')], allowed_nodes=[AppNodeIds.NEEDS_INPUT]),
    _action(AppActionIds.APPROVAL_APPROVE, "Approve execution", category="execution", emphasis="primary", fields=[_field(key="trace_id", label="Trace ID", required=True)], allowed_nodes=[AppNodeIds.APPROVAL_REQUIRED]),
    _action(AppActionIds.APPROVAL_REJECT, "Reject execution", category="execution", fields=[_field(key="trace_id", label="Trace ID", required=True)], allowed_nodes=[AppNodeIds.APPROVAL_REQUIRED]),
    _action(AppActionIds.RESULT_REVIEW, "Review result", category="execution", allowed_nodes=["*"]),
    _action(AppActionIds.KNOWLEDGE_OPEN, "Knowledge", category="learning", allowed_nodes=["*"]),
    _action(AppActionIds.KNOWLEDGE_GENERATE, "Generate catalog RAG", category="learning", allowed_nodes=[AppNodeIds.KNOWLEDGE]),
    _action(AppActionIds.MEMORY_OPEN, "Memory", category="learning", allowed_nodes=["*"]),
    _action(AppActionIds.MEMORY_SAVE, "Save memory", category="learning", kind="form", fields=[_field(key="content", label="Memory", required=True), _field(key="category", label="Category", field_type="select", default="fact", options=[{"value": "fact", "label": "Fact"}, {"value": "preference", "label": "Preference"}, {"value": "instruction", "label": "Instruction"}])], allowed_nodes=[AppNodeIds.MEMORY]),
    _action(AppActionIds.LEARNING_OPEN, "Learning", category="learning", allowed_nodes=["*"]),
    _action(AppActionIds.LEARNING_POLICY_CANDIDATE_OPEN, "Review policy candidate", category="learning", fields=[_field(key="candidate_id", label="Candidate ID", required=True)], invocation_kind="entity_selector", allowed_nodes=[AppNodeIds.LEARNING]),
    _action(AppActionIds.LEARNING_EXECUTION_TRACE_OPEN, "Review execution trace", category="learning", fields=[_field(key="trace_id", label="Trace ID", required=True)], invocation_kind="entity_selector", allowed_nodes=[AppNodeIds.LEARNING]),
    _action(AppActionIds.LEARNING_ACTIVE_POLICY_OPEN, "Review active policy", category="learning", fields=[_field(key="candidate_id", label="Candidate ID", required=True)], invocation_kind="entity_selector", allowed_nodes=[AppNodeIds.LEARNING]),
    _action(AppActionIds.LEARNING_APPROVE, "Approve learning", category="learning", fields=[_field(key="candidate_id", label="Candidate ID", required=True)], allowed_nodes=[AppNodeIds.LEARNING, AppNodeIds.LEARNING_POLICY_CANDIDATE]),
    _action(AppActionIds.LEARNING_REJECT, "Reject learning", category="learning", fields=[_field(key="candidate_id", label="Candidate ID", required=True)], allowed_nodes=[AppNodeIds.LEARNING, AppNodeIds.LEARNING_POLICY_CANDIDATE]),
    _action(AppActionIds.ROUTE_BACK, "Back", category="navigation", invocation_kind="hidden", allowed_nodes=["*"]),
    _action(AppActionIds.ROUTE_FORWARD, "Forward", category="navigation", invocation_kind="hidden", allowed_nodes=["*"]),
    _action(AppActionIds.ROUTE_CANCEL, "Cancel", category="navigation", invocation_kind="hidden", allowed_nodes=["*"]),
    _action(AppActionIds.ROUTE_OPEN_NODE, "Open node", category="navigation", invocation_kind="hidden", allowed_nodes=["*"]),
    _action(AppActionIds.ROUTE_SWITCH_SURFACE, "Switch surface", category="navigation", invocation_kind="hidden", allowed_nodes=["*"]),
    _action(AppActionIds.QA_OPEN, "QA", category="feedback", allowed_nodes=["*"]),
    _action(AppActionIds.QA_RUN, "Run QA scenario", category="feedback", allowed_nodes=[AppNodeIds.QA]),
    _action(AppActionIds.RECOVERY_HOME, "Return home", category="navigation", allowed_nodes=[AppNodeIds.RECOVERY]),
]


def _edge(from_node: str, to_node: str, action_id: str | None = None, edge_type: str | None = None) -> RouteDeckEdgeSpec:
    return RouteDeckEdgeSpec(from_stage=from_node, to_stage=to_node, edge_type=edge_type or ("action" if action_id else "runtime"), action_id=action_id)


def _build_edges() -> list[RouteDeckEdgeSpec]:
    return [
        _edge(AppNodeIds.HOME, AppNodeIds.AUTH_SIGN_IN, AppActionIds.AUTH_SIGN_IN),
        _edge(AppNodeIds.HOME, AppNodeIds.AUTH_REGISTER, AppActionIds.AUTH_REGISTER),
        _edge(AppNodeIds.AUTH_SIGN_IN, AppNodeIds.HOME, AppActionIds.HOME),
        _edge(AppNodeIds.AUTH_REGISTER, AppNodeIds.HOME, AppActionIds.HOME),
        _edge(AppNodeIds.HOME, AppNodeIds.SAAS_AGENT_SELECT, AppActionIds.SAAS_AGENT_LIST),
        _edge(AppNodeIds.HOME, AppNodeIds.SAAS_AGENT_CREATE, AppActionIds.SAAS_AGENT_CREATE),
        _edge(AppNodeIds.SAAS_AGENT_SELECT, AppNodeIds.AGENT_HOME, AppActionIds.SAAS_AGENT_OPEN),
        _edge(AppNodeIds.SAAS_AGENT_SELECT, AppNodeIds.SAAS_AGENT_CREATE, AppActionIds.SAAS_AGENT_CREATE),
        _edge(AppNodeIds.SAAS_AGENT_CREATE, AppNodeIds.AGENT_HOME, AppActionIds.SAAS_AGENT_CREATE),
        _edge(AppNodeIds.AGENT_HOME, AppNodeIds.INSTRUCTIONS, AppActionIds.INSTRUCTIONS_OPEN),
        _edge(AppNodeIds.AGENT_HOME, AppNodeIds.CONNECTION_CONFIGURE, AppActionIds.CONNECTION_CONFIGURE),
        _edge(AppNodeIds.INSTRUCTIONS, AppNodeIds.CONNECTION_CONFIGURE, AppActionIds.CONNECTION_CONFIGURE),
        _edge(AppNodeIds.CONNECTION_CONFIGURE, AppNodeIds.SCHEMA_PREVIEW, AppActionIds.CONNECTION_PREVIEW),
        _edge(AppNodeIds.SCHEMA_PREVIEW, AppNodeIds.CATALOG_ACTIVATION, AppActionIds.CONNECTION_ACTIVATE),
        _edge(AppNodeIds.CATALOG_ACTIVATION, AppNodeIds.CATALOG),
        _edge(AppNodeIds.CATALOG, AppNodeIds.ENTITIES, AppActionIds.ENTITIES_OPEN),
        _edge(AppNodeIds.CATALOG, AppNodeIds.ACTIONS, AppActionIds.ACTIONS_OPEN),
        _edge(AppNodeIds.ACTIONS, AppNodeIds.EXECUTION_PLANNING, AppActionIds.EXECUTION_OPEN),
        _edge(AppNodeIds.EXECUTION_PLANNING, AppNodeIds.NEEDS_INPUT, AppActionIds.EXECUTION_PLAN),
        _edge(AppNodeIds.NEEDS_INPUT, AppNodeIds.EXECUTION_PLANNING, AppActionIds.EXECUTION_INPUT),
        _edge(AppNodeIds.EXECUTION_PLANNING, AppNodeIds.APPROVAL_REQUIRED, AppActionIds.EXECUTION_PLAN),
        _edge(AppNodeIds.EXECUTION_PLANNING, AppNodeIds.EXECUTING, AppActionIds.EXECUTION_PLAN),
        _edge(AppNodeIds.APPROVAL_REQUIRED, AppNodeIds.EXECUTING, AppActionIds.APPROVAL_APPROVE),
        _edge(AppNodeIds.APPROVAL_REQUIRED, AppNodeIds.RESULT_REVIEW, AppActionIds.APPROVAL_REJECT),
        _edge(AppNodeIds.EXECUTING, AppNodeIds.RESULT_REVIEW),
        _edge(AppNodeIds.RESULT_REVIEW, AppNodeIds.EXECUTION_PLANNING, AppActionIds.EXECUTION_PLAN),
        _edge(AppNodeIds.AGENT_HOME, AppNodeIds.KNOWLEDGE, AppActionIds.KNOWLEDGE_OPEN),
        _edge(AppNodeIds.KNOWLEDGE, AppNodeIds.MEMORY, AppActionIds.MEMORY_OPEN),
        _edge(AppNodeIds.KNOWLEDGE, AppNodeIds.LEARNING, AppActionIds.LEARNING_OPEN),
        _edge(AppNodeIds.LEARNING, AppNodeIds.LEARNING_POLICY_CANDIDATE, AppActionIds.LEARNING_POLICY_CANDIDATE_OPEN),
        _edge(AppNodeIds.LEARNING, AppNodeIds.LEARNING_EXECUTION_TRACE, AppActionIds.LEARNING_EXECUTION_TRACE_OPEN),
        _edge(AppNodeIds.LEARNING, AppNodeIds.LEARNING_ACTIVE_POLICY, AppActionIds.LEARNING_ACTIVE_POLICY_OPEN),
        _edge(AppNodeIds.LEARNING, AppNodeIds.LEARNING_POLICY_CANDIDATE, edge_type="contains"),
        _edge(AppNodeIds.LEARNING, AppNodeIds.LEARNING_EXECUTION_TRACE, edge_type="contains"),
        _edge(AppNodeIds.LEARNING, AppNodeIds.LEARNING_ACTIVE_POLICY, edge_type="contains"),
        _edge(AppNodeIds.AGENT_HOME, AppNodeIds.QA, AppActionIds.QA_OPEN),
        _edge(AppNodeIds.RECOVERY, AppNodeIds.HOME, AppActionIds.RECOVERY_HOME),
    ]


def build_app_graph_manifest() -> RouteDeckManifest:
    return RouteDeckManifest(
        version=APP_GRAPH_VERSION,
        nodes=NODE_SPECS,
        edges=_build_edges(),
        actions=ACTION_SPECS,
        policies={
            "sensitive": RouteDeckSensitivePolicy(masked_payload_keys=["credential_value", "password", "token", "api_key"], chat_secret_fields=["credential_value", "password"], url_or_modal_only_fields=["credential_value"], note="RouteDeck masks connection credentials. Graph text turns must not echo secrets.").model_dump(),
            "navigation": {"source_of_truth": "backend_app_graph", "no_frontend_workflow_authority": True},
        },
        test_paths=[
            {"id": "home_to_agent_connection", "nodes": [AppNodeIds.HOME, AppNodeIds.AGENT_HOME, AppNodeIds.CONNECTION_CONFIGURE]},
            {"id": "connection_to_execution", "nodes": [AppNodeIds.CONNECTION_CONFIGURE, AppNodeIds.SCHEMA_PREVIEW, AppNodeIds.CATALOG, AppNodeIds.EXECUTION_PLANNING]},
            {"id": "approval_path", "nodes": [AppNodeIds.EXECUTION_PLANNING, AppNodeIds.APPROVAL_REQUIRED, AppNodeIds.RESULT_REVIEW]},
        ],
    )


async def _stub_handler(state: dict[str, Any]) -> dict[str, Any]:
    return {"node": state.get("node") or AppNodeIds.HOME}


NODE_HANDLERS = {node.id: _stub_handler for node in NODE_SPECS}


def validate_app_graph_manifest() -> list[str]:
    manifest = build_app_graph_manifest()
    errors = validate_manifest(manifest, masked_payload_keys=["credential_value", "password", "token", "api_key"])
    node_ids = {node.id for node in manifest.nodes}
    handler_ids = set(NODE_HANDLERS)
    for node_id in sorted(node_ids - handler_ids):
        errors.append(f"RouteDeck node has no app graph handler: {node_id}")
    for node_id in sorted(handler_ids - node_ids):
        errors.append(f"App graph handler has no RouteDeck node: {node_id}")
    for action in manifest.actions:
        if not action.allowed_nodes:
            errors.append(f"Action has no scope: {action.id}")
    return errors


def route_action_to_card(action: RouteDeckActionSpec, payload: dict[str, Any] | None = None) -> EntryActionCard:
    return EntryActionCard(
        id=action.id,
        label=action.label,
        capability_id=action.capability_id,
        description=action.description,
        emphasis=action.emphasis,
        kind=action.kind,
        category=action.category,
        placement=action.placement,
        fields=[
            EntryActionField(
                key=field.key,
                label=field.label,
                field_type=field.field_type,
                required=field.required,
                placeholder=field.placeholder,
                default=field.default,
                options=field.options,
                help_text=field.help_text,
                validation_hint=field.validation_hint,
                sensitive=field.sensitive,
            )
            for field in action.fields
        ],
        payload=payload or action.payload,
    )
