from __future__ import annotations

from pathlib import Path

import pytest

from corpus.features.sources import (
    LocalSourceRepository,
    SourceNotFound,
    SourceState,
)


def test_repository_keeps_owner_sources_isolated_and_revision_paths_opaque(
    tmp_path: Path,
) -> None:
    repository = LocalSourceRepository(tmp_path / "sources")

    prepared = repository.begin_source(
        owner_key="owner-a",
        connector_key="api",
        display_name="Widgets",
        original_filename="widgets.json",
        content=b'{"openapi":"3.0.3"}',
    )

    assert prepared.input_path.read_bytes() == b'{"openapi":"3.0.3"}'
    assert prepared.artifact_dir.parent.name == prepared.revision.revision_id
    assert "owner-a" not in str(prepared.artifact_dir)
    assert repository.get(
        owner_key="owner-a", source_id=prepared.source.source_id
    ).revision.state is SourceState.PROCESSING
    assert repository.list(owner_key="owner-b") == ()
    with pytest.raises(SourceNotFound):
        repository.get(
            owner_key="owner-b", source_id=prepared.source.source_id
        )


def test_repository_atomically_marks_ready_and_failed_revisions(
    tmp_path: Path,
) -> None:
    repository = LocalSourceRepository(tmp_path / "sources")
    ready = repository.begin_source(
        owner_key="owner-a",
        connector_key="api",
        display_name="Ready API",
        original_filename="ready.yaml",
        content=b"openapi: 3.0.3",
    )

    ready_view = repository.mark_ready(
        owner_key="owner-a",
        source_id=ready.source.source_id,
        revision_id=ready.revision.revision_id,
        summary={"endpoint_count": 3},
    )

    assert ready_view.revision.state is SourceState.READY
    assert ready_view.revision.summary == {"endpoint_count": 3}
    assert not tuple((tmp_path / "sources").rglob("*.tmp"))

    failed = repository.begin_source(
        owner_key="owner-a",
        connector_key="api",
        display_name="Broken API",
        original_filename="broken.json",
        content=b"{}",
    )
    failed_view = repository.mark_failed(
        owner_key="owner-a",
        source_id=failed.source.source_id,
        revision_id=failed.revision.revision_id,
        failure_code="invalid_api_collection",
        failure_message="No OpenAPI version was declared.",
    )
    assert failed_view.revision.state is SourceState.FAILED
    assert failed_view.revision.failure_code == "invalid_api_collection"

