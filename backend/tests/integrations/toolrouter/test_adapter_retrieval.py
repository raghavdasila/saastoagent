from __future__ import annotations

from pathlib import Path
import hashlib
import json

import pytest
import numpy as np

from corpus.integrations.toolrouter import (
    IngestRequest,
    ManagedParameter,
    RetrievalRequest,
    ToolRouterAdapter,
    ToolRouterInputError,
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


def test_curated_subset_is_the_retrieval_corpus_and_does_not_mutate_artifacts(
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
    graph_path = artifacts / "graph" / "semantic_graph.json"
    before = hashlib.sha256(graph_path.read_bytes()).hexdigest()
    graph = json.loads(graph_path.read_text(encoding="utf-8"))
    endpoint_ids = tuple(
        sorted(
            {
                str(card["endpoint_id"])
                for card in graph["cards"]
                if card.get("endpoint_id")
            }
        )
    )
    allowed = tuple(value for value in endpoint_ids if value.endswith("deleteWidget"))
    assert len(allowed) == 1

    result = adapter.retrieve(
        RetrievalRequest(
            artifact_dir=artifacts,
            query="list every widget",
            top_k=5,
            allowed_endpoint_ids=allowed,
        )
    )

    ranked = {
        item.endpoint_id
        for step in result.steps
        for item in step.ranked_endpoints
    }
    assert ranked
    assert ranked <= set(allowed)
    assert hashlib.sha256(graph_path.read_bytes()).hexdigest() == before


def test_full_curated_subset_is_result_equivalent(tmp_path: Path) -> None:
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
    graph = json.loads(
        (artifacts / "graph" / "semantic_graph.json").read_text(encoding="utf-8")
    )
    endpoint_ids = tuple(
        sorted(
            {
                str(card["endpoint_id"])
                for card in graph["cards"]
                if card.get("endpoint_id")
            }
        )
    )
    request = dict(
        artifact_dir=artifacts,
        query="delete widget",
        top_k=5,
        provided_params={},
        trace_mode="full",
    )

    assert adapter.retrieve(RetrievalRequest(**request)) == adapter.retrieve(
        RetrievalRequest(**request, allowed_endpoint_ids=endpoint_ids)
    )


def test_curated_subset_rejects_empty_duplicate_and_unknown_ids(tmp_path: Path) -> None:
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

    for allowed in ((), ("missing",), ("missing", "missing")):
        with pytest.raises(ToolRouterInputError):
            adapter.retrieve(
                RetrievalRequest(
                    artifact_dir=artifacts,
                    query="list widgets",
                    allowed_endpoint_ids=allowed,
                )
            )


def test_managed_profile_header_satisfies_real_router_without_a_value(
    tmp_path: Path,
) -> None:
    spec = tmp_path / "medusa-taxonomy.json"
    spec.write_text(
        json.dumps(
            {
                "openapi": "3.0.3",
                "info": {"title": "Medusa Store", "version": "2.0.0"},
                "paths": {
                    "/store/product-tags": {
                        "get": {
                            "operationId": "GetProductTags",
                            "summary": "List product tags",
                            "parameters": [_publishable_key_parameter()],
                            "responses": {"200": {"description": "Product tags"}},
                        }
                    },
                    "/store/product-types": {
                        "get": {
                            "operationId": "GetProductTypes",
                            "summary": "List product types",
                            "parameters": [_publishable_key_parameter()],
                            "responses": {"200": {"description": "Product types"}},
                        }
                    },
                    "/store/product-types/{id}": {
                        "get": {
                            "operationId": "GetProductTypesId",
                            "summary": "Get product type by id",
                            "parameters": [
                                _publishable_key_parameter(),
                                {
                                    "name": "id",
                                    "in": "path",
                                    "required": True,
                                    "schema": {"type": "string"},
                                },
                            ],
                            "responses": {"200": {"description": "Product type"}},
                        }
                    },
                },
            }
        ),
        encoding="utf-8",
    )
    artifacts = tmp_path / "artifacts"
    adapter = ToolRouterAdapter(
        ToolRouterSettings(), embedding_provider=_TaxonomyEmbeddingProvider()
    )
    adapter.ingest(IngestRequest(source_path=spec, artifact_dir=artifacts))
    graph = json.loads(
        (artifacts / "graph" / "semantic_graph.json").read_text(encoding="utf-8")
    )
    endpoint_ids = {
        str(card["endpoint_id"])
        for card in graph["cards"]
        if card.get("endpoint_id")
    }
    types_id = next(value for value in endpoint_ids if value.endswith("GetProductTypesId"))
    taxonomy = tuple(
        sorted(
            value
            for value in endpoint_ids
            if value.endswith(("GetProductTags", "GetProductTypes"))
        )
    )

    ambiguous = adapter.retrieve(
        RetrievalRequest(
            artifact_dir=artifacts,
            query="get product taxonomy",
            provided_params={},
            allowed_endpoint_ids=taxonomy,
            managed_parameters=(
                ManagedParameter(name="X-Publishable-Api-Key", location="header"),
            ),
        )
    )
    chosen = adapter.retrieve(
        RetrievalRequest(
            artifact_dir=artifacts,
            query="get product taxonomy",
            provided_params={},
            allowed_endpoint_ids=(types_id,),
            managed_parameters=(
                ManagedParameter(name="X-Publishable-Api-Key", location="header"),
            ),
        )
    )
    unmanaged = adapter.retrieve(
        RetrievalRequest(
            artifact_dir=artifacts,
            query="get product taxonomy",
            provided_params={},
            allowed_endpoint_ids=(types_id,),
        )
    )
    wrong_location = adapter.retrieve(
        RetrievalRequest(
            artifact_dir=artifacts,
            query="get product taxonomy",
            provided_params={},
            allowed_endpoint_ids=(types_id,),
            managed_parameters=(
                ManagedParameter(name="x-publishable-api-key", location="query"),
            ),
        )
    )

    assert ambiguous.decision_type == "ASK_DISAMBIGUATE"
    assert chosen.decision_type == "ASK_PARAM"
    assert chosen.missing_params == ("id",)
    assert "x-publishable-api-key" not in chosen.missing_params
    assert chosen.decision_evidence["provided_param_names"] == []
    assert set(unmanaged.missing_params) == {"id", "x-publishable-api-key"}
    assert set(wrong_location.missing_params) == {"id", "x-publishable-api-key"}


def _publishable_key_parameter() -> dict[str, object]:
    return {
        "name": "x-publishable-api-key",
        "in": "header",
        "required": True,
        "schema": {"type": "string"},
    }


class _TaxonomyEmbeddingProvider:
    vocabulary = ("get", "list", "product", "tag", "tags", "type", "types", "id")

    def embed_texts(self, texts: list[str]) -> np.ndarray:
        return np.asarray(
            [
                [float(text.casefold().count(term)) for term in self.vocabulary]
                for text in texts
            ],
            dtype=np.float32,
        )
