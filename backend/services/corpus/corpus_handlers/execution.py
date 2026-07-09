from __future__ import annotations

import uuid
from collections.abc import Mapping
from typing import Any

from fastapi import HTTPException, status

from backend.core.models import AgentExecutionTrace, GeneratedTool
from backend.core.schemas import CorpusGraphState, EntryGraphMessage
from backend.services.agent.rest_operator import (
    _candidate_from_trace,
    _candidate_summary_rows,
    _preview_body,
    _risk_value,
    create_execution_trace,
    execute_rest_tool,
    finalize_execution_trace,
    find_tool_candidates,
)
from backend.services.corpus.manifest import CorpusActionIds, CorpusNodeIds

from .types import CorpusActionContext, CorpusActionResult


async def execution_open(state: CorpusGraphState, payload: Mapping[str, Any], context: CorpusActionContext) -> CorpusActionResult:
    state.node = CorpusNodeIds.EXECUTION_PLANNING
    return CorpusActionResult(state=state)


async def execution_plan(state: CorpusGraphState, payload: Mapping[str, Any], context: CorpusActionContext) -> CorpusActionResult:
    if context.user is None or not state.active_saas_agent_id:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="SaaS Agent selection required")
    goal = str(payload.get("goal") or "").strip()
    if not goal:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="goal is required")
    candidates = await find_tool_candidates(message=goal, saas_agent_id=state.active_saas_agent_id, db=context.db, limit=5)
    if not candidates:
        state.node = CorpusNodeIds.RESULT_REVIEW
        return CorpusActionResult(state=state, messages=[EntryGraphMessage(content="No generated API tool matched that goal.")], evidence=[{"type": "execution_candidates", "candidates": []}])
    top = candidates[0]
    inputs, missing = extract_inputs(goal, top.tool)
    summary = _candidate_summary_rows(candidates)
    risk = _risk_value(top.tool.risk_level)
    if missing:
        trace = await create_execution_trace(candidate=top, inputs=inputs, missing=missing, candidate_summary=summary, status="needs_input", approval_state="not_required", route_node=CorpusNodeIds.NEEDS_INPUT, saas_agent_id=state.active_saas_agent_id, session_id=None, user_id=context.user.id, db=context.db)
        state.pending_trace_id = trace.id
        state.node = CorpusNodeIds.NEEDS_INPUT
        return CorpusActionResult(state=state, messages=[EntryGraphMessage(content=f"`{top.tool.name}` needs more input before execution.")], evidence=[{"type": "needs_input", "trace_id": str(trace.id), "missing": missing, "candidates": summary}])
    if risk != "read" or top.tool.requires_approval:
        trace = await create_execution_trace(candidate=top, inputs=inputs, missing=[], candidate_summary=summary, status="approval_required", approval_state="pending", route_node=CorpusNodeIds.APPROVAL_REQUIRED, saas_agent_id=state.active_saas_agent_id, session_id=None, user_id=context.user.id, db=context.db)
        state.pending_trace_id = trace.id
        state.node = CorpusNodeIds.APPROVAL_REQUIRED
        return CorpusActionResult(state=state, messages=[EntryGraphMessage(content=f"`{top.tool.name}` requires approval before execution.")], evidence=[{"type": "approval_required", "trace_id": str(trace.id), "risk": risk, "candidates": summary}])
    trace = await create_execution_trace(candidate=top, inputs=inputs, missing=[], candidate_summary=summary, status="executing", approval_state="not_required", route_node=CorpusNodeIds.EXECUTING, saas_agent_id=state.active_saas_agent_id, session_id=None, user_id=context.user.id, db=context.db)
    result = await execute_rest_tool(top, inputs, context.db)
    await finalize_execution_trace(trace, result, context.db)
    state.pending_trace_id = trace.id
    state.node = CorpusNodeIds.RESULT_REVIEW
    state.graph_context["execution_result"] = result
    return CorpusActionResult(state=state, messages=[EntryGraphMessage(content=f"Executed `{top.tool.name}` with status {result.get('status_code')}.")], evidence=[{"type": "execution_result", "trace_id": str(trace.id), "result": result, "candidates": summary, "preview": _preview_body(result.get("body"))}])


async def approval_approve(state: CorpusGraphState, payload: Mapping[str, Any], context: CorpusActionContext) -> CorpusActionResult:
    if context.user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Authentication required")
    trace_id = uuid.UUID(str(payload.get("trace_id") or state.pending_trace_id))
    trace = await context.db.get(AgentExecutionTrace, trace_id)
    if trace is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Trace not found")
    candidate = await _candidate_from_trace(context.db, trace)
    if candidate is None:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Trace candidate no longer exists")
    trace.status = "executing"
    trace.approval_state = "approved"
    trace.approved_by = context.user.id
    await context.db.commit()
    result = await execute_rest_tool(candidate, trace.inputs or {}, context.db)
    await finalize_execution_trace(trace, result, context.db)
    state.pending_trace_id = trace.id
    state.node = CorpusNodeIds.RESULT_REVIEW
    state.graph_context["execution_result"] = result
    return CorpusActionResult(state=state, messages=[EntryGraphMessage(content=f"Approved and executed `{trace.tool_name}`.")], evidence=[{"type": "approval_approved", "trace_id": str(trace.id), "result": result}])


async def approval_reject(state: CorpusGraphState, payload: Mapping[str, Any], context: CorpusActionContext) -> CorpusActionResult:
    trace_id = uuid.UUID(str(payload.get("trace_id") or state.pending_trace_id))
    trace = await context.db.get(AgentExecutionTrace, trace_id)
    if trace is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Trace not found")
    trace.status = "canceled"
    trace.approval_state = "rejected"
    trace.route_node = CorpusNodeIds.RESULT_REVIEW
    trace.approved_by = context.user.id if context.user else None
    await context.db.commit()
    state.pending_trace_id = trace.id
    state.node = CorpusNodeIds.RESULT_REVIEW
    return CorpusActionResult(state=state, messages=[EntryGraphMessage(content=f"Rejected execution trace `{str(trace.id)[:8]}`.")], evidence=[{"type": "approval_rejected", "trace_id": str(trace.id)}])


def extract_inputs(goal: str, tool: GeneratedTool) -> tuple[dict[str, Any], list[str]]:
    values: dict[str, Any] = {}
    for chunk in goal.split():
        if "=" in chunk:
            key, value = chunk.split("=", 1)
            values[key.strip()] = value.strip().strip(",")
    schema = (tool.function_schema or {}).get("parameters") or {}
    required = list(schema.get("required") or []) if isinstance(schema, dict) else []
    return values, [name for name in required if name not in values]


def build_execution_handlers():
    return {
        CorpusActionIds.EXECUTION_OPEN: execution_open,
        CorpusActionIds.EXECUTION_PLAN: execution_plan,
        CorpusActionIds.APPROVAL_APPROVE: approval_approve,
        CorpusActionIds.APPROVAL_REJECT: approval_reject,
    }
