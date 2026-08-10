from __future__ import annotations

import json
from pathlib import Path

import pytest

from corpus.evaluation.evidence_index import update_latest_evidence


def test_latest_evidence_remains_current_per_definition(tmp_path: Path) -> None:
    latest_path = tmp_path / ".runtime" / "evaluations" / "latest.json"
    first_path = _artifact_path(tmp_path, "run-one")
    update_latest_evidence(
        repository=tmp_path,
        latest_path=latest_path,
        artifact=_artifact(
            "run-one",
            ("definition-a", "passed", "sha-a-one"),
            ("definition-b", "passed", "sha-b-one"),
        ),
        artifact_path=first_path,
    )

    second_path = _artifact_path(tmp_path, "run-two")
    update_latest_evidence(
        repository=tmp_path,
        latest_path=latest_path,
        artifact=_artifact("run-two", ("definition-a", "failed", "sha-a-two")),
        artifact_path=second_path,
    )

    latest = json.loads(latest_path.read_text(encoding="utf-8"))
    assert latest["evaluations"]["definition-a"] == {
        "status": "failed",
        "runId": "run-two",
        "completedAt": "2026-08-07T10:00:00+00:00",
        "definitionSha256": "sha-a-two",
        "artifact": ".runtime/evaluations/run-two/result.json",
    }
    assert latest["evaluations"]["definition-b"]["runId"] == "run-one"
    assert latest["evaluations"]["definition-b"]["definitionSha256"] == "sha-b-one"


def test_latest_evidence_requires_definition_identity(tmp_path: Path) -> None:
    latest_path = tmp_path / ".runtime" / "evaluations" / "latest.json"
    artifact = _artifact("run-one", ("definition-a", "passed", "sha-a"))
    artifact["results"][0].pop("definitionSha256")

    with pytest.raises(ValueError, match="has no definitionSha256"):
        update_latest_evidence(
            repository=tmp_path,
            latest_path=latest_path,
            artifact=artifact,
            artifact_path=_artifact_path(tmp_path, "run-one"),
        )


def _artifact_path(repository: Path, run_id: str) -> Path:
    return repository / ".runtime" / "evaluations" / run_id / "result.json"


def _artifact(run_id: str, *results: tuple[str, str, str]) -> dict:
    return {
        "runId": run_id,
        "completedAt": "2026-08-07T10:00:00+00:00",
        "results": [
            {
                "evaluationId": evaluation_id,
                "status": status,
                "definitionSha256": definition_sha256,
            }
            for evaluation_id, status, definition_sha256 in results
        ],
    }
