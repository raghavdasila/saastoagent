from __future__ import annotations

import json
import re
from collections import defaultdict, deque
from dataclasses import dataclass, field
from typing import Any

from .openapi_loader import NormalizedBundle, NormalizedEndpoint, schema_name_from_ref


COMPOSITION_KEYS = ("allOf", "oneOf", "anyOf")
SCALAR_CONSTRAINT_KEYS = (
    "enum",
    "const",
    "default",
    "example",
    "minimum",
    "maximum",
    "exclusiveMinimum",
    "exclusiveMaximum",
    "multipleOf",
    "minLength",
    "maxLength",
    "pattern",
    "minItems",
    "maxItems",
    "uniqueItems",
    "nullable",
)


@dataclass(frozen=True)
class ScalarFieldDescriptor:
    name: str
    normalized_name: str
    json_pointer: str
    schema_type: str
    schema_format: str
    required: bool
    read_only: bool
    write_only: bool
    description: str
    constraints: dict[str, Any] = field(default_factory=dict)

    def signature(self) -> str:
        return json.dumps(
            {
                "name": self.normalized_name,
                "type": self.schema_type,
                "format": self.schema_format,
                "required": self.required,
                "read_only": self.read_only,
                "write_only": self.write_only,
                "constraints": self.constraints,
            },
            sort_keys=True,
            separators=(",", ":"),
            default=str,
        )


@dataclass(frozen=True)
class SchemaRelation:
    source_schema_id: str
    target_schema_id: str | None
    relation_type: str
    role: str
    cardinality: str
    json_pointer: str
    raw_ref: str | None
    required: bool
    status: str

    def signature(self, schemas: dict[str, "CanonicalSchema"]) -> str:
        target = schemas.get(self.target_schema_id or "")
        target_stem = target.semantic_stem if target is not None else "unresolved"
        return json.dumps(
            {
                "relation": self.relation_type,
                "role": normalize_identifier(self.role),
                "cardinality": self.cardinality,
                "required": self.required,
                "target_stem": target_stem,
            },
            sort_keys=True,
            separators=(",", ":"),
        )


@dataclass(frozen=True)
class CanonicalSchema:
    schema_id: str
    node_type: str
    source: str
    name: str
    semantic_stem: str
    json_pointer: str
    origin_component_id: str
    aliases: tuple[str, ...]
    description: str
    raw_schema: dict[str, Any]
    scalar_fields: tuple[ScalarFieldDescriptor, ...] = ()
    structural_signature: tuple[str, ...] = ()


@dataclass(frozen=True)
class SchemaWarning:
    code: str
    message: str
    schema_id: str | None = None
    json_pointer: str | None = None
    raw_ref: str | None = None
    candidates: tuple[str, ...] = ()


@dataclass(frozen=True)
class ShapeProjection:
    projection_schema_id: str
    full_schema_id: str


@dataclass
class SemanticSchemaAnalysis:
    schemas: dict[str, CanonicalSchema]
    relations: tuple[SchemaRelation, ...]
    root_schema_ids_by_endpoint: dict[str, dict[str, tuple[str, ...]]]
    component_aliases: dict[str, tuple[str, ...]]
    unreachable_component_ids: tuple[str, ...]
    equivalent_shape_groups: tuple[tuple[str, ...], ...]
    projection_relations: tuple[ShapeProjection, ...]
    ambiguous_equal_shape_groups: tuple[tuple[str, ...], ...]
    warnings: tuple[SchemaWarning, ...]
    inventory: dict[str, int]

    @property
    def reachable_component_ids(self) -> tuple[str, ...]:
        return tuple(
            schema_id
            for schema_id, schema in self.schemas.items()
            if schema.node_type == "api_schema"
        )


def normalize_identifier(value: str) -> str:
    spaced = re.sub(r"([a-z0-9])([A-Z])", r"\1_\2", str(value or ""))
    return re.sub(r"[^a-zA-Z0-9]+", "_", spaced).strip("_").casefold()


def semantic_stem(value: str) -> str:
    tokens = [token for token in normalize_identifier(value).split("_") if token]
    removable = {
        "admin",
        "api",
        "base",
        "create",
        "delete",
        "get",
        "input",
        "list",
        "output",
        "patch",
        "payload",
        "post",
        "put",
        "request",
        "response",
        "store",
        "update",
        "upsert",
    }
    kept = [token for token in tokens if token not in removable]
    return "_".join(kept or tokens) or "unknown"


def _json_pointer_token(value: str) -> str:
    return str(value).replace("~", "~0").replace("/", "~1")


def _constraint_values(schema: dict[str, Any]) -> dict[str, Any]:
    return {key: schema[key] for key in SCALAR_CONSTRAINT_KEYS if key in schema}


def _schema_type(schema: dict[str, Any]) -> str:
    raw_type = schema.get("type")
    if isinstance(raw_type, list):
        return "|".join(sorted(str(item) for item in raw_type))
    if raw_type:
        return str(raw_type)
    if "enum" in schema:
        return "enum"
    return "unknown"


def _is_structural_schema(schema: dict[str, Any]) -> bool:
    return bool(
        isinstance(schema.get("$ref"), str)
        or isinstance(schema.get("properties"), dict)
        or schema.get("type") == "object"
        or any(isinstance(schema.get(key), list) for key in COMPOSITION_KEYS)
        or "not" in schema
        or isinstance(schema.get("additionalProperties"), dict)
    )


def _sources(bundle: NormalizedBundle) -> tuple[str, ...]:
    sources = {endpoint.source for endpoint in bundle.endpoints if endpoint.source}
    manifest_specs = bundle.manifest.get("specs", []) if isinstance(bundle.manifest, dict) else []
    if isinstance(manifest_specs, list):
        for item in manifest_specs:
            if isinstance(item, dict) and item.get("source"):
                sources.add(str(item["source"]))
    return tuple(sorted(sources))


def _component_registry(
    bundle: NormalizedBundle,
) -> tuple[dict[str, CanonicalSchema], dict[str, tuple[str, ...]], list[SchemaWarning]]:
    sources = _sources(bundle)
    registry: dict[str, CanonicalSchema] = {}
    aliases_by_id: dict[str, set[str]] = defaultdict(set)
    warnings: list[SchemaWarning] = []
    for key, raw_schema in bundle.schemas.items():
        if not isinstance(raw_schema, dict):
            continue
        matched_source = next((source for source in sources if key.startswith(f"{source}:")), None)
        if matched_source is None:
            continue
        name = key[len(matched_source) + 1 :]
        if not name:
            continue
        canonical_id = f"{matched_source}:{name}"
        aliases_by_id[canonical_id].add(key)
        registry[canonical_id] = CanonicalSchema(
            schema_id=canonical_id,
            node_type="api_schema",
            source=matched_source,
            name=name,
            semantic_stem=semantic_stem(name),
            json_pointer=f"#/components/schemas/{_json_pointer_token(name)}",
            origin_component_id=canonical_id,
            aliases=(),
            description=str(raw_schema.get("description", "")),
            raw_schema=raw_schema,
        )

    for key, raw_schema in bundle.schemas.items():
        if not isinstance(raw_schema, dict):
            continue
        if any(key.startswith(f"{source}:") for source in sources):
            continue
        candidates = [schema_id for schema_id, schema in registry.items() if schema.name == key]
        if candidates:
            for candidate in candidates:
                aliases_by_id[candidate].add(key)
            continue
        canonical_id = f"bundle:{key}"
        aliases_by_id[canonical_id].add(key)
        registry[canonical_id] = CanonicalSchema(
            schema_id=canonical_id,
            node_type="api_schema",
            source="bundle",
            name=key,
            semantic_stem=semantic_stem(key),
            json_pointer=f"#/components/schemas/{_json_pointer_token(key)}",
            origin_component_id=canonical_id,
            aliases=(),
            description=str(raw_schema.get("description", "")),
            raw_schema=raw_schema,
        )
        if len(sources) > 1:
            warnings.append(
                SchemaWarning(
                    code="source_provenance_missing",
                    message=(
                        f"Schema {key!r} has no source-qualified alias; it remains in the explicit bundle namespace."
                    ),
                    schema_id=canonical_id,
                )
            )

    alias_map: dict[str, set[str]] = defaultdict(set)
    for schema_id, schema in registry.items():
        aliases_by_id[schema_id].add(schema_id)
        aliases_by_id[schema_id].add(schema.name)
        for alias in aliases_by_id[schema_id]:
            alias_map[alias].add(schema_id)

    finalized: dict[str, CanonicalSchema] = {}
    for schema_id, schema in registry.items():
        finalized[schema_id] = CanonicalSchema(
            **{
                **schema.__dict__,
                "aliases": tuple(sorted(aliases_by_id[schema_id])),
            }
        )
    return finalized, {key: tuple(sorted(value)) for key, value in alias_map.items()}, warnings


def _resolve_component(
    source: str,
    name: str,
    registry: dict[str, CanonicalSchema],
    aliases: dict[str, tuple[str, ...]],
) -> tuple[str | None, tuple[str, ...]]:
    source_id = f"{source}:{name}"
    if source_id in registry:
        return source_id, (source_id,)
    bundle_id = f"bundle:{name}"
    if bundle_id in registry:
        return bundle_id, (bundle_id,)
    candidates = aliases.get(name, ())
    if len(candidates) == 1:
        return candidates[0], candidates
    return None, candidates


def _resolve_ref(
    source: str,
    raw_ref: str,
    registry: dict[str, CanonicalSchema],
    aliases: dict[str, tuple[str, ...]],
) -> tuple[str | None, tuple[str, ...], str | None]:
    if not raw_ref.startswith("#"):
        return None, (), "external_ref_unresolved"
    name = schema_name_from_ref(raw_ref)
    if not name:
        return None, (), "invalid_ref"
    resolved, candidates = _resolve_component(source, name, registry, aliases)
    if resolved is None and len(candidates) > 1:
        return None, candidates, "ambiguous_ref"
    if resolved is None:
        return None, (), "internal_ref_unresolved"
    return resolved, candidates, None


def _root_schema_names(endpoint: NormalizedEndpoint) -> tuple[tuple[str, ...], tuple[str, ...]]:
    return tuple(dict.fromkeys(endpoint.request_schemas)), tuple(dict.fromkeys(endpoint.response_schemas))


def analyze_semantic_schemas(bundle: NormalizedBundle) -> SemanticSchemaAnalysis:
    """Build a source-aware, endpoint-rooted schema graph without global field identities."""

    registry, aliases, warnings = _component_registry(bundle)
    root_map: dict[str, dict[str, tuple[str, ...]]] = {}
    reachable_component_ids: set[str] = set()
    queue: deque[str] = deque()

    for endpoint in bundle.endpoints:
        directions: dict[str, tuple[str, ...]] = {}
        request_names, response_names = _root_schema_names(endpoint)
        for direction, names in (("request", request_names), ("response", response_names)):
            resolved_ids: list[str] = []
            for name in names:
                resolved, candidates = _resolve_component(endpoint.source, name, registry, aliases)
                if resolved is None:
                    code = "ambiguous_endpoint_root" if len(candidates) > 1 else "endpoint_root_unresolved"
                    warnings.append(
                        SchemaWarning(
                            code=code,
                            message=f"Could not resolve {direction} schema {name!r} for endpoint {endpoint.id}.",
                            schema_id=None,
                            candidates=candidates,
                        )
                    )
                    continue
                resolved_ids.append(resolved)
                if resolved not in reachable_component_ids:
                    reachable_component_ids.add(resolved)
                    queue.append(resolved)
            directions[direction] = tuple(resolved_ids)
        root_map[endpoint.id] = directions

    working_schemas: dict[str, CanonicalSchema] = {}
    relations: list[SchemaRelation] = []
    processed: set[str] = set()

    def register_inline(parent: CanonicalSchema, pointer: str, raw_schema: dict[str, Any]) -> str:
        origin_pointer = registry[parent.origin_component_id].json_pointer
        relative_pointer = pointer[len(origin_pointer) :] if pointer.startswith(origin_pointer) else pointer
        relative_pointer = relative_pointer if relative_pointer.startswith("/") else f"/{relative_pointer}"
        inline_id = f"{parent.origin_component_id}#{relative_pointer}"
        if inline_id not in working_schemas:
            path_name = relative_pointer.replace("/properties/", ".").replace("/items", "[]").strip("/")
            working_schemas[inline_id] = CanonicalSchema(
                schema_id=inline_id,
                node_type="api_inline_shape",
                source=parent.source,
                name=f"{registry[parent.origin_component_id].name}.{path_name}" if parent.origin_component_id in registry else path_name,
                semantic_stem=semantic_stem(pointer.split("/")[-1] or parent.name),
                json_pointer=pointer,
                origin_component_id=parent.origin_component_id,
                aliases=(),
                description=str(raw_schema.get("description", "")),
                raw_schema=raw_schema,
            )
            queue.append(inline_id)
        return inline_id

    def append_relation(
        source_schema: CanonicalSchema,
        *,
        target_schema_id: str | None,
        relation_type: str,
        role: str,
        cardinality: str,
        pointer: str,
        raw_ref: str | None,
        required: bool,
        status: str,
    ) -> None:
        relations.append(
            SchemaRelation(
                source_schema_id=source_schema.schema_id,
                target_schema_id=target_schema_id,
                relation_type=relation_type,
                role=role,
                cardinality=cardinality,
                json_pointer=pointer,
                raw_ref=raw_ref,
                required=required,
                status=status,
            )
        )
        if target_schema_id in registry and target_schema_id not in reachable_component_ids:
            reachable_component_ids.add(target_schema_id)
            queue.append(target_schema_id)

    def resolve_and_append(
        source_schema: CanonicalSchema,
        *,
        raw_ref: str,
        relation_type: str,
        role: str,
        cardinality: str,
        pointer: str,
        required: bool,
    ) -> None:
        target, candidates, error = _resolve_ref(source_schema.source, raw_ref, registry, aliases)
        append_relation(
            source_schema,
            target_schema_id=target,
            relation_type=relation_type,
            role=role,
            cardinality=cardinality,
            pointer=pointer,
            raw_ref=raw_ref,
            required=required,
            status="resolved" if target else "unresolved",
        )
        if error:
            warnings.append(
                SchemaWarning(
                    code=error,
                    message=f"Could not resolve reference {raw_ref!r} from {source_schema.schema_id} at {pointer}.",
                    schema_id=source_schema.schema_id,
                    json_pointer=pointer,
                    raw_ref=raw_ref,
                    candidates=candidates,
                )
            )

    while queue:
        schema_id = queue.popleft()
        if schema_id in processed:
            continue
        if schema_id in registry:
            working_schemas[schema_id] = registry[schema_id]
        current = working_schemas.get(schema_id)
        if current is None:
            raise ValueError(f"Reachability queue referenced an unknown schema: {schema_id}")
        processed.add(schema_id)
        raw = current.raw_schema
        scalar_fields: list[ScalarFieldDescriptor] = []
        required_fields = {str(item) for item in raw.get("required", []) if isinstance(item, str)}

        direct_ref = raw.get("$ref")
        if isinstance(direct_ref, str):
            resolve_and_append(
                current,
                raw_ref=direct_ref,
                relation_type="references",
                role="$self",
                cardinality="one",
                pointer=current.json_pointer,
                required=True,
            )

        properties = raw.get("properties", {}) if isinstance(raw.get("properties"), dict) else {}
        for field_name, field_schema in properties.items():
            if not isinstance(field_schema, dict):
                warnings.append(
                    SchemaWarning(
                        code="invalid_property_schema",
                        message=f"Property {field_name!r} is not an object and was not materialized.",
                        schema_id=current.schema_id,
                        json_pointer=f"{current.json_pointer}/properties/{_json_pointer_token(field_name)}",
                    )
                )
                continue
            field_name = str(field_name)
            pointer = f"{current.json_pointer}/properties/{_json_pointer_token(field_name)}"
            is_required = field_name in required_fields
            direct_field_ref = field_schema.get("$ref")
            if isinstance(direct_field_ref, str):
                resolve_and_append(
                    current,
                    raw_ref=direct_field_ref,
                    relation_type="references",
                    role=field_name,
                    cardinality="one",
                    pointer=pointer,
                    required=is_required,
                )
                continue

            if field_schema.get("type") == "array" or isinstance(field_schema.get("items"), dict):
                items = field_schema.get("items", {})
                items_pointer = f"{pointer}/items"
                if isinstance(items, dict) and isinstance(items.get("$ref"), str):
                    resolve_and_append(
                        current,
                        raw_ref=str(items["$ref"]),
                        relation_type="contains_many",
                        role=field_name,
                        cardinality="many",
                        pointer=items_pointer,
                        required=is_required,
                    )
                elif isinstance(items, dict) and _is_structural_schema(items):
                    inline_id = register_inline(current, items_pointer, items)
                    append_relation(
                        current,
                        target_schema_id=inline_id,
                        relation_type="contains_many",
                        role=field_name,
                        cardinality="many",
                        pointer=items_pointer,
                        raw_ref=None,
                        required=is_required,
                        status="resolved",
                    )
                else:
                    item_type = _schema_type(items) if isinstance(items, dict) else "unknown"
                    constraints = _constraint_values(field_schema)
                    constraints["items_type"] = item_type
                    if isinstance(items, dict) and items.get("format"):
                        constraints["items_format"] = str(items["format"])
                    scalar_fields.append(
                        ScalarFieldDescriptor(
                            name=field_name,
                            normalized_name=normalize_identifier(field_name),
                            json_pointer=pointer,
                            schema_type="array",
                            schema_format=str(field_schema.get("format", "")),
                            required=is_required,
                            read_only=bool(field_schema.get("readOnly", False)),
                            write_only=bool(field_schema.get("writeOnly", False)),
                            description=str(field_schema.get("description", "")),
                            constraints=constraints,
                        )
                    )
                continue

            if _is_structural_schema(field_schema):
                inline_id = register_inline(current, pointer, field_schema)
                append_relation(
                    current,
                    target_schema_id=inline_id,
                    relation_type="contains_object",
                    role=field_name,
                    cardinality="one",
                    pointer=pointer,
                    raw_ref=None,
                    required=is_required,
                    status="resolved",
                )
                continue

            scalar_fields.append(
                ScalarFieldDescriptor(
                    name=field_name,
                    normalized_name=normalize_identifier(field_name),
                    json_pointer=pointer,
                    schema_type=_schema_type(field_schema),
                    schema_format=str(field_schema.get("format", "")),
                    required=is_required,
                    read_only=bool(field_schema.get("readOnly", False)),
                    write_only=bool(field_schema.get("writeOnly", False)),
                    description=str(field_schema.get("description", "")),
                    constraints=_constraint_values(field_schema),
                )
            )

        if raw.get("type") == "array" and isinstance(raw.get("items"), dict):
            items = raw["items"]
            pointer = f"{current.json_pointer}/items"
            if isinstance(items.get("$ref"), str):
                resolve_and_append(
                    current,
                    raw_ref=str(items["$ref"]),
                    relation_type="contains_many",
                    role="$items",
                    cardinality="many",
                    pointer=pointer,
                    required=True,
                )
            elif _is_structural_schema(items):
                inline_id = register_inline(current, pointer, items)
                append_relation(
                    current,
                    target_schema_id=inline_id,
                    relation_type="contains_many",
                    role="$items",
                    cardinality="many",
                    pointer=pointer,
                    raw_ref=None,
                    required=True,
                    status="resolved",
                )
            else:
                constraints = _constraint_values(raw)
                constraints["items_type"] = _schema_type(items)
                if items.get("format"):
                    constraints["items_format"] = str(items["format"])
                scalar_fields.append(
                    ScalarFieldDescriptor(
                        name="$items",
                        normalized_name="items",
                        json_pointer=pointer,
                        schema_type="array",
                        schema_format=str(raw.get("format", "")),
                        required=True,
                        read_only=bool(raw.get("readOnly", False)),
                        write_only=bool(raw.get("writeOnly", False)),
                        description=str(raw.get("description", "")),
                        constraints=constraints,
                    )
                )

        for composition_key in COMPOSITION_KEYS:
            branches = raw.get(composition_key, [])
            if not isinstance(branches, list):
                continue
            relation_type = {
                "allOf": "all_of",
                "oneOf": "one_of",
                "anyOf": "any_of",
            }[composition_key]
            for index, branch in enumerate(branches):
                if not isinstance(branch, dict):
                    continue
                pointer = f"{current.json_pointer}/{composition_key}/{index}"
                role = f"{composition_key}[{index}]"
                if isinstance(branch.get("$ref"), str):
                    resolve_and_append(
                        current,
                        raw_ref=str(branch["$ref"]),
                        relation_type=relation_type,
                        role=role,
                        cardinality="branch",
                        pointer=pointer,
                        required=True,
                    )
                else:
                    inline_id = register_inline(current, pointer, branch)
                    append_relation(
                        current,
                        target_schema_id=inline_id,
                        relation_type=relation_type,
                        role=role,
                        cardinality="branch",
                        pointer=pointer,
                        raw_ref=None,
                        required=True,
                        status="resolved",
                    )

        if isinstance(raw.get("not"), dict):
            branch = raw["not"]
            pointer = f"{current.json_pointer}/not"
            if isinstance(branch.get("$ref"), str):
                resolve_and_append(
                    current,
                    raw_ref=str(branch["$ref"]),
                    relation_type="not",
                    role="not",
                    cardinality="branch",
                    pointer=pointer,
                    required=True,
                )
            else:
                inline_id = register_inline(current, pointer, branch)
                append_relation(
                    current,
                    target_schema_id=inline_id,
                    relation_type="not",
                    role="not",
                    cardinality="branch",
                    pointer=pointer,
                    raw_ref=None,
                    required=True,
                    status="resolved",
                )

        additional = raw.get("additionalProperties")
        if isinstance(additional, dict):
            pointer = f"{current.json_pointer}/additionalProperties"
            if isinstance(additional.get("$ref"), str):
                resolve_and_append(
                    current,
                    raw_ref=str(additional["$ref"]),
                    relation_type="additional_properties",
                    role="$values",
                    cardinality="map",
                    pointer=pointer,
                    required=False,
                )
            elif _is_structural_schema(additional):
                inline_id = register_inline(current, pointer, additional)
                append_relation(
                    current,
                    target_schema_id=inline_id,
                    relation_type="additional_properties",
                    role="$values",
                    cardinality="map",
                    pointer=pointer,
                    raw_ref=None,
                    required=False,
                    status="resolved",
                )
            else:
                scalar_fields.append(
                    ScalarFieldDescriptor(
                        name="$values",
                        normalized_name="values",
                        json_pointer=pointer,
                        schema_type="map",
                        schema_format="",
                        required=False,
                        read_only=False,
                        write_only=False,
                        description=str(additional.get("description", "")),
                        constraints={
                            "value_type": _schema_type(additional),
                            **(
                                {"value_format": str(additional["format"])}
                                if additional.get("format")
                                else {}
                            ),
                        },
                    )
                )

        if not properties and not _is_structural_schema(raw) and raw.get("type") not in (None, "object", "array"):
            scalar_fields.append(
                ScalarFieldDescriptor(
                    name="$value",
                    normalized_name="value",
                    json_pointer=current.json_pointer,
                    schema_type=_schema_type(raw),
                    schema_format=str(raw.get("format", "")),
                    required=True,
                    read_only=bool(raw.get("readOnly", False)),
                    write_only=bool(raw.get("writeOnly", False)),
                    description=str(raw.get("description", "")),
                    constraints=_constraint_values(raw),
                )
            )

        working_schemas[current.schema_id] = CanonicalSchema(
            **{
                **current.__dict__,
                "scalar_fields": tuple(scalar_fields),
            }
        )

    outgoing: dict[str, list[SchemaRelation]] = defaultdict(list)
    for relation in relations:
        outgoing[relation.source_schema_id].append(relation)

    for schema_id, schema in list(working_schemas.items()):
        feature_signatures = [f"field:{field.signature()}" for field in schema.scalar_fields]
        feature_signatures.extend(
            f"relation:{relation.signature(working_schemas)}" for relation in outgoing.get(schema_id, [])
        )
        working_schemas[schema_id] = CanonicalSchema(
            **{
                **schema.__dict__,
                "structural_signature": tuple(sorted(feature_signatures)),
            }
        )

    exact_groups: dict[tuple[str, ...], list[str]] = defaultdict(list)
    for schema_id, schema in working_schemas.items():
        if len(schema.structural_signature) >= 2:
            exact_groups[schema.structural_signature].append(schema_id)

    equivalent_groups: list[tuple[str, ...]] = []
    ambiguous_groups: list[tuple[str, ...]] = []
    for group in exact_groups.values():
        if len(group) < 2:
            continue
        stems = {working_schemas[schema_id].semantic_stem for schema_id in group}
        sorted_group = tuple(sorted(group))
        if len(stems) == 1:
            equivalent_groups.append(sorted_group)
        else:
            ambiguous_groups.append(sorted_group)
            warnings.append(
                SchemaWarning(
                    code="ambiguous_equal_shape",
                    message="Structurally equal schemas have different semantic names; no identity edge was created.",
                    candidates=sorted_group,
                )
            )

    by_stem: dict[str, list[CanonicalSchema]] = defaultdict(list)
    for schema in working_schemas.values():
        if schema.structural_signature:
            by_stem[schema.semantic_stem].append(schema)
    projections: set[tuple[str, str]] = set()
    for schemas in by_stem.values():
        for candidate in schemas:
            candidate_features = set(candidate.structural_signature)
            for full in schemas:
                if candidate.schema_id == full.schema_id:
                    continue
                full_features = set(full.structural_signature)
                if candidate_features < full_features:
                    projections.add((candidate.schema_id, full.schema_id))

    unreachable = tuple(sorted(set(registry) - reachable_component_ids))
    unresolved_count = sum(1 for relation in relations if relation.status == "unresolved")
    inventory = {
        "input_schema_entries": len(bundle.schemas),
        "canonical_component_schemas": len(registry),
        "collapsed_alias_entries": max(0, len(bundle.schemas) - len(registry)),
        "endpoint_roots": sum(
            len(ids)
            for directions in root_map.values()
            for ids in directions.values()
        ),
        "reachable_component_schemas": len(reachable_component_ids),
        "reachable_inline_shapes": sum(
            1 for schema in working_schemas.values() if schema.node_type == "api_inline_shape"
        ),
        "unreachable_component_schemas": len(unreachable),
        "scalar_field_descriptors": sum(len(schema.scalar_fields) for schema in working_schemas.values()),
        "resolved_relations": len(relations) - unresolved_count,
        "unresolved_relations": unresolved_count,
        "equivalent_shape_groups": len(equivalent_groups),
        "projection_relations": len(projections),
        "ambiguous_equal_shape_groups": len(ambiguous_groups),
        "warnings": len(warnings),
    }

    return SemanticSchemaAnalysis(
        schemas=working_schemas,
        relations=tuple(relations),
        root_schema_ids_by_endpoint=root_map,
        component_aliases=aliases,
        unreachable_component_ids=unreachable,
        equivalent_shape_groups=tuple(sorted(equivalent_groups)),
        projection_relations=tuple(
            ShapeProjection(projection_schema_id=source, full_schema_id=target)
            for source, target in sorted(projections)
        ),
        ambiguous_equal_shape_groups=tuple(sorted(ambiguous_groups)),
        warnings=tuple(warnings),
        inventory=inventory,
    )
