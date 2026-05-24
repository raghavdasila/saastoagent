from __future__ import annotations

import copy
import re
import uuid
from dataclasses import dataclass
from typing import Any


_NATURAL_USER_FIELDS = {
    "address",
    "city",
    "country",
    "country_code",
    "email",
    "first_name",
    "last_name",
    "name",
    "phone",
    "postal_code",
    "quantity",
    "qty",
    "region",
    "region_id",
    "shipping",
    "shipping_address",
    "shipping_method",
    "size",
    "state",
    "variant",
    "variant_id",
    "zip",
}


@dataclass(frozen=True)
class MissingInput:
    name: str
    visibility: str
    public_label: str
    reason: str


@dataclass(frozen=True)
class MissingInputClassification:
    internal: list[MissingInput]
    user_facing: list[MissingInput]


def classify_missing_inputs(missing: list[str], *, action: Any) -> MissingInputClassification:
    internal: list[MissingInput] = []
    user_facing: list[MissingInput] = []
    path_param_names = {
        str(param.get("name"))
        for param in (getattr(action, "parameters", None) or [])
        if isinstance(param, dict) and str(param.get("in") or "").lower() == "path"
    }
    path = str(getattr(action, "path", "") or "")
    for raw_name in missing:
        name = str(raw_name)
        lowered = name.lower()
        if name in path_param_names or _path_contains_parameter(path, name):
            internal.append(MissingInput(name=name, visibility="internal", public_label="", reason="path_identifier"))
            continue
        if lowered == "id" or (lowered.endswith("_id") and lowered not in _NATURAL_USER_FIELDS):
            internal.append(MissingInput(name=name, visibility="internal", public_label="", reason="opaque_identifier"))
            continue
        public_label = _humanize(name)
        user_facing.append(MissingInput(name=name, visibility="user", public_label=public_label, reason="natural_field"))
    return MissingInputClassification(internal=internal, user_facing=user_facing)


def derive_parent_collection_path(path: str, missing_name: str) -> str | None:
    segments = [segment for segment in str(path or "").split("/") if segment]
    marker = "{" + missing_name + "}"
    for index, segment in enumerate(segments):
        if segment != marker:
            continue
        if index == 0:
            return None
        return "/" + "/".join(segments[:index])
    return None


def resolve_dependency_id_from_frame(frame: dict[str, Any] | None, parent_collection_path: str) -> str | None:
    if not isinstance(frame, dict):
        return None
    dependencies = frame.get("internal_dependencies")
    if not isinstance(dependencies, dict):
        return None
    dependency = dependencies.get(parent_collection_path)
    if isinstance(dependency, dict) and dependency.get("id"):
        return str(dependency["id"])
    if isinstance(dependency, str):
        return dependency
    return None


def remember_dependency_id(frame: dict[str, Any] | None, parent_collection_path: str, resource_id: str) -> dict[str, Any]:
    next_frame = copy.deepcopy(frame) if isinstance(frame, dict) else {}
    dependencies = next_frame.get("internal_dependencies")
    if not isinstance(dependencies, dict):
        dependencies = {}
    dependencies[parent_collection_path] = {"id": resource_id}
    next_frame["internal_dependencies"] = dependencies
    return next_frame


def extract_resource_id_from_result(result: dict[str, Any]) -> str | None:
    body = result.get("body") if isinstance(result, dict) else None
    return _extract_id(body, depth=0)


def policy_gap_payload(
    *,
    target_candidate: Any,
    dependency_candidate: Any,
    missing_internal_inputs: list[str],
    session_id: uuid.UUID | None,
    trace_id: uuid.UUID | None,
) -> dict[str, Any]:
    target_path = str(getattr(getattr(target_candidate, "action", None), "path", "") or "")
    dependency_path = str(getattr(getattr(dependency_candidate, "action", None), "path", "") or "")
    target_tool = str(getattr(getattr(target_candidate, "tool", None), "name", "") or "generated action")
    dependency_tool = str(getattr(getattr(dependency_candidate, "tool", None), "name", "") or "generated action")
    risk = _risk_value(getattr(getattr(target_candidate, "tool", None), "risk_level", None))
    action_paths = [path for path in [dependency_path, target_path] if path]
    return {
        "trigger_type": "domain_policy_gap",
        "title": "Owner policy needed for visitor automation",
        "summary": "Public chat found an internal API dependency that requires owner-approved automation before it can run for visitors.",
        "hint_text": "Allow this generated action chain only if the connected app should let the agent manage the internal dependency for public visitors.",
        "target_tool_name": target_tool,
        "target_action_path": target_path,
        "target_risk_level": risk,
        "evidence": {
            "policy_kind": "internal_dependency_write",
            "public_channel": True,
            "reason": "A public request needs an internal path identifier that can be created by another generated action.",
            "missing_internal_inputs": missing_internal_inputs,
            "dependency_tool_name": dependency_tool,
            "dependency_action_path": dependency_path,
            "requested_action_path": target_path,
            "allowed_action_paths": action_paths,
            "session_id": str(session_id) if session_id else None,
            "source_trace_id": str(trace_id) if trace_id else None,
        },
    }


def policy_allows_action_paths(candidate: Any, action_paths: list[str]) -> bool:
    if getattr(candidate, "trigger_type", None) != "domain_policy_gap":
        return False
    if getattr(candidate, "status", None) not in {"approved", "active"}:
        return False
    evidence = getattr(candidate, "evidence", None) or {}
    allowed = evidence.get("allowed_action_paths") if isinstance(evidence, dict) else None
    if not isinstance(allowed, list):
        return False
    allowed_set = {str(path) for path in allowed}
    return all(str(path) in allowed_set for path in action_paths)


def _path_contains_parameter(path: str, name: str) -> bool:
    return bool(re.search(r"\{" + re.escape(name) + r"\}", path or ""))


def _extract_id(value: Any, *, depth: int) -> str | None:
    if depth > 4:
        return None
    if isinstance(value, dict):
        direct_id = value.get("id")
        if isinstance(direct_id, str) and direct_id:
            return direct_id
        for item in value.values():
            found = _extract_id(item, depth=depth + 1)
            if found:
                return found
    if isinstance(value, list):
        for item in value:
            found = _extract_id(item, depth=depth + 1)
            if found:
                return found
    return None


def _humanize(value: str) -> str:
    return value.replace("_", " ").replace("-", " ")


def _risk_value(value: Any) -> str | None:
    if value is None:
        return None
    return value.value if hasattr(value, "value") else str(value)
