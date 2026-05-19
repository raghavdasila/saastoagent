from __future__ import annotations

import uuid
from typing import Any

from pydantic import BaseModel, Field
from routedeck_core import RouteDeckProjection, RouteDeckSurface

from .app_graph import AppGraphState
from .entry import EntryGraphMessage


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
    state: AppGraphState | None = None
    node_id: str | None = Field(default=None, max_length=120)
    saas_agent_id: uuid.UUID | None = None
    operation_id: str = Field(max_length=160)
    args: dict[str, Any] = Field(default_factory=dict)
    projection_version: int | None = Field(default=None, ge=1)


class CorpusActionResponse(BaseModel):
    state: AppGraphState
    projection: RouteDeckProjection
    active_surface: RouteDeckSurface | None = None
    messages: list[EntryGraphMessage] = Field(default_factory=list)
    replace_path: str | None = None


class CorpusStateResponse(BaseModel):
    state: AppGraphState
    projection: RouteDeckProjection
    replace_path: str | None = None


class CorpusDiagnosticsSnapshot(BaseModel):
    graph_manifest: dict[str, Any] = Field(default_factory=dict)
    runtime_snapshot: dict[str, Any] = Field(default_factory=dict)
    introspection: dict[str, Any] = Field(default_factory=dict)
    projection: RouteDeckProjection
