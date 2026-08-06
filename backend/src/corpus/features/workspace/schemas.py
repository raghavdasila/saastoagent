from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field

from .models import WorkspaceOverview, WorkspaceSectionStatus


class WorkspaceSectionView(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    status: WorkspaceSectionStatus
    message: str


class WorkspaceOverviewView(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    agent_count: int = Field(ge=0)
    agents: WorkspaceSectionView
    sources: WorkspaceSectionView
    recent_activity: WorkspaceSectionView

    @classmethod
    def from_model(cls, value: WorkspaceOverview) -> WorkspaceOverviewView:
        return cls.model_validate(value, from_attributes=True)


__all__ = ["WorkspaceOverviewView", "WorkspaceSectionView"]
