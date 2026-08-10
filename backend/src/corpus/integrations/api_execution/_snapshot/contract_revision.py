from __future__ import annotations

import copy
import hashlib
import json
from dataclasses import dataclass
from datetime import datetime, timezone
from enum import StrEnum
from typing import Any, Iterable, Mapping, MutableMapping, Sequence

from .errors import ContractError


HTTP_METHODS = {"get", "post", "put", "patch", "delete", "head", "options"}


class PatchKind(StrEnum):
    SET_NULLABLE = "set_nullable"
    REMOVE_REQUIRED = "remove_required"
    CUSTOM_SCHEMA = "custom_schema"


@dataclass(frozen=True)
class ContractPatch:
    patch_id: str
    kind: PatchKind
    operation_id: str
    status_code: int
    media_type: str
    instance_path: str
    schema_pointer: str
    field_name: str | None
    observed: str
    declared: str
    proposed: str
    evidence_count: int = 1
    parent_schema_pointer: str | None = None
    before_schema: Mapping[str, Any] | None = None
    replacement_schema: Mapping[str, Any] | None = None
    required_override: bool | None = None
    target_hash: str | None = None
    impact_count: int = 1


@dataclass(frozen=True)
class ContractRevision:
    revision_hash: str
    source_hash: str
    parent_hash: str
    approved_patch_ids: tuple[str, ...]
    approved_by: str
    approved_at: datetime
    document: Mapping[str, Any]


def openapi_document_hash(document: Mapping[str, Any]) -> str:
    return hashlib.sha256(
        json.dumps(document, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()


def propose_response_patches(
    document: Mapping[str, Any],
    *,
    operation_id: str,
    status_code: int,
    media_type: str,
    payload: Any,
) -> tuple[ContractPatch, ...]:
    schema, schema_pointer = _response_schema(
        document,
        operation_id=operation_id,
        status_code=status_code,
        media_type=media_type,
    )
    patches: list[ContractPatch] = []
    _compare(
        document,
        schema,
        schema_pointer,
        payload,
        "",
        operation_id,
        status_code,
        media_type,
        patches,
    )
    unique: dict[tuple[PatchKind, str, str | None], ContractPatch] = {}
    counts: dict[tuple[PatchKind, str, str | None], int] = {}
    for patch in patches:
        key = (patch.kind, patch.schema_pointer, patch.field_name)
        unique[key] = patch
        counts[key] = counts.get(key, 0) + 1
    return tuple(
        _with_evidence_count(unique[key], counts[key])
        for key in sorted(unique, key=lambda value: (value[1], value[0].value, value[2] or ""))
    )


def custom_patch_editor(
    document: Mapping[str, Any], base_patch: ContractPatch
) -> Mapping[str, Any]:
    target, target_pointer, parent_pointer, field_name = _custom_patch_target(
        document, base_patch
    )
    resolved, _ = _resolve_schema(document, target, target_pointer)
    allowed_types = _declared_types(resolved)
    parent = _pointer_get(document, parent_pointer) if parent_pointer else None
    required = (
        field_name in tuple(parent.get("required") or ())
        if field_name and isinstance(parent, Mapping)
        else None
    )
    return {
        "instance_path": base_patch.instance_path,
        "schema_pointer": target_pointer,
        "allowed_types": list(allowed_types),
        "allow_null": _allows_null(target) or _allows_null(resolved),
        "required": required,
        "enum_values": list(resolved.get("enum") or ()),
        "before_schema": copy.deepcopy(dict(target)),
        "impact_count": _schema_impact_count(document, target_pointer),
    }


def custom_patch_base_for_response(
    document: Mapping[str, Any],
    *,
    operation_id: str,
    status_code: int,
    media_type: str,
    instance_path: str,
    observed: str,
) -> ContractPatch:
    schema, schema_pointer = _response_schema(
        document,
        operation_id=operation_id,
        status_code=status_code,
        media_type=media_type,
    )
    target, target_pointer = _locate_instance_schema(
        document, schema, schema_pointer, instance_path
    )
    identity = "|".join(
        ("custom-base", operation_id, str(status_code), media_type, target_pointer)
    )
    return ContractPatch(
        patch_id=hashlib.sha256(identity.encode("utf-8")).hexdigest()[:16],
        kind=PatchKind.SET_NULLABLE,
        operation_id=operation_id,
        status_code=status_code,
        media_type=media_type,
        instance_path=instance_path,
        schema_pointer=target_pointer,
        field_name=None,
        observed=observed,
        declared=json.dumps(target, sort_keys=True, separators=(",", ":")),
        proposed="Author custom schema change",
    )


def create_custom_contract_patch(
    document: Mapping[str, Any],
    base_patch: ContractPatch,
    *,
    allowed_types: Iterable[str],
    allow_null: bool,
    required: bool | None,
    enum_values: Sequence[Any] | None,
) -> ContractPatch:
    supported_types = {"string", "number", "integer", "boolean", "object", "array"}
    selected_types = tuple(dict.fromkeys(str(value) for value in allowed_types))
    if not selected_types or any(value not in supported_types for value in selected_types):
        raise ContractError(
            "custom_types_invalid",
            "Choose at least one supported non-null OpenAPI type.",
        )
    target, target_pointer, parent_pointer, field_name = _custom_patch_target(
        document, base_patch
    )
    resolved, _ = _resolve_schema(document, target, target_pointer)
    replacement = copy.deepcopy(dict(target))
    current_types = _declared_types(resolved)
    dialect = str(document.get("openapi", "3.0"))
    if selected_types != current_types:
        replacement = {
            key: copy.deepcopy(target[key])
            for key in (
                "title",
                "description",
                "deprecated",
                "readOnly",
                "writeOnly",
                "default",
                "example",
                "examples",
            )
            if key in target
        }
        if dialect.startswith("3.1"):
            replacement["type"] = (
                selected_types[0] if len(selected_types) == 1 else list(selected_types)
            )
        elif len(selected_types) == 1:
            replacement["type"] = selected_types[0]
        else:
            replacement["oneOf"] = [{"type": value} for value in selected_types]
    _set_custom_nullability(document, replacement, allow_null=allow_null, dialect=dialect)
    if enum_values is not None:
        if enum_values:
            replacement["enum"] = list(enum_values)
        else:
            replacement.pop("enum", None)
    before_hash = openapi_document_hash(target)
    proposed_parts = [" or ".join(selected_types)]
    proposed_parts.append("null allowed" if allow_null else "null rejected")
    if required is not None:
        proposed_parts.append("required" if required else "optional")
    if enum_values is not None:
        proposed_parts.append(
            f"{len(enum_values)} enum values" if enum_values else "no enum restriction"
        )
    identity = json.dumps(
        {
            "kind": PatchKind.CUSTOM_SCHEMA.value,
            "target": target_pointer,
            "replacement": replacement,
            "required": required,
        },
        sort_keys=True,
        separators=(",", ":"),
    )
    return ContractPatch(
        patch_id=hashlib.sha256(identity.encode("utf-8")).hexdigest()[:16],
        kind=PatchKind.CUSTOM_SCHEMA,
        operation_id=base_patch.operation_id,
        status_code=base_patch.status_code,
        media_type=base_patch.media_type,
        instance_path=base_patch.instance_path,
        schema_pointer=target_pointer,
        field_name=field_name,
        observed=base_patch.observed,
        declared=base_patch.declared,
        proposed="Custom: " + ", ".join(proposed_parts),
        evidence_count=base_patch.evidence_count,
        parent_schema_pointer=parent_pointer,
        before_schema=copy.deepcopy(dict(target)),
        replacement_schema=replacement,
        required_override=required,
        target_hash=before_hash,
        impact_count=_schema_impact_count(document, target_pointer),
    )


def approve_contract_patches(
    document: Mapping[str, Any],
    patches: Sequence[ContractPatch],
    *,
    approved_patch_ids: Iterable[str],
    approved_by: str,
    source_hash: str | None = None,
    parent_hash: str | None = None,
) -> ContractRevision:
    approver = approved_by.strip()
    if not approver:
        raise ContractError("approver_required", "An approval identity is required.")
    approved = set(approved_patch_ids)
    if not approved:
        raise ContractError("patch_approval_required", "At least one patch must be approved.")
    available = {patch.patch_id: patch for patch in patches}
    unknown = approved.difference(available)
    if unknown:
        raise ContractError(
            "patch_unknown",
            "One or more approved patches are not part of the diagnostic proposal.",
        )
    revised = copy.deepcopy(dict(document))
    dialect = str(revised.get("openapi", "3.0"))
    for patch_id in sorted(approved):
        _apply_patch(revised, available[patch_id], dialect=dialect)
    original_hash = source_hash or openapi_document_hash(document)
    parent = parent_hash or openapi_document_hash(document)
    revision_hash = openapi_document_hash(revised)
    if revision_hash == parent:
        raise ContractError(
            "revision_unchanged",
            "The approved patches did not produce a new contract revision.",
        )
    return ContractRevision(
        revision_hash=revision_hash,
        source_hash=original_hash,
        parent_hash=parent,
        approved_patch_ids=tuple(sorted(approved)),
        approved_by=approver,
        approved_at=datetime.now(timezone.utc),
        document=revised,
    )


def _response_schema(
    document: Mapping[str, Any],
    *,
    operation_id: str,
    status_code: int,
    media_type: str,
) -> tuple[Mapping[str, Any], str]:
    for path, path_item in (document.get("paths") or {}).items():
        if not isinstance(path_item, Mapping):
            continue
        for method, operation in path_item.items():
            if method not in HTTP_METHODS or not isinstance(operation, Mapping):
                continue
            if operation.get("operationId") != operation_id:
                continue
            responses = operation.get("responses") or {}
            response_key = _response_key(responses, status_code)
            response = responses.get(response_key)
            if not isinstance(response, Mapping):
                break
            normalized_media = media_type.split(";", 1)[0].strip().lower()
            content = response.get("content") or {}
            selected_key = next(
                (
                    key
                    for key in content
                    if key.split(";", 1)[0].strip().lower() == normalized_media
                ),
                None,
            )
            if selected_key is None:
                break
            schema = (content[selected_key] or {}).get("schema")
            if not isinstance(schema, Mapping):
                break
            pointer = "/paths/{}/{}/responses/{}/content/{}/schema".format(
                _escape_pointer(str(path)),
                method,
                _escape_pointer(str(response_key)),
                _escape_pointer(str(selected_key)),
            )
            return schema, pointer
    raise ContractError(
        "response_schema_missing",
        "The selected operation response schema is unavailable.",
    )


def _response_key(responses: Mapping[str, Any], status_code: int) -> str:
    exact = str(status_code)
    if exact in responses:
        return exact
    wildcard = f"{str(status_code)[0]}XX"
    if wildcard in responses:
        return wildcard
    if "default" in responses:
        return "default"
    raise ContractError(
        "response_status_undeclared",
        "The observed response status is not declared by the operation.",
    )


def _compare(
    document: Mapping[str, Any],
    raw_schema: Mapping[str, Any],
    raw_pointer: str,
    value: Any,
    instance_path: str,
    operation_id: str,
    status_code: int,
    media_type: str,
    patches: list[ContractPatch],
) -> None:
    resolved_schema, resolved_pointer = _resolve_schema(document, raw_schema, raw_pointer)
    if value is None:
        if not _allows_null(raw_schema) and not _allows_null(resolved_schema):
            patches.append(
                _patch(
                    PatchKind.SET_NULLABLE,
                    operation_id,
                    status_code,
                    media_type,
                    instance_path or "/",
                    raw_pointer,
                    None,
                    "null",
                    "non-null",
                    "Allow null",
                )
            )
        return
    for index, branch in enumerate(resolved_schema.get("allOf") or ()):
        if isinstance(branch, Mapping):
            _compare(
                document,
                branch,
                f"{resolved_pointer}/allOf/{index}",
                value,
                instance_path,
                operation_id,
                status_code,
                media_type,
                patches,
            )
    schema_type = resolved_schema.get("type")
    if isinstance(value, Mapping) and (schema_type == "object" or "properties" in resolved_schema):
        required = tuple(resolved_schema.get("required") or ())
        for field in required:
            if field not in value:
                patches.append(
                    _patch(
                        PatchKind.REMOVE_REQUIRED,
                        operation_id,
                        status_code,
                        media_type,
                        _join_instance(instance_path, str(field)),
                        resolved_pointer,
                        str(field),
                        "absent",
                        "required",
                        "Make optional",
                    )
                )
        properties = resolved_schema.get("properties") or {}
        for field, field_value in value.items():
            field_schema = properties.get(field)
            if isinstance(field_schema, Mapping):
                _compare(
                    document,
                    field_schema,
                    f"{resolved_pointer}/properties/{_escape_pointer(str(field))}",
                    field_value,
                    _join_instance(instance_path, str(field)),
                    operation_id,
                    status_code,
                    media_type,
                    patches,
                )
    elif isinstance(value, list) and (schema_type == "array" or "items" in resolved_schema):
        item_schema = resolved_schema.get("items")
        if isinstance(item_schema, Mapping):
            for index, item in enumerate(value):
                _compare(
                    document,
                    item_schema,
                    f"{resolved_pointer}/items",
                    item,
                    _join_instance(instance_path, str(index)),
                    operation_id,
                    status_code,
                    media_type,
                    patches,
                )


def _resolve_schema(
    document: Mapping[str, Any], schema: Mapping[str, Any], pointer: str
) -> tuple[Mapping[str, Any], str]:
    current = schema
    current_pointer = pointer
    seen: set[str] = set()
    while isinstance(current.get("$ref"), str):
        reference = str(current["$ref"])
        if not reference.startswith("#/") or reference in seen:
            break
        seen.add(reference)
        current_pointer = reference[1:]
        resolved = _pointer_get(document, current_pointer)
        if not isinstance(resolved, Mapping):
            break
        current = resolved
    return current, current_pointer


def _apply_patch(document: MutableMapping[str, Any], patch: ContractPatch, *, dialect: str) -> None:
    target = _pointer_get(document, patch.schema_pointer)
    if not isinstance(target, MutableMapping):
        raise ContractError("patch_target_invalid", "A schema patch target is invalid.")
    if patch.kind is PatchKind.REMOVE_REQUIRED:
        required = list(target.get("required") or ())
        if patch.field_name not in required:
            raise ContractError("patch_precondition_failed", "The required field has changed.")
        remaining = [value for value in required if value != patch.field_name]
        if remaining:
            target["required"] = remaining
        else:
            target.pop("required", None)
        return
    if patch.kind is PatchKind.SET_NULLABLE:
        if _allows_null(target):
            raise ContractError("patch_precondition_failed", "The schema already allows null.")
        if dialect.startswith("3.1"):
            schema_type = target.get("type")
            if isinstance(schema_type, str):
                target["type"] = [schema_type, "null"]
            elif isinstance(schema_type, list):
                target["type"] = [*schema_type, "null"]
            elif "$ref" in target:
                reference = target.pop("$ref")
                target["anyOf"] = [{"$ref": reference}, {"type": "null"}]
            else:
                target["anyOf"] = [copy.deepcopy(dict(target)), {"type": "null"}]
        else:
            if "$ref" in target:
                reference = target["$ref"]
                if isinstance(reference, str) and reference.startswith("#/"):
                    referenced = _pointer_get(document, reference[1:])
                    if not isinstance(referenced, Mapping):
                        raise ContractError(
                            "patch_target_invalid",
                            "The referenced nullable schema is unavailable.",
                        )
                    target.clear()
                    target.update(copy.deepcopy(dict(referenced)))
                    target["x-contract-revision-source-ref"] = reference
            target["nullable"] = True
        return
    if patch.kind is PatchKind.CUSTOM_SCHEMA:
        if patch.replacement_schema is None or patch.target_hash is None:
            raise ContractError("patch_target_invalid", "The custom schema change is incomplete.")
        if openapi_document_hash(target) != patch.target_hash:
            raise ContractError("patch_precondition_failed", "The custom schema target has changed.")
        target.clear()
        target.update(copy.deepcopy(dict(patch.replacement_schema)))
        if patch.required_override is not None:
            if not patch.parent_schema_pointer or not patch.field_name:
                raise ContractError(
                    "patch_target_invalid",
                    "The custom required-field target is unavailable.",
                )
            parent = _pointer_get(document, patch.parent_schema_pointer)
            if not isinstance(parent, MutableMapping):
                raise ContractError("patch_target_invalid", "The parent schema is unavailable.")
            required = list(parent.get("required") or ())
            if patch.required_override and patch.field_name not in required:
                parent["required"] = [*required, patch.field_name]
            elif not patch.required_override and patch.field_name in required:
                remaining = [value for value in required if value != patch.field_name]
                if remaining:
                    parent["required"] = remaining
                else:
                    parent.pop("required", None)
        return
    raise ContractError("patch_kind_unsupported", "The schema patch kind is unsupported.")


def _custom_patch_target(
    document: Mapping[str, Any], base_patch: ContractPatch
) -> tuple[Mapping[str, Any], str, str | None, str | None]:
    if base_patch.kind is PatchKind.REMOVE_REQUIRED:
        if not base_patch.field_name:
            raise ContractError("patch_target_invalid", "The required field is unavailable.")
        parent_pointer = base_patch.schema_pointer
        target_pointer = (
            f"{parent_pointer}/properties/{_escape_pointer(base_patch.field_name)}"
        )
        field_name = base_patch.field_name
    else:
        target_pointer = base_patch.schema_pointer
        marker = "/properties/"
        if marker in target_pointer:
            parent_pointer, encoded_field = target_pointer.rsplit(marker, 1)
            field_name = encoded_field.replace("~1", "/").replace("~0", "~")
        else:
            parent_pointer = None
            field_name = base_patch.field_name
    target = _pointer_get(document, target_pointer)
    if not isinstance(target, Mapping):
        raise ContractError("patch_target_invalid", "The custom schema target is unavailable.")
    return target, target_pointer, parent_pointer, field_name


def _locate_instance_schema(
    document: Mapping[str, Any],
    schema: Mapping[str, Any],
    schema_pointer: str,
    instance_path: str,
) -> tuple[Mapping[str, Any], str]:
    current = schema
    pointer = schema_pointer
    raw_parts = instance_path.lstrip("/").split("/") if instance_path != "/" else []
    parts = [value.replace("~1", "/").replace("~0", "~") for value in raw_parts]
    for part in parts:
        resolved, resolved_pointer = _resolve_schema(document, current, pointer)
        if part.isdigit():
            item = _schema_items(document, resolved, resolved_pointer)
            if item is None:
                raise ContractError(
                    "custom_target_ambiguous",
                    f"The array schema for {instance_path} cannot be located safely.",
                )
            current, pointer = item
            continue
        container = _schema_property_container(
            document, resolved, resolved_pointer, part
        )
        if container is None:
            raise ContractError(
                "custom_target_ambiguous",
                f"The field schema for {instance_path} cannot be located safely.",
            )
        object_schema, object_pointer = container
        properties = object_schema.get("properties") or {}
        current = properties[part]
        pointer = f"{object_pointer}/properties/{_escape_pointer(part)}"
    if not isinstance(current, Mapping):
        raise ContractError("custom_target_ambiguous", "The schema target is not an object.")
    return current, pointer


def _schema_property_container(
    document: Mapping[str, Any],
    schema: Mapping[str, Any],
    pointer: str,
    field: str,
) -> tuple[Mapping[str, Any], str] | None:
    resolved, resolved_pointer = _resolve_schema(document, schema, pointer)
    properties = resolved.get("properties") or {}
    if field in properties:
        return resolved, resolved_pointer
    for index, branch in enumerate(resolved.get("allOf") or ()):
        if isinstance(branch, Mapping):
            found = _schema_property_container(
                document, branch, f"{resolved_pointer}/allOf/{index}", field
            )
            if found is not None:
                return found
    return None


def _schema_items(
    document: Mapping[str, Any],
    schema: Mapping[str, Any],
    pointer: str,
) -> tuple[Mapping[str, Any], str] | None:
    resolved, resolved_pointer = _resolve_schema(document, schema, pointer)
    items = resolved.get("items")
    if isinstance(items, Mapping):
        return items, f"{resolved_pointer}/items"
    for index, branch in enumerate(resolved.get("allOf") or ()):
        if isinstance(branch, Mapping):
            found = _schema_items(
                document, branch, f"{resolved_pointer}/allOf/{index}"
            )
            if found is not None:
                return found
    return None


def _declared_types(schema: Mapping[str, Any]) -> tuple[str, ...]:
    value = schema.get("type")
    if isinstance(value, str) and value != "null":
        return (value,)
    if isinstance(value, list):
        return tuple(str(item) for item in value if item != "null")
    branches = schema.get("oneOf") or schema.get("anyOf") or ()
    branch_types = tuple(
        str(branch.get("type"))
        for branch in branches
        if isinstance(branch, Mapping) and branch.get("type") not in (None, "null")
    )
    if branch_types:
        return branch_types
    if "properties" in schema:
        return ("object",)
    if "items" in schema:
        return ("array",)
    raise ContractError(
        "custom_type_ambiguous",
        "The schema type is ambiguous; use the advanced schema editor.",
    )


def _set_custom_nullability(
    document: Mapping[str, Any],
    schema: MutableMapping[str, Any],
    *,
    allow_null: bool,
    dialect: str,
) -> None:
    if dialect.startswith("3.1"):
        schema.pop("nullable", None)
        schema_type = schema.get("type")
        if isinstance(schema_type, str):
            schema["type"] = [schema_type, "null"] if allow_null else schema_type
        elif isinstance(schema_type, list):
            non_null = [value for value in schema_type if value != "null"]
            schema["type"] = [*non_null, "null"] if allow_null else (
                non_null[0] if len(non_null) == 1 else non_null
            )
        elif "$ref" in schema and allow_null:
            reference = schema.pop("$ref")
            schema["anyOf"] = [{"$ref": reference}, {"type": "null"}]
        return
    if allow_null and "$ref" in schema:
        reference = schema["$ref"]
        if isinstance(reference, str) and reference.startswith("#/"):
            referenced = _pointer_get(document, reference[1:])
            if not isinstance(referenced, Mapping):
                raise ContractError("patch_target_invalid", "The referenced schema is unavailable.")
            schema.clear()
            schema.update(copy.deepcopy(dict(referenced)))
            schema["x-contract-revision-source-ref"] = reference
    if "oneOf" in schema and isinstance(schema.get("oneOf"), list):
        branches = copy.deepcopy(list(schema.pop("oneOf")))
        if allow_null and branches and isinstance(branches[-1], MutableMapping):
            branches[-1]["nullable"] = True
        schema["anyOf"] = branches
        schema.pop("nullable", None)
        return
    if "anyOf" in schema and isinstance(schema.get("anyOf"), list):
        branches = copy.deepcopy(list(schema["anyOf"]))
        for branch in branches:
            if isinstance(branch, MutableMapping):
                branch.pop("nullable", None)
        if allow_null and branches and isinstance(branches[-1], MutableMapping):
            branches[-1]["nullable"] = True
        schema["anyOf"] = branches
        schema.pop("nullable", None)
        return
    if allow_null:
        schema["nullable"] = True
    else:
        schema.pop("nullable", None)


def _schema_impact_count(document: Mapping[str, Any], pointer: str) -> int:
    tokens = pointer.strip("/").split("/")
    if len(tokens) < 3 or tokens[:2] != ["components", "schemas"]:
        return 1
    reference = "#/" + "/".join(tokens[:3])

    def count(value: Any) -> int:
        if isinstance(value, Mapping):
            return int(value.get("$ref") == reference) + sum(count(item) for item in value.values())
        if isinstance(value, list):
            return sum(count(item) for item in value)
        return 0

    return max(1, count(document))


def _allows_null(schema: Mapping[str, Any]) -> bool:
    if schema.get("nullable") is True:
        return True
    schema_type = schema.get("type")
    if isinstance(schema_type, list) and "null" in schema_type:
        return True
    for keyword in ("oneOf", "anyOf"):
        if any(
            isinstance(branch, Mapping) and _allows_null(branch)
            for branch in (schema.get(keyword) or ())
        ):
            return True
    return False


def _pointer_get(document: Any, pointer: str) -> Any:
    current = document
    for token in pointer.lstrip("/").split("/") if pointer else ():
        decoded = token.replace("~1", "/").replace("~0", "~")
        current = current[int(decoded)] if isinstance(current, list) else current[decoded]
    return current


def _escape_pointer(value: str) -> str:
    return value.replace("~", "~0").replace("/", "~1")


def _join_instance(path: str, value: str) -> str:
    return f"{path}/{_escape_pointer(value)}" if path else f"/{_escape_pointer(value)}"


def _patch(
    kind: PatchKind,
    operation_id: str,
    status_code: int,
    media_type: str,
    instance_path: str,
    schema_pointer: str,
    field_name: str | None,
    observed: str,
    declared: str,
    proposed: str,
) -> ContractPatch:
    identity = "|".join(
        (kind.value, operation_id, str(status_code), media_type, schema_pointer, field_name or "")
    )
    return ContractPatch(
        patch_id=hashlib.sha256(identity.encode("utf-8")).hexdigest()[:16],
        kind=kind,
        operation_id=operation_id,
        status_code=status_code,
        media_type=media_type,
        instance_path=instance_path,
        schema_pointer=schema_pointer,
        field_name=field_name,
        observed=observed,
        declared=declared,
        proposed=proposed,
    )


def _with_evidence_count(patch: ContractPatch, count: int) -> ContractPatch:
    return ContractPatch(**{**patch.__dict__, "evidence_count": count})
