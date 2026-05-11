from __future__ import annotations


class RouteDeckNodeIds:
    BOOTSTRAP = "bootstrap"
    INTENT = "intent"
    DISPLAY_NAME = "display_name"
    EMAIL = "email"
    PASSWORD = "password"
    WORKSPACE_SELECT = "workspace_select"
    WORKSPACE_JOB = "workspace_job"
    WORKSPACE_CONFIRM = "workspace_confirm"
    SETUP_INTRO = "setup_intro"
    CONNECTION_CONFIRM = "connection_confirm"
    OPERATOR_READY = "operator_ready"


class RouteDeckActionIds:
    ENTRY_LEARN_PLATFORM = "entry.learn.platform"
    ENTRY_LEARN_SETUP = "entry.learn.setup"
    ENTRY_FOLLOW_UP_PATTERN = "entry.follow_up:*"
    ENTRY_FOLLOW_UP_PREFIX = "entry.follow_up:"
    INTENT_SIGN_IN = "intent.sign_in"
    INTENT_REGISTER = "intent.register"
    DISPLAY_NAME_SKIP = "display_name.skip"
    WORKSPACE_SELECT_OPEN_PATTERN = "workspace_select.open:*"
    WORKSPACE_SELECT_OPEN_PREFIX = "workspace_select.open:"
    WORKSPACE_CONFIRM_LAUNCH = "workspace_confirm.launch"
    SETUP_REST_START = "setup.rest.start"
    SETUP_OPEN_CHAT = "setup.open_chat"
    SETUP_REST_CONFIGURE = "setup.rest.configure"
    SETUP_CONNECTION_ACTIVATE = "setup.connection.activate"


def follow_up_action_id(index: int) -> str:
    return f"{RouteDeckActionIds.ENTRY_FOLLOW_UP_PREFIX}{index}"


def workspace_select_open_action_id(index: int) -> str:
    return f"{RouteDeckActionIds.WORKSPACE_SELECT_OPEN_PREFIX}{index}"


def is_follow_up_action(action_id: str | None) -> bool:
    return bool(action_id and action_id.startswith(RouteDeckActionIds.ENTRY_FOLLOW_UP_PREFIX))


def is_workspace_select_open_action(action_id: str | None) -> bool:
    return bool(action_id and action_id.startswith(RouteDeckActionIds.WORKSPACE_SELECT_OPEN_PREFIX))
