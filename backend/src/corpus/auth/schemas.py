from __future__ import annotations

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


__all__ = [
    "MembershipView",
    "OrganizationView",
    "OwnerSessionView",
    "OwnerUserCreate",
    "OwnerView",
]
