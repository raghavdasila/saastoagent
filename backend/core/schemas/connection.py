from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class ConnectionCreate(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    type: str = Field(default="rest_api", pattern="^rest_api$")
    provider: str = Field(default="rest_api", max_length=64)
    config: dict[str, Any] = Field(default_factory=dict)
    credentials: dict[str, str] | None = None
    auth_type: str | None = Field(
        default=None,
        pattern="^(none|bearer|api_key_header|api_key_query|basic|oauth_client_credentials|custom_header)$",
    )


class ConnectionRead(BaseModel):
    id: uuid.UUID
    workspace_id: uuid.UUID
    name: str
    type: str
    provider: str
    config: dict[str, Any]
    auth_type: str | None = None
    has_credentials: bool = False
    action_nodes_count: int = 0
    tools_count: int = 0
    activation_status: str | None = None
    activation_steps: dict[str, Any] | None = None
    created_at: datetime
    updated_at: datetime


class ActionNodeRead(BaseModel):
    id: uuid.UUID
    connection_id: uuid.UUID
    workspace_id: uuid.UUID
    name: str
    path: str
    method: str
    description: str | None = None
    risk_level: str
    status: str
    tags: list[Any] = Field(default_factory=list)
    source_type: str | None = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class ToolRead(BaseModel):
    id: uuid.UUID
    action_node_id: uuid.UUID
    connection_id: uuid.UUID
    workspace_id: uuid.UUID
    name: str
    description: str | None = None
    function_schema: dict[str, Any]
    risk_level: str
    status: str
    requires_approval: bool = False
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class ActivationStateRead(BaseModel):
    connection_id: uuid.UUID
    workspace_id: uuid.UUID
    overall_status: str
    steps: dict[str, Any]
    current_step: str | None = None
    blocked_reason: str | None = None
    started_at: datetime | None = None
    completed_at: datetime | None = None
    updated_at: datetime | None = None
