import uuid
from typing import Any, Literal

from pydantic import BaseModel, Field

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
    validation_hint: str | None = Field(default=None, max_length=300)
    sensitive: bool = False


class EntryActionCard(BaseModel):
    id: str = Field(min_length=1, max_length=120)
    label: str = Field(min_length=1, max_length=120)
    capability_id: str | None = Field(default=None, max_length=120)
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
    description: str | None = None
    prompt_placeholder: str | None = None
    allowed_actions: list[str] = Field(default_factory=list)
    expected_input: str | None = None
    recovery_prompt: str | None = None


class EntryGraphManifestEdge(BaseModel):
    from_stage: str = Field(alias="from")
    to_stage: str = Field(alias="to")
    type: str
    condition: str | None = None
    explanation: str | None = None
    action_id: str | None = None

    model_config = {"populate_by_name": True}


class EntryGraphManifestAction(BaseModel):
    id: str
    label: str
    capability_id: str | None = None
    description: str | None = None
    emphasis: EntryActionEmphasis = "secondary"
    kind: EntryActionKind = "button"
    category: EntryActionCategory | None = None
    placement: EntryActionPlacement | None = None
    fields: list[EntryActionField] = Field(default_factory=list)
    payload: dict[str, Any] = Field(default_factory=dict)
    allowed_nodes: list[str] = Field(default_factory=list)
    visibility: str = "contextual"
    recovery_prompt: str | None = None
    sensitive: bool = False


class EntryRouteDeckRuntimeSnapshot(BaseModel):
    current_node: str | None = None
    reachable_nodes: list[str] = Field(default_factory=list)
    valid_actions: list[EntryActionCard] = Field(default_factory=list)
    blocked_actions: list[dict[str, str]] = Field(default_factory=list)
    executed_nodes: list[str] = Field(default_factory=list)
    progress: dict[str, Any] = Field(default_factory=dict)
    recovery_prompts: list[str] = Field(default_factory=list)
    diagnostics: dict[str, Any] = Field(default_factory=dict)


class EntryGraphManifest(BaseModel):
    version: str
    nodes: list[EntryGraphManifestNode] = Field(default_factory=list)
    edges: list[EntryGraphManifestEdge] = Field(default_factory=list)
    actions: list[EntryGraphManifestAction] = Field(default_factory=list)
    policies: dict[str, Any] = Field(default_factory=dict)
    test_paths: list[dict[str, Any]] = Field(default_factory=list)


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
