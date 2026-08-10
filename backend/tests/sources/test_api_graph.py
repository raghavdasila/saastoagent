from __future__ import annotations

import asyncio
import json
import uuid
from pathlib import Path
from types import SimpleNamespace

from corpus.features.sources.connectors.api.graph import ApiGraphPresenter
from corpus.features.sources.operations import GraphStageSelectionHandler
from corpus.features.sources.repository import LocalSourceRepository


def test_graph_presenter_returns_persisted_safe_graph_and_playback(
    tmp_path: Path,
) -> None:
    repository = LocalSourceRepository(tmp_path / "sources")
    prepared = repository.begin_source(
        owner_key="owner-a",
        connector_key="api",
        display_name="Catalog",
        original_filename="catalog.yaml",
        content=b"openapi: 3.0.3\npaths: {}\n",
    )
    repository.mark_running(
        owner_key="owner-a",
        source_id=prepared.source.source_id,
        revision_id=prepared.revision.revision_id,
    )
    repository.mark_ready(
        owner_key="owner-a",
        source_id=prepared.source.source_id,
        revision_id=prepared.revision.revision_id,
        summary={"endpoint_count": 1},
    )
    graph_dir = prepared.artifact_dir / "graph"
    graph_dir.mkdir()
    (graph_dir / "semantic_graph.json").write_text(
        json.dumps(
            {
                "nodes": [
                    {
                        "id": "api_operation:catalog:listProducts",
                        "node_type": "api_operation",
                        "label": "GET /products",
                        "endpoint_id": "catalog:listProducts",
                        "facets": {
                            "method": "GET",
                            "operation_id": "listProducts",
                            "path": "/products",
                            "example_secret": "must-not-leak",
                        },
                        "evidence": [{"value": "must-not-leak"}],
                    },
                    {
                        "id": "resource:products",
                        "node_type": "resource",
                        "label": "products",
                        "endpoint_id": None,
                        "facets": {"resource": "products"},
                        "evidence": [],
                    },
                ],
                "edges": [
                    {
                        "source": "api_operation:catalog:listProducts",
                        "target": "resource:products",
                        "type": "exposes",
                        "status": "observed",
                        "confidence": 0.95,
                        "evidence": [{"value": "must-not-leak"}],
                    }
                ],
                "metadata": {
                    "assembler": "resource_first_v1",
                    "construction_conformance": {
                        "stage_order": ["ingest", "connect"],
                        "stages": {
                            "ingest": {
                                "status": "pass",
                                "metrics": {"endpoint_count": 1},
                                "warnings": [],
                            },
                            "connect": {
                                "status": "warning",
                                "metrics": {"edge_count": 1},
                                "warnings": [
                                    {
                                        "code": "example_warning",
                                        "message": "internal detail",
                                    }
                                ],
                            },
                        },
                    },
                },
            }
        ),
        encoding="utf-8",
    )
    (graph_dir / "graph_trace.jsonl").write_text(
        "\n".join((
            json.dumps({"type": "operation_added", "active_endpoint_id": "catalog:listProducts", "added_nodes": [{"id": "api_operation:catalog:listProducts"}], "updated_nodes": [], "added_edges": [], "cumulative": {"nodes": 1, "unique_edges": 0}}),
            json.dumps({"type": "resource_connected", "active_endpoint_id": "catalog:listProducts", "added_nodes": [{"id": "resource:products"}], "updated_nodes": [{"node_id": "resource:products", "evidence_added": 1}], "added_edges": [{"id": "api_operation:catalog:listProducts|exposes|resource:products"}], "cumulative": {"nodes": 2, "unique_edges": 1}}),
            json.dumps({"type": "cards_complete", "added_nodes": [], "updated_nodes": [], "added_edges": [], "cumulative": {"nodes": 2, "edges": 1, "cards": 2}}),
        )) + "\n",
        encoding="utf-8",
    )

    result = ApiGraphPresenter(repository).inspect(
        owner_key="owner-a",
        source_id=prepared.source.source_id,
    )

    assert result.revision_id == prepared.revision.revision_id
    assert result.total_nodes == 2
    assert result.total_edges == 1
    assert result.semantic_groups[0].label == "products"
    assert result.semantic_groups[0].operation_ids == (
        "api_operation:catalog:listProducts",
    )
    assert [stage.id for stage in result.playback] == ["ingest", "connect"]
    assert result.playback[1].warning_codes == ("example_warning",)
    assert result.trace[1].updated_node_ids == ("resource:products",)
    assert result.trace[2].cumulative_edges == 1
    serialized = result.model_dump_json()
    assert "must-not-leak" not in serialized
    assert "internal detail" not in serialized


def test_graph_stage_selection_is_bound_to_owner_source_revision_and_artifact(
    tmp_path: Path,
) -> None:
    asyncio.run(_exercise_graph_stage_selection(tmp_path))


async def _exercise_graph_stage_selection(tmp_path: Path) -> None:
    owner_id = uuid.UUID("00000000-0000-0000-0000-000000000001")
    repository = LocalSourceRepository(tmp_path / "sources")
    prepared = repository.begin_source(
        owner_key=str(owner_id),
        connector_key="api",
        display_name="Catalog",
        original_filename="catalog.yaml",
        content=b"openapi: 3.0.3\npaths: {}\n",
    )
    repository.mark_running(
        owner_key=str(owner_id),
        source_id=prepared.source.source_id,
        revision_id=prepared.revision.revision_id,
    )
    repository.mark_ready(
        owner_key=str(owner_id),
        source_id=prepared.source.source_id,
        revision_id=prepared.revision.revision_id,
        summary={"endpoint_count": 1},
    )
    graph_dir = prepared.artifact_dir / "graph"
    graph_dir.mkdir()
    (graph_dir / "semantic_graph.json").write_text(
        json.dumps(
            {
                "nodes": [],
                "edges": [],
                "metadata": {
                    "assembler": "resource_first_v1",
                    "construction_conformance": {
                        "stage_order": ["ingest", "connect"],
                        "stages": {
                            "ingest": {"status": "pass", "metrics": {}, "warnings": []},
                            "connect": {"status": "pass", "metrics": {}, "warnings": []},
                        },
                    },
                },
            }
        ),
        encoding="utf-8",
    )
    (graph_dir / "graph_trace.jsonl").write_text(
        json.dumps({"type": "graph_complete", "added_nodes": [], "updated_nodes": [], "added_edges": [], "cumulative": {"nodes": 0, "unique_edges": 0}}) + "\n",
        encoding="utf-8",
    )
    context = SimpleNamespace(
        session_id="source-session",
        attempt_id="source-attempt",
        request_id="source-request",
    )

    class FixedOwnerScope:
        def __init__(self, value: uuid.UUID) -> None:
            self.value = value

        async def organization_id_for_route(self, session_id: str) -> uuid.UUID:
            assert session_id == "source-session"
            return self.value

    handler = GraphStageSelectionHandler(
        ApiGraphPresenter(repository),
        FixedOwnerScope(owner_id),  # type: ignore[arg-type]
    )
    base = {
        "source_id": prepared.source.source_id,
        "revision_id": prepared.revision.revision_id,
        "stage_id": "connect",
    }
    selected = await handler(base, context)  # type: ignore[arg-type]
    assert selected.outcome == "selected"

    wrong_revision = await handler(
        {**base, "revision_id": "x" * 16}, context  # type: ignore[arg-type]
    )
    assert wrong_revision.failure is not None
    assert wrong_revision.failure.code == "graph_stage_unavailable"

    missing_stage = await handler(
        {**base, "stage_id": "not-recorded"}, context  # type: ignore[arg-type]
    )
    assert missing_stage.failure is not None
    assert missing_stage.failure.code == "graph_stage_unavailable"

    other_owner = GraphStageSelectionHandler(
        ApiGraphPresenter(repository),
        FixedOwnerScope(uuid.UUID("00000000-0000-0000-0000-000000000002")),  # type: ignore[arg-type]
    )
    unavailable = await other_owner(base, context)  # type: ignore[arg-type]
    assert unavailable.failure is not None
    assert unavailable.failure.code == "graph_stage_unavailable"
