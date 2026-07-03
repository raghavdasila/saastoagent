from __future__ import annotations

import asyncio
import copy
import json
import re
import time
import uuid
from contextlib import nullcontext
from dataclasses import dataclass, replace
from types import SimpleNamespace
from typing import Any, ContextManager

import httpx
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from backend.core.credentials import decrypt_value, inject_credentials
from backend.core.models import ActionNode, ActionNodeStatus, AgentExecutionTrace, AgentMessage, AgentSession, Connection, GeneratedTool, RiskLevel, ToolStatus
from backend.services.agent.execution_frames import (
    active_resource_context,
    augment_message_with_frame_context,
    build_inputs_from_frame,
    capture_result_frame,
    find_entity_reference,
    load_execution_frame,
    operation_frame_from_candidate,
    promote_active_resource,
    preserve_selected_entity,
    save_execution_frame,
)
from backend.services.agent.api_orchestration import (
    classify_missing_inputs,
    derive_parent_collection_path,
    extract_resource_id_from_result,
)
from backend.services.agent.learning_service import learning_service
from backend.services.agent.state_variables import (
    fill_inputs_from_pending_choice_variables,
    known_resource_collection_paths,
    pending_choice_prompt,
    pending_choice_target_path_for_message,
    remember_choice_variable,
    remember_resource_result_variables,
    resource_variable_name,
    resolve_dependency_id_from_variables,
    resolve_input_from_variables,
)
from backend.services.agent.timing import RequestTiming
from backend.services.toolrouter.adapter import ToolRouterAdapter, ToolRouterDecision, ToolRouterDecisionType
from backend.services.toolrouter import rank_generated_tools

_TOKEN_RE = re.compile(r"[a-z0-9_/-]+", re.IGNORECASE)
_EXECUTION_HINTS = {
    "get",
    "list",
    "find",
    "fetch",
    "show",
    "search",
    "create",
    "update",
    "delete",
    "send",
    "run",
    "execute",
    "call",
}
_COLLECTION_READ_TERMS = {"all", "available", "browse", "catalog", "filter", "find", "have", "inventory", "list", "menu", "offer", "offers", "search", "show", "what", "which"}
_READ_REFINEMENT_TERMS = {"browse", "called", "filter", "find", "list", "matching", "named", "narrow", "only", "search", "show"}
_WRITE_RISKS = {RiskLevel.write.value, RiskLevel.destructive.value, RiskLevel.financial.value}
_MAX_PUBLIC_FAILURE_RECOVERY_STEPS = 4


@dataclass
class ToolCandidate:
    tool: GeneratedTool
    action: ActionNode
    connection: Connection
    score: int
    reason: str


def _timing_span(timing: RequestTiming | None, name: str, **metadata: Any) -> ContextManager[None]:
    return timing.span(name, **metadata) if timing is not None else nullcontext()


async def run_rest_operator_turn(
    *,
    message: str,
    saas_agent_id: uuid.UUID,
    session_id: uuid.UUID | None = None,
    user_id: uuid.UUID | None = None,
    session: AgentSession | None = None,
    db: AsyncSession,
    emit,
    public_response: bool = False,
    timing: RequestTiming | None = None,
) -> str | None:
    with _timing_span(timing, "rest.approval_control_check"):
        approval_result = await _maybe_handle_trace_control(
            message=message,
            saas_agent_id=saas_agent_id,
            session_id=session_id,
            user_id=user_id,
            db=db,
            emit=emit,
            public_response=public_response,
        )
    if approval_result is not None:
        return approval_result

    if public_response and _is_generic_public_capability_message(message):
        return None

    with _timing_span(timing, "rest.execution_frame_resume_check"):
        frame_result = await _maybe_resume_execution_frame(
            message=message,
            saas_agent_id=saas_agent_id,
            session_id=session_id,
            user_id=user_id,
            session=session,
            db=db,
            emit=emit,
            public_response=public_response,
            timing=timing,
        )
    if frame_result is not None:
        return frame_result

    with _timing_span(timing, "rest.candidate_search", limit=5):
        candidates = await find_tool_candidates(message=message, saas_agent_id=saas_agent_id, db=db, limit=5)
    if not candidates:
        return None

    top = candidates[0]
    if top.score < 2 and not _looks_like_api_task(message):
        return None

    return await _route_and_maybe_execute(
        message=message,
        candidates=candidates,
        saas_agent_id=saas_agent_id,
        session_id=session_id,
        user_id=user_id,
        session=session,
        db=db,
        emit=emit,
        public_response=public_response,
        timing=timing,
    )


async def _maybe_resume_execution_frame(
    *,
    message: str,
    saas_agent_id: uuid.UUID,
    session_id: uuid.UUID | None,
    user_id: uuid.UUID | None,
    session: AgentSession | None,
    db: AsyncSession,
    emit,
    public_response: bool,
    timing: RequestTiming | None = None,
) -> str | None:
    with _timing_span(timing, "frame.load_and_entity_resolution"):
        frame = load_execution_frame(session)
        entity = find_entity_reference(message, frame)
    active_resource = active_resource_context(frame)
    read_refinement_path = _last_read_collection_path(frame) if _looks_like_read_refinement(message) else None
    if frame is None or (entity is None and active_resource is None and read_refinement_path is None):
        return None
    if _has_explicit_resource_id(message, "order"):
        order_candidate = await find_candidate_for_action_path(
            saas_agent_id=saas_agent_id,
            db=db,
            action_path="/store/orders/{id}",
            allowed_methods={"GET"},
        )
        if order_candidate is not None:
            return await _route_and_maybe_execute(
                message=message,
                candidates=[order_candidate],
                saas_agent_id=saas_agent_id,
                session_id=session_id,
                user_id=user_id,
                session=session,
                db=db,
                emit=emit,
                public_response=public_response,
                frame=frame,
                selected_entity=entity,
                timing=timing,
            )
    if (
        entity is None
        and _looks_like_collection_read_request(message)
        and not _looks_like_active_resource_read_dependency(message)
        and not _looks_like_active_resource_read_request(message, active_resource)
    ):
        return None
    pending_choice_path = pending_choice_target_path_for_message(frame, message)
    if pending_choice_path:
        pending_candidate = await find_candidate_for_action_path(
            saas_agent_id=saas_agent_id,
            db=db,
            action_path=pending_choice_path,
        )
        if pending_candidate is not None:
            return await _route_and_maybe_execute(
                message=message,
                routed_message=augment_message_with_frame_context(message, entity or {}, frame),
                candidates=[pending_candidate],
                saas_agent_id=saas_agent_id,
                session_id=session_id,
                user_id=user_id,
                session=session,
                db=db,
                emit=emit,
                public_response=public_response,
                frame=frame,
                selected_entity=entity,
                timing=timing,
            )
    routed_message = (
        _augment_message_with_read_collection_context(message, frame, read_refinement_path)
        if entity is None and active_resource is None and read_refinement_path is not None
        else augment_message_with_frame_context(message, entity or {}, frame)
    )
    with _timing_span(timing, "rest.frame_candidate_search", limit=50):
        candidates = await find_tool_candidates(message=routed_message, saas_agent_id=saas_agent_id, db=db, limit=50)
    if not candidates:
        return None
    return await _route_and_maybe_execute(
        message=message,
        routed_message=routed_message,
        candidates=candidates,
        saas_agent_id=saas_agent_id,
        session_id=session_id,
        user_id=user_id,
        session=session,
        db=db,
        emit=emit,
        public_response=public_response,
        frame=frame,
        selected_entity=entity,
        timing=timing,
    )


async def _route_and_maybe_execute(
    *,
    message: str,
    candidates: list[ToolCandidate],
    saas_agent_id: uuid.UUID,
    session_id: uuid.UUID | None,
    user_id: uuid.UUID | None,
    session: AgentSession | None,
    db: AsyncSession,
    emit,
    public_response: bool,
    routed_message: str | None = None,
    frame: dict[str, Any] | None = None,
    selected_entity: dict[str, Any] | None = None,
    timing: RequestTiming | None = None,
) -> str:
    if frame is not None:
        with _timing_span(timing, "rest.frame_candidate_rerank"):
            candidates = _rerank_candidates_for_frame(message=message, candidates=candidates, frame=frame)
    top = candidates[0]
    candidate_summary_rows = _candidate_summary_rows(candidates)
    risk = _risk_value(top.tool.risk_level)
    with _timing_span(timing, "rest.build_inputs"):
        inputs, missing = _build_inputs(message, top.action, top.tool)
    if frame is not None:
        with _timing_span(timing, "rest.inputs.frame_fill"):
            inputs, missing = build_inputs_from_frame(
                message=message,
                action=top.action,
                tool=top.tool,
                frame=frame,
                base_inputs=inputs,
            )
            inputs, missing = _fill_inputs_from_variables(inputs=inputs, missing=missing, action=top.action, frame=frame)
            inputs, missing = fill_inputs_from_pending_choice_variables(message=message, inputs=inputs, missing=missing, frame=frame)
    with _timing_span(timing, "router.decision"):
        decision = ToolRouterAdapter().decide(
            message=routed_message or message,
            candidates=candidates,
            inputs=inputs,
            missing=missing,
        )

    if decision.type in {ToolRouterDecisionType.SHOW_TOPK, ToolRouterDecisionType.BLOCK_UNSAFE}:
        return _format_router_decision(decision)

    if decision.type == ToolRouterDecisionType.ASK_PARAM:
        if public_response:
            public_missing_result = await _handle_public_missing_inputs(
                message=message,
                top=top,
                inputs=inputs,
                missing=missing,
                candidate_summary_rows=candidate_summary_rows,
                saas_agent_id=saas_agent_id,
                session_id=session_id,
                user_id=user_id,
                session=session,
                db=db,
                frame=frame,
                selected_entity=selected_entity,
                timing=timing,
            )
            if public_missing_result is not None:
                return public_missing_result
        trace = await create_execution_trace(
            candidate=top,
            inputs=inputs,
            missing=missing,
            candidate_summary=candidate_summary_rows,
            status="needs_input",
            approval_state="not_required",
            route_node="needs_input",
            saas_agent_id=saas_agent_id,
            session_id=session_id,
            user_id=user_id,
            db=db,
        )
        if selected_entity is not None:
            await save_execution_frame(
                session,
                operation_frame_from_candidate(
                    base_frame=frame,
                    selected_entity=selected_entity,
                    tool=top.tool,
                    action=top.action,
                    inputs=inputs,
                    missing=missing,
                ),
                db,
            )
        content = (
            "I need one more detail before I can do that.\n\n"
            f"Please provide: {_format_missing_input_names(missing, top.action)}.\n\n"
            "Once you provide that, I can continue."
        )
        if not public_response:
            content = content.replace("\n\nOnce you provide", f"\n\nTrace: `{str(trace.id)[:8]}`\n\nOnce you provide")
        return content

    if decision.type == ToolRouterDecisionType.ASK_POLICY:
        if public_response:
            public_policy_result = await _handle_public_active_resource_policy(
                message=message,
                top=top,
                inputs=inputs,
                candidate_summary_rows=candidate_summary_rows,
                saas_agent_id=saas_agent_id,
                session_id=session_id,
                user_id=user_id,
                session=session,
                db=db,
                frame=frame,
                selected_entity=selected_entity,
                timing=timing,
            )
            if public_policy_result is not None:
                return public_policy_result
            if await _approved_public_policy_for_action(
                saas_agent_id=saas_agent_id,
                action_path=str(top.action.path or ""),
                db=db,
                timing=timing,
            ):
                return await _execute_public_target_with_internal_id(
                    message=message,
                    top=top,
                    inputs=inputs,
                    candidate_summary_rows=candidate_summary_rows,
                    saas_agent_id=saas_agent_id,
                    session_id=session_id,
                    user_id=user_id,
                    session=session,
                    db=db,
                    frame=frame,
                    selected_entity=selected_entity,
                    timing=timing,
                )
        trace = await create_execution_trace(
            candidate=top,
            inputs=inputs,
            missing=missing,
            candidate_summary=candidate_summary_rows,
            status="approval_required",
            approval_state="pending",
            route_node="approval_required",
            saas_agent_id=saas_agent_id,
            session_id=session_id,
            user_id=user_id,
            db=db,
        )
        if selected_entity is not None:
            await save_execution_frame(
                session,
                operation_frame_from_candidate(
                    base_frame=frame,
                    selected_entity=selected_entity,
                    tool=top.tool,
                    action=top.action,
                    inputs=inputs,
                    missing=missing,
                ),
                db,
            )
        trace_token = str(trace.id)[:8]
        if not public_response:
            await emit(
                "approval_required",
                {
                    "trace_id": str(trace.id),
                    "trace_token": trace_token,
                    "tool": top.tool.name,
                    "risk": risk,
                    "connection": top.connection.name,
                    "inputs": inputs,
                    "missing": missing,
                },
            )
        if public_response:
            return (
                "This request needs approval before I can run it.\n\n"
                "Ask the agent owner to approve the action, or request a read-only preview instead."
            )
        return (
            "I found the matching API action, but it needs approval before execution.\n\n"
            f"Risk: `{risk}`\n"
            f"Trace: `{trace_token}`\n\n"
            f"Reply `approve {trace_token}` to execute it, or `cancel {trace_token}` to reject it."
        )

    with _timing_span(timing, "trace.create"):
        trace = await create_execution_trace(
            candidate=top,
            inputs=inputs,
            missing=[],
            candidate_summary=candidate_summary_rows,
            status="executing",
            approval_state="not_required",
            route_node="executing",
            saas_agent_id=saas_agent_id,
            session_id=session_id,
            user_id=user_id,
            db=db,
        )
    if not public_response:
        await emit(
            "execution_planned",
            {
                "trace_id": str(trace.id),
                "trace_token": str(trace.id)[:8],
                "tool": top.tool.name,
                "risk": risk,
                "inputs": inputs,
            },
        )
    call_id = uuid.uuid4().hex[:8]
    if not public_response:
        await emit("tool_start", {"tool_name": top.tool.name, "call_id": call_id, "inputs": inputs})
    with _timing_span(timing, "api.execute", method=str(top.action.method or ""), path=str(top.action.path or "")):
        result = await execute_rest_tool(top, inputs, db)
    with _timing_span(timing, "trace.finalize"):
        await finalize_execution_trace(trace, result, db)
    if result.get("error"):
        if selected_entity is not None:
            await save_execution_frame(
                session,
                operation_frame_from_candidate(
                    base_frame=frame,
                    selected_entity=selected_entity,
                    tool=top.tool,
                    action=top.action,
                    inputs=inputs,
                    missing=[],
                ),
                db,
            )
    else:
        next_frame = capture_result_frame(message=message, tool=top.tool, action=top.action, result=result)
        if frame is not None and active_resource_context(frame) is not None:
            next_frame = _preserve_active_resource_context(next_frame, frame)
        if selected_entity is not None:
            next_frame = preserve_selected_entity(next_frame or frame or {}, selected_entity, message=message)
        await save_execution_frame(session, next_frame, db)
    output_text = json.dumps(result, default=str)[:5000]
    if not public_response:
        await emit("tool_end", {"call_id": call_id, "output": output_text})

    if result.get("error"):
        return _format_execution_failure(
            tool_name=top.tool.name,
            result=result,
            trace_token=str(trace.id)[:8],
            public_response=public_response,
        )

    if public_response:
        return _format_public_execution_success(result=result, method=top.action.method)

    return (
        "Here’s what I found.\n\n"
        f"Status: {result.get('status_code')}\n"
        f"Duration: {result.get('duration_ms')} ms\n\n"
        f"Trace: `{str(trace.id)[:8]}`\n\n"
        f"Result preview:\n```json\n{_preview_body_json(result.get('body'))}\n```\n\n"
        "You can ask me to check another item or narrow the result."
    )


async def _handle_public_missing_inputs(
    *,
    message: str,
    top: ToolCandidate,
    inputs: dict[str, Any],
    missing: list[str],
    candidate_summary_rows: list[dict[str, Any]],
    saas_agent_id: uuid.UUID,
    session_id: uuid.UUID | None,
    user_id: uuid.UUID | None,
    session: AgentSession | None,
    db: AsyncSession,
    frame: dict[str, Any] | None,
    selected_entity: dict[str, Any] | None,
    timing: RequestTiming | None = None,
) -> str | None:
    with _timing_span(timing, "inputs.missing_classification"):
        classified = classify_missing_inputs(missing, action=top.action)
    if not classified.internal:
        return None

    if classified.user_facing:
        public_missing = [item.name for item in classified.user_facing]
        await create_execution_trace(
            candidate=top,
            inputs=inputs,
            missing=public_missing,
            candidate_summary=candidate_summary_rows,
            status="needs_input",
            approval_state="not_required",
            route_node="needs_input",
            saas_agent_id=saas_agent_id,
            session_id=session_id,
            user_id=user_id,
            db=db,
        )
        await _save_operation_frame(
            session=session,
            frame=frame,
            selected_entity=selected_entity,
            tool=top.tool,
            action=top.action,
            inputs=inputs,
            missing=missing,
            db=db,
        )
        requested = ", ".join(item.public_label for item in classified.user_facing)
        return (
            "I need one more detail before I can do that.\n\n"
            f"Please provide: {requested}.\n\n"
            "Once you provide that, I can continue."
        )

    internal_names = [item.name for item in classified.internal]
    parent_collection_path = _first_parent_collection_path(top.action.path, internal_names)
    if parent_collection_path is None:
        await _record_public_policy_gap_trace(
            top=top,
            inputs=inputs,
            missing=missing,
            candidate_summary_rows=candidate_summary_rows,
            saas_agent_id=saas_agent_id,
            session_id=session_id,
            user_id=user_id,
            session=session,
            frame=frame,
            selected_entity=selected_entity,
            db=db,
        )
        return _public_policy_needed_message()

    with _timing_span(timing, "dependency.find_candidate", parent_collection_path=parent_collection_path):
        dependency_candidate = await find_dependency_candidate_for_path(
            saas_agent_id=saas_agent_id,
            db=db,
            parent_collection_path=parent_collection_path,
        )
    action_paths = [getattr(getattr(dependency_candidate, "action", None), "path", parent_collection_path), top.action.path]
    with _timing_span(timing, "policy.lookup"):
        approved_policy = await learning_service.approved_domain_policy(saas_agent_id=saas_agent_id, action_paths=action_paths, db=db)

    with _timing_span(timing, "dependency.frame_reuse_check"):
        stored_dependency_id = resolve_dependency_id_from_variables(frame, parent_collection_path)
    if stored_dependency_id and approved_policy is not None:
        return await _execute_public_target_with_internal_id(
            message=message,
            top=top,
            inputs={**inputs, internal_names[0]: stored_dependency_id},
            candidate_summary_rows=candidate_summary_rows,
            saas_agent_id=saas_agent_id,
            session_id=session_id,
            user_id=user_id,
            session=session,
            db=db,
            frame=frame,
            selected_entity=selected_entity,
            timing=timing,
        )

    if dependency_candidate is None:
        await _record_public_policy_gap_trace(
            top=top,
            inputs=inputs,
            missing=missing,
            candidate_summary_rows=candidate_summary_rows,
            saas_agent_id=saas_agent_id,
            session_id=session_id,
            user_id=user_id,
            session=session,
            frame=frame,
            selected_entity=selected_entity,
            db=db,
        )
        return _public_policy_needed_message()

    trace = await create_execution_trace(
        candidate=top,
        inputs=inputs,
        missing=missing,
        candidate_summary=candidate_summary_rows,
        status="needs_input" if approved_policy is None else "executing",
        approval_state="not_required",
        route_node="internal_dependency_policy" if approved_policy is None else "executing",
        saas_agent_id=saas_agent_id,
        session_id=session_id,
        user_id=user_id,
        db=db,
    )
    await _save_operation_frame(
        session=session,
        frame=frame,
        selected_entity=selected_entity,
        tool=top.tool,
        action=top.action,
        inputs=inputs,
        missing=missing,
        db=db,
    )
    if approved_policy is None:
        with _timing_span(timing, "policy.candidate_create"):
            await learning_service.propose_domain_policy_gap(
                trace=trace,
                target_candidate=top,
                dependency_candidate=dependency_candidate,
                missing_internal_inputs=internal_names,
                db=db,
            )
        return _public_policy_needed_message()

    with _timing_span(timing, "dependency.execute"):
        dependency_result = await _execute_public_dependency_candidate(
            dependency_candidate=dependency_candidate,
            candidate_summary_rows=candidate_summary_rows,
            saas_agent_id=saas_agent_id,
            session_id=session_id,
            user_id=user_id,
            db=db,
            timing=timing,
        )
    if dependency_result.get("error"):
        return _format_execution_failure(
            tool_name=dependency_candidate.tool.name,
            result=dependency_result,
            trace_token=str(trace.id)[:8],
            public_response=True,
        )
    dependency_id = extract_resource_id_from_result(dependency_result)
    if not dependency_id:
        return "I could not complete that because the connected API did not return the internal resource I needed."
    next_frame = remember_resource_result_variables(
        frame,
        collection_path=parent_collection_path,
        result=dependency_result,
        origin={
            "method": str(dependency_candidate.action.method or ""),
            "path": str(dependency_candidate.action.path or ""),
            "tool_name": str(dependency_candidate.tool.name or ""),
        },
    )
    next_frame = promote_active_resource(
        next_frame,
        collection_path=parent_collection_path,
        resource_id=dependency_id,
        source_action_path=str(top.action.path or ""),
    )
    if selected_entity is not None:
        next_frame = preserve_selected_entity(next_frame, selected_entity, message=message)
    await save_execution_frame(session, next_frame, db)
    return await _execute_public_target_with_internal_id(
        message=message,
        top=top,
        inputs={**inputs, internal_names[0]: dependency_id},
        candidate_summary_rows=candidate_summary_rows,
        saas_agent_id=saas_agent_id,
        session_id=session_id,
        user_id=user_id,
        session=session,
        db=db,
        frame=next_frame,
        selected_entity=selected_entity,
        existing_trace=trace,
        timing=timing,
    )


async def _approved_public_policy_for_action(
    *,
    saas_agent_id: uuid.UUID,
    action_path: str,
    db: AsyncSession,
    timing: RequestTiming | None = None,
) -> bool:
    if not action_path:
        return False
    with _timing_span(timing, "policy.lookup"):
        approved_policy = await learning_service.approved_domain_policy(
            saas_agent_id=saas_agent_id,
            action_paths=[action_path],
            db=db,
        )
    return approved_policy is not None


async def _handle_public_active_resource_policy(
    *,
    message: str,
    top: ToolCandidate,
    inputs: dict[str, Any],
    candidate_summary_rows: list[dict[str, Any]],
    saas_agent_id: uuid.UUID,
    session_id: uuid.UUID | None,
    user_id: uuid.UUID | None,
    session: AgentSession | None,
    db: AsyncSession,
    frame: dict[str, Any] | None,
    selected_entity: dict[str, Any] | None,
    timing: RequestTiming | None = None,
) -> str | None:
    active_resource = active_resource_context(frame)
    if active_resource is None:
        return None
    internal_names = _active_resource_input_names(top, inputs, active_resource)
    if not internal_names:
        return None
    action_paths = [str(top.action.path or "")]
    with _timing_span(timing, "policy.lookup"):
        approved_policy = await learning_service.approved_domain_policy(saas_agent_id=saas_agent_id, action_paths=action_paths, db=db)
    if approved_policy is not None:
        return await _execute_public_target_with_internal_id(
            message=message,
            top=top,
            inputs=inputs,
            candidate_summary_rows=candidate_summary_rows,
            saas_agent_id=saas_agent_id,
            session_id=session_id,
            user_id=user_id,
            session=session,
            db=db,
            frame=frame,
            selected_entity=selected_entity,
            timing=timing,
        )

    trace = await create_execution_trace(
        candidate=top,
        inputs=inputs,
        missing=internal_names,
        candidate_summary=candidate_summary_rows,
        status="needs_input",
        approval_state="not_required",
        route_node="internal_dependency_policy",
        saas_agent_id=saas_agent_id,
        session_id=session_id,
        user_id=user_id,
        db=db,
    )
    await _save_operation_frame(
        session=session,
        frame=frame,
        selected_entity=selected_entity,
        tool=top.tool,
        action=top.action,
        inputs=inputs,
        missing=internal_names,
        db=db,
    )
    with _timing_span(timing, "policy.candidate_create"):
        await learning_service.propose_domain_policy_gap(
            trace=trace,
            target_candidate=top,
            dependency_candidate=None,
            missing_internal_inputs=internal_names,
            db=db,
        )
    return _public_policy_needed_message()


async def find_dependency_candidate_for_path(
    *,
    saas_agent_id: uuid.UUID,
    db: AsyncSession,
    parent_collection_path: str,
) -> ToolCandidate | None:
    result = await db.execute(
        select(GeneratedTool, ActionNode, Connection)
        .join(ActionNode, GeneratedTool.action_node_id == ActionNode.id)
        .join(Connection, GeneratedTool.connection_id == Connection.id)
        .options(selectinload(Connection.credentials))
        .where(
            GeneratedTool.saas_agent_id == saas_agent_id,
            ActionNode.path == parent_collection_path,
        )
    )
    rows = result.all()
    candidates = [
        ToolCandidate(tool=tool, action=action, connection=connection, score=0, reason="internal_dependency")
        for tool, action, connection in rows
        if str(getattr(action, "method", "") or "").upper() == "POST"
    ]
    if not candidates:
        return None
    return sorted(candidates, key=lambda row: (_required_count(row.tool), row.tool.name))[0]


async def find_candidate_for_action_path(
    *,
    saas_agent_id: uuid.UUID,
    db: AsyncSession,
    action_path: str,
    allowed_methods: set[str] | None = None,
) -> ToolCandidate | None:
    methods = allowed_methods or {"POST", "PUT", "PATCH", "DELETE"}
    result = await db.execute(
        select(GeneratedTool, ActionNode, Connection)
        .join(ActionNode, GeneratedTool.action_node_id == ActionNode.id)
        .join(Connection, GeneratedTool.connection_id == Connection.id)
        .options(selectinload(Connection.credentials))
        .where(
            GeneratedTool.saas_agent_id == saas_agent_id,
            ActionNode.path == action_path,
        )
    )
    rows = result.all()
    candidates = [
        ToolCandidate(tool=tool, action=action, connection=connection, score=100, reason="pending_internal_choice")
        for tool, action, connection in rows
        if str(getattr(action, "method", "") or "").upper() in methods
    ]
    if not candidates:
        return None
    return sorted(candidates, key=lambda row: (_required_count(row.tool), row.tool.name))[0]


async def _execute_public_dependency_candidate(
    *,
    dependency_candidate: ToolCandidate,
    candidate_summary_rows: list[dict[str, Any]],
    saas_agent_id: uuid.UUID,
    session_id: uuid.UUID | None,
    user_id: uuid.UUID | None,
    db: AsyncSession,
    timing: RequestTiming | None = None,
) -> dict[str, Any]:
    dependency_inputs, dependency_missing = _build_inputs("", dependency_candidate.action, dependency_candidate.tool)
    if dependency_missing:
        return {
            "status_code": 0,
            "body": None,
            "duration_ms": 0,
            "error": "Internal dependency action has unresolved required inputs.",
        }
    dependency_trace = await create_execution_trace(
        candidate=dependency_candidate,
        inputs=dependency_inputs,
        missing=[],
        candidate_summary=candidate_summary_rows,
        status="executing",
        approval_state="approved_by_policy",
        route_node="internal_dependency",
        saas_agent_id=saas_agent_id,
        session_id=session_id,
        user_id=user_id,
        db=db,
    )
    with _timing_span(timing, "api.execute", method=str(dependency_candidate.action.method or ""), path=str(dependency_candidate.action.path or "")):
        result = await execute_rest_tool(dependency_candidate, dependency_inputs, db)
    with _timing_span(timing, "trace.finalize", tool=str(dependency_candidate.tool.name or "")):
        await finalize_execution_trace(dependency_trace, result, db)
    return result


async def _execute_public_target_with_internal_id(
    *,
    message: str,
    top: ToolCandidate,
    inputs: dict[str, Any],
    candidate_summary_rows: list[dict[str, Any]],
    saas_agent_id: uuid.UUID,
    session_id: uuid.UUID | None,
    user_id: uuid.UUID | None,
    session: AgentSession | None,
    db: AsyncSession,
    frame: dict[str, Any] | None,
    selected_entity: dict[str, Any] | None,
    existing_trace: AgentExecutionTrace | None = None,
    timing: RequestTiming | None = None,
    recovery_depth: int = 0,
    recovery_attempted_paths: set[str] | None = None,
) -> str:
    trace = existing_trace or await create_execution_trace(
        candidate=top,
        inputs=inputs,
        missing=[],
        candidate_summary=candidate_summary_rows,
        status="executing",
        approval_state="approved_by_policy",
        route_node="executing",
        saas_agent_id=saas_agent_id,
        session_id=session_id,
        user_id=user_id,
        db=db,
    )
    if existing_trace is not None:
        trace.inputs = inputs
        trace.missing_inputs = []
        trace.status = "executing"
        trace.approval_state = "approved_by_policy"
        trace.route_node = "executing"
        await db.commit()
    with _timing_span(timing, "api.execute", method=str(top.action.method or ""), path=str(top.action.path or "")):
        result = await execute_rest_tool(top, inputs, db)
    with _timing_span(timing, "trace.finalize", tool=str(top.tool.name or "")):
        await finalize_execution_trace(trace, result, db)
    if result.get("error") and recovery_depth < _MAX_PUBLIC_FAILURE_RECOVERY_STEPS:
        recovery_result = await _maybe_handle_public_execution_failure_recovery(
            message=message,
            failed_candidate=top,
            failed_inputs=inputs,
            failed_result=result,
            candidate_summary_rows=candidate_summary_rows,
            saas_agent_id=saas_agent_id,
            session_id=session_id,
            user_id=user_id,
            session=session,
            db=db,
            frame=frame,
            selected_entity=selected_entity,
            timing=timing,
            recovery_depth=recovery_depth,
            recovery_attempted_paths=recovery_attempted_paths or set(),
        )
        if recovery_result is not None:
            return recovery_result
    if result.get("error"):
        return _format_execution_failure(tool_name=top.tool.name, result=result, trace_token=str(trace.id)[:8], public_response=True)
    next_frame = capture_result_frame(message=message, tool=top.tool, action=top.action, result=result)
    active_resource = active_resource_context(frame)
    result_collection_path = _result_collection_path_for_frame(candidate=top, active_resource=active_resource, result=result)
    if result_collection_path is not None:
        next_frame = remember_resource_result_variables(
            next_frame or frame,
            collection_path=result_collection_path,
            result=result,
            origin={
                "method": str(top.action.method or ""),
                "path": str(top.action.path or ""),
                "tool_name": str(top.tool.name or ""),
            },
        )
        should_promote_result = _terminal_result_collection_path(str(top.action.path or ""), result) == result_collection_path
        result_resource_id = resolve_dependency_id_from_variables(next_frame, result_collection_path)
        if should_promote_result and result_resource_id:
            next_frame = promote_active_resource(
                next_frame,
                collection_path=result_collection_path,
                resource_id=result_resource_id,
                source_action_path=str(top.action.path or ""),
            )
            next_frame["active_resource"]["reason"] = "workflow_result"
        elif active_resource is not None and result_collection_path != active_resource["collection_path"]:
            next_frame["active_resource"] = active_resource
            active_ref = resource_variable_name(active_resource["collection_path"], "id")
            if isinstance(next_frame.get("variables"), dict) and active_ref in next_frame["variables"]:
                next_frame["active_resource_ref"] = active_ref
    if selected_entity is not None:
        next_frame = preserve_selected_entity(next_frame or frame or {}, selected_entity, message=message)
    await save_execution_frame(session, next_frame or frame, db)
    return _format_public_execution_success(result=result, method=top.action.method)


async def _maybe_handle_public_execution_failure_recovery(
    *,
    message: str,
    failed_candidate: ToolCandidate,
    failed_inputs: dict[str, Any],
    failed_result: dict[str, Any],
    candidate_summary_rows: list[dict[str, Any]],
    saas_agent_id: uuid.UUID,
    session_id: uuid.UUID | None,
    user_id: uuid.UUID | None,
    session: AgentSession | None,
    db: AsyncSession,
    frame: dict[str, Any] | None,
    selected_entity: dict[str, Any] | None,
    timing: RequestTiming | None = None,
    recovery_depth: int = 0,
    recovery_attempted_paths: set[str] | None = None,
) -> str | None:
    if frame is None or active_resource_context(frame) is None:
        return None
    error_detail = _execution_error_detail(failed_result)
    if not error_detail:
        return None
    recovery_message = _recovery_candidate_message(message=message, error_detail=error_detail, frame=frame, failed_candidate=failed_candidate)
    with _timing_span(timing, "rest.failure_recovery_candidate_search", limit=50):
        candidates = await find_tool_candidates(message=recovery_message, saas_agent_id=saas_agent_id, db=db, limit=50)
    candidates = [
        candidate
        for candidate in candidates
        if candidate.action.id != failed_candidate.action.id
        and str(getattr(candidate.action, "method", "") or "").upper() in {"POST", "PUT", "PATCH", "DELETE"}
        and str(getattr(candidate.action, "path", "") or "") not in (recovery_attempted_paths or set())
    ]
    if not candidates:
        return None
    candidates = _rerank_recovery_candidates(
        message=recovery_message,
        error_detail=error_detail,
        candidates=candidates,
        frame=frame,
    )
    recovery = candidates[0]
    recovery_path = str(getattr(recovery.action, "path", "") or "")
    next_attempted_paths = set(recovery_attempted_paths or set())
    if recovery_path:
        next_attempted_paths.add(recovery_path)
    inputs, missing = _build_inputs(recovery_message, recovery.action, recovery.tool)
    inputs, missing = build_inputs_from_frame(
        message=recovery_message,
        action=recovery.action,
        tool=recovery.tool,
        frame=frame,
        base_inputs=inputs,
    )
    inputs, missing = _fill_inputs_from_variables(inputs=inputs, missing=missing, action=recovery.action, frame=frame)
    inputs, missing = fill_inputs_from_pending_choice_variables(message=message, inputs=inputs, missing=missing, frame=frame)
    inputs, missing = await _resolve_opaque_inputs_from_generated_reads(
        message=recovery_message,
        candidate=recovery,
        inputs=inputs,
        missing=missing,
        candidates=candidates,
        saas_agent_id=saas_agent_id,
        session_id=session_id,
        user_id=user_id,
        db=db,
        frame=frame,
        timing=timing,
    )
    choice_prompt = pending_choice_prompt(frame, missing)
    if choice_prompt:
        await save_execution_frame(session, frame, db)
        return choice_prompt
    active_resource = active_resource_context(frame)
    internal_names = _active_resource_input_names(recovery, inputs, active_resource or {})
    internal_names.extend(name for name in _dependency_input_names(recovery.action, inputs, frame) if name not in internal_names)
    if missing:
        classified = classify_missing_inputs(missing, action=recovery.action)
        if classified.user_facing:
            return None
        internal_names.extend(item.name for item in classified.internal if item.name not in internal_names)
    if not internal_names:
        return None

    action_paths = [str(recovery.action.path or "")]
    with _timing_span(timing, "policy.lookup"):
        approved_policy = await learning_service.approved_domain_policy(saas_agent_id=saas_agent_id, action_paths=action_paths, db=db)
    trace = await create_execution_trace(
        candidate=recovery,
        inputs=inputs,
        missing=missing or internal_names,
        candidate_summary=_candidate_summary_rows(candidates) or candidate_summary_rows,
        status="needs_input" if approved_policy is None else "executing",
        approval_state="not_required" if approved_policy is None else "approved_by_policy",
        route_node="internal_dependency_policy" if approved_policy is None else "executing",
        saas_agent_id=saas_agent_id,
        session_id=session_id,
        user_id=user_id,
        db=db,
    )
    await _save_operation_frame(
        session=session,
        frame=frame,
        selected_entity=selected_entity,
        tool=recovery.tool,
        action=recovery.action,
        inputs=inputs,
        missing=missing or internal_names,
        db=db,
    )
    if approved_policy is None:
        with _timing_span(timing, "policy.candidate_create"):
            await learning_service.propose_domain_policy_gap(
                trace=trace,
                target_candidate=recovery,
                dependency_candidate=None,
                missing_internal_inputs=internal_names,
                db=db,
            )
        return _public_policy_needed_message()

    with _timing_span(timing, "api.execute", method=str(recovery.action.method or ""), path=str(recovery.action.path or "")):
        recovery_result = await execute_rest_tool(recovery, inputs, db)
    with _timing_span(timing, "trace.finalize", tool=str(recovery.tool.name or "")):
        await finalize_execution_trace(trace, recovery_result, db)
    if recovery_result.get("error"):
        return _format_execution_failure(tool_name=recovery.tool.name, result=recovery_result, trace_token=str(trace.id)[:8], public_response=True)

    next_frame = frame
    recovery_collection_path = _created_collection_path(recovery)
    recovery_id = extract_resource_id_from_result(recovery_result)
    if recovery_collection_path and recovery_id:
        next_frame = remember_resource_result_variables(
            next_frame,
            collection_path=recovery_collection_path,
            result=recovery_result,
            origin={
                "method": str(recovery.action.method or ""),
                "path": str(recovery.action.path or ""),
                "tool_name": str(recovery.tool.name or ""),
            },
        )
    if selected_entity is not None:
        next_frame = preserve_selected_entity(next_frame or {}, selected_entity, message=message)
    await save_execution_frame(session, next_frame, db)

    return await _execute_public_target_with_internal_id(
        message=message,
        top=failed_candidate,
        inputs=failed_inputs,
        candidate_summary_rows=candidate_summary_rows,
        saas_agent_id=saas_agent_id,
        session_id=session_id,
        user_id=user_id,
        session=session,
        db=db,
        frame=next_frame,
        selected_entity=selected_entity,
        timing=timing,
        recovery_depth=recovery_depth + 1,
        recovery_attempted_paths=next_attempted_paths,
    )


async def _resolve_opaque_inputs_from_generated_reads(
    *,
    message: str,
    candidate: ToolCandidate,
    inputs: dict[str, Any],
    missing: list[str],
    candidates: list[ToolCandidate],
    saas_agent_id: uuid.UUID,
    session_id: uuid.UUID | None,
    user_id: uuid.UUID | None,
    db: AsyncSession,
    frame: dict[str, Any] | None,
    timing: RequestTiming | None = None,
) -> tuple[dict[str, Any], list[str]]:
    if not missing or not isinstance(frame, dict):
        return inputs, missing
    next_inputs = dict(inputs)
    remaining: list[str] = []
    for name in missing:
        string_name = str(name)
        if not _is_opaque_id_input(string_name):
            remaining.append(string_name)
            continue
        resolved = await _resolve_single_opaque_input_from_generated_reads(
            input_name=string_name,
            message=message,
            target_candidate=candidate,
            candidate_summary_rows=_candidate_summary_rows(candidates),
            saas_agent_id=saas_agent_id,
            session_id=session_id,
            user_id=user_id,
            db=db,
            frame=frame,
            timing=timing,
        )
        if resolved is None:
            remaining.append(string_name)
            continue
        next_inputs[string_name] = resolved
    return next_inputs, remaining


async def _resolve_single_opaque_input_from_generated_reads(
    *,
    input_name: str,
    message: str,
    target_candidate: ToolCandidate,
    candidate_summary_rows: list[dict[str, Any]],
    saas_agent_id: uuid.UUID,
    session_id: uuid.UUID | None,
    user_id: uuid.UUID | None,
    db: AsyncSession,
    frame: dict[str, Any],
    timing: RequestTiming | None = None,
) -> str | None:
    noun = _noun_from_id_input(input_name)
    if not noun:
        return None
    lookup_message = " ".join(
        [
            f"list {noun} {noun}s",
            input_name,
            str(getattr(target_candidate.action, "description", "") or ""),
            str(getattr(target_candidate.action, "path", "") or ""),
        ]
    )
    with _timing_span(timing, "resolver.opaque_candidate_search", input_name=input_name, noun=noun):
        read_candidates = await find_tool_candidates(message=lookup_message, saas_agent_id=saas_agent_id, db=db, limit=50)
    read_candidates = _merge_resolver_candidates(
        read_candidates,
        await _find_read_resolver_candidates_by_noun(
            input_name=input_name,
            noun=noun,
            saas_agent_id=saas_agent_id,
            db=db,
            limit=50,
        ),
    )
    read_candidates = _rank_read_resolver_candidates(input_name=input_name, noun=noun, candidates=read_candidates, frame=frame)
    for read_candidate in read_candidates:
        read_inputs, read_missing = _build_inputs(lookup_message, read_candidate.action, read_candidate.tool)
        read_inputs, read_missing = build_inputs_from_frame(
            message=lookup_message,
            action=read_candidate.action,
            tool=read_candidate.tool,
            frame=frame,
            base_inputs=read_inputs,
        )
        read_inputs, read_missing = _fill_inputs_from_variables(inputs=read_inputs, missing=read_missing, action=read_candidate.action, frame=frame)
        read_inputs, read_missing = _fill_inputs_from_frame_fields(inputs=read_inputs, missing=read_missing, frame=frame)
        if read_missing:
            continue
        trace = await create_execution_trace(
            candidate=read_candidate,
            inputs=read_inputs,
            missing=[],
            candidate_summary=_candidate_summary_rows(read_candidates) or candidate_summary_rows,
            status="executing",
            approval_state="not_required",
            route_node="internal_resolver",
            saas_agent_id=saas_agent_id,
            session_id=session_id,
            user_id=user_id,
            db=db,
        )
        with _timing_span(timing, "resolver.opaque_execute", input_name=input_name, method=str(read_candidate.action.method or ""), path=str(read_candidate.action.path or "")):
            result = await execute_rest_tool(read_candidate, read_inputs, db)
        with _timing_span(timing, "trace.finalize", tool=str(read_candidate.tool.name or "")):
            await finalize_execution_trace(trace, result, db)
        if result.get("error"):
            continue
        resolved = _single_resource_id_from_result(result, noun)
        if resolved is not None:
            return resolved
        body = result.get("body") if isinstance(result, dict) else None
        updated_frame = remember_choice_variable(
            frame,
            input_name=input_name,
            target_action_path=str(getattr(target_candidate.action, "path", "") or ""),
            items=[item for item in _resource_items_from_body(body, noun) if isinstance(item, dict)],
            origin={
                "method": str(getattr(target_candidate.action, "method", "") or ""),
                "path": str(getattr(target_candidate.action, "path", "") or ""),
                "field_path": noun,
            },
        )
        frame.clear()
        frame.update(updated_frame)
        return None
    return None


def _rank_read_resolver_candidates(
    *,
    input_name: str,
    noun: str,
    candidates: list[ToolCandidate],
    frame: dict[str, Any],
) -> list[ToolCandidate]:
    read_candidates = [
        candidate
        for candidate in candidates
        if str(getattr(candidate.action, "method", "") or "").upper() in {"GET", "HEAD", "OPTIONS"}
    ]
    ranked = []
    for candidate in read_candidates:
        score = candidate.score
        haystack = " ".join(
            [
                str(getattr(candidate.tool, "name", "") or ""),
                str(getattr(candidate.action, "name", "") or ""),
                str(getattr(candidate.action, "path", "") or ""),
                str(getattr(candidate.action, "description", "") or ""),
                str(getattr(candidate.tool, "description", "") or ""),
            ]
        )
        hay_tokens = set(_tokens(haystack))
        if noun in hay_tokens or _singular(noun) in hay_tokens:
            score += 20
        schema = (candidate.tool.function_schema or {}).get("parameters") or {}
        required = [str(name) for name in (schema.get("required") or [])] if isinstance(schema, dict) else []
        if required and all(_input_value_from_frame(frame, name) is not None for name in required):
            score += 15
        if input_name in hay_tokens:
            score += 5
        ranked.append(_candidate_with_score(candidate, score))
    return sorted(ranked, key=lambda row: (-row.score, _required_count(row.tool), row.tool.name))


async def _find_read_resolver_candidates_by_noun(
    *,
    input_name: str,
    noun: str,
    saas_agent_id: uuid.UUID,
    db: AsyncSession,
    limit: int = 50,
) -> list[ToolCandidate]:
    noun_tokens = _resolver_noun_tokens(input_name=input_name, noun=noun)
    if not noun_tokens:
        return []
    if not hasattr(db, "execute"):
        return []
    result = await db.execute(
        select(GeneratedTool, ActionNode, Connection)
        .join(ActionNode, GeneratedTool.action_node_id == ActionNode.id)
        .join(Connection, GeneratedTool.connection_id == Connection.id)
        .options(selectinload(Connection.credentials))
        .where(
            GeneratedTool.saas_agent_id == saas_agent_id,
            GeneratedTool.status == ToolStatus.active,
            ActionNode.status != ActionNodeStatus.deprecated,
        )
    )
    candidates: list[ToolCandidate] = []
    for tool, action, connection in result.all():
        method = str(getattr(action, "method", "") or "").upper()
        if method not in {"GET", "HEAD", "OPTIONS"}:
            continue
        haystack = " ".join(
            [
                str(getattr(tool, "name", "") or ""),
                str(getattr(action, "name", "") or ""),
                str(getattr(action, "path", "") or ""),
                str(getattr(action, "description", "") or ""),
                str(getattr(tool, "description", "") or ""),
                " ".join(str(tag) for tag in (getattr(action, "tags", None) or [])),
            ]
        )
        hay_tokens = set(_tokens(haystack))
        if not (hay_tokens & noun_tokens):
            continue
        score = 30 + (8 if str(getattr(action, "path", "") or "").lower().find(noun.replace("_", "-")) >= 0 else 0)
        score += 5 if str(getattr(action, "path", "") or "").count("/") <= 3 else 0
        candidates.append(
            ToolCandidate(
                tool=tool,
                action=action,
                connection=connection,
                score=score,
                reason=f"resolver_noun:{noun}",
            )
        )
    return sorted(candidates, key=lambda row: (-row.score, _required_count(row.tool), row.tool.name))[:limit]


def _merge_resolver_candidates(primary: list[ToolCandidate], extra: list[ToolCandidate]) -> list[ToolCandidate]:
    merged: list[ToolCandidate] = []
    seen: set[tuple[str, str]] = set()
    for candidate in [*primary, *extra]:
        key = (
            str(getattr(getattr(candidate, "tool", None), "id", "")),
            str(getattr(getattr(candidate, "action", None), "id", "")),
        )
        if key in seen:
            continue
        seen.add(key)
        merged.append(candidate)
    return merged


def _resolver_noun_tokens(*, input_name: str, noun: str) -> set[str]:
    tokens = set(_tokens(noun))
    tokens.update(_tokens(input_name))
    for token in list(tokens):
        if token.endswith("s") and len(token) > 3:
            tokens.add(token[:-1])
        elif len(token) > 2:
            tokens.add(f"{token}s")
    tokens.discard("id")
    return tokens


def _fill_inputs_from_frame_fields(
    *,
    inputs: dict[str, Any],
    missing: list[str],
    frame: dict[str, Any] | None,
) -> tuple[dict[str, Any], list[str]]:
    if not missing or not isinstance(frame, dict):
        return inputs, missing
    next_inputs = dict(inputs)
    remaining: list[str] = []
    for name in missing:
        value = _input_value_from_frame(frame, str(name))
        if value is None:
            remaining.append(str(name))
        else:
            next_inputs[str(name)] = value
    return next_inputs, remaining


def _input_value_from_frame(frame: dict[str, Any], name: str) -> Any:
    value = resolve_input_from_variables(frame, name, action=SimpleNamespace(path=""))
    if value not in (None, ""):
        return value
    selected = frame.get("selected_entity")
    if isinstance(selected, dict):
        raw = selected.get("raw")
        if isinstance(raw, dict) and name in raw and raw[name] not in (None, ""):
            return raw[name]
    return None


def _single_resource_id_from_result(result: dict[str, Any], noun: str) -> str | None:
    body = result.get("body") if isinstance(result, dict) else None
    items = _resource_items_from_body(body, noun)
    ids = [str(item.get("id")) for item in items if isinstance(item, dict) and item.get("id")]
    unique_ids = list(dict.fromkeys(ids))
    return unique_ids[0] if len(unique_ids) == 1 else None


def _resource_items_from_body(body: Any, noun: str) -> list[dict[str, Any]]:
    if isinstance(body, list):
        return [item for item in body if isinstance(item, dict)]
    if not isinstance(body, dict):
        return []
    plural = noun if noun.endswith("s") else f"{noun}s"
    prioritized_keys = [plural, noun, plural.replace("_", "-"), noun.replace("_", "-")]
    for key in prioritized_keys:
        value = body.get(key)
        if isinstance(value, list):
            return [item for item in value if isinstance(item, dict)]
        if isinstance(value, dict):
            return [value]
    for value in body.values():
        if isinstance(value, list):
            dict_items = [item for item in value if isinstance(item, dict)]
            if dict_items:
                return dict_items
    return []


def _is_opaque_id_input(name: str) -> bool:
    lowered = name.lower()
    return lowered == "id" or lowered.endswith("_id")


def _noun_from_id_input(name: str) -> str:
    lowered = name.lower()
    if lowered == "id":
        return ""
    return lowered[:-3] if lowered.endswith("_id") else lowered


async def _record_public_policy_gap_trace(
    *,
    top: ToolCandidate,
    inputs: dict[str, Any],
    missing: list[str],
    candidate_summary_rows: list[dict[str, Any]],
    saas_agent_id: uuid.UUID,
    session_id: uuid.UUID | None,
    user_id: uuid.UUID | None,
    session: AgentSession | None,
    frame: dict[str, Any] | None,
    selected_entity: dict[str, Any] | None,
    db: AsyncSession,
) -> AgentExecutionTrace:
    trace = await create_execution_trace(
        candidate=top,
        inputs=inputs,
        missing=missing,
        candidate_summary=candidate_summary_rows,
        status="needs_input",
        approval_state="not_required",
        route_node="internal_dependency_policy",
        saas_agent_id=saas_agent_id,
        session_id=session_id,
        user_id=user_id,
        db=db,
    )
    await _save_operation_frame(
        session=session,
        frame=frame,
        selected_entity=selected_entity,
        tool=top.tool,
        action=top.action,
        inputs=inputs,
        missing=missing,
        db=db,
    )
    await learning_service.propose_domain_policy_gap(
        trace=trace,
        target_candidate=top,
        dependency_candidate=None,
        missing_internal_inputs=missing,
        db=db,
    )
    return trace


async def _save_operation_frame(
    *,
    session: AgentSession | None,
    frame: dict[str, Any] | None,
    selected_entity: dict[str, Any] | None,
    tool: GeneratedTool,
    action: ActionNode,
    inputs: dict[str, Any],
    missing: list[str],
    db: AsyncSession,
) -> None:
    if selected_entity is None:
        return
    await save_execution_frame(
        session,
        operation_frame_from_candidate(
            base_frame=frame,
            selected_entity=selected_entity,
            tool=tool,
            action=action,
            inputs=inputs,
            missing=missing,
        ),
        db,
    )


def _first_parent_collection_path(path: str, internal_names: list[str]) -> str | None:
    for name in internal_names:
        parent_path = derive_parent_collection_path(path, name)
        if parent_path:
            return parent_path
    return None


def _public_policy_needed_message() -> str:
    return (
        "I found the item details, but this connected app needs an owner-approved automation policy before I can manage this for visitors.\n\n"
        "I sent this to Sandbox learning for review."
    )


def _format_public_execution_success(*, result: dict[str, Any], method: str | None) -> str:
    if str(method or "").upper() in {"POST", "PUT", "PATCH", "DELETE"}:
        order = _extract_order_body(result.get("body"))
        if order is not None:
            return _format_public_order_success(order)
        return "Done. I handled that for you."
    formatted = _format_public_read_success(result.get("body"))
    if formatted is not None:
        return formatted
    return (
        "Here's what I found.\n\n"
        f"```json\n{_preview_body_json(result.get('body'))}\n```\n\n"
        "You can ask me to check another item or narrow the result."
    )


def _preserve_active_resource_context(next_frame: dict[str, Any] | None, previous_frame: dict[str, Any]) -> dict[str, Any]:
    updated = copy.deepcopy(next_frame or previous_frame)
    for key in ("active_resource", "active_resource_ref"):
        if key in previous_frame and key not in updated:
            updated[key] = copy.deepcopy(previous_frame[key])
    previous_variables = previous_frame.get("variables")
    next_variables = updated.get("variables")
    if isinstance(previous_variables, dict):
        merged = copy.deepcopy(previous_variables)
        if isinstance(next_variables, dict):
            merged.update(copy.deepcopy(next_variables))
        updated["variables"] = merged
    return updated


def _format_public_read_success(body: Any) -> str | None:
    if not isinstance(body, dict):
        return None
    order = _extract_order_body(body)
    if order is not None:
        return _format_public_order_read_success(order)
    shipping_options = body.get("shipping_options")
    if isinstance(shipping_options, list):
        return _format_shipping_options_success(shipping_options)
    payment_providers = body.get("payment_providers")
    if isinstance(payment_providers, list):
        return _format_payment_providers_success(payment_providers)
    products = body.get("products")
    if isinstance(products, list):
        return _format_products_success(products, total_count=body.get("count"))
    return None


def _format_public_order_read_success(order: dict[str, Any]) -> str:
    order_id = str(order.get("id") or "").strip()
    display_id = str(order.get("display_id") or order.get("custom_display_id") or "").strip()
    status_text = str(order.get("status") or "").strip()
    if order_id and display_id:
        first_line = f"Order #{display_id} ({order_id})"
    elif order_id:
        first_line = f"Order {order_id}"
    else:
        first_line = "Order details"
    details: list[str] = []
    if status_text:
        details.append(f"Status: {status_text}.")
    item_summary = _format_order_item_summary(order)
    if item_summary:
        details.append(f"Items: {item_summary}.")
    total_summary = _format_order_total(order)
    if total_summary:
        details.append(f"Total: {total_summary}.")
    return " ".join([first_line + ".", *details])


def _format_shipping_options_success(options: list[Any]) -> str | None:
    names = [str(item.get("name") or item.get("title") or "").strip() for item in options if isinstance(item, dict)]
    names = [name for name in names if name]
    if not names:
        return None
    lines = ["I found these shipping options.", ""]
    lines.extend(f"- {name}" for name in names[:6])
    if len(names) > 6:
        lines.append(f"- {len(names) - 6} more")
    lines.extend(["", "Reply with the option name to use it."])
    return "\n".join(lines)


def _format_payment_providers_success(providers: list[Any]) -> str | None:
    names = []
    for item in providers:
        if not isinstance(item, dict):
            continue
        provider_id = str(item.get("id") or item.get("provider_id") or "").strip()
        if provider_id:
            names.append(provider_id)
    names = _dedupe_preserve_order(names)
    if not names:
        return None
    lines = ["I found these payment providers.", ""]
    lines.extend(f"- {name}" for name in names[:6])
    if len(names) > 6:
        lines.append(f"- {len(names) - 6} more")
    lines.extend(["", "Reply with the provider id to use it."])
    return "\n".join(lines)


def _format_products_success(products: list[Any], *, total_count: Any = None) -> str | None:
    lines = ["Here's what I found.", ""]
    shown = 0
    for product in products[:6]:
        if not isinstance(product, dict):
            continue
        title = str(product.get("title") or product.get("handle") or product.get("id") or "").strip()
        if not title:
            continue
        sizes = _product_size_values(product)
        if sizes:
            lines.append(f"- {title}: sizes {', '.join(sizes)}")
        else:
            lines.append(f"- {title}")
        shown += 1
    if shown == 0:
        return None
    if isinstance(total_count, int) and total_count > shown:
        lines.append(f"- {total_count - shown} more")
    lines.extend(["", "Tell me which product and size you want to add."])
    return "\n".join(lines)


def _product_size_values(product: dict[str, Any]) -> list[str]:
    values: list[str] = []
    for option in product.get("options") or []:
        if not isinstance(option, dict):
            continue
        if str(option.get("title") or "").strip().lower() != "size":
            continue
        for value in option.get("values") or []:
            raw = value.get("value") if isinstance(value, dict) else value
            if raw not in (None, ""):
                values.append(str(raw))
    if not values:
        for variant in product.get("variants") or []:
            if not isinstance(variant, dict):
                continue
            title = str(variant.get("title") or "").strip()
            if title:
                values.append(title.split("/", 1)[0].strip())
    return _dedupe_preserve_order(values)


def _dedupe_preserve_order(values: list[str]) -> list[str]:
    seen: set[str] = set()
    deduped: list[str] = []
    for value in values:
        key = value.strip().lower()
        if not key or key in seen:
            continue
        seen.add(key)
        deduped.append(value.strip())
    return deduped


def _extract_order_body(body: Any) -> dict[str, Any] | None:
    if not isinstance(body, dict):
        return None
    nested_order = body.get("order")
    if isinstance(nested_order, dict):
        return nested_order
    order_id = str(body.get("id") or "")
    if body.get("type") == "order" or order_id.startswith("order_"):
        return body
    return None


def _format_public_order_success(order: dict[str, Any]) -> str:
    order_id = str(order.get("id") or "").strip()
    display_id = str(order.get("display_id") or order.get("custom_display_id") or "").strip()
    if order_id and display_id:
        first_line = f"Done. I placed order #{display_id} ({order_id})."
    elif order_id:
        first_line = f"Done. I placed order {order_id}."
    else:
        first_line = "Done. I placed the order."

    details: list[str] = []
    item_summary = _format_order_item_summary(order)
    if item_summary:
        details.append(f"Items: {item_summary}.")
    total_summary = _format_order_total(order)
    if total_summary:
        details.append(f"Total: {total_summary}.")
    return " ".join([first_line, *details])


def _format_order_item_summary(order: dict[str, Any]) -> str | None:
    items = order.get("items")
    if not isinstance(items, list):
        return None
    chunks: list[str] = []
    for item in items[:3]:
        if not isinstance(item, dict):
            continue
        title = str(item.get("title") or "").strip()
        sku = str(item.get("variant_sku") or item.get("sku") or "").strip()
        if not sku and isinstance(item.get("variant"), dict):
            sku = str(item["variant"].get("sku") or "").strip()
        label = title or sku
        if title and sku:
            label = f"{title} ({sku})"
        if not label:
            continue
        quantity = item.get("quantity")
        if quantity not in (None, ""):
            label = f"{quantity} x {label}"
        chunks.append(label)
    if len(items) > 3:
        chunks.append(f"{len(items) - 3} more")
    return ", ".join(chunks) or None


def _format_order_total(order: dict[str, Any]) -> str | None:
    total = order.get("total")
    currency = str(order.get("currency_code") or "").strip().upper()
    if total in (None, "") or not currency:
        return None
    if isinstance(total, float):
        total_text = f"{total:g}"
    else:
        total_text = str(total)
    return f"{total_text} {currency}"


async def create_execution_trace(
    *,
    candidate: ToolCandidate,
    inputs: dict[str, Any],
    missing: list[str],
    candidate_summary: list[dict[str, Any]],
    status: str,
    approval_state: str,
    route_node: str,
    saas_agent_id: uuid.UUID,
    session_id: uuid.UUID | None,
    user_id: uuid.UUID | None,
    db: AsyncSession,
) -> AgentExecutionTrace:
    trace = AgentExecutionTrace(
        saas_agent_id=saas_agent_id,
        session_id=session_id,
        connection_id=candidate.connection.id,
        action_node_id=candidate.action.id,
        generated_tool_id=candidate.tool.id,
        tool_name=candidate.tool.name,
        action_name=candidate.action.name,
        method=candidate.action.method,
        path=candidate.action.path,
        risk_level=_risk_value(candidate.tool.risk_level),
        status=status,
        approval_state=approval_state,
        inputs=inputs,
        missing_inputs=missing,
        candidate_summary=candidate_summary,
        route_node=route_node,
        requested_by=user_id,
    )
    db.add(trace)
    await db.commit()
    await db.refresh(trace)
    if status == "needs_input" and route_node != "internal_dependency_policy":
        try:
            from backend.services.agent.learning_service import learning_service

            await learning_service.propose_from_trace(trace, db)
        except Exception:
            pass
    return trace


async def finalize_execution_trace(trace: AgentExecutionTrace, result: dict[str, Any], db: AsyncSession) -> None:
    trace.result = result
    trace.error = result.get("error")
    trace.duration_ms = int(result.get("duration_ms") or 0)
    trace.status = "failed" if result.get("error") else "succeeded"
    trace.route_node = "result_review"
    await db.commit()
    schedule_generated_knowledge_refresh(trace.saas_agent_id)
    if trace.status == "failed":
        try:
            from backend.services.agent.learning_service import learning_service

            await learning_service.propose_from_trace(trace, db)
        except Exception:
            pass


def schedule_generated_knowledge_refresh(saas_agent_id: uuid.UUID) -> None:
    try:
        asyncio.get_running_loop().create_task(_refresh_generated_knowledge(saas_agent_id))
    except RuntimeError:
        # There is no loop to schedule on. Execution persistence should still
        # complete; the next activation/manual refresh can rebuild knowledge.
        return


async def _refresh_generated_knowledge(saas_agent_id: uuid.UUID) -> None:
    try:
        from backend.core.database import async_session
        from backend.services.agent.rag_service import rag_service

        async with async_session() as refresh_db:
            await rag_service.ingest_generated_knowledge(saas_agent_id=saas_agent_id, db=refresh_db)
    except Exception:
        # Retrieval refresh is opportunistic and must not affect the chat turn.
        return


async def list_pending_approval_traces(
    *,
    saas_agent_id: uuid.UUID,
    db: AsyncSession,
) -> list[AgentExecutionTrace]:
    result = await db.execute(
        select(AgentExecutionTrace)
        .where(
            AgentExecutionTrace.saas_agent_id == saas_agent_id,
            AgentExecutionTrace.status == "approval_required",
            AgentExecutionTrace.approval_state == "pending",
        )
        .order_by(AgentExecutionTrace.created_at.desc())
        .limit(25)
    )
    return list(result.scalars().all())


async def approve_pending_execution_trace(
    *,
    trace: AgentExecutionTrace,
    approved_by: uuid.UUID | None,
    db: AsyncSession,
) -> tuple[str, dict[str, Any] | None]:
    if trace.status != "approval_required" or trace.approval_state != "pending":
        return f"This request is not waiting for approval. Current status: {trace.status}.", trace.result
    candidate = await _candidate_from_trace(db, trace)
    if candidate is None:
        trace.status = "failed"
        trace.approval_state = "approved"
        trace.error = "Trace candidate no longer exists."
        trace.route_node = "result_review"
        trace.approved_by = approved_by
        await db.commit()
        return "This request can no longer run because the generated action is missing.", trace.result

    trace.status = "executing"
    trace.approval_state = "approved"
    trace.route_node = "executing"
    trace.approved_by = approved_by
    await db.commit()

    result = await execute_rest_tool(candidate, trace.inputs or {}, db)
    await finalize_execution_trace(trace, result, db)
    message = (
        "The approved request ran but the connected API returned an error."
        if result.get("error")
        else "The approved request ran successfully."
    )
    await _append_public_approval_message(trace, message, result, db)
    return message, result


async def cancel_pending_execution_trace(
    *,
    trace: AgentExecutionTrace,
    canceled_by: uuid.UUID | None,
    db: AsyncSession,
) -> str:
    if trace.status != "approval_required" or trace.approval_state != "pending":
        return f"This request is not waiting for approval. Current status: {trace.status}."
    trace.status = "canceled"
    trace.approval_state = "rejected"
    trace.route_node = "result_review"
    trace.approved_by = canceled_by
    await db.commit()
    message = "The agent owner canceled this request. No API call was made."
    await _append_public_approval_message(trace, message, None, db)
    return message


async def _maybe_handle_trace_control(
    *,
    message: str,
    saas_agent_id: uuid.UUID,
    session_id: uuid.UUID | None,
    user_id: uuid.UUID | None,
    db: AsyncSession,
    emit,
    public_response: bool = False,
) -> str | None:
    parsed = _parse_trace_control(message)
    if parsed is None:
        return None
    command, trace_token = parsed
    if public_response:
        return "Approval actions must be handled by the agent owner, not from this public chat."
    trace = await _find_trace_by_token(db, saas_agent_id, trace_token)
    if trace is None:
        return f"I could not find a pending execution trace matching `{trace_token}`."
    if trace.status != "approval_required" or trace.approval_state != "pending":
        return f"Trace `{trace_token}` is not waiting for approval. Current status: `{trace.status}`."
    if command == "cancel":
        trace.status = "canceled"
        trace.approval_state = "rejected"
        trace.route_node = "execution_planning"
        trace.approved_by = user_id
        await db.commit()
        await emit("approval_rejected", {"trace_id": str(trace.id), "trace_token": trace_token})
        return f"Canceled execution trace `{trace_token}`. No API call was made."

    candidate = await _candidate_from_trace(db, trace)
    if candidate is None:
        trace.status = "failed"
        trace.error = "Trace candidate no longer exists."
        trace.route_node = "result_review"
        await db.commit()
        return f"Trace `{trace_token}` can no longer run because its generated tool or action is missing."

    trace.status = "executing"
    trace.approval_state = "approved"
    trace.route_node = "executing"
    trace.approved_by = user_id
    await db.commit()
    await emit("approval_approved", {"trace_id": str(trace.id), "trace_token": trace_token, "tool": trace.tool_name})
    call_id = uuid.uuid4().hex[:8]
    await emit("tool_start", {"tool_name": trace.tool_name, "call_id": call_id, "inputs": trace.inputs or {}})
    result = await execute_rest_tool(candidate, trace.inputs or {}, db)
    await finalize_execution_trace(trace, result, db)
    await emit("tool_end", {"call_id": call_id, "output": json.dumps(result, default=str)[:5000]})
    if result.get("error"):
        return (
            f"Approved trace `{trace_token}` ran but failed.\n\n"
            f"Tool: `{trace.tool_name}`\n"
            f"Status: {result.get('status_code', 0)}\n"
            f"Error: {result.get('error')}"
        )
    return (
        f"Approved trace `{trace_token}` ran successfully.\n\n"
        f"Tool: `{trace.tool_name}`\n"
        f"Status: {result.get('status_code')}\n"
        f"Duration: {result.get('duration_ms')} ms\n\n"
        f"Result preview:\n```json\n{_preview_body_json(result.get('body'))}\n```"
    )


async def find_tool_candidates(
    *,
    message: str,
    saas_agent_id: uuid.UUID,
    db: AsyncSession,
    limit: int = 5,
) -> list[ToolCandidate]:
    search_message = _tool_search_message(message)
    ranked = await rank_generated_tools(message=search_message, saas_agent_id=saas_agent_id, db=db, limit=limit)
    candidates = [
        ToolCandidate(
            tool=row.tool,
            action=row.action,
            connection=row.connection,
            score=max(1, row.score + _operation_intent_bonus(search_message, row.action, row.tool)),
            reason=row.reason,
        )
        for row in ranked
    ]
    return sorted(candidates, key=lambda row: (-row.score, _required_count(row.tool), row.tool.name))[:limit]


def _tool_search_message(message: str) -> str:
    visible_message = message.split(" Active resource collection ", 1)[0]
    search_message = visible_message if _looks_like_payment_options_request(visible_message) else message
    tokens = set(_tokens(search_message))
    expansions: list[str] = []
    if tokens & {"paid", "pay", "paying", "payment", "payments"}:
        expansions.append("payment payments payment providers payment provider payment options payment methods checkout")
    if not expansions:
        return search_message
    return " ".join([search_message, *expansions])


def _operation_intent_bonus(message: str, action: ActionNode, tool: GeneratedTool) -> int:
    tokens = set(_tokens(message))
    haystack = " ".join(
        [
            getattr(tool, "name", "") or "",
            getattr(action, "name", "") or "",
            getattr(action, "path", "") or "",
            getattr(action, "description", "") or "",
        ]
    ).lower()
    hay_tokens = set(_tokens(haystack))
    method = str(getattr(action, "method", "") or "").upper()
    bonus = 0
    write_intent = tokens & {"add", "create", "update", "delete", "remove", "send", "submit", "buy", "purchase"}
    read_intent = tokens & {"list", "show", "find", "fetch", "search", "filter", "get"}
    explicit_id_prefixes = _explicit_resource_id_prefixes(message)
    resource = _collection_resource_from_path(str(getattr(action, "path", "") or ""))
    if write_intent:
        if method in {"POST", "PUT", "PATCH", "DELETE"}:
            bonus += 3
        if method == "GET":
            bonus -= 3
        if write_intent & hay_tokens:
            bonus += 1
    if read_intent and method in {"GET", "HEAD", "OPTIONS"}:
        bonus += 1
    elif read_intent and method in {"POST", "PUT", "PATCH", "DELETE"} and not _has_write_intent(message):
        bonus -= 6
    bonus += _resource_phrase_bonus(tokens=tokens, candidate_tokens=hay_tokens, method=method)
    if read_intent and method == "GET" and _required_count(tool) > 0 and explicit_id_prefixes:
        resource_names = {resource, _singular(resource)}
        bonus += 80 if resource_names & explicit_id_prefixes else -30
    if _has_collection_read_intent(tokens=tokens, action=action):
        if method == "GET" and "{" not in str(getattr(action, "path", "") or ""):
            bonus += 8
        elif method == "GET" and _required_count(tool) > 0:
            bonus += 8 if _has_explicit_resource_id(message=message, resource=resource) else -8
    return bonus


def _has_collection_read_intent(*, tokens: set[str], action: ActionNode) -> bool:
    if not tokens & _COLLECTION_READ_TERMS:
        return False
    resource = _collection_resource_from_path(str(getattr(action, "path", "") or ""))
    if not resource:
        return False
    return resource in tokens or _singular(resource) in tokens


def _collection_resource_from_path(path: str) -> str:
    segments = [segment.lower() for segment in str(path or "").split("/") if segment and not segment.startswith("{")]
    return segments[-1] if segments else ""


def _has_explicit_resource_id(*, message: str, resource: str) -> bool:
    singular = _singular(resource)
    return bool(re.search(rf"\b(?:{re.escape(resource)}|{re.escape(singular)})_[a-z0-9]", message or "", re.IGNORECASE))


def _resource_phrase_bonus(*, tokens: set[str], candidate_tokens: set[str], method: str) -> int:
    bonus = 0
    phrases = [
        ({"payment", "collection"}, 70),
        ({"payment", "session"}, 70),
        ({"shipping", "method"}, 45),
        ({"shipping", "option"}, 45),
    ]
    for phrase, weight in phrases:
        if not phrase <= tokens:
            continue
        if phrase <= candidate_tokens:
            bonus += weight
        elif method in {"POST", "PUT", "PATCH", "DELETE"}:
            bonus -= 20
    return bonus


def _explicit_resource_id_prefixes(message: str) -> set[str]:
    return {match.group(1).lower() for match in re.finditer(r"\b([a-z][a-z0-9]*)_[a-z0-9]", message or "", re.IGNORECASE)}


def _rerank_candidates_for_frame(*, message: str, candidates: list[ToolCandidate], frame: dict[str, Any]) -> list[ToolCandidate]:
    if not (
        _has_write_intent(message)
        or _looks_like_read_refinement(message)
        or _looks_like_collection_read_request(message)
        or find_entity_reference(message, frame) is not None
    ):
        return candidates
    adjusted = [_candidate_with_score(row, _context_candidate_score(message=message, candidate=row, frame=frame)) for row in candidates]
    return sorted(
        adjusted,
        key=lambda row: (
            -row.score,
            _required_count(row.tool),
            row.tool.name,
        ),
    )


def _candidate_with_score(candidate: ToolCandidate, score: int) -> ToolCandidate:
    try:
        return replace(candidate, score=score)
    except TypeError:
        updated = copy.copy(candidate)
        updated.score = score
    return updated


def _rerank_recovery_candidates(
    *,
    message: str,
    error_detail: str,
    candidates: list[ToolCandidate],
    frame: dict[str, Any],
) -> list[ToolCandidate]:
    adjusted = [_candidate_with_score(row, _recovery_candidate_score(message=message, error_detail=error_detail, candidate=row, frame=frame)) for row in candidates]
    return sorted(adjusted, key=lambda row: (-row.score, _required_count(row.tool), row.tool.name))


def _recovery_candidate_score(*, message: str, error_detail: str, candidate: ToolCandidate, frame: dict[str, Any]) -> int:
    score = _context_candidate_score(message=message, candidate=candidate, frame=frame)
    active_resource = active_resource_context(frame)
    if active_resource is None:
        return score
    active_path = str(active_resource.get("collection_path") or "").rstrip("/")
    candidate_path = str(getattr(candidate.action, "path", "") or "").rstrip("/")
    resource_name = _singular(_last_path_segment(active_path).replace("-", "_"))
    schema = (candidate.tool.function_schema or {}).get("parameters") or {}
    props = schema.get("properties") if isinstance(schema, dict) else {}
    if resource_name and isinstance(props, dict) and f"{resource_name}_id" in props:
        score += 30
    if str(getattr(candidate.action, "method", "") or "").upper() == "POST" and "{" not in candidate_path:
        score += 12
    if active_path and re.fullmatch(re.escape(active_path) + r"/\{[^/]+\}", candidate_path):
        score -= 35
    error_tokens = set(_tokens(error_detail))
    haystack = " ".join(
        [
            str(getattr(candidate.tool, "name", "") or ""),
            str(getattr(candidate.action, "name", "") or ""),
            str(getattr(candidate.action, "path", "") or ""),
            str(getattr(candidate.action, "description", "") or ""),
            str(getattr(candidate.tool, "description", "") or ""),
        ]
    )
    hay_tokens = set(_tokens(haystack))
    score += len(error_tokens & hay_tokens) * 3
    for dependency_path in known_resource_collection_paths(frame):
        known_path = str(dependency_path or "").rstrip("/")
        if not known_path:
            continue
        if candidate_path == known_path and str(getattr(candidate.action, "method", "") or "").upper() == "POST":
            score -= 55
        child_match = re.fullmatch(re.escape(known_path) + r"/\{[^/]+\}/(.+)", candidate_path)
        if child_match:
            child_tokens = set(_tokens(child_match.group(1)))
            if child_tokens & error_tokens:
                score += 75
    return score


def _context_candidate_score(*, message: str, candidate: ToolCandidate, frame: dict[str, Any]) -> int:
    base_inputs, _base_missing = _build_inputs(message, candidate.action, candidate.tool)
    inputs, _missing = build_inputs_from_frame(
        message=message,
        action=candidate.action,
        tool=candidate.tool,
        frame=frame,
        base_inputs=base_inputs,
    )
    required = ((candidate.tool.function_schema or {}).get("parameters") or {}).get("required") or []
    filled_required = sum(1 for name in required if str(name) in inputs and str(name) not in base_inputs)
    score = candidate.score + (filled_required * 8)
    method = str(getattr(candidate.action, "method", "") or "").upper()
    candidate_path = str(getattr(candidate.action, "path", "") or "")
    if _looks_like_payment_options_request(message):
        if method in {"GET", "HEAD", "OPTIONS"} and "payment-providers" in candidate_path:
            score += 140
        elif method in {"POST", "PUT", "PATCH", "DELETE"} and "payment" in candidate_path:
            score -= 110
    if _has_write_intent(message):
        if method in {"POST", "PUT", "PATCH", "DELETE"}:
            score += 30
        elif method in {"GET", "HEAD", "OPTIONS"}:
            score -= 45
    score += _strict_resource_path_bonus(message=message, candidate_path=candidate_path)
    if required:
        if all(str(name) in inputs for name in required):
            score += 35
        else:
            score -= 10
    active_resource = active_resource_context(frame)
    last_read_path = _last_read_collection_path(frame)
    if last_read_path and _looks_like_read_refinement(message):
        candidate_path = str(getattr(candidate.action, "path", "") or "").rstrip("/")
        method = str(getattr(candidate.action, "method", "") or "").upper()
        if method in {"GET", "HEAD", "OPTIONS"}:
            if candidate_path == last_read_path:
                score += 14
            elif candidate_path.startswith(last_read_path + "/"):
                score += 4
    if active_resource is not None:
        active_path = str(active_resource.get("collection_path") or "").rstrip("/")
        if _looks_like_collection_read_request(message):
            if method in {"GET", "HEAD", "OPTIONS"}:
                score += 45
            else:
                score -= 45
        if active_path and (candidate_path == active_path or candidate_path.startswith(active_path + "/")):
            score += 10
        score += _workflow_action_bonus(message, candidate)
        if _looks_like_workflow_message(message) and method in {"GET", "HEAD", "OPTIONS"}:
            score -= 40
        if _looks_like_workflow_message(message) and _candidate_missing_after_frame(message, candidate, frame):
            score -= 12
    return score


def _candidate_missing_after_frame(message: str, candidate: ToolCandidate, frame: dict[str, Any]) -> bool:
    base_inputs, _base_missing = _build_inputs(message, candidate.action, candidate.tool)
    _inputs, missing = build_inputs_from_frame(
        message=message,
        action=candidate.action,
        tool=candidate.tool,
        frame=frame,
        base_inputs=base_inputs,
    )
    return bool(missing)


def _looks_like_workflow_message(message: str) -> bool:
    if _looks_like_collection_read_request(message):
        return False
    return bool(set(_tokens(message)) & {"checkout", "complete", "finish", "order", "payment", "place", "ship", "shipping", "submit"})


def _workflow_action_bonus(message: str, candidate: ToolCandidate) -> int:
    message_tokens = set(_tokens(message))
    haystack = " ".join(
        [
            str(getattr(candidate.tool, "name", "") or ""),
            str(getattr(candidate.action, "name", "") or ""),
            str(getattr(candidate.action, "path", "") or ""),
            str(getattr(candidate.action, "description", "") or ""),
            str(getattr(candidate.tool, "description", "") or ""),
        ]
    )
    candidate_tokens = set(_tokens(haystack))
    if "checkout" in message_tokens and candidate_tokens & {"checkout", "complete", "completion", "order", "submit"}:
        return 16
    if message_tokens & {"complete", "finish", "place", "submit"} and candidate_tokens & {"complete", "completion", "order", "submit"}:
        return 12
    if message_tokens & {"shipping", "ship"} and candidate_tokens & {"shipping", "shipment", "delivery"}:
        return 12
    if "payment" in message_tokens and candidate_tokens & {"payment", "payments"}:
        return 12
    return 0


def _strict_resource_path_bonus(*, message: str, candidate_path: str) -> int:
    tokens = set(_tokens(message))
    path_tokens = set(_tokens(candidate_path))
    if {"payment", "session"} <= tokens:
        return 300 if "sessions" in path_tokens or "session" in path_tokens else -120
    if {"payment", "collection"} <= tokens:
        if "sessions" in path_tokens or "session" in path_tokens:
            return -80
        return 220 if {"payment", "collection"} <= path_tokens else -60
    return 0


def _looks_like_payment_options_request(message: str) -> bool:
    tokens = set(_tokens(message))
    if not tokens & {"pay", "payment", "payments"}:
        return False
    if tokens & {"collection", "collections", "create", "initialize", "initiate", "session", "sessions", "start"}:
        return False
    question_terms = {"available", "can", "how", "what", "which"}
    option_terms = {"method", "methods", "option", "options", "provider", "providers"}
    return bool(tokens & question_terms and (tokens & option_terms or "pay" in tokens))


def _active_resource_input_names(candidate: ToolCandidate, inputs: dict[str, Any], active_resource: dict[str, Any]) -> list[str]:
    resource_id = str(active_resource.get("id") or "")
    if not resource_id:
        return []
    collection_path = str(active_resource.get("collection_path") or "")
    resource_name = _singular(_last_path_segment(collection_path).replace("-", "_"))
    schema = (candidate.tool.function_schema or {}).get("parameters") or {}
    required = list(schema.get("required") or []) if isinstance(schema, dict) else []
    names: list[str] = []
    for name in required:
        string_name = str(name)
        if inputs.get(string_name) != resource_id:
            continue
        lowered = string_name.lower()
        if lowered == "id" and _candidate_path_targets_collection(candidate, collection_path):
            names.append(string_name)
        elif resource_name and lowered == f"{resource_name}_id":
            names.append(string_name)
    return names


def _dependency_input_names(action: ActionNode, inputs: dict[str, Any], frame: dict[str, Any] | None) -> list[str]:
    names: list[str] = []
    if not isinstance(frame, dict):
        return names
    for name, value in inputs.items():
        parent_collection_path = derive_parent_collection_path(str(getattr(action, "path", "") or ""), str(name))
        if parent_collection_path is None:
            continue
        dependency_id = resolve_input_from_variables(frame, str(name), action=action)
        if dependency_id is not None and str(value) == dependency_id:
            names.append(str(name))
    return names


def _fill_inputs_from_variables(
    *,
    inputs: dict[str, Any],
    missing: list[str],
    action: ActionNode,
    frame: dict[str, Any] | None,
) -> tuple[dict[str, Any], list[str]]:
    if not missing or not isinstance(frame, dict):
        return inputs, missing
    next_inputs = dict(inputs)
    remaining: list[str] = []
    for name in missing:
        value = resolve_input_from_variables(frame, str(name), action=action)
        if value not in (None, ""):
            next_inputs[str(name)] = value
        else:
            remaining.append(str(name))
    return next_inputs, remaining


def _execution_error_detail(result: dict[str, Any]) -> str:
    body = result.get("body") if isinstance(result, dict) else None
    values: list[str] = []
    if isinstance(body, dict):
        for key in ("message", "error", "detail", "type", "code"):
            value = body.get(key)
            if value:
                values.append(str(value))
    elif isinstance(body, str):
        values.append(body)
    if result.get("error"):
        values.append(str(result["error"]))
    return " ".join(values)[:1000]


def _recovery_candidate_message(
    *,
    message: str,
    error_detail: str,
    frame: dict[str, Any],
    failed_candidate: ToolCandidate,
) -> str:
    parts = [
        "Recover from API error.",
        error_detail,
        message,
        augment_message_with_frame_context("continue workflow", {}, frame),
        str(getattr(failed_candidate.action, "description", "") or ""),
        str(getattr(failed_candidate.action, "path", "") or ""),
    ]
    return " ".join(part for part in parts if part)


def _created_collection_path(candidate: ToolCandidate) -> str | None:
    method = str(getattr(candidate.action, "method", "") or "").upper()
    path = str(getattr(candidate.action, "path", "") or "").rstrip("/")
    if method != "POST" or not path or "{" in path:
        return None
    return path


def _result_collection_path_for_frame(
    *,
    candidate: ToolCandidate,
    active_resource: dict[str, Any] | None,
    result: dict[str, Any] | None = None,
) -> str | None:
    candidate_path = str(getattr(candidate.action, "path", "") or "").rstrip("/")
    transition_path = _terminal_result_collection_path(candidate_path, result)
    if transition_path:
        return transition_path
    created_path = _created_collection_path(candidate)
    if created_path:
        return created_path
    if not candidate_path:
        return None
    active_path = str((active_resource or {}).get("collection_path") or "").rstrip("/")
    if active_path and (candidate_path == active_path or candidate_path.startswith(active_path + "/")):
        return active_path
    parent_path = _parent_collection_path_for_parameterized_action(candidate_path)
    if parent_path:
        return parent_path
    return active_path or None


def _parent_collection_path_for_parameterized_action(path: str) -> str | None:
    segments = [segment for segment in str(path or "").split("/") if segment]
    for index, segment in enumerate(segments):
        if segment.startswith("{") and segment.endswith("}") and index > 0:
            return "/" + "/".join(segments[:index])
    return None


def _terminal_result_collection_path(path: str, result: dict[str, Any] | None) -> str | None:
    if _last_path_segment(path).lower().replace("-", "_") not in {"checkout", "complete", "submit"}:
        return None
    parent_path = _parent_collection_path_for_parameterized_action(path)
    if not parent_path:
        return None
    keys = _top_level_result_resource_keys(result)
    if not keys:
        return None
    parent_segment = _last_path_segment(parent_path).replace("-", "_")
    selected_key = keys[0]
    for key in keys:
        if _pluralize_resource_segment(key).replace("-", "_") != parent_segment:
            selected_key = key
            break
    prefix = parent_path.rsplit("/", 1)[0]
    if not prefix:
        return None
    return f"{prefix}/{_pluralize_resource_segment(selected_key)}"


def _top_level_result_resource_keys(result: dict[str, Any] | None) -> list[str]:
    body = result.get("body") if isinstance(result, dict) else None
    if not isinstance(body, dict):
        return []
    keys: list[str] = []
    for key, value in body.items():
        if not isinstance(value, dict):
            continue
        if isinstance(value.get("id"), str) and value.get("id"):
            keys.append(str(key).strip().replace("_", "-"))
    return [key for key in keys if key]


def _candidate_path_targets_collection(candidate: ToolCandidate, collection_path: str) -> bool:
    path = str(getattr(candidate.action, "path", "") or "")
    normalized = collection_path.rstrip("/")
    return bool(normalized and (path == normalized or path.startswith(normalized + "/")))


def _last_path_segment(path: str) -> str:
    segments = [segment for segment in str(path or "").split("/") if segment]
    return segments[-1] if segments else ""


def _singular(value: str) -> str:
    return value[:-1] if value.endswith("s") else value


def _pluralize_resource_segment(value: str) -> str:
    normalized = str(value or "").strip().replace("_", "-")
    if not normalized:
        return ""
    if normalized.endswith("s"):
        return normalized
    if normalized.endswith("y"):
        return f"{normalized[:-1]}ies"
    return f"{normalized}s"


def _has_write_intent(message: str) -> bool:
    if _looks_like_payment_options_request(message):
        return False
    tokens = set(_tokens(message))
    if tokens & {"add", "buy", "checkout", "complete", "create", "delete", "finish", "place", "purchase", "remove", "send", "ship", "submit", "update"}:
        return True
    context_verbs = {"apply", "choose", "initialize", "initiate", "select", "set", "start", "use"}
    context_targets = {"delivery", "method", "option", "options", "payment", "session", "shipping", "shipment"}
    return bool(tokens & context_verbs and tokens & context_targets)


def _looks_like_read_refinement(message: str) -> bool:
    tokens = set(_tokens(message))
    return bool(tokens & _READ_REFINEMENT_TERMS) and not _has_write_intent(message)


def _looks_like_collection_read_request(message: str) -> bool:
    tokens = set(_tokens(message))
    if _has_write_intent(message):
        return False
    if tokens & {"fetch", "find", "get", "list", "search", "show"}:
        return True
    question_terms = {"available", "have", "what", "which"}
    dependency_terms = {
        "delivery",
        "method",
        "methods",
        "option",
        "options",
        "payment",
        "payments",
        "provider",
        "providers",
        "shipping",
        "shipment",
    }
    return bool(tokens & question_terms and tokens & dependency_terms)


def _looks_like_active_resource_read_dependency(message: str) -> bool:
    tokens = set(_tokens(message))
    if not _looks_like_collection_read_request(message):
        return False
    dependency_terms = {
        "delivery",
        "method",
        "methods",
        "option",
        "options",
        "payment",
        "payments",
        "provider",
        "providers",
        "shipping",
        "shipment",
    }
    return bool(tokens & dependency_terms)


def _looks_like_active_resource_read_request(message: str, active_resource: dict[str, Any] | None) -> bool:
    if active_resource is None or not _looks_like_collection_read_request(message):
        return False
    active_path = str(active_resource.get("collection_path") or "")
    segment = _last_path_segment(active_path).replace("-", "_")
    if not segment:
        return False
    singular = _singular(segment)
    names = {segment, singular, _pluralize_resource_segment(singular).replace("-", "_")}
    tokens = set(_tokens(message))
    if tokens & names:
        return True
    return bool(tokens & {"it", "that", "this"} and tokens & {"fetch", "get", "show"})


def _last_read_collection_path(frame: dict[str, Any] | None) -> str | None:
    if not isinstance(frame, dict):
        return None
    source = frame.get("source")
    if not isinstance(source, dict):
        return None
    method = str(source.get("method") or "").upper()
    path = str(source.get("path") or "").rstrip("/")
    if method not in {"GET", "HEAD", "OPTIONS"} or not path or "{" in path:
        return None
    return path


def _augment_message_with_read_collection_context(message: str, frame: dict[str, Any] | None, collection_path: str | None) -> str:
    if not collection_path:
        return message
    source = frame.get("source") if isinstance(frame, dict) else None
    parts = [message, f"Last read collection {collection_path}"]
    if isinstance(source, dict):
        for key in ("tool_name", "action_name"):
            value = source.get(key)
            if value:
                parts.append(str(value))
    return " ".join(parts)


async def execute_rest_tool(candidate: ToolCandidate, inputs: dict[str, Any], db: AsyncSession) -> dict[str, Any]:
    action = candidate.action
    connection = candidate.connection
    started = time.monotonic()
    headers: dict[str, str] = {}
    params: dict[str, Any] = {}
    try:
        if connection.auth_type and connection.credentials:
            for credential in connection.credentials:
                injected = await inject_credentials(
                    auth_type=connection.auth_type.value if hasattr(connection.auth_type, "value") else str(connection.auth_type),
                    decrypted_value=decrypt_value(credential.encrypted_value),
                    metadata=credential.metadata_ or {},
                )
                headers.update(injected.get("headers") or {})
                params.update(injected.get("params") or {})

        method = (action.method or "GET").upper()
        base_url = str((connection.config or {}).get("base_url") or "").rstrip("/")
        path = action.path or ""
        payload = dict(inputs)
        for param in action.parameters or []:
            if isinstance(param, dict) and param.get("in") == "path" and param.get("name") in payload:
                name = str(param["name"])
                path = path.replace(f"{{{name}}}", str(payload.pop(name)))
        for name in re.findall(r"\{(\w+)\}", path):
            if name in payload:
                path = path.replace(f"{{{name}}}", str(payload.pop(name)))
        url = f"{base_url}{path}" if base_url else path

        body: dict[str, Any] = {}
        for param in action.parameters or []:
            if isinstance(param, dict) and param.get("in") == "query" and param.get("name") in payload:
                params[str(param["name"])] = payload.pop(str(param["name"]))
        if method in {"GET", "DELETE", "HEAD", "OPTIONS"}:
            params.update({key: value for key, value in payload.items() if _is_scalar(value)})
        else:
            body = payload

        async with httpx.AsyncClient(timeout=30, follow_redirects=True) as client:
            response = await client.request(method, url, headers=headers, params=params, json=body or None)
        duration_ms = round((time.monotonic() - started) * 1000, 2)
        try:
            response_body: Any = response.json()
        except Exception:
            response_body = response.text[:5000]
        return {
            "status_code": response.status_code,
            "body": response_body,
            "duration_ms": duration_ms,
            "error": None if response.status_code < 400 else f"HTTP {response.status_code}",
        }
    except Exception as exc:
        error_text = str(exc) or exc.__class__.__name__
        if exc.__class__.__name__ in {"InvalidToken", "InvalidSignature"}:
            error_text = "Stored API credentials could not be decrypted. Reconnect this API credential."
        return {
            "status_code": 0,
            "body": None,
            "duration_ms": round((time.monotonic() - started) * 1000, 2),
            "error": error_text,
            "error_type": exc.__class__.__name__,
        }


def _build_inputs(message: str, action: ActionNode, tool: GeneratedTool) -> tuple[dict[str, Any], list[str]]:
    schema = (tool.function_schema or {}).get("parameters") or {}
    props = schema.get("properties") if isinstance(schema, dict) else {}
    required = list(schema.get("required") or []) if isinstance(schema, dict) else []
    inputs: dict[str, Any] = {}
    missing: list[str] = []

    for name, prop in (props or {}).items():
        lowered = str(name).lower()
        enum_value = _extract_enum_value(message, prop if isinstance(prop, dict) else {})
        named_value = _extract_named_value(message, str(name))
        if named_value is not None:
            inputs[name] = named_value
        elif enum_value is not None:
            inputs[name] = enum_value
        elif lowered == "status":
            status = _extract_status_value(message)
            if status is not None:
                inputs[name] = status
        elif lowered == "id":
            resource_id = _extract_resource_id_for_action(message, action)
            if resource_id is not None:
                inputs[name] = resource_id
        elif lowered in {"limit", "per_page", "page_size", "count", "top_k"}:
            inputs[name] = 5
        elif lowered in {"q", "query", "search", "search_query", "keyword", "name"}:
            search_value = _extract_search_value(message, lowered)
            if search_value is not None:
                inputs[name] = search_value

    for param in action.parameters or []:
        if not isinstance(param, dict) or not param.get("name"):
            continue
        if str(param.get("in") or "").lower() in {"header", "cookie"}:
            continue
        name = str(param["name"])
        if name not in inputs and name in required:
            prop = param.get("schema") if isinstance(param.get("schema"), dict) else {}
            inputs_value = _extract_named_value(message, name) or _extract_enum_value(message, prop)
            if inputs_value is None and name.lower() == "status":
                inputs_value = _extract_status_value(message)
            if inputs_value is None and name.lower() == "id":
                inputs_value = _extract_resource_id_for_action(message, action)
            if inputs_value is not None:
                inputs[name] = inputs_value

    for name in required:
        if name not in inputs:
            missing.append(str(name))
    return inputs, missing


def _extract_named_value(message: str, name: str) -> str | None:
    pattern = re.compile(rf"\b{re.escape(name)}\s*[:=]\s*([^\s,;]+)", re.IGNORECASE)
    match = pattern.search(message)
    if match:
        return match.group(1).strip().strip(".,;:!?\"'")
    return None


def _extract_resource_id_for_action(message: str, action: ActionNode) -> str | None:
    resource = _collection_resource_from_path(str(getattr(action, "path", "") or ""))
    if not resource:
        return None
    singular = _singular(resource)
    match = re.search(rf"\b((?:{re.escape(resource)}|{re.escape(singular)})_[A-Za-z0-9_]+)\b", message or "", re.IGNORECASE)
    return match.group(1) if match else None


def _has_explicit_resource_id(message: str, resource: str) -> bool:
    singular = _singular(resource)
    return bool(re.search(rf"\b(?:{re.escape(resource)}|{re.escape(singular)})_[A-Za-z0-9_]+\b", message or "", re.IGNORECASE))


def _extract_enum_value(message: str, prop: dict[str, Any]) -> str | None:
    options = prop.get("enum")
    if not isinstance(options, list):
        return None
    tokens = set(_tokens(message))
    for option in options:
        value = str(option)
        if value.lower() in tokens:
            return value
    return None


def _extract_status_value(message: str) -> str | None:
    tokens = set(_tokens(message))
    for value in ("available", "pending", "sold", "open", "closed", "active", "inactive"):
        if value in tokens:
            return value
    return None


def _extract_search_value(message: str, name: str) -> str | None:
    named_value = _extract_named_value(message, name)
    if named_value is not None:
        return named_value
    patterns = [
        r"\b(?:search|find|filter)\s+(?:for|by)?\s+(.+)$",
        r"\b(?:named|called|matching)\s+(.+)$",
        r"\b(?:buy|purchase|order)\s+(.+)$",
        r"\badd\s+(.+?)\s+(?:to|into)\s+(?:cart|basket|bag)\b",
        r"\bwith\s+(?:name|keyword|query|search)\s+(.+)$",
    ]
    for pattern in patterns:
        match = re.search(pattern, message, re.IGNORECASE)
        if not match:
            continue
        value = _clean_search_value(match.group(1))
        if value:
            return value
    return None


def _clean_search_value(value: str) -> str | None:
    cleaned = value.strip().strip(".,;:!?\"'")
    if not cleaned:
        return None
    tokens = _tokens(cleaned)
    if tokens and set(tokens) <= {"product", "products", "item", "items", "order", "orders", "customer", "customers"}:
        return None
    return cleaned


def _format_candidate_summary(candidates: list[ToolCandidate]) -> str:
    return "\n".join(
        f"- `{row.tool.name}` ({row.action.method} {row.action.path}, score {row.score})"
        for row in candidates[:5]
    )


def _format_router_decision(decision: ToolRouterDecision) -> str:
    if decision.type == ToolRouterDecisionType.BLOCK_UNSAFE:
        return (
            "I blocked this API request because it looks unsafe for the sandbox.\n\n"
            f"Reason: {decision.reason or 'Unsafe request'}\n\n"
            "Try a narrower operation with explicit identifiers, or ask for a read-only preview first."
        )
    detail_hints = _clarification_hints(decision.candidates)
    return (
        "I need one more detail so I can do the right thing.\n\n"
        f"{detail_hints}\n\n"
        "Reply in plain language with the missing detail."
    )


def _format_execution_failure(*, tool_name: str, result: dict[str, Any], trace_token: str, public_response: bool = False) -> str:
    error_text = str(result.get("error") or "Unknown error")
    status = result.get("status_code", 0)
    if status == 0 or "connection" in error_text.lower():
        summary = "I could not reach the connected API."
    else:
        summary = "The connected API returned an error."
    if public_response:
        if "credential" in error_text.lower() or result.get("error_type") in {"InvalidToken", "InvalidSignature"}:
            detail = "The store owner needs to reconnect the API credentials before I can use this integration."
        else:
            detail = "The store owner may need to check the connected API configuration."
        return (
            f"{summary}\n\n"
            f"{detail}\n\n"
            "Try again after the API is reachable, or ask for a narrower request."
        )
    return (
        f"{summary}\n\n"
        f"Error: {error_text}\n"
        f"Status: {status}\n\n"
        f"Trace: `{trace_token}`\n\n"
        "Try again after the API is reachable, or ask for a narrower request."
    )


def _candidate_summary_rows(candidates: list[ToolCandidate]) -> list[dict[str, Any]]:
    return [
        {
            "tool_name": row.tool.name,
            "method": row.action.method,
            "path": row.action.path,
            "score": row.score,
            "reason": row.reason,
        }
        for row in candidates[:5]
    ]


def _clarification_hints(candidates: list[Any]) -> str:
    path_params: list[str] = []
    collection_labels: list[str] = []
    for candidate in candidates[:5]:
        action = getattr(candidate, "action", None)
        path = str(getattr(action, "path", "") or "")
        params = [
            str(parameter.get("name"))
            for parameter in (getattr(action, "parameters", None) or [])
            if isinstance(parameter, dict)
            and parameter.get("required")
            and str(parameter.get("in") or "").lower() not in {"header", "cookie"}
        ]
        path_params.extend(params)
        label = _entity_label_from_path(path)
        if label and label not in collection_labels:
            collection_labels.append(label)
    if path_params:
        readable = ", ".join(_humanize_name(name) for name in sorted(set(path_params)))
        if collection_labels:
            return f"Do you want the {', '.join(collection_labels)} list, or details for a specific item? If it is a specific item, include {readable}."
        return f"If this is about a specific item, include {readable}."
    if collection_labels:
        return f"Are you asking to list, search, or filter {', '.join(collection_labels)}?"
    return "Please add the target, filter, or identifier you want me to use."


def _entity_label_from_path(path: str) -> str:
    parts = [part for part in path.split("/") if part and not part.startswith("{")]
    if not parts:
        return ""
    return _humanize_name(parts[-1])


def _humanize_name(value: str) -> str:
    return str(value).replace("_", " ").replace("-", " ")


def _format_missing_input_names(missing: list[str], action: ActionNode) -> str:
    return ", ".join(_humanize_missing_input(name, action) for name in missing)


def _humanize_missing_input(name: str, action: ActionNode) -> str:
    if name == "id":
        path = str(getattr(action, "path", "") or "")
        match = re.search(r"/([^/{]+)/\{id\}", path)
        if match:
            return f"{_singular_label(match.group(1))} id"
    return _humanize_name(name)


def _singular_label(value: str) -> str:
    label = _humanize_name(value).strip()
    return label[:-1] if label.endswith("s") and len(label) > 3 else label


def _preview_body(body: Any) -> Any:
    return _bounded_preview(body)


def _preview_body_json(body: Any) -> str:
    return json.dumps(body, indent=2, default=str)


def _bounded_preview(value: Any, *, depth: int = 0) -> Any:
    if depth >= 5:
        if isinstance(value, dict):
            return {"__preview_truncated": "nested object omitted"}
        if isinstance(value, list):
            return [{"__preview_truncated": "nested list omitted"}]
    if isinstance(value, list):
        items = [_bounded_preview(item, depth=depth + 1) for item in value[:5]]
        if len(value) > 5:
            items.append({"__preview_truncated": f"{len(value) - 5} more items"})
        return items
    if isinstance(value, dict):
        keys = list(value.keys())
        preview = {key: _bounded_preview(value[key], depth=depth + 1) for key in keys[:20]}
        if len(keys) > 20:
            preview["__preview_truncated"] = f"{len(keys) - 20} more fields"
        return preview
    if isinstance(value, str) and len(value) > 600:
        return f"{value[:600]}... [truncated {len(value) - 600} chars]"
    return value


async def _append_public_approval_message(
    trace: AgentExecutionTrace,
    message: str,
    result: dict[str, Any] | None,
    db: AsyncSession,
) -> None:
    if trace.session_id is None:
        return
    from backend.services.deployed_agent_events import publish_public_agent_message

    content = message
    if result and not result.get("error"):
        content = (
            f"{message}\n\n"
            f"Result preview:\n```json\n{_preview_body_json(result.get('body'))}\n```"
        )
    agent_message = AgentMessage(
        session_id=trace.session_id,
        saas_agent_id=trace.saas_agent_id,
        role="assistant",
        content=content,
        metadata_={"channel": "deployed_web", "approval_event": True, "approval_trace_id": str(trace.id)},
    )
    db.add(agent_message)
    await db.commit()
    await db.refresh(agent_message)
    await publish_public_agent_message(agent_message)


def _tokens(value: str) -> list[str]:
    normalized = re.sub(r"([a-z0-9])([A-Z])", r"\1 \2", value or "")
    normalized = re.sub(r"[_/.-]+", " ", normalized)
    tokens: list[str] = []
    for raw in _TOKEN_RE.findall(normalized):
        token = raw.lower().strip("_-/")
        if len(token) <= 1:
            continue
        tokens.append(token)
        if token.endswith("s") and len(token) > 3:
            tokens.append(token[:-1])
    return tokens


def _looks_like_api_task(message: str) -> bool:
    return bool(set(_tokens(message)) & _EXECUTION_HINTS)


def _is_generic_public_capability_message(message: str) -> bool:
    tokens = set(_tokens(message))
    if not tokens:
        return False
    domain_terms = {
        "address",
        "basket",
        "buy",
        "cart",
        "catalog",
        "checkout",
        "country",
        "delivery",
        "inventory",
        "item",
        "items",
        "order",
        "orders",
        "payment",
        "product",
        "products",
        "purchase",
        "region",
        "sell",
        "selling",
        "ship",
        "shipping",
        "size",
        "sizes",
        "store",
    }
    if tokens & domain_terms or _has_write_intent(message) or _looks_like_collection_read_request(message):
        return False
    greeting_terms = {"hello", "hey", "hi"}
    filler_terms = {"again", "me", "please", "there", "with", "you"}
    if tokens & greeting_terms and tokens <= greeting_terms | filler_terms:
        return True
    if tokens & {"capability", "capabilities"}:
        return True
    if "help" in tokens:
        return True
    if {"what", "you"} <= tokens and tokens & {"can", "could"} and "do" in tokens:
        return True
    return False


def _required_count(tool: GeneratedTool) -> int:
    schema = (getattr(tool, "function_schema", None) or {}).get("parameters") or {}
    return len(schema.get("required") or []) if isinstance(schema, dict) else 0


def _risk_value(value: Any) -> str:
    return value.value if hasattr(value, "value") else str(value)


def _is_scalar(value: Any) -> bool:
    return isinstance(value, str | int | float | bool)


def _parse_trace_control(message: str) -> tuple[str, str] | None:
    match = re.search(r"\b(approve|cancel|reject)\s+([a-f0-9-]{8,36})\b", message, re.IGNORECASE)
    if not match:
        return None
    command = match.group(1).lower()
    if command == "reject":
        command = "cancel"
    return command, match.group(2).lower()


async def _find_trace_by_token(db: AsyncSession, saas_agent_id: uuid.UUID, token: str) -> AgentExecutionTrace | None:
    result = await db.execute(
        select(AgentExecutionTrace)
        .where(AgentExecutionTrace.saas_agent_id == saas_agent_id)
        .order_by(AgentExecutionTrace.created_at.desc())
        .limit(100)
    )
    for trace in result.scalars().all():
        if str(trace.id).lower().startswith(token):
            return trace
    return None


async def _candidate_from_trace(db: AsyncSession, trace: AgentExecutionTrace) -> ToolCandidate | None:
    if not trace.generated_tool_id or not trace.action_node_id or not trace.connection_id:
        return None
    result = await db.execute(
        select(GeneratedTool, ActionNode, Connection)
        .join(ActionNode, GeneratedTool.action_node_id == ActionNode.id)
        .join(Connection, GeneratedTool.connection_id == Connection.id)
        .options(selectinload(Connection.credentials))
        .where(
            GeneratedTool.id == trace.generated_tool_id,
            ActionNode.id == trace.action_node_id,
            Connection.id == trace.connection_id,
        )
    )
    row = result.first()
    if row is None:
        return None
    tool, action, connection = row
    return ToolCandidate(tool=tool, action=action, connection=connection, score=0, reason="approved_trace_resume")


async def _approved_learning_hints(db: AsyncSession, saas_agent_id: uuid.UUID) -> list[dict[str, str]]:
    try:
        from backend.services.agent.learning_service import learning_service

        hints = await learning_service.approved_hints(saas_agent_id=saas_agent_id, db=db)
    except Exception:
        return []
    return [
        {
            "tool_name": hint.target_tool_name or "",
            "path": hint.target_action_path or "",
            "hint_text": hint.hint_text or "",
        }
        for hint in hints
    ]


def _learning_bonus(tokens: set[str], tool_name: str, path: str | None, hints: list[dict[str, str]]) -> int:
    bonus = 0
    for hint in hints:
        hint_tokens = set(_tokens(" ".join([hint["tool_name"], hint["path"], hint["hint_text"]])))
        if tool_name == hint["tool_name"] or (path and path == hint["path"]):
            bonus += 1
        if tokens & hint_tokens:
            bonus += 1
    return min(bonus, 3)
