from __future__ import annotations

import json
import uuid
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from routedeck_fastapi import SameOriginMutationPolicy

from corpus.features.sources.connectors.api.operation_curation import (
    ApiOperationCurationConflict,
    ApiOperationCurationError,
    ApiOperationCurationService,
)
from corpus.features.sources.repository import LocalSourceRepository, SourceNotFound
from corpus.features.sources.connectors.api.http import create_api_source_router
from corpus.features.sources.http import SourceHttpProblem, source_problem_response
from backend.tests.sources.test_http import OwnerResolver, _auth_settings


OWNER = uuid.UUID("00000000-0000-0000-0000-000000000001")
OTHER_OWNER = uuid.UUID("00000000-0000-0000-0000-000000000002")


def test_operation_curation_is_exact_immutable_and_reloadable(tmp_path: Path) -> None:
    repository, source_id, revision_id = _ready_source(tmp_path)
    service = ApiOperationCurationService(repository)

    initial = service.inspect(
        owner_id=OWNER,
        source_id=source_id,
        source_revision_id=revision_id,
    )
    assert [item.operation_id for item in initial.operations] == [
        "createWidget",
        "listWidgets",
    ]
    assert initial.current is None
    assert initial.history == ()

    first = service.save(
        owner_id=OWNER,
        source_id=source_id,
        source_revision_id=revision_id,
        inventory_fingerprint=initial.inventory_fingerprint,
        included_operation_ids=("listWidgets",),
        excluded_operation_ids=("createWidget",),
        expected_current_curation_id=None,
    )
    assert first.previous_curation_id is None
    assert first.included_operation_ids == ("listWidgets",)
    assert first.excluded_operation_ids == ("createWidget",)

    reloaded = ApiOperationCurationService(
        LocalSourceRepository(tmp_path / "sources")
    ).inspect(
        owner_id=OWNER,
        source_id=source_id,
        source_revision_id=revision_id,
    )
    assert reloaded.current == first
    assert reloaded.history == (first,)

    second = service.save(
        owner_id=OWNER,
        source_id=source_id,
        source_revision_id=revision_id,
        inventory_fingerprint=initial.inventory_fingerprint,
        included_operation_ids=("createWidget", "listWidgets"),
        excluded_operation_ids=(),
        expected_current_curation_id=first.id,
    )
    assert second.id != first.id
    assert second.previous_curation_id == first.id
    assert service.inspect(
        owner_id=OWNER,
        source_id=source_id,
        source_revision_id=revision_id,
    ).history == (first, second)


@pytest.mark.parametrize(
    ("included", "excluded", "message"),
    [
        (("listWidgets", "listWidgets"), ("createWidget",), "duplicate"),
        (("listWidgets",), ("unknownOperation",), "unknown"),
        (("listWidgets",), (), "every discovered operation"),
        (("listWidgets",), ("listWidgets", "createWidget"), "both included and excluded"),
    ],
)
def test_invalid_selection_never_replaces_prior_curation(
    tmp_path: Path,
    included: tuple[str, ...],
    excluded: tuple[str, ...],
    message: str,
) -> None:
    repository, source_id, revision_id = _ready_source(tmp_path)
    service = ApiOperationCurationService(repository)
    inventory = service.inspect(
        owner_id=OWNER,
        source_id=source_id,
        source_revision_id=revision_id,
    )
    prior = service.save(
        owner_id=OWNER,
        source_id=source_id,
        source_revision_id=revision_id,
        inventory_fingerprint=inventory.inventory_fingerprint,
        included_operation_ids=("listWidgets",),
        excluded_operation_ids=("createWidget",),
        expected_current_curation_id=None,
    )

    with pytest.raises(ApiOperationCurationConflict, match=message):
        service.save(
            owner_id=OWNER,
            source_id=source_id,
            source_revision_id=revision_id,
            inventory_fingerprint=inventory.inventory_fingerprint,
            included_operation_ids=included,
            excluded_operation_ids=excluded,
            expected_current_curation_id=prior.id,
        )

    after = service.inspect(
        owner_id=OWNER,
        source_id=source_id,
        source_revision_id=revision_id,
    )
    assert after.current == prior
    assert after.history == (prior,)


def test_stale_inventory_and_owner_are_rejected_without_mutation(tmp_path: Path) -> None:
    repository, source_id, revision_id = _ready_source(tmp_path)
    service = ApiOperationCurationService(repository)
    inventory = service.inspect(
        owner_id=OWNER,
        source_id=source_id,
        source_revision_id=revision_id,
    )

    with pytest.raises(ApiOperationCurationConflict, match="inventory changed"):
        service.save(
            owner_id=OWNER,
            source_id=source_id,
            source_revision_id=revision_id,
            inventory_fingerprint="0" * 64,
            included_operation_ids=("listWidgets",),
            excluded_operation_ids=("createWidget",),
            expected_current_curation_id=None,
        )
    with pytest.raises(SourceNotFound):
        service.inspect(
            owner_id=OTHER_OWNER,
            source_id=source_id,
            source_revision_id=revision_id,
        )
    assert service.inspect(
        owner_id=OWNER,
        source_id=source_id,
        source_revision_id=revision_id,
    ).history == ()


def test_concurrent_saves_use_exact_current_curation_cas(tmp_path: Path) -> None:
    repository, source_id, revision_id = _ready_source(tmp_path)
    service = ApiOperationCurationService(repository)
    inventory = service.inspect(
        owner_id=OWNER,
        source_id=source_id,
        source_revision_id=revision_id,
    )

    def save(included: tuple[str, ...], excluded: tuple[str, ...]):
        return service.save(
            owner_id=OWNER,
            source_id=source_id,
            source_revision_id=revision_id,
            inventory_fingerprint=inventory.inventory_fingerprint,
            included_operation_ids=included,
            excluded_operation_ids=excluded,
            expected_current_curation_id=None,
        )

    with ThreadPoolExecutor(max_workers=2) as executor:
        futures = [
            executor.submit(save, ("listWidgets",), ("createWidget",)),
            executor.submit(save, ("createWidget",), ("listWidgets",)),
        ]
    successes = [future.result() for future in futures if future.exception() is None]
    conflicts = [future.exception() for future in futures if future.exception() is not None]
    assert len(successes) == 1
    assert len(conflicts) == 1
    assert isinstance(conflicts[0], ApiOperationCurationConflict)
    view = service.inspect(
        owner_id=OWNER,
        source_id=source_id,
        source_revision_id=revision_id,
    )
    assert view.history == (successes[0],)
    assert view.current == successes[0]


def test_persisted_history_is_bound_to_exact_owner_revision_inventory_and_chain(
    tmp_path: Path,
) -> None:
    repository, source_id, revision_id = _ready_source(tmp_path)
    service = ApiOperationCurationService(repository)
    inventory = service.inspect(
        owner_id=OWNER,
        source_id=source_id,
        source_revision_id=revision_id,
    )
    saved = service.save(
        owner_id=OWNER,
        source_id=source_id,
        source_revision_id=revision_id,
        inventory_fingerprint=inventory.inventory_fingerprint,
        included_operation_ids=("listWidgets",),
        excluded_operation_ids=("createWidget",),
        expected_current_curation_id=None,
    )
    record_path = (
        repository.revision_dir(owner_key=str(OWNER), source_id=source_id)
        / "operation-curation"
        / "records"
        / f"{saved.id}.json"
    )
    document = json.loads(record_path.read_text(encoding="utf-8"))
    document["selected_by_owner_id"] = str(OTHER_OWNER)
    record_path.write_text(json.dumps(document), encoding="utf-8")

    with pytest.raises(ApiOperationCurationError, match="inconsistent"):
        service.inspect(
            owner_id=OWNER,
            source_id=source_id,
            source_revision_id=revision_id,
        )


def test_operation_curation_http_is_owner_scoped_and_body_free(tmp_path: Path) -> None:
    repository, source_id, revision_id = _ready_source(tmp_path)
    service = ApiOperationCurationService(repository)
    app = FastAPI()
    app.add_exception_handler(SourceHttpProblem, source_problem_response)
    app.include_router(
        create_api_source_router(
            service=object(),
            auth_service=OwnerResolver(),  # type: ignore[arg-type]
            auth_settings=_auth_settings(),
            mutation_policy=SameOriginMutationPolicy(
                trusted_origins=frozenset({"http://127.0.0.1:5199"})
            ),
            max_upload_bytes=1024,
            graph_presenter=object(),
            connection_profiles=object(),
            contract_revision_service=object(),
            connection_check_service=object(),
            operation_curation_service=service,
            route_plan_service=object(),
        )
    )
    with TestClient(app) as client:
        client.headers["Authorization"] = "Bearer owner-a"
        response = client.get(
            f"/api/sources/{source_id}/operation-curation",
            params={"revision_id": revision_id},
        )
        assert response.status_code == 200
        assert response.json()["source_revision_id"] == revision_id
        assert len(response.json()["operations"]) == 2
        client.headers["Authorization"] = "Bearer owner-b"
        hidden = client.get(
            f"/api/sources/{source_id}/operation-curation",
            params={"revision_id": revision_id},
        )
        assert hidden.status_code == 404


def _ready_source(tmp_path: Path) -> tuple[LocalSourceRepository, str, str]:
    repository = LocalSourceRepository(tmp_path / "sources")
    prepared = repository.begin_source(
        owner_key=str(OWNER),
        connector_key="api",
        display_name="Widgets",
        original_filename="widgets.yaml",
        content=b"openapi: 3.0.3\npaths: {}\n",
    )
    repository.mark_running(
        owner_key=str(OWNER),
        source_id=prepared.source.source_id,
        revision_id=prepared.revision.revision_id,
    )
    ready = repository.mark_ready(
        owner_key=str(OWNER),
        source_id=prepared.source.source_id,
        revision_id=prepared.revision.revision_id,
        summary={"endpoint_count": 2},
    )
    graph_dir = prepared.artifact_dir / "graph"
    graph_dir.mkdir(parents=True)
    (graph_dir / "semantic_graph.json").write_text(
        json.dumps(
            {
                "nodes": [
                    {
                        "id": "resource:widgets",
                        "node_type": "resource",
                        "label": "widgets",
                        "endpoint_id": None,
                        "facets": {},
                    },
                    _operation("listWidgets", "GET", "/widgets", "list"),
                    _operation("createWidget", "POST", "/widgets", "create"),
                ],
                "edges": [
                    {
                        "source": "api_operation:widgets:listWidgets",
                        "target": "resource:widgets",
                        "type": "exposes",
                        "status": "declared",
                        "confidence": 1.0,
                    },
                    {
                        "source": "api_operation:widgets:createWidget",
                        "target": "resource:widgets",
                        "type": "exposes",
                        "status": "declared",
                        "confidence": 1.0,
                    },
                ],
                "metadata": {
                    "assembler": "resource_first_v1",
                    "construction_conformance": {
                        "stage_order": [],
                        "stages": {},
                    },
                },
            }
        ),
        encoding="utf-8",
    )
    return repository, ready.source_id, ready.revision.revision_id


def _operation(operation_id: str, method: str, path: str, operation_class: str):
    return {
        "id": f"api_operation:widgets:{operation_id}",
        "node_type": "api_operation",
        "label": f"{method} {path}",
        "endpoint_id": f"widgets:{operation_id}",
        "facets": {
            "method": method,
            "operation_class": operation_class,
            "operation_id": operation_id,
            "path": path,
        },
    }
