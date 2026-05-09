from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any, Awaitable, Callable, TypedDict, cast

from sqlalchemy.ext.asyncio import AsyncSession

from backend.core.models import EntryRun, EntrySession, User
from backend.core.schemas import (
    EntryActionCard,
    EntryGraphMessage,
    EntryGraphSession,
    EntryGraphState,
    EntryUIArtifact,
    UserRead,
    WorkspaceRead,
)

if TYPE_CHECKING:
    from .runtime_store import EntryRuntimeStore


EntryEventSink = Callable[[str, dict[str, Any]], Awaitable[None]]


class EntryRuntimeState(TypedDict, total=False):
    node: str
    intent: str | None
    display_name: str
    email: str
    workspace_name: str
    workspace_slug: str
    active_workspace_id: uuid.UUID | None
    active_connection_id: uuid.UUID | None
    connection_draft: dict[str, Any]
    entry_draft: dict[str, Any]
    platform_question_context: list[dict[str, Any]]
    canvas_artifacts: list[dict[str, Any]]
    follow_up_context: dict[str, Any]
    user_input: str | None
    initial_intent: str | None
    selected_action_id: str | None
    action_payload: dict[str, Any] | None
    current_user: User | None
    runtime: "EntryTurnRuntime"
    messages: list[EntryGraphMessage]
    session_payload: EntryGraphSession | None
    workspaces: list[WorkspaceRead]
    available_actions: list[EntryActionCard]
    persistent_actions: list[EntryActionCard]
    ui_artifacts: list[EntryUIArtifact]
    replace_path: str | None


@dataclass
class EntryTurnRuntime:
    db: AsyncSession
    store: "EntryRuntimeStore"
    session_record: EntrySession
    run_record: EntryRun
    graph_manifest: dict[str, Any]
    event_sink: EntryEventSink | None = None
    stage_sequence: int = 0
    output_sequence: int = 0
    artifact_sequence: int = 0
    executed_stage_ids: list[str] = field(default_factory=list)

    async def emit(self, event: str, data: dict[str, Any]) -> None:
        if self.event_sink is not None:
            await self.event_sink(event, data)

    def next_stage_sequence(self) -> int:
        self.stage_sequence += 1
        return self.stage_sequence

    def next_output_sequence(self) -> int:
        self.output_sequence += 1
        return self.output_sequence


def assistant_message(content: str) -> EntryGraphMessage:
    return EntryGraphMessage(content=content)


def merge_messages(state: EntryRuntimeState, *contents: str) -> list[EntryGraphMessage]:
    messages = list(state.get("messages", []))
    messages.extend(assistant_message(content) for content in contents)
    return messages


def user_read(user: User) -> UserRead:
    return UserRead(
        id=user.id,
        email=user.email,
        is_active=user.is_active,
        is_superuser=user.is_superuser,
        is_verified=user.is_verified,
        display_name=user.display_name,
    )


def state_payload(state: EntryRuntimeState) -> EntryGraphState:
    return EntryGraphState(
        node=cast(Any, state["node"]),
        intent=cast(Any, state.get("intent")),
        display_name=state.get("display_name", ""),
        email=state.get("email", ""),
        workspace_name=state.get("workspace_name", ""),
        workspace_slug=state.get("workspace_slug", ""),
        active_workspace_id=state.get("active_workspace_id"),
        active_connection_id=state.get("active_connection_id"),
        connection_draft=state.get("connection_draft", {}),
        entry_draft=state.get("entry_draft", {}),
        platform_question_context=state.get("platform_question_context", []),
        canvas_artifacts=state.get("canvas_artifacts", []),
        follow_up_context=state.get("follow_up_context", {}),
    )


def state_dump(state: EntryRuntimeState) -> dict[str, Any]:
    return state_payload(state).model_dump(mode="json")
