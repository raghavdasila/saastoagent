from __future__ import annotations

import re
from typing import Any

from sqlalchemy import func, select

from backend.core.credentials import encrypt_value
from backend.core.models import (
    AuthType,
    Connection,
    ConnectionActivationState,
    ConnectionType,
    EncryptedCredential,
    GeneratedTool,
    User,
    Workspace,
    WorkspaceMember,
    WorkspaceRole,
)
from backend.core.schemas import WorkspaceRead
from backend.core.tenancy import create_tenant_schema
from backend.services.discovery.activation import ActivationService
from backend.services.route_deck import RouteDeckActionIds
from backend.services.route_deck.ids import is_workspace_select_open_action

from .graph_runtime import EntryRuntimeState, merge_messages
from .ui_actions import (
    connection_confirm_actions,
    display_name_actions,
    entry_assistant_actions,
    setup_chat_actions,
    setup_intro_actions,
    standard_workspace_actions,
    workspace_confirm_actions,
    workspace_select_actions,
)
from .setup_planner import plan_setup_turn

WORKSPACE_SUFFIX = "Workspace"


def _to_slug(value: str) -> str:
    return re.sub(
        r"-+",
        "-",
        re.sub(r"\s+", "-", re.sub(r"[^a-z0-9\s-]", "", value.lower()).strip()),
    )


def _normalize_workspace_name(value: str) -> str:
    cleaned = re.sub(
        r"\s+",
        " ",
        re.sub(r"^(create|launch|make|start|open)\s+", "", value, flags=re.I),
    ).strip()
    cleaned = re.sub(
        r"^(i\s+(want|need)\s+)?(it|this operator|the operator)\s+(will|should|can|needs to|is going to|to)\s+",
        "",
        cleaned,
        flags=re.I,
    ).strip()
    cleaned = re.sub(r"^(talk|speak|connect)\s+(to|with)\s+my\s+", "my ", cleaned, flags=re.I).strip()
    if not cleaned:
        return ""
    if re.fullmatch(r"(my\s+)?(saas|app|application|platform|product)", cleaned, flags=re.I):
        return f"SaaS Operations {WORKSPACE_SUFFIX}"

    words: list[str] = []
    for part in cleaned.split(" "):
        lowered = part.lower()
        if lowered == "saas":
            words.append("SaaS")
        elif lowered == "api":
            words.append("API")
        elif lowered in {"crm", "erp"}:
            words.append(lowered.upper())
        else:
            words.append(part[:1].upper() + part[1:] if part else part)
    name = " ".join(words).strip()
    if not name.lower().endswith(("workspace", "operator")):
        name = f"{name} {WORKSPACE_SUFFIX}"
    return name


def _workspace_list_text(workspaces: list[WorkspaceRead]) -> str:
    return "\n".join(
        f"{index}. {workspace.name}  /{workspace.slug}"
        for index, workspace in enumerate(workspaces, 1)
    )


def _wants_confirm(value: str) -> bool:
    return bool(
        re.match(r"^(launch|create|yes|y|go|continue|ship|open|do it)$", value.strip(), re.I)
    )


def _auth_required(state: EntryRuntimeState) -> dict[str, Any]:
    return {
        "node": "intent",
        "intent": None,
        "display_name": "",
        "email": "",
        "workspace_name": "",
        "workspace_slug": "",
        "active_connection_id": None,
        "connection_draft": {},
        "messages": merge_messages(
            state,
            "Your authentication context is missing. Say `sign in` or `create account` to continue.",
        ),
    }


def _clear_workspace_draft(state: EntryRuntimeState, message: str) -> dict[str, Any]:
    return {
        "node": "intent",
        "workspace_name": "",
        "workspace_slug": "",
        "active_workspace_id": None,
        "messages": merge_messages(state, message),
        "available_actions": entry_assistant_actions(),
    }


async def list_workspaces(state: EntryRuntimeState, user_id) -> list[WorkspaceRead]:
    db = state["runtime"].db
    stmt = (
        select(Workspace, WorkspaceMember.role)
        .join(WorkspaceMember, WorkspaceMember.workspace_id == Workspace.id)
        .where(WorkspaceMember.user_id == user_id)
        .order_by(Workspace.created_at.desc())
    )
    rows = (await db.execute(stmt)).all()
    return [
        WorkspaceRead(
            id=workspace.id,
            name=workspace.name,
            slug=workspace.slug,
            created_by=workspace.created_by,
            created_at=workspace.created_at,
            role=role.value,
        )
        for workspace, role in rows
    ]


async def create_workspace(
    state: EntryRuntimeState,
    *,
    current_user: User,
    name: str,
    slug: str,
) -> WorkspaceRead:
    db = state["runtime"].db
    existing = await db.execute(select(Workspace).where(Workspace.slug == slug))
    if existing.scalar_one_or_none():
        raise ValueError("Workspace slug already taken")

    workspace = Workspace(
        name=name,
        slug=slug,
        created_by=current_user.id,
    )
    db.add(workspace)
    await db.flush()

    db.add(
        WorkspaceMember(
            user_id=current_user.id,
            workspace_id=workspace.id,
            role=WorkspaceRole.owner,
        )
    )
    await db.flush()
    await create_tenant_schema(workspace.id)

    return WorkspaceRead(
        id=workspace.id,
        name=workspace.name,
        slug=workspace.slug,
        created_by=workspace.created_by,
        created_at=workspace.created_at,
        role=WorkspaceRole.owner.value,
    )


async def _ready_connection_count(state: EntryRuntimeState, workspace_id) -> int:
    db = state["runtime"].db
    return int(
        (
            await db.execute(
                select(func.count(Connection.id))
                .join(ConnectionActivationState, ConnectionActivationState.connection_id == Connection.id, isouter=True)
                .where(
                    Connection.workspace_id == workspace_id,
                    ConnectionActivationState.overall_status == "ready",
                )
            )
        ).scalar_one()
    )


async def _open_workspace_transition(
    state: EntryRuntimeState,
    *,
    workspace: WorkspaceRead,
    workspaces: list[WorkspaceRead] | None = None,
    messages: list | None = None,
) -> dict[str, Any]:
    base_messages = messages if messages is not None else state.get("messages", [])
    entry_draft = state.get("entry_draft") or {}
    carried_connection_draft = state.get("connection_draft") or entry_draft.get("api_draft") or {}
    if await _ready_connection_count(state, workspace.id) > 0:
        return {
            "node": "operator_ready",
            "active_workspace_id": workspace.id,
            "messages": merge_messages({**state, "messages": base_messages}, f"Opening **{workspace.name}** now."),
            "workspaces": workspaces or [workspace],
            "replace_path": f"/w/{workspace.id}",
            "available_actions": standard_workspace_actions(),
        }

    return {
        "node": "operator_ready",
        "active_workspace_id": workspace.id,
        "connection_draft": carried_connection_draft,
        "messages": merge_messages(
            {**state, "messages": base_messages},
            f"**{workspace.name}** is ready. I kept your API draft; Connections can finish the API setup when you need it."
            if carried_connection_draft
            else f"**{workspace.name}** is ready. You can chat here now, and use Connections when you want to add the API.",
        ),
        "workspaces": workspaces or [workspace],
        "replace_path": f"/w/{workspace.id}",
        "available_actions": standard_workspace_actions(),
    }


async def advance_authenticated_user(
    state: EntryRuntimeState,
    *,
    current_user: User,
    extra_messages: list[str] | None = None,
) -> dict[str, Any]:
    workspaces = await list_workspaces(state, current_user.id)
    messages = merge_messages(state, *(extra_messages or []))

    if len(workspaces) == 1:
        workspace = workspaces[0]
        return await _open_workspace_transition(
            state,
            workspace=workspace,
            workspaces=workspaces,
            messages=messages,
        )

    if len(workspaces) > 1:
        return {
            "node": "workspace_select",
            "active_workspace_id": None,
            "messages": merge_messages(
                {**state, "messages": messages},
                "Which operator workspace do you want to open?\n\n"
                f"{_workspace_list_text(workspaces)}\n\n"
                "Type the number to open one, or enter a new workspace name.",
            ),
            "workspaces": workspaces,
            "available_actions": workspace_select_actions(workspaces),
            "replace_path": None,
        }

    entry_draft = state.get("entry_draft") or {}
    draft_workspace_name = entry_draft.get("workspace_name") or entry_draft.get("workspace_job")
    if draft_workspace_name:
        workspace_name = _normalize_workspace_name(str(draft_workspace_name))
        workspace_slug = _to_slug(workspace_name)
        return {
            "node": "workspace_confirm",
            "active_workspace_id": None,
            "workspace_name": workspace_name,
            "workspace_slug": workspace_slug,
            "messages": merge_messages(
                {**state, "messages": messages},
                f"I kept your draft. I can create **{workspace_name}** at /{workspace_slug}. Type `launch` to confirm, or reply with a different name.",
            ),
            "workspaces": workspaces,
            "replace_path": None,
            "available_actions": workspace_confirm_actions(workspace_name, workspace_slug),
        }

    return {
        "node": "workspace_job",
        "active_workspace_id": None,
        "messages": merge_messages(
            {**state, "messages": messages},
            "No workspaces yet. What should this workspace be called?",
        ),
        "workspaces": workspaces,
        "replace_path": None,
    }


async def workspace_select_node(state: EntryRuntimeState) -> dict[str, Any]:
    current_user = state.get("current_user")
    if current_user is None:
        return _auth_required(state)

    selected_action_id = _selected_action_id(state)
    if selected_action_id in (RouteDeckActionIds.NAV_BACK, RouteDeckActionIds.NAV_CANCEL):
        return _clear_workspace_draft(
            state,
            "Canceled workspace selection. You can ask a question, create a workspace, or connect an API later.",
        )

    workspaces = await list_workspaces(state, current_user.id)
    if is_workspace_select_open_action(selected_action_id):
        raw_index = selected_action_id.split(":", 1)[1]
        try:
            selection = int(raw_index)
        except ValueError:
            selection = None
    else:
        selection = None

    value = (state.get("user_input") or "").strip()
    if selection is None:
        try:
            selection = int(value)
        except ValueError:
            selection = None

    if selection is not None:
        if 1 <= selection <= len(workspaces):
            workspace = workspaces[selection - 1]
            return await _open_workspace_transition(
                state,
                workspace=workspace,
                workspaces=workspaces,
                messages=merge_messages(state, f"Opening **{workspace.name}**."),
            )
        return {
            "messages": merge_messages(
                state,
                f"Pick a number between 1 and {len(workspaces)}, or enter a new workspace name.",
            ),
            "workspaces": workspaces,
            "available_actions": workspace_select_actions(workspaces),
        }

    workspace_name = _normalize_workspace_name(value)
    if not workspace_name:
        return {
            "messages": merge_messages(
                state,
                "Type a number from the list to open an existing workspace, or enter a new workspace name.",
            ),
            "workspaces": workspaces,
            "available_actions": workspace_select_actions(workspaces),
        }

    workspace_slug = _to_slug(workspace_name)
    return {
        "node": "workspace_confirm",
        "workspace_name": workspace_name,
        "workspace_slug": workspace_slug,
        "messages": merge_messages(
            state,
            f"I can create **{workspace_name}** at /{workspace_slug}. Type `launch` to confirm, or reply with a different name.",
        ),
        "workspaces": workspaces,
        "available_actions": workspace_confirm_actions(workspace_name, workspace_slug),
    }


async def workspace_job_node(state: EntryRuntimeState) -> dict[str, Any]:
    current_user = state.get("current_user")
    if current_user is None:
        return _auth_required(state)

    selected_action_id = _selected_action_id(state)
    if selected_action_id in (RouteDeckActionIds.NAV_BACK, RouteDeckActionIds.NAV_CANCEL):
        return _clear_workspace_draft(
            state,
            "Canceled workspace creation. You can ask a question or start workspace setup again.",
        )

    value = (state.get("user_input") or "").strip()
    workspace_name = _normalize_workspace_name(value)
    if not workspace_name:
        return {"messages": merge_messages(state, "I need a workspace name before I can create it.")}

    workspace_slug = _to_slug(workspace_name)
    return {
        "node": "workspace_confirm",
        "workspace_name": workspace_name,
        "workspace_slug": workspace_slug,
        "messages": merge_messages(
            state,
            f"I can create **{workspace_name}** at /{workspace_slug}. Type `launch` to confirm, or reply with a different name.",
        ),
        "available_actions": workspace_confirm_actions(workspace_name, workspace_slug),
    }


async def workspace_confirm_node(state: EntryRuntimeState) -> dict[str, Any]:
    current_user = state.get("current_user")
    if current_user is None:
        return _auth_required(state)

    selected_action_id = _selected_action_id(state)
    if selected_action_id == RouteDeckActionIds.NAV_CANCEL:
        return _clear_workspace_draft(
            state,
            "Canceled workspace creation. You can ask a question or create a different workspace.",
        )
    if selected_action_id == RouteDeckActionIds.NAV_BACK:
        workspaces = await list_workspaces(state, current_user.id)
        if workspaces:
            return {
                "node": "workspace_select",
                "workspace_name": "",
                "workspace_slug": "",
                "messages": merge_messages(
                    state,
                    "Back to workspace selection. Pick a workspace number or enter a new workspace name.",
                ),
                "workspaces": workspaces,
                "available_actions": workspace_select_actions(workspaces),
            }
        return {
            "node": "workspace_job",
            "workspace_name": "",
            "workspace_slug": "",
            "messages": merge_messages(
                state,
                "Back to workspace setup. Enter the workspace name.",
            ),
        }

    value = (state.get("user_input") or "").strip()
    if selected_action_id == RouteDeckActionIds.WORKSPACE_CONFIRM_LAUNCH or _wants_confirm(value):
        workspace_name = _normalize_workspace_name(state.get("workspace_name", ""))
        workspace_slug = _to_slug(workspace_name)
        if not workspace_name or not workspace_slug:
            return {
                "node": "workspace_job",
                "messages": merge_messages(
                    state,
                    "I lost the workspace name. Enter it again.",
                ),
            }

        try:
            workspace = await create_workspace(
                state,
                current_user=current_user,
                name=workspace_name,
                slug=workspace_slug,
            )
        except ValueError as exc:
            return {
                "workspace_name": workspace_name,
                "workspace_slug": workspace_slug,
                "messages": merge_messages(
                    state,
                    f"{exc}. Reply with a different name, or type `launch` to retry.",
                ),
                "available_actions": workspace_confirm_actions(workspace_name, workspace_slug),
            }

        transition = await _open_workspace_transition(
            state,
            workspace=workspace,
            workspaces=[workspace],
            messages=merge_messages(state, f"Launching **{workspace.name}** now."),
        )
        return {
            **transition,
            "workspace_name": workspace.name,
            "workspace_slug": workspace.slug,
        }

    workspace_name = _normalize_workspace_name(value)
    if not workspace_name:
        return {
            "messages": merge_messages(state, "That didn't give me a valid workspace name. Try again."),
            "available_actions": workspace_confirm_actions(
                state.get("workspace_name", "your workspace"),
                state.get("workspace_slug", "workspace"),
            ),
        }

    workspace_slug = _to_slug(workspace_name)
    return {
        "workspace_name": workspace_name,
        "workspace_slug": workspace_slug,
        "messages": merge_messages(
            state,
            f"Updated to **{workspace_name}** at /{workspace_slug}. Type `launch` to confirm.",
        ),
        "available_actions": workspace_confirm_actions(workspace_name, workspace_slug),
    }


async def operator_ready_node(state: EntryRuntimeState) -> dict[str, Any]:
    selected_action_id = _selected_action_id(state)
    if selected_action_id == RouteDeckActionIds.INTENT_SIGN_IN:
        return {
            "node": "email",
            "intent": "login",
            "display_name": "",
            "messages": merge_messages(state, "Signing you in. Give me the email for your account."),
        }
    if selected_action_id == RouteDeckActionIds.INTENT_REGISTER:
        return {
            "node": "display_name",
            "intent": "register",
            "messages": merge_messages(
                state,
                "Creating your account. What display name should I use? Type `skip` to leave it blank.",
            ),
            "available_actions": display_name_actions(),
        }
    if state.get("current_user") is None:
        return _auth_required(state)
    if selected_action_id == RouteDeckActionIds.SETUP_REST_START:
        return {
            "node": "setup_intro",
            "messages": merge_messages(state, "Let's connect the REST API this operator can use."),
            "available_actions": setup_intro_actions(state.get("connection_draft") or {}),
        }
    return {}


def _selected_action_id(state: EntryRuntimeState) -> str | None:
    value = state.get("selected_action_id")
    return value.strip() if isinstance(value, str) and value.strip() else None


def _action_payload(state: EntryRuntimeState) -> dict[str, Any]:
    payload = state.get("action_payload")
    return payload if isinstance(payload, dict) else {}


def _validate_connection_payload(payload: dict[str, Any]) -> tuple[dict[str, Any] | None, str | None]:
    name = str(payload.get("name") or "").strip()
    base_url = str(payload.get("base_url") or "").strip()
    spec_url = str(payload.get("spec_url") or "").strip()
    auth_type = str(payload.get("auth_type") or "none").strip()
    if not name:
        return None, "Give the connection a short name."
    if not base_url.startswith(("http://", "https://")):
        return None, "Base URL must start with http:// or https://."
    if not spec_url.startswith(("http://", "https://")):
        return None, "OpenAPI spec URL must start with http:// or https://."
    if auth_type not in {
        "none",
        "bearer",
        "api_key_header",
        "api_key_query",
        "basic",
        "custom_header",
        "oauth_client_credentials",
    }:
        return None, "Choose a supported auth type."
    if auth_type != "none" and not str(payload.get("credential_value") or "").strip():
        return None, "This auth type needs a credential."
    return {
        "name": name,
        "base_url": base_url,
        "spec_url": spec_url,
        "auth_type": auth_type,
        "credential_value": str(payload.get("credential_value") or "").strip(),
        "header_name": str(payload.get("header_name") or "").strip(),
        "query_param_name": str(payload.get("query_param_name") or "").strip(),
    }, None


async def setup_intro_node(state: EntryRuntimeState) -> dict[str, Any]:
    if state.get("current_user") is None:
        return _auth_required(state)
    if not state.get("active_workspace_id"):
        return {
            "node": "workspace_job",
            "messages": merge_messages(state, "I lost the workspace context. Enter the workspace name again."),
        }

    selected_action_id = _selected_action_id(state)
    entry_draft = state.get("entry_draft") or {}
    current_connection_draft = state.get("connection_draft") or entry_draft.get("api_draft") or {}
    if selected_action_id in (RouteDeckActionIds.NAV_BACK, RouteDeckActionIds.NAV_CANCEL):
        return {
            "node": "operator_ready",
            "messages": merge_messages(state, "Canceled API setup. You can continue in chat or reopen setup from Connections."),
            "available_actions": standard_workspace_actions(),
        }
    if selected_action_id == RouteDeckActionIds.SETUP_OPEN_CHAT:
        return {
            "node": "operator_ready",
            "messages": merge_messages(state, "Continuing without API setup for now. API setup remains available in Connections."),
            "available_actions": standard_workspace_actions(),
        }
    if selected_action_id == RouteDeckActionIds.SETUP_REST_START:
        planner_result = await plan_setup_turn(
            workspace_name=state.get("workspace_name"),
            user_input=state.get("user_input"),
            existing_draft=current_connection_draft or None,
            force_form=True,
        )
        return {
            "messages": merge_messages(
                state,
                planner_result.message,
            ),
            "connection_draft": planner_result.draft,
            "available_actions": setup_intro_actions(planner_result.draft),
        }
    if selected_action_id == RouteDeckActionIds.SETUP_REST_CONFIGURE:
        draft, error = _validate_connection_payload(_action_payload(state))
        if error:
            return {
                "messages": merge_messages(state, error),
                "available_actions": setup_intro_actions(_action_payload(state)),
            }
        assert draft is not None
        return {
            "node": "connection_confirm",
            "connection_draft": draft,
            "messages": merge_messages(
                state,
                f"I can connect **{draft['name']}** using `{draft['spec_url']}`. Activate it now?",
            ),
            "available_actions": connection_confirm_actions(draft),
        }

    if selected_action_id is None:
        planner_result = await plan_setup_turn(
            workspace_name=state.get("workspace_name"),
            user_input=state.get("user_input"),
            existing_draft=current_connection_draft or None,
        )
        if planner_result.next_step == "confirm" and not planner_result.missing:
            return {
                "node": "connection_confirm",
                "connection_draft": planner_result.draft,
                "messages": merge_messages(state, planner_result.message),
                "available_actions": connection_confirm_actions(planner_result.draft),
            }
        if planner_result.next_step == "show_form":
            return {
                "connection_draft": planner_result.draft,
                "messages": merge_messages(state, planner_result.message),
                "available_actions": setup_intro_actions(planner_result.draft),
            }
        if planner_result.next_step == "open_chat":
            return {
                "node": "operator_ready",
                "connection_draft": planner_result.draft,
                "messages": merge_messages(state, planner_result.message),
                "available_actions": standard_workspace_actions(),
            }
        return {
            "connection_draft": planner_result.draft,
            "messages": merge_messages(state, planner_result.message),
            "available_actions": setup_chat_actions(),
        }

    return {
        "messages": merge_messages(state, "That setup action is not available here."),
        "available_actions": setup_chat_actions(),
    }


async def connection_confirm_node(state: EntryRuntimeState) -> dict[str, Any]:
    current_user = state.get("current_user")
    if current_user is None:
        return _auth_required(state)
    workspace_id = state.get("active_workspace_id")
    if not workspace_id:
        return {
            "node": "workspace_job",
            "messages": merge_messages(state, "I lost the workspace context. Enter the workspace name again."),
        }

    selected_action_id = _selected_action_id(state)
    if selected_action_id == RouteDeckActionIds.NAV_CANCEL:
        return {
            "node": "operator_ready",
            "messages": merge_messages(state, "Canceled API setup. You can continue in chat or reopen setup from Connections."),
            "available_actions": standard_workspace_actions(),
        }
    if selected_action_id == RouteDeckActionIds.NAV_BACK:
        return {
            "node": "setup_intro",
            "messages": merge_messages(state, "Back to API setup details. Edit the connection or skip setup."),
            "available_actions": setup_intro_actions(state.get("connection_draft") or {}),
        }
    if selected_action_id == RouteDeckActionIds.SETUP_OPEN_CHAT:
        return {
            "node": "operator_ready",
            "messages": merge_messages(state, "Continuing without API setup for now. API setup remains available in Connections."),
            "available_actions": standard_workspace_actions(),
        }
    if selected_action_id == RouteDeckActionIds.SETUP_REST_CONFIGURE:
        draft, error = _validate_connection_payload(_action_payload(state))
        if error:
            return {
                "messages": merge_messages(state, error),
                "available_actions": connection_confirm_actions(state.get("connection_draft") or {}),
            }
        assert draft is not None
        return {
            "connection_draft": draft,
            "messages": merge_messages(state, f"Updated setup to **{draft['name']}**. Activate it now?"),
            "available_actions": connection_confirm_actions(draft),
        }
    if selected_action_id != RouteDeckActionIds.SETUP_CONNECTION_ACTIVATE:
        draft = state.get("connection_draft") or {}
        return {
            "messages": merge_messages(state, "Activate the API when the details look right, or edit the setup."),
            "available_actions": connection_confirm_actions(draft),
        }

    draft = state.get("connection_draft") or {}
    if not draft:
        return {
            "node": "setup_intro",
            "messages": merge_messages(state, "I lost the API setup draft. Send the details again."),
            "available_actions": setup_intro_actions(),
        }

    connection = await _create_connection_from_draft(state, workspace_id=workspace_id, draft=draft)
    service = ActivationService()
    final_event: dict[str, Any] | None = None
    async for event in service.activate(
        connection_id=connection.id,
        workspace_id=workspace_id,
        session=state["runtime"].db,
    ):
        final_event = event
        await state["runtime"].emit(
            "setup_step",
            {
                "type": "setup_step",
                "stage_id": "connection_confirm",
                "connection_id": str(connection.id),
                **event,
            },
        )

    if not final_event or final_event.get("type") == "error":
        return {
            "active_connection_id": connection.id,
            "messages": merge_messages(
                state,
                f"Activation is blocked: {(final_event or {}).get('message', 'unknown error')}",
            ),
            "available_actions": connection_confirm_actions(draft),
        }

    return {
        "node": "operator_ready",
        "active_connection_id": connection.id,
        "messages": merge_messages(
            state,
            f"Activated **{connection.name}** with {final_event.get('tools_count', 0)} callable tools. Opening the operator now.",
        ),
        "available_actions": standard_workspace_actions(),
    }


async def _create_connection_from_draft(
    state: EntryRuntimeState,
    *,
    workspace_id,
    draft: dict[str, Any],
) -> Connection:
    db = state["runtime"].db
    connection = Connection(
        workspace_id=workspace_id,
        name=draft["name"],
        type=ConnectionType.rest_api,
        provider="rest_api",
        config={
            "base_url": draft["base_url"],
            "spec_url": draft["spec_url"],
            "auth_type": draft["auth_type"],
        },
        auth_type=AuthType(draft["auth_type"]),
    )
    db.add(connection)
    await db.flush()

    if draft.get("credential_value"):
        db.add(
            EncryptedCredential(
                connection_id=connection.id,
                credential_type="credential_value",
                encrypted_value=encrypt_value(draft["credential_value"]),
                metadata_={
                    key: value
                    for key, value in {
                        "header_name": draft.get("header_name"),
                        "query_param_name": draft.get("query_param_name"),
                    }.items()
                    if value
                },
            )
        )
    db.add(ConnectionActivationState(connection_id=connection.id, workspace_id=workspace_id))
    await db.flush()
    return connection
