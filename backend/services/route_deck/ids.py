from __future__ import annotations


class RouteDeckNodeIds:
    BOOTSTRAP = "bootstrap"
    INTENT = "intent"
    DISPLAY_NAME = "display_name"
    EMAIL = "email"
    PASSWORD = "password"
    SAAS_AGENT_SELECT = "saas_agent_select"
    SAAS_AGENT_JOB = "saas_agent_job"
    SAAS_AGENT_CONFIRM = "saas_agent_confirm"
    SETUP_INTRO = "setup_intro"
    CONNECTION_CONFIRM = "connection_confirm"
    OPERATOR_READY = "operator_ready"


class RouteDeckActionIds:
    NAV_BACK = "nav.back"
    NAV_CANCEL = "nav.cancel"
    ENTRY_LEARN_PLATFORM = "entry.learn.platform"
    ENTRY_LEARN_SETUP = "entry.learn.setup"
    ENTRY_FOLLOW_UP_PATTERN = "entry.follow_up:*"
    ENTRY_FOLLOW_UP_PREFIX = "entry.follow_up:"
    INTENT_SIGN_IN = "intent.sign_in"
    INTENT_REGISTER = "intent.register"
    DISPLAY_NAME_SKIP = "display_name.skip"
    SAAS_AGENT_SELECT_OPEN_PATTERN = "saas_agent_select.open:*"
    SAAS_AGENT_SELECT_OPEN_PREFIX = "saas_agent_select.open:"
    SAAS_AGENT_CONFIRM_LAUNCH = "saas_agent_confirm.launch"
    SETUP_REST_START = "setup.rest.start"
    SETUP_OPEN_CHAT = "setup.open_chat"
    SETUP_REST_CONFIGURE = "setup.rest.configure"
    SETUP_CONNECTION_ACTIVATE = "setup.connection.activate"


def follow_up_action_id(index: int) -> str:
    return f"{RouteDeckActionIds.ENTRY_FOLLOW_UP_PREFIX}{index}"


def saas_agent_select_open_action_id(index: int) -> str:
    return f"{RouteDeckActionIds.SAAS_AGENT_SELECT_OPEN_PREFIX}{index}"


def is_follow_up_action(action_id: str | None) -> bool:
    return bool(action_id and action_id.startswith(RouteDeckActionIds.ENTRY_FOLLOW_UP_PREFIX))


def is_saas_agent_select_open_action(action_id: str | None) -> bool:
    return bool(action_id and action_id.startswith(RouteDeckActionIds.SAAS_AGENT_SELECT_OPEN_PREFIX))
