from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from backend.core.schemas import CorpusGraphState, EntryGraphMessage
from backend.services.corpus.corpus_routedeck_navigation import CorpusRouteDeckNavigation
from routedeck_core import RouteDeckActionDispatcher, RouteDeckActionResult

from .agent import build_agent_handlers
from .connection import build_connection_handlers
from .content import build_content_handlers
from .execution import build_execution_handlers
from .learning import build_learning_handlers
from .navigation import build_navigation_handlers
from .types import CorpusActionContext


async def _default_action_handler(
    action_id: str,
    state: CorpusGraphState,
    payload: Mapping[str, Any],
    context: CorpusActionContext,
    *,
    action_targets: Mapping[str, str],
):
    state.node = action_targets[action_id]
    return RouteDeckActionResult[CorpusGraphState, EntryGraphMessage](state=state)


def build_corpus_action_dispatcher(
    *,
    navigation: CorpusRouteDeckNavigation,
    action_targets: Mapping[str, str],
) -> RouteDeckActionDispatcher[CorpusGraphState, EntryGraphMessage, CorpusActionContext]:
    handlers = {}
    handlers.update(build_navigation_handlers(navigation))
    handlers.update(build_agent_handlers())
    handlers.update(build_connection_handlers())
    handlers.update(build_execution_handlers())
    handlers.update(build_content_handlers())
    handlers.update(build_learning_handlers())

    async def default_handler(action_id: str, state: CorpusGraphState, payload: Mapping[str, Any], context: CorpusActionContext):
        return await _default_action_handler(action_id, state, payload, context, action_targets=action_targets)

    return RouteDeckActionDispatcher(handlers, default_handler=default_handler)
