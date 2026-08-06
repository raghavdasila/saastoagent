from __future__ import annotations

import json
from pathlib import Path

import pytest

from corpus.evaluation.product_journeys import (
    aggregate_product_journey_artifacts,
)


def test_aggregate_records_fresh_runtime_isolation_and_updates_latest(
    tmp_path: Path,
) -> None:
    artifacts = [
        artifact("component-one", "journey-one"),
        artifact("component-two", "journey-two"),
    ]

    aggregate = aggregate_product_journey_artifacts(tmp_path, artifacts)

    assert aggregate["status"] == "passed"
    assert aggregate["identities"]["runtimeIsolation"] == (
        "fresh Corpus processes and persistent state per journey"
    )
    assert aggregate["identities"]["componentRunIds"] == [
        "component-one",
        "component-two",
    ]
    latest = json.loads(
        (tmp_path / ".runtime" / "evaluations" / "latest.json").read_text()
    )
    assert latest["evaluations"]["journey-one"]["runId"] == aggregate["runId"]
    assert latest["evaluations"]["journey-two"]["runId"] == aggregate["runId"]


def test_aggregate_rejects_mixed_design_identities(tmp_path: Path) -> None:
    first = artifact("component-one", "journey-one")
    second = artifact("component-two", "journey-two")
    second["identities"]["designSha256"] = "different-design"

    with pytest.raises(ValueError, match="one design identity"):
        aggregate_product_journey_artifacts(tmp_path, [first, second])


def artifact(run_id: str, evaluation_id: str) -> dict:
    return {
        "runId": run_id,
        "startedAt": "2026-08-06T04:00:00+00:00",
        "completedAt": "2026-08-06T04:01:00+00:00",
        "identities": {"designSha256": "design-one"},
        "results": [
            {
                "evaluationId": evaluation_id,
                "status": "passed",
                "definitionSha256": f"definition-{evaluation_id}",
                "usage": {
                    "modelInvocations": None,
                    "inputTokens": None,
                    "outputTokens": None,
                },
            }
        ],
    }
