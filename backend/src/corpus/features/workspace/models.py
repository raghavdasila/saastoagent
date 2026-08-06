from __future__ import annotations

from dataclasses import dataclass
from typing import Literal


WorkspaceSectionStatus = Literal["available", "empty", "unavailable"]


@dataclass(frozen=True)
class WorkspaceSectionState:
    status: WorkspaceSectionStatus
    message: str


@dataclass(frozen=True)
class WorkspaceOverview:
    agent_count: int
    agents: WorkspaceSectionState
    sources: WorkspaceSectionState
    recent_activity: WorkspaceSectionState


__all__ = [
    "WorkspaceOverview",
    "WorkspaceSectionState",
    "WorkspaceSectionStatus",
]
