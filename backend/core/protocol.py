"""SSE event helpers used by the agent chat stream.

Mirrors foundation-agent's protocol.py so the frontend hook works unchanged.
"""

from __future__ import annotations

import json
import uuid
from dataclasses import dataclass, field
from typing import Any


@dataclass
class SSEEvent:
    event: str
    data: dict[str, Any] = field(default_factory=dict)

    def encode(self) -> str:
        return f"event: {self.event}\ndata: {json.dumps(self.data, default=str)}\n\n"


def stream_start(session_id: uuid.UUID) -> str:
    return SSEEvent(event="stream_start", data={"session_id": str(session_id)}).encode()


def agent_start(agent_name: str = "assistant") -> str:
    return SSEEvent(event="agent_start", data={"agent_name": agent_name}).encode()


def message_delta(content: str) -> str:
    return SSEEvent(event="message_delta", data={"content": content}).encode()


def thinking_delta(content: str) -> str:
    return SSEEvent(event="thinking_delta", data={"content": content}).encode()


def tool_start(tool_name: str, call_id: str, inputs: dict[str, Any]) -> str:
    return SSEEvent(
        event="tool_start",
        data={"tool_name": tool_name, "call_id": call_id, "inputs": inputs},
    ).encode()


def tool_end(call_id: str, output: str) -> str:
    return SSEEvent(event="tool_end", data={"call_id": call_id, "output": output}).encode()


def follow_ups(questions: list[str]) -> str:
    return SSEEvent(event="follow_ups", data={"questions": questions}).encode()


def source_citations(sources: list[dict[str, Any]]) -> str:
    return SSEEvent(event="source_citations", data={"sources": sources}).encode()


def debug_timing(timing: dict[str, Any]) -> str:
    return SSEEvent(event="debug_timing", data={"timing": timing}).encode()


def agent_end() -> str:
    return SSEEvent(event="agent_end", data={}).encode()


def stream_end() -> str:
    return SSEEvent(event="stream_end", data={}).encode()


def error(message: str, code: str = "internal_error") -> str:
    return SSEEvent(event="error", data={"message": message, "code": code}).encode()


def keepalive() -> str:
    return ": ping\n\n"
