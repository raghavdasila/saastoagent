from __future__ import annotations

import re
from copy import deepcopy
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from backend.core.models import AgentSession
from backend.services.agent.state_variables import (
    remember_resource_id_variable,
    put_variable,
    resolve_input_from_variables,
)

FRAME_METADATA_KEY = "execution_frame_v1"

_BUY_TERMS = {
    "add",
    "buy",
    "cart",
    "checkout",
    "order",
    "purchase",
    "qty",
    "quantity",
}
_WORKFLOW_TERMS = {
    "checkout",
    "complete",
    "continue",
    "delivery",
    "finish",
    "order",
    "pay",
    "payment",
    "place",
    "ship",
    "shipping",
    "submit",
}
_ID_KEYS = ("id", "product_id", "item_id", "entity_id")


def load_execution_frame(session: AgentSession | None) -> dict[str, Any] | None:
    if session is None:
        return None
    frame = (session.metadata_ or {}).get(FRAME_METADATA_KEY)
    return deepcopy(frame) if isinstance(frame, dict) else None


async def save_execution_frame(session: AgentSession | None, frame: dict[str, Any] | None, db: AsyncSession) -> None:
    if session is None:
        return
    metadata = dict(session.metadata_ or {})
    if frame is None:
        metadata.pop(FRAME_METADATA_KEY, None)
    else:
        metadata[FRAME_METADATA_KEY] = frame
    session.metadata_ = metadata
    await db.commit()


def capture_result_frame(
    *,
    message: str,
    tool: Any,
    action: Any,
    result: dict[str, Any],
) -> dict[str, Any] | None:
    if result.get("error"):
        return None
    method = str(getattr(action, "method", "") or "").upper()
    if method not in {"GET", "HEAD", "OPTIONS"}:
        return None

    entities = _entities_from_body(result.get("body"))
    if not entities:
        return None
    return {
        "kind": "result_context",
        "source": {
            "tool_name": getattr(tool, "name", None),
            "action_name": getattr(action, "name", None),
            "method": getattr(action, "method", None),
            "path": getattr(action, "path", None),
        },
        "last_user_message": message,
        "entities": entities[:10],
    }


def preserve_selected_entity(
    frame: dict[str, Any],
    selected_entity: dict[str, Any],
    *,
    message: str | None = None,
) -> dict[str, Any]:
    updated = deepcopy(frame)
    updated["selected_entity"] = deepcopy(selected_entity)
    if message:
        _remember_selected_variant(updated, message, selected_entity)
    return updated


def promote_active_resource(
    frame: dict[str, Any] | None,
    *,
    collection_path: str,
    resource_id: str,
    source_action_path: str,
) -> dict[str, Any]:
    updated = remember_resource_id_variable(
        frame,
        collection_path=collection_path,
        resource_id=resource_id,
        origin={"source_action_path": source_action_path},
    )
    updated["active_resource"] = {
        "collection_path": collection_path,
        "id": resource_id,
        "source_action_path": source_action_path,
        "reason": "internal_dependency_used_successfully",
    }
    return updated


def active_resource_context(frame: dict[str, Any] | None) -> dict[str, Any] | None:
    if not isinstance(frame, dict):
        return None
    resource = frame.get("active_resource")
    if not isinstance(resource, dict):
        return None
    collection_path = resource.get("collection_path")
    resource_id = resource.get("id")
    if not collection_path or not resource_id:
        return None
    return {
        "collection_path": str(collection_path),
        "id": str(resource_id),
        "source_action_path": str(resource.get("source_action_path") or ""),
        "reason": str(resource.get("reason") or ""),
    }


def operation_frame_from_candidate(
    *,
    base_frame: dict[str, Any] | None,
    selected_entity: dict[str, Any],
    tool: Any,
    action: Any,
    inputs: dict[str, Any],
    missing: list[str],
) -> dict[str, Any]:
    return {
        "kind": "operation_context",
        "source": {
            "tool_name": getattr(tool, "name", None),
            "action_name": getattr(action, "name", None),
            "method": getattr(action, "method", None),
            "path": getattr(action, "path", None),
        },
        "selected_entity": selected_entity,
        "entities": list((base_frame or {}).get("entities") or []),
        "inputs": inputs,
        "missing": missing,
    }


def find_entity_reference(message: str, frame: dict[str, Any] | None) -> dict[str, Any] | None:
    if not frame:
        return None
    workflow_continuation = active_resource_context(frame) is not None and _looks_like_workflow_continuation(message)

    entities = [entity for entity in frame.get("entities") or [] if isinstance(entity, dict)]
    normalized_message = _normalize(message)
    compact_message = _compact(normalized_message)
    for entity in entities:
        if _entity_matches_message(entity, normalized_message, compact_message):
            return entity

    if workflow_continuation:
        return None

    selected = frame.get("selected_entity")
    if isinstance(selected, dict):
        if _entity_matches_message(selected, normalized_message, compact_message):
            return selected
        if _looks_like_continuation(message):
            return selected
    if len(entities) == 1 and _looks_like_continuation(message):
        return entities[0]
    return None


def augment_message_with_frame_context(
    message: str,
    entity: dict[str, Any],
    frame: dict[str, Any] | None = None,
) -> str:
    active_resource = active_resource_context(frame)
    if active_resource is not None and _looks_like_workflow_continuation(message):
        parts = [
            message,
            f"Active resource collection {active_resource['collection_path']}",
            "Active resource id available internally",
        ]
        source_action_path = active_resource.get("source_action_path")
        if source_action_path:
            parts.append(f"Last workflow action {source_action_path}")
        return " ".join(parts)

    parts = [message]
    label = entity.get("label")
    entity_id = entity.get("id")
    entity_type = entity.get("entity_type")
    if label:
        parts.append(str(label))
    if entity_id:
        parts.append(f"id {entity_id}")
    if entity_type:
        parts.append(str(entity_type))
    source = (frame or {}).get("source")
    if isinstance(source, dict):
        for key in ("tool_name", "action_name", "method", "path"):
            value = source.get(key)
            if value:
                parts.append(str(value))
    return " ".join(parts)


def build_inputs_from_frame(
    *,
    message: str,
    action: Any,
    tool: Any,
    frame: dict[str, Any],
    base_inputs: dict[str, Any] | None = None,
) -> tuple[dict[str, Any], list[str]]:
    entity = find_entity_reference(message, frame)
    inputs = dict(base_inputs or {})
    schema = (getattr(tool, "function_schema", None) or {}).get("parameters") or {}
    props = schema.get("properties") if isinstance(schema, dict) else {}
    required = list(schema.get("required") or []) if isinstance(schema, dict) else []
    active_resource = active_resource_context(frame)
    for name in props or {}:
        if name in inputs:
            continue
        value = resolve_input_from_variables(frame, str(name), action=action)
        if value is not None:
            inputs[str(name)] = value

    for param in getattr(action, "parameters", None) or []:
        if not isinstance(param, dict) or not param.get("name"):
            continue
        name = str(param["name"])
        if name in inputs:
            continue
        value = resolve_input_from_variables(frame, name, action=action)
        if value is not None:
            inputs[name] = value

    if active_resource is not None:
        for name in props or {}:
            if name in inputs:
                continue
            value = resolve_input_from_variables(frame, str(name), action=action)
            if value is None:
                value = _value_from_active_resource_for_input(str(name), action, active_resource)
            if value is not None:
                inputs[str(name)] = value

        for param in getattr(action, "parameters", None) or []:
            if not isinstance(param, dict) or not param.get("name"):
                continue
            name = str(param["name"])
            if name in inputs:
                continue
            value = resolve_input_from_variables(frame, name, action=action)
            if value is None:
                value = _value_from_active_resource_for_input(name, action, active_resource)
            if value is not None:
                inputs[name] = value

    if entity is not None:
        for name in props or {}:
            if name in inputs:
                continue
            value = _value_from_entity_for_input(str(name), message, entity, action)
            if value is not None:
                inputs[str(name)] = value

        for param in getattr(action, "parameters", None) or []:
            if not isinstance(param, dict) or not param.get("name"):
                continue
            name = str(param["name"])
            if name in inputs:
                continue
            value = _value_from_entity_for_input(name, message, entity, action)
            if value is not None:
                inputs[name] = value

    missing = [str(name) for name in required if str(name) not in inputs]
    return inputs, missing


def _entities_from_body(body: Any) -> list[dict[str, Any]]:
    if isinstance(body, dict):
        for key, value in body.items():
            if isinstance(value, list):
                entities = _entities_from_list(value, str(key))
                if entities:
                    return entities
        return _entities_from_list([body], "result")
    if isinstance(body, list):
        return _entities_from_list(body, "items")
    return []


def _entities_from_list(items: list[Any], entity_type: str) -> list[dict[str, Any]]:
    entities: list[dict[str, Any]] = []
    for item in items:
        if not isinstance(item, dict):
            continue
        entity_id = _first_value(item, ["id", f"{_singular(entity_type)}_id"])
        label = _first_value(item, ["title", "name", "label", "display_name", "handle"])
        if not entity_id and not label:
            continue
        aliases = _aliases_for_item(item, label, entity_id)
        entities.append(
            {
                "entity_type": entity_type,
                "id": str(entity_id) if entity_id is not None else None,
                "label": str(label) if label is not None else str(entity_id),
                "aliases": aliases,
                "raw": _json_safe(item),
            }
        )
    return entities


def _aliases_for_item(item: dict[str, Any], label: Any, entity_id: Any) -> list[str]:
    aliases: set[str] = set()
    for value in (label, entity_id, item.get("handle"), item.get("sku")):
        if value:
            aliases.add(_normalize(str(value)))
    for key in ("title", "name", "label", "display_name"):
        value = item.get(key)
        if value:
            aliases.add(_normalize(str(value)))
    return sorted(alias for alias in aliases if alias)


def _entity_matches_message(entity: dict[str, Any], normalized_message: str, compact_message: str) -> bool:
    aliases = [str(value) for value in entity.get("aliases") or [] if value]
    message_tokens = set(normalized_message.split())
    label = entity.get("label")
    entity_id = entity.get("id")
    if label:
        aliases.append(str(label))
    if entity_id:
        aliases.append(str(entity_id))
    for alias in aliases:
        normalized_alias = _normalize(alias)
        if not normalized_alias:
            continue
        compact_alias = _compact(normalized_alias)
        if normalized_alias in normalized_message or compact_alias in message_tokens:
            return True
    return False


def _first_value(item: dict[str, Any], keys: list[str]) -> Any:
    for key in keys:
        value = item.get(key)
        if value not in (None, ""):
            return value
    for key, value in item.items():
        if key.endswith("_id") and value not in (None, ""):
            return value
    return None


def _value_from_entity_for_input(name: str, message: str, entity: dict[str, Any], action: Any) -> Any:
    lowered = name.lower()
    raw = entity.get("raw") if isinstance(entity.get("raw"), dict) else {}

    if lowered in {"product_id", "item_id", "entity_id"} or lowered == f"{_singular(str(entity.get('entity_type') or 'entity'))}_id":
        return entity.get("id")
    if lowered == "id" and _action_path_targets_entity(action, entity):
        return entity.get("id")
    if lowered.endswith("_id") and lowered.split("_id", 1)[0] in {"product", "item", "entity"}:
        return entity.get("id")
    entity_type = str(entity.get("entity_type") or "")
    if lowered in {"option_id", "shipping_option_id"} and "shipping" in entity_type:
        return entity.get("id")
    if lowered == "provider_id" and "provider" in entity_type:
        return entity.get("id")
    if lowered in {"variant_id", "sku_id"}:
        return _resolve_variant_id(message, raw)
    if lowered in {"quantity", "qty"} and _looks_like_purchase(message):
        return _extract_quantity(message) or 1
    if lowered in {"size", "option_size"}:
        return _extract_size(message)
    return None


def _remember_selected_variant(frame: dict[str, Any], message: str, entity: dict[str, Any]) -> None:
    raw = entity.get("raw") if isinstance(entity.get("raw"), dict) else {}
    variant_id = _resolve_variant_id(message, raw)
    if not variant_id:
        return
    put_variable(
        frame,
        name="selected.variant_id",
        value=variant_id,
        visibility="private",
        value_type="string",
        tags=["selected_entity", "variant_id"],
        aliases=["variant_id", "sku_id"],
        resource={
            "collection_path": f"/{str(entity.get('entity_type') or 'entities')}",
            "resource_id": str(entity.get("id") or ""),
        },
        origin={"field_path": "selected_entity.raw.variants", "message": message},
    )


def _value_from_active_resource_for_input(name: str, action: Any, active_resource: dict[str, Any]) -> Any:
    resource_id = active_resource.get("id")
    if not resource_id:
        return None
    lowered = name.lower()
    collection_path = str(active_resource.get("collection_path") or "")
    resource_name = _resource_name_from_collection_path(collection_path)
    if lowered == "id" and _action_path_targets_collection(action, collection_path):
        return resource_id
    if resource_name and lowered == f"{resource_name}_id":
        return resource_id
    return None


def _resource_name_from_collection_path(collection_path: str) -> str:
    segments = [segment for segment in str(collection_path or "").split("/") if segment]
    if not segments:
        return ""
    return _singular(segments[-1].replace("-", "_"))


def _action_path_targets_collection(action: Any, collection_path: str) -> bool:
    path = str(getattr(action, "path", "") or "")
    if not path or not collection_path:
        return False
    return path == collection_path or path.startswith(collection_path.rstrip("/") + "/")


def _resolve_variant_id(message: str, raw: dict[str, Any]) -> str | None:
    variants = raw.get("variants")
    if not isinstance(variants, list):
        return None
    if len(variants) == 1 and isinstance(variants[0], dict):
        return str(variants[0].get("id")) if variants[0].get("id") else None
    message_tokens = set(_tokens(message))
    requested_size = _extract_size(message)
    if requested_size:
        for variant in variants:
            if not isinstance(variant, dict) or not variant.get("id"):
                continue
            if requested_size in _variant_specific_tokens(variant):
                return str(variant["id"])

    product_tokens = set()
    for key in ("title", "name", "handle", "sku"):
        if raw.get(key):
            product_tokens.update(_tokens(str(raw[key])))
    for variant in variants:
        if not isinstance(variant, dict) or not variant.get("id"):
            continue
        variant_tokens = set(token.lower() for token in _variant_specific_tokens(variant))
        variant_tokens -= product_tokens
        if variant_tokens & message_tokens:
            return str(variant["id"])
    return None


def _variant_specific_tokens(variant: dict[str, Any]) -> set[str]:
    tokens: set[str] = set()
    for key in ("title", "name", "sku"):
        if variant.get(key):
            tokens.update(token.upper() for token in _tokens(str(variant[key])))
    options = variant.get("options")
    if isinstance(options, dict):
        for value in options.values():
            tokens.update(token.upper() for token in _tokens(str(value)))
    elif isinstance(options, list):
        for option in options:
            if isinstance(option, dict):
                tokens.update(token.upper() for token in _tokens(str(option.get("value") or option.get("title") or "")))
    return tokens


def _extract_size(message: str) -> str | None:
    normalized = _normalize(message)
    if "extra large" in normalized:
        return "XL"
    if "extra small" in normalized:
        return "XS"
    tokens = [token.upper() for token in _tokens(message)]
    word_sizes = {"SMALL": "S", "MEDIUM": "M", "LARGE": "L"}
    for token in tokens:
        if token in {"XS", "S", "M", "L", "XL", "XXL"}:
            return token
        mapped = word_sizes.get(token)
        if mapped:
            return mapped
    return None


def _extract_quantity(message: str) -> int | None:
    match = re.search(r"\b(?:qty|quantity)\s*[:=]?\s*(\d+)\b", message, re.IGNORECASE)
    if not match:
        match = re.search(r"\b(\d+)\b", message)
    if not match:
        return None
    try:
        value = int(match.group(1))
    except ValueError:
        return None
    return value if value > 0 else None


def _looks_like_purchase(message: str) -> bool:
    return bool(set(_tokens(message)) & _BUY_TERMS)


def _looks_like_workflow_continuation(message: str) -> bool:
    return bool(set(_tokens(message)) & _WORKFLOW_TERMS)


def _looks_like_continuation(message: str) -> bool:
    tokens = set(_tokens(message))
    if tokens & _BUY_TERMS:
        return True
    return bool(tokens & {"xs", "s", "m", "l", "xl", "xxl", "small", "medium", "large"})


def _json_safe(value: Any, *, depth: int = 0) -> Any:
    if depth > 4:
        return None
    if isinstance(value, dict):
        return {str(key): _json_safe(item, depth=depth + 1) for key, item in list(value.items())[:30]}
    if isinstance(value, list):
        return [_json_safe(item, depth=depth + 1) for item in value[:30]]
    if isinstance(value, (str, int, float, bool)) or value is None:
        return value
    return str(value)


def _tokens(value: str) -> list[str]:
    return re.findall(r"[a-z0-9]+", _normalize(value))


def _normalize(value: str) -> str:
    normalized = re.sub(r"[^a-z0-9]+", " ", value.lower())
    normalized = re.sub(r"\s+", " ", normalized).strip()
    return normalized


def _compact(value: str) -> str:
    return value.replace(" ", "")


def _singular(value: str) -> str:
    return value[:-1] if value.endswith("s") else value


def _action_path_targets_entity(action: Any, entity: dict[str, Any]) -> bool:
    path = _normalize(str(getattr(action, "path", "") or ""))
    entity_type = _normalize(str(entity.get("entity_type") or ""))
    singular = _singular(entity_type)
    if not path or not singular:
        return False
    return f"{entity_type} id" in path or f"{singular} id" in path
