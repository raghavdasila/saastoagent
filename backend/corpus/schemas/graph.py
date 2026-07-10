from __future__ import annotations

import uuid
from typing import Any, Literal

from pydantic import BaseModel, Field
from routedeck_core import (
    RouteDeckActionCard,
    RouteDeckContextLens,
    RouteDeckGraphManifest,
    RouteDeckGraphMessage,
    RouteDeckGraphNavigationLocation,
    RouteDeckGraphRequest,
    RouteDeckGraphResponse,
    RouteDeckGraphState,
    RouteDeckProjection,
    RouteDeckRuntimeSnapshot,
    RouteDeckSurface,
    RouteDeckUIArtifact,
)
from backend.core.schemas.saas_agent import SaaSAgentRead


class CorpusGraphNavigationLocation(RouteDeckGraphNavigationLocation):
    pass


class CorpusGraphState(RouteDeckGraphState):
    active_saas_agent_id: uuid.UUID | None = None
    active_connection_id: uuid.UUID | None = None
    pending_trace_id: uuid.UUID | None = None
    navigation_back_stack: list[CorpusGraphNavigationLocation] = Field(default_factory=list)
    navigation_forward_stack: list[CorpusGraphNavigationLocation] = Field(default_factory=list)


class CorpusGraphRequest(RouteDeckGraphRequest):
    state: CorpusGraphState | None = None
    saas_agent_id: uuid.UUID | None = None


class CorpusRouterDecision(BaseModel):
    intent: Literal["action", "clarify", "no_match"] = "clarify"
    action_id: str | None = Field(default=None, max_length=160)
    node_id: str | None = Field(default=None, max_length=120)
    slots: dict[str, Any] = Field(default_factory=dict)
    confidence: float = Field(default=0.0, ge=0.0, le=1.0)
    clarification: str | None = Field(default=None, max_length=1_000)
    provider: str = "disabled"
    model: str | None = None


class CorpusContextLens(RouteDeckContextLens):
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


class CorpusGraphResponse(RouteDeckGraphResponse):
    state: CorpusGraphState
    graph_manifest: RouteDeckGraphManifest
    route_deck_snapshot: RouteDeckRuntimeSnapshot
    context_lens: CorpusContextLens
    available_actions: list[RouteDeckActionCard] = Field(default_factory=list)
    persistent_actions: list[RouteDeckActionCard] = Field(default_factory=list)
    ui_artifacts: list[RouteDeckUIArtifact] = Field(default_factory=list)
    messages: list[RouteDeckGraphMessage] = Field(default_factory=list)
    saas_agents: list[SaaSAgentRead] = Field(default_factory=list)


class CorpusGraphTurnResponse(CorpusGraphResponse):
    turn_type: Literal["snapshot", "action", "turn"] = "turn"


class CorpusSurface(RouteDeckSurface):
    pass


class CorpusProposal(BaseModel):
    operation_id: str
    label: str
    description: str | None = None
    args: dict[str, Any] = Field(default_factory=dict)
    execution_mode: str = "review"
    safety_class: str | None = None
    input_schema: dict[str, Any] = Field(default_factory=dict)
    target_node: str | None = None


class CorpusActionRequest(BaseModel):
    state: CorpusGraphState | None = None
    node_id: str | None = Field(default=None, max_length=120)
    saas_agent_id: uuid.UUID | None = None
    operation_id: str = Field(max_length=160)
    args: dict[str, Any] = Field(default_factory=dict)
    projection_version: int | None = Field(default=None, ge=1)


class CorpusActionResponse(BaseModel):
    state: CorpusGraphState
    projection: RouteDeckProjection
    active_surface: CorpusSurface | None = None
    messages: list[RouteDeckGraphMessage] = Field(default_factory=list)
    replace_path: str | None = None


class CorpusStateResponse(BaseModel):
    state: CorpusGraphState
    projection: RouteDeckProjection
    replace_path: str | None = None


class CorpusDiagnosticsSnapshot(BaseModel):
    graph_manifest: dict[str, Any] = Field(default_factory=dict)
    runtime_snapshot: dict[str, Any] = Field(default_factory=dict)
    introspection: dict[str, Any] = Field(default_factory=dict)
    projection: RouteDeckProjection
