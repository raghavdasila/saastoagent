from __future__ import annotations

from typing import TYPE_CHECKING, Any

from backend.core.schemas import EntryActionCard, EntryActionField
from routedeck_framework.routedeck_core import build_runtime_snapshot as build_core_runtime_snapshot
from routedeck_framework.routedeck_core import reachable_nodes as core_reachable_nodes
from routedeck_framework.routedeck_core import validate_manifest

from .models import (
    RouteDeckActionSpec,
    RouteDeckEdgeSpec,
    RouteDeckFieldSpec,
    RouteDeckManifest,
    RouteDeckNodeSpec,
    RouteDeckSensitivePolicy,
)
from .ids import RouteDeckActionIds, RouteDeckNodeIds

if TYPE_CHECKING:
    from backend.core.models import User

ROUTE_DECK_VERSION = "route_deck_entry_v1"
ANY_ENTRY_NODE = [RouteDeckNodeIds.BOOTSTRAP, RouteDeckNodeIds.INTENT, RouteDeckNodeIds.OPERATOR_READY]
AUTH_NODES = [RouteDeckNodeIds.DISPLAY_NAME, RouteDeckNodeIds.EMAIL, RouteDeckNodeIds.PASSWORD]
MASKED_PAYLOAD_KEYS = ["credential_value", "password", "token", "api_key"]


def _field(**kwargs: Any) -> RouteDeckFieldSpec:
    return RouteDeckFieldSpec(**kwargs)


REST_CONNECTION_FIELDS = [
    _field(
        key="name",
        label="Connection name",
        required=True,
        placeholder="Acme Billing API",
        validation_hint="Short human-readable name for this API connection.",
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
        placeholder="https://api.example.com/openapi.yaml",
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
    _field(key="header_name", label="Header name", placeholder="X-API-Key"),
    _field(key="query_param_name", label="Query param name", placeholder="api_key"),
]


NODE_SPECS: dict[str, RouteDeckNodeSpec] = {
    RouteDeckNodeIds.BOOTSTRAP: RouteDeckNodeSpec(
        id=RouteDeckNodeIds.BOOTSTRAP,
        label="Bootstrap",
        lane="system",
        description="Resolve current auth/session context and choose the first visible entry node.",
        allowed_actions=[
            RouteDeckActionIds.ENTRY_LEARN_PLATFORM,
            RouteDeckActionIds.ENTRY_LEARN_SETUP,
            RouteDeckActionIds.INTENT_SIGN_IN,
            RouteDeckActionIds.INTENT_REGISTER,
        ],
        recovery_prompt="Choose a visible entry action or describe what you want SaaStoAgent to do.",
    ),
    RouteDeckNodeIds.INTENT: RouteDeckNodeSpec(
        id=RouteDeckNodeIds.INTENT,
        label="Intent",
        lane="auth",
        description="Answer platform questions, draft setup, or route explicit auth intent.",
        prompt_placeholder="Ask about SaaStoAgent, draft setup, or sign in",
        allowed_actions=[
            RouteDeckActionIds.ENTRY_LEARN_PLATFORM,
            RouteDeckActionIds.ENTRY_LEARN_SETUP,
            RouteDeckActionIds.ENTRY_FOLLOW_UP_PATTERN,
            RouteDeckActionIds.INTENT_SIGN_IN,
            RouteDeckActionIds.INTENT_REGISTER,
        ],
        expected_input="Free-text platform question, setup draft, sign-in request, or create-account request.",
        recovery_prompt="Ask a platform question, describe setup, sign in, or create an account.",
    ),
    RouteDeckNodeIds.DISPLAY_NAME: RouteDeckNodeSpec(
        id=RouteDeckNodeIds.DISPLAY_NAME,
        label="Display Name",
        lane="auth",
        description="Collect an optional display name for account creation.",
        prompt_placeholder="Display name, or skip",
        allowed_actions=[RouteDeckActionIds.DISPLAY_NAME_SKIP],
        expected_input="Display name text, skip, or sign in to switch auth mode.",
        recovery_prompt="Provide a display name, choose Skip For Now, or say sign in.",
    ),
    RouteDeckNodeIds.EMAIL: RouteDeckNodeSpec(
        id=RouteDeckNodeIds.EMAIL,
        label="Email",
        lane="auth",
        description="Collect the account email for login or registration.",
        prompt_placeholder="you@example.com",
        expected_input="Valid email address.",
        recovery_prompt="Enter an email address like you@example.com.",
    ),
    RouteDeckNodeIds.PASSWORD: RouteDeckNodeSpec(
        id=RouteDeckNodeIds.PASSWORD,
        label="Password",
        lane="auth",
        description="Collect and verify the password; password values are masked in logs and UI echoes.",
        prompt_placeholder="Password",
        expected_input="Password text. Registration requires at least 8 characters.",
        recovery_prompt="Send the password again. Registration passwords need at least 8 characters.",
    ),
    RouteDeckNodeIds.WORKSPACE_SELECT: RouteDeckNodeSpec(
        id=RouteDeckNodeIds.WORKSPACE_SELECT,
        label="Workspace Select",
        lane="workspace",
        description="Open an existing workspace or describe a new SaaS job.",
        prompt_placeholder="Number or new job description",
        allowed_actions=[RouteDeckActionIds.WORKSPACE_SELECT_OPEN_PATTERN],
        expected_input="Existing workspace number or a new workspace job description.",
        recovery_prompt="Pick a workspace number or describe a new SaaS job.",
    ),
    RouteDeckNodeIds.WORKSPACE_JOB: RouteDeckNodeSpec(
        id=RouteDeckNodeIds.WORKSPACE_JOB,
        label="Workspace Draft",
        lane="workspace",
        description="Collect the job the first operator workspace should own.",
        prompt_placeholder="What SaaS job should this workspace handle?",
        expected_input="Short description of the SaaS job this operator should own.",
        recovery_prompt="Describe the SaaS job, for example billing support or CRM account updates.",
    ),
    RouteDeckNodeIds.WORKSPACE_CONFIRM: RouteDeckNodeSpec(
        id=RouteDeckNodeIds.WORKSPACE_CONFIRM,
        label="Workspace Confirm",
        lane="workspace",
        description="Confirm the workspace name and create it.",
        prompt_placeholder="launch or rename",
        allowed_actions=[RouteDeckActionIds.WORKSPACE_CONFIRM_LAUNCH],
        expected_input="Launch confirmation or replacement workspace name.",
        recovery_prompt="Confirm launch or reply with a different workspace name.",
    ),
    RouteDeckNodeIds.SETUP_INTRO: RouteDeckNodeSpec(
        id=RouteDeckNodeIds.SETUP_INTRO,
        label="REST Setup",
        lane="workspace",
        description="Collect REST API setup details or skip setup into chat.",
        prompt_placeholder="Connect an API or choose an action",
        allowed_actions=[
            RouteDeckActionIds.SETUP_REST_START,
            RouteDeckActionIds.SETUP_REST_CONFIGURE,
            RouteDeckActionIds.SETUP_OPEN_CHAT,
        ],
        expected_input="API setup details, Add API Details, or Skip API Setup.",
        recovery_prompt="Add API details, describe the REST API in chat, or skip setup.",
    ),
    RouteDeckNodeIds.CONNECTION_CONFIRM: RouteDeckNodeSpec(
        id=RouteDeckNodeIds.CONNECTION_CONFIRM,
        label="Connection Confirm",
        lane="workspace",
        description="Review, edit, or activate a REST connection draft.",
        prompt_placeholder="activate or edit setup",
        allowed_actions=[
            RouteDeckActionIds.SETUP_CONNECTION_ACTIVATE,
            RouteDeckActionIds.SETUP_REST_CONFIGURE,
            RouteDeckActionIds.SETUP_OPEN_CHAT,
            RouteDeckActionIds.SETUP_REST_START,
        ],
        expected_input="Activate, edit the setup form, or skip API setup.",
        recovery_prompt="Activate the API, edit details, or skip setup for now.",
    ),
    RouteDeckNodeIds.OPERATOR_READY: RouteDeckNodeSpec(
        id=RouteDeckNodeIds.OPERATOR_READY,
        label="Operator Ready",
        lane="terminal",
        description="Terminal entry state that hands the user to the workspace operator surface.",
        allowed_actions=[
            RouteDeckActionIds.SETUP_REST_START,
            RouteDeckActionIds.INTENT_SIGN_IN,
            RouteDeckActionIds.INTENT_REGISTER,
            RouteDeckActionIds.ENTRY_LEARN_PLATFORM,
            RouteDeckActionIds.ENTRY_LEARN_SETUP,
        ],
        recovery_prompt="Continue in workspace chat or use setup/auth actions if they are visible.",
    ),
}


ACTION_SPECS: dict[str, RouteDeckActionSpec] = {
    RouteDeckActionIds.ENTRY_LEARN_PLATFORM: RouteDeckActionSpec(
        id=RouteDeckActionIds.ENTRY_LEARN_PLATFORM,
        label="What is SaaStoAgent?",
        capability_id="learn",
        description="Ask for a platform overview before signing in.",
        kind="chip",
        category="navigation",
        placement="rail",
        payload={"prompt": "What is SaaStoAgent and what can I build with it?"},
        allowed_nodes=ANY_ENTRY_NODE,
        visibility="persistent",
    ),
    RouteDeckActionIds.ENTRY_LEARN_SETUP: RouteDeckActionSpec(
        id=RouteDeckActionIds.ENTRY_LEARN_SETUP,
        label="How setup works",
        capability_id="setup",
        description="Ask how workspace and API setup works.",
        kind="chip",
        category="setup",
        placement="rail",
        payload={"prompt": "How do I set up a workspace and connect an API?"},
        allowed_nodes=ANY_ENTRY_NODE,
        visibility="persistent",
    ),
    RouteDeckActionIds.ENTRY_FOLLOW_UP_PATTERN: RouteDeckActionSpec(
        id=RouteDeckActionIds.ENTRY_FOLLOW_UP_PATTERN,
        label="Follow-up",
        description="Assistant-suggested follow-up prompt.",
        kind="chip",
        category="navigation",
        placement="inline",
        allowed_nodes=[RouteDeckNodeIds.BOOTSTRAP, RouteDeckNodeIds.INTENT],
        visibility="dynamic",
    ),
    RouteDeckActionIds.INTENT_SIGN_IN: RouteDeckActionSpec(
        id=RouteDeckActionIds.INTENT_SIGN_IN,
        label="Sign In",
        capability_id="signin",
        description="Use an existing operator account.",
        emphasis="primary",
        category="auth",
        placement="next_best",
        allowed_nodes=ANY_ENTRY_NODE,
        visibility="persistent",
    ),
    RouteDeckActionIds.INTENT_REGISTER: RouteDeckActionSpec(
        id=RouteDeckActionIds.INTENT_REGISTER,
        label="Create Account",
        capability_id="register",
        description="Set up a new operator account conversationally.",
        category="auth",
        placement="rail",
        allowed_nodes=ANY_ENTRY_NODE,
        visibility="persistent",
    ),
    RouteDeckActionIds.DISPLAY_NAME_SKIP: RouteDeckActionSpec(
        id=RouteDeckActionIds.DISPLAY_NAME_SKIP,
        label="Skip For Now",
        description="Leave the display name blank and continue to email.",
        category="auth",
        placement="inline",
        allowed_nodes=[RouteDeckNodeIds.DISPLAY_NAME],
    ),
    RouteDeckActionIds.WORKSPACE_SELECT_OPEN_PATTERN: RouteDeckActionSpec(
        id=RouteDeckActionIds.WORKSPACE_SELECT_OPEN_PATTERN,
        label="Open Workspace",
        description="Open one of the listed workspaces.",
        emphasis="primary",
        category="navigation",
        placement="inline",
        allowed_nodes=[RouteDeckNodeIds.WORKSPACE_SELECT],
        visibility="dynamic",
    ),
    RouteDeckActionIds.WORKSPACE_CONFIRM_LAUNCH: RouteDeckActionSpec(
        id=RouteDeckActionIds.WORKSPACE_CONFIRM_LAUNCH,
        label="Launch Workspace",
        description="Create the drafted workspace.",
        emphasis="primary",
        category="navigation",
        placement="inline",
        allowed_nodes=[RouteDeckNodeIds.WORKSPACE_CONFIRM],
    ),
    RouteDeckActionIds.SETUP_REST_START: RouteDeckActionSpec(
        id=RouteDeckActionIds.SETUP_REST_START,
        label="Set Up API",
        capability_id="connect",
        description="Connect or update the REST API this operator can use.",
        emphasis="primary",
        kind="nav",
        category="setup",
        placement="next_best",
        allowed_nodes=[RouteDeckNodeIds.SETUP_INTRO, RouteDeckNodeIds.CONNECTION_CONFIRM, RouteDeckNodeIds.OPERATOR_READY],
        visibility="persistent",
    ),
    RouteDeckActionIds.SETUP_OPEN_CHAT: RouteDeckActionSpec(
        id=RouteDeckActionIds.SETUP_OPEN_CHAT,
        label="Skip API Setup",
        description="Continue without connecting an API right now. API setup remains available in Connections.",
        kind="nav",
        category="navigation",
        placement="inline",
        allowed_nodes=[RouteDeckNodeIds.SETUP_INTRO, RouteDeckNodeIds.CONNECTION_CONFIRM],
    ),
    RouteDeckActionIds.SETUP_REST_CONFIGURE: RouteDeckActionSpec(
        id=RouteDeckActionIds.SETUP_REST_CONFIGURE,
        label="Connect REST API",
        description="Provide the OpenAPI source and auth details for this operator.",
        emphasis="primary",
        kind="form",
        category="setup",
        placement="inline",
        fields=REST_CONNECTION_FIELDS,
        allowed_nodes=[RouteDeckNodeIds.SETUP_INTRO, RouteDeckNodeIds.CONNECTION_CONFIRM],
        sensitive=True,
    ),
    RouteDeckActionIds.SETUP_CONNECTION_ACTIVATE: RouteDeckActionSpec(
        id=RouteDeckActionIds.SETUP_CONNECTION_ACTIVATE,
        label="Activate API",
        description="Create and activate the REST API connection.",
        emphasis="primary",
        category="setup",
        placement="inline",
        allowed_nodes=[RouteDeckNodeIds.CONNECTION_CONFIRM],
    ),
}


EDGE_SPECS = [
    RouteDeckEdgeSpec(from_stage=RouteDeckNodeIds.BOOTSTRAP, to_stage=RouteDeckNodeIds.INTENT, type="conditional", condition="anonymous_start", explanation="Anonymous users enter the public intent stage."),
    RouteDeckEdgeSpec(from_stage=RouteDeckNodeIds.BOOTSTRAP, to_stage=RouteDeckNodeIds.EMAIL, type="conditional", condition="login_initial_intent", action_id=RouteDeckActionIds.INTENT_SIGN_IN, explanation="Explicit sign-in starts email collection."),
    RouteDeckEdgeSpec(from_stage=RouteDeckNodeIds.BOOTSTRAP, to_stage=RouteDeckNodeIds.DISPLAY_NAME, type="conditional", condition="register_initial_intent", action_id=RouteDeckActionIds.INTENT_REGISTER, explanation="Create Account starts registration display-name collection."),
    RouteDeckEdgeSpec(from_stage=RouteDeckNodeIds.BOOTSTRAP, to_stage=RouteDeckNodeIds.WORKSPACE_SELECT, type="conditional", condition="authenticated_many_workspaces", explanation="Authenticated users with multiple workspaces choose one."),
    RouteDeckEdgeSpec(from_stage=RouteDeckNodeIds.BOOTSTRAP, to_stage=RouteDeckNodeIds.WORKSPACE_JOB, type="conditional", condition="authenticated_no_workspaces", explanation="Authenticated users without workspaces draft the first workspace."),
    RouteDeckEdgeSpec(from_stage=RouteDeckNodeIds.BOOTSTRAP, to_stage=RouteDeckNodeIds.OPERATOR_READY, type="conditional", condition="authenticated_single_workspace", explanation="Authenticated users with one workspace open it directly."),
    RouteDeckEdgeSpec(from_stage=RouteDeckNodeIds.INTENT, to_stage=RouteDeckNodeIds.DISPLAY_NAME, type="conditional", condition="register", action_id=RouteDeckActionIds.INTENT_REGISTER, explanation="Registration intent moves to display-name collection."),
    RouteDeckEdgeSpec(from_stage=RouteDeckNodeIds.INTENT, to_stage=RouteDeckNodeIds.EMAIL, type="conditional", condition="login", action_id=RouteDeckActionIds.INTENT_SIGN_IN, explanation="Login intent moves to email collection."),
    RouteDeckEdgeSpec(from_stage=RouteDeckNodeIds.DISPLAY_NAME, to_stage=RouteDeckNodeIds.EMAIL, type="sequence", condition="display_name_collected", action_id=RouteDeckActionIds.DISPLAY_NAME_SKIP, explanation="Display name or skip moves to email."),
    RouteDeckEdgeSpec(from_stage=RouteDeckNodeIds.EMAIL, to_stage=RouteDeckNodeIds.PASSWORD, type="sequence", condition="valid_email", explanation="Valid email moves to password collection."),
    RouteDeckEdgeSpec(from_stage=RouteDeckNodeIds.PASSWORD, to_stage=RouteDeckNodeIds.WORKSPACE_SELECT, type="conditional", condition="authenticated_many_workspaces", explanation="Authenticated users with multiple workspaces choose one."),
    RouteDeckEdgeSpec(from_stage=RouteDeckNodeIds.PASSWORD, to_stage=RouteDeckNodeIds.WORKSPACE_JOB, type="conditional", condition="authenticated_no_workspaces", explanation="Authenticated users without workspaces draft the first workspace."),
    RouteDeckEdgeSpec(from_stage=RouteDeckNodeIds.PASSWORD, to_stage=RouteDeckNodeIds.OPERATOR_READY, type="conditional", condition="authenticated_single_workspace", explanation="Authenticated users with one workspace enter operator mode."),
    RouteDeckEdgeSpec(from_stage=RouteDeckNodeIds.WORKSPACE_SELECT, to_stage=RouteDeckNodeIds.OPERATOR_READY, type="conditional", condition="existing_workspace_selected", action_id=RouteDeckActionIds.WORKSPACE_SELECT_OPEN_PATTERN, explanation="Selecting a workspace opens operator mode."),
    RouteDeckEdgeSpec(from_stage=RouteDeckNodeIds.WORKSPACE_SELECT, to_stage=RouteDeckNodeIds.WORKSPACE_CONFIRM, type="conditional", condition="new_workspace_requested", explanation="A new job description moves to workspace confirmation."),
    RouteDeckEdgeSpec(from_stage=RouteDeckNodeIds.WORKSPACE_JOB, to_stage=RouteDeckNodeIds.WORKSPACE_CONFIRM, type="sequence", condition="workspace_job_collected", explanation="A valid job description creates a workspace draft."),
    RouteDeckEdgeSpec(from_stage=RouteDeckNodeIds.WORKSPACE_CONFIRM, to_stage=RouteDeckNodeIds.OPERATOR_READY, type="conditional", condition="workspace_created", action_id=RouteDeckActionIds.WORKSPACE_CONFIRM_LAUNCH, explanation="Launch creates the workspace and opens operator mode."),
    RouteDeckEdgeSpec(from_stage=RouteDeckNodeIds.OPERATOR_READY, to_stage=RouteDeckNodeIds.SETUP_INTRO, type="conditional", condition="setup_requested", action_id=RouteDeckActionIds.SETUP_REST_START, explanation="Setup can be reopened from a ready workspace."),
    RouteDeckEdgeSpec(from_stage=RouteDeckNodeIds.SETUP_INTRO, to_stage=RouteDeckNodeIds.CONNECTION_CONFIRM, type="conditional", condition="rest_details_ready", action_id=RouteDeckActionIds.SETUP_REST_CONFIGURE, explanation="Complete REST details move to connection confirmation."),
    RouteDeckEdgeSpec(from_stage=RouteDeckNodeIds.SETUP_INTRO, to_stage=RouteDeckNodeIds.OPERATOR_READY, type="conditional", condition="setup_skipped", action_id=RouteDeckActionIds.SETUP_OPEN_CHAT, explanation="Skipping setup returns to operator mode."),
    RouteDeckEdgeSpec(from_stage=RouteDeckNodeIds.CONNECTION_CONFIRM, to_stage=RouteDeckNodeIds.OPERATOR_READY, type="conditional", condition="connection_activated", action_id=RouteDeckActionIds.SETUP_CONNECTION_ACTIVATE, explanation="Activation opens operator mode."),
    RouteDeckEdgeSpec(from_stage=RouteDeckNodeIds.CONNECTION_CONFIRM, to_stage=RouteDeckNodeIds.OPERATOR_READY, type="conditional", condition="setup_skipped", action_id=RouteDeckActionIds.SETUP_OPEN_CHAT, explanation="Skipping setup returns to operator mode."),
]


TEST_PATHS = [
    {"id": "anonymous_learn", "start": RouteDeckNodeIds.BOOTSTRAP, "actions": [RouteDeckActionIds.ENTRY_LEARN_PLATFORM], "expected_nodes": [RouteDeckNodeIds.INTENT]},
    {"id": "sign_in", "start": RouteDeckNodeIds.INTENT, "actions": [RouteDeckActionIds.INTENT_SIGN_IN], "expected_nodes": [RouteDeckNodeIds.EMAIL, RouteDeckNodeIds.PASSWORD]},
    {"id": "sign_up", "start": RouteDeckNodeIds.INTENT, "actions": [RouteDeckActionIds.INTENT_REGISTER, RouteDeckActionIds.DISPLAY_NAME_SKIP], "expected_nodes": [RouteDeckNodeIds.DISPLAY_NAME, RouteDeckNodeIds.EMAIL, RouteDeckNodeIds.PASSWORD]},
    {"id": "setup_skip", "start": RouteDeckNodeIds.SETUP_INTRO, "actions": [RouteDeckActionIds.SETUP_OPEN_CHAT], "expected_nodes": [RouteDeckNodeIds.OPERATOR_READY]},
    {"id": "setup_configure", "start": RouteDeckNodeIds.SETUP_INTRO, "actions": [RouteDeckActionIds.SETUP_REST_CONFIGURE, RouteDeckActionIds.SETUP_CONNECTION_ACTIVATE], "expected_nodes": [RouteDeckNodeIds.CONNECTION_CONFIRM, RouteDeckNodeIds.OPERATOR_READY]},
]


def _matches_action(pattern: str, action_id: str) -> bool:
    if pattern == action_id:
        return True
    if pattern.endswith("*"):
        return action_id.startswith(pattern[:-1])
    return False


def _spec_for_action_id(action_id: str) -> RouteDeckActionSpec | None:
    if action_id in ACTION_SPECS:
        return ACTION_SPECS[action_id]
    for pattern, spec in ACTION_SPECS.items():
        if _matches_action(pattern, action_id):
            return spec
    return None


def get_action_spec(action_id: str) -> RouteDeckActionSpec:
    spec = _spec_for_action_id(action_id)
    if spec is None:
        raise KeyError(action_id)
    return spec


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


def action_card(
    action_id: str,
    *,
    label: str | None = None,
    description: str | None = None,
    emphasis: str | None = None,
    kind: str | None = None,
    fields: list[EntryActionField] | None = None,
    payload: dict[str, Any] | None = None,
    draft: dict[str, Any] | None = None,
    disabled_reason: str | None = None,
) -> EntryActionCard:
    spec = get_action_spec(action_id)
    resolved_fields = fields
    if resolved_fields is None:
        resolved_fields = [_field_card(field, draft=draft) for field in spec.fields]
    return EntryActionCard(
        id=action_id,
        label=label or spec.label,
        capability_id=spec.capability_id,
        description=description if description is not None else spec.description,
        emphasis=emphasis or spec.emphasis,
        kind=kind or spec.kind,
        category=spec.category,
        placement=spec.placement,
        recovery_prompt=spec.recovery_prompt,
        fields=resolved_fields,
        payload=payload if payload is not None else dict(spec.payload),
        disabled_reason=disabled_reason,
    )


def is_action_allowed_for_node(node: str | None, action_id: str) -> bool:
    spec = _spec_for_action_id(action_id)
    if spec is None:
        return False
    if node is None:
        return spec.visibility == "persistent"
    return any(_matches_action(allowed_node, node) for allowed_node in spec.allowed_nodes)


def contextual_actions_for_node(node: str | None) -> list[EntryActionCard]:
    if node is None or node not in NODE_SPECS:
        return []
    actions: list[EntryActionCard] = []
    for action_id in NODE_SPECS[node].allowed_actions:
        if action_id.endswith("*"):
            continue
        spec = ACTION_SPECS.get(action_id)
        if spec and spec.visibility != "persistent":
            actions.append(action_card(action_id))
    return actions


def persistent_actions_for_context(
    *,
    node: str | None,
    current_user: "User | None",
    active_workspace_id: Any | None = None,
) -> list[EntryActionCard]:
    if current_user is None:
        if node in AUTH_NODES:
            return []
        return [
            action_card(RouteDeckActionIds.ENTRY_LEARN_PLATFORM),
            action_card(RouteDeckActionIds.ENTRY_LEARN_SETUP),
            action_card(RouteDeckActionIds.INTENT_SIGN_IN),
            action_card(RouteDeckActionIds.INTENT_REGISTER),
        ]

    if active_workspace_id and node == RouteDeckNodeIds.OPERATOR_READY:
        return [action_card(RouteDeckActionIds.SETUP_REST_START)]

    return []


def reachable_nodes(node: str | None) -> list[str]:
    return core_reachable_nodes(build_route_deck_manifest(), node)


def blocked_actions_for_node(node: str | None) -> list[dict[str, str]]:
    blocked: list[dict[str, str]] = []
    for action_id, spec in ACTION_SPECS.items():
        if spec.visibility == "dynamic":
            continue
        if not is_action_allowed_for_node(node, action_id):
            blocked.append({"id": action_id, "reason": f"Only valid in: {', '.join(spec.allowed_nodes)}"})
    return blocked


def recover_from_invalid_action(node: str | None, action_id: str) -> tuple[str, list[EntryActionCard]]:
    node_spec = NODE_SPECS.get(node or "")
    valid_actions = contextual_actions_for_node(node)
    message = (
        f"`{action_id}` is not available from {node_spec.label if node_spec else 'this step'}. "
        f"{node_spec.recovery_prompt if node_spec else 'Choose one of the visible actions or continue in chat.'}"
    )
    return message, valid_actions


def build_runtime_snapshot(
    *,
    current_node: str | None,
    executed_nodes: list[str] | None = None,
    valid_actions: list[EntryActionCard] | None = None,
    diagnostics: dict[str, Any] | None = None,
) -> dict[str, Any]:
    actions = valid_actions if valid_actions is not None else contextual_actions_for_node(current_node)
    return build_core_runtime_snapshot(
        build_route_deck_manifest(),
        current_node=current_node,
        valid_actions=[action.model_dump(mode="json") for action in actions],
        blocked_actions=blocked_actions_for_node(current_node),
        executed_nodes=executed_nodes,
        diagnostics=diagnostics,
    )


def build_route_deck_manifest() -> RouteDeckManifest:
    sensitive_policy = RouteDeckSensitivePolicy(
        masked_payload_keys=MASKED_PAYLOAD_KEYS,
        chat_secret_fields=["password"],
        url_or_modal_only_fields=["credential_value"],
        note="Secrets may be submitted through controlled fields, but logs, artifacts, and chat echoes must mask them.",
    )
    return RouteDeckManifest(
        version=ROUTE_DECK_VERSION,
        nodes=list(NODE_SPECS.values()),
        edges=EDGE_SPECS,
        actions=list(ACTION_SPECS.values()),
        policies={"sensitive": sensitive_policy.model_dump(mode="json")},
        test_paths=TEST_PATHS,
    )


def validate_route_deck_manifest() -> list[str]:
    return validate_manifest(
        build_route_deck_manifest(),
        masked_payload_keys=MASKED_PAYLOAD_KEYS,
    )
