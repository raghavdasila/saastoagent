from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass
from typing import Any, Iterable

_TOKEN_RE = re.compile(r"[a-z0-9]+", re.IGNORECASE)


@dataclass(frozen=True)
class RouterDocument:
    action_node_id: Any
    generated_tool_id: Any
    endpoint_key: str
    doc_kind: str
    search_text: str
    tokens: list[str]
    graph_refs: dict[str, list[str]]


def tokenize(value: str) -> list[str]:
    normalized = re.sub(r"([a-z0-9])([A-Z])", r"\1 \2", value or "")
    normalized = re.sub(r"[_/{}().:-]+", " ", normalized)
    tokens: list[str] = []
    for raw in _TOKEN_RE.findall(normalized):
        token = raw.lower().strip()
        if len(token) <= 1:
            continue
        tokens.append(token)
        if token.endswith("s") and len(token) > 3:
            tokens.append(token[:-1])
    return list(dict.fromkeys(tokens))


def endpoint_key_for(action: Any) -> str:
    action_id = getattr(action, "id", None)
    if action_id is not None:
        return str(action_id)
    raw = f"{getattr(action, 'method', '')}:{getattr(action, 'path', '')}"
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()[:32]


def build_router_documents(rows: Iterable[tuple[Any, Any]]) -> list[RouterDocument]:
    docs: list[RouterDocument] = []
    for tool, action in rows:
        endpoint_key = endpoint_key_for(action)
        graph_refs = _graph_refs(action, tool)
        docs.append(_doc(action, tool, endpoint_key, "endpoint", _endpoint_text(action, tool), graph_refs))
        for parameter in _as_list(getattr(action, "parameters", None)):
            if isinstance(parameter, dict):
                docs.append(_doc(action, tool, endpoint_key, "parameter", _parameter_text(parameter), graph_refs))
        request_text = _request_text(action, tool)
        if request_text:
            docs.append(_doc(action, tool, endpoint_key, "request", request_text, graph_refs))
        response_text = _response_text(action)
        if response_text:
            docs.append(_doc(action, tool, endpoint_key, "response", response_text, graph_refs))
        auth_text = _auth_text(action)
        if auth_text:
            docs.append(_doc(action, tool, endpoint_key, "auth", auth_text, graph_refs))
        docs.append(_doc(action, tool, endpoint_key, "graph", _graph_text(graph_refs), graph_refs))
    return docs


def catalog_fingerprint(rows: Iterable[tuple[Any, Any]]) -> str:
    payload = []
    for tool, action in rows:
        payload.append(
            {
                "action": {
                    "id": str(getattr(action, "id", "")),
                    "method": _scalar(getattr(action, "method", "")),
                    "path": _scalar(getattr(action, "path", "")),
                    "name": _scalar(getattr(action, "name", "")),
                    "description": _scalar(getattr(action, "description", "")),
                    "parameters": _stable_json_value(getattr(action, "parameters", [])),
                    "request_body": _stable_json_value(getattr(action, "request_body", {})),
                    "responses": _stable_json_value(getattr(action, "responses", {})),
                    "security": _stable_json_value(getattr(action, "security", [])),
                    "tags": _stable_json_value(getattr(action, "tags", [])),
                    "risk_level": _enum_value(getattr(action, "risk_level", "")),
                    "status": _enum_value(getattr(action, "status", "")),
                    "source_index": _scalar(getattr(action, "source_index", "")),
                },
                "tool": {
                    "id": str(getattr(tool, "id", "")),
                    "action_node_id": str(getattr(tool, "action_node_id", "")),
                    "name": _scalar(getattr(tool, "name", "")),
                    "description": _scalar(getattr(tool, "description", "")),
                    "function_schema": _stable_json_value(getattr(tool, "function_schema", {})),
                    "risk_level": _enum_value(getattr(tool, "risk_level", "")),
                    "status": _enum_value(getattr(tool, "status", "")),
                    "requires_approval": bool(getattr(tool, "requires_approval", False)),
                },
            }
        )
    payload.sort(key=lambda item: (item["action"]["method"], item["action"]["path"], item["action"]["id"], item["tool"]["id"]))
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":"), default=str)
    return hashlib.sha256(encoded.encode("utf-8")).hexdigest()


def _doc(action: Any, tool: Any, endpoint_key: str, doc_kind: str, search_text: str, graph_refs: dict[str, list[str]]) -> RouterDocument:
    return RouterDocument(
        action_node_id=getattr(action, "id", None),
        generated_tool_id=getattr(tool, "id", None),
        endpoint_key=endpoint_key,
        doc_kind=doc_kind,
        search_text=search_text,
        tokens=tokenize(search_text),
        graph_refs=graph_refs,
    )


def _endpoint_text(action: Any, tool: Any) -> str:
    return " ".join(
        _non_empty(
            [
                "endpoint",
                _scalar(getattr(action, "method", "")),
                _scalar(getattr(action, "path", "")),
                _scalar(getattr(action, "name", "")),
                _scalar(getattr(action, "description", "")),
                _scalar(getattr(tool, "name", "")),
                _scalar(getattr(tool, "description", "")),
                "tags",
                " ".join(str(tag) for tag in _as_list(getattr(action, "tags", None))),
            ]
        )
    )


def _parameter_text(parameter: dict[str, Any]) -> str:
    parts = [
        "parameter",
        str(parameter.get("name") or ""),
        str(parameter.get("in") or ""),
        "required" if parameter.get("required") else "optional",
        str(parameter.get("description") or ""),
        _compact_json(parameter.get("schema") or {}),
    ]
    return " ".join(_non_empty(parts))


def _request_text(action: Any, tool: Any) -> str:
    parts = [
        "request body schema",
        _compact_json(getattr(action, "request_body", {}) or {}),
        "function parameters",
        _compact_json((getattr(tool, "function_schema", {}) or {}).get("parameters") or {}),
    ]
    return " ".join(_non_empty(parts))


def _response_text(action: Any) -> str:
    responses = getattr(action, "responses", {}) or {}
    if not responses:
        return ""
    return "response schema " + _compact_json(responses)


def _auth_text(action: Any) -> str:
    security = getattr(action, "security", []) or []
    if not security:
        return ""
    return "auth security requirements " + _compact_json(security)


def _graph_refs(action: Any, tool: Any) -> dict[str, list[str]]:
    tags = [str(tag) for tag in _as_list(getattr(action, "tags", None)) if str(tag).strip()]
    resources = tags or _resource_terms_from_path(getattr(action, "path", "") or "")
    param_names = [
        str(parameter.get("name"))
        for parameter in _as_list(getattr(action, "parameters", None))
        if isinstance(parameter, dict) and parameter.get("name")
    ]
    schema = (getattr(tool, "function_schema", {}) or {}).get("parameters") or {}
    properties = schema.get("properties") if isinstance(schema, dict) else {}
    if isinstance(properties, dict):
        param_names.extend(str(name) for name in properties)
    auth = _auth_names(getattr(action, "security", []) or [])
    return {
        "resources": _dedupe([*resources, *_resource_terms_from_path(getattr(action, "path", "") or "")]),
        "tags": _dedupe(tags),
        "params": _dedupe(param_names),
        "auth": _dedupe(auth),
        "methods": _dedupe([str(getattr(action, "method", "") or "").lower()]),
    }


def _graph_text(graph_refs: dict[str, list[str]]) -> str:
    parts = ["graph"]
    for resource in graph_refs.get("resources", []):
        parts.extend(["resource", resource])
    for tag in graph_refs.get("tags", []):
        parts.extend(["tag", tag])
    for param in graph_refs.get("params", []):
        parts.extend(["param", param])
    for method in graph_refs.get("methods", []):
        parts.extend(["method", method])
    return " ".join(_non_empty(parts))


def _resource_terms_from_path(path: str) -> list[str]:
    terms = []
    for segment in str(path or "").split("/"):
        if not segment or segment.startswith("{"):
            continue
        terms.extend(tokenize(segment))
    return _dedupe(terms)


def _auth_names(security: Any) -> list[str]:
    names: list[str] = []
    for item in _as_list(security):
        if isinstance(item, dict):
            names.extend(str(key) for key in item.keys())
    return _dedupe(names)


def _as_list(value: Any) -> list[Any]:
    return value if isinstance(value, list) else []


def _non_empty(values: Iterable[str]) -> list[str]:
    return [value for value in values if value]


def _dedupe(values: Iterable[str]) -> list[str]:
    return list(dict.fromkeys(value for value in values if value))


def _compact_json(value: Any) -> str:
    if value in (None, "", [], {}):
        return ""
    return json.dumps(_stable_json_value(value), sort_keys=True, default=str)


def _stable_json_value(value: Any) -> Any:
    if isinstance(value, dict):
        return {str(key): _stable_json_value(val) for key, val in sorted(value.items(), key=lambda item: str(item[0]))}
    if isinstance(value, list):
        return [_stable_json_value(item) for item in value]
    return _enum_value(value)


def _enum_value(value: Any) -> Any:
    return value.value if hasattr(value, "value") else value


def _scalar(value: Any) -> str:
    if value is None:
        return ""
    return str(_enum_value(value))
