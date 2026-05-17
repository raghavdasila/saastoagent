from __future__ import annotations

import enum
import uuid as uuid_pkg

from sqlalchemy import Boolean, Column, DateTime, Enum, ForeignKey, LargeBinary, String, Text, UniqueConstraint, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import relationship

from .base import Base


class ConnectionType(str, enum.Enum):
    rest_api = "rest_api"


class AuthType(str, enum.Enum):
    none = "none"
    bearer = "bearer"
    api_key_header = "api_key_header"
    api_key_query = "api_key_query"
    basic = "basic"
    oauth_client_credentials = "oauth_client_credentials"
    custom_header = "custom_header"


class RiskLevel(str, enum.Enum):
    read = "read"
    write = "write"
    destructive = "destructive"
    financial = "financial"


class ActionNodeStatus(str, enum.Enum):
    discovered = "discovered"
    deprecated = "deprecated"


class ToolStatus(str, enum.Enum):
    draft = "draft"
    active = "active"


class ActivationOverallStatus(str, enum.Enum):
    blocked = "blocked"
    running = "running"
    ready = "ready"


class ActivationStepStatus(str, enum.Enum):
    pending = "pending"
    running = "running"
    succeeded = "succeeded"
    failed = "failed"
    skipped = "skipped"


class Connection(Base):
    __tablename__ = "connections"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid_pkg.uuid4)
    saas_agent_id = Column(UUID(as_uuid=True), ForeignKey("saas_agents.id", ondelete="CASCADE"), nullable=False, index=True)
    name = Column(String(255), nullable=False)
    type = Column(Enum(ConnectionType, name="sta_v01_connection_type", create_constraint=False), nullable=False)
    provider = Column(String(64), nullable=False, default="rest_api")
    config = Column(JSONB, nullable=False, default=dict)
    auth_type = Column(Enum(AuthType, name="sta_v01_auth_type", create_constraint=False), nullable=True)
    last_generated_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    credentials = relationship("EncryptedCredential", back_populates="connection", cascade="all, delete-orphan", lazy="selectin")
    action_nodes = relationship("ActionNode", back_populates="connection", cascade="all, delete-orphan")
    generated_tools = relationship("GeneratedTool", back_populates="connection", cascade="all, delete-orphan")
    activation_state = relationship("ConnectionActivationState", back_populates="connection", uselist=False, cascade="all, delete-orphan")


class EncryptedCredential(Base):
    __tablename__ = "encrypted_credentials"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid_pkg.uuid4)
    connection_id = Column(UUID(as_uuid=True), ForeignKey("connections.id", ondelete="CASCADE"), nullable=False)
    credential_type = Column(String(100), nullable=False)
    encrypted_value = Column(LargeBinary, nullable=False)
    metadata_ = Column("metadata", JSONB, nullable=True, default=dict)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    connection = relationship("Connection", back_populates="credentials")

    __table_args__ = (UniqueConstraint("connection_id", "credential_type", name="uq_sta_v01_conn_cred_type"),)


class ActionNode(Base):
    __tablename__ = "action_nodes"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid_pkg.uuid4)
    connection_id = Column(UUID(as_uuid=True), ForeignKey("connections.id", ondelete="CASCADE"), nullable=False, index=True)
    saas_agent_id = Column(UUID(as_uuid=True), ForeignKey("saas_agents.id", ondelete="CASCADE"), nullable=False, index=True)
    name = Column(String(500), nullable=False)
    path = Column(String(2000), nullable=False)
    method = Column(String(20), nullable=False)
    description = Column(Text, nullable=True, default="")
    parameters = Column(JSONB, nullable=False, default=list)
    request_body = Column(JSONB, nullable=False, default=dict)
    responses = Column(JSONB, nullable=False, default=dict)
    security = Column(JSONB, nullable=False, default=list)
    tags = Column(JSONB, nullable=False, default=list)
    embedding_text = Column(Text, nullable=True)
    risk_level = Column(Enum(RiskLevel, name="sta_v01_risk_level", create_constraint=False), nullable=False, default=RiskLevel.read)
    status = Column(Enum(ActionNodeStatus, name="sta_v01_action_node_status", create_constraint=False), nullable=False, default=ActionNodeStatus.discovered)
    source_type = Column(String(100), nullable=True)
    source_spec_url = Column(String(2000), nullable=True)
    source_index = Column(String(100), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    connection = relationship("Connection", back_populates="action_nodes")
    generated_tool = relationship("GeneratedTool", back_populates="action_node", uselist=False, cascade="all, delete-orphan")

    __table_args__ = (UniqueConstraint("connection_id", "path", "method", name="uq_sta_v01_action_node_endpoint"),)


class GeneratedTool(Base):
    __tablename__ = "generated_tools"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid_pkg.uuid4)
    action_node_id = Column(UUID(as_uuid=True), ForeignKey("action_nodes.id", ondelete="CASCADE"), nullable=False, index=True)
    connection_id = Column(UUID(as_uuid=True), ForeignKey("connections.id", ondelete="CASCADE"), nullable=False, index=True)
    saas_agent_id = Column(UUID(as_uuid=True), ForeignKey("saas_agents.id", ondelete="CASCADE"), nullable=False, index=True)
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    function_schema = Column(JSONB, nullable=False)
    risk_level = Column(Enum(RiskLevel, name="sta_v01_tool_risk_level", create_constraint=False), nullable=False, default=RiskLevel.read)
    status = Column(Enum(ToolStatus, name="sta_v01_tool_status", create_constraint=False), nullable=False, default=ToolStatus.active)
    requires_approval = Column(Boolean, nullable=False, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    connection = relationship("Connection", back_populates="generated_tools")
    action_node = relationship("ActionNode", back_populates="generated_tool")


class ConnectionActivationState(Base):
    __tablename__ = "connection_activation_state"

    connection_id = Column(UUID(as_uuid=True), ForeignKey("connections.id", ondelete="CASCADE"), primary_key=True)
    saas_agent_id = Column(UUID(as_uuid=True), ForeignKey("saas_agents.id", ondelete="CASCADE"), nullable=False, index=True)
    overall_status = Column(String(20), nullable=False, default=ActivationOverallStatus.blocked.value)
    generate_status = Column(String(20), nullable=False, default=ActivationStepStatus.pending.value)
    embed_status = Column(String(20), nullable=False, default=ActivationStepStatus.pending.value)
    tools_status = Column(String(20), nullable=False, default=ActivationStepStatus.pending.value)
    current_step = Column(String(50), nullable=True)
    blocked_reason = Column(Text, nullable=True)
    started_at = Column(DateTime(timezone=True), nullable=True)
    completed_at = Column(DateTime(timezone=True), nullable=True)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    connection = relationship("Connection", back_populates="activation_state")
