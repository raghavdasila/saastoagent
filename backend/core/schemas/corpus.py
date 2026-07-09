from __future__ import annotations

import uuid
from typing import Any, Literal

from pydantic import BaseModel, Field
from routedeck_core import (
    RouteDeckActionCard,
    RouteDeckActionField,
    RouteDeckContextLens,
    RouteDeckGraphManifest,
    RouteDeckGraphManifestAction,
    RouteDeckGraphManifestEdge,
    RouteDeckGraphManifestNode,
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

from .auth import UserRead
from .saas_agent import SaaSAgentRead

EntryGraphNode = Literal[
    "bootstrap",
    "intent",
    "display_name",
    "email",
    "password",
    "saas_agent_select",
    "saas_agent_job",
    "saas_agent_confirm",
    "setup_intro",
    "connection_confirm",
    "operator_ready",
]
AuthIntent = Literal["login", "register"]
EntryActionEmphasis = Literal["primary", "secondary"]
EntryActionKind = Literal["button", "chip", "form", "nav", "summary"]
EntryActionCategory = Literal["auth", "setup", "navigation", "execution", "feedback", "learning", "deployment"]
EntryActionPlacement = Literal["next_best", "rail", "inline", "evidence"]
EntryActionFieldType = Literal["text", "password", "select", "url", "textarea"]
EntryUIArtifactKind = Literal["widget", "markup"]
EntryUIArtifactSurface = Literal["inline", "canvas", "both"]


class EntryGraphState(BaseModel):
    node: EntryGraphNode
    intent: AuthIntent | None = None
    display_name: str = ""
    email: str = ""
    saas_agent_name: str = ""
    saas_agent_slug: str = ""
    active_saas_agent_id: uuid.UUID | None = None
    active_connection_id: uuid.UUID | None = None
    connection_draft: dict[str, Any] = Field(default_factory=dict)
    entry_draft: dict[str, Any] = Field(default_factory=dict)
    platform_question_context: list[dict[str, Any]] = Field(default_factory=list)
    canvas_artifacts: list[dict[str, Any]] = Field(default_factory=list)
    follow_up_context: dict[str, Any] = Field(default_factory=dict)


class EntryGraphTurnRequest(BaseModel):
    session_id: uuid.UUID | None = None
    state: EntryGraphState | None = None
    user_input: str | None = Field(default=None, max_length=4_000)
    initial_intent: AuthIntent | None = None
    selected_action_id: str | None = Field(default=None, max_length=120)
    action_payload: dict[str, Any] | None = None


class EntryGraphMessage(RouteDeckGraphMessage):
    pass


class EntryGraphSession(BaseModel):
    access_token: str
    token_type: Literal["bearer"] = "bearer"
    user: UserRead


class EntryActionField(RouteDeckActionField):
    field_type: EntryActionFieldType = "text"


class EntryActionCard(RouteDeckActionCard):
    emphasis: EntryActionEmphasis = "secondary"
    kind: EntryActionKind = "button"
    category: EntryActionCategory | None = None
    placement: EntryActionPlacement | None = None
    fields: list[EntryActionField] = Field(default_factory=list)


class EntryUIArtifact(RouteDeckUIArtifact):
    kind: EntryUIArtifactKind
    surface: EntryUIArtifactSurface = "inline"


class EntryGraphManifestNode(RouteDeckGraphManifestNode):
    pass


class EntryGraphManifestEdge(RouteDeckGraphManifestEdge):
    pass


class EntryGraphManifestAction(RouteDeckGraphManifestAction):
    emphasis: EntryActionEmphasis = "secondary"
    kind: EntryActionKind = "button"
    category: EntryActionCategory | None = None
    placement: EntryActionPlacement | None = None
    fields: list[EntryActionField] = Field(default_factory=list)


class EntryRouteDeckRuntimeSnapshot(RouteDeckRuntimeSnapshot):
    valid_actions: list[EntryActionCard] = Field(default_factory=list)


class EntryGraphManifest(RouteDeckGraphManifest):
    nodes: list[EntryGraphManifestNode] = Field(default_factory=list)
    edges: list[EntryGraphManifestEdge] = Field(default_factory=list)
    actions: list[EntryGraphManifestAction] = Field(default_factory=list)


class EntryGraphTurnResponse(BaseModel):
    state: EntryGraphState
    session_id: uuid.UUID | None = None
    run_id: uuid.UUID | None = None
    graph_version: str | None = None
    graph_manifest: EntryGraphManifest | None = None
    messages: list[EntryGraphMessage] = Field(default_factory=list)
    session: EntryGraphSession | None = None
    saas_agents: list[SaaSAgentRead] = Field(default_factory=list)
    available_actions: list[EntryActionCard] = Field(default_factory=list)
    persistent_actions: list[EntryActionCard] = Field(default_factory=list)
    ui_artifacts: list[EntryUIArtifact] = Field(default_factory=list)
    route_deck_snapshot: EntryRouteDeckRuntimeSnapshot | None = None
    replace_path: str | None = None


class EntryPersistentActionsResponse(BaseModel):
    persistent_actions: list[EntryActionCard] = Field(default_factory=list)


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
    graph_manifest: EntryGraphManifest
    route_deck_snapshot: EntryRouteDeckRuntimeSnapshot
    context_lens: CorpusContextLens
    available_actions: list[EntryActionCard] = Field(default_factory=list)
    persistent_actions: list[EntryActionCard] = Field(default_factory=list)
    ui_artifacts: list[EntryUIArtifact] = Field(default_factory=list)
    messages: list[EntryGraphMessage] = Field(default_factory=list)
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
    messages: list[EntryGraphMessage] = Field(default_factory=list)
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
