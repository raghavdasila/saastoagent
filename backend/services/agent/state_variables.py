from __future__ import annotations

import copy
from datetime import datetime, timezone
from typing import Any


def remember_resource_result_variables(
    frame: dict[str, Any] | None,
    *,
    collection_path: str,
    result: dict[str, Any],
    origin: dict[str, Any] | None = None,
) -> dict[str, Any]:
    updated = copy.deepcopy(frame) if isinstance(frame, dict) else {}
    resource = _extract_resource_object(
        result.get("body") if isinstance(result, dict) else None,
        depth=0,
        collection_path=collection_path,
    )
    if not resource:
        return updated
    resource_id = resource.get("id")
    if not isinstance(resource_id, str) or not resource_id:
        return updated

    resource_name = _resource_alias(collection_path)
    id_name = resource_variable_name(collection_path, "id")
    put_variable(
        updated,
        name=id_name,
        value=resource_id,
        visibility="private",
        value_type="string",
        tags=["resource_id", "internal_dependency"],
        aliases=["id", f"{resource_name}_id"],
        resource={"collection_path": collection_path, "resource_id": resource_id},
        origin={**(origin or {}), "field_path": f"{resource_name}.id"},
    )
    updated["active_resource_ref"] = id_name

    for key, value in _scalar_fields(resource).items():
        put_variable(
            updated,
            name=resource_variable_name(collection_path, key),
            value=value,
            visibility="private",
            value_type=_value_type(value),
            tags=["scalar_field"],
            aliases=[key],
            resource={"collection_path": collection_path, "resource_id": resource_id},
            origin={**(origin or {}), "field_path": f"{resource_name}.{key}"},
        )
    return updated


def remember_resource_id_variable(
    frame: dict[str, Any] | None,
    *,
    collection_path: str,
    resource_id: str,
    origin: dict[str, Any] | None = None,
) -> dict[str, Any]:
    updated = copy.deepcopy(frame) if isinstance(frame, dict) else {}
    resource_name = _resource_alias(collection_path)
    name = resource_variable_name(collection_path, "id")
    put_variable(
        updated,
        name=name,
        value=resource_id,
        visibility="private",
        value_type="string",
        tags=["resource_id", "internal_dependency"],
        aliases=["id", f"{resource_name}_id"],
        resource={"collection_path": collection_path, "resource_id": resource_id},
        origin=origin or {},
    )
    updated["active_resource_ref"] = name
    return updated


def put_variable(
    frame: dict[str, Any],
    *,
    name: str,
    value: Any,
    visibility: str,
    value_type: str,
    tags: list[str] | None = None,
    aliases: list[str] | None = None,
    resource: dict[str, Any] | None = None,
    origin: dict[str, Any] | None = None,
    choice: dict[str, Any] | None = None,
) -> dict[str, Any]:
    variables = frame.get("variables")
    if not isinstance(variables, dict):
        variables = {}
    variables[name] = {
        "name": name,
        "value": value,
        "visibility": visibility,
        "value_type": value_type,
        "tags": list(dict.fromkeys(tags or [])),
        "aliases": list(dict.fromkeys(str(alias) for alias in aliases or [] if alias)),
        "resource": resource or None,
        "origin": origin or {},
        "choice": choice or None,
        "updated_at": datetime.now(timezone.utc).isoformat(),
    }
    frame["variables"] = variables
    return frame


def get_variable_value(frame: dict[str, Any] | None, name: str) -> Any:
    variable = get_variable(frame, name)
    return variable.get("value") if isinstance(variable, dict) else None


def get_variable(frame: dict[str, Any] | None, name: str) -> dict[str, Any] | None:
    if not isinstance(frame, dict):
        return None
    variables = frame.get("variables")
    if not isinstance(variables, dict):
        return None
    item = variables.get(name)
    return item if isinstance(item, dict) else None


def resolve_dependency_id_from_variables(frame: dict[str, Any] | None, parent_collection_path: str | None) -> str | None:
    if not parent_collection_path:
        return None
    value = get_variable_value(frame, resource_variable_name(parent_collection_path, "id"))
    return str(value) if value not in (None, "") else None


def resolve_input_from_variables(frame: dict[str, Any] | None, input_name: str, *, action: Any) -> Any:
    if not isinstance(frame, dict):
        return None
    variables = frame.get("variables")
    if not isinstance(variables, dict):
        return None

    target_collection = _target_collection_for_input(str(getattr(action, "path", "") or ""), input_name)
    if target_collection:
        value = get_variable_value(frame, resource_variable_name(target_collection, "id"))
        if value not in (None, ""):
            return value

    active_ref = frame.get("active_resource_ref")
    if isinstance(active_ref, str):
        active = variables.get(active_ref)
        resource = active.get("resource") if isinstance(active, dict) else None
        collection_path = resource.get("collection_path") if isinstance(resource, dict) else None
        if collection_path and input_name != "id":
            value = get_variable_value(frame, resource_variable_name(str(collection_path), input_name))
            if value not in (None, ""):
                return value

    for variable in variables.values():
        if not isinstance(variable, dict):
            continue
        aliases = {str(alias) for alias in variable.get("aliases") or []}
        if variable.get("name") == input_name or (input_name != "id" and input_name in aliases):
            value = variable.get("value")
            if value not in (None, ""):
                return value
    return None


def remember_choice_variable(
    frame: dict[str, Any] | None,
    *,
    input_name: str,
    target_action_path: str,
    items: list[dict[str, Any]],
    origin: dict[str, Any] | None = None,
) -> dict[str, Any]:
    updated = copy.deepcopy(frame) if isinstance(frame, dict) else {}
    choices = [_choice_item(item) for item in items if isinstance(item, dict) and item.get("id")]
    choices = [item for item in choices if item is not None]
    if len({item["value"] for item in choices}) <= 1:
        return updated
    put_variable(
        updated,
        name=f"choice.{input_name}",
        value=None,
        visibility="private",
        value_type="choice",
        tags=["pending_choice", "internal_input"],
        aliases=[input_name],
        origin=origin or {},
        choice={"target_action_path": target_action_path, "input_name": input_name, "items": choices[:8]},
    )
    return updated


def pending_choice_prompt(frame: dict[str, Any] | None, missing: list[str]) -> str | None:
    variable = _choice_variable_for_missing(frame, missing)
    if not variable:
        return None
    choice = variable.get("choice")
    items = choice.get("items") if isinstance(choice, dict) else None
    labels = [str(item["label"]) for item in items or [] if isinstance(item, dict) and item.get("label")]
    if not labels:
        return None
    return "I found multiple options. Which one should I use?\n\n" + "\n".join(f"- {label}" for label in labels[:8])


def resolve_pending_choice(frame: dict[str, Any] | None, input_name: str, message: str) -> str | None:
    variable = _choice_variable_for_missing(frame, [input_name])
    if not variable:
        return None
    choice = variable.get("choice")
    items = choice.get("items") if isinstance(choice, dict) else None
    normalized = _choice_match_text(message)
    for item in items or []:
        if not isinstance(item, dict):
            continue
        for alias in item.get("aliases") or []:
            if alias and str(alias) in normalized:
                return str(item["value"])
    return None


def pending_choice_target_path_for_message(frame: dict[str, Any] | None, message: str) -> str | None:
    if not isinstance(frame, dict):
        return None
    variables = frame.get("variables")
    if not isinstance(variables, dict):
        return None
    for variable in variables.values():
        choice = variable.get("choice") if isinstance(variable, dict) else None
        if not isinstance(choice, dict):
            continue
        input_name = choice.get("input_name")
        if input_name and resolve_pending_choice(frame, str(input_name), message):
            target_path = choice.get("target_action_path")
            return str(target_path) if target_path else None
    return None


def fill_inputs_from_pending_choice_variables(
    *,
    message: str,
    inputs: dict[str, Any],
    missing: list[str],
    frame: dict[str, Any] | None,
) -> tuple[dict[str, Any], list[str]]:
    if not missing or not isinstance(frame, dict):
        return inputs, missing
    next_inputs = dict(inputs)
    remaining: list[str] = []
    for name in missing:
        string_name = str(name)
        value = resolve_pending_choice(frame, string_name, message)
        if value is None:
            remaining.append(string_name)
            continue
        next_inputs[string_name] = value
    return next_inputs, remaining


def known_resource_collection_paths(frame: dict[str, Any] | None) -> list[str]:
    if not isinstance(frame, dict):
        return []
    variables = frame.get("variables")
    if not isinstance(variables, dict):
        return []
    paths: list[str] = []
    for variable in variables.values():
        resource = variable.get("resource") if isinstance(variable, dict) else None
        path = resource.get("collection_path") if isinstance(resource, dict) else None
        if path and str(path) not in paths:
            paths.append(str(path))
    return paths


def resource_variable_name(collection_path: str, field_name: str) -> str:
    return f"resource.{collection_path}.{field_name}"


def _resource_alias(collection_path: str) -> str:
    segment = collection_path.rstrip("/").split("/")[-1].replace("-", "_")
    return segment[:-1] if segment.endswith("s") else segment


def _extract_resource_object(value: Any, *, depth: int, collection_path: str) -> dict[str, Any] | None:
    if depth > 4:
        return None
    if isinstance(value, dict):
        for key in _resource_body_keys(collection_path):
            item = value.get(key)
            if isinstance(item, dict) and isinstance(item.get("id"), str) and item.get("id"):
                return item
            if isinstance(item, list):
                for child in item:
                    if isinstance(child, dict) and isinstance(child.get("id"), str) and child.get("id"):
                        return child
        if isinstance(value.get("id"), str) and value.get("id"):
            return value
        for item in value.values():
            found = _extract_resource_object(item, depth=depth + 1, collection_path=collection_path)
            if found is not None:
                return found
    if isinstance(value, list):
        for item in value:
            found = _extract_resource_object(item, depth=depth + 1, collection_path=collection_path)
            if found is not None:
                return found
    return None


def _resource_body_keys(collection_path: str) -> list[str]:
    segment = collection_path.rstrip("/").split("/")[-1]
    normalized = segment.replace("-", "_")
    singular = normalized[:-1] if normalized.endswith("s") else normalized
    values = [singular, normalized, singular.replace("_", "-"), segment]
    return list(dict.fromkeys(value for value in values if value))


def _scalar_fields(value: dict[str, Any]) -> dict[str, Any]:
    fields: dict[str, Any] = {}
    for key, item in list(value.items())[:40]:
        if item in (None, ""):
            continue
        if isinstance(item, str | int | float | bool):
            fields[str(key)] = item
    return fields


def _value_type(value: Any) -> str:
    if isinstance(value, bool):
        return "boolean"
    if isinstance(value, int | float):
        return "number"
    return "string"


def _target_collection_for_input(path: str, input_name: str) -> str | None:
    segments = [segment for segment in path.split("/") if segment]
    marker = "{" + input_name + "}"
    for index, segment in enumerate(segments):
        if segment == marker and index > 0:
            return "/" + "/".join(segments[:index])
    return None


def _choice_variable_for_missing(frame: dict[str, Any] | None, missing: list[str]) -> dict[str, Any] | None:
    if not isinstance(frame, dict):
        return None
    variables = frame.get("variables")
    if not isinstance(variables, dict):
        return None
    for name in missing:
        variable = variables.get(f"choice.{name}")
        if isinstance(variable, dict) and isinstance(variable.get("choice"), dict):
            return variable
    return None


def _choice_item(item: dict[str, Any]) -> dict[str, Any] | None:
    value = item.get("id")
    if not value:
        return None
    label = _first_string(item, ["title", "name", "label", "display_name", "handle", "code"]) or str(value)
    aliases = {_choice_match_text(label)}
    for key in ("title", "name", "label", "display_name", "handle", "code"):
        raw = item.get(key)
        if isinstance(raw, str) and raw.strip():
            aliases.add(_choice_match_text(raw))
    return {"label": label, "value": str(value), "aliases": sorted(alias for alias in aliases if alias)}


def _choice_match_text(value: str) -> str:
    normalized = value.lower().replace("-", " ").replace("_", " ")
    return " ".join(part for part in normalized.split() if part)


def _first_string(item: dict[str, Any], keys: list[str]) -> str | None:
    for key in keys:
        value = item.get(key)
        if isinstance(value, str) and value.strip():
            return value.strip()
    return None
