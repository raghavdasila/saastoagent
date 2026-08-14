from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
import uuid

import pytest
from routedeck_core.contracts.operations import OperationSource
from routedeck_core.contracts.projection import FrozenJsonObject
from routedeck_core.ports.executor import ExecutionContext

from corpus.features.sources import LocalSourceRepository, SourceService, SourceState
from corpus.features.sources.connectors.api import ApiSourceConnector, SourceUpload
from corpus.features.sources.connectors.api.staged_attachments import (
    ApiStagedAttachmentRepository,
    ApiStagedAttachmentService,
    ApiStagedAttachmentUnavailable,
)
from corpus.features.sources.contracts import API_CONNECTION_FORM_ID
from corpus.features.sources.operations import AcceptStagedApiHandler, ProcessApiHandler

from backend.tests.sources.test_api_connection_check_routedeck import OwnerProbe
from backend.tests.sources.test_service import RecordingJobs


OWNER = uuid.UUID("00000000-0000-0000-0000-000000000001")


def _service(root: Path) -> tuple[ApiStagedAttachmentService, LocalSourceRepository]:
    sources = LocalSourceRepository(root / "sources")
    return (
        ApiStagedAttachmentService(
            repository=ApiStagedAttachmentRepository(root / "sources"),
            sources=sources,
            connector=ApiSourceConnector(object(), max_upload_bytes=1024 * 1024),  # type: ignore[arg-type]
        ),
        sources,
    )


def test_attachment_is_conversation_bound_and_does_not_create_or_process_source(
    tmp_path: Path,
) -> None:
    service, sources = _service(tmp_path)
    staged = service.stage(
        owner_key="owner-a",
        conversation_id="conversation-0001",
        route_session_id="route-session-a",
        display_name="Store API",
        upload=SourceUpload(
            filename="store.yaml",
            content_type="text/yaml",
            content=b"openapi: 3.0.3\ninfo:\n  title: Store\n  version: 1.0.0\npaths: {}\n",
        ),
    )

    assert staged.state == "staged"
    assert sources.list(owner_key="owner-a") == ()
    assert service.current(
        owner_key="owner-a",
        conversation_id="conversation-0001",
        route_session_id="route-session-a",
    ) == staged
    assert service.current(
        owner_key="owner-a",
        conversation_id="conversation-0002",
        route_session_id="route-session-b",
    ) is None

    accepted = service.accept_current(
        owner_key="owner-a",
        conversation_id="conversation-0001",
        route_session_id="route-session-a",
    )

    assert accepted.revision.state is SourceState.ACCEPTED
    assert accepted.revision.job_id is None
    current = service.current(
        owner_key="owner-a",
        conversation_id="conversation-0001",
        route_session_id="route-session-a",
    )
    assert current is not None
    assert current.state == "accepted"
    assert current.source_id == accepted.source_id


def test_accept_is_single_use_and_survives_repository_reload(tmp_path: Path) -> None:
    service, sources = _service(tmp_path)
    service.stage(
        owner_key="owner-a",
        conversation_id="conversation-0001",
        route_session_id="route-session-a",
        display_name="Store API",
        upload=SourceUpload(
            filename="store.json",
            content_type="application/json",
            content=b'{"openapi":"3.0.3","info":{"title":"Store","version":"1"},"paths":{}}',
        ),
    )

    def accept_once():
        return service.accept_current(
            owner_key="owner-a",
            route_session_id="route-session-a",
        )

    with ThreadPoolExecutor(max_workers=2) as executor:
        outcomes = [future for future in (executor.submit(accept_once), executor.submit(accept_once))]
    results = []
    failures = []
    for future in outcomes:
        try:
            results.append(future.result())
        except ApiStagedAttachmentUnavailable as error:
            failures.append(error)

    assert len(results) == 1
    assert len(failures) == 1
    assert len(sources.list(owner_key="owner-a")) == 1

    reloaded, _ = _service(tmp_path)
    assert reloaded.accepted_source(
        owner_key="owner-a",
        conversation_id="conversation-0001",
        route_session_id="route-session-a",
    ) == (results[0].source_id, results[0].revision.revision_id)
    with pytest.raises(ApiStagedAttachmentUnavailable):
        reloaded.accept_current(
            owner_key="owner-a",
            route_session_id="route-session-a",
        )


@pytest.mark.asyncio
async def test_agent_handlers_accept_then_explicitly_queue_the_staged_api(
    tmp_path: Path,
) -> None:
    repository = LocalSourceRepository(tmp_path / "sources")
    connector = ApiSourceConnector(object(), max_upload_bytes=1024 * 1024)  # type: ignore[arg-type]
    staged = ApiStagedAttachmentService(
        repository=ApiStagedAttachmentRepository(tmp_path / "sources"),
        sources=repository,
        connector=connector,
    )
    jobs = RecordingJobs()
    sources = SourceService(repository, connectors=(connector,), jobs=jobs)
    session_id = "source-check-staged-api"
    staged.stage(
        owner_key=str(OWNER),
        conversation_id="conversation-0001",
        route_session_id=session_id,
        display_name="Store API",
        upload=SourceUpload(
            filename="store.yaml",
            content_type="text/yaml",
            content=b"openapi: 3.0.3\ninfo:\n  title: Store\n  version: 1.0.0\npaths: {}\n",
        ),
    )
    context = ExecutionContext(
        session_id=session_id,
        request_id="staged-api-request",
        attempt_id="staged-api-attempt",
        node_id="sources.home",
        source=OperationSource.AGENT,
        context_fingerprint="staged-api-context",
    )

    accepted = await AcceptStagedApiHandler(staged, OwnerProbe(OWNER))({}, context)

    assert accepted.outcome == "accepted"
    assert {
        value.name: value.value.to_python()
        for value in accepted.effects.surface_updates[0].values
    } == {
        "form_handle": API_CONNECTION_FORM_ID,
        "mode": "inspect",
        "selected_source_id": accepted.public_observation.to_python()["source_id"],
        "selected_source_revision_id": accepted.public_observation.to_python()[
            "source_revision_id"
        ],
        "selected_source_display_name": "Store API",
        "processing_state": "accepted",
    }
    accepted_view = repository.list(owner_key=str(OWNER))[0]
    assert accepted_view.revision.state is SourceState.ACCEPTED
    assert accepted_view.revision.job_id is None
    assert jobs.enqueued == []

    selected_context = context.model_copy(
        update={
            "provider_values": FrozenJsonObject(
                {
                    "sources.selected_api_source": {
                        "source_id": accepted_view.source_id,
                        "source_revision_id": accepted_view.revision.revision_id,
                    }
                }
            )
        }
    )
    queued = await ProcessApiHandler(sources, staged, OwnerProbe(OWNER))(
        {}, selected_context
    )

    assert queued.outcome == "queued"
    assert {
        value.name: value.value.to_python()
        for value in queued.effects.surface_updates[0].values
    } == {
        "form_handle": API_CONNECTION_FORM_ID,
        "mode": "inspect",
        "selected_source_id": accepted_view.source_id,
        "selected_source_revision_id": accepted_view.revision.revision_id,
        "selected_source_display_name": "Store API",
        "processing_state": "queued",
    }
    queued_view = repository.get(
        owner_key=str(OWNER), source_id=accepted_view.source_id
    )
    assert queued_view.revision.state is SourceState.QUEUED
    assert queued_view.revision.job_id == str(jobs.job_id)
    assert len(jobs.enqueued) == 1
