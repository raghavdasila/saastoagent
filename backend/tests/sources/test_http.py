from __future__ import annotations

import json
import asyncio
import re
from pathlib import Path
from types import SimpleNamespace
from typing import Any
from uuid import UUID
import uuid
from datetime import UTC, datetime

from fastapi import FastAPI
from fastapi.testclient import TestClient
from routedeck_fastapi import SameOriginMutationPolicy

from backend.tests.integrations.toolrouter.conftest import (
    KeywordEmbeddingProvider,
    write_openapi_fixture,
)
from corpus.auth.config import AuthSettings
from corpus.auth.service import SessionUnavailable
from corpus.features.sources import LocalSourceRepository, SourceService
from corpus.features.sources.connectors.api import (
    ApiGraphPresenter,
    ApiSourceConnector,
)
from corpus.app.toolrouter_source_adapter import (
    ToolRouterApiSourceEngine,
)
from corpus.features.sources.connectors.api.connections import (
    ApiConnectionProfileRepository,
)
from corpus.integrations.medusa_acceptance import MedusaContractAcceptanceAdapter
from corpus.features.sources.connectors.api.http import create_api_source_router
from corpus.features.sources.connectors.api.operation_curation import (
    ApiOperationCurationService,
)
from corpus.features.sources.connectors.api.staged_attachments import (
    ApiStagedAttachmentRepository,
    ApiStagedAttachmentService,
)
from corpus.features.sources.http import (
    SourceHttpProblem,
    create_sources_router,
    source_problem_response,
)
from corpus.integrations.toolrouter import ToolRouterAdapter, ToolRouterSettings
from corpus.jobs import DurableJobRecord, DurableJobState


class OwnerResolver:
    async def resolve_access_token(self, auth_token: str):
        owners = {
            "owner-a": UUID("00000000-0000-0000-0000-000000000001"),
            "owner-b": UUID("00000000-0000-0000-0000-000000000002"),
        }
        try:
            user_id = owners[auth_token]
        except KeyError as error:
            raise SessionUnavailable from error
        return SimpleNamespace(user_id=user_id, organization_id=user_id)

    async def resolve_conversation(
        self, *, access_token: str, conversation_id: str, touch: bool
    ):
        del touch
        if conversation_id != f"conversation-{access_token}":
            from corpus.auth.service import ConversationUnavailable

            raise ConversationUnavailable
        return SimpleNamespace(
            public_id=conversation_id,
            route_session_id=f"route-{access_token}",
        )


class RecordingJobs:
    async def enqueue(self, **kwargs):
        now = datetime.now(UTC)
        return DurableJobRecord(
            id=uuid.uuid4(), owner_id=kwargs["owner_id"],
            job_type=kwargs["job_type"], state=DurableJobState.QUEUED,
            payload=kwargs["payload"], attempt_count=0,
            max_attempts=kwargs["max_attempts"], error_code=None,
            error_message=None, result=None, created_at=now, updated_at=now,
            started_at=None, completed_at=None,
        )

    async def status(self, **kwargs):
        raise NotImplementedError

    async def retry(self, **kwargs):
        raise NotImplementedError


def _candidate_id(payload: dict[str, Any]) -> str:
    match = re.search(r'"candidate_id":\s*"([^"]+)"', payload["prompt"])
    assert match is not None
    return match.group(1)


def _generation_response(payload: dict[str, Any]) -> dict[str, Any]:
    prompt_input = json.loads(payload["prompt"].rsplit("\n", 1)[-1])
    endpoint_id = prompt_input["expected_endpoint_sequence"][0]
    if endpoint_id.endswith("listWidgets"):
        query = "Show me every item currently available"
    elif endpoint_id.endswith("createWidget"):
        query = "Add a new item to the collection"
    else:
        assert endpoint_id.endswith("deleteWidget")
        query = "Remove item widget-123 from the collection"
    return {
        "response": json.dumps(
            {
                "candidate_id": _candidate_id(payload),
                "query": query,
                "strategy": "Natural source-grounded paraphrase",
            }
        ),
        "prompt_eval_count": 120,
        "eval_count": 18,
        "total_duration": 10,
    }


def _review_response(payload: dict[str, Any]) -> dict[str, Any]:
    packet = json.loads(payload["prompt"].rsplit("\n", 1)[-1])
    query = packet["query"].lower()
    expected_suffix = (
        "listWidgets"
        if "every item" in query
        else "createWidget"
        if "add a new item" in query
        else "deleteWidget"
    )
    allowed = payload["format"]["properties"]["selected_endpoint_ids"][
        "items"
    ]["enum"]
    selected = next(
        endpoint_id
        for endpoint_id in allowed
        if endpoint_id.endswith(expected_suffix)
    )
    return {
        "response": json.dumps(
            {
                "candidate_id": _candidate_id(payload),
                "selected_endpoint_ids": [selected],
                "truth_supported": True,
                "category_fidelity": True,
                "naturalness": True,
                "ambiguous": False,
                "reasons": [],
            }
        ),
        "prompt_eval_count": 160,
        "eval_count": 22,
        "total_duration": 10,
    }


def _auth_settings() -> AuthSettings:
    return AuthSettings(
        reset_secret="r" * 40,
        verification_secret="v" * 40,
        public_frontend_url="http://127.0.0.1:5199",
    )


def test_owner_authenticated_sources_http_path_uploads_retrieves_and_generates(
    tmp_path: Path,
) -> None:
    adapter = ToolRouterAdapter(
        ToolRouterSettings(),
        embedding_provider=KeywordEmbeddingProvider(),
        generation_transport=_generation_response,
        review_transport=_review_response,
        model_digest_resolver=lambda model: f"digest:{model}",
    )
    repository = LocalSourceRepository(tmp_path / "sources")
    connector = ApiSourceConnector(
        ToolRouterApiSourceEngine(adapter),
        max_upload_bytes=20 * 1024 * 1024,
    )
    service = SourceService(
        repository,
        connectors=(connector,),
        jobs=RecordingJobs(),
    )
    staged = ApiStagedAttachmentService(
        repository=ApiStagedAttachmentRepository(tmp_path / "sources"),
        sources=repository,
        connector=connector,
    )
    settings = _auth_settings()
    app = FastAPI()
    app.add_exception_handler(SourceHttpProblem, source_problem_response)
    app.include_router(
        create_sources_router(
            service=service,
            auth_service=OwnerResolver(),  # type: ignore[arg-type]
            mutation_policy=SameOriginMutationPolicy(
                trusted_origins=frozenset({"http://127.0.0.1:5199"})
            ),
        )
    )
    app.include_router(
        create_api_source_router(
            service=service,
            auth_service=OwnerResolver(),  # type: ignore[arg-type]
            mutation_policy=SameOriginMutationPolicy(
                trusted_origins=frozenset({"http://127.0.0.1:5199"})
            ),
            max_upload_bytes=20 * 1024 * 1024,
            graph_presenter=ApiGraphPresenter(service.repository),
            connection_profiles=ApiConnectionProfileRepository(service.repository),
                contract_revision_service=MedusaContractAcceptanceAdapter(service.repository),
                connection_check_service=object(),  # endpoint is covered by the Phase C HTTP tests
                operation_curation_service=ApiOperationCurationService(service.repository),
                route_plan_service=object(),
                staged_attachment_service=staged,
        )
    )
    source_file = write_openapi_fixture(tmp_path / "widgets.json")

    with TestClient(app) as client:
        client.headers.update({"Authorization": "Bearer owner-a"})
        uploaded = client.post(
            "/api/sources/api/attachments",
            headers={
                "Origin": "http://127.0.0.1:5199",
                "X-Corpus-Conversation-ID": "conversation-owner-a",
            },
            data={"name": "Widget API"},
            files={
                "file": (
                    "widgets.json",
                    source_file.read_bytes(),
                    "application/json",
                ),
                "description": (
                    "widgets.md",
                    b"# Widget API\nOwner supplied notes.",
                    "text/markdown",
                ),
            },
        )
        assert uploaded.status_code == 201, uploaded.text
        assert uploaded.json()["state"] == "staged"
        assert uploaded.json()["source_id"] is None
        assert client.get("/api/sources").json() == []

        accepted = staged.accept_current(
            owner_key="00000000-0000-0000-0000-000000000001",
            conversation_id="conversation-owner-a",
            route_session_id="route-owner-a",
        )
        assert accepted.revision.state.value == "accepted"
        queued = asyncio.run(
            service.process_source(
                owner_id=UUID("00000000-0000-0000-0000-000000000001"),
                source_id=accepted.source_id,
            )
        )
        source_id = accepted.source_id
        assert queued.revision.state.value == "queued"
        assert queued.revision.job_id
        assert queued.revision.description_filename == "widgets.md"

        listed = client.get("/api/sources")
        assert listed.status_code == 200
        assert [item["source_id"] for item in listed.json()] == [source_id]
        proposals = client.get(f"/api/sources/{source_id}/contract-revisions")
        assert proposals.status_code == 200
        assert proposals.json() == []

        client.headers.update({"Authorization": "Bearer owner-b"})
        hidden = client.get(f"/api/sources/{source_id}")
        assert hidden.status_code == 404
        hidden_proposals = client.get(f"/api/sources/{source_id}/contract-revisions")
        assert hidden_proposals.status_code == 404

        rejected = client.post(
            "/api/sources/api/attachments",
            headers={
                "Origin": "https://attacker.invalid",
                "X-Corpus-Conversation-ID": "conversation-owner-b",
            },
            data={"name": "Widget API"},
            files={"file": ("widgets.json", source_file.read_bytes())},
        )
        assert rejected.status_code == 403
        assert rejected.json()["code"] == "mutation_origin_rejected"
