from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from pathlib import Path
from urllib.parse import urlparse
from typing import Any

from jsonschema import Draft7Validator

from .openapi_loader import NormalizedBundle, NormalizedEndpoint, NormalizedParameter
from .spec_repair import read_repaired_specs


def resolve_ref(spec: dict[str, Any], ref: str) -> dict[str, Any]:
    if not ref.startswith("#/"):
        return {}
    value: Any = spec
    for part in ref[2:].split("/"):
        part = part.replace("~1", "/").replace("~0", "~")
        if not isinstance(value, dict):
            return {}
        value = value.get(part, {})
    return value if isinstance(value, dict) else {}


def dereference_schema(spec: dict[str, Any], schema: dict[str, Any], seen: set[str] | None = None) -> dict[str, Any]:
    seen = seen or set()
    if "$ref" in schema and isinstance(schema["$ref"], str):
        ref = schema["$ref"]
        if ref in seen:
            return {}
        return dereference_schema(spec, resolve_ref(spec, ref), seen | {ref})
    merged = dict(schema)
    for key in ["allOf", "anyOf", "oneOf"]:
        if isinstance(merged.get(key), list) and merged[key]:
            selected = dereference_schema(spec, merged[key][0], seen)
            if key == "allOf":
                combined: dict[str, Any] = {"type": "object", "properties": {}, "required": []}
                for item in merged[key]:
                    item_schema = dereference_schema(spec, item, seen)
                    combined["properties"].update(item_schema.get("properties", {}) if isinstance(item_schema.get("properties"), dict) else {})
                    combined["required"].extend(item_schema.get("required", []) if isinstance(item_schema.get("required"), list) else [])
                return combined
            return selected
    return merged


def sample_for_schema(spec: dict[str, Any], schema: dict[str, Any]) -> Any:
    schema = dereference_schema(spec, schema)
    if "enum" in schema and isinstance(schema["enum"], list) and schema["enum"]:
        return schema["enum"][0]
    schema_type = schema.get("type")
    if isinstance(schema_type, list):
        schema_type = next((item for item in schema_type if item != "null"), schema_type[0])
    if schema_type == "string" or schema.get("format") in {"date-time", "date", "uuid"}:
        return "sample"
    if schema_type == "integer":
        return 1
    if schema_type == "number":
        return 1.0
    if schema_type == "boolean":
        return True
    if schema_type == "array":
        item_schema = schema.get("items", {}) if isinstance(schema.get("items"), dict) else {}
        return [sample_for_schema(spec, item_schema)]
    if schema_type == "object" or "properties" in schema:
        properties = schema.get("properties", {}) if isinstance(schema.get("properties"), dict) else {}
        required = schema.get("required", []) if isinstance(schema.get("required"), list) else []
        selected = required or list(properties)[:1]
        return {
            name: sample_for_schema(spec, prop_schema if isinstance(prop_schema, dict) else {})
            for name, prop_schema in properties.items()
            if name in selected
        }
    return "sample"


def actual_path(path_pattern: str) -> str:
    return re.sub(r"\{[^}]+\}", "sample", path_pattern)


def server_host_url(spec: dict[str, Any]) -> str:
    servers = spec.get("servers", []) if isinstance(spec.get("servers"), list) else []
    if servers and isinstance(servers[0], dict) and servers[0].get("url"):
        parsed = urlparse(str(servers[0]["url"]))
        if parsed.scheme and parsed.netloc:
            return f"{parsed.scheme}://{parsed.netloc}"
    return "http://localhost"


def sample_for_parameter(param: NormalizedParameter, spec: dict[str, Any]) -> Any:
    return sample_for_schema(spec, param.schema or {"type": "string"})


@dataclass
class ValidationContext:
    specs: dict[str, dict[str, Any]]
    endpoints_by_id: dict[str, NormalizedEndpoint] = field(default_factory=dict)
    apps: dict[str, Any] = field(default_factory=dict)
    load_status: dict[str, str] = field(default_factory=dict)
    request_validation_cache: dict[str, dict[str, Any]] = field(default_factory=dict)

    def operation(self, endpoint: NormalizedEndpoint) -> dict[str, Any]:
        spec = self.specs.get(endpoint.source, {})
        path_item = spec.get("paths", {}).get(endpoint.path, {}) if isinstance(spec.get("paths"), dict) else {}
        operation = path_item.get(endpoint.method.lower(), {}) if isinstance(path_item, dict) else {}
        return operation if isinstance(operation, dict) else {}

    def request_schema(self, endpoint: NormalizedEndpoint) -> dict[str, Any] | None:
        request_body = self.operation(endpoint).get("requestBody", {})
        if not isinstance(request_body, dict):
            return None
        content = request_body.get("content", {})
        if not isinstance(content, dict):
            return None
        media = content.get("application/json") or next(iter(content.values()), None)
        if not isinstance(media, dict) or not isinstance(media.get("schema"), dict):
            return None
        return media["schema"]

    def synthetic_request_body(self, endpoint: NormalizedEndpoint) -> dict[str, Any] | list[Any] | None:
        if endpoint.operation_class not in {"create", "update"}:
            return None
        schema = self.request_schema(endpoint)
        if not schema:
            return None
        return sample_for_schema(self.specs.get(endpoint.source, {}), schema)

    def request_body_schema_pass(self, endpoint: NormalizedEndpoint) -> tuple[float, str]:
        body = self.synthetic_request_body(endpoint)
        schema = self.request_schema(endpoint)
        if body is None or not schema:
            return 1.0, "not_applicable"
        spec = self.specs.get(endpoint.source, {})
        resolved = dereference_schema(spec, schema)
        try:
            Draft7Validator(resolved).validate(body)
            return 1.0, "passed"
        except Exception as exc:
            return 0.0, f"{exc.__class__.__name__}: {exc}"

    def security_headers(self, endpoint: NormalizedEndpoint) -> dict[str, str]:
        spec = self.specs.get(endpoint.source, {})
        schemes = spec.get("components", {}).get("securitySchemes", {}) if isinstance(spec.get("components"), dict) else {}
        headers: dict[str, str] = {}
        for scheme_name in endpoint.security:
            scheme = schemes.get(scheme_name, {}) if isinstance(schemes, dict) else {}
            if scheme.get("type") == "http" and str(scheme.get("scheme", "")).lower() == "bearer":
                headers["Authorization"] = "Bearer sample"
            if scheme.get("type") == "apiKey" and scheme.get("in") == "header" and scheme.get("name"):
                headers[str(scheme["name"])] = "sample"
        return headers

    def synthetic_request_parts(self, endpoint: NormalizedEndpoint) -> dict[str, Any]:
        spec = self.specs.get(endpoint.source, {})
        path_params: dict[str, Any] = {}
        query_params: dict[str, Any] = {}
        for param in endpoint.params:
            if not param.required:
                continue
            sample = sample_for_parameter(param, spec)
            if param.location == "path":
                path_params[param.name] = sample
            elif param.location == "query":
                query_params[param.name] = sample
        body = self.synthetic_request_body(endpoint)
        data = b""
        if body is not None:
            data = json.dumps(body).encode("utf-8")
        return {
            "path": actual_path(endpoint.path),
            "path_pattern": endpoint.path,
            "view_args": path_params,
            "args": query_params,
            "headers": self.security_headers(endpoint),
            "data": data,
            "content_type": "application/json",
        }

    def validate_endpoint_request(self, endpoint: NormalizedEndpoint) -> dict[str, Any]:
        body_pass, body_status = self.request_body_schema_pass(endpoint)
        app = self.apps.get(endpoint.source)
        if app is None:
            return {
                "request_body_schema_pass": body_pass,
                "validation_pass": 0.0,
                "validation_status": self.load_status.get(endpoint.source, "openapi_core_app_missing"),
                "request_body_status": body_status,
                "response_validation_status": "unknown_no_fixture",
            }
        try:
            from openapi_core.testing import MockRequest

            parts = self.synthetic_request_parts(endpoint)
            spec = self.specs.get(endpoint.source, {})
            request = MockRequest(
                host_url=server_host_url(spec),
                method=endpoint.method.lower(),
                path=parts["path"],
                path_pattern=parts["path_pattern"],
                args=parts["args"],
                view_args=parts["view_args"],
                headers=parts["headers"],
                data=parts["data"],
                content_type=parts["content_type"],
            )
            app.validate_request(request)
            validation_pass = 1.0
            status = "passed"
        except Exception as exc:
            validation_pass = 0.0
            status = f"{exc.__class__.__name__}: {exc}"
        return {
            "request_body_schema_pass": body_pass,
            "validation_pass": validation_pass,
            "validation_status": status,
            "request_body_status": body_status,
            "response_validation_status": "unknown_no_fixture",
        }

    def validate_step(self, step: dict[str, Any]) -> dict[str, Any]:
        endpoint_id = str(step.get("endpoint_id", ""))
        if endpoint_id in self.request_validation_cache:
            return dict(self.request_validation_cache[endpoint_id])
        endpoint = self.endpoints_by_id.get(endpoint_id)
        if endpoint is None:
            return {
                "request_body_schema_pass": 0.0,
                "validation_pass": 0.0,
                "validation_status": "endpoint_not_found",
                "request_body_status": "endpoint_not_found",
                "response_validation_status": "unknown_no_fixture",
            }
        result = self.validate_endpoint_request(endpoint)
        self.request_validation_cache[endpoint_id] = dict(result)
        return result


def build_validation_context(artifacts_dir: Path, bundle: NormalizedBundle) -> ValidationContext:
    specs = read_repaired_specs(artifacts_dir)
    apps: dict[str, Any] = {}
    statuses: dict[str, str] = {}
    try:
        from openapi_core import OpenAPI
    except ImportError:
        return ValidationContext(
            specs=specs,
            endpoints_by_id={endpoint.id: endpoint for endpoint in bundle.endpoints},
            apps={},
            load_status={source: "openapi-core not installed" for source in specs},
        )
    for source, spec in specs.items():
        try:
            apps[source] = OpenAPI.from_dict(spec)
            statuses[source] = "loaded"
        except Exception as exc:
            statuses[source] = f"load_failed: {exc.__class__.__name__}: {exc}"
    return ValidationContext(
        specs=specs,
        endpoints_by_id={endpoint.id: endpoint for endpoint in bundle.endpoints},
        apps=apps,
        load_status=statuses,
    )
