from __future__ import annotations

import json
from typing import Any

import httpx

from backend.core.config import settings
from backend.core.schemas import AppGraphRouterDecision, AppGraphState, EntryActionCard
from backend.services.route_deck.models import RouteDeckManifest


ROUTER_SYSTEM_PROMPT = """You route a SaaS agent conversation to one eligible application action.
Return only JSON matching this shape:
{"intent":"action|clarify|no_match","action_id":null|string,"node_id":null|string,"slots":{},"confidence":0.0,"clarification":null|string}
Use only provided action ids and node ids. If required information is missing, ask one concise clarification.
Do not invent actions, nodes, credentials, or connection details."""


class AppGraphTurnRouter:
    """App-owned free-text router.

    RouteDeck remains deterministic. This adapter may ask an app-configured
    provider for a suggestion, but graph eligibility still decides execution.
    """

    def __init__(
        self,
        *,
        provider: str | None = None,
        model: str | None = None,
        confidence_threshold: float | None = None,
    ) -> None:
        self.provider = (provider or settings.app_graph_router_provider or "disabled").strip().lower()
        self.model = model or settings.app_graph_router_model or settings.default_model
        self.confidence_threshold = (
            confidence_threshold
            if confidence_threshold is not None
            else settings.app_graph_router_confidence_threshold
        )

    async def route(
        self,
        *,
        user_input: str | None,
        state: AppGraphState,
        actions: list[EntryActionCard],
        manifest: RouteDeckManifest,
    ) -> AppGraphRouterDecision:
        text = (user_input or "").strip()
        if not text:
            return self._clarify(actions, "Tell me what you want this SaaS Agent to do next.")
        if not actions:
            return AppGraphRouterDecision(
                intent="clarify",
                confidence=1.0,
                clarification="I need one available next step before I can continue.",
                provider=self.provider,
                model=self.model,
            )
        if self.provider in {"", "disabled", "none", "off"}:
            return self._clarify(actions)
        if self.provider == "openai":
            return await self._route_openai(text=text, state=state, actions=actions, manifest=manifest)
        if self.provider == "ollama":
            return await self._route_ollama(text=text, state=state, actions=actions, manifest=manifest)
        return self._clarify(actions, "I do not have a configured language router for that yet.")

    def action_needs_clarification(self, decision: AppGraphRouterDecision, actions: list[EntryActionCard]) -> str | None:
        if decision.intent != "action":
            return decision.clarification
        action = next((candidate for candidate in actions if candidate.id == decision.action_id), None)
        if not action:
            return "I cannot take that step from here. Choose one of the visible next steps."
        missing = [
            field.label
            for field in action.fields
            if field.required
            and field.key not in decision.slots
            and field.key not in (action.payload or {})
            and field.default in (None, "")
        ]
        if missing:
            return f"I can do that. I still need: {', '.join(missing)}."
        if decision.confidence < self.confidence_threshold:
            return decision.clarification or "I can help, but I need a little more detail before taking that step."
        return None

    def _clarify(self, actions: list[EntryActionCard], message: str | None = None) -> AppGraphRouterDecision:
        return AppGraphRouterDecision(
            intent="clarify",
            confidence=1.0,
            clarification=message or "I'm SaaStoAgent. I help shape a SaaS Agent, connect it to an API, activate its catalog, and operate it through approved actions.",
            provider=self.provider,
            model=self.model,
        )

    async def _route_openai(
        self,
        *,
        text: str,
        state: AppGraphState,
        actions: list[EntryActionCard],
        manifest: RouteDeckManifest,
    ) -> AppGraphRouterDecision:
        if not settings.openai_api_key:
            return self._clarify(actions, "The language router is not configured yet.")
        try:
            from openai import AsyncOpenAI

            from backend.core.langsmith import wrap_openai_client

            client = wrap_openai_client(AsyncOpenAI(api_key=settings.openai_api_key))
            response = await client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": ROUTER_SYSTEM_PROMPT},
                    {"role": "user", "content": json.dumps(self._router_payload(text, state, actions, manifest))},
                ],
                response_format={"type": "json_object"},
                temperature=0,
            )
            content = response.choices[0].message.content or "{}"
            return self._coerce_decision(content, actions, provider="openai")
        except Exception:
            return self._clarify(actions, "I could not use the language router just now.")

    async def _route_ollama(
        self,
        *,
        text: str,
        state: AppGraphState,
        actions: list[EntryActionCard],
        manifest: RouteDeckManifest,
    ) -> AppGraphRouterDecision:
        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                response = await client.post(
                    f"{settings.app_graph_router_ollama_url.rstrip('/')}/api/chat",
                    json={
                        "model": self.model,
                        "stream": False,
                        "format": "json",
                        "messages": [
                            {"role": "system", "content": ROUTER_SYSTEM_PROMPT},
                            {"role": "user", "content": json.dumps(self._router_payload(text, state, actions, manifest))},
                        ],
                    },
                )
            response.raise_for_status()
            content = (response.json().get("message") or {}).get("content") or "{}"
            return self._coerce_decision(content, actions, provider="ollama")
        except Exception:
            return self._clarify(actions, "I could not use the local language router just now.")

    def _router_payload(
        self,
        text: str,
        state: AppGraphState,
        actions: list[EntryActionCard],
        manifest: RouteDeckManifest,
    ) -> dict[str, Any]:
        action_payloads = [
            {
                "id": action.id,
                "label": action.label,
                "description": action.description,
                "required_fields": [field.key for field in action.fields if field.required],
            }
            for action in actions
        ]
        return {
            "user_input": text,
            "current_node": state.node,
            "active_saas_agent_id": str(state.active_saas_agent_id) if state.active_saas_agent_id else None,
            "eligible_actions": action_payloads,
            "known_nodes": [node.id for node in manifest.nodes],
        }

    def _coerce_decision(
        self,
        content: str,
        actions: list[EntryActionCard],
        *,
        provider: str,
    ) -> AppGraphRouterDecision:
        try:
            raw = json.loads(content)
        except json.JSONDecodeError:
            return self._clarify(actions)
        decision = AppGraphRouterDecision.model_validate(
            {
                **raw,
                "provider": provider,
                "model": self.model,
            }
        )
        valid_ids = {action.id for action in actions}
        if decision.action_id and decision.action_id not in valid_ids:
            return self._clarify(actions, "That step is not available from here.")
        if decision.intent == "action" and not decision.action_id:
            return self._clarify(actions)
        return decision
