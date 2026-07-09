from __future__ import annotations

from typing import Any

from backend.core.schemas import EntryActionCard, EntryActionField
from routedeck_core import (
    RouteDeckActionSpec,
    RouteDeckEdgeSpec,
    RouteDeckFieldSpec,
    RouteDeckManifest,
    RouteDeckManifestBuilder,
    RouteDeckNodeSpec,
    route_deck_action,
    route_deck_edge,
    route_deck_field,
    route_deck_node,
    validate_manifest,
)

CORPUS_GRAPH_VERSION = "corpus_routedeck_v1"


class CorpusNodeIds:
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


class CorpusActionIds:
    HOME = "navigate.home"
    AUTH_SIGN_IN = "auth.sign_in"
    AUTH_REGISTER = "auth.register"
    SAAS_AGENT_LIST = "saas_agent.list"
    SAAS_AGENT_OPEN = "saas_agent.open"
    SAAS_AGENT_CREATE = "saas_agent.create"
    AGENT_HOME = "navigate.agent_home"
    DEPLOYMENT_SAVE = "deployment.save"
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


CORPUS_GRAPH_GROUPS = {
    "home": {CorpusNodeIds.HOME},
    "auth": {CorpusNodeIds.AUTH_SIGN_IN, CorpusNodeIds.AUTH_REGISTER},
    "saas_agent": {CorpusNodeIds.SAAS_AGENT_SELECT, CorpusNodeIds.SAAS_AGENT_CREATE, CorpusNodeIds.AGENT_HOME, CorpusNodeIds.INSTRUCTIONS},
    "connection": {
        CorpusNodeIds.CONNECTION_CONFIGURE,
        CorpusNodeIds.SCHEMA_PREVIEW,
        CorpusNodeIds.CATALOG_ACTIVATION,
        CorpusNodeIds.CATALOG,
        CorpusNodeIds.ENTITIES,
        CorpusNodeIds.ACTIONS,
    },
    "execution": {
        CorpusNodeIds.EXECUTION_PLANNING,
        CorpusNodeIds.NEEDS_INPUT,
        CorpusNodeIds.APPROVAL_REQUIRED,
        CorpusNodeIds.EXECUTING,
        CorpusNodeIds.RESULT_REVIEW,
    },
    "knowledge": {
        CorpusNodeIds.KNOWLEDGE,
        CorpusNodeIds.MEMORY,
        CorpusNodeIds.LEARNING,
        CorpusNodeIds.LEARNING_POLICY_CANDIDATE,
        CorpusNodeIds.LEARNING_EXECUTION_TRACE,
        CorpusNodeIds.LEARNING_ACTIVE_POLICY,
    },
    "qa": {CorpusNodeIds.QA},
    "recovery": {CorpusNodeIds.RECOVERY},
}

CAPABILITY_RAIL_ITEMS = [
    {
        "id": "home",
        "label": "Home",
        "icon_key": "home",
        "nodes": [CorpusNodeIds.HOME],
        "operation_id": CorpusActionIds.HOME,
    },
    {
        "id": "agent",
        "label": "Create Agent",
        "icon_key": "sparkles",
        "nodes": [CorpusNodeIds.SAAS_AGENT_SELECT, CorpusNodeIds.SAAS_AGENT_CREATE, CorpusNodeIds.AGENT_HOME, CorpusNodeIds.INSTRUCTIONS],
        "operation_id": CorpusActionIds.SAAS_AGENT_CREATE,
    },
    {
        "id": "connect",
        "label": "Connect API",
        "icon_key": "plug",
        "nodes": [CorpusNodeIds.CONNECTION_CONFIGURE, CorpusNodeIds.SCHEMA_PREVIEW],
        "operation_id": CorpusActionIds.CONNECTION_CONFIGURE,
    },
    {
        "id": "catalog",
        "label": "Catalog",
        "icon_key": "database",
        "nodes": [CorpusNodeIds.CATALOG_ACTIVATION, CorpusNodeIds.CATALOG],
        "operation_id": CorpusActionIds.CATALOG_OPEN,
    },
    {
        "id": "actions",
        "label": "Actions",
        "icon_key": "wrench",
        "nodes": [CorpusNodeIds.ENTITIES, CorpusNodeIds.ACTIONS],
        "operation_id": CorpusActionIds.ACTIONS_OPEN,
    },
    {
        "id": "execution",
        "label": "Execution",
        "icon_key": "play",
        "nodes": [
            CorpusNodeIds.EXECUTION_PLANNING,
            CorpusNodeIds.NEEDS_INPUT,
            CorpusNodeIds.APPROVAL_REQUIRED,
            CorpusNodeIds.EXECUTING,
            CorpusNodeIds.RESULT_REVIEW,
        ],
        "operation_id": CorpusActionIds.EXECUTION_OPEN,
    },
    {
        "id": "knowledge",
        "label": "Knowledge",
        "icon_key": "book",
        "nodes": [CorpusNodeIds.KNOWLEDGE],
        "operation_id": CorpusActionIds.KNOWLEDGE_OPEN,
    },
    {
        "id": "memory",
        "label": "Memory",
        "icon_key": "brain",
        "nodes": [CorpusNodeIds.MEMORY],
        "operation_id": CorpusActionIds.MEMORY_OPEN,
    },
    {
        "id": "learning",
        "label": "Learning",
        "icon_key": "graduation",
        "nodes": [CorpusNodeIds.LEARNING],
        "child_nodes": [
            CorpusNodeIds.LEARNING_POLICY_CANDIDATE,
            CorpusNodeIds.LEARNING_EXECUTION_TRACE,
            CorpusNodeIds.LEARNING_ACTIVE_POLICY,
        ],
        "operation_id": CorpusActionIds.LEARNING_OPEN,
    },
    {
        "id": "qa",
        "label": "QA",
        "icon_key": "clipboard",
        "nodes": [CorpusNodeIds.QA],
        "operation_id": CorpusActionIds.QA_OPEN,
    },
]

ACTION_TARGETS = {
    CorpusActionIds.HOME: CorpusNodeIds.HOME,
    CorpusActionIds.AUTH_SIGN_IN: CorpusNodeIds.AUTH_SIGN_IN,
    CorpusActionIds.AUTH_REGISTER: CorpusNodeIds.AUTH_REGISTER,
    CorpusActionIds.SAAS_AGENT_LIST: CorpusNodeIds.SAAS_AGENT_SELECT,
    CorpusActionIds.SAAS_AGENT_OPEN: CorpusNodeIds.AGENT_HOME,
    CorpusActionIds.SAAS_AGENT_CREATE: CorpusNodeIds.AGENT_HOME,
    CorpusActionIds.AGENT_HOME: CorpusNodeIds.AGENT_HOME,
    CorpusActionIds.DEPLOYMENT_SAVE: CorpusNodeIds.AGENT_HOME,
    CorpusActionIds.INSTRUCTIONS_OPEN: CorpusNodeIds.INSTRUCTIONS,
    CorpusActionIds.INSTRUCTIONS_SAVE: CorpusNodeIds.INSTRUCTIONS,
    CorpusActionIds.CONNECTION_CONFIGURE: CorpusNodeIds.CONNECTION_CONFIGURE,
    CorpusActionIds.CONNECTION_PREVIEW: CorpusNodeIds.SCHEMA_PREVIEW,
    CorpusActionIds.CONNECTION_ACTIVATE: CorpusNodeIds.CATALOG,
    CorpusActionIds.CATALOG_OPEN: CorpusNodeIds.CATALOG,
    CorpusActionIds.ENTITIES_OPEN: CorpusNodeIds.ENTITIES,
    CorpusActionIds.ACTIONS_OPEN: CorpusNodeIds.ACTIONS,
    CorpusActionIds.EXECUTION_OPEN: CorpusNodeIds.EXECUTION_PLANNING,
    CorpusActionIds.EXECUTION_PLAN: CorpusNodeIds.EXECUTION_PLANNING,
    CorpusActionIds.EXECUTION_INPUT: CorpusNodeIds.EXECUTION_PLANNING,
    CorpusActionIds.APPROVAL_APPROVE: CorpusNodeIds.RESULT_REVIEW,
    CorpusActionIds.APPROVAL_REJECT: CorpusNodeIds.RESULT_REVIEW,
    CorpusActionIds.RESULT_REVIEW: CorpusNodeIds.RESULT_REVIEW,
    CorpusActionIds.KNOWLEDGE_OPEN: CorpusNodeIds.KNOWLEDGE,
    CorpusActionIds.KNOWLEDGE_GENERATE: CorpusNodeIds.KNOWLEDGE,
    CorpusActionIds.MEMORY_OPEN: CorpusNodeIds.MEMORY,
    CorpusActionIds.MEMORY_SAVE: CorpusNodeIds.MEMORY,
    CorpusActionIds.LEARNING_OPEN: CorpusNodeIds.LEARNING,
    CorpusActionIds.LEARNING_POLICY_CANDIDATE_OPEN: CorpusNodeIds.LEARNING_POLICY_CANDIDATE,
    CorpusActionIds.LEARNING_EXECUTION_TRACE_OPEN: CorpusNodeIds.LEARNING_EXECUTION_TRACE,
    CorpusActionIds.LEARNING_ACTIVE_POLICY_OPEN: CorpusNodeIds.LEARNING_ACTIVE_POLICY,
    CorpusActionIds.LEARNING_APPROVE: CorpusNodeIds.LEARNING,
    CorpusActionIds.LEARNING_REJECT: CorpusNodeIds.LEARNING,
    CorpusActionIds.ROUTE_BACK: CorpusNodeIds.HOME,
    CorpusActionIds.ROUTE_FORWARD: CorpusNodeIds.HOME,
    CorpusActionIds.ROUTE_CANCEL: CorpusNodeIds.HOME,
    CorpusActionIds.ROUTE_OPEN_NODE: CorpusNodeIds.HOME,
    CorpusActionIds.ROUTE_SWITCH_SURFACE: CorpusNodeIds.HOME,
    CorpusActionIds.QA_OPEN: CorpusNodeIds.QA,
    CorpusActionIds.QA_RUN: CorpusNodeIds.QA,
    CorpusActionIds.RECOVERY_HOME: CorpusNodeIds.HOME,
}


def _field(**kwargs: Any) -> RouteDeckFieldSpec:
    return route_deck_field(**kwargs)


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
    return route_deck_node(
        node_id,
        label,
        lane=lane,
        description=description,
        actions=actions,
        expected_input=expected_input,
        recovery=recovery,
        allowed_surfaces=allowed_surfaces or {"main": [node_id, "compact"], "active": [node_id]},
        default_surfaces=default_surfaces or {"main": node_id, "active": node_id},
        parent=parent,
        node_kind=node_kind,
        capability_id=capability_id,
        show_in_navgraph=show_in_navgraph,
        show_in_capability_rail=show_in_capability_rail,
        cancel_target_node=cancel_target_node,
        dirty_policy=dirty_policy,
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
    return route_deck_action(
        action_id,
        label,
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
    CorpusActionIds.AGENT_HOME,
    CorpusActionIds.DEPLOYMENT_SAVE,
    CorpusActionIds.INSTRUCTIONS_OPEN,
    CorpusActionIds.CONNECTION_CONFIGURE,
    CorpusActionIds.CATALOG_OPEN,
    CorpusActionIds.ENTITIES_OPEN,
    CorpusActionIds.ACTIONS_OPEN,
    CorpusActionIds.EXECUTION_OPEN,
    CorpusActionIds.KNOWLEDGE_OPEN,
    CorpusActionIds.MEMORY_OPEN,
    CorpusActionIds.LEARNING_OPEN,
    CorpusActionIds.QA_OPEN,
]
ALL_NAV_ACTIONS = [CorpusActionIds.HOME, *AGENT_REQUIRED_ACTIONS]
ROUTE_ACTIONS = [CorpusActionIds.ROUTE_BACK, CorpusActionIds.ROUTE_FORWARD, CorpusActionIds.ROUTE_CANCEL]

NODE_SPECS = [
    _node(CorpusNodeIds.HOME, "Home", lane="system", description="Root application node. Lists eligible SaaS Agents and creates the next graph-owned action.", actions=[CorpusActionIds.AUTH_SIGN_IN, CorpusActionIds.AUTH_REGISTER, CorpusActionIds.SAAS_AGENT_LIST, CorpusActionIds.SAAS_AGENT_CREATE], recovery="Sign in, create an account, list SaaS Agents, or create a SaaS Agent.", allowed_surfaces={"main": ["lounge", "dashboard", "compact"], "active": ["home"]}, default_surfaces={"main": "dashboard", "active": "home"}),
    _node(CorpusNodeIds.AUTH_SIGN_IN, "Sign In", lane="auth", description="Authentication surface for existing users.", actions=[CorpusActionIds.HOME], recovery="Use the sign-in form or return home."),
    _node(CorpusNodeIds.AUTH_REGISTER, "Register", lane="auth", description="Authentication surface for account creation.", actions=[CorpusActionIds.HOME], recovery="Use the registration form or return home."),
    _node(CorpusNodeIds.SAAS_AGENT_SELECT, "SaaS Agent Select", description="Select an eligible SaaS Agent.", actions=[CorpusActionIds.HOME, CorpusActionIds.SAAS_AGENT_OPEN, CorpusActionIds.SAAS_AGENT_CREATE]),
    _node(CorpusNodeIds.SAAS_AGENT_CREATE, "Create SaaS Agent", description="Create a SaaS Agent from name and slug only.", actions=[CorpusActionIds.HOME, CorpusActionIds.SAAS_AGENT_CREATE]),
    _node(CorpusNodeIds.AGENT_HOME, "SaaS Agent Home", description="Current SaaS Agent overview and graph route map.", actions=ALL_NAV_ACTIONS),
    _node(CorpusNodeIds.INSTRUCTIONS, "Instructions", description="Manage this SaaS Agent's system prompt and operating instructions.", actions=[*ALL_NAV_ACTIONS, CorpusActionIds.INSTRUCTIONS_SAVE], dirty_policy="confirm"),
    _node(CorpusNodeIds.CONNECTION_CONFIGURE, "Connection Configure", description="Configure an API connection from graph-provided fields.", actions=[*ALL_NAV_ACTIONS, CorpusActionIds.CONNECTION_PREVIEW, CorpusActionIds.CONNECTION_ACTIVATE]),
    _node(CorpusNodeIds.SCHEMA_PREVIEW, "Schema Preview", description="Preview OpenAPI schema metadata before activation.", actions=[*ALL_NAV_ACTIONS, CorpusActionIds.CONNECTION_ACTIVATE]),
    _node(CorpusNodeIds.CATALOG_ACTIVATION, "Catalog Activation", description="Run catalog, tool, RAG activation through graph handlers.", actions=ALL_NAV_ACTIONS),
    _node(CorpusNodeIds.CATALOG, "Catalog", description="Inspect generated catalog totals and readiness.", actions=ALL_NAV_ACTIONS),
    _node(CorpusNodeIds.ENTITIES, "Entities", description="Inspect graph-authored entity surface.", actions=ALL_NAV_ACTIONS),
    _node(CorpusNodeIds.ACTIONS, "Actions", description="Inspect generated action/tool surface.", actions=ALL_NAV_ACTIONS),
    _node(CorpusNodeIds.EXECUTION_PLANNING, "Execution Planning", description="Plan a typed API execution candidate.", actions=[*ALL_NAV_ACTIONS, CorpusActionIds.EXECUTION_PLAN], expected_input="An execution goal may be submitted through the graph turn endpoint."),
    _node(CorpusNodeIds.NEEDS_INPUT, "Needs Input", description="Collect missing inputs for a planned trace.", actions=[*ALL_NAV_ACTIONS, CorpusActionIds.EXECUTION_INPUT]),
    _node(CorpusNodeIds.APPROVAL_REQUIRED, "Approval Required", description="Approve or reject a pending risky execution trace.", actions=[*ALL_NAV_ACTIONS, CorpusActionIds.APPROVAL_APPROVE, CorpusActionIds.APPROVAL_REJECT]),
    _node(CorpusNodeIds.EXECUTING, "Executing", description="Graph-owned transient execution node.", actions=ALL_NAV_ACTIONS),
    _node(CorpusNodeIds.RESULT_REVIEW, "Result Review", description="Review execution result evidence.", actions=[*ALL_NAV_ACTIONS, CorpusActionIds.RESULT_REVIEW, CorpusActionIds.EXECUTION_PLAN]),
    _node(CorpusNodeIds.KNOWLEDGE, "Knowledge", description="Graph surface for attachments and generated catalog RAG.", actions=[*ALL_NAV_ACTIONS, CorpusActionIds.KNOWLEDGE_GENERATE]),
    _node(CorpusNodeIds.MEMORY, "Memory", description="Graph surface for persistent agent memory.", actions=[*ALL_NAV_ACTIONS, CorpusActionIds.MEMORY_SAVE]),
    _node(
        CorpusNodeIds.LEARNING,
        "Learning",
        description="Graph surface for sandbox learning proposals.",
        actions=[
            *ALL_NAV_ACTIONS,
            *ROUTE_ACTIONS,
            CorpusActionIds.ROUTE_SWITCH_SURFACE,
            CorpusActionIds.LEARNING_POLICY_CANDIDATE_OPEN,
            CorpusActionIds.LEARNING_EXECUTION_TRACE_OPEN,
            CorpusActionIds.LEARNING_ACTIVE_POLICY_OPEN,
        ],
        node_kind="section",
        capability_id="learning",
        allowed_surfaces={"main": ["learning", "compact"], "active": ["policy_gaps", "failed_executions", "active_policies", "rejected"]},
        default_surfaces={"main": "learning", "active": "policy_gaps"},
    ),
    _node(
        CorpusNodeIds.LEARNING_POLICY_CANDIDATE,
        "Policy Candidate",
        description="Review one sandbox learning policy candidate.",
        actions=[*ALL_NAV_ACTIONS, *ROUTE_ACTIONS, CorpusActionIds.LEARNING_APPROVE, CorpusActionIds.LEARNING_REJECT],
        parent=CorpusNodeIds.LEARNING,
        node_kind="detail",
        capability_id="learning",
        show_in_capability_rail=False,
        cancel_target_node=CorpusNodeIds.LEARNING,
        allowed_surfaces={"main": ["learning.policy_candidate", "compact"], "active": ["policy_candidate_review"]},
        default_surfaces={"main": "learning.policy_candidate", "active": "policy_candidate_review"},
    ),
    _node(
        CorpusNodeIds.LEARNING_EXECUTION_TRACE,
        "Execution Trace",
        description="Review one execution trace produced by public chat or owner execution.",
        actions=[*ALL_NAV_ACTIONS, *ROUTE_ACTIONS],
        parent=CorpusNodeIds.LEARNING,
        node_kind="detail",
        capability_id="learning",
        show_in_capability_rail=False,
        cancel_target_node=CorpusNodeIds.LEARNING,
        allowed_surfaces={"main": ["learning.execution_trace", "compact"], "active": ["execution_trace_review"]},
        default_surfaces={"main": "learning.execution_trace", "active": "execution_trace_review"},
    ),
    _node(
        CorpusNodeIds.LEARNING_ACTIVE_POLICY,
        "Active Policy",
        description="Review one approved learning policy.",
        actions=[*ALL_NAV_ACTIONS, *ROUTE_ACTIONS],
        parent=CorpusNodeIds.LEARNING,
        node_kind="detail",
        capability_id="learning",
        show_in_capability_rail=False,
        cancel_target_node=CorpusNodeIds.LEARNING,
        allowed_surfaces={"main": ["learning.active_policy", "compact"], "active": ["active_policy_review"]},
        default_surfaces={"main": "learning.active_policy", "active": "active_policy_review"},
    ),
    _node(CorpusNodeIds.QA, "QA", description="Graph-authored QA scenario surface.", actions=[*ALL_NAV_ACTIONS, CorpusActionIds.QA_RUN]),
    _node(CorpusNodeIds.RECOVERY, "Recovery", lane="system", description="Recovery node for invalid or ineligible graph requests.", actions=[CorpusActionIds.RECOVERY_HOME], recovery="Return home or choose an available next step."),
]

ACTION_SPECS = [
    _action(CorpusActionIds.HOME, "Home", allowed_nodes=["*"]),
    _action(CorpusActionIds.AUTH_SIGN_IN, "Sign in", category="auth", emphasis="primary", allowed_nodes=[CorpusNodeIds.HOME]),
    _action(CorpusActionIds.AUTH_REGISTER, "Create account", category="auth", allowed_nodes=[CorpusNodeIds.HOME]),
    _action(CorpusActionIds.SAAS_AGENT_LIST, "List agents", category="setup", invocation_kind="surface", allowed_nodes=[CorpusNodeIds.HOME, CorpusNodeIds.SAAS_AGENT_SELECT]),
    _action(CorpusActionIds.SAAS_AGENT_OPEN, "Open SaaS Agent", category="setup", invocation_kind="entity_selector", fields=[_field(key="saas_agent_id", label="SaaS Agent ID", required=True)], allowed_nodes=[CorpusNodeIds.SAAS_AGENT_SELECT]),
    _action(CorpusActionIds.SAAS_AGENT_CREATE, "Create SaaS Agent", category="setup", kind="form", emphasis="primary", fields=[_field(key="name", label="Name", required=True, placeholder="Customer Support Agent"), _field(key="slug", label="Slug", required=True, placeholder="customer-support-agent")], allowed_nodes=[CorpusNodeIds.HOME, CorpusNodeIds.SAAS_AGENT_SELECT, CorpusNodeIds.SAAS_AGENT_CREATE]),
    _action(CorpusActionIds.AGENT_HOME, "Agent home", allowed_nodes=["*"]),
    _action(
        CorpusActionIds.DEPLOYMENT_SAVE,
        "Save deployment",
        description="Publish or update this SaaS Agent's deployed visitor chat settings, including anonymous access.",
        category="deployment",
        kind="form",
        emphasis="primary",
        fields=[
            _field(key="enabled", label="Enabled", field_type="select", default="true", options=[{"value": "true", "label": "Enabled"}, {"value": "false", "label": "Disabled"}]),
            _field(key="visitor_auth_mode", label="Visitor access", field_type="select", default="anonymous", options=[{"value": "inherit_from_connection", "label": "Inherit from connection"}, {"value": "anonymous", "label": "Anonymous allowed"}, {"value": "login_required", "label": "Login required"}]),
            _field(key="execution_mode", label="Execution mode", field_type="select", default="sandbox", options=[{"value": "sandbox", "label": "Sandbox"}, {"value": "live", "label": "Live"}]),
            _field(key="default_write_policy", label="Default write policy", field_type="select", default="confirm", options=[{"value": "confirm", "label": "Confirm"}, {"value": "owner_approval", "label": "Owner approval"}, {"value": "block", "label": "Block writes"}]),
            _field(key="welcome_message", label="Welcome message", field_type="textarea", default="How can I help?"),
        ],
        allowed_nodes=["*"],
    ),
    _action(CorpusActionIds.INSTRUCTIONS_OPEN, "Instructions", category="setup", allowed_nodes=["*"]),
    _action(CorpusActionIds.INSTRUCTIONS_SAVE, "Save instructions", category="setup", kind="form", emphasis="primary", fields=[_field(key="system_prompt", label="System prompt", field_type="textarea"), _field(key="instructions", label="Operating instructions", field_type="textarea")], allowed_nodes=[CorpusNodeIds.INSTRUCTIONS]),
    _action(CorpusActionIds.CONNECTION_CONFIGURE, "Connect API", description="Open the secure API connection form for base URL, OpenAPI schema, and credentials.", category="setup", allowed_nodes=["*"]),
    _action(CorpusActionIds.CONNECTION_PREVIEW, "Preview schema", category="setup", kind="form", fields=[_field(key="spec_url", label="OpenAPI URL", field_type="url", placeholder="https://api.example.com/openapi.json"), _field(key="raw_spec", label="Paste OpenAPI schema", field_type="textarea", placeholder="Paste OpenAPI JSON or YAML when the schema is not publicly hosted.")], allowed_nodes=[CorpusNodeIds.CONNECTION_CONFIGURE]),
    _action(CorpusActionIds.CONNECTION_ACTIVATE, "Save and activate API", category="setup", kind="form", emphasis="primary", fields=[_field(key="name", label="Connection name", required=True, placeholder="Production API"), _field(key="base_url", label="Base URL", field_type="url", required=True, placeholder="https://api.example.com"), _field(key="spec_url", label="OpenAPI URL", field_type="url", placeholder="https://api.example.com/openapi.json"), _field(key="raw_spec", label="Paste OpenAPI schema", field_type="textarea", placeholder="Paste OpenAPI JSON or YAML when the schema is not publicly hosted."), _field(key="auth_type", label="Auth type", field_type="select", required=True, default="none", options=[{"value": "none", "label": "No auth"}, {"value": "bearer", "label": "Bearer token"}, {"value": "api_key_header", "label": "API key header"}, {"value": "api_key_query", "label": "API key query param"}, {"value": "basic", "label": "Basic auth"}, {"value": "custom_header", "label": "Custom header"}]), _field(key="credential_value", label="Credential", field_type="password", sensitive=True), _field(key="header_name", label="Header name", placeholder="X-API-Key"), _field(key="query_param_name", label="Query param name", placeholder="api_key")], allowed_nodes=[CorpusNodeIds.CONNECTION_CONFIGURE, CorpusNodeIds.SCHEMA_PREVIEW]),
    _action(CorpusActionIds.CATALOG_OPEN, "Catalog", category="setup", allowed_nodes=["*"]),
    _action(CorpusActionIds.ENTITIES_OPEN, "Entities", category="setup", allowed_nodes=["*"]),
    _action(CorpusActionIds.ACTIONS_OPEN, "Actions", category="setup", allowed_nodes=["*"]),
    _action(CorpusActionIds.EXECUTION_OPEN, "Execution", category="execution", allowed_nodes=["*"]),
    _action(CorpusActionIds.EXECUTION_PLAN, "Plan execution", category="execution", kind="form", emphasis="primary", fields=[_field(key="goal", label="Goal", required=True, placeholder="List products")], allowed_nodes=[CorpusNodeIds.EXECUTION_PLANNING, CorpusNodeIds.RESULT_REVIEW]),
    _action(CorpusActionIds.EXECUTION_INPUT, "Provide input", category="execution", kind="form", fields=[_field(key="inputs_json", label="Inputs JSON", required=True, placeholder='{"id":"..."}')], allowed_nodes=[CorpusNodeIds.NEEDS_INPUT]),
    _action(CorpusActionIds.APPROVAL_APPROVE, "Approve execution", category="execution", emphasis="primary", fields=[_field(key="trace_id", label="Trace ID", required=True)], allowed_nodes=[CorpusNodeIds.APPROVAL_REQUIRED]),
    _action(CorpusActionIds.APPROVAL_REJECT, "Reject execution", category="execution", fields=[_field(key="trace_id", label="Trace ID", required=True)], allowed_nodes=[CorpusNodeIds.APPROVAL_REQUIRED]),
    _action(CorpusActionIds.RESULT_REVIEW, "Review result", category="execution", allowed_nodes=["*"]),
    _action(CorpusActionIds.KNOWLEDGE_OPEN, "Knowledge", category="learning", allowed_nodes=["*"]),
    _action(CorpusActionIds.KNOWLEDGE_GENERATE, "Generate catalog RAG", category="learning", allowed_nodes=[CorpusNodeIds.KNOWLEDGE]),
    _action(CorpusActionIds.MEMORY_OPEN, "Memory", category="learning", allowed_nodes=["*"]),
    _action(CorpusActionIds.MEMORY_SAVE, "Save memory", category="learning", kind="form", fields=[_field(key="content", label="Memory", required=True), _field(key="category", label="Category", field_type="select", default="fact", options=[{"value": "fact", "label": "Fact"}, {"value": "preference", "label": "Preference"}, {"value": "instruction", "label": "Instruction"}])], allowed_nodes=[CorpusNodeIds.MEMORY]),
    _action(CorpusActionIds.LEARNING_OPEN, "Learning", description="Open Sandbox Learning for policy gaps, failed executions, active policies, and rejected candidates.", category="learning", allowed_nodes=["*"]),
    _action(CorpusActionIds.LEARNING_POLICY_CANDIDATE_OPEN, "Review policy candidate", category="learning", fields=[_field(key="candidate_id", label="Candidate ID", required=True)], invocation_kind="entity_selector", allowed_nodes=[CorpusNodeIds.LEARNING]),
    _action(CorpusActionIds.LEARNING_EXECUTION_TRACE_OPEN, "Review execution trace", category="learning", fields=[_field(key="trace_id", label="Trace ID", required=True)], invocation_kind="entity_selector", allowed_nodes=[CorpusNodeIds.LEARNING]),
    _action(CorpusActionIds.LEARNING_ACTIVE_POLICY_OPEN, "Review active policy", category="learning", fields=[_field(key="candidate_id", label="Candidate ID", required=True)], invocation_kind="entity_selector", allowed_nodes=[CorpusNodeIds.LEARNING]),
    _action(CorpusActionIds.LEARNING_APPROVE, "Approve learning", category="learning", fields=[_field(key="candidate_id", label="Candidate ID", required=True)], allowed_nodes=[CorpusNodeIds.LEARNING, CorpusNodeIds.LEARNING_POLICY_CANDIDATE]),
    _action(CorpusActionIds.LEARNING_REJECT, "Reject learning", category="learning", fields=[_field(key="candidate_id", label="Candidate ID", required=True)], allowed_nodes=[CorpusNodeIds.LEARNING, CorpusNodeIds.LEARNING_POLICY_CANDIDATE]),
    _action(CorpusActionIds.ROUTE_BACK, "Back", category="navigation", invocation_kind="hidden", allowed_nodes=["*"]),
    _action(CorpusActionIds.ROUTE_FORWARD, "Forward", category="navigation", invocation_kind="hidden", allowed_nodes=["*"]),
    _action(CorpusActionIds.ROUTE_CANCEL, "Cancel", category="navigation", invocation_kind="hidden", allowed_nodes=["*"]),
    _action(CorpusActionIds.ROUTE_OPEN_NODE, "Open node", category="navigation", invocation_kind="hidden", allowed_nodes=["*"]),
    _action(CorpusActionIds.ROUTE_SWITCH_SURFACE, "Switch surface", category="navigation", invocation_kind="hidden", allowed_nodes=["*"]),
    _action(CorpusActionIds.QA_OPEN, "QA", category="feedback", allowed_nodes=["*"]),
    _action(CorpusActionIds.QA_RUN, "Run QA scenario", category="feedback", allowed_nodes=[CorpusNodeIds.QA]),
    _action(CorpusActionIds.RECOVERY_HOME, "Return home", category="navigation", allowed_nodes=[CorpusNodeIds.RECOVERY]),
]


def _edge(from_node: str, to_node: str, action_id: str | None = None, edge_type: str | None = None) -> RouteDeckEdgeSpec:
    return route_deck_edge(from_node, to_node, action_id=action_id, edge_type=edge_type)


def _build_edges() -> list[RouteDeckEdgeSpec]:
    return [
        _edge(CorpusNodeIds.HOME, CorpusNodeIds.AUTH_SIGN_IN, CorpusActionIds.AUTH_SIGN_IN),
        _edge(CorpusNodeIds.HOME, CorpusNodeIds.AUTH_REGISTER, CorpusActionIds.AUTH_REGISTER),
        _edge(CorpusNodeIds.AUTH_SIGN_IN, CorpusNodeIds.HOME, CorpusActionIds.HOME),
        _edge(CorpusNodeIds.AUTH_REGISTER, CorpusNodeIds.HOME, CorpusActionIds.HOME),
        _edge(CorpusNodeIds.HOME, CorpusNodeIds.SAAS_AGENT_SELECT, CorpusActionIds.SAAS_AGENT_LIST),
        _edge(CorpusNodeIds.HOME, CorpusNodeIds.SAAS_AGENT_CREATE, CorpusActionIds.SAAS_AGENT_CREATE),
        _edge(CorpusNodeIds.SAAS_AGENT_SELECT, CorpusNodeIds.AGENT_HOME, CorpusActionIds.SAAS_AGENT_OPEN),
        _edge(CorpusNodeIds.SAAS_AGENT_SELECT, CorpusNodeIds.SAAS_AGENT_CREATE, CorpusActionIds.SAAS_AGENT_CREATE),
        _edge(CorpusNodeIds.SAAS_AGENT_CREATE, CorpusNodeIds.AGENT_HOME, CorpusActionIds.SAAS_AGENT_CREATE),
        _edge(CorpusNodeIds.AGENT_HOME, CorpusNodeIds.INSTRUCTIONS, CorpusActionIds.INSTRUCTIONS_OPEN),
        _edge(CorpusNodeIds.AGENT_HOME, CorpusNodeIds.CONNECTION_CONFIGURE, CorpusActionIds.CONNECTION_CONFIGURE),
        _edge(CorpusNodeIds.INSTRUCTIONS, CorpusNodeIds.CONNECTION_CONFIGURE, CorpusActionIds.CONNECTION_CONFIGURE),
        _edge(CorpusNodeIds.CONNECTION_CONFIGURE, CorpusNodeIds.SCHEMA_PREVIEW, CorpusActionIds.CONNECTION_PREVIEW),
        _edge(CorpusNodeIds.SCHEMA_PREVIEW, CorpusNodeIds.CATALOG_ACTIVATION, CorpusActionIds.CONNECTION_ACTIVATE),
        _edge(CorpusNodeIds.CATALOG_ACTIVATION, CorpusNodeIds.CATALOG),
        _edge(CorpusNodeIds.CATALOG, CorpusNodeIds.ENTITIES, CorpusActionIds.ENTITIES_OPEN),
        _edge(CorpusNodeIds.CATALOG, CorpusNodeIds.ACTIONS, CorpusActionIds.ACTIONS_OPEN),
        _edge(CorpusNodeIds.ACTIONS, CorpusNodeIds.EXECUTION_PLANNING, CorpusActionIds.EXECUTION_OPEN),
        _edge(CorpusNodeIds.EXECUTION_PLANNING, CorpusNodeIds.NEEDS_INPUT, CorpusActionIds.EXECUTION_PLAN),
        _edge(CorpusNodeIds.NEEDS_INPUT, CorpusNodeIds.EXECUTION_PLANNING, CorpusActionIds.EXECUTION_INPUT),
        _edge(CorpusNodeIds.EXECUTION_PLANNING, CorpusNodeIds.APPROVAL_REQUIRED, CorpusActionIds.EXECUTION_PLAN),
        _edge(CorpusNodeIds.EXECUTION_PLANNING, CorpusNodeIds.EXECUTING, CorpusActionIds.EXECUTION_PLAN),
        _edge(CorpusNodeIds.APPROVAL_REQUIRED, CorpusNodeIds.EXECUTING, CorpusActionIds.APPROVAL_APPROVE),
        _edge(CorpusNodeIds.APPROVAL_REQUIRED, CorpusNodeIds.RESULT_REVIEW, CorpusActionIds.APPROVAL_REJECT),
        _edge(CorpusNodeIds.EXECUTING, CorpusNodeIds.RESULT_REVIEW),
        _edge(CorpusNodeIds.RESULT_REVIEW, CorpusNodeIds.EXECUTION_PLANNING, CorpusActionIds.EXECUTION_PLAN),
        _edge(CorpusNodeIds.AGENT_HOME, CorpusNodeIds.KNOWLEDGE, CorpusActionIds.KNOWLEDGE_OPEN),
        _edge(CorpusNodeIds.KNOWLEDGE, CorpusNodeIds.MEMORY, CorpusActionIds.MEMORY_OPEN),
        _edge(CorpusNodeIds.KNOWLEDGE, CorpusNodeIds.LEARNING, CorpusActionIds.LEARNING_OPEN),
        _edge(CorpusNodeIds.LEARNING, CorpusNodeIds.LEARNING_POLICY_CANDIDATE, CorpusActionIds.LEARNING_POLICY_CANDIDATE_OPEN),
        _edge(CorpusNodeIds.LEARNING, CorpusNodeIds.LEARNING_EXECUTION_TRACE, CorpusActionIds.LEARNING_EXECUTION_TRACE_OPEN),
        _edge(CorpusNodeIds.LEARNING, CorpusNodeIds.LEARNING_ACTIVE_POLICY, CorpusActionIds.LEARNING_ACTIVE_POLICY_OPEN),
        _edge(CorpusNodeIds.LEARNING, CorpusNodeIds.LEARNING_POLICY_CANDIDATE, edge_type="contains"),
        _edge(CorpusNodeIds.LEARNING, CorpusNodeIds.LEARNING_EXECUTION_TRACE, edge_type="contains"),
        _edge(CorpusNodeIds.LEARNING, CorpusNodeIds.LEARNING_ACTIVE_POLICY, edge_type="contains"),
        _edge(CorpusNodeIds.AGENT_HOME, CorpusNodeIds.QA, CorpusActionIds.QA_OPEN),
        _edge(CorpusNodeIds.RECOVERY, CorpusNodeIds.HOME, CorpusActionIds.RECOVERY_HOME),
    ]


def build_corpus_manifest() -> RouteDeckManifest:
    return (
        RouteDeckManifestBuilder(CORPUS_GRAPH_VERSION)
        .add_nodes(NODE_SPECS)
        .add_edges(_build_edges())
        .add_actions(ACTION_SPECS)
        .sensitive_policy(
            masked_payload_keys=["credential_value", "password", "token", "api_key"],
            chat_secret_fields=["credential_value", "password"],
            url_or_modal_only_fields=["credential_value"],
            note="RouteDeck masks connection credentials. Graph text turns must not echo secrets.",
        )
        .policy("navigation", {"source_of_truth": "backend_corpus_graph", "no_frontend_workflow_authority": True})
        .test_path("home_to_agent_connection", [CorpusNodeIds.HOME, CorpusNodeIds.AGENT_HOME, CorpusNodeIds.CONNECTION_CONFIGURE])
        .test_path(
            "connection_to_execution",
            [CorpusNodeIds.CONNECTION_CONFIGURE, CorpusNodeIds.SCHEMA_PREVIEW, CorpusNodeIds.CATALOG, CorpusNodeIds.EXECUTION_PLANNING],
        )
        .test_path("approval_path", [CorpusNodeIds.EXECUTION_PLANNING, CorpusNodeIds.APPROVAL_REQUIRED, CorpusNodeIds.RESULT_REVIEW])
        .build()
    )


CORPUS_MANIFEST = build_corpus_manifest()


async def _stub_handler(state: dict[str, Any]) -> dict[str, Any]:
    return {"node": state.get("node") or CorpusNodeIds.HOME}


NODE_HANDLERS = {node.id: _stub_handler for node in NODE_SPECS}


def validate_corpus_manifest() -> list[str]:
    manifest = build_corpus_manifest()
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
