from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any, cast

from fastapi_users import exceptions as fastapi_users_exceptions
from fastapi_users.db import SQLAlchemyUserDatabase

from backend.core.auth import UserManager, get_jwt_strategy
from backend.core.models import User
from backend.core.schemas import EntryGraphSession, UserCreate
from backend.services.route_deck import RouteDeckActionIds
from backend.services.route_deck.ids import follow_up_action_id, is_follow_up_action

from .entry_assistant import run_entry_assistant
from .graph_runtime import EntryRuntimeState, merge_messages, user_read
from .stage_workspace import advance_authenticated_user
from .ui_actions import display_name_actions, entry_action, entry_assistant_actions


@dataclass
class _Credentials:
    username: str
    password: str


def _is_valid_email(value: str) -> bool:
    return bool(re.match(r"^[^\s@]+@[^\s@]+\.[^\s@]+$", value.strip()))


def _detect_auth_intent(value: str) -> str | None:
    normalized = value.strip().lower()
    if not normalized:
        return None

    if re.search(r"\b(sign\s?in|log\s?in|login|access|enter)\b", normalized) and not re.search(
        r"\b(sign\s?up|register|create account|new account)\b",
        normalized,
    ):
        return "login"

    if re.search(r"\b(sign\s?up|register|create account|new account|join)\b", normalized):
        return "register"

    return None


def _wants_skip(value: str) -> bool:
    return bool(re.match(r"^(skip|none|no name|anonymous|without one)$", value.strip(), re.I))


def _user_manager(state: EntryRuntimeState) -> UserManager:
    return UserManager(SQLAlchemyUserDatabase(state["runtime"].db, User))


def _selected_action_id(state: EntryRuntimeState) -> str | None:
    value = state.get("selected_action_id")
    return value.strip() if isinstance(value, str) and value.strip() else None


def _clear_auth_fields(state: EntryRuntimeState, message: str) -> dict[str, Any]:
    return {
        "node": "intent",
        "intent": None,
        "display_name": "",
        "email": "",
        "messages": merge_messages(state, message),
        "available_actions": entry_assistant_actions(),
    }


def _start_login(state: EntryRuntimeState, message: str = "Signing you in. Give me the email for your account.") -> dict[str, Any]:
    return {
        "node": "email",
        "intent": "login",
        "display_name": "",
        "email": "",
        "messages": merge_messages(state, message),
    }


def _start_register(
    state: EntryRuntimeState,
    message: str = "Creating your account. What display name should I use? Type `skip` to leave it blank.",
) -> dict[str, Any]:
    return {
        "node": "display_name",
        "intent": "register",
        "display_name": "",
        "email": "",
        "messages": merge_messages(state, message),
        "available_actions": display_name_actions(),
    }


def _auth_navigation(state: EntryRuntimeState, stage_id: str) -> dict[str, Any] | None:
    selected_action_id = _selected_action_id(state)
    if selected_action_id == RouteDeckActionIds.NAV_CANCEL:
        return _clear_auth_fields(state, "Canceled auth. You can ask a question, sign in, or create an account.")
    if selected_action_id == RouteDeckActionIds.INTENT_SIGN_IN:
        return _start_login(state, "Switching to sign-in mode. Give me the email for your account.")
    if selected_action_id == RouteDeckActionIds.INTENT_REGISTER:
        return _start_register(
            state,
            "Switching to account creation. What display name should I use? Type `skip` to leave it blank.",
        )
    if selected_action_id == RouteDeckActionIds.NAV_BACK:
        if stage_id == "password":
            return {
                "node": "email",
                "email": "",
                "messages": merge_messages(state, "Back to email. Give me the email address to use."),
            }
        if stage_id == "email" and state.get("intent") == "register":
            return {
                "node": "display_name",
                "email": "",
                "messages": merge_messages(
                    state,
                    "Back to display name. Send a display name, or choose Skip For Now.",
                ),
                "available_actions": display_name_actions(),
            }
        return _clear_auth_fields(state, "Back to the entry step. Ask a question, sign in, or create an account.")
    return None


def _assistant_actions(follow_up_prompts: list[str]) -> list:
    if not follow_up_prompts:
        return []
    actions = entry_assistant_actions()
    existing_payloads = {
        str(action.payload.get("prompt", "")).strip().lower()
        for action in actions
        if action.payload
    }
    for index, prompt in enumerate(follow_up_prompts[:4], 1):
        normalized = prompt.strip()
        if not normalized or normalized.lower() in existing_payloads:
            continue
        auth_intent = _detect_auth_intent(normalized)
        if auth_intent == "login":
            actions.append(entry_action(RouteDeckActionIds.INTENT_SIGN_IN, "Sign In", kind="chip", emphasis="primary"))
            continue
        if auth_intent == "register":
            actions.append(entry_action(RouteDeckActionIds.INTENT_REGISTER, "Create Account", kind="chip", emphasis="primary"))
            continue
        actions.append(
            entry_action(
                follow_up_action_id(index),
                normalized[:48],
                description=normalized,
                kind="chip",
                payload={"prompt": normalized},
            )
        )
    return actions


def _assistant_state_updates(assistant_result: Any, artifacts: list[Any], question_context: list[dict[str, Any]]) -> dict[str, Any]:
    return {
        "entry_draft": assistant_result.entry_draft,
        "platform_question_context": question_context,
        "canvas_artifacts": [
            artifact.model_dump(mode="json") for artifact in artifacts if artifact.surface in ("canvas", "both")
        ],
        "follow_up_context": {"prompts": assistant_result.follow_up_prompts},
        "ui_artifacts": artifacts,
    }


async def bootstrap_node(state: EntryRuntimeState) -> dict[str, Any]:
    current_user = state.get("current_user")
    if current_user is not None:
        return await advance_authenticated_user(state, current_user=current_user)

    # Resilience: if session state was lost but the client sent a known action,
    # honour it directly rather than looping back to the intent prompt.
    selected_action_id = _selected_action_id(state)
    if selected_action_id == RouteDeckActionIds.INTENT_SIGN_IN:
        return _start_login(state)
    if selected_action_id == RouteDeckActionIds.INTENT_REGISTER:
        return _start_register(state)

    initial_intent = state.get("initial_intent")
    if initial_intent == "login":
        return {
            "node": "email",
            "intent": "login",
            "messages": merge_messages(
                state,
                "Welcome back. Give me the email address for your account.",
            ),
        }
    if initial_intent == "register":
        return {
            "node": "display_name",
            "intent": "register",
            "messages": merge_messages(
                state,
                "Let's get your account set up. What display name should go on it? Type `skip` to leave it blank.",
            ),
        }

    assistant_result, artifacts, question_context = await run_entry_assistant(
        user_input=state.get("user_input"),
        selected_action_id=selected_action_id,
        action_payload=state.get("action_payload"),
        existing_draft=state.get("entry_draft") or {},
        platform_question_context=state.get("platform_question_context") or [],
    )
    assistant_updates = _assistant_state_updates(assistant_result, artifacts, question_context)
    if assistant_result.next_step == "login":
        return {
            **assistant_updates,
            "node": "email",
            "intent": "login",
            "display_name": "",
            "messages": merge_messages(state, "Signing you in. Give me the email for your account."),
        }
    if assistant_result.next_step == "register":
        return {
            **assistant_updates,
            "node": "display_name",
            "intent": "register",
            "messages": merge_messages(
                state,
                "Creating your account. What display name should I use? Type `skip` to leave it blank.",
            ),
            "available_actions": display_name_actions(),
        }
    return {
        **assistant_updates,
        "node": "intent",
        "messages": merge_messages(state, assistant_result.message),
        "available_actions": _assistant_actions(assistant_result.follow_up_prompts),
    }


async def intent_node(state: EntryRuntimeState) -> dict[str, Any]:
    selected_action_id = _selected_action_id(state)
    if selected_action_id == RouteDeckActionIds.INTENT_SIGN_IN:
        intent = "login"
    elif selected_action_id == RouteDeckActionIds.INTENT_REGISTER:
        intent = "register"
    else:
        value = (state.get("user_input") or "").strip()
        intent = _detect_auth_intent(value)

    should_call_assistant = (
        selected_action_id in (None, RouteDeckActionIds.ENTRY_LEARN_PLATFORM, RouteDeckActionIds.ENTRY_LEARN_SETUP)
        or is_follow_up_action(selected_action_id)
    )
    assistant_updates: dict[str, Any] = {}
    if not intent and should_call_assistant:
        assistant_result, artifacts, question_context = await run_entry_assistant(
            user_input=state.get("user_input"),
            selected_action_id=selected_action_id,
            action_payload=state.get("action_payload"),
            existing_draft=state.get("entry_draft") or {},
            platform_question_context=state.get("platform_question_context") or [],
        )
        assistant_updates = _assistant_state_updates(assistant_result, artifacts, question_context)
        if assistant_result.next_step in ("login", "register"):
            intent = assistant_result.next_step
        else:
            return {
                **assistant_updates,
                "messages": merge_messages(state, assistant_result.message),
                "available_actions": _assistant_actions(assistant_result.follow_up_prompts),
            }

    if not intent:
        return {
            "messages": merge_messages(
                state,
                "I can answer questions, draft setup details, or help you sign in/create an account. What would you like to do?",
            ),
            "available_actions": entry_assistant_actions(),
        }

    if intent == "register":
        return {
            **assistant_updates,
            "node": "display_name",
            "intent": "register",
            "messages": merge_messages(
                state,
                "Creating your account. What display name should I use? Type `skip` to leave it blank.",
            ),
            "available_actions": display_name_actions(),
        }

    return {
        **assistant_updates,
        "node": "email",
        "intent": "login",
        "display_name": "",
        "messages": merge_messages(
            state,
            "Signing you in. Give me the email for your account.",
        ),
    }


async def display_name_node(state: EntryRuntimeState) -> dict[str, Any]:
    navigation = _auth_navigation(state, "display_name")
    if navigation is not None:
        return navigation

    selected_action_id = _selected_action_id(state)
    if selected_action_id == RouteDeckActionIds.DISPLAY_NAME_SKIP:
        display_name = ""
    elif selected_action_id is not None:
        return {
            "messages": merge_messages(state, "That action is no longer valid here."),
            "available_actions": display_name_actions(),
        }
    else:
        value = (state.get("user_input") or "").strip()
        intent = _detect_auth_intent(value)
        if intent == "login":
            return {
                "node": "email",
                "intent": "login",
                "display_name": "",
                "messages": merge_messages(
                    state,
                    "Switching to sign-in mode. Give me the email for your account.",
                ),
            }

        display_name = "" if _wants_skip(value) else value
    return {
        "node": "email",
        "display_name": display_name,
        "messages": merge_messages(
            state,
            f"Using **{display_name}**. Now give me the email for the new account."
            if display_name
            else "No display name. Give me the email for the new account.",
        ),
    }


async def email_node(state: EntryRuntimeState) -> dict[str, Any]:
    navigation = _auth_navigation(state, "email")
    if navigation is not None:
        return navigation

    value = (state.get("user_input") or "").strip()
    if not _is_valid_email(value):
        return {
            "messages": merge_messages(
                state,
                "That doesn't look like a valid email address. Try again with something like `you@example.com`.",
            )
        }

    return {
        "node": "password",
        "email": value,
        "messages": merge_messages(state, "Got it. Send the password â€” I'll mask it in the thread."),
    }


async def password_node(state: EntryRuntimeState) -> dict[str, Any]:
    navigation = _auth_navigation(state, "password")
    if navigation is not None:
        return navigation

    value = (state.get("user_input") or "").strip()
    if state.get("intent") == "register" and len(value) < 8:
        return {
            "messages": merge_messages(state, "Use at least 8 characters, then send it again.")
        }

    manager = _user_manager(state)

    try:
        if state.get("intent") == "register":
            current_user = await manager.create(
                UserCreate(
                    email=state.get("email", ""),
                    password=value,
                    display_name=state.get("display_name") or None,
                )
            )
            success_message = "Account created and signed in."
        else:
            current_user = await manager.authenticate(
                cast(Any, _Credentials(username=state.get("email", ""), password=value))
            )
            if current_user is None:
                return {
                    "node": "email",
                    "email": "",
                    "messages": merge_messages(
                        state,
                        "Invalid email or password. Start again from the email address.",
                    ),
                }
            if not current_user.is_active:
                return {
                    "node": "email",
                    "email": "",
                    "messages": merge_messages(state, "This account is inactive."),
                }
            success_message = "Signed in."
    except fastapi_users_exceptions.UserAlreadyExists:
        return {
            "node": "email",
            "email": "",
            "messages": merge_messages(
                state,
                "That email already has an account. Start again from the email address or say `sign in`.",
            ),
        }
    except fastapi_users_exceptions.InvalidPasswordException as exc:
        return {
            "messages": merge_messages(state, str(exc.reason))
        }

    token = await get_jwt_strategy().write_token(current_user)
    transition = await advance_authenticated_user(
        state,
        current_user=current_user,
        extra_messages=[success_message],
    )
    return {
        **transition,
        "current_user": current_user,
        "session_payload": EntryGraphSession(access_token=token, user=user_read(current_user)),
    }
