from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .openapi_loader import NormalizedBundle, schema_refs, slugify


@dataclass
class GraphArtifacts:
    nodes: list[dict[str, Any]]
    edges: list[dict[str, Any]]


def add_node(nodes: dict[str, dict[str, Any]], node_id: str, kind: str, label: str, text: str = "") -> None:
    nodes.setdefault(node_id, {"id": node_id, "kind": kind, "label": label, "text": text or label})


def add_edge(edges: list[dict[str, Any]], source: str, target: str, kind: str) -> None:
    if source and target:
        edges.append({"source": source, "target": target, "kind": kind})


def schema_node_id(name: str) -> str:
    return f"schema:{name}"


def build_schema_graph(bundle: NormalizedBundle) -> GraphArtifacts:
    nodes: dict[str, dict[str, Any]] = {}
    edges: list[dict[str, Any]] = []

    for method in ["GET", "POST", "PUT", "PATCH", "DELETE"]:
        add_node(nodes, f"method:{method}", "method", method)

    for scheme, value in bundle.security_schemes.items():
        add_node(nodes, f"auth:{scheme}", "auth", scheme, json.dumps(value, sort_keys=True))

    for schema_name, schema in bundle.schemas.items():
        add_node(nodes, schema_node_id(schema_name), "schema", schema_name, json.dumps(schema, sort_keys=True))
        if isinstance(schema, dict):
            properties = schema.get("properties", {})
            if isinstance(properties, dict):
                for field_name, field_schema in properties.items():
                    field_id = f"field:{schema_name}.{field_name}"
                    add_node(nodes, field_id, "field", f"{schema_name}.{field_name}", json.dumps(field_schema, sort_keys=True))
                    add_edge(edges, field_id, schema_node_id(schema_name), "field_of")
                    for ref in schema_refs(field_schema):
                        target = schema_node_id(ref.rstrip("/").split("/")[-1])
                        add_edge(edges, field_id, target, "references")
            for ref in schema_refs(schema):
                target = schema_node_id(ref.rstrip("/").split("/")[-1])
                if target != schema_node_id(schema_name):
                    add_edge(edges, schema_node_id(schema_name), target, "references")

    for endpoint in bundle.endpoints:
        endpoint_node = f"endpoint:{endpoint.id}"
        endpoint_text = " ".join(
            [
                endpoint.method,
                endpoint.path,
                endpoint.operation_id,
                endpoint.summary,
                endpoint.description,
                " ".join(endpoint.tags),
                " ".join(endpoint.resources),
                endpoint.operation_class,
            ]
        )
        add_node(nodes, endpoint_node, "endpoint", endpoint.id, endpoint_text)
        add_edge(edges, endpoint_node, f"method:{endpoint.method}", "has_method")
        for tag in endpoint.tags:
            tag_id = f"tag:{slugify(tag)}"
            add_node(nodes, tag_id, "tag", tag)
            add_edge(edges, endpoint_node, tag_id, "has_tag")
        for resource in endpoint.resources:
            resource_id = f"resource:{resource}"
            add_node(nodes, resource_id, "resource", resource)
            add_edge(edges, endpoint_node, resource_id, "operates_on")
        for param in endpoint.params:
            param_id = f"param:{endpoint.id}.{param.location}.{param.name}"
            add_node(nodes, param_id, "param", param.name, f"{param.location} {param.name} {param.description}")
            add_edge(edges, endpoint_node, param_id, "requires_param" if param.required else "optional_param")
            if param.schema_name:
                add_edge(edges, param_id, schema_node_id(param.schema_name), "references")
        for schema_name in endpoint.request_schemas:
            add_edge(edges, endpoint_node, schema_node_id(schema_name), "request_schema")
        for schema_name in endpoint.response_schemas:
            add_edge(edges, endpoint_node, schema_node_id(schema_name), "response_schema")
        for scheme in endpoint.security:
            scheme_id = f"auth:{scheme}"
            add_node(nodes, scheme_id, "auth", scheme)
            add_edge(edges, endpoint_node, scheme_id, "secured_by")

    unique_edges = []
    seen = set()
    for edge in edges:
        key = (edge["source"], edge["target"], edge["kind"])
        if key not in seen:
            unique_edges.append(edge)
            seen.add(key)
    return GraphArtifacts(nodes=list(nodes.values()), edges=unique_edges)


def write_graph(graph: GraphArtifacts, out_dir: Path) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)
    with (out_dir / "graph_nodes.jsonl").open("w", encoding="utf-8") as fh:
        for node in graph.nodes:
            fh.write(json.dumps(node, sort_keys=True) + "\n")
    with (out_dir / "graph_edges.jsonl").open("w", encoding="utf-8") as fh:
        for edge in graph.edges:
            fh.write(json.dumps(edge, sort_keys=True) + "\n")


def read_graph(artifacts_dir: Path) -> GraphArtifacts:
    nodes = [json.loads(line) for line in (artifacts_dir / "graph_nodes.jsonl").read_text(encoding="utf-8").splitlines() if line.strip()]
    edges = [json.loads(line) for line in (artifacts_dir / "graph_edges.jsonl").read_text(encoding="utf-8").splitlines() if line.strip()]
    return GraphArtifacts(nodes=nodes, edges=edges)
