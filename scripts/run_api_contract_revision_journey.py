from __future__ import annotations

import argparse
import asyncio
import hashlib
import json
import subprocess
import urllib.request
from datetime import UTC, datetime
from pathlib import Path
from urllib.parse import urlsplit
from uuid import uuid4

from playwright.async_api import Page, TimeoutError as PlaywrightTimeoutError, async_playwright


MEDUSA_SPEC = Path(
    r"D:\Dev\AI Projects\agent-core\research\openapi_toolrouter_benchmark"
    r"\data\openapi\medusa_store.yaml"
)
EXPECTED_RAW = "fd17273078c222a5632459f67204cbc9cf03cb925641d47669209baa9cc97fb6"
EXPECTED_PARENT = "bc1b4b2456eefab4684a07ffa6e63f652118f5a705dd13eba5d77e74ab965c6e"
EXPECTED_FINAL = "c0b9c6bf1b149a0e458de9fbda4f7bad3cf6f9f7eb4ff383bded3b09d23e50ef"
ALLOWED_OPERATION_IDS = frozenset({
    "workspace.open_sources",
    "sources.open_api_creation",
    "sources.propose_contract_revision",
    "sources.approve_contract_revision",
})


async def main() -> None:
    parser = argparse.ArgumentParser(description="Record immutable API contract revision review.")
    parser.add_argument("--url", default="http://127.0.0.1:5199")
    parser.add_argument("--headed", action="store_true")
    args = parser.parse_args()
    repository = Path(__file__).resolve().parents[1]
    if not MEDUSA_SPEC.is_file() or hashlib.sha256(MEDUSA_SPEC.read_bytes()).hexdigest() != EXPECTED_RAW:
        raise SystemExit("The exact reviewed Medusa source is unavailable.")

    run_id = f"{datetime.now(UTC).strftime('%Y%m%dT%H%M%SZ')}-{uuid4().hex[:10]}"
    directory = repository / "artifacts" / "api-contract-revision" / run_id
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
    }
    observations: dict[str, object] = {
        "sourceInventory": [],
        "sourceInventoryVersion": 0,
        "currentSources": {},
        "contractProposals": {},
    }
    ids: dict[str, str] = {}
    owner = {
        "display_name": "Contract Revision Evidence Owner",
        "email": f"contract-revision-{uuid4().hex}@example.com",
        "password": f"Corpus-Contract-{uuid4().hex}!8",
    }
    video_path: str | None = None
    error: str | None = None
    phase_trace_start = 0

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
            await _upload(page, hub)
            await hub.get_by_text("ready", exact=True).first.wait_for(timeout=180_000)
            await hub.get_by_role("button", name="Review API changes", exact=True).wait_for(timeout=30_000)
            ids.update(await _source_ids(page, observations))
            await _capture(page, repository, directory, screenshots, "01-ready-parent-desktop", full_page=True)
            _record(assertions, "exact reviewed raw Source became ready", True, {
                "sourceId": ids["sourceId"],
                "parentRevisionId": ids["parentRevisionId"],
                "rawSha256": EXPECTED_RAW,
            })

            await hub.get_by_role("button", name="Review API changes", exact=True).click()
            proposal_panel = _proposal_panel(page)
            await proposal_panel.get_by_role("heading", name="Proposed API version update", exact=True).wait_for(timeout=90_000)
            await proposal_panel.get_by_text("Shared-schema impact: 2", exact=True).wait_for()
            await proposal_panel.get_by_text("6435eb6c5861391b", exact=True).wait_for()
            await proposal_panel.get_by_text(EXPECTED_PARENT, exact=True).wait_for()
            await proposal_panel.get_by_text(EXPECTED_FINAL, exact=True).wait_for()
            proposals = await _observed_proposals(observations, ids["sourceId"])
            if len(proposals) != 1:
                raise RuntimeError("The exact persisted contract proposal was not unique.")
            ids["proposalId"] = proposals[0]["proposal_id"]
            _assert_proposal(proposals[0])
            proposal_top_bounds = await _capture_desktop_viewport(
                page,
                proposal_panel,
                proposal_panel.get_by_role(
                    "heading", name="Proposed API version update", exact=True
                ),
                {
                    "heading": proposal_panel.get_by_role(
                        "heading", name="Proposed API version update", exact=True
                    ),
                    "impact": proposal_panel.get_by_text(
                        "Shared-schema impact: 2", exact=True
                    ),
                },
                repository,
                directory,
                screenshots,
                "02-proposal-top-desktop",
            )
            proposal_review_button = proposal_panel.get_by_role(
                "button", name="Review this API update", exact=True
            )
            proposal_bottom_bounds = await _capture_desktop_viewport(
                page,
                proposal_panel,
                proposal_review_button,
                {
                    "lastPatch": proposal_panel.get_by_text(
                        "3f4de4aa354d0324", exact=True
                    ),
                    "review": proposal_review_button,
                },
                repository,
                directory,
                screenshots,
                "03-proposal-patches-review-desktop",
            )
            _record(assertions, "proposal exposes the exact chain and shared impact before review", True, {
                "proposalId": ids["proposalId"], "patchCount": 12, "impactCount": 2,
                "parentHash": EXPECTED_PARENT, "finalHash": EXPECTED_FINAL,
                "desktopViewport": {"width": 1440, "height": 1000},
                "desktopTopBounds": proposal_top_bounds,
                "desktopBottomBounds": proposal_bottom_bounds,
            })

            await proposal_panel.get_by_role("button", name="Review this API update", exact=True).click()
            review_surface = _review_surface(page)
            review_heading = review_surface.get_by_role("heading", name="Create this immutable API version?", exact=True)
            await review_heading.wait_for(timeout=30_000)
            await page.reload()
            await review_heading.wait_for(timeout=30_000)
            ids["reviewId"] = await _latest_review_id(safe_trace)
            review_bounds = await _capture_desktop_viewport(
                page,
                review_surface,
                review_heading,
                {
                    "heading": review_heading,
                    "impact": review_surface.get_by_text(
                        "Explicit shared-schema impact: 2", exact=True
                    ),
                    "accept": review_surface.get_by_role(
                        "button", name="Accept and create new version", exact=True
                    ),
                    "reject": review_surface.get_by_role(
                        "button", name="Keep current version unchanged", exact=True
                    ),
                },
                repository,
                directory,
                screenshots,
                "04-review-reloaded-desktop",
            )
            _record(assertions, "required review survives reload with exact proposal evidence", True, {
                "reviewId": ids["reviewId"], "parentRevisionId": ids["parentRevisionId"],
                "desktopViewport": {"width": 1440, "height": 1000},
                "desktopBounds": review_bounds,
            })

            await page.set_viewport_size({"width": 390, "height": 844})
            accept = review_surface.get_by_role("button", name="Accept and create new version", exact=True)
            reject = review_surface.get_by_role("button", name="Keep current version unchanged", exact=True)
            await accept.scroll_into_view_if_needed()
            await page.wait_for_timeout(300)
            bounds = {
                "heading": await review_heading.bounding_box(),
                "impact": await review_surface.get_by_text("Explicit shared-schema impact: 2", exact=True).bounding_box(),
                "accept": await accept.bounding_box(),
                "reject": await reject.bounding_box(),
            }
            if not all(_inside_viewport(value, 390, 844) for value in bounds.values()):
                raise RuntimeError(f"Review controls are outside the mobile viewport: {bounds}")
            await _capture(page, repository, directory, screenshots, "05-review-mobile-390x844", full_page=False)
            _record(assertions, "mobile review shows impact and both decisions in viewport", True, {
                "viewport": {"width": 390, "height": 844}, "bounds": bounds,
            })

            inventory_version = int(observations["sourceInventoryVersion"])
            await reject.click()
            await page.reload()
            await hub.get_by_role("heading", name="Source Hub", exact=True).wait_for(timeout=30_000)
            current_after_reject = await _observed_current_source(
                observations,
                ids["sourceId"],
                minimum_inventory_version=inventory_version + 1,
            )
            if current_after_reject["revision"]["revision_id"] != ids["parentRevisionId"]:
                raise RuntimeError("Review rejection mutated the Source revision.")
            _record(assertions, "review rejection leaves the parent revision current", True, {
                "currentRevisionId": ids["parentRevisionId"],
            })

            await page.set_viewport_size({"width": 1440, "height": 1000})
            await proposal_panel.get_by_role("button", name="Review this API update", exact=True).click()
            await review_heading.wait_for(timeout=30_000)
            await review_surface.get_by_role("button", name="Accept and create new version", exact=True).click()
            await hub.get_by_text("Validated API version", exact=True).wait_for(timeout=60_000)
            current = await _observed_current_source(
                observations, ids["sourceId"],
                excluding_revision_id=ids["parentRevisionId"],
            )
            ids["approvedRevisionId"] = current["revision"]["revision_id"]
            if ids["approvedRevisionId"] == ids["parentRevisionId"]:
                raise RuntimeError("Approval did not create a new Source revision.")
            if current["revision"]["parent_revision_id"] != ids["parentRevisionId"]:
                raise RuntimeError("The approved revision lost its exact parent identity.")
            if current["revision"]["summary"]["final_canonical_sha256"] != EXPECTED_FINAL:
                raise RuntimeError("The approved revision hash is not the reviewed final hash.")
            await page.reload()
            await hub.get_by_text("Validated API version", exact=True).wait_for(timeout=30_000)
            await _capture(page, repository, directory, screenshots, "06-approved-reloaded-desktop", full_page=True)
            _record(assertions, "approval creates a new immutable child and reload preserves it", True, {
                "parentRevisionId": ids["parentRevisionId"],
                "approvedRevisionId": ids["approvedRevisionId"],
                "finalHash": EXPECTED_FINAL,
            })

            # Restart remains after visual proof so evidence ordering cannot hide
            # the mobile review state if recovery itself fails.
            subprocess.run(
                ["docker", "compose", "restart", "backend"],
                cwd=repository,
                check=True,
                capture_output=True,
                text=True,
            )
            await asyncio.to_thread(_wait_ready, "http://127.0.0.1:8099/readyz")
            await page.reload()
            await hub.get_by_role("heading", name="Source Hub", exact=True).wait_for(timeout=60_000)
            await hub.get_by_text("Validated API version", exact=True).wait_for(timeout=60_000)
            restarted = await _observed_current_source(
                observations, ids["sourceId"]
            )
            if restarted["revision"]["revision_id"] != ids["approvedRevisionId"]:
                raise RuntimeError("The approved revision did not survive backend restart.")
            await _capture(page, repository, directory, screenshots, "07-approved-after-restart", full_page=True)
            _record(assertions, "approved revision survives backend restart", True, {
                "approvedRevisionId": ids["approvedRevisionId"],
            })

            phase_trace = safe_trace[phase_trace_start:]
            observed_operation_ids = {
                str(item["operationId"])
                for item in phase_trace
                if isinstance(item.get("operationId"), str)
            }
            unexpected_operation_ids = sorted(observed_operation_ids - ALLOWED_OPERATION_IDS)
            no_execution_path = not unexpected_operation_ids
            _record(assertions, "proposal review and approval dispatch only the bounded non-execution operations", no_execution_path, {
                "observedRequestCount": sum(1 for item in phase_trace if item.get("event") == "response"),
                "observedOperationIds": sorted(observed_operation_ids),
                "allowedOperationIds": sorted(ALLOWED_OPERATION_IDS),
                "unexpectedOperationIds": unexpected_operation_ids,
                "serverBoundary": "ApiContractRevisionService has no HTTP transport dependency; backend focused test and exact reference preflight cover it.",
            })
        except Exception as caught:
            error = f"{type(caught).__name__}: {caught}"
        finally:
            video = page.video
            await page.close()
            if video is not None:
                raw = Path(await video.path())
                final = directory / "api-contract-revision-continuous.webm"
                raw.replace(final)
                video_path = str(final.relative_to(repository))
            await context.close()
            await browser.close()

    unexpected = (
        diagnostics["httpErrors"]
        + diagnostics["consoleErrors"]
        + diagnostics["pageErrors"]
        + diagnostics["requestFailures"]
    )
    passed = error is None and not unexpected and len(assertions) == 8 and all(
        bool(item["passed"]) for item in assertions
    )
    trace_path = directory / "corpus-trace.json"
    trace_path.write_text(json.dumps(safe_trace, indent=2) + "\n", encoding="utf-8")
    result = {
        "schema": "corpus.api-contract-revision-journey.v1",
        "runId": run_id,
        "status": "passed" if passed else "failed",
        "runtime": {
            "location": "local Docker Compose",
            "frontend": args.url,
            "backend": "http://127.0.0.1:8099",
            "command": ".\\.venv\\Scripts\\python.exe scripts\\run_api_contract_revision_journey.py --url http://127.0.0.1:5199",
        },
        "ids": ids,
        "assertions": assertions,
        "diagnostics": diagnostics,
        "screenshots": screenshots,
        "video": video_path,
        "trace": str(trace_path.relative_to(repository)),
        "rawPlaywrightTrace": None,
        "redaction": {"headers": False, "cookies": False, "requestBodies": False, "responseBodies": False, "credentials": False},
        "error": error,
        "limitations": [
            "The reviewed contract is a Corpus derivative for local Medusa 2.13.6 evidence, not an official or version-pinned Medusa contract.",
            "The journey proves proposal/review/approval only; it does not run a connection check or execute an API operation.",
            "Browser diagnostics cannot observe server outbound traffic; zero transport is also enforced structurally because the Phase B service has no HTTP transport dependency and by focused backend tests.",
        ],
    }
    result_path = directory / "result.json"
    result_path.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(f"run={run_id} status={result['status']} assertions={len(assertions)}")
    print(f"artifact={result_path}")
    if error is not None:
        print(f"error={error}")
    raise SystemExit(0 if passed else 1)


async def _register(page: Page, url: str, owner: dict[str, str]) -> None:
    await page.goto(url)
    await page.get_by_role("heading", name="Explore Corpus").wait_for(timeout=30_000)
    await page.get_by_role("button", name="Create account", exact=True).click()
    await page.get_by_role("heading", name="Create account", exact=True).wait_for(timeout=15_000)
    await _bind_registration_fields(page, owner)
    await page.locator("form").get_by_role("button", name="Create account", exact=True).click()
    await page.get_by_label("Sign out", exact=True).wait_for(timeout=30_000)


async def _bind_registration_fields(page: Page, owner: dict[str, str]) -> None:
    expected = (
        (page.get_by_label("Display name", exact=True), owner["display_name"]),
        (page.get_by_label("Email", exact=True), owner["email"]),
        (page.get_by_label("Password", exact=True), owner["password"]),
    )
    deadline = asyncio.get_running_loop().time() + 15
    while asyncio.get_running_loop().time() < deadline:
        try:
            for field, _ in expected:
                await field.wait_for(state="visible", timeout=1_000)
            if not all([await field.is_enabled() for field, _ in expected]):
                await page.wait_for_timeout(100)
                continue
            for field, value in expected:
                await field.fill(value, timeout=1_000)
            await page.wait_for_timeout(100)
            if all([await field.input_value(timeout=1_000) == value for field, value in expected]):
                return
        except PlaywrightTimeoutError:
            pass
    raise RuntimeError("The registration form did not retain its exact owner inputs.")


async def _upload(page: Page, hub) -> None:
    await hub.locator(".sources-header-actions").get_by_role(
        "button", name="Add API source", exact=True
    ).click()
    await hub.get_by_role("heading", name="Add an API source", exact=True).wait_for()
    await hub.get_by_label("Source name").fill("Reviewed local Medusa Store")
    await hub.get_by_label("OpenAPI or Swagger definition").set_input_files(MEDUSA_SPEC)
    await hub.get_by_role("button", name="Add API definition", exact=True).click()
    await hub.get_by_text("Ready to analyze", exact=True).wait_for(timeout=30_000)
    await hub.get_by_role("button", name="Analyze API operations", exact=True).click()


def _source_hub(page: Page):
    return page.locator('section.sources-debug[aria-labelledby="source-hub-title"]')


def _proposal_panel(page: Page):
    return page.locator(".contract-revision-panel")


def _review_surface(page: Page):
    return page.locator(".contract-revision-review")


async def _source_ids(page: Page, observations: dict[str, object]) -> dict[str, str]:
    detail = page.locator(".source-detail-list")
    revision = await detail.locator("div", has_text="API version").locator("code").first.inner_text()
    for _ in range(100):
        sources = observations.get("sourceInventory")
        if isinstance(sources, list):
            matches = [
                item for item in sources
                if isinstance(item, dict)
                and isinstance(item.get("revision"), dict)
                and item["revision"].get("revision_id") == revision
            ]
            if len(matches) == 1:
                return {
                    "sourceId": str(matches[0]["source_id"]),
                    "parentRevisionId": revision,
                    "jobId": str(matches[0]["revision"]["job_id"]),
                }
        await page.wait_for_timeout(100)
    raise RuntimeError("The exact ready Source identity was not observed in its owner inventory.")


async def _observed_current_source(
    observations: dict[str, object],
    source_id: str,
    *,
    excluding_revision_id: str | None = None,
    minimum_inventory_version: int | None = None,
) -> dict[str, object]:
    for _ in range(100):
        if minimum_inventory_version is None:
            current = observations.get("currentSources")
            if isinstance(current, dict):
                value = current.get(source_id)
                if isinstance(value, dict) and isinstance(value.get("revision"), dict):
                    revision_id = value["revision"].get("revision_id")
                    if excluding_revision_id is None or revision_id != excluding_revision_id:
                        return value
        inventory = observations.get("sourceInventory")
        inventory_version = observations.get("sourceInventoryVersion")
        if (
            isinstance(inventory, list)
            and (
                minimum_inventory_version is None
                or isinstance(inventory_version, int)
                and inventory_version >= minimum_inventory_version
            )
        ):
            matches = [item for item in inventory if isinstance(item, dict) and item.get("source_id") == source_id]
            if len(matches) == 1 and isinstance(matches[0].get("revision"), dict):
                revision_id = matches[0]["revision"].get("revision_id")
                if excluding_revision_id is None or revision_id != excluding_revision_id:
                    return matches[0]
        await asyncio.sleep(0.1)
    raise RuntimeError("The current owner-scoped Source state was not observed.")


async def _observed_proposals(
    observations: dict[str, object], source_id: str
) -> list[dict[str, object]]:
    for _ in range(100):
        values = observations.get("contractProposals")
        if isinstance(values, dict):
            proposals = values.get(source_id)
            if isinstance(proposals, list) and proposals:
                return [item for item in proposals if isinstance(item, dict)]
        await asyncio.sleep(0.1)
    raise RuntimeError("The owner-scoped persisted contract proposal was not observed.")


async def _latest_review_id(trace: list[dict[str, object]]) -> str:
    for item in reversed(trace):
        review_id = item.get("reviewId")
        if isinstance(review_id, str) and review_id:
            return review_id
    raise RuntimeError("The durable review ID was not observed.")


def _assert_proposal(proposal: dict[str, object]) -> None:
    patches = proposal.get("patches")
    if proposal.get("repaired_parent_sha256") != EXPECTED_PARENT or proposal.get("final_canonical_sha256") != EXPECTED_FINAL:
        raise RuntimeError("The persisted proposal hash chain is invalid.")
    if not isinstance(patches, list) or len(patches) != 11:
        raise RuntimeError("The persisted proposal does not contain eleven patches.")
    shared = [item for item in patches if isinstance(item, dict) and item.get("patch_id") == "6435eb6c5861391b"]
    if len(shared) != 1 or shared[0].get("impact_count") != 2:
        raise RuntimeError("The shared BaseRegionCountry impact is invalid.")


def _attach_diagnostics(page: Page, diagnostics, trace, observations) -> None:
    sequence = 0

    async def response_event(response) -> None:
        nonlocal sequence
        path = urlsplit(response.url).path
        if not path.startswith("/api/"):
            return
        sequence += 1
        event: dict[str, object] = {"sequence": sequence, "event": "response", "method": response.request.method, "path": path, "status": response.status}
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
                    observations["sourceInventoryVersion"] = int(
                        observations["sourceInventoryVersion"]
                    ) + 1
                elif len(parts) == 3 and parts[:2] == ["api", "sources"] and isinstance(body, dict):
                    observations["currentSources"][parts[2]] = body
                elif len(parts) == 4 and parts[:2] == ["api", "sources"] and parts[3] == "contract-revisions" and isinstance(body, list):
                    observations["contractProposals"][parts[2]] = body
            except Exception:
                pass
        trace.append(event)
        if response.status >= 400:
            diagnostics["httpErrors"].append({"status": response.status, "method": response.request.method, "path": path})

    page.on("response", response_event)
    page.on("console", lambda message: diagnostics["consoleErrors"].append({"type": message.type, "text": message.text[:500]}) if message.type in {"warning", "error"} else None)
    page.on("pageerror", lambda exception: diagnostics["pageErrors"].append({"message": str(exception)[:500]}))
    def request_failed(request) -> None:
        item = {
            "method": request.method,
            "path": urlsplit(request.url).path,
            "failure": request.failure,
        }
        target = (
            diagnostics["expectedAbortedRequests"]
            if _is_expected_abort(item)
            else diagnostics["requestFailures"]
        )
        target.append(item)

    page.on("requestfailed", request_failed)


def _is_expected_abort(item: dict[str, object]) -> bool:
    if item.get("failure") != "net::ERR_ABORTED":
        return False
    path = str(item.get("path", ""))
    return path.startswith("/api/routedeck/") and (
        path.endswith("/events")
        or "/conversation" in path
        or "/private-forms/" in path
    )


def _wait_ready(url: str) -> None:
    for _ in range(60):
        try:
            with urllib.request.urlopen(url, timeout=2) as response:
                if response.status == 200:
                    return
        except Exception:
            pass
        import time
        time.sleep(1)
    raise RuntimeError("Corpus backend did not recover after restart.")


def _inside_viewport(value: dict[str, float] | None, width: int, height: int) -> bool:
    return value is not None and value["x"] >= 0 and value["y"] >= 0 and value["x"] + value["width"] <= width and value["y"] + value["height"] <= height


async def _capture(page: Page, repository: Path, directory: Path, output: list[str], name: str, *, full_page: bool) -> None:
    path = directory / f"{name}.png"
    await page.screenshot(path=path, full_page=full_page)
    output.append(str(path.relative_to(repository)))


async def _capture_desktop_viewport(
    page: Page,
    surface,
    scroll_target,
    targets: dict[str, object],
    repository: Path,
    directory: Path,
    output: list[str],
    name: str,
) -> dict[str, dict[str, float] | None]:
    width, height = 1440, 1000
    await page.set_viewport_size({"width": width, "height": height})
    await scroll_target.scroll_into_view_if_needed()
    await surface.wait_for(state="visible")
    await page.wait_for_timeout(300)
    bounds = {name: await target.bounding_box() for name, target in targets.items()}
    if not all(_inside_viewport(value, width, height) for value in bounds.values()):
        raise RuntimeError(f"{name} evidence is outside the desktop viewport: {bounds}")
    path = directory / f"{name}.png"
    await page.screenshot(path=path, full_page=False)
    output.append(str(path.relative_to(repository)))
    return bounds


def _record(assertions: list[dict[str, object]], name: str, passed: bool, observed: object) -> None:
    assertions.append({"name": name, "passed": passed, "observed": observed})


if __name__ == "__main__":
    asyncio.run(main())
