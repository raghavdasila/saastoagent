from __future__ import annotations

import json
import re
from pathlib import Path
from types import SimpleNamespace
from typing import Any
from uuid import UUID

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
    ApiSourceConnector,
)
from corpus.features.sources.connectors.api.toolrouter import (
    ToolRouterApiSourceEngine,
)
from corpus.features.sources.connectors.api.http import create_api_source_router
from corpus.features.sources.http import (
    SourceHttpProblem,
    create_sources_router,
    source_problem_response,
)
from corpus.integrations.toolrouter import ToolRouterAdapter, ToolRouterSettings


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
        return SimpleNamespace(user_id=user_id)


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
    service = SourceService(
        LocalSourceRepository(tmp_path / "sources"),
        connectors=(
            ApiSourceConnector(
                ToolRouterApiSourceEngine(adapter),
                max_upload_bytes=20 * 1024 * 1024,
            ),
        ),
    )
    settings = _auth_settings()
    app = FastAPI()
    app.add_exception_handler(SourceHttpProblem, source_problem_response)
    app.include_router(
        create_sources_router(
            service=service,
            auth_service=OwnerResolver(),  # type: ignore[arg-type]
            auth_settings=settings,
            mutation_policy=SameOriginMutationPolicy(
                trusted_origins=frozenset({"http://127.0.0.1:5199"})
            ),
        )
    )
    app.include_router(
        create_api_source_router(
            service=service,
            auth_service=OwnerResolver(),  # type: ignore[arg-type]
            auth_settings=settings,
            mutation_policy=SameOriginMutationPolicy(
                trusted_origins=frozenset({"http://127.0.0.1:5199"})
            ),
            max_upload_bytes=20 * 1024 * 1024,
        )
    )
    source_file = write_openapi_fixture(tmp_path / "widgets.json")

    with TestClient(app) as client:
        client.headers.update({"Authorization": "Bearer owner-a"})
        uploaded = client.post(
            "/api/sources/api",
            headers={"Origin": "http://127.0.0.1:5199"},
            data={"name": "Widget API"},
            files={
                "file": (
                    "widgets.json",
                    source_file.read_bytes(),
                    "application/json",
                )
            },
        )
        assert uploaded.status_code == 201, uploaded.text
        source_id = uploaded.json()["source_id"]
        assert uploaded.json()["connector_key"] == "api"
        assert uploaded.json()["revision"]["state"] == "ready"

        listed = client.get("/api/sources")
        assert listed.status_code == 200
        assert [item["source_id"] for item in listed.json()] == [source_id]

        retrieved = client.post(
            f"/api/sources/{source_id}/retrieve",
            headers={"Origin": "http://127.0.0.1:5199"},
            json={"query": "list widgets", "top_k": 3, "trace_mode": "bounded"},
        )
        assert retrieved.status_code == 200, retrieved.text
        assert retrieved.json()["steps"][0]["ranked_items"][0][
            "item_id"
        ].endswith("listWidgets")

        evalset = client.post(
            f"/api/sources/{source_id}/evalsets",
            headers={"Origin": "http://127.0.0.1:5199"},
            json={
                "evalset_id": "paraphrase-smoke",
                "categories": ["paraphrase"],
                "tasks_per_category": 1,
                "max_generation_attempts": 1,
                "max_review_attempts": 1,
            },
        )
        assert evalset.status_code == 200, evalset.text
        assert evalset.json()["status"] == "ready", evalset.text
        assert evalset.json()["accepted_count"] == 1

        client.headers.update({"Authorization": "Bearer owner-b"})
        hidden = client.get(f"/api/sources/{source_id}")
        assert hidden.status_code == 404

        rejected = client.post(
            "/api/sources/api",
            headers={"Origin": "https://attacker.invalid"},
            data={"name": "Widget API"},
            files={"file": ("widgets.json", source_file.read_bytes())},
        )
        assert rejected.status_code == 403
        assert rejected.json()["code"] == "mutation_origin_rejected"
