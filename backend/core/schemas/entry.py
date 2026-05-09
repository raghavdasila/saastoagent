import uuid
from typing import Any, Literal

from pydantic import BaseModel, Field

from .auth import UserRead
from .workspace import WorkspaceRead

EntryGraphNode = Literal[
    "intent",
    "display_name",
    "email",
    "password",
    "workspace_select",
    "workspace_job",
    "workspace_confirm",
    "setup_intro",
    "connection_confirm",
    "operator_ready",
]
AuthIntent = Literal["login", "register"]
EntryActionEmphasis = Literal["primary", "secondary"]
EntryActionKind = Literal["button", "chip", "form", "nav", "summary"]
EntryActionCategory = Literal["auth", "setup", "navigation", "execution", "feedback", "learning"]
EntryActionPlacement = Literal["next_best", "rail", "inline", "evidence"]
EntryActionFieldType = Literal["text", "password", "select", "url"]
EntryUIArtifactKind = Literal["widget", "markup"]
EntryUIArtifactSurface = Literal["inline", "canvas", "both"]


class EntryGraphState(BaseModel):
    node: EntryGraphNode
    intent: AuthIntent | None = None
    display_name: str = ""
    email: str = ""
    workspace_name: str = ""
    workspace_slug: str = ""
    active_workspace_id: uuid.UUID | None = None
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


class EntryGraphMessage(BaseModel):
    role: Literal["assistant"] = "assistant"
    content: str


class EntryGraphSession(BaseModel):
    access_token: str
    token_type: Literal["bearer"] = "bearer"
    user: UserRead


class EntryActionField(BaseModel):
    key: str = Field(min_length=1, max_length=120)
    label: str = Field(min_length=1, max_length=120)
    field_type: EntryActionFieldType = "text"
    required: bool = False
    placeholder: str | None = Field(default=None, max_length=240)
    default: Any = None
    options: list[dict[str, str]] | None = None
    help_text: str | None = Field(default=None, max_length=300)


class EntryActionCard(BaseModel):
    id: str = Field(min_length=1, max_length=120)
    label: str = Field(min_length=1, max_length=120)
    description: str | None = Field(default=None, max_length=240)
    emphasis: EntryActionEmphasis = "secondary"
    kind: EntryActionKind = "button"
    category: EntryActionCategory | None = None
    placement: EntryActionPlacement | None = None
    explanation: str | None = Field(default=None, max_length=500)
    recovery_prompt: str | None = Field(default=None, max_length=300)
    feedback_target: str | None = Field(default=None, max_length=160)
    fields: list[EntryActionField] = Field(default_factory=list)
    payload: dict[str, Any] = Field(default_factory=dict)
    disabled_reason: str | None = Field(default=None, max_length=240)


class EntryUIArtifact(BaseModel):
    id: str = Field(min_length=1, max_length=120)
    kind: EntryUIArtifactKind
    surface: EntryUIArtifactSurface = "inline"
    title: str | None = Field(default=None, max_length=160)
    widget_type: str | None = Field(default=None, max_length=120)
    payload: dict[str, Any] = Field(default_factory=dict)
    markup: str | None = Field(default=None, max_length=20_000)


class EntryGraphManifestNode(BaseModel):
    id: str
    label: str
    lane: str
    parent: str | None = None


class EntryGraphManifestEdge(BaseModel):
    from_stage: str = Field(alias="from")
    to_stage: str = Field(alias="to")
    type: str
    condition: str | None = None

    model_config = {"populate_by_name": True}


class EntryGraphManifest(BaseModel):
    version: str
    nodes: list[EntryGraphManifestNode] = Field(default_factory=list)
    edges: list[EntryGraphManifestEdge] = Field(default_factory=list)


class EntryGraphTurnResponse(BaseModel):
    state: EntryGraphState
    session_id: uuid.UUID | None = None
    run_id: uuid.UUID | None = None
    graph_version: str | None = None
    graph_manifest: EntryGraphManifest | None = None
    messages: list[EntryGraphMessage] = Field(default_factory=list)
    session: EntryGraphSession | None = None
    workspaces: list[WorkspaceRead] = Field(default_factory=list)
    available_actions: list[EntryActionCard] = Field(default_factory=list)
    persistent_actions: list[EntryActionCard] = Field(default_factory=list)
    ui_artifacts: list[EntryUIArtifact] = Field(default_factory=list)
    replace_path: str | None = None


class EntryPersistentActionsResponse(BaseModel):
    persistent_actions: list[EntryActionCard] = Field(default_factory=list)
