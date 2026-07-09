from __future__ import annotations

import asyncio
import json
import uuid
from collections.abc import Mapping
from typing import Any, AsyncIterator

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from backend.core.config import settings
from backend.core.models import User
from backend.core.schemas import CorpusContextLens, CorpusGraphRequest, CorpusGraphState, CorpusActionResponse, EntryGraphMessage
from backend.services.corpus.corpus_context import CorpusContextQueries
from backend.services.corpus.corpus_handlers import CorpusActionContext, build_corpus_action_dispatcher
from backend.services.corpus.corpus_navgraph import CorpusNavgraphDiagnostics
from backend.services.corpus.corpus_turn_planning import (
    build_corpus_turn_planning_context,
    normalize_corpus_turn_plan,
    resolve_explicit_navigation_turn,
)
from backend.services.corpus.manifest import ACTION_TARGETS, CAPABILITY_RAIL_ITEMS, CorpusActionIds, CorpusNodeIds, route_action_to_card
from routedeck_core import (
    RouteDeckActionResult,
    RouteDeckDispatchInput,
    RouteDeckDispatchResult,
    RouteDeckIntrospection,
    RouteDeckOperation,
    RouteDeckProjection,
    RouteDeckRuntimeBase,
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


class CorpusRouteDeckRuntime(RouteDeckRuntimeBase[CorpusGraphState, EntryGraphMessage]):
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
    ) -> RouteDeckActionResult[CorpusGraphState, EntryGraphMessage]:
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
            messages=[EntryGraphMessage.model_validate(message) for message in result.messages],
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
