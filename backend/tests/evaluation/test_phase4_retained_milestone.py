from __future__ import annotations

import json
from pathlib import Path

import pytest

from scripts.verify_phase4_retained_milestone import REQUIRED_ASSERTIONS, verify


def test_retained_phase4_verifier_accepts_only_the_pre_failure_behavior(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr("scripts.verify_phase4_retained_milestone.REPOSITORY_ROOT", tmp_path)
    screenshot_paths = []
    for index, token in enumerate((
        "07-deployment-review", "08-deployed-channel", "08b-deployed-navgraph",
        "08c-second-deployment-review", "08d-rollback-review",
        "08e-public-access-paused", "08f-public-access-restored",
        "09-public-clarification", "10-public-resolved", "99-failure",
    )):
        path = tmp_path / f"{index}-{token}.png"
        path.write_bytes(b"png")
        screenshot_paths.append(str(path))
    artifact = tmp_path / "result.json"
    artifact.write_text(json.dumps({
        "runId": "run-1", "status": "failed",
        "error": "strict mode violation: two Operations headings",
        "assertions": [{"name": name, "passed": True} for name in REQUIRED_ASSERTIONS],
        "ids": {
            "conversationId": "conversation", "agentId": "agent",
            "approvedRevisionId": "revision", "curationId": "curation", "buildId": "build",
        },
        "screenshots": screenshot_paths,
        "diagnostics": {"httpErrors": [], "consoleErrors": [], "pageErrors": [], "requestFailures": []},
        "interactionEvents": [
            {"operationId": value} for value in (
                "channels.create", "deployment.deploy", "deployment.rollback",
                "channels.set_enabled", "agents.open_operations",
            )
        ],
    }), encoding="utf-8")
    video = tmp_path / "phase4.webm"
    video.write_bytes(b"video")
    monkeypatch.setattr("scripts.verify_phase4_retained_milestone._duration", lambda _path: 305.92)

    report = verify(artifact, video)

    assert report["status"] == "partial"
    assert report["sourceCampaignStatus"] == "failed"
    assert report["missingRequiredBehavior"] == "explicit exact-owner Operations promotion into Evaluation"
    assert report["video"]["includesTerminalRecorderFailure"] is True


def test_retained_phase4_verifier_rejects_a_promotion_claim(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr("scripts.verify_phase4_retained_milestone.REPOSITORY_ROOT", tmp_path)
    screenshot_paths = []
    for token in (
        "07-deployment-review", "08-deployed-channel", "08b-deployed-navgraph",
        "08c-second-deployment-review", "08d-rollback-review",
        "08e-public-access-paused", "08f-public-access-restored",
        "09-public-clarification", "10-public-resolved", "99-failure",
    ):
        path = tmp_path / f"{token}.png"
        path.write_bytes(b"png")
        screenshot_paths.append(str(path))
    artifact = tmp_path / "result.json"
    artifact.write_text(json.dumps({
        "runId": "run-1", "status": "failed",
        "error": "strict mode violation: two Operations headings",
        "assertions": [{"name": name, "passed": True} for name in REQUIRED_ASSERTIONS],
        "ids": {
            "conversationId": "conversation", "agentId": "agent",
            "approvedRevisionId": "revision", "curationId": "curation", "buildId": "build",
        },
        "screenshots": screenshot_paths,
        "diagnostics": {"httpErrors": [], "consoleErrors": [], "pageErrors": [], "requestFailures": []},
        "interactionEvents": [
            {"operationId": value} for value in (
                "channels.create", "deployment.deploy", "deployment.rollback",
                "channels.set_enabled", "agents.open_operations",
                "operations.promote_evaluation_case",
            )
        ],
    }), encoding="utf-8")
    video = tmp_path / "phase4.webm"
    video.write_bytes(b"video")
    monkeypatch.setattr("scripts.verify_phase4_retained_milestone._duration", lambda _path: 305.92)

    with pytest.raises(RuntimeError, match="must not claim"):
        verify(artifact, video)
