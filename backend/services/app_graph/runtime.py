from __future__ import annotations

import asyncio
import json
import uuid
from typing import Any, AsyncIterator, Mapping
from urllib.parse import urlencode

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from backend.core.config import settings
from backend.core.models import User
from backend.core.schemas import (
    AppGraphContextLens,
    AppGraphNavigationLocation,
    AppGraphRequest,
    AppGraphResponse,
    AppGraphState,
    CorpusActionResponse,
    CorpusDiagnosticsSnapshot,
    CorpusStateResponse,
    EntryGraphManifest,
    EntryGraphMessage,
    EntryRouteDeckRuntimeSnapshot,
    EntryUIArtifact,
    SaaSAgentRead,
)
from backend.services.app_graph.corpus_context import CorpusContextQueries
from backend.services.app_graph.corpus_handlers import CorpusActionContext, build_corpus_action_dispatcher
from backend.services.app_graph.corpus_operation_requests import CorpusOperationRequests
from backend.services.app_graph.manifest import (
    ACTION_SPECS,
    ACTION_TARGETS,
    APP_GRAPH_VERSION,
    AppActionIds,
    AppNodeIds,
    build_app_graph_manifest,
    route_action_to_card,
)
from backend.services.app_graph.corpus_routedeck_navigation import CorpusRouteDeckNavigation
from backend.services.app_graph.corpus_operations import CorpusOperationPolicy
from backend.services.app_graph.corpus_routedeck_state import CorpusRouteDeckStateProjector
from backend.services.app_graph.corpus_surfaces import CorpusSurfaceRegistry
from backend.services.app_graph.corpus_turn_planning import (
    build_corpus_turn_planning_context,
    normalize_corpus_turn_plan,
    resolve_explicit_navigation_turn,
)
from routedeck_core import RouteDeckActionDispatcher, RouteDeckOperation, RouteDeckSurface, build_runtime_snapshot


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

class CorpusGraphRuntime:
    def __init__(self) -> None:
        self.manifest = build_app_graph_manifest()
        self._action_by_id = {action.id: action for action in ACTION_SPECS}
        self._node_by_id = {node.id: node for node in self.manifest.nodes}
        self._presentation_state_by_key: dict[str, dict[str, Any]] = {}
        self._operation_policy = CorpusOperationPolicy()
        self._surface_registry = CorpusSurfaceRegistry()
        self._navigation = CorpusRouteDeckNavigation(
            surface_registry=self._surface_registry,
            node_by_id=self._node_by_id,
        )
        self._operation_requests = CorpusOperationRequests(
            navigation=self._navigation,
            surface_registry=self._surface_registry,
        )
        self._context_queries = CorpusContextQueries(node_by_id=self._node_by_id)
        self._action_dispatcher: RouteDeckActionDispatcher[AppGraphState, EntryGraphMessage, CorpusActionContext] = build_corpus_action_dispatcher(
            navigation=self._navigation,
            action_targets=ACTION_TARGETS,
        )
        self._route_deck_projector = CorpusRouteDeckStateProjector(
            manifest=self.manifest,
            node_by_id=self._node_by_id,
            operation_policy=self._operation_policy,
            surface_registry=self._surface_registry,
        )

    def request_from_location(
        self,
        *,
        node_id: str | None = None,
        saas_agent_id: uuid.UUID | None = None,
        surface_id: str | None = None,
        user_input: str | None = None,
    ) -> AppGraphRequest:
        if node_id is None and saas_agent_id is None and surface_id is None and user_input is None:
            return AppGraphRequest()
        state = AppGraphState(
            node=node_id or AppNodeIds.HOME,
            active_saas_agent_id=saas_agent_id,
            active_surface_id=surface_id,
        )
        return AppGraphRequest(
            state=state,
            node_id=node_id or state.node,
            saas_agent_id=saas_agent_id,
            user_input=user_input,
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
        validated_args = self._operation_requests.validated_payload(
            state=turn_state,
            operation=operation,
            args=args,
            projection=projection,
        )
        if (
            operation.execution_mode != "auto"
            and turn_state.pending_operation_id != operation.id
            and not self._surface_registry.is_surface_hosted_operation(node_id=turn_state.node, operation_id=operation.id)
        ):
            return await self._stage_review_operation(
                state=turn_state,
                operation=operation,
                args={**operation.payload, **validated_args},
                user=user,
                db=db,
                projection_version=projection.projection_version + 1,
            )
        response = await self.action(
            request=AppGraphRequest(
                state=turn_state,
                node_id=turn_state.node,
                saas_agent_id=turn_state.active_saas_agent_id,
                selected_action_id=operation_id,
                action_payload={**operation.payload, **validated_args},
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
        active_surface = self._active_surface_from_projection(next_projection)
        return CorpusActionResponse(
            state=response.state,
            projection=next_projection,
            active_surface=active_surface,
            messages=response.messages,
            replace_path=response.replace_path,
        )

    async def _stage_review_operation(
        self,
        *,
        state: AppGraphState,
        operation: RouteDeckOperation,
        args: dict[str, Any],
        user: User | None,
        db: AsyncSession,
        projection_version: int,
    ) -> CorpusActionResponse:
        review_state = self._operation_requests.review_state_for_operation(
            state=state,
            operation=operation,
            args=args,
        )
        review_projection = await self.route_deck_projection(
            request=AppGraphRequest(
                state=review_state,
                node_id=review_state.node,
                saas_agent_id=review_state.active_saas_agent_id,
            ),
            user=user,
            db=db,
            projection_version=projection_version,
        )
        active_surface = self._active_surface_from_projection(review_projection)
        return CorpusActionResponse(
            state=review_state,
            projection=review_projection,
            active_surface=active_surface,
            messages=[],
            replace_path=self._path_for_state(review_state),
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
        streamed_before_decision = False
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
        surface_navigation_id = self._surface_navigation_id(surface_intent)
        surface_variant_intent = self._surface_variant_intent(surface_intent)
        surface_intent_changed = self._store_surface_intent(turn_state, user, surface_variant_intent)
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
        if surface_navigation_id:
            response = await self.corpus_action(
                request=normalized_request,
                operation_id=AppActionIds.ROUTE_SWITCH_SURFACE,
                args={"surface_id": surface_navigation_id},
                user=user,
                db=db,
                projection_version=projection.projection_version,
            )
            yield {
                "event_type": "operation_completed",
                "projection_version": response.projection.projection_version,
                "payload": {
                    "operation_id": AppActionIds.ROUTE_SWITCH_SURFACE,
                    "state": response.state.model_dump(mode="json"),
                    "projection": response.projection.model_dump(mode="json"),
                    "active_surface": response.active_surface.model_dump(mode="json") if response.active_surface else None,
                    "messages": [message.model_dump(mode="json") for message in response.messages],
                    "replace_path": response.replace_path,
                },
            }
            async for event in self._stream_operation_reply_events(
                api_key=api_key,
                user_input=request.user_input or "",
                decision_message=str(decision.get("message") or ""),
                response=response,
                operation_id=AppActionIds.ROUTE_SWITCH_SURFACE,
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
            if streamed_before_decision:
                pass
            elif surface_intent_changed:
                async for event in self._message_delta_events(projection_version=projection.projection_version, text=message):
                    yield event
            else:
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
        done_status = "committed" if operation.execution_mode == "auto" or turn_state.pending_operation_id == operation.id else "review"
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

    async def action(self, *, request: AppGraphRequest, user: User | None, db: AsyncSession) -> AppGraphResponse:
        state = await self._initial_state(request, user, db)
        previous_location = self._current_location(state)
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
        result = await self._action_dispatcher.dispatch(
            action_id,
            state=state,
            payload=payload,
            context=CorpusActionContext(user=user, db=db, queries=self._context_queries),
        )
        state = result.state
        messages = result.messages
        evidence = result.evidence
        if not action_id.startswith("route."):
            self._clear_pending_operation(state)
            if state.node != previous_location.node_id and state.active_surface_id == previous_location.surface_id:
                state.active_surface_id = None
            self._push_navigation(state, previous_location)
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

    def _resolved_surface_id(self, state: AppGraphState) -> str | None:
        return self._navigation.resolved_surface_id(state)

    def _history_params_for_state(self, state: AppGraphState) -> dict[str, Any]:
        return self._navigation.history_params_for_state(state)

    def _current_location(self, state: AppGraphState) -> AppGraphNavigationLocation:
        return self._navigation.current_location(state)

    def _app_location_from_route_deck(self, location) -> AppGraphNavigationLocation:
        return self._navigation.location_from_route_deck(location)

    def _app_locations_from_route_deck(self, locations) -> list[AppGraphNavigationLocation]:
        return self._navigation.locations_from_route_deck(locations)

    def _clear_pending_operation(self, state: AppGraphState) -> None:
        state.pending_operation_id = None
        state.pending_operation_args = {}

    def _location_from_payload(
        self,
        state: AppGraphState,
        payload: dict[str, Any],
        *,
        preserve_current_params: bool = False,
    ) -> AppGraphNavigationLocation:
        return self._navigation.location_from_payload(
            state,
            payload,
            preserve_current_params=preserve_current_params,
        )

    def _apply_location(self, state: AppGraphState, location: AppGraphNavigationLocation) -> None:
        self._navigation.apply_location(state, location)

    def _push_navigation(self, state: AppGraphState, previous: AppGraphNavigationLocation) -> None:
        self._navigation.push_navigation(state, previous)

    def _cancel_target_location(self, state: AppGraphState) -> AppGraphNavigationLocation | None:
        return self._navigation.cancel_target_location(state)

    def _route_actions(self, state: AppGraphState) -> list[Any]:
        route_actions: list[Any] = [
            self._action_by_id[AppActionIds.ROUTE_OPEN_NODE],
            self._action_by_id[AppActionIds.ROUTE_SWITCH_SURFACE],
        ]
        if state.navigation_back_stack:
            route_actions.append(self._action_by_id[AppActionIds.ROUTE_BACK])
        if state.navigation_forward_stack:
            route_actions.append(self._action_by_id[AppActionIds.ROUTE_FORWARD])
        if self._cancel_target_location(state):
            route_actions.append(self._action_by_id[AppActionIds.ROUTE_CANCEL])
        return route_actions

    def _active_surface_from_projection(self, projection) -> RouteDeckSurface | None:
        return self._navigation.active_surface_from_projection(projection)

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
        actions.extend(route_action_to_card(action) for action in self._route_actions(state))
        return actions

    def _is_action_eligible(self, action_id: str, state: AppGraphState, user: User | None, lens: AppGraphContextLens) -> bool:
        if action_id in {
            AppActionIds.ROUTE_BACK,
            AppActionIds.ROUTE_FORWARD,
            AppActionIds.ROUTE_CANCEL,
            AppActionIds.ROUTE_OPEN_NODE,
            AppActionIds.ROUTE_SWITCH_SURFACE,
        }:
            return True
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
        state.active_surface_id = self._resolved_surface_id(state)
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

    def _operation_for_action(self, action: Any) -> RouteDeckOperation:
        return self._operation_policy.operation_for_action(action)

    def _projection_context(self, state: AppGraphState, user: User | None) -> str:
        return "lounge" if user is None and state.node == AppNodeIds.HOME else state.node

    def _presentation_key(self, state: AppGraphState, user: User | None) -> str:
        actor = str(user.id) if user else "anonymous"
        agent = str(state.active_saas_agent_id) if state.active_saas_agent_id else "none"
        return f"{actor}:{agent}:{state.node}"

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

    def _surface_navigation_id(self, surface_intent: Any) -> str | None:
        if not isinstance(surface_intent, dict):
            return None
        surface_id = surface_intent.get("surface_id")
        return surface_id if isinstance(surface_id, str) and surface_id else None

    def _surface_variant_intent(self, surface_intent: Any) -> dict[str, str]:
        if not isinstance(surface_intent, dict):
            return {}
        return {
            key: value
            for key, value in surface_intent.items()
            if key != "surface_id" and isinstance(key, str) and isinstance(value, str)
        }

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
        if action_id in {
            AppActionIds.AUTH_SIGN_IN,
            AppActionIds.AUTH_REGISTER,
            AppActionIds.HOME,
            AppActionIds.RECOVERY_HOME,
            AppActionIds.ROUTE_BACK,
            AppActionIds.ROUTE_FORWARD,
            AppActionIds.ROUTE_CANCEL,
            AppActionIds.ROUTE_OPEN_NODE,
            AppActionIds.ROUTE_SWITCH_SURFACE,
        }:
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
            path = (
                f"/app/agents/{state.active_saas_agent_id}"
                if state.node == AppNodeIds.AGENT_HOME
                else f"/app/agents/{state.active_saas_agent_id}/{state.node}"
            )
        else:
            path = "/app/home" if state.node == AppNodeIds.HOME else f"/app/{state.node}"
        surface_id = self._resolved_surface_id(state)
        if not surface_id:
            return path
        return f"{path}?{urlencode({'surface_id': surface_id})}"

    async def _context_lens(self, state: AppGraphState, user: User | None, db: AsyncSession) -> AppGraphContextLens:
        return await self._context_queries.context_lens(state, user, db)

    async def _list_saas_agents(self, user: User | None, db: AsyncSession) -> list[SaaSAgentRead]:
        return await self._context_queries.list_saas_agents(user, db)

    async def _require_member(self, saas_agent_id: uuid.UUID, user: User, db: AsyncSession):
        return await self._context_queries.require_member(saas_agent_id, user, db)

    def _apply_navigation_transition(self, state: AppGraphState, transition) -> None:
        self._navigation.apply_transition(state, transition)


corpus_graph_runtime = CorpusGraphRuntime()


def _openai_latency_options() -> dict[str, Any]:
    effort = settings.openai_reasoning_effort.strip()
    return {"reasoning_effort": effort} if effort else {}
