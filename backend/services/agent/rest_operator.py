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
from backend.core.models import ActionNode, AgentExecutionTrace, Connection, GeneratedTool, RiskLevel

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
) -> str | None:
    approval_result = await _maybe_handle_trace_control(
        message=message,
        saas_agent_id=saas_agent_id,
        session_id=session_id,
        user_id=user_id,
        db=db,
        emit=emit,
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

    if risk in _WRITE_RISKS or top.tool.requires_approval:
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
        return (
            "I found the matching API action, but it needs approval before execution.\n\n"
            f"Candidate: `{top.tool.name}` on {top.connection.name}\n"
            f"Risk: `{risk}`\n"
            f"Trace: `{trace_token}`\n\n"
            f"Reply `approve {trace_token}` to execute it, or `cancel {trace_token}` to reject it."
        )

    if missing:
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
        return (
            "I found the likely API action, but it needs more inputs before it can run.\n\n"
            f"Candidate: `{top.tool.name}` on {top.connection.name}\n"
            f"Missing: {', '.join(f'`{name}`' for name in missing)}\n\n"
            f"Trace: `{str(trace.id)[:8]}`\n\n"
            f"Other close matches:\n{candidate_summary}"
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
    await emit("tool_start", {"tool_name": top.tool.name, "call_id": call_id, "inputs": inputs})
    result = await execute_rest_tool(top, inputs, db)
    await finalize_execution_trace(trace, result, db)
    output_text = json.dumps(result, default=str)[:5000]
    await emit("tool_end", {"call_id": call_id, "output": output_text})

    if result.get("error"):
        return (
            f"I selected `{top.tool.name}` but the API call failed.\n\n"
            f"Error: {result['error']}\n"
            f"Status: {result.get('status_code', 0)}\n\n"
            f"Trace: `{str(trace.id)[:8]}`\n\n"
            "The failure has enough trace detail for a learning candidate in the next pass."
        )

    return (
        f"I used `{top.tool.name}` from {top.connection.name}.\n\n"
        f"Status: {result.get('status_code')}\n"
        f"Duration: {result.get('duration_ms')} ms\n\n"
        f"Trace: `{str(trace.id)[:8]}`\n\n"
        f"Result preview:\n```json\n{json.dumps(_preview_body(result.get('body')), indent=2, default=str)[:2500]}\n```\n\n"
        f"Close action matches considered:\n{candidate_summary}"
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


async def _maybe_handle_trace_control(
    *,
    message: str,
    saas_agent_id: uuid.UUID,
    session_id: uuid.UUID | None,
    user_id: uuid.UUID | None,
    db: AsyncSession,
    emit,
) -> str | None:
    parsed = _parse_trace_control(message)
    if parsed is None:
        return None
    command, trace_token = parsed
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
                connection.auth_type.value if hasattr(connection.auth_type, "value") else str(connection.auth_type),
                decrypt_value(credential.encrypted_value),
                credential.metadata_ or {},
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
            inputs[name] = message

    for param in action.parameters or []:
        if not isinstance(param, dict) or not param.get("name"):
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


def _format_candidate_summary(candidates: list[ToolCandidate]) -> str:
    return "\n".join(
        f"- `{row.tool.name}` ({row.action.method} {row.action.path}, score {row.score})"
        for row in candidates[:5]
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


def _preview_body(body: Any) -> Any:
    if isinstance(body, list):
        return body[:5]
    if isinstance(body, dict):
        return {key: body[key] for key in list(body.keys())[:20]}
    return body


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
