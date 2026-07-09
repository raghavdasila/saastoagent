from __future__ import annotations

import json
import re
from collections.abc import Mapping
from typing import Any

from routedeck_core import RouteDeckProjection, RouteDeckSurface

from backend.core.schemas import CorpusGraphState
from backend.services.corpus.manifest import CorpusActionIds


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
