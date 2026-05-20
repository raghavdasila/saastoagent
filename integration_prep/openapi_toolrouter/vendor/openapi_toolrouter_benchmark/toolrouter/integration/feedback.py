from __future__ import annotations

import hashlib
import json
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .schemas import StandardFeedbackEvent, ToolRouteDecision


SECRET_MARKERS = ("password", "secret", "token", "api_key", "apikey", "credential", "authorization")


def redact_secrets(value: Any) -> Any:
    if isinstance(value, dict):
        redacted: dict[str, Any] = {}
        for key, item in value.items():
            key_text = str(key).casefold()
            if any(marker in key_text for marker in SECRET_MARKERS) and not isinstance(item, (dict, list)):
                redacted[str(key)] = "[REDACTED]"
            else:
                redacted[str(key)] = redact_secrets(item)
        return redacted
    if isinstance(value, list):
        return [redact_secrets(item) for item in value]
    return value


def conversation_context_hash(conversation_context: list[dict[str, Any]] | None) -> str:
    payload = json.dumps(redact_secrets(conversation_context or []), sort_keys=True, default=str)
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def read_standard_feedback_events(path: Path | None) -> list[dict[str, Any]]:
    if path is None or not path.exists():
        return []
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def write_standard_feedback_event(path: Path, event: StandardFeedbackEvent) -> dict[str, Any]:
    path.parent.mkdir(parents=True, exist_ok=True)
    record = event.model_dump(mode="json")
    with path.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(record, sort_keys=True) + "\n")
    return record


def feedback_event_from_decision(
    *,
    tenant_id: str,
    integration_id: str,
    query: str,
    conversation_context: list[dict[str, Any]] | None,
    decision: ToolRouteDecision,
    provided_params: dict[str, Any],
    feedback_source: str = "agent",
    label_quality: str = "implicit",
) -> StandardFeedbackEvent:
    return StandardFeedbackEvent(
        event_id=str(uuid.uuid4()),
        tenant_id=tenant_id,
        integration_id=integration_id,
        timestamp=datetime.now(timezone.utc).isoformat(),
        query=query,
        conversation_context_hash=conversation_context_hash(conversation_context),
        decision_type=decision.decision_type,
        top_candidates=[candidate.model_dump(mode="json") for candidate in decision.top_candidates],
        selected_endpoint=decision.selected_endpoint,
        missing_params=list(decision.missing_params),
        provided_params=redact_secrets(provided_params),
        follow_up_question=decision.follow_up_question,
        guardrail_mode=decision.guardrail_decision.mode,
        validation_result=decision.validation.model_dump(mode="json"),
        execution_result=None,
        feedback_source=feedback_source,  # type: ignore[arg-type]
        label_quality=label_quality,  # type: ignore[arg-type]
    )
