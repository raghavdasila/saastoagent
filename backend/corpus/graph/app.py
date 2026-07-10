from __future__ import annotations

import asyncio
import json
import re
import uuid
from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any, AsyncIterator, TypeAlias

from fastapi import HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.core.config import settings
from backend.core.credentials import encrypt_value
from backend.core.models import (
    ActionNode,
    AgentExecutionTrace,
    AuthType,
    Connection,
    ConnectionActivationState,
    ConnectionType,
    EncryptedCredential,
    GeneratedTool,
    SaaSAgent,
    SaaSAgentMember,
    SaaSAgentRole,
    User,
)
from backend.core.schemas.saas_agent import SaaSAgentRead
from backend.corpus.schemas import (
    CorpusActionResponse,
    CorpusContextLens,
    CorpusGraphNavigationLocation,
    CorpusGraphRequest,
    CorpusGraphState,
    CorpusSurface,
)
from backend.core.tenancy import create_tenant_schema
from backend.services.agent.learning_service import learning_service
from backend.services.agent.memory_service import memory_service
from backend.services.agent.rag_service import rag_service
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
from backend.services.catalog import SaaSAgent_catalog, preview_openapi_spec
from backend.corpus.graph.definitions import (
    ACTION_TARGETS,
    CAPABILITY_RAIL_ITEMS,
    CORPUS_MANIFEST,
    CorpusActionIds,
    CorpusNodeIds,
    CorpusSurfaceCatalog,
    CorpusSurfaceSpec,
)
from backend.services.deployed_agents import get_or_create_deployment
from backend.services.discovery.activation import ActivationService
from backend.services.toolrouter import latest_ready_index, router_index_stats
from routedeck_core import (
    RouteDeckActionDispatcher,
    RouteDeckActionCard,
    RouteDeckActionField,
    RouteDeckActionResult,
    RouteDeckApp,
    RouteDeckDispatchInput,
    RouteDeckDispatchResult,
    RouteDeckGraphMessage,
    RouteDeckGraphNavigationController,
    RouteDeckIntrospection,
    RouteDeckManifest,
    RouteDeckNavigationPolicy,
    RouteDeckOperation,
    RouteDeckOperationPolicy,
    RouteDeckOperationRequestPolicy,
    RouteDeckProjection,
    RouteDeckRouteActionIds,
    RouteDeckRuntimeBase,
    RouteDeckSurface,
    RouteDeckSurfaceRegistry,
    build_runtime_snapshot,
)


def route_action_to_card(action: Any, payload: dict[str, Any] | None = None) -> RouteDeckActionCard:
    return RouteDeckActionCard(
        id=action.id,
        label=action.label,
        capability_id=action.capability_id,
        description=action.description,
        emphasis=action.emphasis,
        kind=action.kind,
        category=action.category,
        placement=action.placement,
        fields=[
            RouteDeckActionField(
                key=field.key,
                label=field.label,
                field_type=field.field_type,
                required=field.required,
                placeholder=field.placeholder,
                default=field.default,
                options=field.options,
                help_text=field.help_text,
                validation_hint=field.validation_hint,
                sensitive=field.sensitive,
            )
            for field in action.fields
        ],
        payload=payload or action.payload,
    )


CorpusActionResult: TypeAlias = RouteDeckActionResult[CorpusGraphState, RouteDeckGraphMessage]


@dataclass(slots=True)
class CorpusActionContext:
    user: User | None
    db: AsyncSession
    queries: CorpusContextQueries


class CorpusContextQueries:
    """Database-backed context and membership queries for Corpus graph runtime."""

    def __init__(self, *, node_by_id: dict[str, object]) -> None:
        self._node_by_id = node_by_id

    async def context_lens(self, state: CorpusGraphState, user: User | None, db: AsyncSession) -> CorpusContextLens:
        selected = await db.get(SaaSAgent, state.active_saas_agent_id) if state.active_saas_agent_id and user else None
        connection_count = ready_connection_count = action_count = tool_count = 0
        router_summary = None
        pending_status = None
        if selected is not None:
            connection_count = int((await db.execute(select(func.count(Connection.id)).where(Connection.saas_agent_id == selected.id))).scalar_one() or 0)
            ready_connection_count = int((await db.execute(select(func.count(ConnectionActivationState.connection_id)).where(ConnectionActivationState.saas_agent_id == selected.id, ConnectionActivationState.overall_status == "ready"))).scalar_one() or 0)
            action_count = int((await db.execute(select(func.count(ActionNode.id)).where(ActionNode.saas_agent_id == selected.id))).scalar_one() or 0)
            tool_count = int((await db.execute(select(func.count(GeneratedTool.id)).where(GeneratedTool.saas_agent_id == selected.id))).scalar_one() or 0)
            router_summary = router_index_stats(await latest_ready_index(session=db, saas_agent_id=selected.id))
            if state.pending_trace_id:
                trace = await db.get(AgentExecutionTrace, state.pending_trace_id)
                pending_status = trace.status if trace else None
        node = self._node_by_id.get(state.node)
        return CorpusContextLens(
            selected_saas_agent_id=selected.id if selected else None,
            selected_saas_agent_name=selected.name if selected else None,
            selected_saas_agent_slug=selected.slug if selected else None,
            current_node=state.node,
            working_on=getattr(node, "label", None) if node else "Recovery",
            connection_count=connection_count,
            ready_connection_count=ready_connection_count,
            action_count=action_count,
            tool_count=tool_count,
            router_index_status=router_summary.get("status") if router_summary else None,
            router_documents_count=int(router_summary.get("document_count", 0)) if router_summary else 0,
            router_endpoint_count=int(router_summary.get("endpoint_count", 0)) if router_summary else 0,
            router_version=router_summary.get("router_version") if router_summary else None,
            pending_trace_id=state.pending_trace_id,
            pending_trace_status=pending_status,
        )

    async def list_saas_agents(self, user: User | None, db: AsyncSession) -> list[SaaSAgentRead]:
        if user is None:
            return []
        result = await db.execute(select(SaaSAgent, SaaSAgentMember.role).join(SaaSAgentMember, SaaSAgentMember.saas_agent_id == SaaSAgent.id).where(SaaSAgentMember.user_id == user.id).order_by(SaaSAgent.created_at.desc()))
        return [
            SaaSAgentRead(
                id=agent.id,
                name=agent.name,
                slug=agent.slug,
                system_prompt=agent.system_prompt,
                instructions=agent.instructions,
                created_by=agent.created_by,
                created_at=agent.created_at,
                role=role.value if hasattr(role, "value") else str(role),
            )
            for agent, role in result.all()
        ]

    async def require_member(self, saas_agent_id: uuid.UUID, user: User, db: AsyncSession) -> SaaSAgentMember:
        member = (await db.execute(select(SaaSAgentMember).where(SaaSAgentMember.saas_agent_id == saas_agent_id, SaaSAgentMember.user_id == user.id))).scalar_one_or_none()
        if member is None:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not a member of this SaaS Agent")
        return member


async def handle_saas_agent_open(state: CorpusGraphState, payload: Mapping[str, Any], context: CorpusActionContext) -> CorpusActionResult:
    if context.user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Authentication required")
    raw_id = payload.get("saas_agent_id") or state.active_saas_agent_id
    if not raw_id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="saas_agent_id is required")
    state.active_saas_agent_id = uuid.UUID(str(raw_id))
    await context.queries.require_member(state.active_saas_agent_id, context.user, context.db)
    state.node = CorpusNodeIds.AGENT_HOME
    return CorpusActionResult(
        state=state,
        messages=[RouteDeckGraphMessage(content="I opened that SaaS Agent.")],
        evidence=[{"type": "saas_agent_selected", "saas_agent_id": str(state.active_saas_agent_id)}],
    )


async def handle_saas_agent_create(state: CorpusGraphState, payload: Mapping[str, Any], context: CorpusActionContext) -> CorpusActionResult:
    if context.user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Authentication required")
    name = str(payload.get("name") or "").strip()
    slug = str(payload.get("slug") or "").strip()
    if not name or not slug:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="name and slug are required")
    if (await context.db.execute(select(SaaSAgent).where(SaaSAgent.slug == slug))).scalar_one_or_none():
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="SaaS Agent slug already taken")
    agent = SaaSAgent(id=uuid.uuid4(), name=name, slug=slug, created_by=context.user.id)
    context.db.add(agent)
    context.db.add(SaaSAgentMember(user_id=context.user.id, saas_agent_id=agent.id, role=SaaSAgentRole.owner))
    await context.db.commit()
    await context.db.refresh(agent)
    await create_tenant_schema(agent.id)
    state.active_saas_agent_id = agent.id
    state.node = CorpusNodeIds.AGENT_HOME
    return CorpusActionResult(
        state=state,
        messages=[RouteDeckGraphMessage(content=f"Created {agent.name}. Next we can connect its API.")],
        evidence=[{"type": "saas_agent_created", "saas_agent_id": str(agent.id)}],
    )


async def handle_agent_home(state: CorpusGraphState, payload: Mapping[str, Any], context: CorpusActionContext) -> CorpusActionResult:
    state.node = CorpusNodeIds.AGENT_HOME
    return CorpusActionResult(state=state)


def build_agent_handlers():
    return {
        CorpusActionIds.SAAS_AGENT_OPEN: handle_saas_agent_open,
        CorpusActionIds.SAAS_AGENT_CREATE: handle_saas_agent_create,
        CorpusActionIds.AGENT_HOME: handle_agent_home,
    }


async def handle_connection_configure(state: CorpusGraphState, payload: Mapping[str, Any], context: CorpusActionContext) -> CorpusActionResult:
    state.node = CorpusNodeIds.CONNECTION_CONFIGURE
    return CorpusActionResult(state=state)


async def handle_connection_preview(state: CorpusGraphState, payload: Mapping[str, Any], context: CorpusActionContext) -> CorpusActionResult:
    preview = await preview_openapi_spec(spec_url=str(payload.get("spec_url") or ""), raw_spec=payload.get("raw_spec"))
    state.node = CorpusNodeIds.SCHEMA_PREVIEW
    state.graph_context["schema_preview"] = preview.model_dump()
    return CorpusActionResult(
        state=state,
        messages=[RouteDeckGraphMessage(content=f"Previewed `{preview.title}` with {preview.endpoint_count} endpoints.")],
        evidence=[{"type": "schema_preview", **preview.model_dump()}],
    )


async def handle_connection_activate(state: CorpusGraphState, payload: Mapping[str, Any], context: CorpusActionContext) -> CorpusActionResult:
    if context.user is None or not state.active_saas_agent_id:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="SaaS Agent selection required")
    await context.queries.require_member(state.active_saas_agent_id, context.user, context.db)
    connection_id = payload.get("connection_id")
    if connection_id:
        connection = await context.db.get(Connection, uuid.UUID(str(connection_id)))
        if connection is None or connection.saas_agent_id != state.active_saas_agent_id:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Connection not found")
    else:
        auth_type = str(payload.get("auth_type") or "none")
        connection = Connection(
            saas_agent_id=state.active_saas_agent_id,
            name=str(payload.get("name") or "Primary API"),
            type=ConnectionType.rest_api,
            provider="rest_api",
            config={
                "base_url": payload.get("base_url"),
                "spec_url": payload.get("spec_url"),
                "raw_spec": payload.get("raw_spec"),
                "auth_type": auth_type,
            },
            auth_type=AuthType(auth_type),
        )
        context.db.add(connection)
        await context.db.flush()
        credential_value = str(payload.get("credential_value") or "")
        if credential_value:
            context.db.add(EncryptedCredential(connection_id=connection.id, credential_type="credential_value", encrypted_value=encrypt_value(credential_value), metadata_={key: payload.get(key) for key in ("header_name", "query_param_name") if payload.get(key)}))
        context.db.add(ConnectionActivationState(connection_id=connection.id, saas_agent_id=state.active_saas_agent_id))
        await context.db.commit()
        await context.db.refresh(connection)
    state.active_connection_id = connection.id
    state.node = CorpusNodeIds.CATALOG_ACTIVATION
    events = []
    async for event in ActivationService().activate(connection_id=connection.id, saas_agent_id=state.active_saas_agent_id, session=context.db):
        events.append(event)
    state.node = CorpusNodeIds.CATALOG
    state.graph_context["activation_events"] = events
    state.graph_context["router_index"] = router_index_from_activation_events(events)
    return CorpusActionResult(
        state=state,
        messages=[RouteDeckGraphMessage(content="The API catalog is activated and ready to inspect.")],
        evidence=[{"type": "activation", "events": events}],
    )


async def handle_catalog_open(state: CorpusGraphState, payload: Mapping[str, Any], context: CorpusActionContext) -> CorpusActionResult:
    if state.active_saas_agent_id:
        catalog = await SaaSAgent_catalog(context.db, state.active_saas_agent_id)
        state.graph_context["catalog"] = catalog
        state.graph_context["router_index"] = catalog.get("router_index")
    state.node = CorpusNodeIds.CATALOG
    return CorpusActionResult(state=state)


async def handle_entities_open(state: CorpusGraphState, payload: Mapping[str, Any], context: CorpusActionContext) -> CorpusActionResult:
    state.node = CorpusNodeIds.ENTITIES
    return CorpusActionResult(state=state)


async def handle_actions_open(state: CorpusGraphState, payload: Mapping[str, Any], context: CorpusActionContext) -> CorpusActionResult:
    state.node = CorpusNodeIds.ACTIONS
    return CorpusActionResult(state=state)


def router_index_from_activation_events(events: list[dict[str, Any]]) -> dict[str, Any] | None:
    for event in reversed(events):
        if event.get("type") != "step" or event.get("step") != "router_index" or event.get("status") != "done":
            continue
        return {
            "status": event.get("router_index_status") or "ready",
            "router_version": event.get("router_version"),
            "document_count": int(event.get("router_documents_count") or 0),
            "endpoint_count": int(event.get("router_endpoint_count") or 0),
            "catalog_fingerprint": event.get("catalog_fingerprint"),
        }
    return None


def build_connection_handlers():
    return {
        CorpusActionIds.CONNECTION_CONFIGURE: handle_connection_configure,
        CorpusActionIds.CONNECTION_PREVIEW: handle_connection_preview,
        CorpusActionIds.CONNECTION_ACTIVATE: handle_connection_activate,
        CorpusActionIds.CATALOG_OPEN: handle_catalog_open,
        CorpusActionIds.ENTITIES_OPEN: handle_entities_open,
        CorpusActionIds.ACTIONS_OPEN: handle_actions_open,
    }


DEPLOYMENT_VISITOR_AUTH_MODES = {"inherit_from_connection", "anonymous", "login_required"}
DEPLOYMENT_EXECUTION_MODES = {"sandbox", "live"}
DEPLOYMENT_WRITE_POLICIES = {"confirm", "owner_approval", "block"}


async def handle_knowledge_open(state: CorpusGraphState, payload: Mapping[str, Any], context: CorpusActionContext) -> CorpusActionResult:
    state.node = CorpusNodeIds.KNOWLEDGE
    return CorpusActionResult(state=state)


async def handle_instructions_open(state: CorpusGraphState, payload: Mapping[str, Any], context: CorpusActionContext) -> CorpusActionResult:
    state.node = CorpusNodeIds.INSTRUCTIONS
    return CorpusActionResult(state=state)


async def handle_deployment_save(state: CorpusGraphState, payload: Mapping[str, Any], context: CorpusActionContext) -> CorpusActionResult:
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
        messages=[RouteDeckGraphMessage(content=f"Deployment settings saved. Public chat is {status_text}.")],
        evidence=[
            {
                "type": "deployment_saved",
                "saas_agent_id": str(state.active_saas_agent_id),
                "enabled": deployment.enabled,
                "visitor_auth_mode": deployment.visitor_auth_mode,
            }
        ],
    )


async def handle_instructions_save(state: CorpusGraphState, payload: Mapping[str, Any], context: CorpusActionContext) -> CorpusActionResult:
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
        messages=[RouteDeckGraphMessage(content="Saved instructions for this SaaS Agent.")],
        evidence=[
            {
                "type": "instructions_saved",
                "saas_agent_id": str(agent.id),
                "system_prompt": agent.system_prompt,
                "instructions": agent.instructions,
            }
        ],
    )


async def handle_knowledge_generate(state: CorpusGraphState, payload: Mapping[str, Any], context: CorpusActionContext) -> CorpusActionResult:
    if not state.active_saas_agent_id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="SaaS Agent selection required")
    result = await rag_service.ingest_generated_knowledge(saas_agent_id=state.active_saas_agent_id, db=context.db)
    state.node = CorpusNodeIds.KNOWLEDGE
    return CorpusActionResult(
        state=state,
        messages=[RouteDeckGraphMessage(content=f"Generated catalog RAG: {result['documents']} documents, {result['chunks']} chunks.")],
        evidence=[{"type": "rag_generation", **result}],
    )


async def handle_memory_open(state: CorpusGraphState, payload: Mapping[str, Any], context: CorpusActionContext) -> CorpusActionResult:
    state.node = CorpusNodeIds.MEMORY
    return CorpusActionResult(state=state)


async def handle_memory_save(state: CorpusGraphState, payload: Mapping[str, Any], context: CorpusActionContext) -> CorpusActionResult:
    if context.user is None or not state.active_saas_agent_id:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="SaaS Agent selection required")
    memory = await memory_service.save(str(payload.get("content") or ""), saas_agent_id=state.active_saas_agent_id, category=str(payload.get("category") or "fact"), user_id=context.user.id, db=context.db)
    state.node = CorpusNodeIds.MEMORY
    return CorpusActionResult(
        state=state,
        messages=[RouteDeckGraphMessage(content="Saved that memory for this SaaS Agent.")],
        evidence=[{"type": "memory_saved", "memory_id": str(memory.id)}],
    )


async def handle_qa_open(state: CorpusGraphState, payload: Mapping[str, Any], context: CorpusActionContext) -> CorpusActionResult:
    state.node = CorpusNodeIds.QA
    return CorpusActionResult(state=state)


async def handle_qa_run(state: CorpusGraphState, payload: Mapping[str, Any], context: CorpusActionContext) -> CorpusActionResult:
    state.node = CorpusNodeIds.QA
    return CorpusActionResult(
        state=state,
        messages=[RouteDeckGraphMessage(content="QA scenarios are ready to validate the current flow and evidence.")],
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
        CorpusActionIds.KNOWLEDGE_OPEN: handle_knowledge_open,
        CorpusActionIds.INSTRUCTIONS_OPEN: handle_instructions_open,
        CorpusActionIds.DEPLOYMENT_SAVE: handle_deployment_save,
        CorpusActionIds.INSTRUCTIONS_SAVE: handle_instructions_save,
        CorpusActionIds.KNOWLEDGE_GENERATE: handle_knowledge_generate,
        CorpusActionIds.MEMORY_OPEN: handle_memory_open,
        CorpusActionIds.MEMORY_SAVE: handle_memory_save,
        CorpusActionIds.QA_OPEN: handle_qa_open,
        CorpusActionIds.QA_RUN: handle_qa_run,
    }


async def handle_execution_open(state: CorpusGraphState, payload: Mapping[str, Any], context: CorpusActionContext) -> CorpusActionResult:
    state.node = CorpusNodeIds.EXECUTION_PLANNING
    return CorpusActionResult(state=state)


async def handle_execution_plan(state: CorpusGraphState, payload: Mapping[str, Any], context: CorpusActionContext) -> CorpusActionResult:
    if context.user is None or not state.active_saas_agent_id:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="SaaS Agent selection required")
    goal = str(payload.get("goal") or "").strip()
    if not goal:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="goal is required")
    candidates = await find_tool_candidates(message=goal, saas_agent_id=state.active_saas_agent_id, db=context.db, limit=5)
    if not candidates:
        state.node = CorpusNodeIds.RESULT_REVIEW
        return CorpusActionResult(state=state, messages=[RouteDeckGraphMessage(content="No generated API tool matched that goal.")], evidence=[{"type": "execution_candidates", "candidates": []}])
    top = candidates[0]
    inputs, missing = extract_inputs(goal, top.tool)
    summary = _candidate_summary_rows(candidates)
    risk = _risk_value(top.tool.risk_level)
    if missing:
        trace = await create_execution_trace(candidate=top, inputs=inputs, missing=missing, candidate_summary=summary, status="needs_input", approval_state="not_required", route_node=CorpusNodeIds.NEEDS_INPUT, saas_agent_id=state.active_saas_agent_id, session_id=None, user_id=context.user.id, db=context.db)
        state.pending_trace_id = trace.id
        state.node = CorpusNodeIds.NEEDS_INPUT
        return CorpusActionResult(state=state, messages=[RouteDeckGraphMessage(content=f"`{top.tool.name}` needs more input before execution.")], evidence=[{"type": "needs_input", "trace_id": str(trace.id), "missing": missing, "candidates": summary}])
    if risk != "read" or top.tool.requires_approval:
        trace = await create_execution_trace(candidate=top, inputs=inputs, missing=[], candidate_summary=summary, status="approval_required", approval_state="pending", route_node=CorpusNodeIds.APPROVAL_REQUIRED, saas_agent_id=state.active_saas_agent_id, session_id=None, user_id=context.user.id, db=context.db)
        state.pending_trace_id = trace.id
        state.node = CorpusNodeIds.APPROVAL_REQUIRED
        return CorpusActionResult(state=state, messages=[RouteDeckGraphMessage(content=f"`{top.tool.name}` requires approval before execution.")], evidence=[{"type": "approval_required", "trace_id": str(trace.id), "risk": risk, "candidates": summary}])
    trace = await create_execution_trace(candidate=top, inputs=inputs, missing=[], candidate_summary=summary, status="executing", approval_state="not_required", route_node=CorpusNodeIds.EXECUTING, saas_agent_id=state.active_saas_agent_id, session_id=None, user_id=context.user.id, db=context.db)
    result = await execute_rest_tool(top, inputs, context.db)
    await finalize_execution_trace(trace, result, context.db)
    state.pending_trace_id = trace.id
    state.node = CorpusNodeIds.RESULT_REVIEW
    state.graph_context["execution_result"] = result
    return CorpusActionResult(state=state, messages=[RouteDeckGraphMessage(content=f"Executed `{top.tool.name}` with status {result.get('status_code')}.")], evidence=[{"type": "execution_result", "trace_id": str(trace.id), "result": result, "candidates": summary, "preview": _preview_body(result.get("body"))}])


async def handle_approval_approve(state: CorpusGraphState, payload: Mapping[str, Any], context: CorpusActionContext) -> CorpusActionResult:
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
    return CorpusActionResult(state=state, messages=[RouteDeckGraphMessage(content=f"Approved and executed `{trace.tool_name}`.")], evidence=[{"type": "approval_approved", "trace_id": str(trace.id), "result": result}])


async def handle_approval_reject(state: CorpusGraphState, payload: Mapping[str, Any], context: CorpusActionContext) -> CorpusActionResult:
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
    return CorpusActionResult(state=state, messages=[RouteDeckGraphMessage(content=f"Rejected execution trace `{str(trace.id)[:8]}`.")], evidence=[{"type": "approval_rejected", "trace_id": str(trace.id)}])


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
        CorpusActionIds.EXECUTION_OPEN: handle_execution_open,
        CorpusActionIds.EXECUTION_PLAN: handle_execution_plan,
        CorpusActionIds.APPROVAL_APPROVE: handle_approval_approve,
        CorpusActionIds.APPROVAL_REJECT: handle_approval_reject,
    }


async def handle_learning_open(state: CorpusGraphState, payload: Mapping[str, Any], context: CorpusActionContext) -> CorpusActionResult:
    state.node = CorpusNodeIds.LEARNING
    return CorpusActionResult(state=state)


async def handle_learning_policy_candidate_open(state: CorpusGraphState, payload: Mapping[str, Any], context: CorpusActionContext) -> CorpusActionResult:
    candidate_id = str(payload.get("candidate_id") or "").strip()
    if not candidate_id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="candidate_id is required")
    state.node = CorpusNodeIds.LEARNING_POLICY_CANDIDATE
    state.route_params = {"candidate_id": candidate_id}
    state.active_surface_id = "learning.policy_candidate.review"
    return CorpusActionResult(state=state, evidence=[{"type": "learning_policy_candidate_opened", "candidate_id": candidate_id}])


async def handle_learning_execution_trace_open(state: CorpusGraphState, payload: Mapping[str, Any], context: CorpusActionContext) -> CorpusActionResult:
    trace_id = str(payload.get("trace_id") or "").strip()
    if not trace_id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="trace_id is required")
    state.node = CorpusNodeIds.LEARNING_EXECUTION_TRACE
    state.route_params = {"trace_id": trace_id}
    state.active_surface_id = "learning.execution_trace.review"
    return CorpusActionResult(state=state, evidence=[{"type": "learning_execution_trace_opened", "trace_id": trace_id}])


async def handle_learning_active_policy_open(state: CorpusGraphState, payload: Mapping[str, Any], context: CorpusActionContext) -> CorpusActionResult:
    candidate_id = str(payload.get("candidate_id") or "").strip()
    if not candidate_id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="candidate_id is required")
    state.node = CorpusNodeIds.LEARNING_ACTIVE_POLICY
    state.route_params = {"candidate_id": candidate_id}
    state.active_surface_id = "learning.active_policy.review"
    return CorpusActionResult(state=state, evidence=[{"type": "learning_active_policy_opened", "candidate_id": candidate_id}])


async def handle_learning_approve(state: CorpusGraphState, payload: Mapping[str, Any], context: CorpusActionContext) -> CorpusActionResult:
    return await review_learning(state, payload, context, "approved")


async def handle_learning_reject(state: CorpusGraphState, payload: Mapping[str, Any], context: CorpusActionContext) -> CorpusActionResult:
    return await review_learning(state, payload, context, "rejected")


async def review_learning(state: CorpusGraphState, payload: Mapping[str, Any], context: CorpusActionContext, review_status: str) -> CorpusActionResult:
    if context.user is None or not state.active_saas_agent_id:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="SaaS Agent selection required")
    candidate = await learning_service.review(candidate_id=uuid.UUID(str(payload.get("candidate_id"))), saas_agent_id=state.active_saas_agent_id, status=review_status, reviewed_by=context.user.id, db=context.db)
    if candidate is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Learning candidate not found")
    state.node = CorpusNodeIds.LEARNING
    return CorpusActionResult(
        state=state,
        messages=[RouteDeckGraphMessage(content=f"Learning candidate {review_status}.")],
        evidence=[{"type": "learning_reviewed", "candidate_id": str(candidate.id), "status": candidate.status}],
    )


def build_learning_handlers():
    return {
        CorpusActionIds.LEARNING_OPEN: handle_learning_open,
        CorpusActionIds.LEARNING_POLICY_CANDIDATE_OPEN: handle_learning_policy_candidate_open,
        CorpusActionIds.LEARNING_EXECUTION_TRACE_OPEN: handle_learning_execution_trace_open,
        CorpusActionIds.LEARNING_ACTIVE_POLICY_OPEN: handle_learning_active_policy_open,
        CorpusActionIds.LEARNING_APPROVE: handle_learning_approve,
        CorpusActionIds.LEARNING_REJECT: handle_learning_reject,
    }


def build_navigation_handlers(navigation: Any):
    async def route_back(state: CorpusGraphState, payload: Mapping[str, Any], context: CorpusActionContext) -> CorpusActionResult:
        navigation.move_back(state)
        return CorpusActionResult(state=state)

    async def route_forward(state: CorpusGraphState, payload: Mapping[str, Any], context: CorpusActionContext) -> CorpusActionResult:
        navigation.move_forward(state)
        return CorpusActionResult(state=state)

    async def route_cancel(state: CorpusGraphState, payload: Mapping[str, Any], context: CorpusActionContext) -> CorpusActionResult:
        navigation.cancel(state)
        return CorpusActionResult(state=state)

    async def route_open_node(state: CorpusGraphState, payload: Mapping[str, Any], context: CorpusActionContext) -> CorpusActionResult:
        navigation.open_node(state, payload)
        return CorpusActionResult(state=state)

    async def route_switch_surface(state: CorpusGraphState, payload: Mapping[str, Any], context: CorpusActionContext) -> CorpusActionResult:
        navigation.switch_surface(state, payload)
        return CorpusActionResult(state=state)

    async def navigate_home(state: CorpusGraphState, payload: Mapping[str, Any], context: CorpusActionContext) -> CorpusActionResult:
        state.node = CorpusNodeIds.HOME
        return CorpusActionResult(state=state)

    async def recovery_home(state: CorpusGraphState, payload: Mapping[str, Any], context: CorpusActionContext) -> CorpusActionResult:
        return await navigate_home(state, payload, context)

    async def auth_sign_in(state: CorpusGraphState, payload: Mapping[str, Any], context: CorpusActionContext) -> CorpusActionResult:
        state.node = CorpusNodeIds.AUTH_SIGN_IN
        return CorpusActionResult(state=state, messages=[RouteDeckGraphMessage(content="Sign in, and I will keep the current work ready for you.")])

    async def auth_register(state: CorpusGraphState, payload: Mapping[str, Any], context: CorpusActionContext) -> CorpusActionResult:
        state.node = CorpusNodeIds.AUTH_REGISTER
        return CorpusActionResult(state=state, messages=[RouteDeckGraphMessage(content="Create your account, and I will continue from here.")])

    return {
        CorpusActionIds.ROUTE_BACK: route_back,
        CorpusActionIds.ROUTE_FORWARD: route_forward,
        CorpusActionIds.ROUTE_CANCEL: route_cancel,
        CorpusActionIds.ROUTE_OPEN_NODE: route_open_node,
        CorpusActionIds.ROUTE_SWITCH_SURFACE: route_switch_surface,
        CorpusActionIds.HOME: navigate_home,
        CorpusActionIds.RECOVERY_HOME: recovery_home,
        CorpusActionIds.AUTH_SIGN_IN: auth_sign_in,
        CorpusActionIds.AUTH_REGISTER: auth_register,
    }


async def _default_action_handler(
    action_id: str,
    state: CorpusGraphState,
    payload: Mapping[str, Any],
    context: CorpusActionContext,
    *,
    action_targets: Mapping[str, str],
):
    state.node = action_targets[action_id]
    return RouteDeckActionResult[CorpusGraphState, RouteDeckGraphMessage](state=state)


def build_corpus_action_dispatcher(
    *,
    navigation: Any,
    action_targets: Mapping[str, str],
) -> RouteDeckActionDispatcher[CorpusGraphState, RouteDeckGraphMessage, CorpusActionContext]:
    handlers = {}
    handlers.update(build_navigation_handlers(navigation))
    handlers.update(build_agent_handlers())
    handlers.update(build_connection_handlers())
    handlers.update(build_execution_handlers())
    handlers.update(build_content_handlers())
    handlers.update(build_learning_handlers())

    async def default_handler(action_id: str, state: CorpusGraphState, payload: Mapping[str, Any], context: CorpusActionContext):
        return await _default_action_handler(action_id, state, payload, context, action_targets=action_targets)

    return RouteDeckActionDispatcher(handlers, default_handler=default_handler)


ALLOWED_TURN_PLAN_INTENTS = {
    "reply_now",
    "open_surface",
    "clarify",
    "deep_work",
    "propose_operation",
}
_CLARIFY_SAFE_MESSAGE = "I need a clearer next step from the currently available options."
_OPEN_SURFACE_INTENT = "open_surface"
_OPERATION_INTENTS = {"open_surface", "propose_operation"}
_INTERNAL_ROUTE_OPERATION_IDS = {
    CorpusActionIds.ROUTE_BACK,
    CorpusActionIds.ROUTE_FORWARD,
    CorpusActionIds.ROUTE_CANCEL,
    CorpusActionIds.ROUTE_OPEN_NODE,
    CorpusActionIds.ROUTE_SWITCH_SURFACE,
}

__all__ = [
    "build_corpus_turn_planning_context",
    "normalize_corpus_turn_plan",
    "resolve_explicit_navigation_turn",
]

_TOKEN_RE = re.compile(r"[a-z0-9]+")
_NAVIGATION_WORDS = {
    "connect",
    "go",
    "navigate",
    "open",
    "show",
    "start",
    "switch",
    "take",
    "view",
}
_STOP_WORDS = {
    "a",
    "an",
    "and",
    "can",
    "for",
    "i",
    "me",
    "my",
    "now",
    "please",
    "so",
    "that",
    "the",
    "there",
    "this",
    "to",
    "with",
}
_POLICY_REVIEW_TOKENS = {
    "approval",
    "approvals",
    "guard",
    "guarded",
    "guardrail",
    "guardrails",
    "policy",
    "policies",
    "protect",
    "protected",
    "safety",
    "safe",
}


def build_corpus_turn_planning_context(
    *,
    projection: RouteDeckProjection,
    state: CorpusGraphState,
) -> dict[str, Any]:
    active_surfaces = [
        _surface_summary(surface)
        for surface in projection.surfaces.values()
        if surface.role == "active" and surface.surface_id
    ]
    current_active_surface = _current_active_surface(
        active_surfaces=active_surfaces,
        projection=projection,
        state=state,
    )
    current_surface_id = current_active_surface["surface_id"] if current_active_surface else None
    current_node_id = state.node or projection.navigation.current.node_id or projection.graph_node
    return {
        "current": {
            "node_id": current_node_id,
            "surface_id": current_surface_id,
        },
        "active_saas_agent": _active_saas_agent_summary(projection=projection, state=state),
        "active_surface": current_active_surface,
        "active_surfaces": active_surfaces,
        "surface_options": _surface_options(active_surfaces),
        "visible_entities": _visible_entities(current_active_surface),
        "legal_operations": [
            _operation_summary(
                operation,
            )
            for operation in projection.legal_operations
            if _is_product_planning_operation(operation)
        ],
    }


def normalize_corpus_turn_plan(
    raw_plan: Any,
    *,
    planning_context: Mapping[str, Any],
) -> dict[str, Any]:
    payload = _coerce_mapping(raw_plan)
    intent = payload.get("intent")
    operation_id = payload.get("operation_id")
    legal_operations_by_id = {
        operation["id"]: operation
        for operation in planning_context.get("legal_operations", [])
        if isinstance(operation, Mapping) and isinstance(operation.get("id"), str)
    }
    legal_operation_ids = set(legal_operations_by_id)

    if intent not in ALLOWED_TURN_PLAN_INTENTS:
        return _clarify_safe_result()
    if operation_id is not None and not isinstance(operation_id, str):
        return _clarify_safe_result()
    if operation_id and operation_id not in legal_operation_ids:
        return _clarify_safe_result()
    surface_intent_valid, surface_intent = _normalize_surface_intent(
        payload.get("surface_intent"),
        planning_context=planning_context,
    )
    if not surface_intent_valid:
        return _clarify_safe_result()
    if intent == "propose_operation" and not operation_id:
        return _clarify_safe_result()
    if intent == _OPEN_SURFACE_INTENT and not operation_id and "surface_id" not in surface_intent:
        return _clarify_safe_result()

    operation = legal_operations_by_id.get(operation_id) if operation_id else None
    valid_args, normalized_args = _normalize_operation_args(
        operation=operation,
        raw_args=payload.get("args"),
    )
    if not valid_args:
        return _clarify_safe_result()
    normalized_intent = intent
    if operation_id and normalized_intent not in _OPERATION_INTENTS:
        normalized_intent = "propose_operation"
    normalized = {
        "intent": normalized_intent,
        "message": payload.get("message") if isinstance(payload.get("message"), str) else "",
        "operation_id": operation_id if normalized_intent in _OPERATION_INTENTS else None,
        "args": normalized_args,
        "surface_intent": surface_intent,
        "confidence": _normalize_confidence(payload.get("confidence")),
        "preamble": payload.get("preamble") if isinstance(payload.get("preamble"), str) else None,
    }
    if normalized["intent"] == "clarify" and not normalized["message"]:
        normalized["message"] = _CLARIFY_SAFE_MESSAGE
    return normalized


def resolve_explicit_navigation_turn(
    plan: Mapping[str, Any],
    *,
    user_input: str,
    planning_context: Mapping[str, Any],
) -> dict[str, Any]:
    normalized = dict(plan)
    priority_operation = _priority_navigation_operation(
        user_input=user_input,
        planning_context=planning_context,
    )
    if priority_operation is not None:
        confidence = _normalize_confidence(normalized.get("confidence"))
        return {
            **normalized,
            "intent": "open_surface",
            "operation_id": priority_operation["id"],
            "args": {},
            "surface_intent": {},
            "confidence": max(confidence, 0.82),
        }

    surface_intent = normalized.get("surface_intent")
    if normalized.get("operation_id") or (
        isinstance(surface_intent, Mapping) and isinstance(surface_intent.get("surface_id"), str)
    ):
        return normalized
    if normalized.get("intent") not in {"reply_now", "clarify", "deep_work"}:
        return normalized
    if not _looks_like_explicit_navigation(user_input):
        return normalized

    request_tokens = _significant_tokens(user_input)
    operation = _best_navigation_operation(request_tokens, planning_context)
    if operation is None:
        return normalized

    confidence = _normalize_confidence(normalized.get("confidence"))
    return {
        **normalized,
        "intent": "open_surface",
        "operation_id": operation["id"],
        "args": {},
        "surface_intent": {},
        "confidence": max(confidence, 0.78),
    }


def _operation_summary(
    operation: Any,
) -> dict[str, Any]:
    input_schema = _normalized_input_schema(getattr(operation, "input_schema", None))
    return {
        "id": operation.id,
        "label": operation.label,
        "description": operation.description,
        "invocation_kind": operation.invocation_kind,
        "can_dispatch_now": operation.can_dispatch_now,
        "target_node": operation.target_node,
        "required_args": list(operation.required_args),
        "missing_args": list(operation.missing_args),
        "execution_mode": operation.execution_mode,
        "safety_class": operation.safety_class,
        "input_schema": input_schema,
        "accepted_arg_keys": _accepted_arg_keys(input_schema),
    }


def _is_product_planning_operation(operation: Any) -> bool:
    operation_id = getattr(operation, "id", None)
    if operation_id in _INTERNAL_ROUTE_OPERATION_IDS:
        return False
    if isinstance(operation_id, str) and operation_id.startswith("route."):
        return False
    return getattr(operation, "invocation_kind", None) != "hidden"


def _surface_summary(surface: RouteDeckSurface) -> dict[str, Any]:
    summary = {
        "surface_id": surface.surface_id,
        "label": surface.label,
        "component": surface.component,
        "variant": surface.variant,
        "role": surface.role,
        "surface_kind": surface.surface_kind,
    }
    description = _string_or_none(surface.props.get("planning_description"))
    if description:
        summary["description"] = description
    selectable_entities = _normalized_planning_entities(surface.props.get("planning_entities"))
    if selectable_entities:
        summary["selectable_entities"] = selectable_entities
        entity_count = surface.props.get("planning_entity_count")
        if isinstance(entity_count, int) and entity_count >= 0:
            summary["selectable_entity_count"] = entity_count
        if surface.props.get("planning_entities_truncated") is True:
            summary["selectable_entities_truncated"] = True
    return summary


def _current_active_surface(
    *,
    active_surfaces: list[dict[str, Any]],
    projection: RouteDeckProjection,
    state: CorpusGraphState,
) -> dict[str, Any] | None:
    surface_id = state.active_surface_id or projection.navigation.current.surface_id
    if surface_id:
        for surface in active_surfaces:
            if surface["surface_id"] == surface_id:
                return surface
    default_surface = next(
        (
            _surface_summary(surface)
            for surface in projection.surfaces.values()
            if surface.role == "active" and surface.default and surface.surface_id
        ),
        None,
    )
    return default_surface or (active_surfaces[0] if active_surfaces else None)


def _active_saas_agent_summary(
    *,
    projection: RouteDeckProjection,
    state: CorpusGraphState,
) -> dict[str, str] | None:
    if state.active_saas_agent_id is None:
        return None
    lens_props = _lens_props(projection)
    return {
        "id": str(state.active_saas_agent_id),
        "name": _string_or_none(lens_props.get("selected_saas_agent_name")),
        "slug": _string_or_none(lens_props.get("selected_saas_agent_slug")),
    }


def _lens_props(projection: RouteDeckProjection) -> Mapping[str, Any]:
    if projection.context_lens is None:
        return {}
    return projection.context_lens.model_dump(mode="json")


def _coerce_mapping(raw_plan: Any) -> Mapping[str, Any]:
    if isinstance(raw_plan, Mapping):
        return raw_plan
    if isinstance(raw_plan, str):
        try:
            parsed = json.loads(raw_plan)
        except json.JSONDecodeError:
            return {}
        return parsed if isinstance(parsed, Mapping) else {}
    return {}


def _normalize_confidence(value: Any) -> float:
    if isinstance(value, bool):
        return 0.0
    if isinstance(value, (int, float)):
        return max(0.0, min(float(value), 1.0))
    return 0.0


def _string_or_none(value: Any) -> str | None:
    return value if isinstance(value, str) else None


def _visible_entities(active_surface: Mapping[str, Any] | None) -> list[dict[str, Any]]:
    if not isinstance(active_surface, Mapping):
        return []
    raw_entities = active_surface.get("selectable_entities")
    return [dict(entity) for entity in raw_entities] if isinstance(raw_entities, list) else []


def _normalized_planning_entities(raw_entities: Any) -> list[dict[str, Any]]:
    if not isinstance(raw_entities, list):
        return []
    entities: list[dict[str, Any]] = []
    for raw_entity in raw_entities:
        if not isinstance(raw_entity, Mapping):
            continue
        operation_id = raw_entity.get("operation_id")
        args = raw_entity.get("args")
        label = raw_entity.get("label")
        if not isinstance(operation_id, str) or not isinstance(args, Mapping) or not isinstance(label, str):
            continue
        entity = {
            "operation_id": operation_id,
            "label": label,
            "args": dict(args),
        }
        entity_type = _string_or_none(raw_entity.get("entity_type"))
        if entity_type:
            entity["entity_type"] = entity_type
        entity_id = _string_or_none(raw_entity.get("id"))
        if entity_id:
            entity["id"] = entity_id
        slug = _string_or_none(raw_entity.get("slug"))
        if slug:
            entity["slug"] = slug
        description = _string_or_none(raw_entity.get("description"))
        if description:
            entity["description"] = description
        entities.append(entity)
    return entities


def _surface_options(active_surfaces: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [
        {
            "surface_id": surface["surface_id"],
            "label": surface["label"],
            "component": surface["component"],
            "surface_kind": surface["surface_kind"],
            **({"description": surface["description"]} if isinstance(surface.get("description"), str) else {}),
        }
        for surface in active_surfaces
        if isinstance(surface.get("surface_id"), str)
    ]


def _normalized_input_schema(raw_schema: Any) -> dict[str, Any]:
    if not isinstance(raw_schema, Mapping):
        return {"fields": []}
    schema = {key: value for key, value in raw_schema.items()}
    raw_fields = raw_schema.get("fields")
    if not isinstance(raw_fields, list):
        schema["fields"] = []
        return schema
    schema["fields"] = [dict(field) for field in raw_fields if isinstance(field, Mapping)]
    return schema


def _accepted_arg_keys(input_schema: Mapping[str, Any]) -> list[str]:
    accepted_keys: list[str] = []
    fields = input_schema.get("fields")
    if not isinstance(fields, list):
        return accepted_keys
    for field in fields:
        if not isinstance(field, Mapping):
            continue
        key = field.get("key")
        if isinstance(key, str):
            accepted_keys.append(key)
    return accepted_keys


def _normalize_operation_args(
    *,
    operation: Mapping[str, Any] | None,
    raw_args: Any,
) -> tuple[bool, dict[str, Any]]:
    args = raw_args if isinstance(raw_args, dict) else {}
    if operation is None:
        return True, {}
    accepted_keys = operation.get("accepted_arg_keys")
    if not isinstance(accepted_keys, list):
        return True, {}
    return True, {
        key: args[key]
        for key in accepted_keys
        if isinstance(key, str) and key in args
    }


def _normalize_surface_intent(
    raw_surface_intent: Any,
    *,
    planning_context: Mapping[str, Any],
) -> tuple[bool, dict[str, str]]:
    if not isinstance(raw_surface_intent, Mapping):
        return True, {}
    normalized = {
        key: value
        for key, value in raw_surface_intent.items()
        if isinstance(key, str) and isinstance(value, str) and key != "surface_id"
    }
    if "surface_id" not in raw_surface_intent:
        return True, normalized
    surface_id = raw_surface_intent.get("surface_id")
    surface_option_ids = {
        option.get("surface_id")
        for option in planning_context.get("surface_options", [])
        if isinstance(option, Mapping)
    }
    if not isinstance(surface_id, str) or surface_id not in surface_option_ids:
        return False, {}
    normalized["surface_id"] = surface_id
    return True, normalized


def _looks_like_explicit_navigation(text: str) -> bool:
    return bool(_tokens(text) & _NAVIGATION_WORDS)


def _tokens(text: str) -> set[str]:
    return set(_TOKEN_RE.findall(text.lower()))


def _significant_tokens(text: str) -> set[str]:
    return {
        token
        for token in _tokens(text)
        if token not in _NAVIGATION_WORDS and token not in _STOP_WORDS and len(token) > 1
    }


def _best_navigation_operation(
    request_tokens: set[str],
    planning_context: Mapping[str, Any],
) -> Mapping[str, Any] | None:
    if not request_tokens:
        return None
    scored: list[tuple[int, Mapping[str, Any]]] = []
    for operation in planning_context.get("legal_operations", []):
        if not isinstance(operation, Mapping) or not _is_openable_operation(operation):
            continue
        operation_tokens = _operation_match_tokens(operation)
        overlap = request_tokens & operation_tokens
        if not overlap:
            continue
        label = str(operation.get("label") or "").strip().lower()
        score = len(overlap)
        if label and label in " ".join(sorted(request_tokens)):
            score += 3
        scored.append((score, operation))
    if not scored:
        return None
    scored.sort(key=lambda item: item[0], reverse=True)
    if len(scored) > 1 and scored[0][0] == scored[1][0]:
        return None
    return scored[0][1]


def _priority_navigation_operation(
    *,
    user_input: str,
    planning_context: Mapping[str, Any],
) -> Mapping[str, Any] | None:
    if not _looks_like_explicit_navigation(user_input):
        return None
    request_tokens = _tokens(user_input)
    if request_tokens.isdisjoint(_POLICY_REVIEW_TOKENS):
        return None
    return _legal_openable_operation_by_id(planning_context, CorpusActionIds.LEARNING_OPEN)


def _legal_openable_operation_by_id(
    planning_context: Mapping[str, Any],
    operation_id: str,
) -> Mapping[str, Any] | None:
    for operation in planning_context.get("legal_operations", []):
        if isinstance(operation, Mapping) and operation.get("id") == operation_id and _is_openable_operation(operation):
            return operation
    return None


def _is_openable_operation(operation: Mapping[str, Any]) -> bool:
    if operation.get("execution_mode") != "auto":
        return False
    if operation.get("can_dispatch_now") is not True:
        return False
    if operation.get("required_args") or operation.get("missing_args"):
        return False
    if operation.get("kind") == "form":
        return False
    return operation.get("invocation_kind") in {"direct", "surface"}


def _operation_match_tokens(operation: Mapping[str, Any]) -> set[str]:
    parts = [
        operation.get("id"),
        operation.get("label"),
        operation.get("description"),
        operation.get("target_node"),
    ]
    return _significant_tokens(" ".join(part for part in parts if isinstance(part, str)))


def _clarify_safe_result() -> dict[str, Any]:
    return {
        "intent": "clarify",
        "message": _CLARIFY_SAFE_MESSAGE,
        "operation_id": None,
        "args": {},
        "surface_intent": {},
        "confidence": 0.0,
        "preamble": None,
    }


class CorpusOperationPolicy(RouteDeckOperationPolicy):
    """Maps Corpus app actions into generic RouteDeck operations."""

    def __init__(self) -> None:
        super().__init__(
            target_nodes_by_action=ACTION_TARGETS,
            review_action_ids=[
                "execution.plan",
                "execution.provide_input",
                "approval.approve",
                "approval.reject",
                "knowledge.generate",
                "memory.save",
                "learning.approve",
                "learning.reject",
                "qa.run",
            ],
            safety_class_by_category={
                "execution": "write_external",
                "deployment": "draft",
                "feedback": "draft",
                "learning": "draft",
                "auth": "credential",
            },
        )


class CorpusOperationRequests(RouteDeckOperationRequestPolicy):
    """Corpus route action IDs wired into RouteDeck operation requests."""

    def __init__(
        self,
        *,
        navigation: CorpusRouteDeckNavigation,
        surface_registry: CorpusSurfaceRegistry,
        route_actions: RouteDeckRouteActionIds,
    ) -> None:
        super().__init__(
            navigation=navigation,
            surface_registry=surface_registry,
            route_actions=route_actions,
        )

    def validated_payload(
        self,
        *,
        state: CorpusGraphState,
        operation: RouteDeckOperation,
        args: dict[str, Any] | None,
        projection: RouteDeckProjection,
    ) -> dict[str, Any]:
        try:
            return super().validated_payload(
                state=state,
                operation=operation,
                args=args,
                projection=projection,
            )
        except ValueError as exc:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc

    def review_state_for_operation(
        self,
        *,
        state: CorpusGraphState,
        operation: RouteDeckOperation,
        args: dict[str, Any],
    ) -> CorpusGraphState:
        return super().review_state_for_operation(state=state, operation=operation, args=args)


NAV_PARAM_SAAS_AGENT_ID = "saas_agent_id"


class CorpusRouteDeckNavigation(RouteDeckGraphNavigationController):
    """Corpus-specific history params on top of RouteDeck navigation."""

    def __init__(
        self,
        *,
        surface_registry: CorpusSurfaceRegistry,
        node_by_id: Mapping[str, Any],
        policy: RouteDeckNavigationPolicy | None = None,
    ) -> None:
        super().__init__(
            surface_registry=surface_registry,
            node_by_id=node_by_id,
            policy=policy,
            location_factory=CorpusGraphNavigationLocation,
        )

    def extra_history_params(self, state: CorpusGraphState) -> Mapping[str, Any]:
        if not state.active_saas_agent_id:
            return {}
        return {NAV_PARAM_SAAS_AGENT_ID: str(state.active_saas_agent_id)}

    def apply_extra_history_params(self, state: CorpusGraphState, params: dict[str, Any]) -> None:
        raw_saas_agent_id = params.pop(NAV_PARAM_SAAS_AGENT_ID, None)
        if not raw_saas_agent_id:
            return
        try:
            state.active_saas_agent_id = uuid.UUID(str(raw_saas_agent_id))
        except (TypeError, ValueError):
            return

    def cancel_target_location(self, state: CorpusGraphState) -> CorpusGraphNavigationLocation | None:
        node = self._node_by_id.get(state.node)
        cancel_target_node = getattr(node, "cancel_target_node", None) if node else None
        if cancel_target_node:
            params: dict[str, Any] = {}
            if state.active_saas_agent_id:
                params[NAV_PARAM_SAAS_AGENT_ID] = str(state.active_saas_agent_id)
            return self.make_location(
                node_id=cancel_target_node,
                surface_id=self._surface_registry.default_surface_id_for(cancel_target_node),
                params=params,
            )
        return state.navigation_back_stack[-1] if state.navigation_back_stack else None


class CorpusSurfaceRegistry(RouteDeckSurfaceRegistry):
    """Adapts Corpus surface descriptors to RouteDeck surface mechanics."""

    Surface = CorpusSurface

    def __init__(self, catalog: CorpusSurfaceCatalog | None = None) -> None:
        self._catalog = catalog or CorpusSurfaceCatalog()
        super().__init__(
            active_components_by_node=self._catalog.active_components_by_node,
            default_surface_ids_by_node=self._catalog.default_surface_ids_by_node,
            surface_hosted_operations_by_node=self._catalog.surface_hosted_operations_by_node,
            operation_review_surface_prefix=self._catalog.operation_review_surface_prefix,
        )

    def frame_surface(
        self,
        *,
        state: CorpusGraphState,
        lens: CorpusContextLens,
        saas_agents: list[SaaSAgentRead],
        context: str,
        presentation_state: dict[str, Any],
        node_by_id: dict[str, Any],
    ) -> CorpusSurface:
        spec = self._catalog.frame_spec(state=state, lens=lens, saas_agents=saas_agents, context=context)
        return self.build_surface_from_spec(
            spec=spec,
            variant=self.surface_variant_for_node(
                node_id=state.node,
                presentation_state=presentation_state,
                surface_name="main",
                default=spec.variant,
                node_by_id=node_by_id,
            ),
            label=spec.label or lens.working_on,
            props=spec.resolve_props(state=state, lens=lens, saas_agents=saas_agents),
        )

    def active_surfaces(
        self,
        *,
        state: CorpusGraphState,
        lens: CorpusContextLens,
        saas_agents: list[SaaSAgentRead],
        context: str,
    ) -> list[CorpusSurface]:
        return self.surfaces_from_specs(
            self._catalog.active_specs(state=state, lens=lens, saas_agents=saas_agents, context=context),
            state=state,
            lens=lens,
            saas_agents=saas_agents,
        )

    def review_surface_props(
        self,
        *,
        state: CorpusGraphState,
        lens: CorpusContextLens,
        saas_agents: list[SaaSAgentRead],
    ) -> dict[str, Any]:
        return self._catalog.review_props(
            lens=lens,
            saas_agents=saas_agents,
            graph_context=state.graph_context,
        )

    def surface_props_for_spec(
        self,
        spec: CorpusSurfaceSpec,
        **context: Any,
    ) -> dict[str, Any]:
        state = context.get("state")
        lens = context.get("lens")
        saas_agents = context.get("saas_agents") or []
        if not isinstance(state, CorpusGraphState) or not isinstance(lens, CorpusContextLens):
            return dict(super().surface_props_for_spec(spec, **context))
        return {
            "title": lens.working_on,
            "node_id": state.node,
            "saas_agents": [agent.model_dump(mode="json") for agent in saas_agents],
            "lens": lens.model_dump(mode="json"),
            **spec.resolve_props(state=state, lens=lens, saas_agents=saas_agents),
            **state.graph_context,
            "router_index": state.graph_context.get("router_index") or self._catalog.router_index_from_lens(lens),
        }

    def surface_label_for_spec(
        self,
        spec: CorpusSurfaceSpec,
        **context: Any,
    ) -> str | None:
        lens = context.get("lens")
        return spec.label or (lens.working_on if isinstance(lens, CorpusContextLens) else None)


def build_graph_introspection(
    manifest: RouteDeckManifest,
    *,
    state: CorpusGraphState,
    lens: CorpusContextLens,
    projection: RouteDeckProjection,
    valid_actions: list[dict[str, Any]],
    blocked_actions: list[dict[str, str]],
    guard_explanations: list[dict[str, Any]],
    diagnostics: dict[str, Any] | None = None,
) -> dict[str, Any]:
    runtime_snapshot = build_runtime_snapshot(
        manifest,
        current_node=state.node,
        valid_actions=valid_actions,
        blocked_actions=blocked_actions,
        executed_nodes=state.executed_nodes,
        diagnostics=diagnostics or {},
    )
    return {
        "current_node": state.node,
        "reachable_nodes": runtime_snapshot["reachable_nodes"],
        "legal_operations": [operation.model_dump(mode="json") for operation in projection.legal_operations],
        "blocked_operations": blocked_actions,
        "guard_explanations": guard_explanations,
        "surface_projection": {
            name: surface.model_dump(mode="json") for name, surface in projection.surfaces.items()
        },
        "route_trace": {
            "executed_nodes": list(state.executed_nodes),
            "replace_path": diagnostics.get("replace_path") if diagnostics else None,
        },
        "runtime_snapshot": runtime_snapshot,
        "context_lens": lens.model_dump(mode="json"),
    }


class CorpusNavgraphDiagnostics:
    """Builds read-only RouteDeck navgraph diagnostics for the Corpus app."""

    def introspection(
        self,
        *,
        manifest: RouteDeckManifest,
        state: CorpusGraphState,
        lens: CorpusContextLens,
        projection: RouteDeckProjection,
        valid_actions: list[dict[str, Any]],
        blocked_actions: list[dict[str, Any]],
        guard_explanations: list[dict[str, Any]],
        diagnostics: dict[str, Any],
    ) -> dict[str, Any]:
        return build_graph_introspection(
            manifest,
            state=state,
            lens=lens,
            projection=projection,
            valid_actions=valid_actions,
            blocked_actions=blocked_actions,
            guard_explanations=guard_explanations,
            diagnostics={**diagnostics, "navgraph": True},
        )


CORPUS_TURN_ROUTER_PROMPT = """You are Corpus, the central SaaStoAgent platform graph agent.
You own platform navigation, setup, recovery, and surface selection for SaaStoAgent.
RouteDeck exposes the current graph-aware context. You decide what to do from that current legal context.
Use only the provided planning_context. Never infer hidden routes, hidden permissions, or hidden surfaces.
Return only JSON:
{
  "intent": "reply_now" | "open_surface" | "clarify" | "deep_work" | "propose_operation",
  "message": string,
  "operation_id": string|null,
  "args": object,
  "surface_intent": object,
  "confidence": number,
  "preamble": string|null
}.

Rules:
- The agent decides; planning_context only exposes current legal possibilities.
- Use only operation ids present in planning_context.legal_operations.
- Never invent or patch graph state directly.
- Prefer a legal typed operation when one clearly satisfies the request.
- When planning_context.visible_entities exposes an operation_id plus args for a currently visible item, prefer that exact typed operation payload instead of asking for a hidden internal id.
- If you include operation_id, the turn is an action request; use "propose_operation" or "open_surface", not "reply_now".
- Use "open_surface" with surface_intent.surface_id when switching to one of planning_context.surface_options.
- Do not return internal route.* operation ids. RouteDeck route operations are runtime/browser plumbing, not Corpus planning vocabulary.
- Use "propose_operation" for legal operations that require review before execution.
- Use "reply_now" only for informational answers that do not change the current workspace.
- If your response would claim that you are opening, switching, preparing, or staging workspace state, return a legal typed operation or surface_intent instead.
- Use "clarify" when the request is ambiguous or no legal operation can satisfy it.
- Use "deep_work" only when a slower synthesized answer is genuinely needed.
- If multiple legal operations could fit, prefer "clarify" over guessing.
- For "open_surface" and "propose_operation", do not ask for extra confirmation in "message". The operation will already be opening or staged.
- For surface-opening turns, make "message" the prompt to show after the active surface is visible."""

CORPUS_STREAM_PROMPT = """You are Corpus, the central SaaStoAgent platform agent.
Respond conversationally and concisely to the user based on the provided
planning_context. Do not claim to run created SaaS Agents. If a platform action
is needed, describe the next step naturally; the Corpus graph will decide the
typed operation separately. Do not ask the user for extra confirmation to open
or switch a work surface. Do not claim that a workspace surface is being opened
unless the router has already selected a typed operation or surface intent."""

CORPUS_OPERATION_STREAM_PROMPT = """You are Corpus, the central SaaStoAgent platform agent.
Write the assistant-facing reply after a typed Corpus operation has already committed or staged.
The operation_context is the source of truth. Preserve exact names, ids, statuses, and surface labels.
Do not invent hidden state, pending approvals, deployments, or external API results.
Use operation_context.effect_summary as the primary factual summary of what happened.
Do not say you will open, save, stage, or switch something if operation_context says it already happened.
Opening or activating a Register or Sign in surface never means the account was created or the user signed in. It only means the form is ready.
Do not mention internal component names, route ids, node ids, operation ids, surface ids, or JSON fields unless the user explicitly asks for technical diagnostics.
Be brief and conversational, and tell the user what is now available when a surface is active."""


class CorpusRouteDeckRuntime(RouteDeckRuntimeBase[CorpusGraphState, RouteDeckGraphMessage]):
    """RouteDeck runtime implementation for the Corpus/SaaStoAgent app."""

    def __init__(self) -> None:
        super().__init__()
        self._action_dispatcher = build_corpus_action_dispatcher(
            navigation=self._navigation,
            action_targets=ACTION_TARGETS,
        )
        self._context_queries = CorpusContextQueries(node_by_id=self._node_by_id)
        self._route_deck_projector = self.build_state_projector()
        self._navgraph_diagnostics = CorpusNavgraphDiagnostics()

    def request_from_location(
        self,
        *,
        node_id: str | None = None,
        saas_agent_id: uuid.UUID | None = None,
        surface_id: str | None = None,
        user_input: str | None = None,
    ) -> CorpusGraphRequest:
        if node_id is None and saas_agent_id is None and surface_id is None and user_input is None:
            return CorpusGraphRequest()
        state = CorpusGraphState(
            node=node_id or CorpusNodeIds.HOME,
            active_saas_agent_id=saas_agent_id,
            active_surface_id=surface_id,
        )
        return CorpusGraphRequest(
            state=state,
            node_id=node_id or state.node,
            saas_agent_id=saas_agent_id,
            user_input=user_input,
        )

    async def stream_corpus_turn(
        self,
        *,
        request: CorpusGraphRequest,
        user: User | None,
        db: AsyncSession,
        projection_version: int = 1,
        openai_api_key: str | None = None,
    ) -> AsyncIterator[dict[str, Any]]:
        context = {
            "request": request,
            "user": user,
            "db": db,
            "projection_version": projection_version,
        }
        runtime_state = await self.snapshot(context)
        turn_state = CorpusGraphState.model_validate(runtime_state.graph_state or {})
        projection = runtime_state.projection
        api_key = settings.openai_api_key if openai_api_key is None else openai_api_key
        if not api_key:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Corpus graph requires a configured LLM. Set STA_OPENAI_API_KEY before using Corpus.",
            )

        planning_context = build_corpus_turn_planning_context(
            state=turn_state,
            projection=projection,
        )
        yield {"event_type": "corpus_status", "projection_version": projection.projection_version, "payload": {"status": "thinking"}}
        decision_task = asyncio.create_task(
            self._corpus_turn_plan(
                api_key=api_key,
                user_input=request.user_input or "",
                planning_context=planning_context,
            )
        )
        try:
            decision = await decision_task
        except Exception as exc:
            yield {
                "event_type": "corpus_error",
                "projection_version": projection.projection_version,
                "payload": {"message": "Corpus could not complete the model turn.", "error": exc.__class__.__name__},
            }
            return

        decision = normalize_corpus_turn_plan(decision, planning_context=planning_context)
        decision = resolve_explicit_navigation_turn(
            decision,
            user_input=request.user_input or "",
            planning_context=planning_context,
        )
        surface_intent = decision.get("surface_intent")
        surface_navigation_id = self.surface_navigation_id_from_intent(surface_intent)
        surface_variant_intent = self.surface_variant_intent_from_intent(surface_intent)
        if self.store_surface_intent_for_state(turn_state, surface_variant_intent, context):
            context["request"] = CorpusGraphRequest(
                state=turn_state,
                node_id=turn_state.node,
                saas_agent_id=turn_state.active_saas_agent_id,
                user_input=request.user_input,
            )
            context["projection_version"] = projection.projection_version + 1
            runtime_state = await self.snapshot(context)
            turn_state = CorpusGraphState.model_validate(runtime_state.graph_state or {})
            projection = runtime_state.projection
            yield {
                "event_type": "projection_update",
                "projection_version": projection.projection_version,
                "payload": {"projection": projection.model_dump(mode="json")},
            }

        if surface_navigation_id:
            dispatch_result, response = await self._dispatch_corpus_operation(
                operation_id=CorpusActionIds.ROUTE_SWITCH_SURFACE,
                args={"surface_id": surface_navigation_id},
                state=turn_state,
                context=context,
                projection_version=projection.projection_version,
            )
            yield dispatch_result.events[0].model_dump(mode="json")
            async for event in self._stream_operation_reply_events(
                api_key=api_key,
                user_input=request.user_input or "",
                decision_message=str(decision.get("message") or ""),
                response=response,
                operation_id=CorpusActionIds.ROUTE_SWITCH_SURFACE,
                projection_version=response.projection.projection_version,
            ):
                yield event
            yield {"event_type": "corpus_done", "projection_version": response.projection.projection_version, "payload": {"status": "committed"}}
            return

        intent = self._turn_plan_intent(decision)
        message = str(decision.get("message") or "").strip()
        operation_id = decision.get("operation_id")
        operation = next((candidate for candidate in projection.legal_operations if candidate.id == operation_id), None)
        if operation is None:
            if operation_id:
                message = message or "That action is not available from here."
                async for event in self._message_delta_events(projection_version=projection.projection_version, text=message):
                    yield event
                yield {"event_type": "corpus_done", "projection_version": projection.projection_version, "payload": {"status": "clarify"}}
                return
            if intent == "deep_work":
                streamed_text = ""
                preamble = str(decision.get("preamble") or message or "").strip()
                if preamble:
                    async for event in self._message_delta_events(projection_version=projection.projection_version, text=preamble):
                        yield event
                try:
                    async for delta in self._stream_corpus_message(
                        api_key=api_key,
                        user_input=request.user_input or "",
                        planning_context=self._reply_planning_context(planning_context),
                    ):
                        if not delta:
                            continue
                        streamed_text += delta
                        yield {"event_type": "message_delta", "projection_version": projection.projection_version, "payload": {"delta": delta}}
                except Exception as exc:
                    yield {
                        "event_type": "corpus_error",
                        "projection_version": projection.projection_version,
                        "payload": {"message": "Corpus could not complete the model turn.", "error": exc.__class__.__name__},
                    }
                    return
                if message and not streamed_text and not preamble:
                    async for event in self._message_delta_events(projection_version=projection.projection_version, text=message):
                        yield event
                yield {"event_type": "corpus_done", "projection_version": projection.projection_version, "payload": {"status": "deep_work"}}
                return
            message = message or "I can help from here. Choose one of the visible next steps."
            async for event in self._stream_reply_events(
                api_key=api_key,
                user_input=request.user_input or "",
                planning_context=planning_context,
                projection_version=projection.projection_version,
                fallback_message=message,
            ):
                yield event
            done_status = intent if intent in {"reply_now", "clarify"} else "clarify"
            yield {"event_type": "corpus_done", "projection_version": projection.projection_version, "payload": {"status": done_status}}
            return

        dispatch_result, response = await self._dispatch_corpus_operation(
            operation_id=operation.id,
            args=decision.get("args") or {},
            state=turn_state,
            context=context,
            projection_version=projection.projection_version,
        )
        yield dispatch_result.events[0].model_dump(mode="json")
        done_status = "review" if response.state.pending_operation_id == operation.id else "committed"
        async for event in self._stream_operation_reply_events(
            api_key=api_key,
            user_input=request.user_input or "",
            decision_message=message,
            response=response,
            operation_id=operation.id,
            projection_version=response.projection.projection_version,
        ):
            yield event
        yield {"event_type": "corpus_done", "projection_version": response.projection.projection_version, "payload": {"status": done_status}}

    async def prepare_state(self, context: dict[str, Any]) -> CorpusGraphState:
        return await self._prepared_state_from_context(context)

    async def prepare_dispatch_state(
        self,
        request: RouteDeckDispatchInput,
        context: dict[str, Any],
    ) -> CorpusGraphState:
        graph_request = self._request_from_dispatch(request, context)
        user = self._user_from_context(context)
        db = self._db_from_context(context)
        state = await self._initial_state(graph_request, user, db)
        state.node = await self._eligible_node_or_recovery(graph_request.node_id or state.node, state, user, db)
        return state

    async def project_state(
        self,
        state: CorpusGraphState,
        *,
        context: dict[str, Any],
        projection_version: int = 1,
    ) -> RouteDeckProjection:
        return await self._projection_for_state(
            state=state,
            context=context,
            projection_version=projection_version,
        )

    def base_location_for_state(self, state: CorpusGraphState, context: dict[str, Any]) -> str | None:
        if state.active_saas_agent_id:
            return (
                f"/app/agents/{state.active_saas_agent_id}"
                if state.node == CorpusNodeIds.AGENT_HOME
                else f"/app/agents/{state.active_saas_agent_id}/{state.node}"
            )
        return "/app/home" if state.node == CorpusNodeIds.HOME else f"/app/{state.node}"

    def dispatch_metadata_for_state(self, state: CorpusGraphState, context: dict[str, Any]) -> dict[str, Any]:
        return {"replace_path": self.location_for_state(state, context)}

    def should_stage_operation_review(
        self,
        *,
        state: CorpusGraphState,
        operation: RouteDeckOperation,
        context: dict[str, Any],
    ) -> bool:
        return (
            super().should_stage_operation_review(state=state, operation=operation, context=context)
            and not self._surface_registry.is_surface_hosted_operation(node_id=state.node, operation_id=operation.id)
        )

    async def execute_action_with_context(
        self,
        operation_id: str,
        state: CorpusGraphState,
        payload: dict[str, Any],
        context: dict[str, Any],
    ) -> RouteDeckActionResult[CorpusGraphState, RouteDeckGraphMessage]:
        return await self._action_dispatcher.dispatch(
            operation_id,
            state=state,
            payload=payload,
            context=CorpusActionContext(
                user=self._user_from_context(context),
                db=self._db_from_context(context),
                queries=self._context_queries,
            ),
        )

    async def _dispatch_corpus_operation(
        self,
        *,
        operation_id: str,
        args: dict[str, Any],
        state: CorpusGraphState,
        context: dict[str, Any],
        projection_version: int,
    ) -> tuple[RouteDeckDispatchResult, CorpusActionResponse]:
        dispatch_context = {
            **context,
            "request": CorpusGraphRequest(
                state=state,
                node_id=state.node,
                saas_agent_id=state.active_saas_agent_id,
            ),
            "node_id": state.node,
            "saas_agent_id": state.active_saas_agent_id,
            "projection_version": projection_version,
        }
        result = await self.dispatch(
            RouteDeckDispatchInput(
                operation_id=operation_id,
                args=args,
                graph_state=state.model_dump(mode="json"),
                projection_version=projection_version,
            ),
            dispatch_context,
        )
        return result, self._corpus_action_response_from_dispatch_result(result)

    def _corpus_action_response_from_dispatch_result(self, result: RouteDeckDispatchResult) -> CorpusActionResponse:
        return CorpusActionResponse(
            state=CorpusGraphState.model_validate(result.state.graph_state or {}),
            projection=result.state.projection,
            active_surface=result.active_surface,
            messages=[RouteDeckGraphMessage.model_validate(message) for message in result.messages],
            replace_path=result.state.location or result.metadata.get("replace_path"),
        )

    async def inspect(
        self,
        query: dict[str, Any] | None = None,
        context: dict[str, Any] | None = None,
    ) -> RouteDeckIntrospection:
        ctx = {**(context or {}), **(query or {})}
        projection = (await self.snapshot(ctx)).projection
        raw = projection.diagnostics.get("introspection") if isinstance(projection.diagnostics, dict) else {}
        return RouteDeckIntrospection(
            current_node=raw.get("current_node"),
            reachable_nodes=list(raw.get("reachable_nodes") or []),
            legal_operations=list(raw.get("legal_operations") or []),
            blocked_operations=list(raw.get("blocked_operations") or []),
            guard_explanations=[
                explanation if isinstance(explanation, str) else str(explanation.get("reason") or explanation)
                for explanation in raw.get("guard_explanations") or []
            ],
            surfaces=dict(raw.get("surface_projection") or {}),
            route_traces=[raw.get("route_trace") or {}],
            diagnostics={
                "runtime_snapshot": raw.get("runtime_snapshot") or {},
                "context_lens": raw.get("context_lens") or {},
            },
        )

    def _request_from_context(self, context: dict[str, Any]) -> CorpusGraphRequest:
        request = context.get("request")
        if isinstance(request, CorpusGraphRequest):
            return request
        return CorpusGraphRequest(
            node_id=context.get("node_id"),
            saas_agent_id=context.get("saas_agent_id"),
            user_input=context.get("user_input"),
        )

    def _request_from_dispatch(self, request: RouteDeckDispatchInput, context: dict[str, Any]) -> CorpusGraphRequest:
        state = self._state_from_graph_state(request.graph_state)
        return CorpusGraphRequest(
            state=state,
            node_id=context.get("node_id") or state.node,
            saas_agent_id=context.get("saas_agent_id") or state.active_saas_agent_id,
        )

    def _state_from_graph_state(self, graph_state: dict[str, Any]) -> CorpusGraphState:
        if graph_state:
            return CorpusGraphState.model_validate(graph_state)
        return CorpusGraphState()

    def _user_from_context(self, context: dict[str, Any]) -> User | None:
        user = context.get("user")
        return user if isinstance(user, User) else None

    def _db_from_context(self, context: dict[str, Any]) -> AsyncSession:
        return context.get("db")

    async def _prepared_state_from_context(self, context: dict[str, Any]) -> CorpusGraphState:
        request = self._request_from_context(context)
        user = self._user_from_context(context)
        db = self._db_from_context(context)
        state = await self._initial_state(request, user, db)
        state.node = await self._eligible_node_or_recovery(request.node_id or state.node, state, user, db)
        return state

    async def _projection_for_state(
        self,
        *,
        state: CorpusGraphState,
        context: dict[str, Any],
        projection_version: int,
    ) -> RouteDeckProjection:
        user = self._user_from_context(context)
        db = self._db_from_context(context)
        actions = await self._valid_actions(state, user, db)
        lens = await self._context_lens(state, user, db)
        saas_agents = await self._list_saas_agents(user, db)
        projection_context = self._projection_context(state, user)
        presentation_state = self.stored_presentation_state_for_state(state, context)
        projection = self._route_deck_projector.project_state(
            state,
            current_context=projection_context,
            actions=actions,
            surfaces=self._surfaces_for_projection(
                state=state,
                lens=lens,
                saas_agents=saas_agents,
                projection_context=projection_context,
                presentation_state=presentation_state,
            ),
            context_lens=lens,
            presentation_state={"context": projection_context, **presentation_state},
            projection_version=projection_version,
            diagnostics=self._projection_diagnostics(state),
            review_surface_props=self._surface_registry.review_surface_props(
                state=state,
                lens=lens,
                saas_agents=saas_agents,
            ),
        )
        blocked_actions = self._blocked_actions(state, user, lens)
        guard_explanations = self._guard_explanations(state, user, lens)
        introspection = self._navgraph_diagnostics.introspection(
            manifest=self.manifest,
            state=state,
            lens=lens,
            projection=projection,
            valid_actions=[action.model_dump(mode="json") for action in actions],
            blocked_actions=blocked_actions,
            guard_explanations=guard_explanations,
            diagnostics={**self._base_diagnostics(state), "replace_path": self.location_for_state(state, context)},
        )
        return projection.model_copy(update={"diagnostics": {**projection.diagnostics, "introspection": introspection}})

    def _surfaces_for_projection(
        self,
        *,
        state: CorpusGraphState,
        lens: CorpusContextLens,
        saas_agents: list[Any],
        projection_context: str,
        presentation_state: dict[str, Any],
    ) -> list[Any]:
        frame_surface = self._surface_registry.frame_surface(
            state=state,
            lens=lens,
            saas_agents=saas_agents,
            context=projection_context,
            presentation_state=presentation_state,
            node_by_id=self._node_by_id,
        )
        return [
            frame_surface,
            *self._surface_registry.active_surfaces(
                state=state,
                lens=lens,
                saas_agents=saas_agents,
                context=projection_context,
            ),
        ]

    def _projection_diagnostics(self, state: CorpusGraphState) -> dict[str, Any]:
        default_surface_by_node = self._route_deck_projector.default_surface_by_node_for_state(state)
        return {
            **self._base_diagnostics(state),
            "capability_rail": CAPABILITY_RAIL_ITEMS,
            "node_hierarchy": self._route_deck_projector.node_hierarchy(default_surface_by_node=default_surface_by_node),
        }

    def _base_diagnostics(self, state: CorpusGraphState) -> dict[str, Any]:
        return {
            "source": "corpus_graph",
            "graph_version": self.manifest.version,
            "selected_saas_agent_id": str(state.active_saas_agent_id) if state.active_saas_agent_id else None,
        }

    async def _initial_state(self, request: CorpusGraphRequest, user: User | None, db: AsyncSession) -> CorpusGraphState:
        state = request.state or CorpusGraphState()
        if request.saas_agent_id:
            state.active_saas_agent_id = request.saas_agent_id
        if state.active_saas_agent_id and user:
            await self._require_member(state.active_saas_agent_id, user, db)
        if not user and state.node not in {CorpusNodeIds.HOME, CorpusNodeIds.AUTH_SIGN_IN, CorpusNodeIds.AUTH_REGISTER}:
            state.node = CorpusNodeIds.HOME
            state.active_saas_agent_id = None
        if state.node not in self._node_by_id:
            state.node = CorpusNodeIds.RECOVERY
        if not state.executed_nodes:
            state.executed_nodes = [state.node]
        return state

    async def _eligible_node_or_recovery(
        self,
        node_id: str,
        state: CorpusGraphState,
        user: User | None,
        db: AsyncSession,
    ) -> str:
        if node_id not in self._node_by_id:
            return CorpusNodeIds.RECOVERY
        if node_id in {CorpusNodeIds.HOME, CorpusNodeIds.AUTH_SIGN_IN, CorpusNodeIds.AUTH_REGISTER, CorpusNodeIds.RECOVERY}:
            return node_id
        if user is None:
            return CorpusNodeIds.HOME
        if node_id in {CorpusNodeIds.SAAS_AGENT_SELECT, CorpusNodeIds.SAAS_AGENT_CREATE}:
            return node_id
        if not state.active_saas_agent_id:
            return CorpusNodeIds.SAAS_AGENT_SELECT
        await self._require_member(state.active_saas_agent_id, user, db)
        if node_id == CorpusNodeIds.EXECUTION_PLANNING:
            lens = await self._context_lens(state, user, db)
            if lens.tool_count <= 0:
                return CorpusNodeIds.CONNECTION_CONFIGURE
        if node_id == CorpusNodeIds.APPROVAL_REQUIRED and not state.pending_trace_id:
            return CorpusNodeIds.RESULT_REVIEW
        return node_id

    async def _valid_actions(self, state: CorpusGraphState, user: User | None, db: AsyncSession) -> list[Any]:
        node = self._node_by_id.get(state.node) or self._node_by_id[CorpusNodeIds.HOME]
        lens = await self._context_lens(state, user, db)
        actions = []
        for action_id in node.allowed_actions:
            action = self._action_by_id.get(action_id)
            if action and self._is_action_eligible(action_id, state, user, lens):
                payload: dict[str, Any] = {}
                if state.active_saas_agent_id:
                    payload["saas_agent_id"] = str(state.active_saas_agent_id)
                if state.pending_trace_id:
                    payload["trace_id"] = str(state.pending_trace_id)
                actions.append(route_action_to_card(action, payload=payload or None))
        actions.extend(route_action_to_card(action) for action in self.route_actions_for_state(state))
        return actions

    def _is_action_eligible(
        self,
        action_id: str,
        state: CorpusGraphState,
        user: User | None,
        lens: CorpusContextLens,
    ) -> bool:
        if self.is_route_action_id(action_id):
            return True
        if action_id in {CorpusActionIds.AUTH_SIGN_IN, CorpusActionIds.AUTH_REGISTER}:
            return user is None
        if action_id in {CorpusActionIds.HOME, CorpusActionIds.RECOVERY_HOME}:
            return True
        if user is None:
            return False
        if action_id in {CorpusActionIds.SAAS_AGENT_CREATE, CorpusActionIds.SAAS_AGENT_LIST, CorpusActionIds.SAAS_AGENT_OPEN}:
            return True
        if not state.active_saas_agent_id:
            return False
        if action_id in {
            CorpusActionIds.CATALOG_OPEN,
            CorpusActionIds.ENTITIES_OPEN,
            CorpusActionIds.ACTIONS_OPEN,
            CorpusActionIds.EXECUTION_OPEN,
        }:
            return lens.connection_count > 0
        if action_id == CorpusActionIds.EXECUTION_PLAN:
            return lens.tool_count > 0
        if action_id in {CorpusActionIds.APPROVAL_APPROVE, CorpusActionIds.APPROVAL_REJECT}:
            return bool(state.pending_trace_id)
        return True

    def _projection_context(self, state: CorpusGraphState, user: User | None) -> str:
        return "lounge" if user is None and state.node == CorpusNodeIds.HOME else state.node

    def presentation_state_key(self, state: CorpusGraphState, context: dict[str, Any]) -> str:
        user = self._user_from_context(context)
        actor = str(user.id) if user else "anonymous"
        agent = str(state.active_saas_agent_id) if state.active_saas_agent_id else "none"
        return f"{actor}:{agent}:{state.node}"

    def _blocked_actions(
        self,
        state: CorpusGraphState,
        user: User | None,
        lens: CorpusContextLens,
    ) -> list[dict[str, str]]:
        blocked: list[dict[str, str]] = []
        node = self._node_by_id.get(state.node) or self._node_by_id[CorpusNodeIds.HOME]
        for action_id in node.allowed_actions:
            reason = self._action_block_reason(action_id, state, user, lens)
            if reason:
                blocked.append({"id": action_id, "reason": reason})
        return blocked

    def _guard_explanations(
        self,
        state: CorpusGraphState,
        user: User | None,
        lens: CorpusContextLens,
    ) -> list[dict[str, Any]]:
        explanations = []
        if user is None:
            explanations.append({"guard": "auth", "status": "missing", "message": "Authentication is required beyond Lounge and auth flows."})
        if not state.active_saas_agent_id and user is not None:
            explanations.append({"guard": "saas_agent_selection", "status": "missing", "message": "Choose a SaaS Agent before agent-specific routes become reachable."})
        if state.node == CorpusNodeIds.EXECUTION_PLANNING and lens.tool_count <= 0:
            explanations.append({"guard": "tool_readiness", "status": "missing", "message": "Connect and activate an API before execution planning is reachable."})
        if state.node == CorpusNodeIds.APPROVAL_REQUIRED and not state.pending_trace_id:
            explanations.append({"guard": "pending_trace", "status": "missing", "message": "Approval requires a pending execution trace."})
        return explanations

    def _action_block_reason(
        self,
        action_id: str,
        state: CorpusGraphState,
        user: User | None,
        lens: CorpusContextLens,
    ) -> str | None:
        if self.is_route_action_id(action_id):
            return None
        if action_id in {
            CorpusActionIds.AUTH_SIGN_IN,
            CorpusActionIds.AUTH_REGISTER,
            CorpusActionIds.HOME,
            CorpusActionIds.RECOVERY_HOME,
        }:
            return None
        if user is None:
            return "Authentication required"
        if action_id in {CorpusActionIds.SAAS_AGENT_CREATE, CorpusActionIds.SAAS_AGENT_LIST, CorpusActionIds.SAAS_AGENT_OPEN}:
            return None
        if not state.active_saas_agent_id:
            return "SaaS Agent selection required"
        if action_id in {
            CorpusActionIds.CATALOG_OPEN,
            CorpusActionIds.ENTITIES_OPEN,
            CorpusActionIds.ACTIONS_OPEN,
            CorpusActionIds.EXECUTION_OPEN,
        } and lens.connection_count <= 0:
            return "Connect and activate an API first"
        if action_id == CorpusActionIds.EXECUTION_PLAN and lens.tool_count <= 0:
            return "No generated tools are ready yet"
        if action_id in {CorpusActionIds.APPROVAL_APPROVE, CorpusActionIds.APPROVAL_REJECT} and not state.pending_trace_id:
            return "No pending approval exists"
        return None

    async def _context_lens(self, state: CorpusGraphState, user: User | None, db: AsyncSession) -> CorpusContextLens:
        return await self._context_queries.context_lens(state, user, db)

    async def _list_saas_agents(self, user: User | None, db: AsyncSession):
        return await self._context_queries.list_saas_agents(user, db)

    async def _require_member(self, saas_agent_id, user: User, db: AsyncSession):
        return await self._context_queries.require_member(saas_agent_id, user, db)

    def _turn_plan_intent(self, decision: dict[str, Any]) -> str:
        intent = str(decision.get("intent") or "").strip()
        allowed = {"reply_now", "open_surface", "clarify", "deep_work", "propose_operation"}
        if intent in allowed:
            return intent
        return "propose_operation" if decision.get("operation_id") else "reply_now"

    async def _message_delta_events(self, *, projection_version: int, text: str) -> AsyncIterator[dict[str, Any]]:
        for delta in self._message_text_chunks(text):
            yield {"event_type": "message_delta", "projection_version": projection_version, "payload": {"delta": delta}}
            await asyncio.sleep(0)

    async def _stream_reply_events(
        self,
        *,
        api_key: str,
        user_input: str,
        planning_context: dict[str, Any],
        projection_version: int,
        fallback_message: str,
    ) -> AsyncIterator[dict[str, Any]]:
        streamed_text = ""
        try:
            async for delta in self._stream_corpus_message(
                api_key=api_key,
                user_input=user_input,
                planning_context=self._reply_planning_context(planning_context),
            ):
                if not delta:
                    continue
                streamed_text += delta
                yield {"event_type": "message_delta", "projection_version": projection_version, "payload": {"delta": delta}}
        except Exception as exc:
            yield {
                "event_type": "corpus_error",
                "projection_version": projection_version,
                "payload": {"message": "Corpus could not complete the model turn.", "error": exc.__class__.__name__},
            }
            return
        if not streamed_text and fallback_message:
            async for event in self._message_delta_events(projection_version=projection_version, text=fallback_message):
                yield event

    async def _stream_operation_reply_events(
        self,
        *,
        api_key: str,
        user_input: str,
        decision_message: str,
        response: CorpusActionResponse,
        operation_id: str,
        projection_version: int,
    ) -> AsyncIterator[dict[str, Any]]:
        operation_context = self._operation_stream_context(
            response=response,
            operation_id=operation_id,
        )
        try:
            async for delta in self._stream_corpus_operation_message(
                api_key=api_key,
                user_input=user_input,
                decision_message=decision_message,
                operation_context=operation_context,
            ):
                if not delta:
                    continue
                yield {"event_type": "message_delta", "projection_version": projection_version, "payload": {"delta": delta}}
        except Exception as exc:
            yield {
                "event_type": "corpus_error",
                "projection_version": projection_version,
                "payload": {"message": "Corpus completed the operation but could not stream the model reply.", "error": exc.__class__.__name__},
            }

    def _operation_stream_context(
        self,
        *,
        response: CorpusActionResponse,
        operation_id: str,
    ) -> dict[str, Any]:
        active_surface = response.active_surface
        return {
            "operation_id": operation_id,
            "effect_summary": self._operation_effect_summary(response),
            "state": {
                "has_selected_saas_agent": bool(response.state.active_saas_agent_id),
                "has_pending_review_operation": bool(response.state.pending_operation_id),
            },
            "active_surface": {
                "label": active_surface.label or active_surface.name,
                "description": getattr(active_surface, "description", None),
            } if active_surface else None,
            "messages": [message.model_dump(mode="json") for message in response.messages],
        }

    def _operation_effect_summary(self, response: CorpusActionResponse) -> str:
        messages = [message.content.strip() for message in response.messages if message.content.strip()]
        if messages:
            return " ".join(messages)
        if response.active_surface:
            label = response.active_surface.label or response.active_surface.name
            return f"The {label} surface is active. No form has been submitted by this operation."
        return "The workspace state was updated."

    def _message_text_chunks(self, text: str, *, target_size: int = 18) -> list[str]:
        if not text:
            return []
        return [text[index : index + target_size] for index in range(0, len(text), target_size)]

    def _reply_planning_context(self, planning_context: dict[str, Any]) -> dict[str, Any]:
        blocked_keys = {
            "id",
            "operation_id",
            "args",
            "surface_id",
            "input_schema",
            "accepted_arg_keys",
            "required_args",
            "missing_args",
        }
        return self._redact_planning_context(planning_context, blocked_keys=blocked_keys)

    def _redact_planning_context(self, value: Any, *, blocked_keys: set[str]) -> Any:
        if isinstance(value, Mapping):
            return {
                key: self._redact_planning_context(child, blocked_keys=blocked_keys)
                for key, child in value.items()
                if isinstance(key, str) and key not in blocked_keys
            }
        if isinstance(value, list):
            return [self._redact_planning_context(child, blocked_keys=blocked_keys) for child in value]
        return value

    async def _corpus_turn_plan(self, *, api_key: str, user_input: str, planning_context: dict[str, Any]) -> dict[str, Any]:
        from openai import AsyncOpenAI

        from backend.core.langsmith import wrap_openai_client

        client = wrap_openai_client(AsyncOpenAI(api_key=api_key))
        response = await client.chat.completions.create(
            model=settings.default_model,
            messages=[
                {"role": "system", "content": CORPUS_TURN_ROUTER_PROMPT},
                {"role": "user", "content": json.dumps({"user_input": user_input, "planning_context": planning_context})},
            ],
            response_format={"type": "json_object"},
            **_openai_latency_options(),
        )
        content = response.choices[0].message.content or "{}"
        try:
            parsed = json.loads(content)
        except json.JSONDecodeError:
            parsed = {"intent": "clarify", "message": "I could not read the model response.", "operation_id": None, "args": {}}
        return normalize_corpus_turn_plan(parsed, planning_context=planning_context)

    async def _stream_corpus_message(self, *, api_key: str, user_input: str, planning_context: dict[str, Any]) -> AsyncIterator[str]:
        from openai import AsyncOpenAI

        from backend.core.langsmith import wrap_openai_client

        client = wrap_openai_client(AsyncOpenAI(api_key=api_key))
        stream = await client.chat.completions.create(
            model=settings.default_model,
            messages=[
                {"role": "system", "content": CORPUS_STREAM_PROMPT},
                {"role": "user", "content": json.dumps({"user_input": user_input, "planning_context": planning_context})},
            ],
            stream=True,
            **_openai_latency_options(),
        )
        async for chunk in stream:
            content = chunk.choices[0].delta.content if chunk.choices else None
            if content:
                yield content

    async def _stream_corpus_operation_message(
        self,
        *,
        api_key: str,
        user_input: str,
        decision_message: str,
        operation_context: dict[str, Any],
    ) -> AsyncIterator[str]:
        from openai import AsyncOpenAI

        from backend.core.langsmith import wrap_openai_client

        client = wrap_openai_client(AsyncOpenAI(api_key=api_key))
        model_operation_context = {
            key: value
            for key, value in operation_context.items()
            if key != "operation_id"
        }
        stream = await client.chat.completions.create(
            model=settings.default_model,
            messages=[
                {"role": "system", "content": CORPUS_OPERATION_STREAM_PROMPT},
                {
                    "role": "user",
                    "content": json.dumps(
                        {
                            "user_input": user_input,
                            "decision_message": decision_message,
                            "operation_context": model_operation_context,
                        }
                    ),
                },
            ],
            stream=True,
            **_openai_latency_options(),
        )
        async for chunk in stream:
            content = chunk.choices[0].delta.content if chunk.choices else None
            if content:
                yield content



def _openai_latency_options() -> dict[str, Any]:
    effort = settings.openai_reasoning_effort.strip()
    return {"reasoning_effort": effort} if effort else {}


corpus_route_deck_app = (
    RouteDeckApp(CorpusGraphState, runtime_base=CorpusRouteDeckRuntime, name="CorpusRouteDeckRuntime")
    .manifest(CORPUS_MANIFEST)
    .initial_node(CorpusNodeIds.HOME)
    .surfaces(CorpusSurfaceRegistry)
    .navigation(CorpusRouteDeckNavigation)
    .operation_policy(CorpusOperationPolicy)
    .operation_requests(CorpusOperationRequests)
    .route_actions(
        RouteDeckRouteActionIds(
            open_node=CorpusActionIds.ROUTE_OPEN_NODE,
            switch_surface=CorpusActionIds.ROUTE_SWITCH_SURFACE,
            back=CorpusActionIds.ROUTE_BACK,
            forward=CorpusActionIds.ROUTE_FORWARD,
            cancel=CorpusActionIds.ROUTE_CANCEL,
        )
    )
    .operation_review_component("CorpusOperationReviewSurface")
)

route_deck_runtime = corpus_route_deck_app.compile()
