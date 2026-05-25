from __future__ import annotations

import asyncio
import json
import uuid
from typing import Any, AsyncIterator

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
from backend.core.schemas import (
    AppGraphContextLens,
    AppGraphRequest,
    AppGraphResponse,
    AppGraphState,
    CorpusActionResponse,
    CorpusDiagnosticsSnapshot,
    CorpusProposal,
    CorpusStateResponse,
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
from backend.services.app_graph.corpus_operations import CorpusOperationPolicy
from backend.services.app_graph.corpus_routedeck_state import CorpusRouteDeckStateProjector
from backend.services.app_graph.corpus_surfaces import CorpusSurfaceRegistry
from backend.services.catalog import SaaSAgent_catalog, preview_openapi_spec
from backend.services.discovery.activation import ActivationService
from routedeck_core import RouteDeckOperation, RouteDeckSurface, build_runtime_snapshot


CORPUS_TURN_ROUTER_PROMPT = """You are Corpus, the central SaaStoAgent platform graph agent.
You own platform navigation, setup, recovery, and surface selection for SaaStoAgent.
You do not run created SaaS Agents in this version.
Classify the turn, choose at most one legal RouteDeck operation, and return only JSON:
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
- Use only operation ids present in route_deck_projection.legal_operations.
- Use "open_surface" when the user asks to open a workflow surface such as signup, login, API setup, knowledge, memory, execution, QA, or recovery.
- Use "propose_operation" for legal operations that require review before execution.
- Use "reply_now" for greetings, short platform questions, and requests that can be answered from the projection without another model pass.
- Use "clarify" when the request is ambiguous or no legal operation can satisfy it.
- Use "deep_work" only when a slower synthesized answer is genuinely needed.
- For surface-opening turns, make "message" the prompt to show after the active surface is visible."""

CORPUS_STREAM_PROMPT = """You are Corpus, the central SaaStoAgent platform agent.
Respond conversationally and concisely to the user based on the RouteDeck
projection. Do not claim to run created SaaS Agents. If a platform action is
needed, describe the next step naturally; the Corpus graph will decide the typed
operation separately."""

CORPUS_ROUTER_FIRST_TOKEN_BUDGET_SECONDS = 0.6


class CorpusGraphRuntime:
    def __init__(self) -> None:
        self.manifest = build_app_graph_manifest()
        self._action_by_id = {action.id: action for action in ACTION_SPECS}
        self._node_by_id = {node.id: node for node in self.manifest.nodes}
        self._presentation_state_by_key: dict[str, dict[str, Any]] = {}
        self._operation_policy = CorpusOperationPolicy()
        self._surface_registry = CorpusSurfaceRegistry()
        self._route_deck_projector = CorpusRouteDeckStateProjector(
            manifest=self.manifest,
            node_by_id=self._node_by_id,
            operation_policy=self._operation_policy,
            surface_registry=self._surface_registry,
        )

    async def snapshot(self, *, request: AppGraphRequest, user: User | None, db: AsyncSession) -> AppGraphResponse:
        state = await self._initial_state(request, user, db)
        state.node = await self._eligible_node_or_recovery(request.node_id or state.node, state, user, db)
        return await self._response(state=state, user=user, db=db, messages=[])

    async def route_deck_projection(
        self,
        *,
        request: AppGraphRequest,
        user: User | None,
        db: AsyncSession,
        projection_version: int = 1,
    ):
        state = await self._initial_state(request, user, db)
        state.node = await self._eligible_node_or_recovery(request.node_id or state.node, state, user, db)
        actions = await self._valid_actions(state, user, db)
        lens = await self._context_lens(state, user, db)
        saas_agents = await self._list_saas_agents(user, db)
        context = self._projection_context(state, user)
        presentation_state = self._presentation_state_by_key.get(self._presentation_key(state, user), {})
        replace_path = self._path_for_state(state)
        blocked_actions = self._blocked_actions(state, user, lens)
        return self._route_deck_projector.project(
            state=state,
            user=user,
            lens=lens,
            actions=actions,
            saas_agents=saas_agents,
            context=context,
            presentation_state=presentation_state,
            replace_path=replace_path,
            projection_version=projection_version,
            blocked_actions=blocked_actions,
            guard_explanations=self._guard_explanations(state, user, lens),
        )

    async def corpus_state(
        self,
        *,
        request: AppGraphRequest,
        user: User | None,
        db: AsyncSession,
        projection_version: int = 1,
    ) -> CorpusStateResponse:
        state = await self._initial_state(request, user, db)
        state.node = await self._eligible_node_or_recovery(request.node_id or state.node, state, user, db)
        projection = await self.route_deck_projection(
            request=AppGraphRequest(
                state=state,
                node_id=state.node,
                saas_agent_id=state.active_saas_agent_id,
            ),
            user=user,
            db=db,
            projection_version=projection_version,
        )
        return CorpusStateResponse(
            state=state,
            projection=projection,
            replace_path=self._path_for_state(state),
        )

    async def diagnostics_snapshot(
        self,
        *,
        request: AppGraphRequest,
        user: User | None,
        db: AsyncSession,
        projection_version: int = 1,
    ) -> CorpusDiagnosticsSnapshot:
        state = await self._initial_state(request, user, db)
        state.node = await self._eligible_node_or_recovery(request.node_id or state.node, state, user, db)
        normalized_request = AppGraphRequest(
            state=state,
            node_id=state.node,
            saas_agent_id=state.active_saas_agent_id,
            user_input=request.user_input,
        )
        projection = await self.route_deck_projection(
            request=normalized_request,
            user=user,
            db=db,
            projection_version=projection_version,
        )
        introspection = projection.diagnostics.get("introspection") if isinstance(projection.diagnostics, dict) else {}
        runtime_snapshot = introspection.get("runtime_snapshot") if isinstance(introspection, dict) else {}
        return CorpusDiagnosticsSnapshot(
            graph_manifest=self.manifest.model_dump(by_alias=True),
            runtime_snapshot=runtime_snapshot or {},
            introspection=introspection or {},
            projection=projection,
        )

    async def corpus_action(
        self,
        *,
        request: AppGraphRequest,
        operation_id: str,
        args: dict[str, Any] | None,
        user: User | None,
        db: AsyncSession,
        projection_version: int = 1,
    ) -> CorpusActionResponse:
        turn_state = await self._initial_state(request, user, db)
        turn_state.node = await self._eligible_node_or_recovery(request.node_id or turn_state.node, turn_state, user, db)
        normalized_request = AppGraphRequest(
            state=turn_state,
            node_id=turn_state.node,
            saas_agent_id=turn_state.active_saas_agent_id,
            user_input=request.user_input,
        )
        projection = await self.route_deck_projection(
            request=normalized_request,
            user=user,
            db=db,
            projection_version=projection_version,
        )
        operation = next((candidate for candidate in projection.legal_operations if candidate.id == operation_id), None)
        if operation is None:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Operation is not legal from the current graph state")
        response = await self.action(
            request=AppGraphRequest(
                state=turn_state,
                node_id=turn_state.node,
                saas_agent_id=turn_state.active_saas_agent_id,
                selected_action_id=operation_id,
                action_payload={**operation.payload, **(args or {})},
            ),
            user=user,
            db=db,
        )
        next_projection = await self.route_deck_projection(
            request=AppGraphRequest(
                state=response.state,
                node_id=response.state.node,
                saas_agent_id=response.state.active_saas_agent_id,
            ),
            user=user,
            db=db,
            projection_version=projection_version + 1,
        )
        active_surface = next((surface for surface in next_projection.surfaces.values() if surface.role == "active"), None)
        return CorpusActionResponse(
            state=response.state,
            projection=next_projection,
            active_surface=active_surface,
            messages=response.messages,
            replace_path=response.replace_path,
        )

    async def stream_corpus_turn(
        self,
        *,
        request: AppGraphRequest,
        user: User | None,
        db: AsyncSession,
        projection_version: int = 1,
        openai_api_key: str | None = None,
    ) -> AsyncIterator[dict[str, Any]]:
        turn_state = await self._initial_state(request, user, db)
        turn_state.node = await self._eligible_node_or_recovery(request.node_id or turn_state.node, turn_state, user, db)
        normalized_request = AppGraphRequest(
            state=turn_state,
            node_id=turn_state.node,
            saas_agent_id=turn_state.active_saas_agent_id,
            user_input=request.user_input,
        )
        projection = await self.route_deck_projection(
            request=normalized_request,
            user=user,
            db=db,
            projection_version=projection_version,
        )
        decision = self._deterministic_turn_plan(
            user_input=request.user_input or "",
            state=turn_state,
            projection=projection,
        )
        streamed_before_decision = False
        if decision is not None:
            yield {"event_type": "corpus_status", "projection_version": projection.projection_version, "payload": {"status": "thinking"}}
        else:
            api_key = settings.openai_api_key if openai_api_key is None else openai_api_key
            if not api_key:
                raise HTTPException(
                    status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                    detail="Corpus graph requires a configured LLM. Set STA_OPENAI_API_KEY before using Corpus.",
                )
            yield {"event_type": "corpus_status", "projection_version": projection.projection_version, "payload": {"status": "thinking"}}
            decision_task = asyncio.create_task(
                self._corpus_turn_plan(
                    api_key=api_key,
                    user_input=request.user_input or "",
                    projection=projection.model_dump(mode="json"),
                )
            )
            try:
                decision = await asyncio.wait_for(
                    asyncio.shield(decision_task),
                    timeout=CORPUS_ROUTER_FIRST_TOKEN_BUDGET_SECONDS,
                )
            except asyncio.TimeoutError:
                streamed_before_decision = True
                async for event in self._stream_reply_events(
                    api_key=api_key,
                    user_input=request.user_input or "",
                    projection=projection.model_dump(mode="json"),
                    projection_version=projection.projection_version,
                    fallback_message="",
                ):
                    yield event
                try:
                    decision = await decision_task
                except Exception as exc:
                    yield {
                        "event_type": "corpus_error",
                        "projection_version": projection.projection_version,
                        "payload": {"message": "Corpus could not complete the model turn.", "error": exc.__class__.__name__},
                    }
                    return
            except Exception as exc:
                yield {
                    "event_type": "corpus_error",
                    "projection_version": projection.projection_version,
                    "payload": {"message": "Corpus could not complete the model turn.", "error": exc.__class__.__name__},
                }
                return
        surface_intent_changed = self._store_surface_intent(turn_state, user, decision.get("surface_intent"))
        if surface_intent_changed:
            projection = await self.route_deck_projection(
                request=normalized_request,
                user=user,
                db=db,
                projection_version=projection.projection_version + 1,
            )
            yield {
                "event_type": "projection_update",
                "projection_version": projection.projection_version,
                "payload": {"projection": projection.model_dump(mode="json")},
            }
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
                        projection=projection.model_dump(mode="json"),
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
            if streamed_before_decision:
                pass
            elif surface_intent_changed:
                async for event in self._message_delta_events(projection_version=projection.projection_version, text=message):
                    yield event
            else:
                async for event in self._stream_reply_events(
                    api_key=api_key,
                    user_input=request.user_input or "",
                    projection=projection.model_dump(mode="json"),
                    projection_version=projection.projection_version,
                    fallback_message=message,
                ):
                    yield event
            done_status = intent if intent in {"reply_now", "clarify"} else "clarify"
            yield {"event_type": "corpus_done", "projection_version": projection.projection_version, "payload": {"status": done_status}}
            return
        if operation.execution_mode == "auto":
            response = await self.corpus_action(
                request=normalized_request,
                operation_id=operation.id,
                args=decision.get("args") or {},
                user=user,
                db=db,
                projection_version=projection.projection_version,
            )
            yield {
                "event_type": "operation_completed",
                "projection_version": response.projection.projection_version,
                "payload": {
                    "operation_id": operation.id,
                    "state": response.state.model_dump(mode="json"),
                    "projection": response.projection.model_dump(mode="json"),
                    "active_surface": response.active_surface.model_dump(mode="json") if response.active_surface else None,
                    "messages": [message.model_dump(mode="json") for message in response.messages],
                    "replace_path": response.replace_path,
                },
            }
            yield {
                "event_type": "corpus_done",
                "projection_version": response.projection.projection_version,
                "payload": {"status": "committed"},
            }
            return
        proposal = CorpusProposal(
            operation_id=operation.id,
            label=operation.label,
            description=operation.description,
            args=decision.get("args") or {},
            execution_mode=operation.execution_mode,
            safety_class=operation.safety_class,
            input_schema=operation.input_schema,
            target_node=operation.target_node,
        )
        yield {
            "event_type": "proposal",
            "projection_version": projection.projection_version,
            "payload": proposal.model_dump(mode="json"),
        }

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
        if action_id in {AppActionIds.AUTH_SIGN_IN, AppActionIds.AUTH_REGISTER}:
            return user is None
        if action_id in {AppActionIds.HOME, AppActionIds.RECOVERY_HOME}:
            return True
        if user is None:
            return False
        if action_id in {AppActionIds.SAAS_AGENT_CREATE, AppActionIds.SAAS_AGENT_LIST, AppActionIds.SAAS_AGENT_OPEN}:
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
            ids.extend([AppActionIds.AGENT_HOME, AppActionIds.INSTRUCTIONS_OPEN, AppActionIds.CONNECTION_CONFIGURE, AppActionIds.KNOWLEDGE_OPEN, AppActionIds.MEMORY_OPEN, AppActionIds.LEARNING_OPEN, AppActionIds.QA_OPEN])
            if lens.connection_count > 0:
                ids.extend([AppActionIds.CATALOG_OPEN, AppActionIds.ENTITIES_OPEN, AppActionIds.ACTIONS_OPEN, AppActionIds.EXECUTION_OPEN])
        return [route_action_to_card(self._action_by_id[action_id]) for action_id in ids]

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
        projection: dict[str, Any],
        projection_version: int,
        fallback_message: str,
    ) -> AsyncIterator[dict[str, Any]]:
        streamed_text = ""
        try:
            async for delta in self._stream_corpus_message(
                api_key=api_key,
                user_input=user_input,
                projection=projection,
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

    def _message_text_chunks(self, text: str, *, target_size: int = 18) -> list[str]:
        if not text:
            return []
        return [text[index : index + target_size] for index in range(0, len(text), target_size)]

    async def _corpus_turn_plan(self, *, api_key: str, user_input: str, projection: dict[str, Any]) -> dict[str, Any]:
        from openai import AsyncOpenAI

        from backend.core.langsmith import wrap_openai_client

        client = wrap_openai_client(AsyncOpenAI(api_key=api_key))
        response = await client.chat.completions.create(
            model=settings.default_model,
            messages=[
                {"role": "system", "content": CORPUS_TURN_ROUTER_PROMPT},
                {"role": "user", "content": json.dumps({"user_input": user_input, "route_deck_projection": projection})},
            ],
            response_format={"type": "json_object"},
            **_openai_latency_options(),
        )
        content = response.choices[0].message.content or "{}"
        try:
            parsed = json.loads(content)
        except json.JSONDecodeError:
            return {"intent": "clarify", "message": "I could not read the model response.", "operation_id": None, "args": {}}
        if not isinstance(parsed, dict):
            return {"intent": "clarify", "message": "", "operation_id": None, "args": {}}
        parsed.setdefault("intent", "propose_operation" if parsed.get("operation_id") else "reply_now")
        parsed.setdefault("args", {})
        parsed.setdefault("surface_intent", {})
        return parsed

    async def _stream_corpus_message(self, *, api_key: str, user_input: str, projection: dict[str, Any]) -> AsyncIterator[str]:
        from openai import AsyncOpenAI

        from backend.core.langsmith import wrap_openai_client

        client = wrap_openai_client(AsyncOpenAI(api_key=api_key))
        stream = await client.chat.completions.create(
            model=settings.default_model,
            messages=[
                {"role": "system", "content": CORPUS_STREAM_PROMPT},
                {"role": "user", "content": json.dumps({"user_input": user_input, "route_deck_projection": projection})},
            ],
            stream=True,
            **_openai_latency_options(),
        )
        async for chunk in stream:
            content = chunk.choices[0].delta.content if chunk.choices else None
            if content:
                yield content

    def _operation_for_action(self, action: Any) -> RouteDeckOperation:
        return self._operation_policy.operation_for_action(action)

    def _projection_context(self, state: AppGraphState, user: User | None) -> str:
        return "lounge" if user is None and state.node == AppNodeIds.HOME else state.node

    def _presentation_key(self, state: AppGraphState, user: User | None) -> str:
        actor = str(user.id) if user else "anonymous"
        return f"{actor}:{state.node}"

    def _frame_surface(
        self,
        *,
        state: AppGraphState,
        lens: AppGraphContextLens,
        saas_agents: list[SaaSAgentRead],
        context: str,
        presentation_state: dict[str, Any],
    ) -> RouteDeckSurface:
        return self._surface_registry.frame_surface(
            state=state,
            lens=lens,
            saas_agents=saas_agents,
            context=context,
            presentation_state=presentation_state,
            node_by_id=self._node_by_id,
        )

    def _surface_variant(self, state: AppGraphState, presentation_state: dict[str, Any], surface_name: str, default: str) -> str:
        return self._surface_registry.surface_variant(state, presentation_state, surface_name, default, self._node_by_id)

    def _store_surface_intent(self, state: AppGraphState, user: User | None, surface_intent: Any) -> bool:
        key = self._presentation_key(state, user)
        current = self._presentation_state_by_key.setdefault(key, {})
        return self._surface_registry.store_surface_intent(
            state=state,
            surface_intent=surface_intent,
            node_by_id=self._node_by_id,
            presentation_state=current,
        )

    def _deterministic_open_message(self, operation: RouteDeckOperation) -> str:
        return self._surface_registry.deterministic_open_message(operation)

    def _deterministic_turn_plan(
        self,
        *,
        user_input: str,
        state: AppGraphState,
        projection: Any,
    ) -> dict[str, Any] | None:
        legal_operation_ids = {getattr(operation, "id", None) for operation in getattr(projection, "legal_operations", [])}
        if (
            state.active_saas_agent_id
            and AppActionIds.CONNECTION_CONFIGURE in legal_operation_ids
            and _looks_like_api_setup_request(user_input)
        ):
            return {
                "intent": "open_surface",
                "message": self._deterministic_open_message(
                    next(operation for operation in projection.legal_operations if operation.id == AppActionIds.CONNECTION_CONFIGURE)
                ),
                "operation_id": AppActionIds.CONNECTION_CONFIGURE,
                "args": {},
                "surface_intent": None,
                "confidence": 1.0,
                "preamble": None,
            }
        return None

    def _blocked_actions(self, state: AppGraphState, user: User | None, lens: AppGraphContextLens) -> list[dict[str, str]]:
        blocked: list[dict[str, str]] = []
        node = self._node_by_id.get(state.node) or self._node_by_id[AppNodeIds.HOME]
        for action_id in node.allowed_actions:
            reason = self._action_block_reason(action_id, state, user, lens)
            if reason:
                blocked.append({"id": action_id, "reason": reason})
        return blocked

    def _guard_explanations(self, state: AppGraphState, user: User | None, lens: AppGraphContextLens) -> list[dict[str, Any]]:
        explanations = []
        if user is None:
            explanations.append({"guard": "auth", "status": "missing", "message": "Authentication is required beyond Lounge and auth flows."})
        if not state.active_saas_agent_id and user is not None:
            explanations.append({"guard": "saas_agent_selection", "status": "missing", "message": "Choose a SaaS Agent before agent-specific routes become reachable."})
        if state.node == AppNodeIds.EXECUTION_PLANNING and lens.tool_count <= 0:
            explanations.append({"guard": "tool_readiness", "status": "missing", "message": "Connect and activate an API before execution planning is reachable."})
        if state.node == AppNodeIds.APPROVAL_REQUIRED and not state.pending_trace_id:
            explanations.append({"guard": "pending_trace", "status": "missing", "message": "Approval requires a pending execution trace."})
        return explanations

    def _action_block_reason(self, action_id: str, state: AppGraphState, user: User | None, lens: AppGraphContextLens) -> str | None:
        if action_id in {AppActionIds.AUTH_SIGN_IN, AppActionIds.AUTH_REGISTER, AppActionIds.HOME, AppActionIds.RECOVERY_HOME}:
            return None
        if user is None:
            return "Authentication required"
        if action_id in {AppActionIds.SAAS_AGENT_CREATE, AppActionIds.SAAS_AGENT_LIST, AppActionIds.SAAS_AGENT_OPEN}:
            return None
        if not state.active_saas_agent_id:
            return "SaaS Agent selection required"
        if action_id in {AppActionIds.CATALOG_OPEN, AppActionIds.ENTITIES_OPEN, AppActionIds.ACTIONS_OPEN, AppActionIds.EXECUTION_OPEN} and lens.connection_count <= 0:
            return "Connect and activate an API first"
        if action_id == AppActionIds.EXECUTION_PLAN and lens.tool_count <= 0:
            return "No generated tools are ready yet"
        if action_id in {AppActionIds.APPROVAL_APPROVE, AppActionIds.APPROVAL_REJECT} and not state.pending_trace_id:
            return "No pending approval exists"
        return None

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

    async def _handle_instructions_open(self, state, payload, user, db):
        state.node = AppNodeIds.INSTRUCTIONS
        return state, [], []

    async def _handle_instructions_save(self, state, payload, user, db):
        if user is None or not state.active_saas_agent_id:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="SaaS Agent selection required")
        member = await self._require_member(state.active_saas_agent_id, user, db)
        if member.role not in (SaaSAgentRole.owner, SaaSAgentRole.admin):
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="SaaS Agent admin role required")
        agent = await db.get(SaaSAgent, state.active_saas_agent_id)
        if agent is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="SaaS Agent not found")
        agent.system_prompt = str(payload.get("system_prompt") or "").strip() or None
        agent.instructions = str(payload.get("instructions") or "").strip() or None
        await db.commit()
        await db.refresh(agent)
        state.node = AppNodeIds.INSTRUCTIONS
        state.dirty_surfaces.pop("instructions", None)
        state.graph_context["instructions_saved"] = True
        return (
            state,
            [EntryGraphMessage(content="Saved instructions for this SaaS Agent.")],
            [
                {
                    "type": "instructions_saved",
                    "saas_agent_id": str(agent.id),
                    "system_prompt": agent.system_prompt,
                    "instructions": agent.instructions,
                }
            ],
        )

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

    async def _handle_learning_policy_candidate_open(self, state, payload, user, db):
        candidate_id = str(payload.get("candidate_id") or "").strip()
        if not candidate_id:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="candidate_id is required")
        state.node = AppNodeIds.LEARNING_POLICY_CANDIDATE
        state.route_params = {"candidate_id": candidate_id}
        state.active_surface_id = "learning.policy_candidate.review"
        return state, [], [{"type": "learning_policy_candidate_opened", "candidate_id": candidate_id}]

    async def _handle_learning_execution_trace_open(self, state, payload, user, db):
        trace_id = str(payload.get("trace_id") or "").strip()
        if not trace_id:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="trace_id is required")
        state.node = AppNodeIds.LEARNING_EXECUTION_TRACE
        state.route_params = {"trace_id": trace_id}
        state.active_surface_id = "learning.execution_trace.review"
        return state, [], [{"type": "learning_execution_trace_opened", "trace_id": trace_id}]

    async def _handle_learning_active_policy_open(self, state, payload, user, db):
        candidate_id = str(payload.get("candidate_id") or "").strip()
        if not candidate_id:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="candidate_id is required")
        state.node = AppNodeIds.LEARNING_ACTIVE_POLICY
        state.route_params = {"candidate_id": candidate_id}
        state.active_surface_id = "learning.active_policy.review"
        return state, [], [{"type": "learning_active_policy_opened", "candidate_id": candidate_id}]

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


corpus_graph_runtime = CorpusGraphRuntime()


def _looks_like_api_setup_request(user_input: str) -> bool:
    normalized = user_input.lower().replace("-", " ").replace("_", " ")
    tokens = {token.strip(".,!?;:()[]{}") for token in normalized.split()}
    api_tokens = {"api", "openapi", "schema", "connection", "credentials", "credential"}
    setup_tokens = {"connect", "setup", "set", "configure", "add", "integrate", "link", "onboard", "activate"}
    return bool(tokens & api_tokens) and bool(tokens & setup_tokens)


def _openai_latency_options() -> dict[str, Any]:
    effort = settings.openai_reasoning_effort.strip()
    return {"reasoning_effort": effort} if effort else {}
