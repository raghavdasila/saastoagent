from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from fastapi import HTTPException, status

from backend.core.models import SaaSAgent, SaaSAgentRole
from backend.core.schemas import CorpusGraphState, EntryGraphMessage
from backend.services.agent.memory_service import memory_service
from backend.services.agent.rag_service import rag_service
from backend.services.corpus.manifest import CorpusActionIds, CorpusNodeIds
from backend.services.deployed_agents import get_or_create_deployment

from .types import CorpusActionContext, CorpusActionResult


DEPLOYMENT_VISITOR_AUTH_MODES = {"inherit_from_connection", "anonymous", "login_required"}
DEPLOYMENT_EXECUTION_MODES = {"sandbox", "live"}
DEPLOYMENT_WRITE_POLICIES = {"confirm", "owner_approval", "block"}


async def knowledge_open(state: CorpusGraphState, payload: Mapping[str, Any], context: CorpusActionContext) -> CorpusActionResult:
    state.node = CorpusNodeIds.KNOWLEDGE
    return CorpusActionResult(state=state)


async def instructions_open(state: CorpusGraphState, payload: Mapping[str, Any], context: CorpusActionContext) -> CorpusActionResult:
    state.node = CorpusNodeIds.INSTRUCTIONS
    return CorpusActionResult(state=state)


async def deployment_save(state: CorpusGraphState, payload: Mapping[str, Any], context: CorpusActionContext) -> CorpusActionResult:
    if context.user is None or not state.active_saas_agent_id:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="SaaS Agent selection required")
    member = await context.queries.require_member(state.active_saas_agent_id, context.user, context.db)
    if member.role not in (SaaSAgentRole.owner, SaaSAgentRole.admin):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="SaaS Agent admin role required")

    deployment = await get_or_create_deployment(saas_agent_id=state.active_saas_agent_id, db=context.db)
    deployment.enabled = coerce_bool_payload(payload.get("enabled"), default=bool(deployment.enabled), field="enabled")
    deployment.visitor_auth_mode = coerce_choice_payload(
        payload.get("visitor_auth_mode"),
        default=deployment.visitor_auth_mode or "inherit_from_connection",
        field="visitor_auth_mode",
        allowed=DEPLOYMENT_VISITOR_AUTH_MODES,
    )
    deployment.execution_mode = coerce_choice_payload(
        payload.get("execution_mode"),
        default=deployment.execution_mode or "sandbox",
        field="execution_mode",
        allowed=DEPLOYMENT_EXECUTION_MODES,
    )
    deployment.default_write_policy = coerce_choice_payload(
        payload.get("default_write_policy"),
        default=deployment.default_write_policy or "confirm",
        field="default_write_policy",
        allowed=DEPLOYMENT_WRITE_POLICIES,
    )
    welcome_message = str(payload.get("welcome_message") or deployment.welcome_message or "How can I help?").strip()
    if not welcome_message:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="welcome_message is required")
    if len(welcome_message) > 2000:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="welcome_message is too long")
    deployment.welcome_message = welcome_message

    await context.db.commit()
    await context.db.refresh(deployment)
    state.node = CorpusNodeIds.AGENT_HOME
    state.graph_context["deployment"] = {
        "enabled": deployment.enabled,
        "visitor_auth_mode": deployment.visitor_auth_mode,
        "execution_mode": deployment.execution_mode,
        "default_write_policy": deployment.default_write_policy,
    }
    status_text = "published" if deployment.enabled else "disabled"
    return CorpusActionResult(
        state=state,
        messages=[EntryGraphMessage(content=f"Deployment settings saved. Public chat is {status_text}.")],
        evidence=[
            {
                "type": "deployment_saved",
                "saas_agent_id": str(state.active_saas_agent_id),
                "enabled": deployment.enabled,
                "visitor_auth_mode": deployment.visitor_auth_mode,
            }
        ],
    )


async def instructions_save(state: CorpusGraphState, payload: Mapping[str, Any], context: CorpusActionContext) -> CorpusActionResult:
    if context.user is None or not state.active_saas_agent_id:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="SaaS Agent selection required")
    member = await context.queries.require_member(state.active_saas_agent_id, context.user, context.db)
    if member.role not in (SaaSAgentRole.owner, SaaSAgentRole.admin):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="SaaS Agent admin role required")
    agent = await context.db.get(SaaSAgent, state.active_saas_agent_id)
    if agent is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="SaaS Agent not found")
    agent.system_prompt = str(payload.get("system_prompt") or "").strip() or None
    agent.instructions = str(payload.get("instructions") or "").strip() or None
    await context.db.commit()
    await context.db.refresh(agent)
    state.node = CorpusNodeIds.INSTRUCTIONS
    state.dirty_surfaces.pop("instructions", None)
    state.graph_context["instructions_saved"] = True
    return CorpusActionResult(
        state=state,
        messages=[EntryGraphMessage(content="Saved instructions for this SaaS Agent.")],
        evidence=[
            {
                "type": "instructions_saved",
                "saas_agent_id": str(agent.id),
                "system_prompt": agent.system_prompt,
                "instructions": agent.instructions,
            }
        ],
    )


async def knowledge_generate(state: CorpusGraphState, payload: Mapping[str, Any], context: CorpusActionContext) -> CorpusActionResult:
    if not state.active_saas_agent_id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="SaaS Agent selection required")
    result = await rag_service.ingest_generated_knowledge(saas_agent_id=state.active_saas_agent_id, db=context.db)
    state.node = CorpusNodeIds.KNOWLEDGE
    return CorpusActionResult(
        state=state,
        messages=[EntryGraphMessage(content=f"Generated catalog RAG: {result['documents']} documents, {result['chunks']} chunks.")],
        evidence=[{"type": "rag_generation", **result}],
    )


async def memory_open(state: CorpusGraphState, payload: Mapping[str, Any], context: CorpusActionContext) -> CorpusActionResult:
    state.node = CorpusNodeIds.MEMORY
    return CorpusActionResult(state=state)


async def memory_save(state: CorpusGraphState, payload: Mapping[str, Any], context: CorpusActionContext) -> CorpusActionResult:
    if context.user is None or not state.active_saas_agent_id:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="SaaS Agent selection required")
    memory = await memory_service.save(str(payload.get("content") or ""), saas_agent_id=state.active_saas_agent_id, category=str(payload.get("category") or "fact"), user_id=context.user.id, db=context.db)
    state.node = CorpusNodeIds.MEMORY
    return CorpusActionResult(
        state=state,
        messages=[EntryGraphMessage(content="Saved that memory for this SaaS Agent.")],
        evidence=[{"type": "memory_saved", "memory_id": str(memory.id)}],
    )


async def qa_open(state: CorpusGraphState, payload: Mapping[str, Any], context: CorpusActionContext) -> CorpusActionResult:
    state.node = CorpusNodeIds.QA
    return CorpusActionResult(state=state)


async def qa_run(state: CorpusGraphState, payload: Mapping[str, Any], context: CorpusActionContext) -> CorpusActionResult:
    state.node = CorpusNodeIds.QA
    return CorpusActionResult(
        state=state,
        messages=[EntryGraphMessage(content="QA scenarios are ready to validate the current flow and evidence.")],
        evidence=[{"type": "qa_contract", "scenario_basis": ["node_id", "action_id", "evidence"]}],
    )


def coerce_bool_payload(value: Any, *, default: bool, field: str) -> bool:
    if value is None or value == "":
        return default
    if isinstance(value, bool):
        return value
    normalized = str(value).strip().lower()
    if normalized in {"true", "1", "yes", "on"}:
        return True
    if normalized in {"false", "0", "no", "off"}:
        return False
    raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"{field} must be a boolean")


def coerce_choice_payload(value: Any, *, default: str, field: str, allowed: set[str]) -> str:
    normalized = str(value if value not in (None, "") else default).strip()
    if normalized not in allowed:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"{field} is invalid")
    return normalized


def build_content_handlers():
    return {
        CorpusActionIds.KNOWLEDGE_OPEN: knowledge_open,
        CorpusActionIds.INSTRUCTIONS_OPEN: instructions_open,
        CorpusActionIds.DEPLOYMENT_SAVE: deployment_save,
        CorpusActionIds.INSTRUCTIONS_SAVE: instructions_save,
        CorpusActionIds.KNOWLEDGE_GENERATE: knowledge_generate,
        CorpusActionIds.MEMORY_OPEN: memory_open,
        CorpusActionIds.MEMORY_SAVE: memory_save,
        CorpusActionIds.QA_OPEN: qa_open,
        CorpusActionIds.QA_RUN: qa_run,
    }
