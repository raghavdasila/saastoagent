from __future__ import annotations

import json
import re
import unicodedata
from copy import deepcopy
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Iterable
from urllib.request import Request, urlopen

import yaml

from .spec_repair import repair_specs, write_spec_artifacts


HTTP_METHODS = {"get", "post", "put", "patch", "delete", "head", "options", "trace"}


@dataclass
class NormalizedParameter:
    name: str
    location: str
    required: bool = False
    schema_ref: str | None = None
    schema_name: str | None = None
    description: str = ""
    schema: dict[str, Any] = field(default_factory=dict)


@dataclass
class NormalizedEndpoint:
    id: str
    source: str
    method: str
    path: str
    operation_id: str
    tags: list[str]
    summary: str
    description: str
    params: list[NormalizedParameter]
    required_params: list[str]
    request_schemas: list[str]
    response_schemas: list[str]
    security: list[str]
    resources: list[str]
    operation_class: str
    operation_confidence: float


@dataclass
class NormalizedBundle:
    endpoints: list[NormalizedEndpoint]
    schemas: dict[str, dict[str, Any]]
    security_schemes: dict[str, dict[str, Any]]
    manifest: dict[str, Any]
    raw_specs: dict[str, dict[str, Any]] = field(default_factory=dict)
    resolved_specs: dict[str, dict[str, Any]] = field(default_factory=dict)
    repaired_specs: dict[str, dict[str, Any]] = field(default_factory=dict)
    repair_manifest: dict[str, Any] = field(default_factory=dict)

    def endpoint_by_operation(self, operation_id: str) -> NormalizedEndpoint:
        for endpoint in self.endpoints:
            if endpoint.operation_id == operation_id:
                return endpoint
        raise KeyError(operation_id)

    def endpoint_by_id(self, endpoint_id: str) -> NormalizedEndpoint:
        for endpoint in self.endpoints:
            if endpoint.id == endpoint_id:
                return endpoint
        raise KeyError(endpoint_id)


def normalize_text(value: Any) -> str:
    return unicodedata.normalize("NFKC", str(value or "")).casefold()


def slugify(value: str) -> str:
    text = re.sub(r"[^a-zA-Z0-9]+", "_", value).strip("_").lower()
    return text or "unknown"


def source_name(path: Path) -> str:
    name = path.stem.lower()
    name = name.replace("openapi", "").strip("_-")
    return slugify(name or path.stem)


def schema_name_from_ref(ref: str | None) -> str | None:
    if not ref:
        return None
    return ref.rstrip("/").split("/")[-1]


def schema_refs(schema: Any) -> list[str]:
    refs: list[str] = []
    if isinstance(schema, dict):
        ref = schema.get("$ref")
        if isinstance(ref, str):
            refs.append(ref)
        for value in schema.values():
            refs.extend(schema_refs(value))
    elif isinstance(schema, list):
        for item in schema:
            refs.extend(schema_refs(item))
    return list(dict.fromkeys(refs))


def count_schema_refs(schema: Any) -> int:
    if isinstance(schema, dict):
        return (1 if isinstance(schema.get("$ref"), str) else 0) + sum(
            count_schema_refs(value) for value in schema.values()
        )
    if isinstance(schema, list):
        return sum(count_schema_refs(item) for item in schema)
    return 0


def schema_names_from_content(content: dict[str, Any] | None) -> list[str]:
    names: list[str] = []
    if not isinstance(content, dict):
        return names
    for media in content.values():
        schema = media.get("schema", {}) if isinstance(media, dict) else {}
        for ref in schema_refs(schema):
            name = schema_name_from_ref(ref)
            if name:
                names.append(name)
    return list(dict.fromkeys(names))


def read_spec(path_or_url: str | Path) -> tuple[str, dict[str, Any]]:
    raw_name = str(path_or_url)
    if raw_name.startswith(("http://", "https://")):
        request = Request(raw_name, headers={"User-Agent": "toolrouter-benchmark/0.1"})
        with urlopen(request, timeout=60) as response:
            text = response.read().decode("utf-8")
        name = slugify(raw_name.rstrip("/").split("/")[-1] or "download")
    else:
        path = Path(path_or_url)
        text = path.read_text(encoding="utf-8")
        name = source_name(path)
    parsed = yaml.safe_load(text)
    if not isinstance(parsed, dict):
        raise ValueError(f"OpenAPI spec did not parse as an object: {path_or_url}")
    return name, parsed


def validate_spec_with_library(spec: dict[str, Any]) -> dict[str, Any]:
    try:
        from openapi_spec_validator import validate
    except ImportError:
        return {"ok": False, "status": "openapi-spec-validator not installed", "errors": []}
    try:
        validate(spec)
        return {"ok": True, "status": "valid", "errors": []}
    except Exception as exc:
        return {
            "ok": False,
            "status": f"{exc.__class__.__name__}: {exc}",
            "errors": [str(exc)],
        }


def resolver_base_url(path_or_url: str | Path) -> str | None:
    raw = str(path_or_url)
    if raw.startswith(("http://", "https://", "file://")):
        return raw
    try:
        return Path(path_or_url).resolve().as_uri()
    except Exception:
        return None


def recursion_ref_stub(_limit: int, parsed_url: Any, _recursions: tuple[Any, ...] = ()) -> dict[str, str]:
    if getattr(parsed_url, "fragment", ""):
        return {"$ref": f"#{parsed_url.fragment}"}
    return {"$ref": parsed_url.geturl()}


def resolve_spec_with_prance(path_or_url: str | Path, raw_spec: dict[str, Any]) -> tuple[dict[str, Any], dict[str, Any]]:
    status = {
        "ok": False,
        "mode": "internal_component_refs",
        "refs_before": count_schema_refs(raw_spec),
        "refs_after": None,
        "parser": None,
        "errors": [],
    }
    try:
        from prance import BaseParser
    except ImportError:
        status["errors"].append("prance not installed")
        return raw_spec, status

    parsed_spec = raw_spec
    try:
        parser = BaseParser(
            spec_string=yaml.safe_dump(raw_spec, sort_keys=False),
            lazy=True,
            strict=False,
            backend="openapi-spec-validator",
        )
        parser.parse()
        parsed_spec = parser.specification
        status["parser"] = "baseparser_loaded"
    except Exception as exc:
        status["parser"] = f"baseparser_validation_failed: {exc.__class__.__name__}: {exc}"

    try:
        from prance.util.resolver import RESOLVE_INTERNAL, RefResolver

        resolved = deepcopy(parsed_spec)
        components = resolved.get("components", {}) if isinstance(resolved.get("components"), dict) else {}
        schemas = components.get("schemas", {}) if isinstance(components.get("schemas"), dict) else {}
        partial = {"components": {"schemas": schemas}}
        resolver = RefResolver(
            partial,
            url=resolver_base_url(path_or_url),
            recursion_limit=1,
            recursion_limit_handler=recursion_ref_stub,
            resolve_types=RESOLVE_INTERNAL,
            strict=False,
        )
        resolver.resolve_references()
        resolved.setdefault("components", {})["schemas"] = resolver.specs.get("components", {}).get("schemas", {})
        status["ok"] = True
        status["refs_after"] = count_schema_refs(resolved)
        return resolved, status
    except Exception as exc:
        status["errors"].append(f"{exc.__class__.__name__}: {exc}")
        return parsed_spec, status


def build_openapi_core_apps(raw_specs: dict[str, dict[str, Any]]) -> dict[str, str]:
    statuses: dict[str, str] = {}
    try:
        from openapi_core import OpenAPI
    except ImportError:
        return {name: "openapi-core not installed" for name in raw_specs}
    for name, spec in raw_specs.items():
        try:
            OpenAPI.from_dict(spec)
            statuses[name] = "loaded"
        except Exception as exc:
            statuses[name] = f"load_failed: {exc.__class__.__name__}: {exc}"
    return statuses


def merge_parameters(path_params: list[dict[str, Any]], op_params: list[dict[str, Any]]) -> list[dict[str, Any]]:
    merged: dict[tuple[str, str], dict[str, Any]] = {}
    for param in path_params + op_params:
        if not isinstance(param, dict):
            continue
        key = (str(param.get("in", "")), str(param.get("name", "")))
        merged[key] = param
    return list(merged.values())


def normalize_parameter(param: dict[str, Any]) -> NormalizedParameter:
    schema = param.get("schema") if isinstance(param.get("schema"), dict) else {}
    ref = next(iter(schema_refs(schema)), None)
    return NormalizedParameter(
        name=str(param.get("name", "")),
        location=str(param.get("in", "")),
        required=bool(param.get("required", False)),
        schema_ref=ref,
        schema_name=schema_name_from_ref(ref),
        description=str(param.get("description", "")),
        schema=schema,
    )


def infer_operation_class(method: str, path: str, params: list[NormalizedParameter], operation: dict[str, Any]) -> tuple[str, float]:
    method = method.upper()
    path_params = [p for p in params if p.location == "path"]
    op_text = normalize_text(" ".join([operation.get("operationId", ""), operation.get("summary", ""), path]))
    if method == "DELETE":
        return "delete", 0.98
    if method in {"PATCH", "PUT"}:
        return "update", 0.96
    if method == "POST":
        return ("custom", 0.60) if path_params else ("create", 0.90)
    if method == "GET":
        if "search" in op_text:
            return "search", 0.82
        return ("get", 0.93) if path_params else ("list", 0.93)
    return "custom", 0.50


def clean_resource(value: str) -> str | None:
    value = slugify(value)
    if not value:
        return None
    return value


def infer_resources(path: str, tags: list[str], operation_id: str, schema_names: Iterable[str]) -> list[str]:
    resources: list[str] = []
    for tag in tags:
        cleaned = clean_resource(tag)
        if cleaned:
            resources.append(cleaned)
    for segment in path.strip("/").split("/"):
        if segment.startswith("{"):
            continue
        cleaned = clean_resource(segment)
        if cleaned:
            resources.append(cleaned)
    for name in schema_names:
        cleaned = clean_resource(re.sub(r"^(admin|store)", "", name, flags=re.I))
        if cleaned:
            resources.append(cleaned)
    if not resources and operation_id:
        cleaned = clean_resource(operation_id)
        if cleaned:
            resources.append(cleaned)
    return list(dict.fromkeys(resources))[:8]


def normalize_security(operation: dict[str, Any], spec: dict[str, Any]) -> list[str]:
    security = operation.get("security", spec.get("security", []))
    names: list[str] = []
    if isinstance(security, list):
        for requirement in security:
            if isinstance(requirement, dict):
                names.extend(str(name) for name in requirement)
    if operation.get("x-authenticated") and "authenticated" not in names:
        names.append("authenticated")
    return list(dict.fromkeys(names))


def normalize_spec(name: str, raw_spec: dict[str, Any]) -> tuple[list[NormalizedEndpoint], dict[str, dict[str, Any]], dict[str, dict[str, Any]]]:
    components = raw_spec.get("components", {}) if isinstance(raw_spec.get("components"), dict) else {}
    schemas = components.get("schemas", {}) if isinstance(components.get("schemas"), dict) else {}
    security_schemes = components.get("securitySchemes", {}) if isinstance(components.get("securitySchemes"), dict) else {}
    endpoints: list[NormalizedEndpoint] = []
    paths = raw_spec.get("paths", {}) if isinstance(raw_spec.get("paths"), dict) else {}
    for path, path_item in paths.items():
        if not isinstance(path_item, dict):
            continue
        path_params = path_item.get("parameters", [])
        path_params = path_params if isinstance(path_params, list) else []
        for method, operation in path_item.items():
            if method not in HTTP_METHODS or not isinstance(operation, dict):
                continue
            op_params = operation.get("parameters", [])
            op_params = op_params if isinstance(op_params, list) else []
            params = [normalize_parameter(p) for p in merge_parameters(path_params, op_params)]
            request_body = operation.get("requestBody", {}) if isinstance(operation.get("requestBody"), dict) else {}
            request_schemas = schema_names_from_content(request_body.get("content"))
            response_schemas: list[str] = []
            responses = operation.get("responses", {}) if isinstance(operation.get("responses"), dict) else {}
            for status, response in responses.items():
                if str(status).startswith("2") and isinstance(response, dict):
                    response_schemas.extend(schema_names_from_content(response.get("content")))
            response_schemas = list(dict.fromkeys(response_schemas))
            tags = [str(tag) for tag in operation.get("tags", [])] if isinstance(operation.get("tags"), list) else []
            operation_id = str(operation.get("operationId") or f"{method}_{slugify(path)}")
            op_class, confidence = infer_operation_class(method, path, params, operation)
            schema_names = request_schemas + response_schemas + [p.schema_name for p in params if p.schema_name]
            resources = infer_resources(path, tags, operation_id, [s for s in schema_names if s])
            endpoint_id = f"{name}:{operation_id}"
            endpoints.append(
                NormalizedEndpoint(
                    id=endpoint_id,
                    source=name,
                    method=method.upper(),
                    path=str(path),
                    operation_id=operation_id,
                    tags=tags,
                    summary=str(operation.get("summary", "")),
                    description=str(operation.get("description", "")),
                    params=params,
                    required_params=[p.name for p in params if p.required],
                    request_schemas=request_schemas,
                    response_schemas=response_schemas,
                    security=normalize_security(operation, raw_spec),
                    resources=resources,
                    operation_class=op_class,
                    operation_confidence=confidence,
                )
            )
    return endpoints, schemas, security_schemes


def load_openapi_specs(paths_or_urls: Iterable[str | Path]) -> NormalizedBundle:
    endpoints: list[NormalizedEndpoint] = []
    schemas: dict[str, dict[str, Any]] = {}
    security_schemes: dict[str, dict[str, Any]] = {}
    raw_specs: dict[str, dict[str, Any]] = {}
    resolved_specs: dict[str, dict[str, Any]] = {}
    spec_summaries: list[dict[str, Any]] = []
    for path_or_url in paths_or_urls:
        name, raw_spec = read_spec(path_or_url)
        validation = validate_spec_with_library(raw_spec)
        resolved, prance_resolution = resolve_spec_with_prance(path_or_url, raw_spec)
        raw_specs[name] = raw_spec
        resolved_specs[name] = resolved
        spec_endpoints, spec_schemas, spec_security = normalize_spec(name, raw_spec)
        endpoints.extend(spec_endpoints)
        for schema_name, schema in spec_schemas.items():
            schemas[f"{name}:{schema_name}"] = schema
            schemas.setdefault(schema_name, schema)
        for scheme_name, scheme in spec_security.items():
            security_schemes[f"{name}:{scheme_name}"] = scheme
            security_schemes.setdefault(scheme_name, scheme)
        spec_summaries.append(
            {
                "source": name,
                "title": raw_spec.get("info", {}).get("title"),
                "version": raw_spec.get("info", {}).get("version"),
                "openapi": raw_spec.get("openapi"),
                "paths": len(raw_spec.get("paths", {}) or {}),
                "endpoints": len(spec_endpoints),
                "spec_validation": validation,
                "prance_resolution": prance_resolution,
            }
        )
    repaired_specs, repair_manifest = repair_specs(raw_specs)
    repaired_validation = {
        name: validate_spec_with_library(spec)
        for name, spec in repaired_specs.items()
    }
    repair_counts = repair_manifest.get("repair_counts", {})
    for summary in spec_summaries:
        source = str(summary["source"])
        summary["repair_count"] = int(repair_counts.get(source, 0))
        summary["repaired_validation"] = repaired_validation.get(source, {})
    manifest = {
        "spec_count": len(spec_summaries),
        "specs": spec_summaries,
        "endpoint_count": len(endpoints),
        "schema_count": len(schemas),
        "security_scheme_count": len(security_schemes),
        "openapi_core": build_openapi_core_apps(raw_specs),
        "openapi_core_repaired": build_openapi_core_apps(repaired_specs),
        "repair_counts": repair_counts,
        "repair_policy": repair_manifest.get("policy", "remove_invalid_defaults_only"),
    }
    return NormalizedBundle(
        endpoints=endpoints,
        schemas=schemas,
        security_schemes=security_schemes,
        manifest=manifest,
        raw_specs=raw_specs,
        resolved_specs=resolved_specs,
        repaired_specs=repaired_specs,
        repair_manifest=repair_manifest,
    )


def dataclass_to_dict(value: Any) -> Any:
    if hasattr(value, "__dataclass_fields__"):
        return asdict(value)
    if isinstance(value, list):
        return [dataclass_to_dict(item) for item in value]
    if isinstance(value, dict):
        return {key: dataclass_to_dict(item) for key, item in value.items()}
    return value


def write_normalized_bundle(bundle: NormalizedBundle, out_dir: Path) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)
    if bundle.raw_specs:
        write_spec_artifacts(bundle.raw_specs, bundle.repaired_specs, bundle.repair_manifest, out_dir)
    payload = {
        "manifest": bundle.manifest,
        "endpoints": dataclass_to_dict(bundle.endpoints),
        "schemas": bundle.schemas,
        "security_schemes": bundle.security_schemes,
    }
    (out_dir / "openapi_normalized.json").write_text(json.dumps(payload, indent=2), encoding="utf-8")
    (out_dir / "endpoint_index.json").write_text(
        json.dumps({endpoint.id: dataclass_to_dict(endpoint) for endpoint in bundle.endpoints}, indent=2),
        encoding="utf-8",
    )
    (out_dir / "schema_index.json").write_text(json.dumps(bundle.schemas, indent=2), encoding="utf-8")
    (out_dir / "ingest_manifest.json").write_text(json.dumps(bundle.manifest, indent=2), encoding="utf-8")


def read_normalized_bundle(artifacts_dir: Path) -> NormalizedBundle:
    payload = json.loads((artifacts_dir / "openapi_normalized.json").read_text(encoding="utf-8"))
    endpoints = [
        NormalizedEndpoint(
            **{
                **endpoint,
                "params": [NormalizedParameter(**param) for param in endpoint.get("params", [])],
            }
        )
        for endpoint in payload["endpoints"]
    ]
    return NormalizedBundle(
        endpoints=endpoints,
        schemas=payload.get("schemas", {}),
        security_schemes=payload.get("security_schemes", {}),
        manifest=payload.get("manifest", {}),
    )
