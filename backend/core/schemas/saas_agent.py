import uuid
from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field


class SaaSAgentCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    slug: str = Field(..., min_length=1, max_length=255, pattern=r"^[a-z0-9][a-z0-9\-]*$")


class SaaSAgentRead(BaseModel):
    id: uuid.UUID
    name: str
    slug: str
    created_by: uuid.UUID
    created_at: datetime
    role: str | None = None

    model_config = {"from_attributes": True}


class SaaSAgentStats(BaseModel):
    connections_count: int = 0
    tools_count: int = 0
    learnings_count: int = 0
    active_learnings_count: int = 0
    systems_count: int = 0
    connections_with_learnings: int = 0
    tools_with_learnings: int = 0
    avg_confidence: float = 0.0
    maturity: float = 0.0


VisitorAuthMode = Literal["inherit_from_connection", "anonymous", "login_required"]
ExecutionMode = Literal["sandbox", "live"]
DefaultWritePolicy = Literal["confirm", "owner_approval", "block"]
DeploymentPolicyState = Literal[
    "allowed_read",
    "needs_visitor_auth",
    "needs_owner_approval",
    "blocked",
    "failed_with_recovery",
]


class SaaSAgentDeploymentRead(BaseModel):
    id: uuid.UUID
    saas_agent_id: uuid.UUID
    enabled: bool
    visitor_auth_mode: VisitorAuthMode
    execution_mode: ExecutionMode
    default_write_policy: DefaultWritePolicy
    welcome_message: str
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class SaaSAgentDeploymentUpdate(BaseModel):
    enabled: bool = False
    visitor_auth_mode: VisitorAuthMode = "inherit_from_connection"
    execution_mode: ExecutionMode = "sandbox"
    default_write_policy: DefaultWritePolicy = "confirm"
    welcome_message: str = Field(default="How can I help?", min_length=1, max_length=2000)


class DeployedAgentProfile(BaseModel):
    saas_agent_id: uuid.UUID
    slug: str
    name: str
    enabled: bool
    auth_required: bool
    visitor_auth_mode: VisitorAuthMode
    execution_mode: ExecutionMode
    default_write_policy: DefaultWritePolicy
    policy_state: DeploymentPolicyState
    welcome_message: str


class AgentApprovalRead(BaseModel):
    trace_id: uuid.UUID
    trace_token: str
    status: str
    approval_state: str
    tool_name: str
    action_name: str | None = None
    method: str | None = None
    path: str | None = None
    risk_level: str | None = None
    inputs: dict = Field(default_factory=dict)
    requested_by: uuid.UUID | None = None
    created_at: datetime


class AgentApprovalDecisionRead(BaseModel):
    trace_id: uuid.UUID
    status: str
    approval_state: str
    message: str
    result: dict | None = None
