from __future__ import annotations

import uuid
from typing import Any

from fastapi_users.db import SQLAlchemyUserDatabase
from sqlalchemy.ext.asyncio import AsyncSession

from backend.core.auth import UserManager, get_jwt_strategy
from backend.core.models import User, Workspace, WorkspaceMember, WorkspaceRole
from backend.core.schemas import UserCreate
from backend.core.tenancy import create_tenant_schema

from .domain import QA_DOMAIN_MODEL, QA_SCENARIOS
from .schemas import QAEvalRequest, QAEvalResponse, QAResetResponse, QAScenario

QA_PASSWORD = "SaaStoAgent-QA-123!"


def list_scenarios() -> list[QAScenario]:
    return [QAScenario.model_validate(item) for item in QA_SCENARIOS]


def domain_model() -> dict[str, Any]:
    return QA_DOMAIN_MODEL


def is_reset_allowed(auth_secret: str) -> bool:
    return auth_secret in {"CHANGE-ME-IN-PRODUCTION", "dev-secret-change-in-prod"}


def _strings_from_evidence(evidence: dict[str, Any], key: str) -> list[str]:
    value = evidence.get(key)
    if isinstance(value, list):
        return [str(item) for item in value]
    if isinstance(value, str):
        return [value]
    return []


def _visible_text(evidence: dict[str, Any]) -> str:
    parts = [str(evidence.get("visible_text") or "")]
    parts.extend(_strings_from_evidence(evidence, "messages"))
    return "\n".join(parts).lower()


def _action_ids(evidence: dict[str, Any], key: str) -> set[str]:
    value = evidence.get(key)
    if not isinstance(value, list):
        return set()
    ids: set[str] = set()
    for item in value:
        if isinstance(item, str):
            ids.add(item)
        elif isinstance(item, dict) and isinstance(item.get("id"), str):
            ids.add(item["id"])
    return ids


def _catalog_count(evidence: dict[str, Any], key: str) -> int | None:
    totals = evidence.get("catalog_totals")
    if isinstance(totals, dict) and isinstance(totals.get(key), int):
        return int(totals[key])
    value = evidence.get(key)
    if isinstance(value, int):
        return value
    if isinstance(value, list):
        return len(value)
    return None


def _tool_names(evidence: dict[str, Any]) -> list[str]:
    value = evidence.get("tool_calls")
    if not isinstance(value, list):
        return []
    names: list[str] = []
    for item in value:
        if isinstance(item, str):
            names.append(item)
        elif isinstance(item, dict):
            for key in ("tool_name", "toolName", "name", "id"):
                name = item.get(key)
                if isinstance(name, str) and name:
                    names.append(name)
                    break
    return names


def _status_from_evidence(evidence: dict[str, Any], key: str) -> int | None:
    value = evidence.get("api_status")
    if isinstance(value, int):
        return value

    statuses = evidence.get("api_statuses")
    if isinstance(statuses, dict) and isinstance(statuses.get(key), int):
        return int(statuses[key])

    responses = evidence.get("api_responses")
    if isinstance(responses, dict):
        response = responses.get(key)
        if isinstance(response, int):
            return response
        if isinstance(response, dict) and isinstance(response.get("status"), int):
            return int(response["status"])
    return None


def _gate_passes(gate: str, params: dict[str, Any], evidence: dict[str, Any]) -> bool:
    text = _visible_text(evidence)
    if gate == "assistant_response":
        messages = _strings_from_evidence(evidence, "assistant_messages")
        return any(message.strip() for message in messages)
    if gate == "visible_text":
        expected = str(params.get("text") or "").lower()
        return bool(expected) and expected in text
    if gate == "message_not_contains":
        forbidden = str(params.get("text") or "").lower()
        return bool(forbidden) and forbidden not in text
    if gate == "route_deck_snapshot_present":
        return bool(evidence.get("route_deck_snapshot_present"))
    if gate == "route_deck_current_node":
        return evidence.get("current_node") == params.get("node")
    if gate == "route_deck_current_node_one_of":
        nodes = params.get("nodes")
        return isinstance(nodes, list) and evidence.get("current_node") in nodes
    if gate == "action_enabled":
        action_id = str(params.get("action_id") or "")
        return action_id in _action_ids(evidence, "enabled_action_ids")
    if gate == "no_console_errors":
        return len(_strings_from_evidence(evidence, "console_errors")) == 0
    if gate == "workspace_view":
        aliases = {"connections": "connect"}
        expected = aliases.get(str(params.get("view") or ""), str(params.get("view") or ""))
        current = evidence.get("workspace_view") or evidence.get("active_view") or evidence.get("current_view")
        current_text = aliases.get(str(current or ""), str(current or ""))
        return bool(expected) and current_text == expected
    if gate == "catalog_count_at_least":
        key = str(params.get("key") or "")
        minimum = int(params.get("min") or 1)
        count = _catalog_count(evidence, key)
        return count is not None and count >= minimum
    if gate == "tool_called":
        expected = str(params.get("tool_name_contains") or params.get("tool_name") or "").lower()
        names = [name.lower() for name in _tool_names(evidence)]
        if not expected:
            return bool(names)
        return any(expected in name for name in names)
    if gate == "api_response_ok":
        key = str(params.get("key") or "")
        status = _status_from_evidence(evidence, key)
        return status is not None and 200 <= status < 300
    return False


def evaluate_turn(body: QAEvalRequest) -> QAEvalResponse:
    gates: dict[str, bool] = {}
    failures: list[str] = []
    for index, gate in enumerate(body.evidence_gates):
        key = f"{gate.gate}:{index}"
        passed = _gate_passes(gate.gate, gate.params, body.evidence)
        gates[key] = passed
        if gate.required and not passed:
            failures.append(gate.gate)

    verdict = "pass" if not failures else "fail"
    reasoning = "All required evidence gates passed." if verdict == "pass" else f"Failed gates: {', '.join(failures)}."
    return QAEvalResponse(
        qa_run_id=str(uuid.uuid4()),
        verdict=verdict,
        confidence=1.0 if verdict == "pass" else 0.85,
        reasoning=reasoning,
        gates=gates,
        failures=failures,
    )


async def _create_user(session: AsyncSession, *, email: str, display_name: str) -> User:
    manager = UserManager(SQLAlchemyUserDatabase(session, User))
    return await manager.create(
        UserCreate(email=email, password=QA_PASSWORD, display_name=display_name),
        safe=False,
    )


async def _create_workspace(session: AsyncSession, *, user: User, run_token: str) -> Workspace:
    workspace = Workspace(
        name="QA Seed Workspace",
        slug=f"qa-seed-{run_token}",
        created_by=user.id,
    )
    session.add(workspace)
    await session.flush()
    session.add(
        WorkspaceMember(
            user_id=user.id,
            workspace_id=workspace.id,
            role=WorkspaceRole.owner,
        )
    )
    await session.flush()
    await session.commit()
    await create_tenant_schema(workspace.id)
    await session.refresh(workspace)
    return workspace


async def reset_qa_context(session: AsyncSession) -> QAResetResponse:
    run_token = uuid.uuid4().hex[:10]
    seeded_email = f"qa-seeded-{run_token}@example.com"
    signup_email = f"qa-signup-{run_token}@example.com"
    seeded_user = await _create_user(session, email=seeded_email, display_name="QA Seeded User")
    workspace = await _create_workspace(session, user=seeded_user, run_token=run_token)
    await get_jwt_strategy().write_token(seeded_user)

    return QAResetResponse(
        qa_run_id=f"qa-{run_token}",
        signup_email=signup_email,
        signup_password=QA_PASSWORD,
        seeded_email=seeded_email,
        seeded_password=QA_PASSWORD,
        seeded_workspace_id=str(workspace.id),
        seeded_workspace_name=workspace.name,
    )
