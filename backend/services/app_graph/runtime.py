from __future__ import annotations

import uuid
from typing import Any

from fastapi import HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

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
from backend.core.schemas import (
    AppGraphContextLens,
    AppGraphRequest,
    AppGraphResponse,
    AppGraphState,
    AppGraphSurface,
    EntryGraphManifest,
    EntryGraphMessage,
    EntryRouteDeckRuntimeSnapshot,
    EntryUIArtifact,
    SaaSAgentRead,
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
from backend.services.app_graph.manifest import (
    ACTION_SPECS,
    ACTION_TARGETS,
    APP_GRAPH_VERSION,
    AppActionIds,
    AppNodeIds,
    build_app_graph_manifest,
    route_action_to_card,
)
from backend.services.app_graph.router import AppGraphTurnRouter
from backend.services.catalog import SaaSAgent_catalog, preview_openapi_spec
from backend.services.discovery.activation import ActivationService
from routedeck_core import build_runtime_snapshot


class AppGraphRuntime:
    def __init__(self) -> None:
        self.manifest = build_app_graph_manifest()
        self._action_by_id = {action.id: action for action in ACTION_SPECS}
        self._node_by_id = {node.id: node for node in self.manifest.nodes}
        self.router = AppGraphTurnRouter()

    async def snapshot(self, *, request: AppGraphRequest, user: User | None, db: AsyncSession) -> AppGraphResponse:
        state = await self._initial_state(request, user, db)
        state.node = await self._eligible_node_or_recovery(request.node_id or state.node, state, user, db)
        return await self._response(state=state, user=user, db=db, messages=[])

    async def turn(self, *, request: AppGraphRequest, user: User | None, db: AsyncSession) -> AppGraphResponse:
        if request.selected_action_id:
            return await self.action(request=request, user=user, db=db)
        state = await self._initial_state(request, user, db)
        actions = await self._valid_actions(state, user, db)
        decision = await self.router.route(
            user_input=request.user_input,
            state=state,
            actions=actions,
            manifest=self.manifest,
        )
        clarification = self.router.action_needs_clarification(decision, actions)
        if decision.intent == "action" and decision.action_id and not clarification:
            routed_request = AppGraphRequest(
                state=state,
                selected_action_id=decision.action_id,
                action_payload=decision.slots,
            )
            response = await self.action(request=routed_request, user=user, db=db)
            response.evidence.append({"type": "turn_router", "decision": decision.model_dump(mode="json")})
            return response
        message = clarification or decision.clarification or "I can help from here. Choose one of the visible next steps."
        return await self._response(
            state=state,
            user=user,
            db=db,
            messages=[EntryGraphMessage(content=message)],
            evidence=[{"type": "turn_router", "decision": decision.model_dump(mode="json")}],
        )

    async def action(self, *, request: AppGraphRequest, user: User | None, db: AsyncSession) -> AppGraphResponse:
        state = await self._initial_state(request, user, db)
        action_id = request.selected_action_id
        payload = request.action_payload or {}
        if not action_id or action_id not in self._action_by_id:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Unknown app action")
        valid_ids = {action.id for action in await self._valid_actions(state, user, db)}
        if action_id not in valid_ids:
            state.node = AppNodeIds.RECOVERY
            return await self._response(
                state=state,
                user=user,
                db=db,
                messages=[EntryGraphMessage(content="That action is not available from here.")],
                evidence=[{"type": "blocked_action", "action_id": action_id, "valid_actions": sorted(valid_ids)}],
            )
        handler = getattr(self, f"_handle_{action_id.replace('.', '_')}", None)
        if handler is None:
            state.node = ACTION_TARGETS[action_id]
            messages: list[EntryGraphMessage] = []
            evidence: list[dict[str, Any]] = []
        else:
            state, messages, evidence = await handler(state, payload, user, db)
        if state.node not in state.executed_nodes:
            state.executed_nodes.append(state.node)
        return await self._response(state=state, user=user, db=db, messages=messages, evidence=evidence)

    async def _initial_state(self, request: AppGraphRequest, user: User | None, db: AsyncSession) -> AppGraphState:
        state = request.state or AppGraphState()
        if request.saas_agent_id:
            state.active_saas_agent_id = request.saas_agent_id
        if state.active_saas_agent_id and user:
            await self._require_member(state.active_saas_agent_id, user, db)
        if not user and state.node not in {AppNodeIds.HOME, AppNodeIds.AUTH_SIGN_IN, AppNodeIds.AUTH_REGISTER}:
            state.node = AppNodeIds.HOME
            state.active_saas_agent_id = None
        if state.node not in self._node_by_id:
            state.node = AppNodeIds.RECOVERY
        if not state.executed_nodes:
            state.executed_nodes = [state.node]
        return state

    async def _eligible_node_or_recovery(self, node_id: str, state: AppGraphState, user: User | None, db: AsyncSession) -> str:
        if node_id not in self._node_by_id:
            return AppNodeIds.RECOVERY
        if node_id in {AppNodeIds.HOME, AppNodeIds.AUTH_SIGN_IN, AppNodeIds.AUTH_REGISTER, AppNodeIds.RECOVERY}:
            return node_id
        if user is None:
            return AppNodeIds.HOME
        if node_id in {AppNodeIds.SAAS_AGENT_SELECT, AppNodeIds.SAAS_AGENT_CREATE}:
            return node_id
        if not state.active_saas_agent_id:
            return AppNodeIds.SAAS_AGENT_SELECT
        await self._require_member(state.active_saas_agent_id, user, db)
        if node_id == AppNodeIds.EXECUTION_PLANNING:
            lens = await self._context_lens(state, user, db)
            if lens.tool_count <= 0:
                return AppNodeIds.CONNECTION_CONFIGURE
        if node_id == AppNodeIds.APPROVAL_REQUIRED and not state.pending_trace_id:
            return AppNodeIds.RESULT_REVIEW
        return node_id

    async def _valid_actions(self, state: AppGraphState, user: User | None, db: AsyncSession):
        node = self._node_by_id.get(state.node) or self._node_by_id[AppNodeIds.HOME]
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
        return actions

    def _is_action_eligible(self, action_id: str, state: AppGraphState, user: User | None, lens: AppGraphContextLens) -> bool:
        if action_id in {AppActionIds.AUTH_SIGN_IN, AppActionIds.AUTH_REGISTER, AppActionIds.HOME, AppActionIds.RECOVERY_HOME}:
            return True
        if user is None:
            return False
        if action_id in {AppActionIds.SAAS_AGENT_CREATE, AppActionIds.SAAS_AGENT_OPEN}:
            return True
        if not state.active_saas_agent_id:
            return False
        if action_id in {AppActionIds.CATALOG_OPEN, AppActionIds.ENTITIES_OPEN, AppActionIds.ACTIONS_OPEN, AppActionIds.EXECUTION_OPEN}:
            return lens.connection_count > 0
        if action_id == AppActionIds.EXECUTION_PLAN:
            return lens.tool_count > 0
        if action_id in {AppActionIds.APPROVAL_APPROVE, AppActionIds.APPROVAL_REJECT}:
            return bool(state.pending_trace_id)
        return True

    async def _response(self, *, state: AppGraphState, user: User | None, db: AsyncSession, messages: list[EntryGraphMessage], evidence: list[dict[str, Any]] | None = None) -> AppGraphResponse:
        state.node = await self._eligible_node_or_recovery(state.node, state, user, db)
        actions = await self._valid_actions(state, user, db)
        lens = await self._context_lens(state, user, db)
        snapshot = build_runtime_snapshot(
            self.manifest,
            current_node=state.node,
            valid_actions=[action.model_dump() for action in actions],
            executed_nodes=state.executed_nodes,
            diagnostics={"source": "app_graph", "graph_version": APP_GRAPH_VERSION, "selected_saas_agent_id": str(state.active_saas_agent_id) if state.active_saas_agent_id else None},
        )
        return AppGraphResponse(
            state=state,
            graph_version=APP_GRAPH_VERSION,
            graph_manifest=EntryGraphManifest.model_validate(self.manifest.model_dump(by_alias=True)),
            route_deck_snapshot=EntryRouteDeckRuntimeSnapshot.model_validate(snapshot),
            context_lens=lens,
            active_surface=self._surface_for_state(state, lens),
            available_actions=actions,
            persistent_actions=await self._persistent_actions(state, user, lens),
            ui_artifacts=[EntryUIArtifact(id="context-lens", kind="widget", surface="both", title="Context lens", widget_type="context_lens", payload=lens.model_dump(mode="json"))],
            evidence=evidence or [],
            diagnostics=snapshot["diagnostics"],
            messages=messages,
            saas_agents=await self._list_saas_agents(user, db),
            replace_path=self._path_for_state(state),
        )

    async def _persistent_actions(self, state: AppGraphState, user: User | None, lens: AppGraphContextLens):
        if user is None:
            return []
        ids = [AppActionIds.HOME]
        if state.active_saas_agent_id:
            ids.extend([AppActionIds.AGENT_HOME, AppActionIds.CONNECTION_CONFIGURE, AppActionIds.KNOWLEDGE_OPEN, AppActionIds.MEMORY_OPEN, AppActionIds.LEARNING_OPEN, AppActionIds.QA_OPEN])
            if lens.connection_count > 0:
                ids.extend([AppActionIds.CATALOG_OPEN, AppActionIds.ENTITIES_OPEN, AppActionIds.ACTIONS_OPEN, AppActionIds.EXECUTION_OPEN])
        return [route_action_to_card(self._action_by_id[action_id]) for action_id in ids]

    def _surface_for_state(self, state: AppGraphState, lens: AppGraphContextLens) -> AppGraphSurface:
        renderers = {
            AppNodeIds.HOME: ("home", "Home"),
            AppNodeIds.AUTH_SIGN_IN: ("auth_sign_in", "Sign in"),
            AppNodeIds.AUTH_REGISTER: ("auth_register", "Register"),
            AppNodeIds.SAAS_AGENT_SELECT: ("home", "Select SaaS Agent"),
            AppNodeIds.SAAS_AGENT_CREATE: ("home", "Create SaaS Agent"),
            AppNodeIds.AGENT_HOME: ("agent_home", "SaaS Agent Home"),
            AppNodeIds.CONNECTION_CONFIGURE: ("connection_configure", "Connection Setup"),
            AppNodeIds.SCHEMA_PREVIEW: ("schema_preview", "Schema Preview"),
            AppNodeIds.CATALOG_ACTIVATION: ("catalog_activation", "Catalog Activation"),
            AppNodeIds.CATALOG: ("catalog", "Catalog"),
            AppNodeIds.ENTITIES: ("entities", "Entities"),
            AppNodeIds.ACTIONS: ("actions", "Actions"),
            AppNodeIds.EXECUTION_PLANNING: ("execution", "Execution Planning"),
            AppNodeIds.NEEDS_INPUT: ("execution", "Missing Inputs"),
            AppNodeIds.APPROVAL_REQUIRED: ("execution", "Approval Required"),
            AppNodeIds.EXECUTING: ("execution", "Executing"),
            AppNodeIds.RESULT_REVIEW: ("execution", "Result Review"),
            AppNodeIds.KNOWLEDGE: ("knowledge", "Knowledge"),
            AppNodeIds.MEMORY: ("memory", "Memory"),
            AppNodeIds.LEARNING: ("learning", "Learning"),
            AppNodeIds.QA: ("qa", "QA"),
            AppNodeIds.RECOVERY: ("recovery", "Recovery"),
        }
        renderer, title = renderers.get(state.node, ("recovery", "Recovery"))
        return AppGraphSurface(id=state.node, renderer=renderer, title=title, payload={"lens": lens.model_dump(mode="json"), **state.graph_context})

    def _path_for_state(self, state: AppGraphState) -> str:
        if state.active_saas_agent_id:
            return f"/app/agents/{state.active_saas_agent_id}" if state.node == AppNodeIds.AGENT_HOME else f"/app/agents/{state.active_saas_agent_id}/{state.node}"
        return "/app/home" if state.node == AppNodeIds.HOME else f"/app/{state.node}"

    async def _context_lens(self, state: AppGraphState, user: User | None, db: AsyncSession) -> AppGraphContextLens:
        selected = await db.get(SaaSAgent, state.active_saas_agent_id) if state.active_saas_agent_id and user else None
        connection_count = ready_connection_count = action_count = tool_count = 0
        pending_status = None
        if selected is not None:
            connection_count = int((await db.execute(select(func.count(Connection.id)).where(Connection.saas_agent_id == selected.id))).scalar_one() or 0)
            ready_connection_count = int((await db.execute(select(func.count(ConnectionActivationState.connection_id)).where(ConnectionActivationState.saas_agent_id == selected.id, ConnectionActivationState.overall_status == "ready"))).scalar_one() or 0)
            action_count = int((await db.execute(select(func.count(ActionNode.id)).where(ActionNode.saas_agent_id == selected.id))).scalar_one() or 0)
            tool_count = int((await db.execute(select(func.count(GeneratedTool.id)).where(GeneratedTool.saas_agent_id == selected.id))).scalar_one() or 0)
            if state.pending_trace_id:
                trace = await db.get(AgentExecutionTrace, state.pending_trace_id)
                pending_status = trace.status if trace else None
        node = self._node_by_id.get(state.node)
        return AppGraphContextLens(
            selected_saas_agent_id=selected.id if selected else None,
            selected_saas_agent_name=selected.name if selected else None,
            selected_saas_agent_slug=selected.slug if selected else None,
            current_node=state.node,
            working_on=node.label if node else "Recovery",
            connection_count=connection_count,
            ready_connection_count=ready_connection_count,
            action_count=action_count,
            tool_count=tool_count,
            pending_trace_id=state.pending_trace_id,
            pending_trace_status=pending_status,
        )

    async def _list_saas_agents(self, user: User | None, db: AsyncSession) -> list[SaaSAgentRead]:
        if user is None:
            return []
        result = await db.execute(select(SaaSAgent, SaaSAgentMember.role).join(SaaSAgentMember, SaaSAgentMember.saas_agent_id == SaaSAgent.id).where(SaaSAgentMember.user_id == user.id).order_by(SaaSAgent.created_at.desc()))
        return [SaaSAgentRead(id=agent.id, name=agent.name, slug=agent.slug, created_by=agent.created_by, created_at=agent.created_at, role=role.value if hasattr(role, "value") else str(role)) for agent, role in result.all()]

    async def _require_member(self, saas_agent_id: uuid.UUID, user: User, db: AsyncSession) -> SaaSAgentMember:
        member = (await db.execute(select(SaaSAgentMember).where(SaaSAgentMember.saas_agent_id == saas_agent_id, SaaSAgentMember.user_id == user.id))).scalar_one_or_none()
        if member is None:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not a member of this SaaS Agent")
        return member

    async def _handle_navigate_home(self, state, payload, user, db):
        state.node = AppNodeIds.HOME
        return state, [], []

    async def _handle_recovery_home(self, state, payload, user, db):
        return await self._handle_navigate_home(state, payload, user, db)

    async def _handle_auth_sign_in(self, state, payload, user, db):
        state.node = AppNodeIds.AUTH_SIGN_IN
        return state, [EntryGraphMessage(content="Sign in, and I will keep the current work ready for you.")], []

    async def _handle_auth_register(self, state, payload, user, db):
        state.node = AppNodeIds.AUTH_REGISTER
        return state, [EntryGraphMessage(content="Create your account, and I will continue from here.")], []

    async def _handle_saas_agent_open(self, state, payload, user, db):
        if user is None:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Authentication required")
        raw_id = payload.get("saas_agent_id") or state.active_saas_agent_id
        if not raw_id:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="saas_agent_id is required")
        state.active_saas_agent_id = uuid.UUID(str(raw_id))
        await self._require_member(state.active_saas_agent_id, user, db)
        state.node = AppNodeIds.AGENT_HOME
        return state, [EntryGraphMessage(content="I opened that SaaS Agent.")], [{"type": "saas_agent_selected", "saas_agent_id": str(state.active_saas_agent_id)}]

    async def _handle_saas_agent_create(self, state, payload, user, db):
        if user is None:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Authentication required")
        name = str(payload.get("name") or "").strip()
        slug = str(payload.get("slug") or "").strip()
        if not name or not slug:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="name and slug are required")
        if (await db.execute(select(SaaSAgent).where(SaaSAgent.slug == slug))).scalar_one_or_none():
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="SaaS Agent slug already taken")
        agent = SaaSAgent(id=uuid.uuid4(), name=name, slug=slug, created_by=user.id)
        db.add(agent)
        db.add(SaaSAgentMember(user_id=user.id, saas_agent_id=agent.id, role=SaaSAgentRole.owner))
        await db.commit()
        await db.refresh(agent)
        await create_tenant_schema(agent.id)
        state.active_saas_agent_id = agent.id
        state.node = AppNodeIds.AGENT_HOME
        return state, [EntryGraphMessage(content=f"Created {agent.name}. Next we can connect its API.")], [{"type": "saas_agent_created", "saas_agent_id": str(agent.id)}]

    async def _handle_navigate_agent_home(self, state, payload, user, db):
        state.node = AppNodeIds.AGENT_HOME
        return state, [], []

    async def _handle_navigate_connection_configure(self, state, payload, user, db):
        state.node = AppNodeIds.CONNECTION_CONFIGURE
        return state, [], []

    async def _handle_connection_preview(self, state, payload, user, db):
        preview = await preview_openapi_spec(spec_url=str(payload.get("spec_url") or ""), raw_spec=payload.get("raw_spec"))
        state.node = AppNodeIds.SCHEMA_PREVIEW
        state.graph_context["schema_preview"] = preview.model_dump()
        return state, [EntryGraphMessage(content=f"Previewed `{preview.title}` with {preview.endpoint_count} endpoints.")], [{"type": "schema_preview", **preview.model_dump()}]

    async def _handle_connection_activate(self, state, payload, user, db):
        if user is None or not state.active_saas_agent_id:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="SaaS Agent selection required")
        await self._require_member(state.active_saas_agent_id, user, db)
        connection_id = payload.get("connection_id")
        if connection_id:
            connection = await db.get(Connection, uuid.UUID(str(connection_id)))
            if connection is None or connection.saas_agent_id != state.active_saas_agent_id:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Connection not found")
        else:
            auth_type = str(payload.get("auth_type") or "none")
            connection = Connection(saas_agent_id=state.active_saas_agent_id, name=str(payload.get("name") or "Primary API"), type=ConnectionType.rest_api, provider="rest_api", config={"base_url": payload.get("base_url"), "spec_url": payload.get("spec_url"), "auth_type": auth_type}, auth_type=AuthType(auth_type))
            db.add(connection)
            await db.flush()
            credential_value = str(payload.get("credential_value") or "")
            if credential_value:
                db.add(EncryptedCredential(connection_id=connection.id, credential_type="credential_value", encrypted_value=encrypt_value(credential_value), metadata_={key: payload.get(key) for key in ("header_name", "query_param_name") if payload.get(key)}))
            db.add(ConnectionActivationState(connection_id=connection.id, saas_agent_id=state.active_saas_agent_id))
            await db.commit()
            await db.refresh(connection)
        state.active_connection_id = connection.id
        state.node = AppNodeIds.CATALOG_ACTIVATION
        events = []
        async for event in ActivationService().activate(connection_id=connection.id, saas_agent_id=state.active_saas_agent_id, session=db):
            events.append(event)
        state.node = AppNodeIds.CATALOG
        state.graph_context["activation_events"] = events
        return state, [EntryGraphMessage(content="The API catalog is activated and ready to inspect.")], [{"type": "activation", "events": events}]

    async def _handle_catalog_open(self, state, payload, user, db):
        if state.active_saas_agent_id:
            state.graph_context["catalog"] = await SaaSAgent_catalog(db, state.active_saas_agent_id)
        state.node = AppNodeIds.CATALOG
        return state, [], []

    async def _handle_entities_open(self, state, payload, user, db):
        state.node = AppNodeIds.ENTITIES
        return state, [], []

    async def _handle_actions_open(self, state, payload, user, db):
        state.node = AppNodeIds.ACTIONS
        return state, [], []

    async def _handle_execution_open(self, state, payload, user, db):
        state.node = AppNodeIds.EXECUTION_PLANNING
        return state, [], []

    async def _handle_execution_plan(self, state, payload, user, db):
        if user is None or not state.active_saas_agent_id:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="SaaS Agent selection required")
        goal = str(payload.get("goal") or "").strip()
        if not goal:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="goal is required")
        candidates = await find_tool_candidates(message=goal, saas_agent_id=state.active_saas_agent_id, db=db, limit=5)
        if not candidates:
            state.node = AppNodeIds.RESULT_REVIEW
            return state, [EntryGraphMessage(content="No generated API tool matched that goal.")], [{"type": "execution_candidates", "candidates": []}]
        top = candidates[0]
        inputs, missing = self._extract_inputs(goal, top.tool)
        summary = _candidate_summary_rows(candidates)
        risk = _risk_value(top.tool.risk_level)
        if missing:
            trace = await create_execution_trace(candidate=top, inputs=inputs, missing=missing, candidate_summary=summary, status="needs_input", approval_state="not_required", route_node=AppNodeIds.NEEDS_INPUT, saas_agent_id=state.active_saas_agent_id, session_id=None, user_id=user.id, db=db)
            state.pending_trace_id = trace.id
            state.node = AppNodeIds.NEEDS_INPUT
            return state, [EntryGraphMessage(content=f"`{top.tool.name}` needs more input before execution.")], [{"type": "needs_input", "trace_id": str(trace.id), "missing": missing, "candidates": summary}]
        if risk != "read" or top.tool.requires_approval:
            trace = await create_execution_trace(candidate=top, inputs=inputs, missing=[], candidate_summary=summary, status="approval_required", approval_state="pending", route_node=AppNodeIds.APPROVAL_REQUIRED, saas_agent_id=state.active_saas_agent_id, session_id=None, user_id=user.id, db=db)
            state.pending_trace_id = trace.id
            state.node = AppNodeIds.APPROVAL_REQUIRED
            return state, [EntryGraphMessage(content=f"`{top.tool.name}` requires approval before execution.")], [{"type": "approval_required", "trace_id": str(trace.id), "risk": risk, "candidates": summary}]
        trace = await create_execution_trace(candidate=top, inputs=inputs, missing=[], candidate_summary=summary, status="executing", approval_state="not_required", route_node=AppNodeIds.EXECUTING, saas_agent_id=state.active_saas_agent_id, session_id=None, user_id=user.id, db=db)
        result = await execute_rest_tool(top, inputs, db)
        await finalize_execution_trace(trace, result, db)
        state.pending_trace_id = trace.id
        state.node = AppNodeIds.RESULT_REVIEW
        state.graph_context["execution_result"] = result
        return state, [EntryGraphMessage(content=f"Executed `{top.tool.name}` with status {result.get('status_code')}.")], [{"type": "execution_result", "trace_id": str(trace.id), "result": result, "candidates": summary, "preview": _preview_body(result.get("body"))}]

    async def _handle_approval_approve(self, state, payload, user, db):
        if user is None:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Authentication required")
        trace_id = uuid.UUID(str(payload.get("trace_id") or state.pending_trace_id))
        trace = await db.get(AgentExecutionTrace, trace_id)
        if trace is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Trace not found")
        candidate = await _candidate_from_trace(db, trace)
        if candidate is None:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Trace candidate no longer exists")
        trace.status = "executing"
        trace.approval_state = "approved"
        trace.approved_by = user.id
        await db.commit()
        result = await execute_rest_tool(candidate, trace.inputs or {}, db)
        await finalize_execution_trace(trace, result, db)
        state.pending_trace_id = trace.id
        state.node = AppNodeIds.RESULT_REVIEW
        state.graph_context["execution_result"] = result
        return state, [EntryGraphMessage(content=f"Approved and executed `{trace.tool_name}`.")], [{"type": "approval_approved", "trace_id": str(trace.id), "result": result}]

    async def _handle_approval_reject(self, state, payload, user, db):
        trace_id = uuid.UUID(str(payload.get("trace_id") or state.pending_trace_id))
        trace = await db.get(AgentExecutionTrace, trace_id)
        if trace is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Trace not found")
        trace.status = "canceled"
        trace.approval_state = "rejected"
        trace.route_node = AppNodeIds.RESULT_REVIEW
        trace.approved_by = user.id if user else None
        await db.commit()
        state.pending_trace_id = trace.id
        state.node = AppNodeIds.RESULT_REVIEW
        return state, [EntryGraphMessage(content=f"Rejected execution trace `{str(trace.id)[:8]}`.")], [{"type": "approval_rejected", "trace_id": str(trace.id)}]

    async def _handle_knowledge_open(self, state, payload, user, db):
        state.node = AppNodeIds.KNOWLEDGE
        return state, [], []

    async def _handle_knowledge_generate(self, state, payload, user, db):
        if not state.active_saas_agent_id:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="SaaS Agent selection required")
        result = await rag_service.ingest_generated_knowledge(saas_agent_id=state.active_saas_agent_id, db=db)
        state.node = AppNodeIds.KNOWLEDGE
        return state, [EntryGraphMessage(content=f"Generated catalog RAG: {result['documents']} documents, {result['chunks']} chunks.")], [{"type": "rag_generation", **result}]

    async def _handle_memory_open(self, state, payload, user, db):
        state.node = AppNodeIds.MEMORY
        return state, [], []

    async def _handle_memory_save(self, state, payload, user, db):
        if user is None or not state.active_saas_agent_id:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="SaaS Agent selection required")
        memory = await memory_service.save(str(payload.get("content") or ""), saas_agent_id=state.active_saas_agent_id, category=str(payload.get("category") or "fact"), user_id=user.id, db=db)
        state.node = AppNodeIds.MEMORY
        return state, [EntryGraphMessage(content="Saved that memory for this SaaS Agent.")], [{"type": "memory_saved", "memory_id": str(memory.id)}]

    async def _handle_learning_open(self, state, payload, user, db):
        state.node = AppNodeIds.LEARNING
        return state, [], []

    async def _handle_learning_approve(self, state, payload, user, db):
        return await self._review_learning(state, payload, user, db, "approved")

    async def _handle_learning_reject(self, state, payload, user, db):
        return await self._review_learning(state, payload, user, db, "rejected")

    async def _review_learning(self, state, payload, user, db, review_status: str):
        if user is None or not state.active_saas_agent_id:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="SaaS Agent selection required")
        candidate = await learning_service.review(candidate_id=uuid.UUID(str(payload.get("candidate_id"))), saas_agent_id=state.active_saas_agent_id, status=review_status, reviewed_by=user.id, db=db)
        if candidate is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Learning candidate not found")
        state.node = AppNodeIds.LEARNING
        return state, [EntryGraphMessage(content=f"Learning candidate {review_status}.")], [{"type": "learning_reviewed", "candidate_id": str(candidate.id), "status": candidate.status}]

    async def _handle_qa_open(self, state, payload, user, db):
        state.node = AppNodeIds.QA
        return state, [], []

    async def _handle_qa_run(self, state, payload, user, db):
        state.node = AppNodeIds.QA
        return state, [EntryGraphMessage(content="QA scenarios are ready to validate the current flow and evidence.")], [{"type": "qa_contract", "scenario_basis": ["node_id", "action_id", "evidence"]}]

    def _extract_inputs(self, goal: str, tool: GeneratedTool) -> tuple[dict[str, Any], list[str]]:
        values: dict[str, Any] = {}
        for chunk in goal.split():
            if "=" in chunk:
                key, value = chunk.split("=", 1)
                values[key.strip()] = value.strip().strip(",")
        schema = (tool.function_schema or {}).get("parameters") or {}
        required = list(schema.get("required") or []) if isinstance(schema, dict) else []
        return values, [name for name in required if name not in values]


app_graph_runtime = AppGraphRuntime()
