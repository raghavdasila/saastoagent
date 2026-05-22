from __future__ import annotations

import json
import re
import time
import uuid
from dataclasses import dataclass
from typing import Any

import httpx
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from backend.core.credentials import decrypt_value, inject_credentials
from backend.core.models import ActionNode, AgentExecutionTrace, AgentMessage, Connection, GeneratedTool, RiskLevel
from backend.services.toolrouter.adapter import ToolRouterAdapter, ToolRouterDecision, ToolRouterDecisionType

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
_WRITE_RISKS = {RiskLevel.write.value, RiskLevel.destructive.value, RiskLevel.financial.value}


@dataclass
class ToolCandidate:
    tool: GeneratedTool
    action: ActionNode
    connection: Connection
    score: int
    reason: str


async def run_rest_operator_turn(
    *,
    message: str,
    saas_agent_id: uuid.UUID,
    session_id: uuid.UUID | None = None,
    user_id: uuid.UUID | None = None,
    db: AsyncSession,
    emit,
    public_response: bool = False,
) -> str | None:
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

    candidates = await find_tool_candidates(message=message, saas_agent_id=saas_agent_id, db=db, limit=5)
    if not candidates:
        return None

    top = candidates[0]
    if top.score < 2 and not _looks_like_api_task(message):
        return None

    candidate_summary = _format_candidate_summary(candidates)
    candidate_summary_rows = _candidate_summary_rows(candidates)
    risk = _risk_value(top.tool.risk_level)
    inputs, missing = _build_inputs(message, top.action, top.tool)
    decision = ToolRouterAdapter().decide(
        message=message,
        candidates=candidates,
        inputs=inputs,
        missing=missing,
    )

    if decision.type in {ToolRouterDecisionType.SHOW_TOPK, ToolRouterDecisionType.BLOCK_UNSAFE}:
        return _format_router_decision(decision)

    if decision.type == ToolRouterDecisionType.ASK_PARAM:
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
        content = (
            "I need one more detail before I can do that.\n\n"
            f"Please provide: {', '.join(_humanize_name(name) for name in missing)}.\n\n"
            "Once you provide that, I can continue."
        )
        if not public_response:
            content = content.replace("\n\nOnce you provide", f"\n\nTrace: `{str(trace.id)[:8]}`\n\nOnce you provide")
        return content

    if decision.type == ToolRouterDecisionType.ASK_POLICY:
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
    result = await execute_rest_tool(top, inputs, db)
    await finalize_execution_trace(trace, result, db)
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
        return (
            "Here’s what I found.\n\n"
            f"```json\n{json.dumps(_preview_body(result.get('body')), indent=2, default=str)[:2500]}\n```\n\n"
            "You can ask me to check another item or narrow the result."
        )

    return (
        "Here’s what I found.\n\n"
        f"Status: {result.get('status_code')}\n"
        f"Duration: {result.get('duration_ms')} ms\n\n"
        f"Trace: `{str(trace.id)[:8]}`\n\n"
        f"Result preview:\n```json\n{json.dumps(_preview_body(result.get('body')), indent=2, default=str)[:2500]}\n```\n\n"
        "You can ask me to check another item or narrow the result."
    )


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
    if status == "needs_input":
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
    try:
        from backend.services.agent.rag_service import rag_service

        await rag_service.ingest_generated_knowledge(saas_agent_id=trace.saas_agent_id, db=db)
    except Exception:
        # Execution should not fail because retrieval refresh failed.
        pass
    if trace.status == "failed":
        try:
            from backend.services.agent.learning_service import learning_service

            await learning_service.propose_from_trace(trace, db)
        except Exception:
            pass


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
        f"Result preview:\n```json\n{json.dumps(_preview_body(result.get('body')), indent=2, default=str)[:2500]}\n```"
    )


async def find_tool_candidates(
    *,
    message: str,
    saas_agent_id: uuid.UUID,
    db: AsyncSession,
    limit: int = 5,
) -> list[ToolCandidate]:
    result = await db.execute(
        select(GeneratedTool, ActionNode, Connection)
        .join(ActionNode, GeneratedTool.action_node_id == ActionNode.id)
        .join(Connection, GeneratedTool.connection_id == Connection.id)
        .options(selectinload(Connection.credentials))
        .where(GeneratedTool.saas_agent_id == saas_agent_id)
    )
    tokens = set(_tokens(message))
    learning_hints = await _approved_learning_hints(db, saas_agent_id)
    candidates: list[ToolCandidate] = []
    for tool, action, connection in result.all():
        haystack = " ".join(
            [
                tool.name or "",
                tool.description or "",
                action.name or "",
                action.description or "",
                action.path or "",
                action.method or "",
                " ".join(str(tag) for tag in (action.tags or [])),
            ]
        )
        hay_tokens = set(_tokens(haystack))
        score = len(tokens & hay_tokens)
        method = (action.method or "").lower()
        if method in tokens:
            score += 2
        if method == "get" and tokens & {"list", "find", "fetch", "show", "search"}:
            score += 1
        if score <= 0:
            continue
        score += _learning_bonus(tokens, tool.name, action.path, learning_hints)
        reason = ", ".join(sorted(list(tokens & hay_tokens))[:5]) or action.method
        candidates.append(ToolCandidate(tool=tool, action=action, connection=connection, score=score, reason=reason))
    return sorted(candidates, key=lambda row: (-row.score, _required_count(row.tool), row.tool.name))[:limit]


async def execute_rest_tool(candidate: ToolCandidate, inputs: dict[str, Any], db: AsyncSession) -> dict[str, Any]:
    action = candidate.action
    connection = candidate.connection
    headers: dict[str, str] = {}
    params: dict[str, Any] = {}
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

    started = time.monotonic()
    try:
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
        return {"status_code": 0, "body": None, "duration_ms": round((time.monotonic() - started) * 1000, 2), "error": str(exc)}


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
        return match.group(1).strip()
    return None


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
        return (
            f"{summary}\n\n"
            f"Error: {error_text}\n\n"
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
            if isinstance(parameter, dict) and parameter.get("required")
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


def _preview_body(body: Any) -> Any:
    if isinstance(body, list):
        return body[:5]
    if isinstance(body, dict):
        return {key: body[key] for key in list(body.keys())[:20]}
    return body


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
            f"Result preview:\n```json\n{json.dumps(_preview_body(result.get('body')), indent=2, default=str)[:2500]}\n```"
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


def _required_count(tool: GeneratedTool) -> int:
    schema = (tool.function_schema or {}).get("parameters") or {}
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
