from __future__ import annotations

import uuid
from typing import Any, Literal

from pydantic import BaseModel, Field

from .entry import (
    EntryActionCard,
    EntryGraphManifest,
    EntryGraphMessage,
    EntryRouteDeckRuntimeSnapshot,
    EntryUIArtifact,
)
from .saas_agent import SaaSAgentRead


class AppGraphState(BaseModel):
    node: str = "home"
    active_saas_agent_id: uuid.UUID | None = None
    active_connection_id: uuid.UUID | None = None
    pending_trace_id: uuid.UUID | None = None
    graph_context: dict[str, Any] = Field(default_factory=dict)
    executed_nodes: list[str] = Field(default_factory=list)


class AppGraphRequest(BaseModel):
    state: AppGraphState | None = None
    node_id: str | None = Field(default=None, max_length=120)
    saas_agent_id: uuid.UUID | None = None
    selected_action_id: str | None = Field(default=None, max_length=160)
    action_payload: dict[str, Any] = Field(default_factory=dict)
    user_input: str | None = Field(default=None, max_length=8_000)


class AppGraphRouterDecision(BaseModel):
    intent: Literal["action", "clarify", "no_match"] = "clarify"
    action_id: str | None = Field(default=None, max_length=160)
    node_id: str | None = Field(default=None, max_length=120)
    slots: dict[str, Any] = Field(default_factory=dict)
    confidence: float = Field(default=0.0, ge=0.0, le=1.0)
    clarification: str | None = Field(default=None, max_length=1_000)
    provider: str = "disabled"
    model: str | None = None


class AppGraphContextLens(BaseModel):
    selected_saas_agent_id: uuid.UUID | None = None
    selected_saas_agent_name: str | None = None
    selected_saas_agent_slug: str | None = None
    current_node: str
    working_on: str
    connection_count: int = 0
    ready_connection_count: int = 0
    action_count: int = 0
    tool_count: int = 0
    pending_trace_id: uuid.UUID | None = None
    pending_trace_status: str | None = None


class AppGraphSurface(BaseModel):
    id: str
    renderer: str
    title: str
    payload: dict[str, Any] = Field(default_factory=dict)


class AppGraphResponse(BaseModel):
    state: AppGraphState
    graph_version: str
    graph_manifest: EntryGraphManifest
    route_deck_snapshot: EntryRouteDeckRuntimeSnapshot
    context_lens: AppGraphContextLens
    active_surface: AppGraphSurface
    available_actions: list[EntryActionCard] = Field(default_factory=list)
    persistent_actions: list[EntryActionCard] = Field(default_factory=list)
    ui_artifacts: list[EntryUIArtifact] = Field(default_factory=list)
    evidence: list[dict[str, Any]] = Field(default_factory=list)
    diagnostics: dict[str, Any] = Field(default_factory=dict)
    messages: list[EntryGraphMessage] = Field(default_factory=list)
    saas_agents: list[SaaSAgentRead] = Field(default_factory=list)
    replace_path: str | None = None


class AppGraphTurnResponse(AppGraphResponse):
    turn_type: Literal["snapshot", "action", "turn"] = "turn"
