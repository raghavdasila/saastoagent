from __future__ import annotations

import json
import re
from dataclasses import asdict, dataclass, field
from typing import Any, Callable

from .openapi_loader import NormalizedBundle, NormalizedEndpoint, slugify
from .semantic_schema_graph import (
    CanonicalSchema,
    SchemaRelation,
    SemanticSchemaAnalysis,
    analyze_semantic_schemas,
    semantic_stem,
)


EDGE_STATUSES = {"observed", "derived", "inferred"}
GraphTraceCallback = Callable[[dict[str, Any]], None]


@dataclass(frozen=True)
class SemanticEvidence:
    source: str
    field: str
    value: str


@dataclass(frozen=True)
class SemanticNode:
    id: str
    node_type: str
    label: str
    text: str
    endpoint_id: str | None = None
    facets: dict[str, Any] = field(default_factory=dict)
    evidence: list[SemanticEvidence] = field(default_factory=list)


@dataclass(frozen=True)
class SemanticEdge:
    source: str
    target: str
    type: str
    confidence: float
    status: str
    evidence: list[SemanticEvidence]
    facets: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class SemanticNodeCard:
    card_id: str
    node_id: str
    node_type: str
    endpoint_id: str | None
    title: str
    body: str
    facets: dict[str, Any]
    evidence: list[SemanticEvidence]

    def embedding_text(self) -> str:
        facet_text = " ".join(f"{key} {value}" for key, value in sorted(self.facets.items()))
        evidence_text = " ".join(item.value for item in self.evidence)
        return " ".join([self.node_type, self.title, self.body, facet_text, evidence_text]).strip()


@dataclass(frozen=True)
class SemanticGraph:
    nodes: list[SemanticNode]
    edges: list[SemanticEdge]
    cards: list[SemanticNodeCard]
    metadata: dict[str, Any] = field(default_factory=dict)

    @property
    def nodes_by_id(self) -> dict[str, SemanticNode]:
        return {node.id: node for node in self.nodes}


def _emit_trace(trace_callback: GraphTraceCallback | None, event: dict[str, Any]) -> None:
    if trace_callback is not None:
        trace_callback(event)


def _edge_key(edge: SemanticEdge) -> str:
    return f"{edge.source}|{edge.type}|{edge.target}"


def _node_update_payload(before: SemanticNode, after: SemanticNode) -> dict[str, Any]:
    before_evidence = {(item.source, item.field, item.value) for item in before.evidence}
    evidence_added = [
        asdict(item)
        for item in after.evidence
        if (item.source, item.field, item.value) not in before_evidence
    ]
    facets_changed = {
        key: value
        for key, value in after.facets.items()
        if before.facets.get(key) != value
    }
    if after.text == before.text:
        text_fragment_added = ""
    elif after.text.startswith(before.text):
        text_fragment_added = after.text[len(before.text) :].strip()
    else:
        text_fragment_added = after.text
    return {
        "node_id": after.id,
        "text_fragment_added": text_fragment_added,
        "facets_changed": facets_changed,
        "evidence_added": evidence_added,
        "endpoint_id_changed": before.endpoint_id != after.endpoint_id,
    }


def _evidence(source: str, field: str, value: Any) -> SemanticEvidence:
    return SemanticEvidence(source=source, field=field, value=str(value or ""))


def _operation_node_id(endpoint_id: str) -> str:
    return f"api_operation:{endpoint_id}"


def _shape_node_id(endpoint_id: str, direction: str, schema_name: str) -> str:
    return f"api_shape:{endpoint_id}:{direction}:{schema_name}"


def _field_node_id(schema_name: str, field_name: str) -> str:
    return f"api_field:{schema_name}.{field_name}"


def _action_node_id(endpoint_id: str) -> str:
    return f"action:{endpoint_id}"


def _permission_node_id(scheme: str) -> str:
    return f"permission:{slugify(scheme)}"


def _side_effect_for_endpoint(endpoint: NormalizedEndpoint) -> tuple[str, str]:
    method = endpoint.method.upper()
    if method == "GET":
        return "read", "reads"
    if method == "DELETE":
        return "delete", "deletes"
    if method in {"PATCH", "PUT"}:
        return "update", "mutates"
    if method == "POST" and endpoint.operation_class == "create":
        return "create", "creates"
    return "mutate", "mutates"


def _side_effect_node_id(side_effect: str) -> str:
    return f"side_effect:{side_effect}"


def _doc_node_id(endpoint_id: str, name: str) -> str:
    return f"doc_chunk:{endpoint_id}:{name}"


def _example_node_id(endpoint_id: str, index: int) -> str:
    return f"example_query:{endpoint_id}:{index}"


def _operation_terms(endpoint: NormalizedEndpoint) -> str:
    split_operation = " ".join(re.findall(r"[A-Z]?[a-z]+|[A-Z]+(?=[A-Z]|$)|[0-9]+", endpoint.operation_id))
    return " ".join(
        [
            endpoint.method,
            endpoint.path,
            endpoint.operation_id,
            split_operation,
            endpoint.summary,
            endpoint.description,
            endpoint.operation_class,
            " ".join(endpoint.tags),
            " ".join(endpoint.resources),
        ]
    )


def _required_inputs_for_endpoint(
    endpoint: NormalizedEndpoint,
    analysis: SemanticSchemaAnalysis,
    outgoing_relations: dict[str, list[SchemaRelation]],
) -> list[dict[str, Any]]:
    """Return endpoint-scoped required inputs with OpenAPI provenance.

    Explicit parameters and required fields on request roots are descriptors of
    an operation, not global graph identities. allOf members are traversed
    because they are jointly required; alternative oneOf/anyOf branches remain
    unresolved choices and are not flattened into unconditional requirements.
    """

    values: list[dict[str, Any]] = []
    for parameter in endpoint.params:
        if not parameter.required:
            continue
        values.append(
            {
                "name": parameter.name,
                "location": parameter.location,
                "kind": "parameter",
                "json_pointer": f"endpoint:{endpoint.id}/parameters/{parameter.location}/{parameter.name}",
                "schema_id": parameter.schema_name,
                "description": parameter.description,
            }
        )

    visited: set[str] = set()

    def visit_request_schema(schema_id: str) -> None:
        if schema_id in visited:
            return
        visited.add(schema_id)
        schema = analysis.schemas.get(schema_id)
        if schema is None:
            return
        for field in schema.scalar_fields:
            if not field.required or field.read_only:
                continue
            values.append(
                {
                    "name": field.name,
                    "location": "body",
                    "kind": "schema_field",
                    "json_pointer": field.json_pointer,
                    "schema_id": schema.schema_id,
                    "description": field.description,
                }
            )
        for relation in outgoing_relations.get(schema_id, []):
            if relation.status != "resolved" or not relation.target_schema_id:
                continue
            if relation.relation_type == "all_of":
                visit_request_schema(relation.target_schema_id)
                continue
            if relation.required and relation.relation_type in {
                "references",
                "contains_object",
                "contains_many",
                "additional_properties",
            }:
                values.append(
                    {
                        "name": relation.role,
                        "location": "body",
                        "kind": "schema_object",
                        "json_pointer": relation.json_pointer,
                        "schema_id": relation.target_schema_id,
                        "description": "",
                    }
                )

    request_roots = analysis.root_schema_ids_by_endpoint.get(endpoint.id, {}).get("request", ())
    for schema_id in request_roots:
        visit_request_schema(schema_id)

    unique: dict[tuple[str, str], dict[str, Any]] = {}
    for value in values:
        key = (str(value["location"]).casefold(), str(value["name"]).casefold())
        unique.setdefault(key, value)
    return list(unique.values())


def _add_node(nodes: dict[str, SemanticNode], node: SemanticNode) -> None:
    existing = nodes.get(node.id)
    if existing is None:
        nodes[node.id] = node
        return
    merged_evidence = list({(item.source, item.field, item.value): item for item in [*existing.evidence, *node.evidence]}.values())
    merged_facets = {**existing.facets, **node.facets}
    nodes[node.id] = SemanticNode(
        id=existing.id,
        node_type=existing.node_type,
        label=existing.label,
        text=" ".join(dict.fromkeys([existing.text, node.text])),
        endpoint_id=existing.endpoint_id or node.endpoint_id,
        facets=merged_facets,
        evidence=merged_evidence,
    )


def _add_edge(
    edges: list[SemanticEdge],
    nodes: dict[str, SemanticNode],
    source: str,
    target: str,
    edge_type: str,
    confidence: float,
    status: str,
    evidence: list[SemanticEvidence],
    facets: dict[str, Any] | None = None,
) -> None:
    if source not in nodes:
        raise ValueError(f"Semantic graph edge source does not exist: {source}")
    if target not in nodes:
        raise ValueError(f"Semantic graph edge target does not exist: {target}")
    if status not in EDGE_STATUSES:
        raise ValueError(f"Unknown semantic graph edge status: {status}")
    if not evidence:
        raise ValueError(f"Semantic graph edge requires evidence: {source} -> {target}")
    edges.append(
        SemanticEdge(
            source=source,
            target=target,
            type=edge_type,
            confidence=max(0.0, min(1.0, float(confidence))),
            status=status,
            evidence=evidence,
            facets=dict(facets or {}),
        )
    )


def _schema_text(schema_name: str, schema: dict[str, Any]) -> str:
    return f"{schema_name} {json.dumps(schema, sort_keys=True)}"


def _build_cards(nodes: dict[str, SemanticNode]) -> list[SemanticNodeCard]:
    cards: list[SemanticNodeCard] = []
    for node in nodes.values():
        cards.append(
            SemanticNodeCard(
                card_id=f"semantic_card:{node.id}",
                node_id=node.id,
                node_type=node.node_type,
                endpoint_id=node.endpoint_id,
                title=node.label,
                body=node.text,
                facets=dict(node.facets),
                evidence=list(node.evidence),
            )
        )
    return cards


def build_field_first_semantic_graph(
    bundle: NormalizedBundle,
    *,
    example_queries_by_endpoint: dict[str, list[str]] | None = None,
    trace_callback: GraphTraceCallback | None = None,
) -> SemanticGraph:
    example_queries_by_endpoint = example_queries_by_endpoint or {}
    nodes: dict[str, SemanticNode] = {}
    edges: list[SemanticEdge] = []

    for permission_index, (scheme, value) in enumerate(bundle.security_schemes.items(), start=1):
        before_nodes = dict(nodes)
        evidence = [_evidence("components.securitySchemes", scheme, value)]
        _add_node(
            nodes,
            SemanticNode(
                id=_permission_node_id(scheme),
                node_type="permission",
                label=scheme,
                text=f"permission security authentication authorization {scheme} {json.dumps(value, sort_keys=True)}",
                evidence=evidence,
            ),
        )
        added_nodes = [node for node_id, node in nodes.items() if node_id not in before_nodes]
        updated_nodes = [
            _node_update_payload(before_nodes[node_id], node)
            for node_id, node in nodes.items()
            if node_id in before_nodes and node != before_nodes[node_id]
        ]
        _emit_trace(
            trace_callback,
            {
                "type": "permission_complete",
                "permission_index": permission_index,
                "permission_total": len(bundle.security_schemes),
                "scheme_name": scheme,
                "added_nodes": [asdict(node) for node in added_nodes],
                "updated_nodes": updated_nodes,
                "cumulative": {
                    "nodes": len(nodes),
                    "raw_edges": len(edges),
                    "unique_edges": 0,
                },
            },
        )

    for schema_index, (schema_name, schema) in enumerate(bundle.schemas.items(), start=1):
        before_nodes = dict(nodes)
        properties = (
            schema.get("properties", {})
            if isinstance(schema, dict) and isinstance(schema.get("properties"), dict)
            else {}
        )
        for field_name, field_schema in properties.items():
            evidence = [_evidence(f"schema:{schema_name}", f"properties.{field_name}", field_schema)]
            _add_node(
                nodes,
                SemanticNode(
                    id=_field_node_id(schema_name, str(field_name)),
                    node_type="api_field",
                    label=f"{schema_name}.{field_name}",
                    text=f"field {schema_name} {field_name} {json.dumps(field_schema, sort_keys=True)}",
                    facets={"schema": schema_name, "field": str(field_name)},
                    evidence=evidence,
                ),
            )
        added_nodes = [node for node_id, node in nodes.items() if node_id not in before_nodes]
        updated_nodes = [
            _node_update_payload(before_nodes[node_id], node)
            for node_id, node in nodes.items()
            if node_id in before_nodes and node != before_nodes[node_id]
        ]
        _emit_trace(
            trace_callback,
            {
                "type": "schema_complete",
                "schema_index": schema_index,
                "schema_total": len(bundle.schemas),
                "schema_name": schema_name,
                "property_count": len(properties),
                "added_nodes": [asdict(node) for node in added_nodes],
                "updated_nodes": updated_nodes,
                "cumulative": {
                    "nodes": len(nodes),
                    "raw_edges": len(edges),
                    "unique_edges": 0,
                },
            },
        )

    trace_seen_edge_keys: set[str] = set()

    for endpoint_index, endpoint in enumerate(bundle.endpoints, start=1):
        before_nodes = dict(nodes)
        before_edge_count = len(edges)
        op_node_id = _operation_node_id(endpoint.id)
        op_evidence = [
            _evidence(endpoint.id, "method", endpoint.method),
            _evidence(endpoint.id, "path", endpoint.path),
            _evidence(endpoint.id, "operation_id", endpoint.operation_id),
            _evidence(endpoint.id, "summary", endpoint.summary),
            _evidence(endpoint.id, "description", endpoint.description),
        ]
        _add_node(
            nodes,
            SemanticNode(
                id=op_node_id,
                node_type="api_operation",
                label=f"{endpoint.method} {endpoint.path}",
                text=f"api operation endpoint {_operation_terms(endpoint)}",
                endpoint_id=endpoint.id,
                facets={
                    "method": endpoint.method,
                    "path": endpoint.path,
                    "operation_id": endpoint.operation_id,
                    "operation_class": endpoint.operation_class,
                    "source": endpoint.source,
                },
                evidence=op_evidence,
            ),
        )

        action_node_id = _action_node_id(endpoint.id)
        _add_node(
            nodes,
            SemanticNode(
                id=action_node_id,
                node_type="action",
                label=endpoint.operation_id,
                text=f"action intent {_operation_terms(endpoint)}",
                endpoint_id=endpoint.id,
                facets={"operation_class": endpoint.operation_class, "method": endpoint.method},
                evidence=[_evidence(endpoint.id, "operation", _operation_terms(endpoint))],
            ),
        )
        _add_edge(edges, nodes, op_node_id, action_node_id, "performs", 0.95, "observed", [_evidence(endpoint.id, "operation_id", endpoint.operation_id)])
        _add_edge(edges, nodes, action_node_id, op_node_id, "projects", 0.95, "derived", [_evidence(endpoint.id, "operation_id", endpoint.operation_id)])

        side_effect, resource_edge_type = _side_effect_for_endpoint(endpoint)
        side_effect_id = _side_effect_node_id(side_effect)
        _add_node(
            nodes,
            SemanticNode(
                id=side_effect_id,
                node_type="side_effect",
                label=side_effect,
                text=f"side effect {side_effect} {endpoint.method} {endpoint.operation_class}",
                evidence=[_evidence(endpoint.id, "method", endpoint.method)],
            ),
        )
        _add_edge(edges, nodes, op_node_id, side_effect_id, "has_action", 0.75, "derived", [_evidence(endpoint.id, "method", endpoint.method)])

        for resource in endpoint.resources:
            resource_id = f"resource:{resource}"
            _add_node(
                nodes,
                SemanticNode(
                    id=resource_id,
                    node_type="resource",
                    label=resource,
                    text=f"resource entity object {resource}",
                    facets={"resource": resource},
                    evidence=[_evidence(endpoint.id, "resources", resource)],
                ),
            )
            _add_edge(edges, nodes, op_node_id, resource_id, "exposes", 0.85, "observed", [_evidence(endpoint.id, "resources", resource)])
            _add_edge(edges, nodes, side_effect_id, resource_id, resource_edge_type, 0.70, "derived", [_evidence(endpoint.id, "method", endpoint.method)])

        for scheme in endpoint.security:
            permission_id = _permission_node_id(scheme)
            if permission_id not in nodes:
                _add_node(
                    nodes,
                    SemanticNode(
                        id=permission_id,
                        node_type="permission",
                        label=scheme,
                        text=f"permission security authentication authorization {scheme}",
                        evidence=[_evidence(endpoint.id, "security", scheme)],
                    ),
                )
            _add_edge(edges, nodes, op_node_id, permission_id, "requires", 0.90, "observed", [_evidence(endpoint.id, "security", scheme)])

        for direction, schema_names, edge_type in [
            ("request", endpoint.request_schemas, "accepts"),
            ("response", endpoint.response_schemas, "returns"),
        ]:
            for schema_name in schema_names:
                schema = bundle.schemas.get(schema_name, {})
                shape_id = _shape_node_id(endpoint.id, direction, schema_name)
                _add_node(
                    nodes,
                    SemanticNode(
                        id=shape_id,
                        node_type="api_shape",
                        label=f"{direction} {schema_name}",
                        text=f"{direction} shape schema {_schema_text(schema_name, schema if isinstance(schema, dict) else {})}",
                        endpoint_id=endpoint.id,
                        facets={"schema": schema_name, "direction": direction},
                        evidence=[_evidence(endpoint.id, f"{direction}_schema", schema_name)],
                    ),
                )
                _add_edge(edges, nodes, op_node_id, shape_id, edge_type, 0.90, "observed", [_evidence(endpoint.id, f"{direction}_schema", schema_name)])
                if isinstance(schema, dict):
                    properties = schema.get("properties", {}) if isinstance(schema.get("properties"), dict) else {}
                    for field_name in properties:
                        field_id = _field_node_id(schema_name, str(field_name))
                        if field_id in nodes:
                            _add_edge(edges, nodes, shape_id, field_id, "has_field", 0.85, "observed", [_evidence(f"schema:{schema_name}", "field", field_name)])

        doc_id = _doc_node_id(endpoint.id, "operation")
        _add_node(
            nodes,
            SemanticNode(
                id=doc_id,
                node_type="doc_chunk",
                label=f"{endpoint.operation_id} docs",
                text=f"documentation summary description {_operation_terms(endpoint)}",
                endpoint_id=endpoint.id,
                facets={"kind": "operation_doc"},
                evidence=[_evidence(endpoint.id, "summary_description", f"{endpoint.summary} {endpoint.description}")],
            ),
        )
        _add_edge(edges, nodes, doc_id, op_node_id, "projects", 0.80, "derived", [_evidence(endpoint.id, "summary", endpoint.summary)])

        for index, query in enumerate(example_queries_by_endpoint.get(endpoint.id, [])):
            example_id = _example_node_id(endpoint.id, index)
            _add_node(
                nodes,
                SemanticNode(
                    id=example_id,
                    node_type="example_query",
                    label=query,
                    text=f"example user query {query} endpoint {endpoint.operation_id} {endpoint.summary}",
                    endpoint_id=endpoint.id,
                    facets={"kind": "example_query"},
                    evidence=[_evidence(endpoint.id, "example_query", query)],
                ),
            )
            _add_edge(edges, nodes, example_id, action_node_id, "resembles", 0.85, "observed", [_evidence(endpoint.id, "example_query", query)])
            _add_edge(edges, nodes, example_id, op_node_id, "projects", 0.75, "derived", [_evidence(endpoint.id, "example_query", query)])

        added_nodes = [node for node_id, node in nodes.items() if node_id not in before_nodes]
        updated_nodes = [
            _node_update_payload(before_nodes[node_id], node)
            for node_id, node in nodes.items()
            if node_id in before_nodes and node != before_nodes[node_id]
        ]
        added_edges: list[dict[str, Any]] = []
        duplicate_edge_attempt_count = 0
        for edge in edges[before_edge_count:]:
            edge_key = _edge_key(edge)
            if edge_key in trace_seen_edge_keys:
                duplicate_edge_attempt_count += 1
                continue
            trace_seen_edge_keys.add(edge_key)
            added_edges.append({"id": edge_key, **asdict(edge)})
        _emit_trace(
            trace_callback,
            {
                "type": "endpoint_complete",
                "endpoint_index": endpoint_index,
                "endpoint_total": len(bundle.endpoints),
                "endpoint": asdict(endpoint),
                "added_nodes": [asdict(node) for node in added_nodes],
                "updated_nodes": updated_nodes,
                "added_edges": added_edges,
                "duplicate_edge_attempt_count": duplicate_edge_attempt_count,
                "cumulative": {
                    "nodes": len(nodes),
                    "raw_edges": len(edges),
                    "unique_edges": len(trace_seen_edge_keys),
                },
            },
        )

    unique_edges: list[SemanticEdge] = []
    seen: set[tuple[str, str, str]] = set()
    for edge in edges:
        key = (edge.source, edge.target, edge.type)
        if key in seen:
            continue
        seen.add(key)
        unique_edges.append(edge)

    _emit_trace(
        trace_callback,
        {
            "type": "deduplication_complete",
            "raw_edge_count": len(edges),
            "unique_edge_count": len(unique_edges),
            "removed_duplicate_count": len(edges) - len(unique_edges),
            "cumulative": {
                "nodes": len(nodes),
                "raw_edges": len(edges),
                "unique_edges": len(unique_edges),
            },
        },
    )

    cards = _build_cards(nodes)
    _emit_trace(
        trace_callback,
        {
            "type": "cards_complete",
            "card_count": len(cards),
            "cards": [
                {
                    "card_id": card.card_id,
                    "node_id": card.node_id,
                    "embedding_text": card.embedding_text(),
                }
                for card in cards
            ],
            "cumulative": {
                "nodes": len(nodes),
                "edges": len(unique_edges),
                "cards": len(cards),
            },
        },
    )

    return SemanticGraph(
        nodes=list(nodes.values()),
        edges=unique_edges,
        cards=cards,
        metadata={
            "assembler": "field_first_legacy",
            "experimental": True,
            "known_limitation": "materializes every schema property occurrence as an api_field node",
        },
    )


def _canonical_schema_node_id(schema: CanonicalSchema) -> str:
    return f"{schema.node_type}:{schema.schema_id}"


def _schema_relation_evidence(relation: SchemaRelation) -> list[SemanticEvidence]:
    value = relation.raw_ref or relation.target_schema_id or "unresolved"
    return [_evidence(f"schema:{relation.source_schema_id}", relation.json_pointer, value)]


def _schema_node(
    schema: CanonicalSchema,
    outgoing_relations: list[SchemaRelation],
) -> SemanticNode:
    scalar_field_facets = [asdict(field) for field in schema.scalar_fields]
    relation_facets = [
        {
            "role": relation.role,
            "relation_type": relation.relation_type,
            "cardinality": relation.cardinality,
            "required": relation.required,
            "target_schema_id": relation.target_schema_id,
            "status": relation.status,
            "json_pointer": relation.json_pointer,
        }
        for relation in outgoing_relations
    ]
    scalar_text = " ".join(
        " ".join(
            part
            for part in (
                field.name,
                field.normalized_name,
                field.schema_type,
                field.schema_format,
                "required" if field.required else "optional",
                "read only" if field.read_only else "",
                "write only" if field.write_only else "",
                field.description,
                json.dumps(field.constraints, sort_keys=True, default=str),
            )
            if part
        )
        for field in schema.scalar_fields
    )
    relation_text = " ".join(
        f"{relation.relation_type} role {relation.role} {relation.cardinality} target "
        f"{relation.target_schema_id or 'unresolved'}"
        for relation in outgoing_relations
    )
    return SemanticNode(
        id=_canonical_schema_node_id(schema),
        node_type=schema.node_type,
        label=schema.name,
        text=" ".join(
            part
            for part in (
                "canonical api schema" if schema.node_type == "api_schema" else "inline api shape",
                schema.name,
                schema.semantic_stem,
                schema.description,
                scalar_text,
                relation_text,
            )
            if part
        ),
        facets={
            "schema_id": schema.schema_id,
            "source": schema.source,
            "semantic_stem": schema.semantic_stem,
            "json_pointer": schema.json_pointer,
            "origin_component_id": schema.origin_component_id,
            "aliases": list(schema.aliases),
            "scalar_field_count": len(schema.scalar_fields),
            "scalar_fields": scalar_field_facets,
            "relation_count": len(outgoing_relations),
            "relations": relation_facets,
        },
        evidence=[
            _evidence(f"schema:{schema.schema_id}", "json_pointer", schema.json_pointer),
            _evidence(f"schema:{schema.schema_id}", "source", schema.source),
        ],
    )


def _endpoint_schema_closure(
    analysis: SemanticSchemaAnalysis,
    endpoint_id: str,
    outgoing_relations: dict[str, list[SchemaRelation]],
) -> list[str]:
    roots = analysis.root_schema_ids_by_endpoint.get(endpoint_id, {})
    queue = [*roots.get("request", ()), *roots.get("response", ())]
    ordered: list[str] = []
    seen: set[str] = set()
    while queue:
        schema_id = queue.pop(0)
        if schema_id in seen:
            continue
        seen.add(schema_id)
        ordered.append(schema_id)
        for relation in outgoing_relations.get(schema_id, []):
            if relation.status == "resolved" and relation.target_schema_id:
                queue.append(relation.target_schema_id)
    return ordered


def _unique_trace_edges(
    edges: list[SemanticEdge],
    start_index: int,
    seen_edge_keys: set[str],
) -> tuple[list[dict[str, Any]], int]:
    added_edges: list[dict[str, Any]] = []
    duplicates = 0
    for edge in edges[start_index:]:
        edge_key = _edge_key(edge)
        if edge_key in seen_edge_keys:
            duplicates += 1
            continue
        seen_edge_keys.add(edge_key)
        added_edges.append({"id": edge_key, **asdict(edge)})
    return added_edges, duplicates


def build_resource_first_semantic_graph(
    bundle: NormalizedBundle,
    *,
    example_queries_by_endpoint: dict[str, list[str]] | None = None,
    trace_callback: GraphTraceCallback | None = None,
) -> SemanticGraph:
    """Build the experimental endpoint-rooted graph selected for further research."""

    example_queries_by_endpoint = example_queries_by_endpoint or {}
    analysis = analyze_semantic_schemas(bundle)
    nodes: dict[str, SemanticNode] = {}
    edges: list[SemanticEdge] = []
    trace_seen_edge_keys: set[str] = set()
    outgoing_relations: dict[str, list[SchemaRelation]] = {}
    for relation in analysis.relations:
        outgoing_relations.setdefault(relation.source_schema_id, []).append(relation)

    for permission_index, (scheme, value) in enumerate(bundle.security_schemes.items(), start=1):
        before_nodes = dict(nodes)
        _add_node(
            nodes,
            SemanticNode(
                id=_permission_node_id(scheme),
                node_type="permission",
                label=scheme,
                text=f"permission security authentication authorization {scheme} {json.dumps(value, sort_keys=True)}",
                evidence=[_evidence("components.securitySchemes", scheme, value)],
            ),
        )
        added_nodes = [node for node_id, node in nodes.items() if node_id not in before_nodes]
        _emit_trace(
            trace_callback,
            {
                "type": "permission_complete",
                "permission_index": permission_index,
                "permission_total": len(bundle.security_schemes),
                "scheme_name": scheme,
                "added_nodes": [asdict(node) for node in added_nodes],
                "updated_nodes": [],
                "cumulative": {"nodes": len(nodes), "raw_edges": len(edges), "unique_edges": 0},
            },
        )

    _emit_trace(
        trace_callback,
        {
            "type": "schema_registry_complete",
            "inventory": dict(analysis.inventory),
            "canonical_aliases": {
                alias: list(candidates)
                for alias, candidates in analysis.component_aliases.items()
                if len(candidates) == 1 and alias != candidates[0]
            },
            "unreachable_component_ids": list(analysis.unreachable_component_ids),
            "warnings": [asdict(warning) for warning in analysis.warnings],
            "added_nodes": [],
            "updated_nodes": [],
            "cumulative": {"nodes": len(nodes), "raw_edges": len(edges), "unique_edges": 0},
        },
    )

    resource_inference_ambiguities: list[dict[str, Any]] = []

    for endpoint_index, endpoint in enumerate(bundle.endpoints, start=1):
        before_nodes = dict(nodes)
        before_edge_count = len(edges)
        separately_traced_schema_ids: set[str] = set()
        closure = _endpoint_schema_closure(analysis, endpoint.id, outgoing_relations)
        for discovery_index, schema_id in enumerate(closure, start=1):
            schema = analysis.schemas[schema_id]
            schema_node = _schema_node(schema, outgoing_relations.get(schema_id, []))
            if schema_node.id in nodes:
                continue
            _add_node(nodes, schema_node)
            separately_traced_schema_ids.add(schema_node.id)
            _emit_trace(
                trace_callback,
                {
                    "type": "schema_discovered",
                    "active_endpoint_id": endpoint.id,
                    "endpoint": asdict(endpoint),
                    "endpoint_index": endpoint_index,
                    "endpoint_total": len(bundle.endpoints),
                    "discovery_index": discovery_index,
                    "closure_size": len(closure),
                    "schema_id": schema_id,
                    "schema_name": schema.name,
                    "schema_node_type": schema.node_type,
                    "scalar_field_count": len(schema.scalar_fields),
                    "relation_count": len(outgoing_relations.get(schema_id, [])),
                    "added_nodes": [asdict(schema_node)],
                    "updated_nodes": [],
                    "added_edges": [],
                    "cumulative": {
                        "nodes": len(nodes),
                        "raw_edges": len(edges),
                        "unique_edges": len(trace_seen_edge_keys),
                    },
                },
            )
        op_node_id = _operation_node_id(endpoint.id)
        required_inputs = _required_inputs_for_endpoint(endpoint, analysis, outgoing_relations)
        required_input_names = [str(value["name"]) for value in required_inputs]
        op_evidence = [
            _evidence(endpoint.id, "method", endpoint.method),
            _evidence(endpoint.id, "path", endpoint.path),
            _evidence(endpoint.id, "operation_id", endpoint.operation_id),
            _evidence(endpoint.id, "summary", endpoint.summary),
            _evidence(endpoint.id, "description", endpoint.description),
            *[
                _evidence(
                    endpoint.id,
                    "required_input",
                    f"{value['location']}:{value['name']}:{value['json_pointer']}",
                )
                for value in required_inputs
            ],
        ]
        _add_node(
            nodes,
            SemanticNode(
                id=op_node_id,
                node_type="api_operation",
                label=f"{endpoint.method} {endpoint.path}",
                text=(
                    f"api operation endpoint {_operation_terms(endpoint)} required inputs "
                    + " ".join(required_input_names)
                ).strip(),
                endpoint_id=endpoint.id,
                facets={
                    "method": endpoint.method,
                    "path": endpoint.path,
                    "operation_id": endpoint.operation_id,
                    "operation_class": endpoint.operation_class,
                    "source": endpoint.source,
                    "parameters": [asdict(parameter) for parameter in endpoint.params],
                    "required_inputs": required_inputs,
                    "required_input_names": required_input_names,
                },
                evidence=op_evidence,
            ),
        )

        action_node_id = _action_node_id(endpoint.id)
        _add_node(
            nodes,
            SemanticNode(
                id=action_node_id,
                node_type="action",
                label=endpoint.operation_id,
                text=f"action intent {_operation_terms(endpoint)}",
                endpoint_id=endpoint.id,
                facets={"operation_class": endpoint.operation_class, "method": endpoint.method},
                evidence=[_evidence(endpoint.id, "operation", _operation_terms(endpoint))],
            ),
        )
        _add_edge(
            edges,
            nodes,
            op_node_id,
            action_node_id,
            "performs",
            0.95,
            "observed",
            [_evidence(endpoint.id, "operation_id", endpoint.operation_id)],
        )
        _add_edge(
            edges,
            nodes,
            action_node_id,
            op_node_id,
            "projects",
            0.95,
            "derived",
            [_evidence(endpoint.id, "operation_id", endpoint.operation_id)],
        )

        side_effect, resource_edge_type = _side_effect_for_endpoint(endpoint)
        side_effect_id = _side_effect_node_id(side_effect)
        _add_node(
            nodes,
            SemanticNode(
                id=side_effect_id,
                node_type="side_effect",
                label=side_effect,
                text=f"side effect {side_effect} {endpoint.method} {endpoint.operation_class}",
                evidence=[_evidence(endpoint.id, "method", endpoint.method)],
            ),
        )
        _add_edge(
            edges,
            nodes,
            op_node_id,
            side_effect_id,
            "has_action",
            0.75,
            "derived",
            [_evidence(endpoint.id, "method", endpoint.method)],
        )

        resource_node_ids: dict[str, str] = {}
        for resource in endpoint.resources:
            resource_id = f"resource:{resource}"
            resource_node_ids[resource] = resource_id
            _add_node(
                nodes,
                SemanticNode(
                    id=resource_id,
                    node_type="resource",
                    label=resource,
                    text=f"resource entity object {resource}",
                    facets={"resource": resource},
                    evidence=[_evidence(endpoint.id, "resources", resource)],
                ),
            )
            _add_edge(
                edges,
                nodes,
                op_node_id,
                resource_id,
                "exposes",
                0.85,
                "observed",
                [_evidence(endpoint.id, "resources", resource)],
            )
            _add_edge(
                edges,
                nodes,
                side_effect_id,
                resource_id,
                resource_edge_type,
                0.70,
                "derived",
                [_evidence(endpoint.id, "method", endpoint.method)],
            )

        for scheme in endpoint.security:
            permission_id = _permission_node_id(scheme)
            if permission_id not in nodes:
                _add_node(
                    nodes,
                    SemanticNode(
                        id=permission_id,
                        node_type="permission",
                        label=scheme,
                        text=f"permission security authentication authorization {scheme}",
                        evidence=[_evidence(endpoint.id, "security", scheme)],
                    ),
                )
            _add_edge(
                edges,
                nodes,
                op_node_id,
                permission_id,
                "requires",
                0.90,
                "observed",
                [_evidence(endpoint.id, "security", scheme)],
            )

        closure_set = set(closure)
        for source_schema_id in closure:
            for relation in outgoing_relations.get(source_schema_id, []):
                if (
                    relation.status != "resolved"
                    or not relation.target_schema_id
                    or relation.target_schema_id not in closure_set
                ):
                    continue
                source_id = _canonical_schema_node_id(analysis.schemas[source_schema_id])
                target_id = _canonical_schema_node_id(analysis.schemas[relation.target_schema_id])
                _add_edge(
                    edges,
                    nodes,
                    source_id,
                    target_id,
                    relation.relation_type,
                    1.0,
                    "observed",
                    _schema_relation_evidence(relation),
                    facets={
                        "role": relation.role,
                        "cardinality": relation.cardinality,
                        "required": relation.required,
                        "json_pointer": relation.json_pointer,
                        "raw_ref": relation.raw_ref,
                    },
                )

        root_directions = analysis.root_schema_ids_by_endpoint.get(endpoint.id, {})
        direct_root_ids = set(root_directions.get("request", ())) | set(root_directions.get("response", ()))
        for direction, edge_type in (("request", "accepts"), ("response", "returns")):
            for schema_id in root_directions.get(direction, ()):
                schema = analysis.schemas[schema_id]
                shape_id = _shape_node_id(endpoint.id, direction, schema.name)
                schema_node_id = _canonical_schema_node_id(schema)
                _add_node(
                    nodes,
                    SemanticNode(
                        id=shape_id,
                        node_type="api_shape",
                        label=f"{direction} {schema.name}",
                        text=(
                            f"{direction} shape canonical schema {schema.name} {schema.semantic_stem} "
                            f"for {endpoint.method} {endpoint.path} fields "
                            + " ".join(
                                " ".join(
                                    part
                                    for part in (
                                        field.name,
                                        field.schema_type,
                                        field.schema_format,
                                        field.description,
                                    )
                                    if part
                                )
                                for field in schema.scalar_fields
                            )
                        ),
                        endpoint_id=endpoint.id,
                        facets={
                            "schema": schema.name,
                            "canonical_schema_id": schema.schema_id,
                            "direction": direction,
                        },
                        evidence=[_evidence(endpoint.id, f"{direction}_schema", schema.name)],
                    ),
                )
                _add_edge(
                    edges,
                    nodes,
                    op_node_id,
                    shape_id,
                    edge_type,
                    0.90,
                    "observed",
                    [_evidence(endpoint.id, f"{direction}_schema", schema.name)],
                )
                _add_edge(
                    edges,
                    nodes,
                    shape_id,
                    schema_node_id,
                    "uses_schema",
                    1.0,
                    "observed",
                    [_evidence(endpoint.id, f"{direction}_schema", schema.schema_id)],
                )

        for resource, resource_id in resource_node_ids.items():
            resource_key = semantic_stem(resource)
            matches = [
                schema_id
                for schema_id in direct_root_ids
                if analysis.schemas[schema_id].semantic_stem == resource_key
            ]
            if len(matches) == 1:
                schema = analysis.schemas[matches[0]]
                _add_edge(
                    edges,
                    nodes,
                    _canonical_schema_node_id(schema),
                    resource_id,
                    "describes_resource",
                    0.95,
                    "derived",
                    [
                        _evidence(endpoint.id, "resource", resource),
                        _evidence(f"schema:{schema.schema_id}", "semantic_stem", schema.semantic_stem),
                    ],
                )
            elif len(matches) > 1:
                resource_inference_ambiguities.append(
                    {
                        "endpoint_id": endpoint.id,
                        "resource": resource,
                        "candidate_schema_ids": sorted(matches),
                        "reason": "multiple direct endpoint roots have the same exact semantic stem",
                    }
                )

        doc_id = _doc_node_id(endpoint.id, "operation")
        _add_node(
            nodes,
            SemanticNode(
                id=doc_id,
                node_type="doc_chunk",
                label=f"{endpoint.operation_id} docs",
                text=f"documentation summary description {_operation_terms(endpoint)}",
                endpoint_id=endpoint.id,
                facets={"kind": "operation_doc"},
                evidence=[
                    _evidence(endpoint.id, "summary_description", f"{endpoint.summary} {endpoint.description}")
                ],
            ),
        )
        _add_edge(
            edges,
            nodes,
            doc_id,
            op_node_id,
            "projects",
            0.80,
            "derived",
            [_evidence(endpoint.id, "summary", endpoint.summary)],
        )

        for index, query in enumerate(example_queries_by_endpoint.get(endpoint.id, [])):
            example_id = _example_node_id(endpoint.id, index)
            _add_node(
                nodes,
                SemanticNode(
                    id=example_id,
                    node_type="example_query",
                    label=query,
                    text=f"example user query {query} endpoint {endpoint.operation_id} {endpoint.summary}",
                    endpoint_id=endpoint.id,
                    facets={"kind": "example_query"},
                    evidence=[_evidence(endpoint.id, "example_query", query)],
                ),
            )
            _add_edge(
                edges,
                nodes,
                example_id,
                action_node_id,
                "resembles",
                0.85,
                "observed",
                [_evidence(endpoint.id, "example_query", query)],
            )
            _add_edge(
                edges,
                nodes,
                example_id,
                op_node_id,
                "projects",
                0.75,
                "derived",
                [_evidence(endpoint.id, "example_query", query)],
            )

        added_nodes = [
            node
            for node_id, node in nodes.items()
            if node_id not in before_nodes and node_id not in separately_traced_schema_ids
        ]
        updated_nodes = [
            _node_update_payload(before_nodes[node_id], node)
            for node_id, node in nodes.items()
            if node_id in before_nodes and node != before_nodes[node_id]
        ]
        added_edges, duplicate_edge_attempt_count = _unique_trace_edges(
            edges,
            before_edge_count,
            trace_seen_edge_keys,
        )
        _emit_trace(
            trace_callback,
            {
                "type": "endpoint_complete",
                "active_endpoint_id": endpoint.id,
                "endpoint_index": endpoint_index,
                "endpoint_total": len(bundle.endpoints),
                "endpoint": asdict(endpoint),
                "schema_closure": closure,
                "added_nodes": [asdict(node) for node in added_nodes],
                "updated_nodes": updated_nodes,
                "added_edges": added_edges,
                "duplicate_edge_attempt_count": duplicate_edge_attempt_count,
                "cumulative": {
                    "nodes": len(nodes),
                    "raw_edges": len(edges),
                    "unique_edges": len(trace_seen_edge_keys),
                },
            },
        )

    inference_edge_start = len(edges)
    for group in analysis.equivalent_shape_groups:
        representative = group[0]
        representative_node_id = _canonical_schema_node_id(analysis.schemas[representative])
        for schema_id in group[1:]:
            schema_node_id = _canonical_schema_node_id(analysis.schemas[schema_id])
            evidence = [
                _evidence(
                    "structural_signature",
                    "exact_equal",
                    f"{representative}|{schema_id}",
                )
            ]
            _add_edge(
                edges,
                nodes,
                representative_node_id,
                schema_node_id,
                "equivalent_shape",
                1.0,
                "inferred",
                evidence,
            )
            _add_edge(
                edges,
                nodes,
                schema_node_id,
                representative_node_id,
                "equivalent_shape",
                1.0,
                "inferred",
                evidence,
            )

    for projection in analysis.projection_relations:
        _add_edge(
            edges,
            nodes,
            _canonical_schema_node_id(analysis.schemas[projection.projection_schema_id]),
            _canonical_schema_node_id(analysis.schemas[projection.full_schema_id]),
            "projection_of",
            1.0,
            "inferred",
            [
                _evidence(
                    "structural_signature",
                    "strict_subset_same_semantic_stem",
                    f"{projection.projection_schema_id}|{projection.full_schema_id}",
                )
            ],
        )

    inference_edges, inference_duplicate_count = _unique_trace_edges(
        edges,
        inference_edge_start,
        trace_seen_edge_keys,
    )
    _emit_trace(
        trace_callback,
        {
            "type": "resource_inference_complete",
            "equivalent_shape_groups": [list(group) for group in analysis.equivalent_shape_groups],
            "projection_relations": [asdict(item) for item in analysis.projection_relations],
            "ambiguous_equal_shape_groups": [
                list(group) for group in analysis.ambiguous_equal_shape_groups
            ],
            "resource_inference_ambiguities": resource_inference_ambiguities,
            "added_nodes": [],
            "updated_nodes": [],
            "added_edges": inference_edges,
            "duplicate_edge_attempt_count": inference_duplicate_count,
            "cumulative": {
                "nodes": len(nodes),
                "raw_edges": len(edges),
                "unique_edges": len(trace_seen_edge_keys),
            },
        },
    )

    unique_edges: list[SemanticEdge] = []
    seen: set[tuple[str, str, str]] = set()
    for edge in edges:
        key = (edge.source, edge.target, edge.type)
        if key in seen:
            continue
        seen.add(key)
        unique_edges.append(edge)

    _emit_trace(
        trace_callback,
        {
            "type": "deduplication_complete",
            "raw_edge_count": len(edges),
            "unique_edge_count": len(unique_edges),
            "removed_duplicate_count": len(edges) - len(unique_edges),
            "cumulative": {
                "nodes": len(nodes),
                "raw_edges": len(edges),
                "unique_edges": len(unique_edges),
            },
        },
    )

    cards = _build_cards(nodes)
    _emit_trace(
        trace_callback,
        {
            "type": "cards_complete",
            "card_count": len(cards),
            "cards": [
                {
                    "card_id": card.card_id,
                    "node_id": card.node_id,
                    "embedding_text": card.embedding_text(),
                }
                for card in cards
            ],
            "cumulative": {"nodes": len(nodes), "edges": len(unique_edges), "cards": len(cards)},
        },
    )

    graph = SemanticGraph(
        nodes=list(nodes.values()),
        edges=unique_edges,
        cards=cards,
        metadata={
            "assembler": "resource_first_v1",
            "experimental": True,
            "schema_analysis": dict(analysis.inventory),
            "schema_warnings": [asdict(warning) for warning in analysis.warnings],
            "unreachable_component_ids": list(analysis.unreachable_component_ids),
            "equivalent_shape_groups": [list(group) for group in analysis.equivalent_shape_groups],
            "projection_relations": [asdict(item) for item in analysis.projection_relations],
            "ambiguous_equal_shape_groups": [
                list(group) for group in analysis.ambiguous_equal_shape_groups
            ],
            "resource_inference_ambiguities": resource_inference_ambiguities,
        },
    )
    from .semantic_graph_conformance import (
        assert_semantic_graph_conformance,
        build_semantic_graph_conformance_report,
    )

    conformance = build_semantic_graph_conformance_report(bundle, graph)
    graph.metadata["construction_conformance"] = conformance
    assert_semantic_graph_conformance(conformance)
    _emit_trace(
        trace_callback,
        {
            "type": "conformance_complete",
            "report": conformance,
            "added_nodes": [],
            "updated_nodes": [],
            "added_edges": [],
            "cumulative": {
                "nodes": len(graph.nodes),
                "edges": len(graph.edges),
                "cards": len(graph.cards),
            },
        },
    )
    return graph


def build_semantic_graph(
    bundle: NormalizedBundle,
    *,
    example_queries_by_endpoint: dict[str, list[str]] | None = None,
    trace_callback: GraphTraceCallback | None = None,
) -> SemanticGraph:
    return build_resource_first_semantic_graph(
        bundle,
        example_queries_by_endpoint=example_queries_by_endpoint,
        trace_callback=trace_callback,
    )
