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
    SaaSAgent,
    SaaSAgentMember,
    SaaSAgentRole,
)
from backend.core.schemas import SaaSAgentRead
from backend.core.tenancy import create_tenant_schema
from backend.services.discovery.activation import ActivationService
from backend.services.route_deck import RouteDeckActionIds
from backend.services.route_deck.ids import is_saas_agent_select_open_action

from .graph_runtime import EntryRuntimeState, merge_messages
from .ui_actions import (
    connection_confirm_actions,
    display_name_actions,
    entry_assistant_actions,
    setup_chat_actions,
    setup_intro_actions,
    standard_saas_agent_actions,
    saas_agent_confirm_actions,
    saas_agent_select_actions,
)
from .setup_planner import plan_setup_turn

SAAS_AGENT_SUFFIX = "SaaS Agent"


def _to_slug(value: str) -> str:
    return re.sub(
        r"-+",
        "-",
        re.sub(r"\s+", "-", re.sub(r"[^a-z0-9\s-]", "", value.lower()).strip()),
    )


def _normalize_saas_agent_name(value: str) -> str:
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
        return f"SaaS Operations {SAAS_AGENT_SUFFIX}"

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
    if not name.lower().endswith(("saas agent", "operator")):
        name = f"{name} {SAAS_AGENT_SUFFIX}"
    return name


def _saas_agent_list_text(saas_agents: list[SaaSAgentRead]) -> str:
    return "\n".join(
        f"{index}. {saas_agent.name}  /{saas_agent.slug}"
        for index, saas_agent in enumerate(saas_agents, 1)
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
        "saas_agent_name": "",
        "saas_agent_slug": "",
        "active_connection_id": None,
        "connection_draft": {},
        "messages": merge_messages(
            state,
            "Your authentication context is missing. Say `sign in` or `create account` to continue.",
        ),
    }


def _clear_saas_agent_draft(state: EntryRuntimeState, message: str) -> dict[str, Any]:
    return {
        "node": "intent",
        "saas_agent_name": "",
        "saas_agent_slug": "",
        "active_saas_agent_id": None,
        "messages": merge_messages(state, message),
        "available_actions": entry_assistant_actions(),
    }


async def list_saas_agents(state: EntryRuntimeState, user_id) -> list[SaaSAgentRead]:
    db = state["runtime"].db
    stmt = (
        select(SaaSAgent, SaaSAgentMember.role)
        .join(SaaSAgentMember, SaaSAgentMember.saas_agent_id == SaaSAgent.id)
        .where(SaaSAgentMember.user_id == user_id)
        .order_by(SaaSAgent.created_at.desc())
    )
    rows = (await db.execute(stmt)).all()
    return [
        SaaSAgentRead(
            id=saas_agent.id,
            name=saas_agent.name,
            slug=saas_agent.slug,
            created_by=saas_agent.created_by,
            created_at=saas_agent.created_at,
            role=role.value,
        )
        for saas_agent, role in rows
    ]


async def create_saas_agent(
    state: EntryRuntimeState,
    *,
    current_user: User,
    name: str,
    slug: str,
) -> SaaSAgentRead:
    db = state["runtime"].db
    existing = await db.execute(select(SaaSAgent).where(SaaSAgent.slug == slug))
    if existing.scalar_one_or_none():
        raise ValueError("SaaS Agent slug already taken")

    saas_agent = SaaSAgent(
        name=name,
        slug=slug,
        created_by=current_user.id,
    )
    db.add(saas_agent)
    await db.flush()

    db.add(
        SaaSAgentMember(
            user_id=current_user.id,
            saas_agent_id=saas_agent.id,
            role=SaaSAgentRole.owner,
        )
    )
    await db.flush()
    await create_tenant_schema(saas_agent.id)

    return SaaSAgentRead(
        id=saas_agent.id,
        name=saas_agent.name,
        slug=saas_agent.slug,
        created_by=saas_agent.created_by,
        created_at=saas_agent.created_at,
        role=SaaSAgentRole.owner.value,
    )


def _valid_slug(value: str) -> bool:
    return bool(re.fullmatch(r"[a-z0-9][a-z0-9-]*", value.strip()))


async def _ready_connection_count(state: EntryRuntimeState, saas_agent_id) -> int:
    db = state["runtime"].db
    return int(
        (
            await db.execute(
                select(func.count(Connection.id))
                .join(ConnectionActivationState, ConnectionActivationState.connection_id == Connection.id, isouter=True)
                .where(
                    Connection.saas_agent_id == saas_agent_id,
                    ConnectionActivationState.overall_status == "ready",
                )
            )
        ).scalar_one()
    )


async def _open_saas_agent_transition(
    state: EntryRuntimeState,
    *,
    saas_agent: SaaSAgentRead,
    saas_agents: list[SaaSAgentRead] | None = None,
    messages: list | None = None,
) -> dict[str, Any]:
    base_messages = messages if messages is not None else state.get("messages", [])
    entry_draft = state.get("entry_draft") or {}
    carried_connection_draft = state.get("connection_draft") or entry_draft.get("api_draft") or {}
    if await _ready_connection_count(state, saas_agent.id) > 0:
        return {
            "node": "operator_ready",
            "active_saas_agent_id": saas_agent.id,
            "messages": merge_messages({**state, "messages": base_messages}, f"Opening **{saas_agent.name}** now."),
            "saas_agents": saas_agents or [saas_agent],
            "replace_path": f"/agents/{saas_agent.id}",
            "available_actions": standard_saas_agent_actions(),
        }

    return {
        "node": "operator_ready",
        "active_saas_agent_id": saas_agent.id,
        "connection_draft": carried_connection_draft,
        "messages": merge_messages(
            {**state, "messages": base_messages},
            f"**{saas_agent.name}** is ready. I kept your API draft; Connections can finish the API setup when you need it."
            if carried_connection_draft
            else f"**{saas_agent.name}** is ready. You can chat here now, and use Connections when you want to add the API.",
        ),
        "saas_agents": saas_agents or [saas_agent],
        "replace_path": f"/agents/{saas_agent.id}",
        "available_actions": standard_saas_agent_actions(),
    }


async def advance_authenticated_user(
    state: EntryRuntimeState,
    *,
    current_user: User,
    extra_messages: list[str] | None = None,
) -> dict[str, Any]:
    saas_agents = await list_saas_agents(state, current_user.id)
    messages = merge_messages(state, *(extra_messages or []))

    if len(saas_agents) == 1:
        saas_agent = saas_agents[0]
        return await _open_saas_agent_transition(
            state,
            saas_agent=saas_agent,
            saas_agents=saas_agents,
            messages=messages,
        )

    if len(saas_agents) > 1:
        return {
            "node": "saas_agent_select",
            "active_saas_agent_id": None,
            "messages": merge_messages(
                {**state, "messages": messages},
                "Which SaaS Agent do you want to open?\n\n"
                f"{_saas_agent_list_text(saas_agents)}\n\n"
                "Type the number to open one, or enter a new SaaS Agent name.",
            ),
            "saas_agents": saas_agents,
            "available_actions": saas_agent_select_actions(saas_agents),
            "replace_path": None,
        }

    entry_draft = state.get("entry_draft") or {}
    draft_saas_agent_name = entry_draft.get("saas_agent_name") or entry_draft.get("saas_agent_job")
    if draft_saas_agent_name:
        saas_agent_name = _normalize_saas_agent_name(str(draft_saas_agent_name))
        saas_agent_slug = _to_slug(saas_agent_name)
        return {
            "node": "saas_agent_confirm",
            "active_saas_agent_id": None,
            "saas_agent_name": saas_agent_name,
            "saas_agent_slug": saas_agent_slug,
            "messages": merge_messages(
                {**state, "messages": messages},
                f"I kept your draft. I can create **{saas_agent_name}** at /{saas_agent_slug}. Type `launch` to confirm, or reply with a different name.",
            ),
            "saas_agents": saas_agents,
            "replace_path": None,
            "available_actions": saas_agent_confirm_actions(saas_agent_name, saas_agent_slug),
        }

    return {
        "node": "saas_agent_job",
        "active_saas_agent_id": None,
        "messages": merge_messages(
            {**state, "messages": messages},
            "No saas_agents yet. What should this SaaS Agent be called?",
        ),
        "saas_agents": saas_agents,
        "replace_path": None,
    }


async def saas_agent_select_node(state: EntryRuntimeState) -> dict[str, Any]:
    current_user = state.get("current_user")
    if current_user is None:
        return _auth_required(state)

    selected_action_id = _selected_action_id(state)
    if selected_action_id in (RouteDeckActionIds.NAV_BACK, RouteDeckActionIds.NAV_CANCEL):
        return _clear_saas_agent_draft(
            state,
            "Canceled SaaS Agent selection. You can ask a question, create a SaaS Agent, or connect an API later.",
        )

    saas_agents = await list_saas_agents(state, current_user.id)
    if is_saas_agent_select_open_action(selected_action_id):
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
        if 1 <= selection <= len(saas_agents):
            saas_agent = saas_agents[selection - 1]
            return await _open_saas_agent_transition(
                state,
                saas_agent=saas_agent,
                saas_agents=saas_agents,
                messages=merge_messages(state, f"Opening **{saas_agent.name}**."),
            )
        return {
            "messages": merge_messages(
                state,
                f"Pick a number between 1 and {len(saas_agents)}, or enter a new SaaS Agent name.",
            ),
            "saas_agents": saas_agents,
            "available_actions": saas_agent_select_actions(saas_agents),
        }

    saas_agent_name = _normalize_saas_agent_name(value)
    if not saas_agent_name:
        return {
            "messages": merge_messages(
                state,
                "Type a number from the list to open an existing SaaS Agent, or enter a new SaaS Agent name.",
            ),
            "saas_agents": saas_agents,
            "available_actions": saas_agent_select_actions(saas_agents),
        }

    saas_agent_slug = _to_slug(saas_agent_name)
    return {
        "node": "saas_agent_confirm",
        "saas_agent_name": saas_agent_name,
        "saas_agent_slug": saas_agent_slug,
        "messages": merge_messages(
            state,
            f"I can create **{saas_agent_name}** at /{saas_agent_slug}. Type `launch` to confirm, or reply with a different name.",
        ),
        "saas_agents": saas_agents,
        "available_actions": saas_agent_confirm_actions(saas_agent_name, saas_agent_slug),
    }


async def saas_agent_job_node(state: EntryRuntimeState) -> dict[str, Any]:
    current_user = state.get("current_user")
    if current_user is None:
        return _auth_required(state)

    selected_action_id = _selected_action_id(state)
    if selected_action_id in (RouteDeckActionIds.NAV_BACK, RouteDeckActionIds.NAV_CANCEL):
        return _clear_saas_agent_draft(
            state,
            "Canceled SaaS Agent creation. You can ask a question or start SaaS Agent setup again.",
        )

    value = (state.get("user_input") or "").strip()
    saas_agent_name = _normalize_saas_agent_name(value)
    if not saas_agent_name:
        return {"messages": merge_messages(state, "I need a SaaS Agent name before I can create it.")}

    saas_agent_slug = _to_slug(saas_agent_name)
    return {
        "node": "saas_agent_confirm",
        "saas_agent_name": saas_agent_name,
        "saas_agent_slug": saas_agent_slug,
        "messages": merge_messages(
            state,
            f"I can create **{saas_agent_name}** at /{saas_agent_slug}. Type `launch` to confirm, or reply with a different name.",
        ),
        "available_actions": saas_agent_confirm_actions(saas_agent_name, saas_agent_slug),
    }


async def saas_agent_confirm_node(state: EntryRuntimeState) -> dict[str, Any]:
    current_user = state.get("current_user")
    if current_user is None:
        return _auth_required(state)

    selected_action_id = _selected_action_id(state)
    if selected_action_id == RouteDeckActionIds.NAV_CANCEL:
        return _clear_saas_agent_draft(
            state,
            "Canceled SaaS Agent creation. You can ask a question or create a different SaaS Agent.",
        )
    if selected_action_id == RouteDeckActionIds.NAV_BACK:
        saas_agents = await list_saas_agents(state, current_user.id)
        if saas_agents:
            return {
                "node": "saas_agent_select",
                "saas_agent_name": "",
                "saas_agent_slug": "",
                "messages": merge_messages(
                    state,
                    "Back to SaaS Agent selection. Pick a SaaS Agent number or enter a new SaaS Agent name.",
                ),
                "saas_agents": saas_agents,
                "available_actions": saas_agent_select_actions(saas_agents),
            }
        return {
            "node": "saas_agent_job",
            "saas_agent_name": "",
            "saas_agent_slug": "",
            "messages": merge_messages(
                state,
                "Back to SaaS Agent setup. Enter the SaaS Agent name.",
            ),
        }

    value = (state.get("user_input") or "").strip()
    if selected_action_id == RouteDeckActionIds.SAAS_AGENT_CONFIRM_LAUNCH or _wants_confirm(value):
        payload = _action_payload(state)
        payload_name = str(payload.get("name") or "").strip()
        payload_slug = str(payload.get("slug") or "").strip()
        saas_agent_name = _normalize_saas_agent_name(payload_name or state.get("saas_agent_name", ""))
        saas_agent_slug = _to_slug(payload_slug or state.get("saas_agent_slug") or saas_agent_name)
        if not saas_agent_name or not saas_agent_slug:
            return {
                "node": "saas_agent_job",
                "messages": merge_messages(
                    state,
                    "I lost the SaaS Agent name. Enter it again.",
                ),
            }
        if not _valid_slug(saas_agent_slug):
            return {
                "saas_agent_name": saas_agent_name,
                "saas_agent_slug": saas_agent_slug,
                "messages": merge_messages(
                    state,
                    "The slug needs lowercase letters, numbers, and hyphens only.",
                ),
                "available_actions": saas_agent_confirm_actions(saas_agent_name, _to_slug(saas_agent_name)),
            }

        try:
            saas_agent = await create_saas_agent(
                state,
                current_user=current_user,
                name=saas_agent_name,
                slug=saas_agent_slug,
            )
        except ValueError as exc:
            return {
                "saas_agent_name": saas_agent_name,
                "saas_agent_slug": saas_agent_slug,
                "messages": merge_messages(
                    state,
                    f"{exc}. Reply with a different name, or type `launch` to retry.",
                ),
                "available_actions": saas_agent_confirm_actions(saas_agent_name, saas_agent_slug),
            }

        transition = await _open_saas_agent_transition(
            state,
            saas_agent=saas_agent,
            saas_agents=[saas_agent],
            messages=merge_messages(state, f"Launching **{saas_agent.name}** now."),
        )
        return {
            **transition,
            "saas_agent_name": saas_agent.name,
            "saas_agent_slug": saas_agent.slug,
        }

    saas_agent_name = _normalize_saas_agent_name(value)
    if not saas_agent_name:
        return {
            "messages": merge_messages(state, "That didn't give me a valid SaaS Agent name. Try again."),
            "available_actions": saas_agent_confirm_actions(
                state.get("saas_agent_name", "your SaaS Agent"),
                state.get("saas_agent_slug", "saas-agent"),
            ),
        }

    saas_agent_slug = _to_slug(saas_agent_name)
    return {
        "saas_agent_name": saas_agent_name,
        "saas_agent_slug": saas_agent_slug,
        "messages": merge_messages(
            state,
            f"Updated to **{saas_agent_name}** at /{saas_agent_slug}. Type `launch` to confirm.",
        ),
        "available_actions": saas_agent_confirm_actions(saas_agent_name, saas_agent_slug),
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
    if not state.get("active_saas_agent_id"):
        return {
            "node": "saas_agent_job",
            "messages": merge_messages(state, "I lost the SaaS Agent context. Enter the SaaS Agent name again."),
        }

    selected_action_id = _selected_action_id(state)
    entry_draft = state.get("entry_draft") or {}
    current_connection_draft = state.get("connection_draft") or entry_draft.get("api_draft") or {}
    if selected_action_id in (RouteDeckActionIds.NAV_BACK, RouteDeckActionIds.NAV_CANCEL):
        return {
            "node": "operator_ready",
            "messages": merge_messages(state, "Canceled API setup. You can continue in chat or reopen setup from Connections."),
            "available_actions": standard_saas_agent_actions(),
        }
    if selected_action_id == RouteDeckActionIds.SETUP_OPEN_CHAT:
        return {
            "node": "operator_ready",
            "messages": merge_messages(state, "Continuing without API setup for now. API setup remains available in Connections."),
            "available_actions": standard_saas_agent_actions(),
        }
    if selected_action_id == RouteDeckActionIds.SETUP_REST_START:
        planner_result = await plan_setup_turn(
            saas_agent_name=state.get("saas_agent_name"),
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
            saas_agent_name=state.get("saas_agent_name"),
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
                "available_actions": standard_saas_agent_actions(),
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
    saas_agent_id = state.get("active_saas_agent_id")
    if not saas_agent_id:
        return {
            "node": "saas_agent_job",
            "messages": merge_messages(state, "I lost the SaaS Agent context. Enter the SaaS Agent name again."),
        }

    selected_action_id = _selected_action_id(state)
    if selected_action_id == RouteDeckActionIds.NAV_CANCEL:
        return {
            "node": "operator_ready",
            "messages": merge_messages(state, "Canceled API setup. You can continue in chat or reopen setup from Connections."),
            "available_actions": standard_saas_agent_actions(),
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
            "available_actions": standard_saas_agent_actions(),
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

    connection = await _create_connection_from_draft(state, saas_agent_id=saas_agent_id, draft=draft)
    service = ActivationService()
    final_event: dict[str, Any] | None = None
    async for event in service.activate(
        connection_id=connection.id,
        saas_agent_id=saas_agent_id,
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
        "available_actions": standard_saas_agent_actions(),
    }


async def _create_connection_from_draft(
    state: EntryRuntimeState,
    *,
    saas_agent_id,
    draft: dict[str, Any],
) -> Connection:
    db = state["runtime"].db
    connection = Connection(
        saas_agent_id=saas_agent_id,
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
    db.add(ConnectionActivationState(connection_id=connection.id, saas_agent_id=saas_agent_id))
    await db.flush()
    return connection
