from __future__ import annotations

import argparse
import asyncio
import hashlib
import json
import os
import re
import shutil
import sys
import time
from datetime import UTC, datetime
from pathlib import Path
from urllib.parse import urlsplit
from uuid import uuid4

from playwright.async_api import Page, async_playwright

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import scripts.run_horizontal_product_journey as horizontal
from scripts.run_api_connection_check_journey import MEDUSA_ENV, _load_required_value, _profiles
from scripts.run_api_contract_revision_journey import (
    MEDUSA_SPEC,
    _observed_current_source,
    _observed_proposals,
    _proposal_panel,
    _register,
    _review_surface,
)
from scripts.run_api_operation_curation_journey import _curation_panel, _observed_curation
from scripts.run_api_route_planning_journey import _attach_diagnostics


PRODUCT_URL = "http://127.0.0.1:5199"
BACKEND_URL = "http://127.0.0.1:8099"
MEDUSA_BASE_URL = "http://host.docker.internal:9100"


def arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Record the real v0.2 Sandbox deployment-mode journey."
    )
    parser.add_argument("--headed", action="store_true")
    parser.add_argument("--url", default=PRODUCT_URL)
    return parser.parse_args()


async def _capture(page: Page, directory: Path, name: str) -> str:
    path = directory / f"{name}.png"
    await page.screenshot(path=path, full_page=True)
    return str(path.relative_to(ROOT)).replace("\\", "/")


async def _register_with_direct_loopback_dispatch(
    page: Page,
    url: str,
    owner: dict[str, str],
) -> None:
    """Keep the real registration operation while isolating its test IP bucket.

    The frontend development proxy is shared by every browser journey and is
    intentionally limited to five registrations per hour. Only the final
    registration dispatch is sent to the same loopback backend directly; the
    normal response still returns through the browser and the route is removed
    immediately afterward. No product operation after registration uses this
    evidence-harness route.
    """

    async def dispatch(route, request) -> None:
        try:
            payload = request.post_data_json
        except Exception:
            payload = None
        operation_id = (
            payload.get("operation_id") or payload.get("operationId")
            if isinstance(payload, dict)
            else None
        )
        if operation_id != "lounge.create_owner_account":
            await route.continue_()
            return
        direct = await route.fetch(
            url=f"{BACKEND_URL}{urlsplit(request.url).path}",
        )
        await route.fulfill(response=direct)

    pattern = "**/api/routedeck/dispatch"
    await page.route(pattern, dispatch)
    try:
        await _register(page, url, owner)
    finally:
        await page.unroute(pattern, dispatch)


def _observation_state() -> dict[str, object]:
    return {
        "sequence": 0,
        "sourceInventory": [],
        "sourceInventoryVersion": 0,
        "currentSources": {},
        "contractProposals": {},
        "profiles": {},
        "curations": {},
        "plans": [],
        "publicForbiddenFields": [],
        "agents": [],
        "designs": [],
        "builds": [],
        "sandbox": [],
        "evaluations": [],
        "channels": [],
        "deployments": [],
        "operations": [],
        "chatOperations": [],
        "chatInspectionTools": [],
    }


def _record_private_runtime_responses(
    page: Page,
    responses: list[dict[str, object]],
) -> None:
    async def observe(response) -> None:
        path = urlsplit(response.url).path
        if not (
            path.startswith("/api/agents/")
            and ("/sandbox" in path or "/evaluations" in path)
        ):
            return
        try:
            body = await response.json()
        except Exception:
            body = None
        responses.append(
            {
                "method": response.request.method,
                "path": path,
                "status": response.status,
                "body": body,
            }
        )

    page.on("response", lambda response: asyncio.create_task(observe(response)))


def _latest_response(
    responses: list[dict[str, object]],
    *,
    method: str,
    path_suffix: str,
    status: int | None = None,
) -> dict[str, object]:
    for item in reversed(responses):
        if item.get("method") != method or not str(item.get("path", "")).endswith(path_suffix):
            continue
        if status is not None and item.get("status") != status:
            continue
        body = item.get("body")
        if isinstance(body, dict):
            return body
    raise RuntimeError(f"No {method} response ending in {path_suffix!r} was observed.")


async def _wait_response(
    responses: list[dict[str, object]],
    *,
    method: str,
    path_suffix: str,
    status: int | None = None,
    timeout_seconds: float = 30,
) -> dict[str, object]:
    deadline = time.monotonic() + timeout_seconds
    while time.monotonic() < deadline:
        try:
            return _latest_response(
                responses,
                method=method,
                path_suffix=path_suffix,
                status=status,
            )
        except RuntimeError:
            await asyncio.sleep(0.05)
    raise RuntimeError(f"No {method} response ending in {path_suffix!r} was observed.")


async def _send_playground_message(
    page: Page,
    playground,
    responses: list[dict[str, object]],
    *,
    session_id: str,
    text: str,
) -> dict[str, object]:
    path_suffix = f"/sandbox/sessions/{session_id}/messages"
    existing = sum(
        1
        for item in responses
        if item.get("method") == "POST"
        and str(item.get("path", "")).endswith(path_suffix)
    )
    await playground.get_by_label("Message", exact=True).fill(text)
    await playground.get_by_role("button", name="Send message", exact=True).click()
    deadline = time.monotonic() + 180
    while time.monotonic() < deadline:
        matching = [
            item
            for item in responses
            if item.get("method") == "POST"
            and str(item.get("path", "")).endswith(path_suffix)
        ]
        if len(matching) > existing:
            response = matching[-1]
            if response.get("status") != 200:
                raise RuntimeError(
                    "The Playground message failed: "
                    f"HTTP {response.get('status')} {response.get('body')}"
                )
            body = response.get("body")
            if not isinstance(body, dict):
                raise RuntimeError("The Playground message response is incomplete.")
            return body
        await page.wait_for_timeout(50)
    raise TimeoutError("The Playground message did not receive a runtime response.")


async def _prepare_ready_build(
    page: Page,
    directory: Path,
    observations: dict[str, object],
    medusa_key: str,
) -> dict[str, str]:
    screenshots: list[str] = []
    ids: dict[str, str] = {}
    hub = await horizontal._open_sources(page)
    await horizontal._surface_add_and_analyze_api(page, hub, directory, screenshots)
    await hub.get_by_text("ready", exact=True).first.wait_for(timeout=180_000)
    ids.update(await horizontal._observed_source_ids(observations))

    await hub.get_by_role("button", name="Review API changes", exact=True).click()
    proposal = _proposal_panel(page)
    await proposal.get_by_role(
        "heading", name="Proposed API version update", exact=True
    ).wait_for(timeout=90_000)
    proposals = await _observed_proposals(observations, ids["sourceId"])
    ids["proposalId"] = str(proposals[0]["proposal_id"])
    await proposal.get_by_role(
        "button", name="Review this API update", exact=True
    ).click()
    review = _review_surface(page)
    await review.get_by_role(
        "heading", name="Create this immutable API version?", exact=True
    ).wait_for(timeout=30_000)
    await review.get_by_role(
        "button", name="Accept and create new version", exact=True
    ).click()
    await hub.get_by_text("Validated API version", exact=True).wait_for(timeout=60_000)
    current = await _observed_current_source(
        observations,
        ids["sourceId"],
        excluding_revision_id=ids["parentRevisionId"],
    )
    ids["approvedRevisionId"] = str(current["revision"]["revision_id"])

    await hub.get_by_role("button", name="Connection", exact=True).click()
    connection = hub.locator("section.api-connection-panel")
    await connection.get_by_role("heading", name="API connections", exact=True).wait_for(
        timeout=30_000
    )
    await horizontal._save_profile_exact(
        page,
        connection,
        "Sandbox v0.2 local Medusa",
        medusa_key,
        base_url=MEDUSA_BASE_URL,
        environment="local",
    )
    profiles = await _profiles(observations, ids["sourceId"], minimum_count=1)
    ids["profileId"] = str(
        next(
            item
            for item in profiles
            if item.get("profile_name") == "Sandbox v0.2 local Medusa"
        )["id"]
    )

    await hub.get_by_role("button", name="Operations", exact=True).click()
    curation = _curation_panel(page)
    await curation.get_by_role(
        "heading", name="API operation curation", exact=True
    ).wait_for(timeout=30_000)
    inventory = await _observed_curation(
        observations, ids["sourceId"], minimum_history=0
    )
    operation_ids = {
        str(item["operation_id"])
        for item in inventory["operations"]
        if isinstance(item, dict)
    }
    await horizontal._classify_operations(
        curation, operation_ids, horizontal.INCLUDED_OPERATIONS
    )
    await curation.get_by_role(
        "button", name="Save operation selection", exact=True
    ).click()
    saved = await _observed_curation(
        observations, ids["sourceId"], minimum_history=1
    )
    ids["curationId"] = str(saved["current"]["id"])

    await hub.get_by_role("button", name="Agent", exact=True).click()
    await hub.get_by_role("button", name="Create a new Agent", exact=True).click()
    await horizontal._create_agent_from_surface(page)
    ids["agentId"] = await horizontal._latest_agent_id(observations)
    await page.get_by_role("button", name="Attach Source", exact=True).click()
    await page.locator(".agent-sources").get_by_text(
        f"API version {ids['approvedRevisionId']}", exact=True
    ).wait_for(timeout=30_000)

    await horizontal._open_bound_agent_area(page, "Designer", "Agent Designer")
    await horizontal._maximize_current_surface(page)
    await page.get_by_role("button", name="Propose design", exact=True).click()
    await page.get_by_role(
        "region", name="Agent design blueprint", exact=True
    ).wait_for(timeout=30_000)
    await horizontal._fill_designer_feature_and_generate(
        page, horizontal.CHAT_PROMPTS["generate_design_feature"]
    )
    await page.locator(".designer-home__status").get_by_text(
        "Revision 2", exact=True
    ).wait_for(timeout=120_000)
    await page.get_by_text(
        "Customize the Agent goal, behaviors, and policies", exact=True
    ).click()
    await page.get_by_label("Goal", exact=True).fill(
        "Answer exact product lookup questions and require review before changing a cart."
    )
    await page.get_by_role("button", name="Save customization", exact=True).click()
    await page.locator(".designer-home__status").get_by_text(
        "Revision 3", exact=True
    ).wait_for(timeout=30_000)
    await page.get_by_role("button", name="Review for approval", exact=True).click()
    await page.get_by_role(
        "heading", name="Approve exact Agent design", exact=True
    ).wait_for(timeout=30_000)
    await page.get_by_role("button", name="Approve design", exact=True).click()
    await page.get_by_role("button", name="Request build", exact=True).click()
    await page.get_by_role("button", name="Build requested", exact=True).wait_for(
        timeout=30_000
    )

    await horizontal._open_agent_area_for_mode(
        page,
        "surface",
        label="Builds",
        heading="Agent Builds",
        return_operation_id="designer.return_to_agent",
        open_operation_id="agents.open_builds",
        prompt=horizontal.CHAT_PROMPTS["enter_build"],
        trace=[],
        interactions=[],
        continuation="Continue to Builds",
    )
    await page.get_by_role(
        "button", name="Assemble accepted build", exact=True
    ).click()
    ready = page.locator(".builder-home li[data-status='ready']")
    await ready.wait_for(timeout=180_000)
    ids["buildId"] = await horizontal._latest_build_id(observations)
    coverage = ready.get_by_role(
        "region", name=f"Initial evaluation coverage for build {ids['buildId']}", exact=True
    )
    await coverage.get_by_text(
        re.compile(r"^(Queued automatically|Generating automatically|Ready with [1-9][0-9]* generated case)")
    ).wait_for(timeout=180_000)
    await ready.get_by_role("button", name="Start runtime", exact=True).click()
    await ready.get_by_text("Running", exact=True).first.wait_for(timeout=30_000)
    return ids


async def _open_sandbox(page: Page) -> None:
    await horizontal._open_agent_area_for_mode(
        page,
        "surface",
        label="Sandbox",
        heading="Agent Sandbox",
        return_operation_id="agents.return_to_hub",
        open_operation_id="agents.open_sandbox",
        prompt=horizontal.CHAT_PROMPTS["enter_private_trial"],
        trace=[],
        interactions=[],
        continuation="Continue to Sandbox",
    )
    await page.locator("#sandbox-title").wait_for(timeout=30_000)


async def _refresh_sandbox_surface(page: Page) -> None:
    await page.reload(wait_until="domcontentloaded")
    await page.locator("#sandbox-title").wait_for(timeout=90_000)


async def _run_sandbox_journey(
    page: Page,
    directory: Path,
    ids: dict[str, str],
    responses: list[dict[str, object]],
    medusa_region_id: str,
) -> dict[str, object]:
    await _open_sandbox(page)
    await page.get_by_label("Ready immutable build", exact=True).select_option(
        ids["buildId"]
    )
    await page.get_by_role("button", name="Deploy to Sandbox", exact=True).click()
    await page.get_by_text(re.compile(r"^Active build ")).wait_for(timeout=60_000)
    deployment = await _wait_response(
        responses,
        method="POST",
        path_suffix="/sandbox/deployments",
        status=201,
    )
    ids["sandboxTargetId"] = str(deployment["target_id"])
    ids["sandboxDeploymentId"] = str(deployment["id"])
    ids["runtimeDeploymentId"] = str(deployment["runtime_deployment_id"])
    await _capture(page, directory, "01-explicit-sandbox-deployment")

    await page.get_by_role("button", name="Playground", exact=True).click()
    playground = page.get_by_role("region", name="Playground", exact=True)
    await playground.get_by_role(
        "button", name="New conversation", exact=True
    ).click()
    session_response = await _wait_response(
        responses, method="POST", path_suffix="/sandbox/sessions", status=201
    )
    session = session_response["session"]
    if not isinstance(session, dict):
        raise RuntimeError("The Playground session response is incomplete.")
    ids["playgroundSessionId"] = str(session["session_id"])

    message = playground.get_by_label("Message", exact=True)
    await _send_playground_message(
        page,
        playground,
        responses,
        session_id=ids["playgroundSessionId"],
        text='Find products matching "Medusa T-Shirt".',
    )
    await playground.locator(".sandbox-conversation li[data-role='assistant']").last.wait_for(
        timeout=180_000
    )
    write_turn = await _send_playground_message(
        page,
        playground,
        responses,
        session_id=ids["playgroundSessionId"],
        text="Create a cart.",
    )

    review = page.get_by_role("region", name="Review Sandbox Agent action")
    for _ in range(4):
        if await review.count():
            break
        projection = write_turn.get("projection")
        messages = projection.get("messages") if isinstance(projection, dict) else None
        assistant = next(
            (
                str(item.get("content", ""))
                for item in reversed(messages if isinstance(messages, list) else [])
                if isinstance(item, dict) and item.get("role") == "assistant"
            ),
            "",
        )
        folded = assistant.casefold()
        if "should i use" in folded or "which operation" in folded:
            answer = "Use carts."
        elif "region" in folded:
            answer = medusa_region_id
        else:
            raise RuntimeError(
                "The cart write did not reach a review or a recognized clarification: "
                f"{assistant}"
            )
        write_turn = await _send_playground_message(
            page,
            playground,
            responses,
            session_id=ids["playgroundSessionId"],
            text=answer,
        )
    await review.wait_for(timeout=180_000)
    await _capture(page, directory, "02-playground-review")
    await review.get_by_role("button", name="Approve action", exact=True).click()
    await review.wait_for(state="detached", timeout=180_000)
    conversation_response = await _wait_response(
        responses,
        method="POST",
        path_suffix=f"/sandbox/sessions/{ids['playgroundSessionId']}/reviews",
        status=200,
    )
    resolved_session = conversation_response.get("session")
    if not isinstance(resolved_session, dict) or str(resolved_session.get("session_id")) != ids["playgroundSessionId"]:
        raise RuntimeError("Review resolution did not retain the exact Playground session.")
    await _send_playground_message(
        page,
        playground,
        responses,
        session_id=ids["playgroundSessionId"],
        text="What product did we add, and what is the cart status now?",
    )
    await playground.locator(".sandbox-conversation li[data-role='assistant']").last.wait_for(
        timeout=180_000
    )
    await _capture(page, directory, "03-persistent-multiturn-playground")

    await playground.get_by_role("button", name="Open diagnostics", exact=True).click()
    await page.get_by_text(re.compile(r"^Runtime revision ")).wait_for(timeout=30_000)
    diagnostics = await _wait_response(
        responses,
        method="GET",
        path_suffix=f"/sandbox/sessions/{ids['playgroundSessionId']}/diagnostics",
        status=200,
    )
    await _capture(page, directory, "04-private-diagnostics")

    # Re-enter Sandbox before launching Evaluation so this surface fetches the
    # post-generation case collection rather than retaining an earlier render
    # that observed the set while its background job was still in flight.
    await _refresh_sandbox_surface(page)
    await page.get_by_role("button", name="Evaluations", exact=True).click()
    generated = page.get_by_role("listitem").filter(has_text="Generated coverage").first
    run_generated = generated.get_by_role(
        "button", name="Run against Sandbox", exact=True
    )
    await run_generated.wait_for(timeout=180_000)
    deadline = time.monotonic() + 30
    while time.monotonic() < deadline and not await run_generated.is_enabled():
        await page.wait_for_timeout(100)
    if not await run_generated.is_enabled():
        raise RuntimeError(
            "The ready generated Evaluation set has no runnable projected cases."
        )
    evaluation_snapshot = await _wait_response(
        responses,
        method="GET",
        path_suffix="/evaluations",
        status=200,
    )
    sets = evaluation_snapshot.get("evaluation_sets")
    if not isinstance(sets, list):
        raise RuntimeError("Evaluation sets are unavailable.")
    generated_set = next(
        item
        for item in sets
        if isinstance(item, dict)
        and item.get("name") == "Generated coverage"
        and str(item.get("build_id")) == ids["buildId"]
    )
    ids["evalsetId"] = str(generated_set["id"])
    await run_generated.click()
    queued = await _wait_response(
        responses,
        method="POST",
        path_suffix="/evaluations/sandbox-runs",
        status=202,
    )
    queued_sets = queued.get("evaluation_sets")
    queued_set = next(
        (
            item
            for item in (queued_sets if isinstance(queued_sets, list) else [])
            if isinstance(item, dict)
            and str(item.get("id")) == ids["evalsetId"]
        ),
        None,
    )
    queued_cases = queued_set.get("cases") if isinstance(queued_set, dict) else None
    queued_attempts = [
        item.get("latest_run_attempt")
        for item in (queued_cases if isinstance(queued_cases, list) else [])
        if isinstance(item, dict)
        and isinstance(item.get("latest_run_attempt"), dict)
    ]
    if not queued_attempts:
        raise RuntimeError("The Sandbox evaluation run queued no case attempts.")
    ids["evaluationAttemptId"] = str(queued_attempts[0]["id"])

    terminal: dict[str, object] | None = None
    deadline = time.monotonic() + 240
    while time.monotonic() < deadline:
        await _refresh_sandbox_surface(page)
        await page.get_by_role("button", name="Evaluations", exact=True).click()
        latest = _latest_response(
            responses,
            method="GET",
            path_suffix="/evaluations",
            status=200,
        )
        for evaluation_set in latest.get("evaluation_sets", []):
            if not isinstance(evaluation_set, dict) or str(evaluation_set.get("id")) != ids["evalsetId"]:
                continue
            for case in evaluation_set.get("cases", []):
                if not isinstance(case, dict):
                    continue
                attempt = case.get("latest_run_attempt")
                if isinstance(attempt, dict) and str(attempt.get("id")) == ids["evaluationAttemptId"]:
                    if attempt.get("status") in {"succeeded", "failed"}:
                        terminal = attempt
                        break
            if terminal is not None:
                break
        if terminal is not None:
            break
        await page.wait_for_timeout(2_000)
    if terminal is None:
        raise TimeoutError("The Sandbox evaluation attempt did not reach a durable terminal state.")
    ids["evaluationSessionId"] = str(terminal.get("sandbox_session_id") or "")
    if not ids["evaluationSessionId"]:
        raise RuntimeError("The evaluation result has no isolated Sandbox session lineage.")
    if ids["evaluationSessionId"] == ids["playgroundSessionId"]:
        raise RuntimeError("Evaluation reused the Playground session.")
    if terminal.get("status") != "succeeded":
        raise RuntimeError(
            f"The real Sandbox evaluation failed: {terminal.get('failure_code')} {terminal.get('failure_message')}"
        )
    await _capture(page, directory, "05-durable-evaluation-result")
    return {
        "diagnosticsRevision": diagnostics.get("projection", {}).get("revision")
        if isinstance(diagnostics.get("projection"), dict)
        else None,
        "evaluationStatus": terminal.get("status"),
        "evaluationFailureCode": terminal.get("failure_code"),
    }


async def run(args: argparse.Namespace) -> Path:
    horizontal.ACTIVE_MEDUSA_SPEC = MEDUSA_SPEC
    medusa_key = os.environ.get("MEDUSA_PUBLISHABLE_KEY") or _load_required_value(
        MEDUSA_ENV, "MEDUSA_PUBLISHABLE_KEY"
    )
    medusa_region_id = os.environ.get("MEDUSA_REGION_ID") or _load_required_value(
        MEDUSA_ENV, "MEDUSA_REGION_ID"
    )
    run_id = f"{datetime.now(UTC).strftime('%Y%m%dT%H%M%SZ')}-{uuid4().hex[:10]}"
    directory = ROOT / "artifacts" / "sandbox-deployment-v02" / run_id
    videos = directory / "raw-video"
    directory.mkdir(parents=True, exist_ok=False)
    owner = {
        "display_name": "Sandbox v0.2 Evidence Owner",
        "email": f"sandbox-v02-{uuid4().hex}@example.com",
        "password": f"Corpus-Sandbox-v02-{uuid4().hex}!9",
    }
    observations = _observation_state()
    diagnostics: dict[str, list[dict[str, object]]] = {
        "httpErrors": [],
        "consoleErrors": [],
        "pageErrors": [],
        "requestFailures": [],
        "expectedAbortedRequests": [],
    }
    trace: list[dict[str, object]] = []
    private_responses: list[dict[str, object]] = []
    ids: dict[str, str] = {}
    error: str | None = None
    result: dict[str, object] = {}
    video_path: Path | None = None

    async with async_playwright() as playwright:
        browser = await playwright.chromium.launch(headless=not args.headed)
        context = await browser.new_context(
            viewport={"width": 1440, "height": 1000},
            record_video_dir=videos,
            record_video_size={"width": 1440, "height": 1000},
        )
        page = await context.new_page()
        _attach_diagnostics(page, "sandbox-v02", diagnostics, trace, observations)
        horizontal._observe_horizontal(page, observations, trace)
        _record_private_runtime_responses(page, private_responses)
        try:
            await _register_with_direct_loopback_dispatch(page, args.url, owner)
            ids.update(await _prepare_ready_build(page, directory, observations, medusa_key))
            result = await _run_sandbox_journey(
                page,
                directory,
                ids,
                private_responses,
                medusa_region_id,
            )
        except Exception as caught:
            error = f"{type(caught).__name__}: {caught}"
            try:
                await _capture(page, directory, "99-failure")
            except Exception:
                pass
        finally:
            page_video = page.video
            await context.close()
            if page_video is not None:
                video_path = Path(await page_video.path())
            await browser.close()

    retained_video: str | None = None
    video_sha256: str | None = None
    if video_path is not None and video_path.is_file():
        final_video = directory / "sandbox-deployment-v02.webm"
        shutil.copy2(video_path, final_video)
        retained_video = str(final_video.relative_to(ROOT)).replace("\\", "/")
        video_sha256 = hashlib.sha256(final_video.read_bytes()).hexdigest()

    if error is None:
        unexpected_diagnostics = {
            name: len(diagnostics[name])
            for name in ("httpErrors", "pageErrors", "requestFailures")
            if diagnostics[name]
        }
        if unexpected_diagnostics:
            error = (
                "RuntimeError: unexpected_browser_diagnostics: "
                + ", ".join(
                    f"{name}={count}"
                    for name, count in unexpected_diagnostics.items()
                )
            )

    evidence = {
        "schema": "corpus.sandbox-deployment-mode.v0.2.evidence.v1",
        "runId": run_id,
        "status": "passed" if error is None else "failed",
        "recordedAt": datetime.now(UTC).isoformat(),
        "runtime": {
            "location": "local",
            "productUrl": f"{args.url.rstrip('/')}/",
            "readinessUrl": f"{BACKEND_URL}/readyz",
            "medusaBaseUrl": MEDUSA_BASE_URL,
            "playbackRate": 1.0,
        },
        "ids": ids,
        "result": result,
        "video": {
            "path": retained_video,
            "sha256": video_sha256,
            "bytes": (ROOT / retained_video).stat().st_size if retained_video else None,
        },
        "diagnostics": diagnostics,
        "error": error,
    }
    evidence_path = directory / "result.json"
    evidence_path.write_text(json.dumps(evidence, indent=2) + "\n", encoding="utf-8")
    if error is not None:
        raise RuntimeError(f"Sandbox deployment journey failed; see {evidence_path}: {error}")
    return evidence_path


def main() -> None:
    evidence = asyncio.run(run(arguments()))
    print(evidence)


if __name__ == "__main__":
    main()
