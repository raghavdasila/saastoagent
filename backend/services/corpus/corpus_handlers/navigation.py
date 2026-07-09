from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from backend.core.schemas import CorpusGraphState, EntryGraphMessage
from backend.services.corpus.corpus_routedeck_navigation import CorpusRouteDeckNavigation
from backend.services.corpus.manifest import CorpusActionIds, CorpusNodeIds

from .types import CorpusActionContext, CorpusActionResult


def build_navigation_handlers(navigation: CorpusRouteDeckNavigation):
    async def route_back(state: CorpusGraphState, payload: Mapping[str, Any], context: CorpusActionContext) -> CorpusActionResult:
        navigation.move_back(state)
        return CorpusActionResult(state=state)

    async def route_forward(state: CorpusGraphState, payload: Mapping[str, Any], context: CorpusActionContext) -> CorpusActionResult:
        navigation.move_forward(state)
        return CorpusActionResult(state=state)

    async def route_cancel(state: CorpusGraphState, payload: Mapping[str, Any], context: CorpusActionContext) -> CorpusActionResult:
        navigation.cancel(state)
        return CorpusActionResult(state=state)

    async def route_open_node(state: CorpusGraphState, payload: Mapping[str, Any], context: CorpusActionContext) -> CorpusActionResult:
        navigation.open_node(state, payload)
        return CorpusActionResult(state=state)

    async def route_switch_surface(state: CorpusGraphState, payload: Mapping[str, Any], context: CorpusActionContext) -> CorpusActionResult:
        navigation.switch_surface(state, payload)
        return CorpusActionResult(state=state)

    async def navigate_home(state: CorpusGraphState, payload: Mapping[str, Any], context: CorpusActionContext) -> CorpusActionResult:
        state.node = CorpusNodeIds.HOME
        return CorpusActionResult(state=state)

    async def recovery_home(state: CorpusGraphState, payload: Mapping[str, Any], context: CorpusActionContext) -> CorpusActionResult:
        return await navigate_home(state, payload, context)

    async def auth_sign_in(state: CorpusGraphState, payload: Mapping[str, Any], context: CorpusActionContext) -> CorpusActionResult:
        state.node = CorpusNodeIds.AUTH_SIGN_IN
        return CorpusActionResult(state=state, messages=[EntryGraphMessage(content="Sign in, and I will keep the current work ready for you.")])

    async def auth_register(state: CorpusGraphState, payload: Mapping[str, Any], context: CorpusActionContext) -> CorpusActionResult:
        state.node = CorpusNodeIds.AUTH_REGISTER
        return CorpusActionResult(state=state, messages=[EntryGraphMessage(content="Create your account, and I will continue from here.")])

    return {
        CorpusActionIds.ROUTE_BACK: route_back,
        CorpusActionIds.ROUTE_FORWARD: route_forward,
        CorpusActionIds.ROUTE_CANCEL: route_cancel,
        CorpusActionIds.ROUTE_OPEN_NODE: route_open_node,
        CorpusActionIds.ROUTE_SWITCH_SURFACE: route_switch_surface,
        CorpusActionIds.HOME: navigate_home,
        CorpusActionIds.RECOVERY_HOME: recovery_home,
        CorpusActionIds.AUTH_SIGN_IN: auth_sign_in,
        CorpusActionIds.AUTH_REGISTER: auth_register,
    }
