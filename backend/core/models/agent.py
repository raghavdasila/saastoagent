"""Agent runtime models — chat sessions, messages, documents (RAG), memories.

All rows are scoped to a saas_agent_id (and the message authoring user_id).
This keeps each SaaSAgent's agent context fully isolated.
"""

from __future__ import annotations

import uuid as uuid_pkg
from datetime import datetime

from pgvector.sqlalchemy import Vector
from sqlalchemy import Column, DateTime, ForeignKey, Index, Integer, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import relationship

from .base import Base


class AgentSession(Base):
    __tablename__ = "agent_sessions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid_pkg.uuid4)
    saas_agent_id = Column(
        UUID(as_uuid=True),
        ForeignKey("saas_agents.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    user_id = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    title = Column(String(255), nullable=True)
    metadata_ = Column("metadata", JSONB, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    messages = relationship(
        "AgentMessage",
        back_populates="session",
        cascade="all, delete-orphan",
        order_by="AgentMessage.created_at",
    )

    __table_args__ = (Index("ix_agent_sessions_ws_updated", "saas_agent_id", "updated_at"),)


class AgentMessage(Base):
    __tablename__ = "agent_messages"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid_pkg.uuid4)
    session_id = Column(
        UUID(as_uuid=True),
        ForeignKey("agent_sessions.id", ondelete="CASCADE"),
        nullable=False,
    )
    saas_agent_id = Column(
        UUID(as_uuid=True),
        ForeignKey("saas_agents.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    role = Column(String(20), nullable=False)  # user | assistant | tool
    content = Column(Text, nullable=False, default="")
    tool_calls = Column(JSONB, nullable=True)
    thinking = Column(Text, nullable=True)
    sources = Column(JSONB, nullable=True)
    follow_ups = Column(JSONB, nullable=True)
    metadata_ = Column("metadata", JSONB, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    session = relationship("AgentSession", back_populates="messages")

    __table_args__ = (
        Index("ix_agent_messages_session_created", "session_id", "created_at"),
    )


class AgentDocument(Base):
    __tablename__ = "agent_documents"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid_pkg.uuid4)
    saas_agent_id = Column(
        UUID(as_uuid=True),
        ForeignKey("saas_agents.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    uploaded_by = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )
    filename = Column(String(255), nullable=False)
    original_name = Column(String(255), nullable=False)
    content_type = Column(String(100), nullable=False)
    size_bytes = Column(Integer, nullable=False, default=0)
    chunk_count = Column(Integer, nullable=False, default=0)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    chunks = relationship(
        "AgentDocumentChunk",
        back_populates="document",
        cascade="all, delete-orphan",
    )


class AgentDocumentChunk(Base):
    __tablename__ = "agent_document_chunks"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid_pkg.uuid4)
    document_id = Column(
        UUID(as_uuid=True),
        ForeignKey("agent_documents.id", ondelete="CASCADE"),
        nullable=False,
    )
    saas_agent_id = Column(
        UUID(as_uuid=True),
        ForeignKey("saas_agents.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    chunk_index = Column(Integer, nullable=False)
    content = Column(Text, nullable=False)
    embedding = Column(Vector(1536), nullable=True)
    metadata_ = Column("metadata", JSONB, nullable=True)

    document = relationship("AgentDocument", back_populates="chunks")

    __table_args__ = (Index("ix_agent_chunks_SaaSAgent", "saas_agent_id"),)


class AgentMemory(Base):
    __tablename__ = "agent_memories"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid_pkg.uuid4)
    saas_agent_id = Column(
        UUID(as_uuid=True),
        ForeignKey("saas_agents.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    session_id = Column(
        UUID(as_uuid=True),
        ForeignKey("agent_sessions.id", ondelete="SET NULL"),
        nullable=True,
    )
    user_id = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )
    content = Column(Text, nullable=False)
    category = Column(String(50), nullable=False, default="fact")
    embedding = Column(Vector(1536), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class AgentExecutionTrace(Base):
    __tablename__ = "agent_execution_traces"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid_pkg.uuid4)
    saas_agent_id = Column(
        UUID(as_uuid=True),
        ForeignKey("saas_agents.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    session_id = Column(
        UUID(as_uuid=True),
        ForeignKey("agent_sessions.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    message_id = Column(
        UUID(as_uuid=True),
        ForeignKey("agent_messages.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    connection_id = Column(
        UUID(as_uuid=True),
        ForeignKey("connections.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    action_node_id = Column(
        UUID(as_uuid=True),
        ForeignKey("action_nodes.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    generated_tool_id = Column(
        UUID(as_uuid=True),
        ForeignKey("generated_tools.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    tool_name = Column(String(255), nullable=False)
    action_name = Column(String(500), nullable=True)
    method = Column(String(20), nullable=True)
    path = Column(String(2000), nullable=True)
    risk_level = Column(String(30), nullable=False, default="read")
    status = Column(String(40), nullable=False, default="planned")
    approval_state = Column(String(40), nullable=False, default="not_required")
    inputs = Column(JSONB, nullable=False, default=dict)
    missing_inputs = Column(JSONB, nullable=False, default=list)
    candidate_summary = Column(JSONB, nullable=False, default=list)
    result = Column(JSONB, nullable=True)
    error = Column(Text, nullable=True)
    duration_ms = Column(Integer, nullable=True)
    route_node = Column(String(80), nullable=True)
    requested_by = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    approved_by = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    __table_args__ = (
        Index("ix_agent_execution_traces_agent_created", "saas_agent_id", "created_at"),
    )


class AgentLearningCandidate(Base):
    __tablename__ = "agent_learning_candidates"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid_pkg.uuid4)
    saas_agent_id = Column(
        UUID(as_uuid=True),
        ForeignKey("saas_agents.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    source_trace_id = Column(
        UUID(as_uuid=True),
        ForeignKey("agent_execution_traces.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    trigger_type = Column(String(80), nullable=False)
    status = Column(String(40), nullable=False, default="proposed")
    title = Column(String(255), nullable=False)
    summary = Column(Text, nullable=False)
    hint_text = Column(Text, nullable=False)
    target_tool_name = Column(String(255), nullable=True)
    target_action_path = Column(String(2000), nullable=True)
    target_risk_level = Column(String(30), nullable=True)
    evidence = Column(JSONB, nullable=False, default=dict)
    created_by = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    reviewed_by = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    reviewed_at = Column(DateTime(timezone=True), nullable=True)

    __table_args__ = (
        Index("ix_agent_learning_candidates_agent_status", "saas_agent_id", "status"),
    )
