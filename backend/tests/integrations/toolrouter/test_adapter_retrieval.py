from __future__ import annotations

from pathlib import Path

from corpus.integrations.toolrouter import (
    IngestRequest,
    RetrievalRequest,
    ToolRouterAdapter,
    ToolRouterSettings,
)

from .conftest import KeywordEmbeddingProvider, write_openapi_fixture


def test_retrieval_reloads_persisted_index_and_returns_grag_evidence(
    tmp_path: Path,
) -> None:
    artifacts = tmp_path / "artifacts"
    provider = KeywordEmbeddingProvider()
    adapter = ToolRouterAdapter(
        ToolRouterSettings(), embedding_provider=provider
    )
    adapter.ingest(
        IngestRequest(
            source_path=write_openapi_fixture(tmp_path / "widget-api.json"),
            artifact_dir=artifacts,
        )
    )

    restarted = ToolRouterAdapter(
        ToolRouterSettings(), embedding_provider=provider
    )
    result = restarted.retrieve(
        RetrievalRequest(
            artifact_dir=artifacts,
            query="list every widget",
            top_k=3,
            trace_mode="full",
        )
    )

    assert result.query == "list every widget"
    assert result.decision_type in {
        "ROUTE",
        "ASK_DISAMBIGUATE",
        "ASK_PARAM",
        "NO_TOOL",
        "ABSTAIN",
    }
    assert result.decision_reason
    assert result.steps
    assert result.steps[0].ranked_endpoints
    assert result.steps[0].ranked_endpoints[0].endpoint_id.endswith(
        "listWidgets"
    )
    assert result.steps[0].trace["trace_mode"] == "full"
    assert result.steps[0].trace["top_seed_cards"]


def test_retrieval_reports_missing_required_openapi_parameters(
    tmp_path: Path,
) -> None:
    artifacts = tmp_path / "artifacts"
    adapter = ToolRouterAdapter(
        ToolRouterSettings(), embedding_provider=KeywordEmbeddingProvider()
    )
    adapter.ingest(
        IngestRequest(
            source_path=write_openapi_fixture(tmp_path / "widget-api.json"),
            artifact_dir=artifacts,
        )
    )

    result = adapter.retrieve(
        RetrievalRequest(
            artifact_dir=artifacts,
            query="delete widget",
            provided_params={},
        )
    )

    assert result.decision_type == "ASK_PARAM"
    assert "widget_id" in result.missing_params

