from __future__ import annotations

import enum
from dataclasses import dataclass, field
from typing import Any, Sequence


class ToolRouterDecisionType(str, enum.Enum):
    ROUTE = "route"
    SHOW_TOPK = "show_topk"
    ASK_PARAM = "ask_param"
    ASK_POLICY = "ask_policy"
    BLOCK_UNSAFE = "block_unsafe"


@dataclass(frozen=True)
class ToolRouterDecision:
    type: ToolRouterDecisionType
    selected: Any | None = None
    candidates: list[Any] = field(default_factory=list)
    inputs: dict[str, Any] = field(default_factory=dict)
    missing: list[str] = field(default_factory=list)
    reason: str = ""


class ToolRouterAdapter:
    """Backend-local decision adapter for generated OpenAPI tools.

    This is the production boundary for the integration-prep router work. It
    keeps route decisions independent from UI/RouteDeck and lets the existing
    execution trace machinery remain the executor of record.
    """

    WRITE_RISKS = {"write", "destructive", "financial"}
    UNSAFE_BULK_TERMS = {"all", "every", "truncate", "drop", "wipe", "purge"}

    def decide(
        self,
        *,
        message: str,
        candidates: Sequence[Any],
        inputs: dict[str, Any],
        missing: list[str],
    ) -> ToolRouterDecision:
        ranked = list(candidates)
        if not ranked:
            return ToolRouterDecision(type=ToolRouterDecisionType.SHOW_TOPK, candidates=[])

        top = ranked[0]
        if self._is_ambiguous(ranked):
            return ToolRouterDecision(
                type=ToolRouterDecisionType.SHOW_TOPK,
                candidates=ranked[:5],
                reason="Multiple generated tools matched with the same score.",
            )

        if missing:
            return ToolRouterDecision(
                type=ToolRouterDecisionType.ASK_PARAM,
                selected=top,
                candidates=ranked[:5],
                inputs=inputs,
                missing=missing,
                reason="The selected tool requires more inputs.",
            )

        risk = self._risk(top)
        if risk in self.WRITE_RISKS:
            if risk == "destructive" and self._looks_like_bulk_destructive(message):
                return ToolRouterDecision(
                    type=ToolRouterDecisionType.BLOCK_UNSAFE,
                    selected=top,
                    candidates=ranked[:5],
                    inputs=inputs,
                    reason="Bulk destructive requests are blocked in the sandbox slice.",
                )
            return ToolRouterDecision(
                type=ToolRouterDecisionType.ASK_POLICY,
                selected=top,
                candidates=ranked[:5],
                inputs=inputs,
                reason="Write or risky actions require confirmation.",
            )

        if bool(getattr(getattr(top, "tool", None), "requires_approval", False)):
            return ToolRouterDecision(
                type=ToolRouterDecisionType.ASK_POLICY,
                selected=top,
                candidates=ranked[:5],
                inputs=inputs,
                reason="The generated tool requires approval.",
            )

        return ToolRouterDecision(
            type=ToolRouterDecisionType.ROUTE,
            selected=top,
            candidates=ranked[:5],
            inputs=inputs,
            reason="A single safe generated tool matched.",
        )

    def _is_ambiguous(self, candidates: list[Any]) -> bool:
        if len(candidates) < 2:
            return False
        if int(getattr(candidates[0], "score", 0) or 0) != int(getattr(candidates[1], "score", 0) or 0):
            return False
        return self._required_count(candidates[0]) == self._required_count(candidates[1])

    def _risk(self, candidate: Any) -> str:
        risk = getattr(getattr(candidate, "tool", None), "risk_level", None)
        if hasattr(risk, "value"):
            return str(risk.value)
        return str(risk or "read")

    def _looks_like_bulk_destructive(self, message: str) -> bool:
        lowered = (message or "").lower()
        return any(term in lowered.split() for term in self.UNSAFE_BULK_TERMS)

    def _required_count(self, candidate: Any) -> int:
        tool = getattr(candidate, "tool", None)
        schema = (getattr(tool, "function_schema", None) or {}).get("parameters") or {}
        if isinstance(schema, dict):
            required = schema.get("required") or []
            if isinstance(required, list):
                return len(required)
        action = getattr(candidate, "action", None)
        parameters = getattr(action, "parameters", None) or []
        return sum(1 for parameter in parameters if isinstance(parameter, dict) and parameter.get("required"))
