from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class StartSandboxArguments(BaseModel):
    model_config = ConfigDict(extra="forbid")
    agent_ref: str = Field(min_length=1, max_length=64)
    build_id: uuid.UUID | None = None
    message: str = Field(
        min_length=1,
        max_length=4_000,
        description=(
            "The user's unresolved request for the built Agent. Preserve its meaning and "
            "ambiguity; do not answer it, add missing details, split it into operations, "
            "select an operation, or invent identifiers."
        ),
    )


class ResumeSandboxArguments(BaseModel):
    model_config = ConfigDict(extra="forbid")
    agent_ref: str = Field(min_length=1, max_length=64)
    run_id: uuid.UUID | None = None
    message: str = Field(
        min_length=1,
        max_length=4_000,
        description="The user's exact natural clarification reply; do not rewrite or expand it.",
    )
    selected_operation_id: str | None = Field(
        default=None,
        min_length=1,
        max_length=160,
        description=(
            "When the latest Sandbox tool observation contains candidate_choices and the "
            "user chooses one by its natural label, copy that candidate's exact operation_id. "
            "Do not put an operation choice in answers and never invent an identity."
        ),
    )
    answers: dict[str, str] = Field(
        default_factory=dict,
        max_length=16,
        description=(
            "Only the exact missing_input_names from the latest Sandbox tool observation, "
            "using values explicitly supplied by the user. Keep this empty for an operation choice."
        ),
    )


class ResolveSandboxReviewArguments(BaseModel):
    model_config = ConfigDict(extra="forbid")
    agent_ref: str = Field(min_length=1, max_length=64)
    run_id: uuid.UUID
    review_id: str = Field(min_length=1, max_length=160)


class SandboxClarificationChoiceView(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")
    operation_id: str
    label: str | None


class SandboxClarificationView(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")
    question: str
    candidate_operation_ids: tuple[str, ...]
    candidate_choices: tuple[SandboxClarificationChoiceView, ...]
    missing_input_names: tuple[str, ...]


class SandboxEventView(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")
    sequence: int
    kind: str
    occurred_at: str
    safe_data: dict[str, object]


class SandboxRunView(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")
    id: uuid.UUID
    agent_id: uuid.UUID
    build_id: uuid.UUID
    runtime_session_id: str
    runtime_run_id: str
    status: str
    message: str
    awaiting: str | None
    clarification: SandboxClarificationView | None
    final_response: str | None
    api_call_count: int
    events: tuple[SandboxEventView, ...]
    routedeck_projection: dict[str, object]
    failure_code: str | None
    created_at: datetime
    updated_at: datetime


class SandboxRunCollectionView(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")
    agent_id: uuid.UUID
    runs: tuple[SandboxRunView, ...]


__all__ = [
    "ResumeSandboxArguments",
    "ResolveSandboxReviewArguments",
    "SandboxClarificationChoiceView",
    "SandboxClarificationView",
    "SandboxEventView",
    "SandboxRunCollectionView",
    "SandboxRunView",
    "StartSandboxArguments",
]
