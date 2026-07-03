from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from backend.core.schemas import AppGraphState, EntryGraphMessage
from backend.services.app_graph.corpus_routedeck_navigation import CorpusRouteDeckNavigation
from backend.services.app_graph.manifest import AppActionIds, AppNodeIds

from .types import CorpusActionContext, CorpusActionResult


def build_navigation_handlers(navigation: CorpusRouteDeckNavigation):
    async def route_back(state: AppGraphState, payload: Mapping[str, Any], context: CorpusActionContext) -> CorpusActionResult:
        navigation.move_back(state)
        return CorpusActionResult(state=state)

    async def route_forward(state: AppGraphState, payload: Mapping[str, Any], context: CorpusActionContext) -> CorpusActionResult:
        navigation.move_forward(state)
        return CorpusActionResult(state=state)

    async def route_cancel(state: AppGraphState, payload: Mapping[str, Any], context: CorpusActionContext) -> CorpusActionResult:
        navigation.cancel(state)
        return CorpusActionResult(state=state)

    async def route_open_node(state: AppGraphState, payload: Mapping[str, Any], context: CorpusActionContext) -> CorpusActionResult:
        navigation.open_node(state, payload)
        return CorpusActionResult(state=state)

    async def route_switch_surface(state: AppGraphState, payload: Mapping[str, Any], context: CorpusActionContext) -> CorpusActionResult:
        navigation.switch_surface(state, payload)
        return CorpusActionResult(state=state)

    async def navigate_home(state: AppGraphState, payload: Mapping[str, Any], context: CorpusActionContext) -> CorpusActionResult:
        state.node = AppNodeIds.HOME
        return CorpusActionResult(state=state)

    async def recovery_home(state: AppGraphState, payload: Mapping[str, Any], context: CorpusActionContext) -> CorpusActionResult:
        return await navigate_home(state, payload, context)

    async def auth_sign_in(state: AppGraphState, payload: Mapping[str, Any], context: CorpusActionContext) -> CorpusActionResult:
        state.node = AppNodeIds.AUTH_SIGN_IN
        return CorpusActionResult(state=state, messages=[EntryGraphMessage(content="Sign in, and I will keep the current work ready for you.")])

    async def auth_register(state: AppGraphState, payload: Mapping[str, Any], context: CorpusActionContext) -> CorpusActionResult:
        state.node = AppNodeIds.AUTH_REGISTER
        return CorpusActionResult(state=state, messages=[EntryGraphMessage(content="Create your account, and I will continue from here.")])

    return {
        AppActionIds.ROUTE_BACK: route_back,
        AppActionIds.ROUTE_FORWARD: route_forward,
        AppActionIds.ROUTE_CANCEL: route_cancel,
        AppActionIds.ROUTE_OPEN_NODE: route_open_node,
        AppActionIds.ROUTE_SWITCH_SURFACE: route_switch_surface,
        AppActionIds.HOME: navigate_home,
        AppActionIds.RECOVERY_HOME: recovery_home,
        AppActionIds.AUTH_SIGN_IN: auth_sign_in,
        AppActionIds.AUTH_REGISTER: auth_register,
    }
