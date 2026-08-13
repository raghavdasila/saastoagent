from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

import pytest

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
    selected_schema = payload["format"]["properties"]["selected_endpoint_ids"]
    assert "uniqueItems" not in selected_schema
    allowed = selected_schema["items"]["enum"]
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


def test_evalset_factory_can_use_one_explicit_openai_model_for_both_roles(
    tmp_path: Path,
) -> None:
    adapter = ToolRouterAdapter(
        ToolRouterSettings(
            model_provider="openai",
            openai_api_key="deployment-key",
            generator_model="gpt-5.6-luna",
            reviewer_model="gpt-5.6-luna",
        ),
        embedding_provider=KeywordEmbeddingProvider(),
        generation_transport=_generation_response,
        review_transport=lambda payload: _review_response(payload, accepted=True),
        model_digest_resolver=lambda model: f"openai-digest:{model}",
    )
    artifacts = _ingest(adapter, tmp_path)

    result = adapter.generate_evalset(
        EvalsetRequest(
            artifact_dir=artifacts,
            evalset_id="openai-luna-smoke",
            categories=("paraphrase",),
            tasks_per_category=1,
            max_generation_attempts=1,
            max_review_attempts=1,
        )
    )

    assert result.status == "ready"
    assert result.generator_model == "gpt-5.6-luna"
    assert result.reviewer_model == "gpt-5.6-luna"


def test_evalset_factory_rejects_duplicate_semantic_review_endpoint_ids(
    tmp_path: Path,
) -> None:
    def duplicate_review(payload: dict[str, Any]) -> dict[str, Any]:
        selected_schema = payload["format"]["properties"]["selected_endpoint_ids"]
        selected = selected_schema["items"]["enum"][0]
        return {
            "response": json.dumps(
                {
                    "candidate_id": _candidate_id(payload),
                    "selected_endpoint_ids": [selected, selected],
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

    adapter = ToolRouterAdapter(
        ToolRouterSettings(),
        embedding_provider=KeywordEmbeddingProvider(),
        generation_transport=_generation_response,
        review_transport=duplicate_review,
        model_digest_resolver=lambda model: f"digest:{model}",
    )
    artifacts = _ingest(adapter, tmp_path)

    result = adapter.generate_evalset(
        EvalsetRequest(
            artifact_dir=artifacts,
            evalset_id="duplicate-review-endpoints",
            categories=("paraphrase",),
            tasks_per_category=1,
            max_generation_attempts=1,
            max_review_attempts=1,
        )
    )

    assert result.status == "failed"
    assert result.accepted_count == 0
    assert result.terminal_status_counts == {"semantic_review_failed": 1}


def test_evalset_factory_generates_only_from_the_exact_allowed_endpoint_subset(
    tmp_path: Path,
) -> None:
    adapter = _adapter(accepted=True)
    artifacts = _ingest(adapter, tmp_path)
    normalized = json.loads(
        (artifacts / "normalized" / "openapi_normalized.json").read_text(
            encoding="utf-8"
        )
    )
    create_endpoint = next(
        item["id"]
        for item in normalized["endpoints"]
        if item["operation_id"] == "createWidget"
    )

    result = adapter.generate_evalset(
        EvalsetRequest(
            artifact_dir=artifacts,
            evalset_id="curated-create-only",
            allowed_endpoint_ids=(create_endpoint,),
            categories=("paraphrase",),
            tasks_per_category=1,
            max_generation_attempts=1,
            max_review_attempts=1,
        )
    )

    assert result.status == "ready"
    assert result.expected_count == 1
    assert result.accepted_count == 1
    assert result.accepted_tasks[0]["expected_endpoint_sequence"] == [
        create_endpoint
    ]
    persisted = json.loads(
        (artifacts / "normalized" / "openapi_normalized.json").read_text(
            encoding="utf-8"
        )
    )
    assert len(persisted["endpoints"]) == 3


def test_evalset_factory_rejects_empty_duplicate_or_unknown_endpoint_subsets(
    tmp_path: Path,
) -> None:
    adapter = _adapter(accepted=True)
    artifacts = _ingest(adapter, tmp_path)

    for allowed in ((), ("missing",), ("duplicate", "duplicate")):
        with pytest.raises(Exception):
            adapter.generate_evalset(
                EvalsetRequest(
                    artifact_dir=artifacts,
                    evalset_id=f"invalid-{len(allowed)}",
                    allowed_endpoint_ids=allowed,
                )
            )


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
