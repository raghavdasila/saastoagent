from __future__ import annotations

import json
from pathlib import Path

import numpy as np

from corpus.integrations.toolrouter import (
    IngestRequest,
    ToolRouterAdapter,
    ToolRouterSettings,
)

from .conftest import KeywordEmbeddingProvider, write_openapi_fixture


def test_ingest_persists_normalized_graph_index_and_provenance(
    tmp_path: Path,
) -> None:
    source = write_openapi_fixture(tmp_path / "widget-api.json")
    artifacts = tmp_path / "artifacts"
    adapter = ToolRouterAdapter(
        ToolRouterSettings(),
        embedding_provider=KeywordEmbeddingProvider(),
    )

    result = adapter.ingest(
        IngestRequest(source_path=source, artifact_dir=artifacts)
    )

    assert result.endpoint_count == 3
    assert result.schema_count >= 1
    assert result.graph_node_count > result.endpoint_count
    assert result.graph_edge_count > 0
    assert result.graph_card_count == result.graph_node_count
    assert result.repair_count == 0
    assert result.validation_status == "valid"
    assert (artifacts / "normalized" / "openapi_normalized.json").is_file()
    assert (artifacts / "graph" / "semantic_graph.json").is_file()
    assert (artifacts / "graph" / "embeddings.npy").is_file()
    assert (artifacts / "graph" / "graph_trace.jsonl").is_file()
    manifest = json.loads(
        (artifacts / "integration_manifest.json").read_text(encoding="utf-8")
    )
    assert manifest["graph_mode"] == "resource_first_v1"
    assert manifest["embedding_model"] == (
        "sentence-transformers/all-MiniLM-L6-v2"
    )
    assert manifest["embedding_revision"] == (
        "1110a243fdf4706b3f48f1d95db1a4f5529b4d41"
    )
    assert np.load(artifacts / "graph" / "embeddings.npy").shape[0] == (
        result.graph_card_count
    )


def test_ingest_rejects_a_document_without_openapi_endpoints(
    tmp_path: Path,
) -> None:
    source = tmp_path / "empty.json"
    source.write_text(
        '{"openapi":"3.0.3","info":{"title":"Empty","version":"1"},"paths":{}}',
        encoding="utf-8",
    )
    adapter = ToolRouterAdapter(
        ToolRouterSettings(),
        embedding_provider=KeywordEmbeddingProvider(),
    )

    try:
        adapter.ingest(
            IngestRequest(source_path=source, artifact_dir=tmp_path / "out")
        )
    except Exception as error:
        assert type(error).__name__ == "ToolRouterInputError"
        assert "no operations" in str(error).casefold()
    else:
        raise AssertionError("An endpoint-free OpenAPI document must fail")

