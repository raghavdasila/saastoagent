from __future__ import annotations

from typing import Any

from backend.core.models import User
from backend.core.schemas import EntryActionCard, EntryActionField, WorkspaceRead


def _short_description(value: str | None) -> str | None:
    if value is None or len(value) <= 240:
        return value
    return f"{value[:237].rstrip()}..."


def entry_action(
    action_id: str,
    label: str,
    *,
    description: str | None = None,
    emphasis: str = "secondary",
    kind: str = "button",
    fields: list[EntryActionField] | None = None,
    payload: dict[str, Any] | None = None,
) -> EntryActionCard:
    return EntryActionCard(
        id=action_id,
        label=label,
        description=_short_description(description),
        emphasis=emphasis,
        kind=kind,
        fields=fields or [],
        payload=payload or {},
    )


def intent_actions() -> list[EntryActionCard]:
    return [
        entry_action(
            "intent.sign_in",
            "Sign In",
            description="Use an existing operator account.",
            emphasis="primary",
        ),
        entry_action(
            "intent.register",
            "Create Account",
            description="Set up a new operator account conversationally.",
        ),
    ]


def entry_assistant_actions() -> list[EntryActionCard]:
    return [
        entry_action(
            "entry.learn.platform",
            "What is SaaStoAgent?",
            description="Ask for a platform overview before signing in.",
            kind="chip",
            payload={"prompt": "What is SaaStoAgent and what can I build with it?"},
        ),
        entry_action(
            "entry.learn.setup",
            "How setup works",
            description="Ask how workspace and API setup works.",
            kind="chip",
            payload={"prompt": "How do I set up a workspace and connect an API?"},
        ),
        entry_action(
            "intent.sign_in",
            "Sign In",
            description="Use an existing operator account.",
            emphasis="primary",
        ),
        entry_action(
            "intent.register",
            "Create Account",
            description="Set up a new operator account.",
        ),
    ]


def persistent_entry_actions(
    *,
    node: str | None,
    current_user: User | None,
    active_workspace_id: Any | None = None,
) -> list[EntryActionCard]:
    if current_user is None:
        if node in {"display_name", "email", "password"}:
            return []
        return entry_assistant_actions()

    if active_workspace_id and node == "operator_ready":
        return [
            entry_action(
                "setup.rest.start",
                "Set Up API",
                description="Connect or update the REST API this operator can use.",
                emphasis="primary",
                kind="nav",
            )
        ]

    return []


def display_name_actions() -> list[EntryActionCard]:
    return [
        entry_action(
            "display_name.skip",
            "Skip For Now",
            description="Leave the display name blank and continue to email.",
        )
    ]


def workspace_confirm_actions(workspace_name: str, workspace_slug: str) -> list[EntryActionCard]:
    return [
        entry_action(
            "workspace_confirm.launch",
            "Launch Workspace",
            description=f"Create {workspace_name} at /{workspace_slug}.",
            emphasis="primary",
        )
    ]


def workspace_select_actions(workspaces: list[WorkspaceRead]) -> list[EntryActionCard]:
    if len(workspaces) > 3:
        return []

    actions: list[EntryActionCard] = []
    for index, workspace in enumerate(workspaces, 1):
        actions.append(
            entry_action(
                f"workspace_select.open:{index}",
                workspace.name,
                description=f"Open /{workspace.slug}",
                emphasis="primary" if index == 1 else "secondary",
            )
        )
    return actions


def standard_workspace_actions() -> list[EntryActionCard]:
    return [
        entry_action(
            "setup.rest.start",
            "Set Up API",
            description="Connect or update the REST API this operator can use.",
            emphasis="primary",
            kind="nav",
        ),
        entry_action(
            "setup.open_chat",
            "Skip API Setup",
            description="Continue without connecting an API right now. API setup remains available in Connections.",
            kind="nav",
        ),
    ]


def setup_chat_actions() -> list[EntryActionCard]:
    return [
        entry_action(
            "setup.rest.start",
            "Add API Details",
            description="Open a structured setup form for the API details.",
            emphasis="primary",
        ),
        entry_action(
            "setup.open_chat",
            "Skip API Setup",
            description="Continue without connecting an API right now. API setup remains available in Connections.",
            kind="nav",
        ),
    ]


def rest_connection_form_action(
    *,
    draft: dict[str, Any] | None = None,
    label: str = "Connect REST API",
) -> EntryActionCard:
    draft = draft or {}
    return entry_action(
        "setup.rest.configure",
        label,
        description="Provide the OpenAPI source and auth details for this operator.",
        emphasis="primary",
        kind="form",
        fields=[
            EntryActionField(
                key="name",
                label="Connection name",
                required=True,
                placeholder="Acme Billing API",
                default=draft.get("name", ""),
            ),
            EntryActionField(
                key="base_url",
                label="Base URL",
                field_type="url",
                required=True,
                placeholder="https://api.example.com",
                default=draft.get("base_url", ""),
            ),
            EntryActionField(
                key="spec_url",
                label="OpenAPI spec URL",
                field_type="url",
                required=True,
                placeholder="https://api.example.com/openapi.yaml",
                default=draft.get("spec_url", ""),
            ),
            EntryActionField(
                key="auth_type",
                label="Auth type",
                field_type="select",
                required=True,
                default=draft.get("auth_type", "none"),
                options=[
                    {"value": "none", "label": "No auth"},
                    {"value": "bearer", "label": "Bearer token"},
                    {"value": "api_key_header", "label": "API key header"},
                    {"value": "api_key_query", "label": "API key query param"},
                    {"value": "basic", "label": "Basic auth"},
                    {"value": "custom_header", "label": "Custom header"},
                ],
            ),
            EntryActionField(
                key="credential_value",
                label="Credential",
                field_type="password",
                placeholder="Token, API key, or user:pass",
                default="",
                help_text="Leave empty when auth type is No auth.",
            ),
            EntryActionField(
                key="header_name",
                label="Header name",
                placeholder="X-API-Key",
                default=draft.get("header_name", ""),
            ),
            EntryActionField(
                key="query_param_name",
                label="Query param name",
                placeholder="api_key",
                default=draft.get("query_param_name", ""),
            ),
        ],
    )


def connection_confirm_actions(draft: dict[str, Any]) -> list[EntryActionCard]:
    return [
        entry_action(
            "setup.connection.activate",
            "Activate API",
            description=f"Create and activate {draft.get('name') or 'this REST API'}.",
            emphasis="primary",
        ),
        rest_connection_form_action(draft=draft, label="Edit Details"),
        *standard_workspace_actions(),
    ]


def setup_intro_actions(draft: dict[str, Any] | None = None) -> list[EntryActionCard]:
    return [
        rest_connection_form_action(draft=draft),
        *standard_workspace_actions(),
    ]
