from __future__ import annotations

import argparse
import asyncio
import hashlib
import json
import re
import shutil
import subprocess
import sys
from datetime import UTC, datetime
from pathlib import Path
from urllib.parse import urlsplit
from uuid import uuid4

from playwright.async_api import Page, TimeoutError as PlaywrightTimeoutError, async_playwright

REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
if str(REPOSITORY_ROOT) not in sys.path:
    sys.path.insert(0, str(REPOSITORY_ROOT))

import scripts.run_api_contract_revision_journey as contract_journey
from scripts.deployed_e2e_runtime import GcpJourneyRuntime
from scripts.run_api_contract_revision_journey import (
    EXPECTED_FINAL,
    EXPECTED_RAW,
    MEDUSA_SPEC,
    _capture,
    _inside_viewport,
    _latest_review_id,
    _observed_current_source,
    _observed_proposals,
    _proposal_panel,
    _record,
    _register,
    _review_surface,
    _source_hub,
    _source_ids,
    _upload,
    _wait_ready,
)


MEDUSA_ENV = Path(r"D:\Dev\AI Projects\routedeck\examples\medusa-agent\.env.local")
ALLOWED_PHASE_OPERATION_IDS = frozenset(
    {
        "workspace.open_sources",
        "sources.open_api_creation",
        "sources.propose_contract_revision",
        "sources.approve_contract_revision",
        "sources.save_api_connection",
        "sources.test_api_connection",
    }
)
EXPECTED_ASSERTION_COUNT = 8


async def main() -> None:
    parser = argparse.ArgumentParser(description="Record the safe API connection-check lifecycle.")
    parser.add_argument("--url", default="http://127.0.0.1:5199")
    parser.add_argument("--backend-url", default="http://127.0.0.1:8099")
    parser.add_argument("--runtime-mode", choices=("local", "gcp-production"), default="local")
    parser.add_argument("--medusa-spec", type=Path, default=MEDUSA_SPEC)
    parser.add_argument("--medusa-env", type=Path, default=MEDUSA_ENV)
    parser.add_argument("--medusa-base-url", default="http://127.0.0.1:9100")
    parser.add_argument("--gcp-project", default="saastoagent")
    parser.add_argument("--corpus-vm", default="corpus-vm-1")
    parser.add_argument("--corpus-zone", default="asia-south1-a")
    parser.add_argument("--medusa-vm", default="medusa-test-vm-1")
    parser.add_argument("--medusa-zone", default="us-west1-a")
    parser.add_argument("--headed", action="store_true")
    args = parser.parse_args()
    repository = Path(__file__).resolve().parents[1]
    if not args.medusa_spec.is_file():
        raise SystemExit("The exact reviewed Medusa Source is unavailable.")
    raw_sha256 = hashlib.sha256(args.medusa_spec.read_bytes()).hexdigest()
    if raw_sha256 != EXPECTED_RAW:
        raise SystemExit("The exact reviewed Medusa Source is unavailable.")
    contract_journey.MEDUSA_SPEC = args.medusa_spec
    runtime = (
        GcpJourneyRuntime(
            project=args.gcp_project,
            corpus_vm=args.corpus_vm,
            corpus_zone=args.corpus_zone,
            medusa_vm=args.medusa_vm,
            medusa_zone=args.medusa_zone,
            medusa_base_url=args.medusa_base_url,
        )
        if args.runtime_mode == "gcp-production"
        else None
    )
    medusa_key = _load_required_value(args.medusa_env, "MEDUSA_PUBLISHABLE_KEY")
    invalid_key = f"invalid-phase-c-{uuid4().hex}"
    run_id = f"{datetime.now(UTC).strftime('%Y%m%dT%H%M%SZ')}-{uuid4().hex[:10]}"
    directory = repository / "artifacts" / "api-connection-check" / run_id
    directory.mkdir(parents=True, exist_ok=False)
    screenshots: list[str] = []
    assertions: list[dict[str, object]] = []
    safe_trace: list[dict[str, object]] = []
    diagnostics: dict[str, list[dict[str, object]]] = {
        "httpErrors": [],
        "consoleErrors": [],
        "pageErrors": [],
        "requestFailures": [],
        "expectedAbortedRequests": [],
        "expectedBusinessFailures": [],
    }
    observations: dict[str, object] = {
        "sourceInventory": [],
        "sourceInventoryVersion": 0,
        "currentSources": {},
        "contractProposals": {},
        "profiles": {},
        "checks": {},
    }
    ids: dict[str, str] = {}
    owner = {
        "display_name": "API Check Evidence Owner",
        "email": f"api-check-{uuid4().hex}@example.com",
        "password": f"Corpus-Api-Check-{uuid4().hex}!8",
    }
    other_owner = {
        "display_name": "API Check Isolation Owner",
        "email": f"api-check-isolation-{uuid4().hex}@example.com",
        "password": f"Corpus-Api-Isolation-{uuid4().hex}!8",
    }
    video_path: str | None = None
    error: str | None = None
    phase_trace_start = 0
    phase_trace_end = 0

    async with async_playwright() as playwright:
        browser = await playwright.chromium.launch(headless=not args.headed)
        context = await browser.new_context(
            viewport={"width": 1440, "height": 1000},
            record_video_dir=directory / "raw-video",
            record_video_size={"width": 1440, "height": 1000},
        )
        page = await context.new_page()
        _attach_diagnostics(page, diagnostics, safe_trace, observations)
        try:
            await _register(page, args.url, owner)
            phase_trace_start = len(safe_trace)
            await page.get_by_role("button", name="Open Sources", exact=True).click()
            hub = _source_hub(page)
            await hub.get_by_role("heading", name="Source Hub", exact=True).wait_for(timeout=30_000)
            await _upload_current(page, hub, args.medusa_spec)
            await hub.get_by_text("ready", exact=True).first.wait_for(timeout=180_000)
            ids.update(await _source_ids(page, observations))
            inventory_500s = [
                item for item in diagnostics["httpErrors"]
                if item.get("method") == "GET" and item.get("path") == "/api/sources" and item.get("status") == 500
            ]
            _record(assertions, "fresh Source processing publishes a coherent ready inventory", not inventory_500s, {
                "sourceId": ids["sourceId"],
                "parentRevisionId": ids["parentRevisionId"],
                "jobId": ids.get("jobId"),
                "inventory500Count": len(inventory_500s),
            })

            await hub.get_by_role("button", name="Review API changes", exact=True).click()
            proposal_panel = _proposal_panel(page)
            await proposal_panel.get_by_role(
                "heading", name="Proposed API version update", exact=True
            ).wait_for(timeout=90_000)
            proposals = await _observed_proposals(observations, ids["sourceId"])
            ids["proposalId"] = str(proposals[0]["proposal_id"])
            expected_final_sha256 = _expected_final_sha256(
                proposals[0], runtime_mode=args.runtime_mode
            )
            await proposal_panel.get_by_role(
                "button", name="Review this API update", exact=True
            ).click()
            review_surface = _review_surface(page)
            await review_surface.get_by_role(
                "heading", name="Create this immutable API version?", exact=True
            ).wait_for(timeout=30_000)
            ids["reviewId"] = await _latest_review_id(safe_trace)
            await review_surface.get_by_role(
                "button", name="Accept and create new version", exact=True
            ).click()
            await hub.get_by_text("Validated API version", exact=True).wait_for(timeout=60_000)
            current = await _observed_current_source(
                observations,
                ids["sourceId"],
                excluding_revision_id=ids["parentRevisionId"],
            )
            ids["approvedRevisionId"] = str(current["revision"]["revision_id"])
            if current["revision"]["summary"].get("final_canonical_sha256") != expected_final_sha256:
                raise RuntimeError("The approved Source revision is not the exact reviewed contract.")
            _record(assertions, "owner approved the exact effective API revision", True, {
                "proposalId": ids["proposalId"],
                "reviewId": ids["reviewId"],
                "approvedRevisionId": ids["approvedRevisionId"],
                "finalHash": expected_final_sha256,
            })

            await hub.get_by_role("button", name="Connection", exact=True).click()
            panel = hub.locator("section.api-connection-panel")
            await panel.get_by_role("heading", name="API connections", exact=True).wait_for(timeout=30_000)
            profile_prefix = "Private Medusa" if runtime is not None else "Local Medusa"
            await _save_profile(
                panel,
                f"{profile_prefix} valid",
                medusa_key,
                base_url=args.medusa_base_url,
            )
            valid_profiles = await _profiles(observations, ids["sourceId"], minimum_count=1)
            valid = next(
                item for item in valid_profiles
                if item.get("profile_name") == f"{profile_prefix} valid"
            )
            ids["validProfileId"] = str(valid["id"])
            await panel.get_by_label("Connection profile", exact=True).select_option(ids["validProfileId"])
            await panel.get_by_label("Safe check operation", exact=True).select_option("GetProductTypes")
            await panel.get_by_role("button", name="Test connection", exact=True).click()
            await panel.get_by_text("Connection check succeeded", exact=True).wait_for(timeout=60_000)
            valid_checks = await _checks(observations, ids["sourceId"], minimum_count=1)
            valid_check = next(item for item in valid_checks if item.get("status") == "succeeded")
            ids["validCheckId"] = str(valid_check["id"])
            if valid_check.get("http_call_count") != 1 or valid_check.get("status_code") != 200:
                raise RuntimeError("The real safe read did not retain its exact one-call success.")
            valid_desktop_bounds = await _capture_result_viewport(
                page,
                repository,
                directory,
                screenshots,
                panel,
                status="succeeded",
                name="01-valid-check-desktop",
            )
            _record(assertions, "valid protected profile performs one validated GetProductTypes read", True, {
                "profileId": ids["validProfileId"],
                "checkId": ids["validCheckId"],
                "operationId": valid_check.get("operation_id"),
                "httpCallCount": valid_check.get("http_call_count"),
                "statusCode": valid_check.get("status_code"),
                "validationIssueCount": valid_check.get("validation_issue_count"),
                "desktopBounds": valid_desktop_bounds,
            })

            await _save_profile(
                panel,
                f"{profile_prefix} invalid",
                invalid_key,
                base_url=args.medusa_base_url,
            )
            profiles = await _profiles(observations, ids["sourceId"], minimum_count=2)
            invalid = next(
                item for item in profiles
                if item.get("profile_name") == f"{profile_prefix} invalid"
            )
            ids["invalidProfileId"] = str(invalid["id"])
            await panel.get_by_label("Connection profile", exact=True).select_option(ids["invalidProfileId"])
            await panel.get_by_role("button", name="Test connection", exact=True).click()
            await panel.get_by_text("Connection check failed", exact=True).wait_for(timeout=60_000)
            failed_checks = await _checks(observations, ids["sourceId"], minimum_count=2)
            failed_check = next(item for item in failed_checks if item.get("connection_profile_id") == ids["invalidProfileId"])
            ids["failedCheckId"] = str(failed_check["id"])
            if failed_check.get("status") != "failed" or failed_check.get("http_call_count") != 1:
                raise RuntimeError("The invalid credential did not remain a one-call failed check.")
            if len(diagnostics["expectedBusinessFailures"]) != 1:
                raise RuntimeError("The exact invalid-credential business failure was not uniquely observed.")
            invalid_desktop_bounds = await _capture_result_viewport(
                page,
                repository,
                directory,
                screenshots,
                panel,
                status="failed",
                name="02-invalid-credential-failure-desktop",
            )
            _record(assertions, "invalid credential remains a visible persisted one-call failure", True, {
                "profileId": ids["invalidProfileId"],
                "checkId": ids["failedCheckId"],
                "httpCallCount": failed_check.get("http_call_count"),
                "errorCode": failed_check.get("error_code"),
                "expectedRouteDeckFailureCount": 1,
                "desktopBounds": invalid_desktop_bounds,
            })

            await page.reload()
            await panel.get_by_text("Connection check succeeded", exact=True).wait_for(timeout=30_000)
            await panel.get_by_text("Connection check failed", exact=True).wait_for(timeout=30_000)
            await page.set_viewport_size({"width": 390, "height": 844})
            check_section = panel.locator("section.api-connection-checks")
            safe_heading = check_section.get_by_role("heading", name="Test API connection", exact=True)
            test_button = check_section.get_by_role("button", name="Test connection", exact=True)
            await safe_heading.scroll_into_view_if_needed()
            surface_dock = page.locator("[data-agent-surface-dock]")
            initial_control_bounds = {
                "heading": await safe_heading.bounding_box(),
                "button": await test_button.bounding_box(),
            }
            scroll_delta = _scroll_delta_for_group(
                initial_control_bounds,
                await surface_dock.bounding_box(),
                margin=16.0,
            )
            await surface_dock.evaluate(
                "(element, delta) => element.scrollBy({top: delta, left: 0, behavior: 'instant'})",
                scroll_delta,
            )
            control_bounds = {
                "heading": await safe_heading.bounding_box(),
                "button": await test_button.bounding_box(),
            }
            if not all(_inside_viewport(value, 390, 844) for value in control_bounds.values()):
                raise RuntimeError(f"Safe-check controls are outside the mobile viewport: {control_bounds}")
            await _capture(page, repository, directory, screenshots, "03a-check-controls-mobile-390x844", full_page=False)
            failed_item = check_section.locator('li[data-status="failed"]').first
            latest_failure = failed_item.get_by_text("Connection check failed", exact=True)
            await latest_failure.scroll_into_view_if_needed()
            failure_bounds = {"failure": await latest_failure.bounding_box()}
            if not all(_inside_viewport(value, 390, 844) for value in failure_bounds.values()):
                raise RuntimeError(f"Safe-check failure is outside the mobile viewport: {failure_bounds}")
            await _capture(page, repository, directory, screenshots, "03b-check-failure-mobile-390x844", full_page=False)
            _record(assertions, "reload retains redacted success and failure evidence on mobile", True, {
                "viewport": {"width": 390, "height": 844},
                "controlBounds": control_bounds,
                "failureBounds": failure_bounds,
                "checkCount": len(failed_checks),
                "captureSequence": ["03a-check-controls-mobile-390x844", "03b-check-failure-mobile-390x844"],
            })

            await page.set_viewport_size({"width": 1440, "height": 1000})
            if runtime is None:
                subprocess.run(
                    ["docker", "compose", "restart", "backend"],
                    cwd=repository,
                    check=True,
                    capture_output=True,
                    text=True,
                )
                await asyncio.to_thread(
                    _wait_ready, args.backend_url.rstrip("/") + "/readyz"
                )
            else:
                await asyncio.to_thread(runtime.restart_corpus, args.backend_url)
            await page.reload()
            await panel.get_by_text("Connection check succeeded", exact=True).wait_for(timeout=60_000)
            await panel.get_by_text("Connection check failed", exact=True).wait_for(timeout=60_000)
            restarted_checks = await _checks(observations, ids["sourceId"], minimum_count=2)
            await _capture(page, repository, directory, screenshots, "04-check-history-after-restart", full_page=True)
            _record(assertions, "immutable check history survives backend restart", len(restarted_checks) == 2, {
                "checkIds": sorted(str(item["id"]) for item in restarted_checks),
            })

            phase_trace_end = len(safe_trace)
            sign_out = page.get_by_label("Sign out", exact=True)
            await sign_out.wait_for(timeout=30_000)
            await sign_out.click()
            await page.get_by_role("heading", name="Explore Corpus", exact=True).wait_for(timeout=30_000)
            await sign_out.wait_for(state="detached", timeout=30_000)
            await _register(page, args.url, other_owner)
            await page.get_by_role("button", name="Open Sources", exact=True).click()
            other_hub = _source_hub(page)
            await other_hub.get_by_text("No API sources yet.", exact=True).wait_for(timeout=30_000)
            if await other_hub.get_by_text("Medusa Store", exact=False).count() != 0:
                raise RuntimeError("The second owner can see the first owner's Source.")
            await _capture(page, repository, directory, screenshots, "05-other-owner-empty-inventory", full_page=True)
            _record(assertions, "second owner cannot see the Source or connection checks", True, {
                "visibleSourceCount": 0,
                "firstOwnerSourceId": ids["sourceId"],
            })

            phase_trace = safe_trace[phase_trace_start:phase_trace_end]
            observed_operation_ids = {
                str(item["operationId"])
                for item in phase_trace
                if isinstance(item.get("operationId"), str)
            }
            unexpected_operation_ids = sorted(observed_operation_ids - ALLOWED_PHASE_OPERATION_IDS)
            call_counts = sorted(
                int(item["http_call_count"])
                for item in restarted_checks
            )
            _record(assertions, "campaign stays inside the safe-check operation boundary", not unexpected_operation_ids and call_counts == [1, 1], {
                "observedOperationIds": sorted(observed_operation_ids),
                "unexpectedOperationIds": unexpected_operation_ids,
                "checkHttpCallCounts": call_counts,
                "genericExecutionOperationObserved": False,
            })
        except Exception as caught:
            error = f"{type(caught).__name__}: {caught}"
        finally:
            video = page.video
            await page.close()
            if video is not None:
                raw = Path(await video.path())
                final = directory / "api-connection-check-continuous.webm"
                raw.replace(final)
                video_path = str(final.relative_to(repository))
            await context.close()
            await browser.close()

    classify_expected_console_errors(diagnostics)
    unexpected = (
        diagnostics["httpErrors"]
        + diagnostics["consoleErrors"]
        + diagnostics["pageErrors"]
        + diagnostics["requestFailures"]
    )
    passed = (
        error is None
        and not unexpected
        and len(assertions) == EXPECTED_ASSERTION_COUNT
        and all(bool(item["passed"]) for item in assertions)
    )
    trace_path = directory / "corpus-trace.json"
    result = {
        "schema": "corpus.api-connection-check-journey.v1",
        "runId": run_id,
        "status": "passed" if passed else "failed",
        "runtime": {
            "location": (
                "GCP production VMs"
                if args.runtime_mode == "gcp-production"
                else "local Docker Compose"
            ),
            "frontend": args.url,
            "backend": args.backend_url,
            "medusa": args.medusa_base_url,
            "medusaSourceSha256": raw_sha256,
            "runtimeMode": args.runtime_mode,
        },
        "ids": ids,
        "assertions": assertions,
        "diagnostics": diagnostics,
        "screenshots": screenshots,
        "video": video_path,
        "trace": str(trace_path.relative_to(repository)),
        "rawPlaywrightTrace": None,
        "redaction": {
            "headers": False,
            "query": False,
            "cookies": False,
            "requestBodies": False,
            "responseBodies": False,
            "credentials": False,
        },
        "error": error,
        "limitations": [
            "This slice proves only GetProductTypes/GetProductTags connection checks, not generic API execution, curation or route planning.",
            "The real invalid credential is intentionally expected to fail; only its exact RouteDeck operation/failure code can be classified as expected.",
            "Outbound call count is retained by the Corpus execution adapter and immutable check record; browser diagnostics do not inspect target request headers or bodies.",
        ],
    }
    result_path = directory / "result.json"
    trace_json = json.dumps(safe_trace, indent=2) + "\n"
    result_json = json.dumps(result, indent=2) + "\n"
    _publish_evidence(
        directory=directory,
        result_path=result_path,
        trace_path=trace_path,
        result_json=result_json,
        trace_json=trace_json,
        secrets=(medusa_key, invalid_key),
    )
    print(f"run={run_id} status={result['status']} assertions={len(assertions)}")
    print(f"artifact={result_path}")
    if error is not None:
        print(f"error={error}")
    raise SystemExit(0 if passed else 1)


def _expected_final_sha256(
    proposal: dict[str, object], *, runtime_mode: str
) -> str:
    value = proposal.get("final_canonical_sha256")
    del runtime_mode
    parent = proposal.get("repaired_parent_sha256")
    if (
        value != EXPECTED_FINAL
        or not isinstance(parent, str)
        or re.fullmatch(r"[0-9a-f]{64}", parent) is None
    ):
        raise RuntimeError(
            "The proposal does not preserve the exact reviewed correction contract."
        )
    return EXPECTED_FINAL


async def _upload_current(page: Page, hub, medusa_spec: Path) -> None:
    await hub.locator(".sources-header-actions").get_by_role(
        "button", name="Add API source", exact=True
    ).click()
    intake = page.locator("section.sources-debug.api-source-workspace")
    await intake.get_by_role(
        "heading", name="Add API source", exact=True
    ).wait_for(timeout=30_000)
    source_name = intake.get_by_label("Source name", exact=True)
    deadline = asyncio.get_running_loop().time() + 15
    while asyncio.get_running_loop().time() < deadline:
        try:
            await source_name.wait_for(state="visible", timeout=1_000)
            await source_name.fill("Reviewed private Medusa Store", timeout=1_000)
            await page.wait_for_timeout(100)
            if await source_name.input_value(timeout=1_000) == "Reviewed private Medusa Store":
                break
        except PlaywrightTimeoutError:
            pass
    else:
        raise RuntimeError("The Source intake did not retain its exact name.")
    definition = intake.get_by_label("OpenAPI or Swagger definition", exact=True)
    await definition.set_input_files(medusa_spec)
    if await definition.input_value() == "":
        raise RuntimeError("The private Medusa definition was not bound to intake.")
    if await source_name.input_value() != "Reviewed private Medusa Store":
        await source_name.fill("Reviewed private Medusa Store")
    await intake.get_by_role(
        "button", name="Add API definition", exact=True
    ).click()
    await intake.get_by_text("Ready to analyze", exact=True).wait_for(timeout=90_000)
    await intake.get_by_role(
        "button", name="Analyze API operations", exact=True
    ).click()


async def _save_profile(
    panel,
    name: str,
    credential: str,
    *,
    base_url: str = "http://host.docker.internal:9100",
) -> None:
    await panel.get_by_label("Profile name", exact=True).fill(name)
    await panel.get_by_label("Environment", exact=True).fill("local")
    await panel.get_by_label("Base URL", exact=True).fill(base_url)
    await panel.get_by_label("Authentication", exact=True).select_option("api_key")
    await panel.get_by_label("Header name", exact=True).fill("x-publishable-api-key")
    await panel.get_by_label("API key", exact=True).fill(credential)
    await panel.get_by_role("button", name="Save connection", exact=True).click()
    await panel.get_by_text(name, exact=True).wait_for(timeout=30_000)


async def _capture_result_viewport(
    page: Page,
    repository: Path,
    directory: Path,
    screenshots: list[str],
    panel,
    *,
    status: str,
    name: str,
) -> dict[str, dict[str, float] | None]:
    result = panel.locator(f'li[data-status="{status}"]').first
    label = result.get_by_text(
        "Connection check succeeded" if status == "succeeded" else "Connection check failed",
        exact=True,
    )
    await label.wait_for(timeout=30_000)
    await result.scroll_into_view_if_needed()
    surface_dock = page.locator("[data-agent-surface-dock]")
    scroll_delta = _scroll_delta_for_group(
        {"result": await result.bounding_box()},
        await surface_dock.bounding_box(),
        margin=16.0,
    )
    await surface_dock.evaluate(
        "(element, delta) => element.scrollBy({top: delta, left: 0, behavior: 'instant'})",
        scroll_delta,
    )
    bounds = {
        "result": await result.bounding_box(),
        "status": await label.bounding_box(),
    }
    viewport = page.viewport_size
    if viewport is None or not all(
        _inside_viewport(value, viewport["width"], viewport["height"])
        for value in bounds.values()
    ):
        raise RuntimeError(f"The {status} connection result is outside the desktop viewport: {bounds}")
    await _capture(page, repository, directory, screenshots, name, full_page=False)
    return bounds


async def _profiles(observations: dict[str, object], source_id: str, *, minimum_count: int):
    for _ in range(150):
        values = observations["profiles"].get(source_id, [])
        if isinstance(values, list) and len(values) >= minimum_count:
            return values
        await asyncio.sleep(0.1)
    raise TimeoutError("The redacted connection profile observation did not arrive.")


async def _checks(observations: dict[str, object], source_id: str, *, minimum_count: int):
    for _ in range(150):
        values = observations["checks"].get(source_id, [])
        if isinstance(values, list) and len(values) >= minimum_count:
            return values
        await asyncio.sleep(0.1)
    raise TimeoutError("The redacted connection-check observation did not arrive.")


def _attach_diagnostics(page: Page, diagnostics, trace, observations) -> None:
    sequence = 0
    response_statuses: dict[tuple[str, str], int] = {}

    async def response_event(response) -> None:
        nonlocal sequence
        path = urlsplit(response.url).path
        if not path.startswith("/api/"):
            return
        response_statuses[(response.request.method, path)] = response.status
        sequence += 1
        event: dict[str, object] = {
            "sequence": sequence,
            "event": "response",
            "method": response.request.method,
            "path": path,
            "status": response.status,
        }
        body = None
        if path.endswith("/dispatch") or "/reviews/" in path:
            try:
                body = await response.json()
                event["disposition"] = body.get("disposition")
                event["operationId"] = body.get("operation_id")
                event["outcome"] = body.get("outcome")
                failure = body.get("failure")
                event["failureCode"] = failure.get("code") if isinstance(failure, dict) else None
                review = body.get("review")
                if isinstance(review, dict):
                    event["reviewId"] = review.get("id")
            except Exception:
                event["parse"] = "unavailable"
        elif response.request.method == "GET" and response.status == 200:
            try:
                body = await response.json()
                parts = [part for part in path.split("/") if part]
                if parts == ["api", "sources"] and isinstance(body, list):
                    observations["sourceInventory"] = body
                    observations["sourceInventoryVersion"] = int(observations["sourceInventoryVersion"]) + 1
                elif len(parts) == 3 and parts[:2] == ["api", "sources"] and isinstance(body, dict):
                    observations["currentSources"][parts[2]] = body
                elif len(parts) == 4 and parts[:2] == ["api", "sources"] and parts[3] == "contract-revisions" and isinstance(body, list):
                    observations["contractProposals"][parts[2]] = body
                elif len(parts) == 4 and parts[:2] == ["api", "sources"] and parts[3] == "connections" and isinstance(body, list):
                    observations["profiles"][parts[2]] = [
                        {
                            "id": item.get("id"),
                            "profile_name": item.get("profile_name"),
                            "revision_id": item.get("revision_id"),
                            "credential_version": item.get("credential_version"),
                        }
                        for item in body if isinstance(item, dict)
                    ]
                elif len(parts) == 4 and parts[:2] == ["api", "sources"] and parts[3] == "connection-checks" and isinstance(body, list):
                    observations["checks"][parts[2]] = [
                        {
                            key: item.get(key)
                            for key in (
                                "id", "source_revision_id", "connection_profile_id",
                                "operation_id", "status", "status_code", "error_code",
                                "validation_issue_count", "http_call_count",
                                "effective_contract_sha256",
                            )
                        }
                        for item in body if isinstance(item, dict)
                    ]
            except Exception:
                pass
        trace.append(event)
        if response.status >= 400:
            item = {
                "status": response.status,
                "method": response.request.method,
                "path": path,
                "operationId": event.get("operationId"),
                "failureCode": event.get("failureCode"),
            }
            target = (
                diagnostics["expectedBusinessFailures"]
                if is_expected_invalid_credential_failure(item)
                else diagnostics["httpErrors"]
            )
            target.append(item)

    page.on("response", response_event)
    def console_event(message) -> None:
        if message.type not in {"warning", "error"}:
            return
        location = message.location or {}
        diagnostics["consoleErrors"].append(
            {
                "type": message.type,
                "text": message.text[:500],
                "locationPath": urlsplit(str(location.get("url", ""))).path,
            }
        )

    page.on("console", console_event)
    page.on("pageerror", lambda exception: diagnostics["pageErrors"].append({"message": str(exception)[:500]}))

    def request_failed(request) -> None:
        item = {"method": request.method, "path": urlsplit(request.url).path, "failure": request.failure}
        expected_abort = is_expected_aborted_request(item, response_statuses)
        diagnostics["expectedAbortedRequests" if expected_abort else "requestFailures"].append(item)

    page.on("requestfailed", request_failed)


def is_expected_aborted_request(
    item: dict[str, object],
    response_statuses: dict[tuple[str, str], int],
) -> bool:
    if item.get("failure") != "net::ERR_ABORTED":
        return False
    method = str(item.get("method", ""))
    path = str(item.get("path", ""))
    route_deck_poll = path.startswith("/api/routedeck/") and (
        path.endswith("/events")
        or "/conversation" in path
        or "/private-forms/" in path
    )
    completed_sign_out_navigation = (
        method == "POST"
        and path == "/api/auth/sign-out"
        and response_statuses.get((method, path)) == 204
    )
    return route_deck_poll or completed_sign_out_navigation


def is_expected_invalid_credential_failure(item: dict[str, object]) -> bool:
    return (
        item.get("status") == 409
        and item.get("method") == "POST"
        and str(item.get("path", "")).endswith("/dispatch")
        and item.get("operationId") == "sources.test_api_connection"
        and item.get("failureCode") == "api_connection_check_failed"
    )


def classify_expected_console_errors(diagnostics: dict[str, list[dict[str, object]]]) -> None:
    remaining = len(diagnostics["expectedBusinessFailures"])
    retained: list[dict[str, object]] = []
    for item in diagnostics["consoleErrors"]:
        text = str(item.get("text", ""))
        if (
            remaining > 0
            and "Failed to load resource" in text
            and "409" in text
            and str(item.get("locationPath", "")).endswith("/dispatch")
        ):
            remaining -= 1
            continue
        retained.append(item)
    diagnostics["consoleErrors"] = retained


def _load_required_value(path: Path, name: str) -> str:
    if not path.is_file():
        raise SystemExit("The local Medusa credential file is unavailable.")
    for line in path.read_text(encoding="utf-8").splitlines():
        key, separator, value = line.partition("=")
        if separator and key.strip() == name and value.strip():
            return value.strip().strip('"').strip("'")
    raise SystemExit("The required local Medusa credential is unavailable.")


def _publish_evidence(
    *,
    directory: Path,
    result_path: Path,
    trace_path: Path,
    result_json: str,
    trace_json: str,
    secrets: tuple[str, ...],
) -> None:
    encoded = tuple(secret.encode("utf-8") for secret in secrets if secret)
    leak = any(secret.decode("utf-8") in result_json or secret.decode("utf-8") in trace_json for secret in encoded)
    if not leak:
        for path in directory.rglob("*"):
            if path.is_file() and any(secret in path.read_bytes() for secret in encoded):
                leak = True
                break
    if leak:
        # This directory is created exclusively for the current recorder run.
        # Remove it before raising so detected credentials never become evidence.
        shutil.rmtree(directory)
        raise RuntimeError("Sensitive value detected; recorder evidence was removed before publication.")
    trace_path.write_text(trace_json, encoding="utf-8")
    result_path.write_text(result_json, encoding="utf-8")


def _scroll_delta_for_group(
    targets: dict[str, dict[str, float] | None],
    container: dict[str, float] | None,
    *,
    margin: float,
) -> float:
    if container is None or not targets or any(value is None for value in targets.values()):
        raise RuntimeError("The mobile evidence bounds are unavailable.")
    concrete = tuple(value for value in targets.values() if value is not None)
    group_top = min(value["y"] for value in concrete)
    group_bottom = max(value["y"] + value["height"] for value in concrete)
    available_height = container["height"] - (2 * margin)
    if group_bottom - group_top > available_height:
        raise RuntimeError("The mobile evidence controls cannot fit inside the surface dock with the required margin.")
    return group_top - (container["y"] + margin)


if __name__ == "__main__":
    asyncio.run(main())
