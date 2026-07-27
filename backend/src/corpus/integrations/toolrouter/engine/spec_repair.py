from __future__ import annotations

import json
from copy import deepcopy
from pathlib import Path
from typing import Any

import yaml
from jsonschema import Draft7Validator
from jsonschema.exceptions import SchemaError, ValidationError


def pointer_escape(value: str) -> str:
    return value.replace("~", "~0").replace("/", "~1")


def json_pointer(path: list[str]) -> str:
    return "/" + "/".join(pointer_escape(item) for item in path)


def is_schema_like(value: dict[str, Any]) -> bool:
    return any(
        key in value
        for key in [
            "type",
            "properties",
            "items",
            "enum",
            "allOf",
            "anyOf",
            "oneOf",
            "$ref",
            "format",
        ]
    )


def validator_schema(schema: dict[str, Any]) -> dict[str, Any]:
    cleaned = deepcopy(schema)
    cleaned.pop("default", None)
    if cleaned.get("nullable") is True and "type" in cleaned:
        schema_type = cleaned["type"]
        if isinstance(schema_type, str):
            cleaned["type"] = [schema_type, "null"]
        elif isinstance(schema_type, list) and "null" not in schema_type:
            cleaned["type"] = [*schema_type, "null"]
    cleaned.pop("nullable", None)
    return cleaned


def default_is_valid(schema: dict[str, Any], value: Any) -> tuple[bool, str]:
    if "$ref" in schema:
        return True, "default validation skipped for unresolved $ref schema"
    try:
        Draft7Validator.check_schema(validator_schema(schema))
        Draft7Validator(validator_schema(schema)).validate(value)
        return True, "valid"
    except ValidationError as exc:
        return False, exc.message
    except SchemaError as exc:
        return True, f"default validation skipped for unsupported schema: {exc.message}"
    except Exception as exc:
        return True, f"default validation skipped: {exc.__class__.__name__}: {exc}"


def repair_invalid_defaults(source: str, spec: dict[str, Any]) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    repaired = deepcopy(spec)
    repairs: list[dict[str, Any]] = []

    def visit(value: Any, path: list[str]) -> None:
        if isinstance(value, dict):
            if "default" in value and is_schema_like(value):
                old_value = value["default"]
                valid, reason = default_is_valid(value, old_value)
                if not valid:
                    del value["default"]
                    repairs.append(
                        {
                            "source": source,
                            "json_pointer": json_pointer([*path, "default"]),
                            "old_value": old_value,
                            "new_value": None,
                            "action": "remove_invalid_default",
                            "reason": f"default is invalid for sibling schema: {reason}",
                        }
                    )
            for key, child in list(value.items()):
                visit(child, [*path, str(key)])
        elif isinstance(value, list):
            for index, child in enumerate(value):
                visit(child, [*path, str(index)])

    visit(repaired, [])
    return repaired, repairs


def repair_specs(raw_specs: dict[str, dict[str, Any]]) -> tuple[dict[str, dict[str, Any]], dict[str, Any]]:
    repaired_specs: dict[str, dict[str, Any]] = {}
    repairs: list[dict[str, Any]] = []
    for source, spec in raw_specs.items():
        repaired, source_repairs = repair_invalid_defaults(source, spec)
        repaired_specs[source] = repaired
        repairs.extend(source_repairs)
    return repaired_specs, {
        "version": 1,
        "policy": "remove_invalid_defaults_only",
        "repairs": repairs,
        "repair_counts": {
            source: sum(1 for repair in repairs if repair["source"] == source)
            for source in raw_specs
        },
    }


def write_spec_artifacts(
    raw_specs: dict[str, dict[str, Any]],
    repaired_specs: dict[str, dict[str, Any]],
    repair_manifest: dict[str, Any],
    out_dir: Path,
) -> None:
    raw_dir = out_dir / "raw_openapi"
    repaired_dir = out_dir / "repaired_openapi"
    raw_dir.mkdir(parents=True, exist_ok=True)
    repaired_dir.mkdir(parents=True, exist_ok=True)
    for source, spec in raw_specs.items():
        (raw_dir / f"{source}.yaml").write_text(yaml.safe_dump(spec, sort_keys=False), encoding="utf-8")
    for source, spec in repaired_specs.items():
        (repaired_dir / f"{source}.yaml").write_text(yaml.safe_dump(spec, sort_keys=False), encoding="utf-8")
    (out_dir / "repair_manifest.json").write_text(json.dumps(repair_manifest, indent=2), encoding="utf-8")


def read_repair_manifest(artifacts_dir: Path) -> dict[str, Any]:
    path = artifacts_dir / "repair_manifest.json"
    if not path.exists():
        return {"version": 1, "policy": "remove_invalid_defaults_only", "repairs": [], "repair_counts": {}}
    return json.loads(path.read_text(encoding="utf-8"))


def read_repaired_specs(artifacts_dir: Path) -> dict[str, dict[str, Any]]:
    repaired_dir = artifacts_dir / "repaired_openapi"
    if not repaired_dir.exists():
        return {}
    specs: dict[str, dict[str, Any]] = {}
    for path in sorted(repaired_dir.glob("*.yaml")):
        payload = yaml.safe_load(path.read_text(encoding="utf-8"))
        if isinstance(payload, dict):
            specs[path.stem] = payload
    return specs
