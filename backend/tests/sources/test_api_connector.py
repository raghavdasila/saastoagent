from __future__ import annotations

from pathlib import Path

import pytest

from corpus.features.sources.connectors.api import (
    ApiSourceConnector,
    SourceUpload,
    SourceUploadError,
)
from corpus.features.sources.connectors.api.toolrouter import (
    ToolRouterApiSourceEngine,
)
from corpus.features.sources.contracts import SourceRetrievalResult
from corpus.integrations.toolrouter import ToolRouterAdapter, ToolRouterSettings
from backend.tests.integrations.toolrouter.conftest import (
    KeywordEmbeddingProvider,
    write_openapi_fixture,
)


@pytest.mark.parametrize(
    ("filename", "content", "message"),
    [
        ("empty.json", b"", "empty"),
        ("notes.txt", b"not an API", "JSON, YAML, or YML"),
        ("../api.json", b"{}", "plain filename"),
        ("api.json", b"{}", "OpenAPI or Swagger version"),
    ],
)
def test_api_upload_validation_rejects_unsafe_or_unsupported_input(
    filename: str,
    content: bytes,
    message: str,
) -> None:
    connector = ApiSourceConnector(
        ToolRouterApiSourceEngine(
            ToolRouterAdapter(
                ToolRouterSettings(),
                embedding_provider=KeywordEmbeddingProvider(),
            )
        ),
        max_upload_bytes=1024,
    )

    with pytest.raises(SourceUploadError, match=message):
        connector.validate_upload(
            SourceUpload(
                filename=filename,
                content_type="application/json",
                content=content,
            )
        )


def test_api_connector_runs_real_toolrouter_ingestion_and_retrieval(
    tmp_path: Path,
) -> None:
    source = write_openapi_fixture(tmp_path / "widgets.json")
    connector = ApiSourceConnector(
        ToolRouterApiSourceEngine(
            ToolRouterAdapter(
                ToolRouterSettings(),
                embedding_provider=KeywordEmbeddingProvider(),
            )
        ),
        max_upload_bytes=20 * 1024 * 1024,
    )
    upload = connector.validate_upload(
        SourceUpload(
            filename="widgets.json",
            content_type="application/json",
            content=source.read_bytes(),
        )
    )
    input_path = tmp_path / upload.filename
    input_path.write_bytes(upload.content)

    summary = connector.ingest(
        input_path=input_path,
        artifact_dir=tmp_path / "artifacts",
    )
    retrieval = connector.retrieve(
        artifact_dir=tmp_path / "artifacts",
        query="list widgets",
        top_k=3,
        trace_mode="bounded",
        provided_params=None,
    )

    assert summary["endpoint_count"] == 3
    assert isinstance(retrieval, SourceRetrievalResult)
    assert retrieval.steps[0].ranked_items[0].item_kind == "api_operation"
    assert retrieval.steps[0].ranked_items[0].item_id.endswith("listWidgets")


def test_only_the_api_toolrouter_bridge_imports_toolrouter() -> None:
    sources_root = (
        Path(__file__).resolve().parents[2]
        / "src"
        / "corpus"
        / "features"
        / "sources"
    )
    leaking = []
    for path in sources_root.rglob("*.py"):
        relative = path.relative_to(sources_root).as_posix()
        if relative == "connectors/api/toolrouter.py":
            continue
        if "corpus.integrations.toolrouter" in path.read_text(encoding="utf-8"):
            leaking.append(relative)
    assert leaking == []


def test_generic_sources_http_has_no_connector_specific_transport() -> None:
    sources_root = (
        Path(__file__).resolve().parents[2]
        / "src"
        / "corpus"
        / "features"
        / "sources"
    )
    http_source = (sources_root / "http.py").read_text(encoding="utf-8")

    assert ".connectors.api" not in http_source
    assert 'router.post("/api"' not in http_source
    assert "UploadFile" not in http_source
    assert "invalid_api_collection" not in http_source
