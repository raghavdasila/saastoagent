from __future__ import annotations

import uuid
from typing import Any, Literal

from pydantic import BaseModel, Field
from routedeck_core import (
    RouteDeckContextLens,
    RouteDeckGraphNavigationLocation,
    RouteDeckGraphRequest,
    RouteDeckGraphResponse,
    RouteDeckGraphState,
)

from .entry import (
    EntryActionCard,
    EntryGraphManifest,
    EntryGraphMessage,
    EntryRouteDeckRuntimeSnapshot,
    EntryUIArtifact,
)
from .saas_agent import SaaSAgentRead


class AppGraphNavigationLocation(RouteDeckGraphNavigationLocation):
    pass


class AppGraphState(RouteDeckGraphState):
    active_saas_agent_id: uuid.UUID | None = None
    active_connection_id: uuid.UUID | None = None
    pending_trace_id: uuid.UUID | None = None
    navigation_back_stack: list[AppGraphNavigationLocation] = Field(default_factory=list)
    navigation_forward_stack: list[AppGraphNavigationLocation] = Field(default_factory=list)


class AppGraphRequest(RouteDeckGraphRequest):
    state: AppGraphState | None = None
    saas_agent_id: uuid.UUID | None = None


class AppGraphRouterDecision(BaseModel):
    intent: Literal["action", "clarify", "no_match"] = "clarify"
    action_id: str | None = Field(default=None, max_length=160)
    node_id: str | None = Field(default=None, max_length=120)
    slots: dict[str, Any] = Field(default_factory=dict)
    confidence: float = Field(default=0.0, ge=0.0, le=1.0)
    clarification: str | None = Field(default=None, max_length=1_000)
    provider: str = "disabled"
    model: str | None = None


class AppGraphContextLens(RouteDeckContextLens):
    selected_saas_agent_id: uuid.UUID | None = None
    selected_saas_agent_name: str | None = None
    selected_saas_agent_slug: str | None = None
    connection_count: int = 0
    ready_connection_count: int = 0
    action_count: int = 0
    tool_count: int = 0
    router_index_status: str | None = None
    router_documents_count: int = 0
    router_endpoint_count: int = 0
    router_version: str | None = None
    pending_trace_id: uuid.UUID | None = None
    pending_trace_status: str | None = None


class AppGraphResponse(RouteDeckGraphResponse):
    state: AppGraphState
    graph_manifest: EntryGraphManifest
    route_deck_snapshot: EntryRouteDeckRuntimeSnapshot
    context_lens: AppGraphContextLens
    available_actions: list[EntryActionCard] = Field(default_factory=list)
    persistent_actions: list[EntryActionCard] = Field(default_factory=list)
    ui_artifacts: list[EntryUIArtifact] = Field(default_factory=list)
    messages: list[EntryGraphMessage] = Field(default_factory=list)
    saas_agents: list[SaaSAgentRead] = Field(default_factory=list)


class AppGraphTurnResponse(AppGraphResponse):
    turn_type: Literal["snapshot", "action", "turn"] = "turn"
