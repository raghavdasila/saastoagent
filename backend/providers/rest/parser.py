from __future__ import annotations

import json
from typing import Any

import httpx
import jsonref
import yaml

from backend.core.models import RiskLevel

MAX_SPEC_SIZE = 20 * 1024 * 1024
HTTP_METHODS = {"get", "post", "put", "patch", "delete", "head", "options", "trace"}
FINANCIAL_KEYWORDS = {
    "payment",
    "billing",
    "charge",
    "invoice",
    "subscription",
    "refund",
    "payout",
    "transaction",
    "price",
    "checkout",
}


async def fetch_spec(url: str, headers: dict[str, str] | None = None) -> str:
    async with httpx.AsyncClient(timeout=30, follow_redirects=True) as client:
        resp = await client.get(url, headers=headers or {})
        resp.raise_for_status()
        if len(resp.content) > MAX_SPEC_SIZE:
            raise ValueError("OpenAPI spec exceeds the 20MB limit")
        return resp.text


def parse_and_validate_spec(raw: str) -> dict[str, Any]:
    parsed = yaml.safe_load(raw)
    if not isinstance(parsed, dict):
        raise ValueError("Spec must be a YAML or JSON object")
    if "openapi" not in parsed and "swagger" not in parsed:
        raise ValueError("Not a valid OpenAPI or Swagger spec")
    resolved = jsonref.replace_refs(parsed)
    return json.loads(json.dumps(resolved, default=str))


def extract_endpoints(spec: dict[str, Any]) -> list[dict[str, Any]]:
    endpoints: list[dict[str, Any]] = []
    index = 0
    for path, path_item in (spec.get("paths") or {}).items():
        if not isinstance(path_item, dict):
            continue
        path_params = path_item.get("parameters", [])
        if not isinstance(path_params, list):
            path_params = []

        for method, operation in path_item.items():
            if method.lower() not in HTTP_METHODS or not isinstance(operation, dict):
                continue
            merged = dict(operation)
            merged["parameters"] = _merge_parameters(path_params, operation.get("parameters", []))
            endpoints.append(
                {
                    "index": index,
                    "path": path,
                    "method": method.upper(),
                    "operation": merged,
                }
            )
            index += 1
    return endpoints


def _merge_parameters(path_params: list[Any], op_params: Any) -> list[dict[str, Any]]:
    if not isinstance(op_params, list):
        op_params = []
    merged: dict[tuple[str, str], dict[str, Any]] = {}
    for param in [*path_params, *op_params]:
        if isinstance(param, dict):
            merged[(str(param.get("name", "")), str(param.get("in", "")))] = param
    return list(merged.values())


def classify_risk(method: str, path: str, description: str = "", tags: list[str] | None = None) -> RiskLevel:
    searchable = f"{path} {description} {' '.join(tags or [])}".lower()
    method = method.upper()
    if method == "DELETE":
        return RiskLevel.destructive
    if method in {"POST", "PUT", "PATCH"} and any(word in searchable for word in FINANCIAL_KEYWORDS):
        return RiskLevel.financial
    if method in {"POST", "PUT", "PATCH"}:
        return RiskLevel.write
    return RiskLevel.read


def build_action_node_data(endpoint: dict[str, Any], connection_id, workspace_id, spec_url: str) -> dict[str, Any]:
    operation = endpoint["operation"]
    method = endpoint["method"]
    path = endpoint["path"]
    description = operation.get("description") or operation.get("summary") or ""
    tags = operation.get("tags") if isinstance(operation.get("tags"), list) else []
    op_id = operation.get("operationId") or f"{method} {path}"

    params = operation.get("parameters") if isinstance(operation.get("parameters"), list) else []
    param_names = [str(p.get("name")) for p in params if isinstance(p, dict) and p.get("name")]
    body_names = _request_body_property_names(operation.get("requestBody"))
    embedding_text = " ".join(
        [method, path, str(op_id), " ".join(tags), description, " ".join(param_names), " ".join(body_names)]
    ).strip()

    return {
        "connection_id": connection_id,
        "workspace_id": workspace_id,
        "name": str(op_id),
        "path": path,
        "method": method,
        "description": description,
        "parameters": params,
        "request_body": operation.get("requestBody") or {},
        "responses": operation.get("responses") or {},
        "security": operation.get("security") or [],
        "tags": tags,
        "embedding_text": embedding_text,
        "risk_level": classify_risk(method, path, description, tags),
        "source_spec_url": spec_url,
        "source_index": str(endpoint["index"]),
    }


def _request_body_property_names(request_body: Any) -> list[str]:
    names: list[str] = []
    if not isinstance(request_body, dict):
        return names
    content = request_body.get("content")
    if not isinstance(content, dict):
        return names
    for media in content.values():
        if not isinstance(media, dict):
            continue
        schema = media.get("schema")
        if isinstance(schema, dict) and isinstance(schema.get("properties"), dict):
            names.extend(str(name) for name in schema["properties"].keys())
    return names
