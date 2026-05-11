from __future__ import annotations

from typing import Any

from backend.core.models import User
from backend.core.schemas import EntryActionCard, EntryActionField, WorkspaceRead
from backend.services.route_deck import RouteDeckActionIds
from backend.services.route_deck.catalog import action_card as graph_action_card
from backend.services.route_deck.catalog import persistent_actions_for_context
from backend.services.route_deck.ids import workspace_select_open_action_id


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
    try:
        return graph_action_card(
            action_id,
            label=label,
            description=_short_description(description),
            emphasis=emphasis,
            kind=kind,
            fields=fields,
            payload=payload,
        )
    except KeyError:
        return EntryActionCard(
            id=action_id,
            label=label,
            capability_id=None,
            description=_short_description(description),
            emphasis=emphasis,
            kind=kind,
            fields=fields or [],
            payload=payload or {},
        )


def intent_actions() -> list[EntryActionCard]:
    return [
        entry_action(
            RouteDeckActionIds.INTENT_SIGN_IN,
            "Sign In",
            description="Use an existing operator account.",
            emphasis="primary",
        ),
        entry_action(
            RouteDeckActionIds.INTENT_REGISTER,
            "Create Account",
            description="Set up a new operator account conversationally.",
        ),
    ]


def entry_assistant_actions() -> list[EntryActionCard]:
    return [
        entry_action(
            RouteDeckActionIds.ENTRY_LEARN_PLATFORM,
            "What is SaaStoAgent?",
            description="Ask for a platform overview before signing in.",
            kind="chip",
            payload={"prompt": "What is SaaStoAgent and what can I build with it?"},
        ),
        entry_action(
            RouteDeckActionIds.ENTRY_LEARN_SETUP,
            "How setup works",
            description="Ask how workspace and API setup works.",
            kind="chip",
            payload={"prompt": "How do I set up a workspace and connect an API?"},
        ),
        entry_action(
            RouteDeckActionIds.INTENT_SIGN_IN,
            "Sign In",
            description="Use an existing operator account.",
            emphasis="primary",
        ),
        entry_action(
            RouteDeckActionIds.INTENT_REGISTER,
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
    return persistent_actions_for_context(
        node=node,
        current_user=current_user,
        active_workspace_id=active_workspace_id,
    )


def display_name_actions() -> list[EntryActionCard]:
    return [
        entry_action(
            RouteDeckActionIds.DISPLAY_NAME_SKIP,
            "Skip For Now",
            description="Leave the display name blank and continue to email.",
        )
    ]


def workspace_confirm_actions(workspace_name: str, workspace_slug: str) -> list[EntryActionCard]:
    return [
        entry_action(
            RouteDeckActionIds.WORKSPACE_CONFIRM_LAUNCH,
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
                workspace_select_open_action_id(index),
                workspace.name,
                description=f"Open /{workspace.slug}",
                emphasis="primary" if index == 1 else "secondary",
            )
        )
    return actions


def standard_workspace_actions() -> list[EntryActionCard]:
    return [
        entry_action(
            RouteDeckActionIds.SETUP_REST_START,
            "Set Up API",
            description="Connect or update the REST API this operator can use.",
            emphasis="primary",
            kind="nav",
        ),
        entry_action(
            RouteDeckActionIds.SETUP_OPEN_CHAT,
            "Skip API Setup",
            description="Continue without connecting an API right now. API setup remains available in Connections.",
            kind="nav",
        ),
    ]


def setup_chat_actions() -> list[EntryActionCard]:
    return [
        entry_action(
            RouteDeckActionIds.SETUP_REST_START,
            "Add API Details",
            description="Open a structured setup form for the API details.",
            emphasis="primary",
        ),
        entry_action(
            RouteDeckActionIds.SETUP_OPEN_CHAT,
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
    return graph_action_card(
        RouteDeckActionIds.SETUP_REST_CONFIGURE,
        label=label,
        draft=draft,
    )


def connection_confirm_actions(draft: dict[str, Any]) -> list[EntryActionCard]:
    return [
        entry_action(
            RouteDeckActionIds.SETUP_CONNECTION_ACTIVATE,
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
