from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any, Optional

from pydantic import BaseModel, Field


class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=32_000)
    session_id: Optional[uuid.UUID] = None
    reasoning_mode: str = Field(default="balanced", pattern="^(fast|balanced|thorough)$")
    handoff_context: Optional[dict[str, Any]] = None


class AgentSessionRead(BaseModel):
    id: uuid.UUID
    saas_agent_id: uuid.UUID
    user_id: Optional[uuid.UUID] = None
    title: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    message_count: int = 0

    model_config = {"from_attributes": True}


class AgentSessionList(BaseModel):
    sessions: list[AgentSessionRead]
    total: int


class AgentMessageRead(BaseModel):
    id: uuid.UUID
    session_id: uuid.UUID
    role: str
    content: str
    tool_calls: Optional[list | dict] = None
    thinking: Optional[str] = None
    sources: Optional[list] = None
    follow_ups: Optional[list] = None
    created_at: datetime

    model_config = {"from_attributes": True}


class AgentDocumentRead(BaseModel):
    id: uuid.UUID
    saas_agent_id: uuid.UUID
    filename: str
    original_name: str
    content_type: str
    size_bytes: int
    chunk_count: int
    created_at: datetime

    model_config = {"from_attributes": True}


class AgentDocumentChunkRead(BaseModel):
    id: uuid.UUID
    document_id: uuid.UUID
    chunk_index: int
    content: str
    has_embedding: bool = False

    model_config = {"from_attributes": True}


class AgentMemoryRead(BaseModel):
    id: uuid.UUID
    saas_agent_id: uuid.UUID
    session_id: Optional[uuid.UUID] = None
    content: str
    category: str
    created_at: datetime

    model_config = {"from_attributes": True}


class AgentMemoryCreate(BaseModel):
    content: str = Field(..., min_length=1, max_length=4000)
    category: str = Field(default="fact", pattern="^(fact|preference|instruction)$")


class AgentAdminStats(BaseModel):
    total_sessions: int
    total_messages: int
    total_documents: int
    total_memories: int


class AgentLearningCandidateRead(BaseModel):
    id: uuid.UUID
    saas_agent_id: uuid.UUID
    source_trace_id: Optional[uuid.UUID] = None
    trigger_type: str
    status: str
    title: str
    summary: str
    hint_text: str
    target_tool_name: Optional[str] = None
    target_action_path: Optional[str] = None
    target_risk_level: Optional[str] = None
    evidence: dict[str, Any] | None = None
    created_at: datetime
    reviewed_at: Optional[datetime] = None

    model_config = {"from_attributes": True}
