from __future__ import annotations

import uuid
from collections.abc import Mapping
from typing import Any

from fastapi import HTTPException, status

from backend.core.schemas import AppGraphState, EntryGraphMessage
from backend.services.agent.learning_service import learning_service
from backend.services.app_graph.manifest import AppActionIds, AppNodeIds

from .types import CorpusActionContext, CorpusActionResult


async def learning_open(state: AppGraphState, payload: Mapping[str, Any], context: CorpusActionContext) -> CorpusActionResult:
    state.node = AppNodeIds.LEARNING
    return CorpusActionResult(state=state)


async def learning_policy_candidate_open(state: AppGraphState, payload: Mapping[str, Any], context: CorpusActionContext) -> CorpusActionResult:
    candidate_id = str(payload.get("candidate_id") or "").strip()
    if not candidate_id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="candidate_id is required")
    state.node = AppNodeIds.LEARNING_POLICY_CANDIDATE
    state.route_params = {"candidate_id": candidate_id}
    state.active_surface_id = "learning.policy_candidate.review"
    return CorpusActionResult(state=state, evidence=[{"type": "learning_policy_candidate_opened", "candidate_id": candidate_id}])


async def learning_execution_trace_open(state: AppGraphState, payload: Mapping[str, Any], context: CorpusActionContext) -> CorpusActionResult:
    trace_id = str(payload.get("trace_id") or "").strip()
    if not trace_id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="trace_id is required")
    state.node = AppNodeIds.LEARNING_EXECUTION_TRACE
    state.route_params = {"trace_id": trace_id}
    state.active_surface_id = "learning.execution_trace.review"
    return CorpusActionResult(state=state, evidence=[{"type": "learning_execution_trace_opened", "trace_id": trace_id}])


async def learning_active_policy_open(state: AppGraphState, payload: Mapping[str, Any], context: CorpusActionContext) -> CorpusActionResult:
    candidate_id = str(payload.get("candidate_id") or "").strip()
    if not candidate_id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="candidate_id is required")
    state.node = AppNodeIds.LEARNING_ACTIVE_POLICY
    state.route_params = {"candidate_id": candidate_id}
    state.active_surface_id = "learning.active_policy.review"
    return CorpusActionResult(state=state, evidence=[{"type": "learning_active_policy_opened", "candidate_id": candidate_id}])


async def learning_approve(state: AppGraphState, payload: Mapping[str, Any], context: CorpusActionContext) -> CorpusActionResult:
    return await review_learning(state, payload, context, "approved")


async def learning_reject(state: AppGraphState, payload: Mapping[str, Any], context: CorpusActionContext) -> CorpusActionResult:
    return await review_learning(state, payload, context, "rejected")


async def review_learning(state: AppGraphState, payload: Mapping[str, Any], context: CorpusActionContext, review_status: str) -> CorpusActionResult:
    if context.user is None or not state.active_saas_agent_id:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="SaaS Agent selection required")
    candidate = await learning_service.review(candidate_id=uuid.UUID(str(payload.get("candidate_id"))), saas_agent_id=state.active_saas_agent_id, status=review_status, reviewed_by=context.user.id, db=context.db)
    if candidate is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Learning candidate not found")
    state.node = AppNodeIds.LEARNING
    return CorpusActionResult(
        state=state,
        messages=[EntryGraphMessage(content=f"Learning candidate {review_status}.")],
        evidence=[{"type": "learning_reviewed", "candidate_id": str(candidate.id), "status": candidate.status}],
    )


def build_learning_handlers():
    return {
        AppActionIds.LEARNING_OPEN: learning_open,
        AppActionIds.LEARNING_POLICY_CANDIDATE_OPEN: learning_policy_candidate_open,
        AppActionIds.LEARNING_EXECUTION_TRACE_OPEN: learning_execution_trace_open,
        AppActionIds.LEARNING_ACTIVE_POLICY_OPEN: learning_active_policy_open,
        AppActionIds.LEARNING_APPROVE: learning_approve,
        AppActionIds.LEARNING_REJECT: learning_reject,
    }
