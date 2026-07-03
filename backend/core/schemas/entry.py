import uuid
from typing import Any, Literal

from pydantic import BaseModel, Field
from routedeck_core import (
    RouteDeckActionCard,
    RouteDeckActionField,
    RouteDeckGraphManifest,
    RouteDeckGraphManifestAction,
    RouteDeckGraphManifestEdge,
    RouteDeckGraphManifestNode,
    RouteDeckGraphMessage,
    RouteDeckRuntimeSnapshot,
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
