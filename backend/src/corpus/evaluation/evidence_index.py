from __future__ import annotations

import json
from pathlib import Path
from typing import Any


LATEST_EVIDENCE_SCHEMA = "corpus.self-evaluation.latest.v1"


def update_latest_evidence(
    *,
    repository: Path,
    latest_path: Path,
    artifact: dict[str, Any],
    artifact_path: Path,
) -> None:
    """Index the newest immutable evidence independently for each definition."""

    latest = (
        _load_object(latest_path)
        if latest_path.exists()
        else {"schema": LATEST_EVIDENCE_SCHEMA, "evaluations": {}}
    )
    if latest.get("schema") != LATEST_EVIDENCE_SCHEMA:
        raise ValueError(f"Unsupported evaluation evidence index: {latest_path}")
    evaluations = latest.get("evaluations")
    if not isinstance(evaluations, dict):
        raise ValueError(f"Evaluation evidence index has no evaluations object: {latest_path}")

    artifact_reference = str(artifact_path.relative_to(repository)).replace("\\", "/")
    for result in artifact["results"]:
        definition_sha256 = result.get("definitionSha256")
        if not isinstance(definition_sha256, str) or not definition_sha256:
            raise ValueError(
                f"Evaluation {result.get('evaluationId')!r} has no definitionSha256"
            )
        evaluations[result["evaluationId"]] = {
            "status": result["status"],
            "runId": artifact["runId"],
            "completedAt": artifact["completedAt"],
            "definitionSha256": definition_sha256,
            "artifact": artifact_reference,
        }

    temporary = latest_path.with_suffix(".tmp")
    temporary.parent.mkdir(parents=True, exist_ok=True)
    temporary.write_text(json.dumps(latest, indent=2) + "\n", encoding="utf-8")
    temporary.replace(latest_path)


def _load_object(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"Expected JSON object: {path}")
    return value


__all__ = ["LATEST_EVIDENCE_SCHEMA", "update_latest_evidence"]
