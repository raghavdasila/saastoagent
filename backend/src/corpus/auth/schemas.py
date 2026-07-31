from __future__ import annotations

from datetime import datetime
from typing import Literal

from fastapi_users import schemas
from pydantic import BaseModel, ConfigDict, EmailStr, Field


class OwnerUserCreate(schemas.BaseUserCreate):
    display_name: str | None = Field(default=None, max_length=128)


class OwnerView(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    email: EmailStr
    display_name: str | None
    is_verified: bool


class OrganizationView(BaseModel):
    name: str
    slug: str


class MembershipView(BaseModel):
    role: Literal["owner", "admin", "member"]


class OwnerSessionView(BaseModel):
    owner: OwnerView
    organization: OrganizationView
    membership: MembershipView
    route_session_state: Literal["adopted", "resumed"]


class AnonymousPrincipalView(BaseModel):
    type: Literal["anonymous"] = "anonymous"


class OwnerPrincipalView(BaseModel):
    type: Literal["owner"] = "owner"
    owner: OwnerView
    organization: OrganizationView
    membership: MembershipView


class TokenPairView(BaseModel):
    access_token: str
    access_expires_at: datetime
    refresh_token: str
    refresh_idle_expires_at: datetime
    refresh_absolute_expires_at: datetime
    principal: AnonymousPrincipalView | OwnerPrincipalView


class RefreshRequest(BaseModel):
    refresh_token: str = Field(min_length=32, max_length=512)


class ActiveConversationRunView(BaseModel):
    request_id: str
    status: Literal["running", "completed", "interrupted"]
    stage: Literal[
        "starting",
        "awaiting_model",
        "generating",
        "completed",
        "interrupted",
    ]
    cursor: int = Field(ge=1)


class ConversationView(BaseModel):
    id: str
    current_node_id: str
    session_version: int = Field(ge=0)
    updated_at: datetime
    active_run: ActiveConversationRunView | None = None


__all__ = [
    "AnonymousPrincipalView",
    "ActiveConversationRunView",
    "ConversationView",
    "MembershipView",
    "OrganizationView",
    "OwnerSessionView",
    "OwnerPrincipalView",
    "OwnerUserCreate",
    "OwnerView",
    "RefreshRequest",
    "TokenPairView",
]
