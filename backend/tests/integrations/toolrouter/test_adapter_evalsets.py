from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

from corpus.integrations.toolrouter import (
    EvalsetRequest,
    IngestRequest,
    ToolRouterAdapter,
    ToolRouterSettings,
)
from corpus.integrations.toolrouter.engine.evalset_factory_generation import (
    OllamaGenerationClient,
)

from .conftest import KeywordEmbeddingProvider, write_openapi_fixture


def test_evalset_client_accepts_an_explicit_container_model_endpoint(
    tmp_path: Path,
) -> None:
    client = OllamaGenerationClient(
        model="gemma4:latest",
        cache_dir=tmp_path / "cache",
        audit_path=tmp_path / "audit.jsonl",
        url="http://host.docker.internal:11434",
        transport=lambda _payload: {},
    )

    assert client.url == "http://host.docker.internal:11434"


def _candidate_id(payload: dict[str, Any]) -> str:
    match = re.search(r'"candidate_id":\s*"([^"]+)"', payload["prompt"])
    assert match is not None
    return match.group(1)


def _generation_response(payload: dict[str, Any]) -> dict[str, Any]:
    return {
        "response": json.dumps(
            {
                "candidate_id": _candidate_id(payload),
                "query": "Show me every item currently available",
                "strategy": "Natural source-grounded paraphrase",
            }
        ),
        "prompt_eval_count": 120,
        "eval_count": 18,
        "total_duration": 10,
    }


def _review_response(
    payload: dict[str, Any], *, accepted: bool
) -> dict[str, Any]:
    allowed = payload["format"]["properties"]["selected_endpoint_ids"][
        "items"
    ]["enum"]
    selected = next(
        endpoint_id
        for endpoint_id in allowed
        if endpoint_id.endswith("createWidget")
    )
    return {
        "response": json.dumps(
            {
                "candidate_id": _candidate_id(payload),
                "selected_endpoint_ids": [selected],
                "truth_supported": accepted,
                "category_fidelity": accepted,
                "naturalness": True,
                "ambiguous": False,
                "reasons": [] if accepted else ["The query does not preserve the endpoint truth."],
            }
        ),
        "prompt_eval_count": 160,
        "eval_count": 22,
        "total_duration": 10,
    }


def _adapter(*, accepted: bool) -> ToolRouterAdapter:
    return ToolRouterAdapter(
        ToolRouterSettings(),
        embedding_provider=KeywordEmbeddingProvider(),
        generation_transport=_generation_response,
        review_transport=lambda payload: _review_response(
            payload, accepted=accepted
        ),
        model_digest_resolver=lambda model: f"digest:{model}",
    )


def _ingest(adapter: ToolRouterAdapter, tmp_path: Path) -> Path:
    artifacts = tmp_path / "artifacts"
    adapter.ingest(
        IngestRequest(
            source_path=write_openapi_fixture(tmp_path / "widget-api.json"),
            artifact_dir=artifacts,
        )
    )
    return artifacts


def test_evalset_factory_exports_generated_and_independently_reviewed_cases(
    tmp_path: Path,
) -> None:
    adapter = _adapter(accepted=True)
    artifacts = _ingest(adapter, tmp_path)

    result = adapter.generate_evalset(
        EvalsetRequest(
            artifact_dir=artifacts,
            evalset_id="paraphrase-smoke",
            categories=("paraphrase",),
            tasks_per_category=1,
            max_generation_attempts=1,
            max_review_attempts=1,
        )
    )

    assert result.status == "ready"
    assert result.completed_count == result.expected_count == 1
    assert result.accepted_count == 1
    assert result.quarantined_count == 0
    assert result.offline_tokens == 320
    assert result.generator_model == "gemma4:latest"
    assert result.generator_model_digest == "digest:gemma4:latest"
    assert result.reviewer_model == "qwen2.5-coder:7b"
    assert result.reviewer_model_digest == "digest:qwen2.5-coder:7b"
    assert result.accepted_tasks[0]["query"] == (
        "Show me every item currently available"
    )
    assert (result.run_dir / "candidates.jsonl").is_file()
    assert (result.run_dir / "reviews.jsonl").is_file()
    assert (result.run_dir / "token_ledger.jsonl").is_file()
    assert (result.run_dir / "accepted_tasks.json").is_file()
    assert (result.run_dir / "accepted_manifest.json").is_file()


def test_evalset_factory_keeps_rejected_candidates_quarantined(
    tmp_path: Path,
) -> None:
    adapter = _adapter(accepted=False)
    artifacts = _ingest(adapter, tmp_path)

    result = adapter.generate_evalset(
        EvalsetRequest(
            artifact_dir=artifacts,
            evalset_id="rejected-smoke",
            categories=("paraphrase",),
            tasks_per_category=1,
            max_generation_attempts=1,
            max_review_attempts=1,
        )
    )

    assert result.status == "quarantined"
    assert result.accepted_count == 0
    assert result.quarantined_count == 1
    assert result.accepted_tasks == ()
    assert not (result.run_dir / "accepted_tasks.json").exists()
    assert result.terminal_status_counts == {"semantic_reject": 1}
