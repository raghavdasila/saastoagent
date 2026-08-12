from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
from pathlib import Path


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
REQUIRED_ASSERTIONS = (
    "eligible build is review-gated and deployed to hosted Web",
    "active deployment shows its exact immutable RouteDeck NavGraph",
    "a second reviewed deployment creates a distinct immutable ready release",
    "reviewed rollback activates the exact earlier ready deployment",
    "reviewed pause removes public access without changing deployment lineage",
    "reviewed resume restores the same hosted Agent address",
    "deployment survives backend and worker restart",
    "deployed Agent visibly waits for ToolRouter clarification without an API call",
    "public hosted session completes the deployed read without secrets",
    "deployed Agent keeps owner-only runtime diagnostics out of the public session",
)
REQUIRED_SCREENSHOTS = (
    "07-deployment-review",
    "08-deployed-channel",
    "08b-deployed-navgraph",
    "08c-second-deployment-review",
    "08d-rollback-review",
    "08e-public-access-paused",
    "08f-public-access-restored",
    "09-public-clarification",
    "10-public-resolved",
    "99-failure",
)


def _path(value: str) -> Path:
    path = Path(value)
    return path if path.is_absolute() else REPOSITORY_ROOT / path


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _duration(path: Path) -> float:
    completed = subprocess.run(
        [
            "ffprobe",
            "-v",
            "error",
            "-show_entries",
            "format=duration",
            "-of",
            "default=noprint_wrappers=1:nokey=1",
            str(path),
        ],
        cwd=REPOSITORY_ROOT,
        capture_output=True,
        text=True,
        timeout=30,
        check=False,
    )
    if completed.returncode != 0:
        raise RuntimeError("The retained Phase 4 video cannot be inspected.")
    return round(float(completed.stdout.strip()), 3)


def verify(artifact: Path, video: Path) -> dict[str, object]:
    artifact_path = artifact if artifact.is_absolute() else REPOSITORY_ROOT / artifact
    document = json.loads(artifact_path.read_text(encoding="utf-8"))
    if document.get("status") != "failed":
        raise RuntimeError("The source campaign must retain its truthful failed status.")
    error = document.get("error")
    if not isinstance(error, str) or "strict mode violation" not in error or "Operations" not in error:
        raise RuntimeError("The retained campaign has an unexpected terminal failure.")

    assertions = document.get("assertions")
    by_name = {
        item.get("name"): item
        for item in assertions
        if isinstance(assertions, list)
        and isinstance(item, dict)
        and isinstance(item.get("name"), str)
    }
    missing = [
        name
        for name in REQUIRED_ASSERTIONS
        if not isinstance(by_name.get(name), dict) or by_name[name].get("passed") is not True
    ]
    if missing:
        raise RuntimeError("The retained Phase 4 behavior is incomplete: " + ", ".join(missing))

    ids = document.get("ids")
    required_ids = ("conversationId", "agentId", "approvedRevisionId", "curationId", "buildId")
    if not isinstance(ids, dict) or any(
        not isinstance(ids.get(name), str) or not ids[name] for name in required_ids
    ):
        raise RuntimeError("The retained Phase 4 lineage is incomplete.")

    screenshots = document.get("screenshots")
    if not isinstance(screenshots, list):
        raise RuntimeError("The retained Phase 4 screenshot manifest is unavailable.")
    verified_screenshots: dict[str, str] = {}
    for token in REQUIRED_SCREENSHOTS:
        matches = [value for value in screenshots if isinstance(value, str) and token in value]
        if len(matches) != 1:
            raise RuntimeError(f"The retained Phase 4 screenshot {token!r} is unavailable.")
        screenshot = _path(matches[0])
        if not screenshot.is_file() or screenshot.stat().st_size <= 0:
            raise RuntimeError(f"The retained Phase 4 screenshot {token!r} is empty.")
        verified_screenshots[token] = _sha256(screenshot)

    diagnostics = document.get("diagnostics")
    if not isinstance(diagnostics, dict) or any(
        diagnostics.get(name)
        for name in ("httpErrors", "consoleErrors", "pageErrors", "requestFailures")
    ):
        raise RuntimeError("The retained Phase 4 interval contains unexpected diagnostics.")

    interaction_events = document.get("interactionEvents")
    operation_ids = {
        item.get("operationId")
        for item in interaction_events
        if isinstance(interaction_events, list) and isinstance(item, dict)
    }
    required_operations = {
        "channels.create",
        "deployment.deploy",
        "deployment.rollback",
        "channels.set_enabled",
        "agents.open_operations",
    }
    if not required_operations.issubset(operation_ids):
        raise RuntimeError("The retained Phase 4 operation chronology is incomplete.")
    if "operations.promote_evaluation_case" in operation_ids:
        raise RuntimeError("This partial verifier must not claim an Operations promotion.")

    video_path = video if video.is_absolute() else REPOSITORY_ROOT / video
    if not video_path.is_file() or video_path.stat().st_size <= 0:
        raise RuntimeError("The derived Phase 4 feature film is unavailable.")
    duration = _duration(video_path)
    if duration != 305.92:
        raise RuntimeError("The derived Phase 4 feature film boundary changed.")

    return {
        "milestone": "phase4-deployment-public-operations",
        "status": "partial",
        "runId": document.get("runId"),
        "sourceCampaignStatus": "failed",
        "acceptedAssertions": list(REQUIRED_ASSERTIONS),
        "missingRequiredBehavior": "explicit exact-owner Operations promotion into Evaluation",
        "ids": {name: ids[name] for name in required_ids},
        "screenshots": verified_screenshots,
        "video": {
            "path": str(video_path.relative_to(REPOSITORY_ROOT)),
            "durationSeconds": duration,
            "sha256": _sha256(video_path),
            "bytes": video_path.stat().st_size,
            "playbackRate": 1.0,
            "continuousFeatureInterval": True,
            "includesTerminalRecorderFailure": True,
        },
        "sourceArtifact": {
            "path": str(artifact_path.relative_to(REPOSITORY_ROOT)),
            "sha256": _sha256(artifact_path),
            "bytes": artifact_path.stat().st_size,
        },
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Verify the retained partial Phase 4 milestone.")
    parser.add_argument("--artifact", required=True, type=Path)
    parser.add_argument("--video", required=True, type=Path)
    args = parser.parse_args()
    print(json.dumps(verify(args.artifact, args.video), indent=2))


if __name__ == "__main__":
    main()
