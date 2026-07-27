from __future__ import annotations

from pathlib import Path

import pytest

from corpus.features.sources import (
    LocalSourceRepository,
    SourceService,
    SourceState,
)
from corpus.features.sources.connectors.api import ApiSourceConnector, SourceUpload
from corpus.features.sources.connectors.api.toolrouter import (
    ToolRouterApiSourceEngine,
)
from corpus.integrations.toolrouter import (
    ToolRouterAdapter,
    ToolRouterSettings,
)
from backend.tests.integrations.toolrouter.conftest import (
    KeywordEmbeddingProvider,
    write_openapi_fixture,
)


def _service(tmp_path: Path) -> SourceService:
    return SourceService(
        LocalSourceRepository(tmp_path / "sources"),
        connectors=(
            ApiSourceConnector(
                ToolRouterApiSourceEngine(
                    ToolRouterAdapter(
                        ToolRouterSettings(),
                        embedding_provider=KeywordEmbeddingProvider(),
                    )
                ),
                max_upload_bytes=20 * 1024 * 1024,
            ),
        ),
    )


def test_service_processes_api_connector_without_a_generic_type_switch(
    tmp_path: Path,
) -> None:
    service = _service(tmp_path)
    source_file = write_openapi_fixture(tmp_path / "widgets.json")

    created = service.create_source(
        owner_key="owner-a",
        connector_key="api",
        display_name="Widget API",
        upload=SourceUpload(
            filename="widgets.json",
            content_type="application/json",
            content=source_file.read_bytes(),
        ),
    )

    assert created.connector_key == "api"
    assert created.revision.state is SourceState.READY
    assert created.revision.summary["endpoint_count"] == 3
    assert service.list_sources(owner_key="owner-a") == (created,)
    retrieval = service.retrieve(
        owner_key="owner-a",
        source_id=created.source_id,
        query="list widgets",
        top_k=3,
        trace_mode="bounded",
        provided_params=None,
    )
    assert retrieval.steps[0].ranked_items


def test_service_persists_failed_processing_without_claiming_readiness(
    tmp_path: Path,
) -> None:
    service = _service(tmp_path)

    with pytest.raises(Exception):
        service.create_source(
            owner_key="owner-a",
            connector_key="api",
            display_name="Broken API",
            upload=SourceUpload(
                filename="broken.json",
                content_type="application/json",
                content=(
                    b'{"openapi":"3.0.3","info":{"title":"Broken",'
                    b'"version":"1"},"paths":{}}'
                ),
            ),
        )

    failed = service.list_sources(owner_key="owner-a")
    assert len(failed) == 1
    assert failed[0].revision.state is SourceState.FAILED
    assert failed[0].revision.failure_code == "source_processing_failed"
