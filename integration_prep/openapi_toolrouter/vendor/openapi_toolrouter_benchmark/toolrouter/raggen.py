from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .openapi_loader import NormalizedBundle


@dataclass
class RagCorpus:
    documents: list[dict[str, Any]]


def endpoint_text(endpoint: Any) -> str:
    param_text = " ".join(
        f"{param.location} parameter {param.name} {'required' if param.required else 'optional'} {param.description}"
        for param in endpoint.params
    )
    return " ".join(
        [
            f"endpoint {endpoint.id}",
            endpoint.method,
            endpoint.path,
            endpoint.operation_id,
            endpoint.summary,
            endpoint.description,
            "tags " + " ".join(endpoint.tags),
            "resources " + " ".join(endpoint.resources),
            "operation_class " + endpoint.operation_class,
            "request_schemas " + " ".join(endpoint.request_schemas),
            "response_schemas " + " ".join(endpoint.response_schemas),
            "security " + " ".join(endpoint.security),
            param_text,
        ]
    )


def build_rag_corpus(bundle: NormalizedBundle) -> RagCorpus:
    docs: list[dict[str, Any]] = []
    for endpoint in bundle.endpoints:
        docs.append(
            {
                "id": f"endpoint:{endpoint.id}",
                "kind": "endpoint",
                "endpoint_id": endpoint.id,
                "text": endpoint_text(endpoint),
            }
        )
        for param in endpoint.params:
            docs.append(
                {
                    "id": f"param:{endpoint.id}.{param.location}.{param.name}",
                    "kind": "parameter",
                    "endpoint_id": endpoint.id,
                    "text": f"{endpoint.id} {endpoint.path} {param.location} parameter {param.name} required {param.required} {param.description} {param.schema_name or ''}",
                }
            )
        for schema_name in endpoint.request_schemas:
            docs.append(
                {
                    "id": f"request_schema:{endpoint.id}.{schema_name}",
                    "kind": "request_schema",
                    "endpoint_id": endpoint.id,
                    "text": f"{endpoint.id} request schema {schema_name}",
                }
            )
        for schema_name in endpoint.response_schemas:
            docs.append(
                {
                    "id": f"response_schema:{endpoint.id}.{schema_name}",
                    "kind": "response_schema",
                    "endpoint_id": endpoint.id,
                    "text": f"{endpoint.id} response schema {schema_name}",
                }
            )
        if endpoint.security:
            docs.append(
                {
                    "id": f"auth:{endpoint.id}",
                    "kind": "auth",
                    "endpoint_id": endpoint.id,
                    "text": f"{endpoint.id} auth security {' '.join(endpoint.security)}",
                }
            )
    return RagCorpus(documents=docs)


def write_rag_corpus(corpus: RagCorpus, out_dir: Path) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)
    with (out_dir / "rag_corpus.jsonl").open("w", encoding="utf-8") as fh:
        for doc in corpus.documents:
            fh.write(json.dumps(doc, sort_keys=True) + "\n")


def read_rag_corpus(artifacts_dir: Path) -> RagCorpus:
    docs = [json.loads(line) for line in (artifacts_dir / "rag_corpus.jsonl").read_text(encoding="utf-8").splitlines() if line.strip()]
    return RagCorpus(documents=docs)
