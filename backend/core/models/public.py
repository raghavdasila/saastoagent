import enum
import uuid as uuid_pkg

from fastapi_users.db import SQLAlchemyBaseUserTableUUID
from sqlalchemy import Boolean, Column, DateTime, Enum, ForeignKey, String, Text, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from .base import Base


class SaaSAgentRole(str, enum.Enum):
    owner = "owner"
    admin = "admin"
    operator = "operator"
    viewer = "viewer"


class User(SQLAlchemyBaseUserTableUUID, Base):
    __tablename__ = "users"

    display_name = Column(String(255), nullable=True)

    saas_agents = relationship("SaaSAgentMember", back_populates="user", lazy="selectin")


class SaaSAgent(Base):
    __tablename__ = "saas_agents"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid_pkg.uuid4)
    name = Column(String(255), nullable=False)
    slug = Column(String(255), nullable=False, unique=True)
    created_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    members = relationship("SaaSAgentMember", back_populates="saas_agent", lazy="selectin")
    deployment = relationship("SaaSAgentDeployment", back_populates="saas_agent", uselist=False, lazy="selectin")


class SaaSAgentMember(Base):
    __tablename__ = "saas_agent_members"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid_pkg.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    saas_agent_id = Column(UUID(as_uuid=True), ForeignKey("saas_agents.id"), nullable=False)
    role = Column(Enum(SaaSAgentRole), nullable=False, default=SaaSAgentRole.viewer)
    joined_at = Column(DateTime(timezone=True), server_default=func.now())

    user = relationship("User", back_populates="saas_agents")
    saas_agent = relationship("SaaSAgent", back_populates="members")


class SaaSAgentDeployment(Base):
    __tablename__ = "saas_agent_deployments"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid_pkg.uuid4)
    saas_agent_id = Column(UUID(as_uuid=True), ForeignKey("saas_agents.id", ondelete="CASCADE"), nullable=False, unique=True, index=True)
    enabled = Column(Boolean, nullable=False, default=False)
    visitor_auth_mode = Column(String(40), nullable=False, default="inherit_from_connection")
    execution_mode = Column(String(40), nullable=False, default="sandbox")
    default_write_policy = Column(String(40), nullable=False, default="confirm")
    welcome_message = Column(Text, nullable=False, default="How can I help?")
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    saas_agent = relationship("SaaSAgent", back_populates="deployment")
