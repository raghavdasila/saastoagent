from __future__ import annotations

import enum
import uuid as uuid_pkg

from sqlalchemy import Column, DateTime, Enum, ForeignKey, Index, Integer, String, Text, UniqueConstraint, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import relationship

from .base import Base


class ToolRouterIndexStatus(str, enum.Enum):
    building = "building"
    ready = "ready"
    blocked = "blocked"
    stale = "stale"


class ToolRouterIndex(Base):
    __tablename__ = "toolrouter_indexes"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid_pkg.uuid4)
    saas_agent_id = Column(UUID(as_uuid=True), ForeignKey("saas_agents.id", ondelete="CASCADE"), nullable=False, index=True)
    router_version = Column(String(80), nullable=False)
    catalog_fingerprint = Column(String(128), nullable=False)
    status = Column(
        Enum(ToolRouterIndexStatus, name="sta_v01_toolrouter_index_status", create_constraint=False),
        nullable=False,
        default=ToolRouterIndexStatus.building,
    )
    document_count = Column(Integer, nullable=False, default=0)
    endpoint_count = Column(Integer, nullable=False, default=0)
    stats = Column(JSONB, nullable=False, default=dict)
    error = Column(Text, nullable=True)
    built_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    documents = relationship("ToolRouterDocument", back_populates="index", cascade="all, delete-orphan")

    __table_args__ = (
        UniqueConstraint(
            "saas_agent_id",
            "router_version",
            "catalog_fingerprint",
            name="uq_sta_v01_toolrouter_index_fingerprint",
        ),
        Index("ix_toolrouter_indexes_agent_ready", "saas_agent_id", "router_version", "status"),
    )


class ToolRouterDocument(Base):
    __tablename__ = "toolrouter_documents"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid_pkg.uuid4)
    index_id = Column(UUID(as_uuid=True), ForeignKey("toolrouter_indexes.id", ondelete="CASCADE"), nullable=False, index=True)
    saas_agent_id = Column(UUID(as_uuid=True), ForeignKey("saas_agents.id", ondelete="CASCADE"), nullable=False, index=True)
    action_node_id = Column(UUID(as_uuid=True), ForeignKey("action_nodes.id", ondelete="CASCADE"), nullable=False, index=True)
    generated_tool_id = Column(UUID(as_uuid=True), ForeignKey("generated_tools.id", ondelete="CASCADE"), nullable=False, index=True)
    endpoint_key = Column(String(96), nullable=False, index=True)
    doc_kind = Column(String(40), nullable=False, index=True)
    search_text = Column(Text, nullable=False)
    tokens = Column(JSONB, nullable=False, default=list)
    graph_refs = Column(JSONB, nullable=False, default=dict)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    index = relationship("ToolRouterIndex", back_populates="documents")

    __table_args__ = (
        Index("ix_toolrouter_documents_agent_kind", "saas_agent_id", "doc_kind"),
        Index("ix_toolrouter_documents_endpoint", "index_id", "endpoint_key"),
    )
