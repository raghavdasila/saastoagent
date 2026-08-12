from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Literal


WorkspaceSectionStatus = Literal["available", "empty", "unavailable"]


@dataclass(frozen=True)
class WorkspaceSectionState:
    status: WorkspaceSectionStatus
    message: str


@dataclass(frozen=True)
class WorkspaceActivity:
    kind: Literal["agent", "source"]
    title: str
    status: str
    occurred_at: datetime


@dataclass(frozen=True)
class WorkspaceOverview:
    agent_count: int
    source_count: int
    agents: WorkspaceSectionState
    sources: WorkspaceSectionState
    recent_activity: WorkspaceSectionState
    activity: tuple[WorkspaceActivity, ...] = ()


__all__ = [
    "WorkspaceOverview",
    "WorkspaceActivity",
    "WorkspaceSectionState",
    "WorkspaceSectionStatus",
]
