from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.core.models import AgentExecutionTrace, AgentLearningCandidate


def learning_payload_from_trace(trace: AgentExecutionTrace) -> dict[str, Any] | None:
    if trace.status == "failed":
        return {
            "trigger_type": "failed_execution",
            "title": f"Failure pattern for {trace.tool_name}",
            "summary": f"{trace.tool_name} failed on {trace.method} {trace.path}: {trace.error or 'unknown error'}",
            "hint_text": f"When using {trace.tool_name}, verify inputs and API availability before retrying.",
        }
    if trace.status == "needs_input" and trace.missing_inputs:
        missing = ", ".join(str(item) for item in trace.missing_inputs)
        return {
            "trigger_type": "missing_inputs",
            "title": f"Missing inputs for {trace.tool_name}",
            "summary": f"{trace.tool_name} needs these inputs before execution: {missing}",
            "hint_text": f"Ask for or infer {missing} before selecting {trace.tool_name}.",
        }
    return None


class LearningService:
    async def propose_from_trace(
        self,
        trace: AgentExecutionTrace,
        db: AsyncSession,
    ) -> AgentLearningCandidate | None:
        payload = learning_payload_from_trace(trace)
        if payload is None:
            return None
        existing = (
            await db.execute(
                select(AgentLearningCandidate).where(
                    AgentLearningCandidate.saas_agent_id == trace.saas_agent_id,
                    AgentLearningCandidate.source_trace_id == trace.id,
                    AgentLearningCandidate.trigger_type == payload["trigger_type"],
                )
            )
        ).scalar_one_or_none()
        if existing is not None:
            return existing
        candidate = AgentLearningCandidate(
            saas_agent_id=trace.saas_agent_id,
            source_trace_id=trace.id,
            status="proposed",
            target_tool_name=trace.tool_name,
            target_action_path=trace.path,
            target_risk_level=trace.risk_level,
            evidence={
                "trace_id": str(trace.id),
                "status": trace.status,
                "approval_state": trace.approval_state,
                "missing_inputs": trace.missing_inputs or [],
                "error": trace.error,
            },
            **payload,
        )
        db.add(candidate)
        await db.commit()
        await db.refresh(candidate)
        return candidate

    async def review(
        self,
        *,
        candidate_id: uuid.UUID,
        saas_agent_id: uuid.UUID,
        status: str,
        reviewed_by: uuid.UUID | None,
        db: AsyncSession,
    ) -> AgentLearningCandidate | None:
        candidate = await db.get(AgentLearningCandidate, candidate_id)
        if candidate is None or candidate.saas_agent_id != saas_agent_id:
            return None
        candidate.status = status
        candidate.reviewed_by = reviewed_by
        candidate.reviewed_at = datetime.now(timezone.utc)
        await db.commit()
        await db.refresh(candidate)
        return candidate

    async def approved_hints(self, *, saas_agent_id: uuid.UUID, db: AsyncSession) -> list[AgentLearningCandidate]:
        result = await db.execute(
            select(AgentLearningCandidate)
            .where(
                AgentLearningCandidate.saas_agent_id == saas_agent_id,
                AgentLearningCandidate.status.in_(["approved", "active"]),
            )
            .order_by(AgentLearningCandidate.created_at.desc())
            .limit(50)
        )
        return list(result.scalars().all())


learning_service = LearningService()
