from __future__ import annotations

import argparse
import asyncio
import json
import shutil
import subprocess
import sys
import time
from datetime import UTC, datetime
from pathlib import Path
from urllib.parse import parse_qs, urlsplit
from uuid import uuid4

from playwright.async_api import Page, async_playwright

REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
if str(REPOSITORY_ROOT) not in sys.path:
    sys.path.insert(0, str(REPOSITORY_ROOT))

from scripts.run_agents_archive_delete_journey import (
    chronological_ffmpeg_command,
    save_video,
)
from scripts.run_api_connection_check_journey import (
    _publish_evidence,
    _scroll_delta_for_group,
    is_expected_aborted_request,
)
from scripts.run_api_contract_revision_journey import (
    _capture,
    _inside_viewport,
    _record,
    _register,
    _source_hub,
    _source_ids,
    _wait_ready,
)


EXPECTED_OPERATION_IDS = frozenset({"createOrder", "listOrders", "trackShipment"})
EXPECTED_PHASE_OPERATION_IDS = frozenset(
    {
        "workspace.open_sources",
        "sources.open_api_creation",
        "sources.save_api_operation_curation",
    }
)
EXPECTED_ASSERTION_COUNT = 9
PROBE_NAME = "API operation curation development probe"
PROBE_YAML = b"""openapi: 3.0.3
info:
  title: Corpus operation curation development probe
  version: 1.0.0
paths:
  /orders:
    get:
      operationId: listOrders
      responses:
        '200':
          description: Orders
          content:
            application/json:
              schema:
                type: array
                items:
                  type: object
    post:
      operationId: createOrder
      responses:
        '201':
          description: Created
  /shipments/{shipment_id}:
    get:
      operationId: trackShipment
      parameters:
        - name: shipment_id
          in: path
          required: true
          schema:
            type: string
      responses:
        '200':
          description: Shipment
"""


async def main() -> None:
    parser = argparse.ArgumentParser(description="Record exact API operation curation.")
    parser.add_argument("--url", default="http://127.0.0.1:5199")
    parser.add_argument("--backend-url", default="http://127.0.0.1:8099")
    parser.add_argument("--headed", action="store_true")
    args = parser.parse_args()
    repository = Path(__file__).resolve().parents[1]
    run_id = f"{datetime.now(UTC).strftime('%Y%m%dT%H%M%SZ')}-{uuid4().hex[:10]}"
    directory = repository / "artifacts" / "api-operation-curation" / run_id
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
        "sequence": 0,
        "sourceInventory": [],
        "sourceInventoryVersion": 0,
        "curations": {},
    }
    ids: dict[str, str] = {}
    owner = {
        "display_name": "Operation Curation Evidence Owner",
        "email": f"api-curation-{uuid4().hex}@example.com",
        "password": f"Corpus-Api-Curation-{uuid4().hex}!8",
    }
    other_owner = {
        "display_name": "Operation Curation Isolation Owner",
        "email": f"api-curation-isolation-{uuid4().hex}@example.com",
        "password": f"Corpus-Api-Curation-Isolation-{uuid4().hex}!8",
    }
    phase_trace_start = 0
    phase_trace_end = 0
    primary_video_path: str | None = None
    race_video_path: str | None = None
    assembled_video: str | None = None
    assembly: dict[str, object] | None = None
    race_start: float | None = None
    race_end: float | None = None
    error: str | None = None

    async with async_playwright() as playwright:
        browser = await playwright.chromium.launch(headless=not args.headed)
        context = await browser.new_context(
            viewport={"width": 1440, "height": 1000},
            record_video_dir=directory / "raw-video",
            record_video_size={"width": 1440, "height": 1000},
        )
        primary = await context.new_page()
        video_clock = time.monotonic()
        _attach_diagnostics(primary, "primary", diagnostics, safe_trace, observations)
        race_page: Page | None = None
        try:
            await _register(primary, args.url, owner)
            ids["primaryConversationId"] = await _selected_conversation_id(primary)
            phase_trace_start = len(safe_trace)
            hub = await _open_sources(primary)
            await _upload_probe(hub)
            await hub.get_by_text("ready", exact=True).first.wait_for(timeout=180_000)
            ids.update(await _source_ids(primary, observations))
            inventory_500s = [
                item
                for item in diagnostics["httpErrors"]
                if item.get("method") == "GET"
                and item.get("path") == "/api/sources"
                and item.get("status") == 500
            ]
            panel = _curation_panel(primary)
            await panel.get_by_role("heading", name="API operation curation", exact=True).wait_for(
                timeout=60_000
            )
            initial = await _observed_curation(
                observations, ids["sourceId"], minimum_history=0
            )
            ids["artifactRevisionId"] = str(initial["artifact_revision_id"])
            ids["inventoryFingerprint"] = str(initial["inventory_fingerprint"])
            inventory_ids = {
                str(item["operation_id"])
                for item in initial.get("operations", [])
                if isinstance(item, dict)
            }
            _record(
                assertions,
                "fresh Source processing publishes one coherent exact ToolRouter inventory",
                not inventory_500s and inventory_ids == EXPECTED_OPERATION_IDS,
                {
                    "sourceId": ids["sourceId"],
                    "revisionId": ids["parentRevisionId"],
                    "jobId": ids.get("jobId"),
                    "artifactRevisionId": ids["artifactRevisionId"],
                    "inventory500Count": len(inventory_500s),
                    "operationIds": sorted(inventory_ids),
                },
            )

            await panel.get_by_label("Filter operations", exact=True).fill("track")
            visible_rows = await panel.locator(".api-curation-list > li").count()
            unclassified_copy = await panel.get_by_text(
                "3 operations still need an explicit decision.", exact=True
            ).inner_text()
            await panel.get_by_label("Filter operations", exact=True).fill("")
            _record(
                assertions,
                "filtering remains non-mutating and every operation starts unclassified",
                visible_rows == 1 and unclassified_copy.startswith("3 operations"),
                {"filteredVisibleRows": visible_rows, "unclassifiedCount": 3},
            )

            await _classify(
                panel,
                included={"listOrders", "trackShipment"},
                excluded={"createOrder"},
            )
            desktop_identity_bounds = await _capture_group(
                primary,
                panel,
                {
                    "heading": panel.get_by_role(
                        "heading", name="API operation curation", exact=True
                    ),
                    "revision": panel.get_by_text("Revision", exact=True),
                    "inventory": panel.get_by_text("Inventory", exact=True),
                },
                1440,
                1000,
                repository,
                directory,
                screenshots,
                "01a-curation-identity-desktop",
            )
            desktop_action_bounds = await _capture_group(
                primary,
                panel,
                {
                    "createExcluded": panel.locator(
                        ".api-curation-list > li", has_text="createOrder"
                    ).get_by_role("radio", name="Exclude", exact=True),
                    "listIncluded": panel.locator(
                        ".api-curation-list > li", has_text="listOrders"
                    ).get_by_role("radio", name="Include", exact=True),
                    "trackIncluded": panel.locator(
                        ".api-curation-list > li", has_text="trackShipment"
                    ).get_by_role("radio", name="Include", exact=True),
                    "classification": panel.get_by_text(
                        "Every discovered operation is explicitly classified.", exact=True
                    ),
                    "save": panel.get_by_role(
                        "button", name="Save operation selection", exact=True
                    ),
                },
                1440,
                1000,
                repository,
                directory,
                screenshots,
                "01b-curation-decisions-save-desktop",
            )
            await panel.get_by_role("button", name="Save operation selection", exact=True).click()
            await panel.get_by_text(
                "Saved 2 included and 1 excluded operations for this exact revision.",
                exact=True,
            ).wait_for(timeout=30_000)
            first = await _observed_curation(
                observations, ids["sourceId"], minimum_history=1
            )
            ids["firstCurationId"] = str(first["current"]["id"])
            _record(
                assertions,
                "first explicit selection appends one exact immutable curation",
                _selection(first) == ({"listOrders", "trackShipment"}, {"createOrder"}),
                {
                    "curationId": ids["firstCurationId"],
                    "historyCount": len(first["history"]),
                    "desktopIdentityBounds": desktop_identity_bounds,
                    "desktopActionBounds": desktop_action_bounds,
                    "captureSequence": [
                        "01a-curation-identity-desktop",
                        "01b-curation-decisions-save-desktop",
                    ],
                },
            )

            race_start = round(time.monotonic() - video_clock, 3)
            race_page = await context.new_page()
            _attach_diagnostics(race_page, "concurrent", diagnostics, safe_trace, observations)
            await race_page.goto(_concurrent_entry_url(primary.url, args.url))
            await race_page.get_by_label("Sign out", exact=True).wait_for(timeout=30_000)
            inherited = await _selected_conversation_id(race_page)
            await race_page.get_by_role("button", name="New conversation", exact=True).click()
            await race_page.wait_for_function(
                "([key, previous]) => sessionStorage.getItem(key) !== previous",
                arg=["corpus.selected-conversation.v1", inherited],
                timeout=30_000,
            )
            ids["concurrentConversationId"] = await _selected_conversation_id(race_page)
            race_hub = await _open_sources(race_page)
            await _select_source(race_hub, PROBE_NAME)
            race_panel = _curation_panel(race_page)
            await race_panel.get_by_text(
                "Every discovered operation is explicitly classified.", exact=True
            ).wait_for(timeout=30_000)
            await _classify(
                race_panel,
                included={"createOrder", "listOrders"},
                excluded={"trackShipment"},
            )
            await race_panel.get_by_role(
                "button", name="Save operation selection", exact=True
            ).click()
            await race_panel.get_by_text(
                "Saved 2 included and 1 excluded operations for this exact revision.",
                exact=True,
            ).wait_for(timeout=30_000)
            second = await _observed_curation(
                observations,
                ids["sourceId"],
                minimum_history=2,
                current_not=ids["firstCurationId"],
            )
            ids["secondCurationId"] = str(second["current"]["id"])
            _record(
                assertions,
                "a distinct authenticated conversation advances curation by exact CAS",
                ids["concurrentConversationId"] != ids["primaryConversationId"]
                and _selection(second) == ({"createOrder", "listOrders"}, {"trackShipment"}),
                {
                    "primaryConversationId": ids["primaryConversationId"],
                    "concurrentConversationId": ids["concurrentConversationId"],
                    "previousCurationId": ids["firstCurationId"],
                    "currentCurationId": ids["secondCurationId"],
                },
            )
            race_video = race_page.video
            await race_page.close()
            if race_video is not None:
                race_video_path = await save_video(
                    race_video,
                    repository,
                    directory / "concurrent-conversation.webm",
                )
            race_page = None
            race_end = round(time.monotonic() - video_clock, 3)

            await primary.bring_to_front()
            await panel.get_by_role("button", name="Save operation selection", exact=True).click()
            stale_alert = panel.get_by_role("alert")
            await stale_alert.wait_for(timeout=30_000)
            stale_text = await stale_alert.inner_text()
            authoritative = await _observed_curation(
                observations,
                ids["sourceId"],
                minimum_history=2,
                current_not=ids["firstCurationId"],
            )
            visible_included, visible_excluded = await _visible_selection(
                panel,
                expected_included={"createOrder", "listOrders"},
                expected_excluded={"trackShipment"},
            )
            visible_history_count = await _saved_version_count(panel, expected=2)
            _record(
                assertions,
                "stale first-conversation save fails and refetches the authoritative selection",
                "changed" in stale_text.lower()
                and str(authoritative["current"]["id"]) == ids["secondCurationId"]
                and len(authoritative["history"]) == 2
                and visible_included == {"createOrder", "listOrders"}
                and visible_excluded == {"trackShipment"}
                and visible_history_count == 2
                and len(diagnostics["expectedBusinessFailures"]) == 1,
                {
                    "failureCode": "api_operation_curation_selection_stale",
                    "priorCurationId": ids["firstCurationId"],
                    "authoritativeCurationId": ids["secondCurationId"],
                    "historyCount": len(authoritative["history"]),
                    "visibleIncluded": sorted(visible_included),
                    "visibleExcluded": sorted(visible_excluded),
                    "visibleSavedVersions": visible_history_count,
                },
            )
            await _capture_group(
                primary,
                panel,
                {
                    "failure": stale_alert,
                    "savedVersions": panel.get_by_text("Saved versions", exact=True),
                },
                1440,
                1000,
                repository,
                directory,
                screenshots,
                "02-stale-conflict-authoritative-desktop",
            )
            await _capture_group(
                primary,
                panel,
                {
                    "createIncluded": panel.locator(
                        ".api-curation-list > li", has_text="createOrder"
                    ).get_by_role("radio", name="Include", exact=True),
                    "trackExcluded": panel.locator(
                        ".api-curation-list > li", has_text="trackShipment"
                    ).get_by_role("radio", name="Exclude", exact=True),
                    "classification": panel.get_by_text(
                        "Every discovered operation is explicitly classified.", exact=True
                    ),
                },
                1440,
                1000,
                repository,
                directory,
                screenshots,
                "02b-stale-conflict-visible-authoritative-decisions-desktop",
            )

            await primary.reload()
            hub = _source_hub(primary)
            await hub.get_by_role("heading", name="Source Hub", exact=True).wait_for(timeout=60_000)
            await _select_source(hub, PROBE_NAME)
            panel = _curation_panel(primary)
            await panel.get_by_text("Every discovered operation is explicitly classified.", exact=True).wait_for(
                timeout=30_000
            )
            reloaded = await _observed_curation(
                observations,
                ids["sourceId"],
                minimum_history=2,
                current_not=ids["firstCurationId"],
            )
            _record(
                assertions,
                "reload preserves both immutable records and the exact current selection",
                str(reloaded["current"]["id"]) == ids["secondCurationId"]
                and len(reloaded["history"]) == 2,
                {"historyCount": 2, "currentCurationId": ids["secondCurationId"]},
            )

            await primary.set_viewport_size({"width": 390, "height": 844})
            mobile_identity_bounds = await _capture_group(
                primary,
                panel,
                {
                    "heading": panel.get_by_role(
                        "heading", name="API operation curation", exact=True
                    ),
                    "savedVersions": panel.get_by_text("Saved versions", exact=True),
                },
                390,
                844,
                repository,
                directory,
                screenshots,
                "03a-curation-identity-mobile-390x844",
            )
            mobile_action_bounds = await _capture_group(
                primary,
                panel,
                {
                    "classification": panel.get_by_text(
                        "Every discovered operation is explicitly classified.", exact=True
                    ),
                    "save": panel.get_by_role(
                        "button", name="Save operation selection", exact=True
                    ),
                },
                390,
                844,
                repository,
                directory,
                screenshots,
                "03b-curation-controls-mobile-390x844",
            )
            _record(
                assertions,
                "mobile viewport visibly contains persisted curation identity and controls",
                True,
                {
                    "viewport": {"width": 390, "height": 844},
                    "identityBounds": mobile_identity_bounds,
                    "actionBounds": mobile_action_bounds,
                    "captureSequence": [
                        "03a-curation-identity-mobile-390x844",
                        "03b-curation-controls-mobile-390x844",
                    ],
                },
            )

            await primary.set_viewport_size({"width": 1440, "height": 1000})
            subprocess.run(
                ["docker", "compose", "restart", "backend"],
                cwd=repository,
                check=True,
                capture_output=True,
                text=True,
            )
            await asyncio.to_thread(_wait_ready, args.backend_url.rstrip("/") + "/readyz")
            await primary.reload()
            hub = _source_hub(primary)
            await hub.get_by_role("heading", name="Source Hub", exact=True).wait_for(timeout=60_000)
            await _select_source(hub, PROBE_NAME)
            panel = _curation_panel(primary)
            await panel.get_by_text("Every discovered operation is explicitly classified.", exact=True).wait_for(
                timeout=60_000
            )
            restarted = await _observed_curation(
                observations,
                ids["sourceId"],
                minimum_history=2,
                current_not=ids["firstCurationId"],
            )
            await _capture(
                primary,
                repository,
                directory,
                screenshots,
                "04-curation-after-backend-restart",
                full_page=True,
            )
            _record(
                assertions,
                "exact curation history survives backend restart",
                str(restarted["current"]["id"]) == ids["secondCurationId"]
                and len(restarted["history"]) == 2,
                {"currentCurationId": ids["secondCurationId"], "historyCount": 2},
            )

            phase_trace_end = len(safe_trace)
            sign_out = primary.get_by_label("Sign out", exact=True)
            await sign_out.click()
            await primary.get_by_role("heading", name="Explore Corpus", exact=True).wait_for(
                timeout=30_000
            )
            await sign_out.wait_for(state="detached", timeout=30_000)
            await _register(primary, args.url, other_owner)
            other_hub = await _open_sources(primary)
            await other_hub.get_by_text("No API sources yet.", exact=True).wait_for(timeout=30_000)
            await _capture(
                primary,
                repository,
                directory,
                screenshots,
                "05-other-owner-empty-source-inventory",
                full_page=True,
            )
            phase_trace = safe_trace[phase_trace_start:phase_trace_end]
            observed_operation_ids = {
                str(item["operationId"])
                for item in phase_trace
                if isinstance(item.get("operationId"), str)
            }
            curation_dispatches = [
                item
                for item in phase_trace
                if item.get("operationId") == "sources.save_api_operation_curation"
            ]
            unexpected_operation_ids = sorted(
                observed_operation_ids - EXPECTED_PHASE_OPERATION_IDS
            )
            _record(
                assertions,
                "second owner is isolated and the campaign remains non-executing",
                await other_hub.locator(".sources-list > li").count() == 0
                and len(curation_dispatches) == 3
                and not unexpected_operation_ids,
                {
                    "firstOwnerSourceId": ids["sourceId"],
                    "secondOwnerVisibleSources": 0,
                    "curationDispatchCount": len(curation_dispatches),
                    "observedOperationIds": sorted(observed_operation_ids),
                    "unexpectedOperationIds": unexpected_operation_ids,
                    "externalApiCallCount": 0,
                },
            )
        except Exception as caught:
            error = f"{type(caught).__name__}: {caught}"
            try:
                await _capture(
                    primary,
                    repository,
                    directory,
                    screenshots,
                    "99-failure-state",
                    full_page=True,
                )
            except Exception:
                pass
        finally:
            if race_page is not None:
                race_video = race_page.video
                await race_page.close()
                if race_video is not None:
                    race_video_path = await save_video(
                        race_video,
                        repository,
                        directory / "concurrent-conversation.webm",
                    )
            primary_video = primary.video
            await primary.close()
            if primary_video is not None:
                primary_video_path = await save_video(
                    primary_video,
                    repository,
                    directory / "api-operation-curation-primary.webm",
                )
            await context.close()
            await browser.close()

    if (
        primary_video_path is not None
        and race_video_path is not None
        and race_start is not None
        and race_end is not None
    ):
        assembled_video, assembly = _assemble_video(
            repository=repository,
            directory=directory,
            primary=repository / primary_video_path,
            secondary=repository / race_video_path,
            race_start=race_start,
            race_end=race_end,
        )
    _classify_expected_console_errors(diagnostics)
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
        and assembled_video is not None
    )
    trace_path = directory / "corpus-trace.json"
    result_path = directory / "result.json"
    result = {
        "schema": "corpus.api-operation-curation-journey.v1",
        "runId": run_id,
        "status": "passed" if passed else "failed",
        "runtime": {
            "location": "local Docker Compose",
            "frontend": args.url,
            "backend": args.backend_url,
            "command": (
                ".\\.venv\\Scripts\\python.exe "
                "scripts\\run_api_operation_curation_journey.py "
                f"--url {args.url} --backend-url {args.backend_url}"
            ),
        },
        "ids": ids,
        "assertions": assertions,
        "diagnostics": diagnostics,
        "screenshots": screenshots,
        "video": assembled_video,
        "rawVideos": [
            item for item in (primary_video_path, race_video_path) if item is not None
        ],
        "videoAssembly": assembly,
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
            "The uploaded OpenAPI document is explicitly labeled a development probe; it is processed by the real Source Hub Huey worker and ToolRouter path, not a product fixture or fallback.",
            "The browser stale case is an exact current-curation CAS conflict between two real authenticated conversations. Exact changed-inventory fingerprint failure is separately covered by the real SQL RouteDeck guard test.",
            "The two-page concurrency sequence is retained as raw clips and one chronological ffmpeg assembly with exact offsets; raw Playwright tracing is disabled because it retains authorization headers.",
            "This slice never creates a route plan, resolves a credential, or executes an API operation. Zero execution is also enforced structurally and by focused backend tests because the curation service has no transport dependency.",
        ],
    }
    trace_json = json.dumps(safe_trace, indent=2) + "\n"
    result_json = json.dumps(result, indent=2) + "\n"
    _publish_evidence(
        directory=directory,
        result_path=result_path,
        trace_path=trace_path,
        result_json=result_json,
        trace_json=trace_json,
        secrets=(owner["password"], other_owner["password"]),
    )
    print(f"run={run_id} status={result['status']} assertions={len(assertions)}")
    print(f"artifact={result_path}")
    print("ids=" + json.dumps(ids, sort_keys=True))
    if error is not None:
        print(f"error={error}")
    raise SystemExit(0 if passed else 1)


async def _open_sources(page: Page):
    await page.get_by_role("button", name="Open Sources", exact=True).click()
    hub = _source_hub(page)
    await hub.get_by_role("heading", name="Source Hub", exact=True).wait_for(timeout=30_000)
    return hub


async def _upload_probe(hub) -> None:
    await hub.get_by_role("button", name="Add API source", exact=True).click()
    await hub.get_by_role("heading", name="Add an API source", exact=True).wait_for()
    await hub.get_by_label("Source name", exact=True).fill(PROBE_NAME)
    await hub.get_by_label("OpenAPI or Swagger definition", exact=True).set_input_files(
        {
            "name": "api-operation-curation-development-probe.yaml",
            "mimeType": "application/yaml",
            "buffer": PROBE_YAML,
        }
    )
    await hub.get_by_role("button", name="Upload and process", exact=True).click()


def _curation_panel(page: Page):
    return page.locator(
        'section.api-operation-curation[aria-labelledby="api-operation-curation-title"]'
    )


async def _select_source(hub, name: str) -> None:
    button = hub.locator(".sources-inventory .sources-list button", has_text=name)
    await button.wait_for(timeout=30_000)
    await button.click()
    await hub.get_by_role("heading", name=name, exact=True).wait_for(timeout=30_000)


async def _classify(panel, *, included: set[str], excluded: set[str]) -> None:
    if included | excluded != EXPECTED_OPERATION_IDS or included & excluded:
        raise RuntimeError("The recorder selection must explicitly classify the exact inventory.")
    for operation_id in sorted(EXPECTED_OPERATION_IDS):
        row = panel.locator(".api-curation-list > li", has_text=operation_id)
        decision = "Include" if operation_id in included else "Exclude"
        await row.get_by_role("radio", name=decision, exact=True).click()
    await panel.get_by_text(
        "Every discovered operation is explicitly classified.", exact=True
    ).wait_for()


async def _visible_selection(
    panel,
    *,
    expected_included: set[str],
    expected_excluded: set[str],
) -> tuple[set[str], set[str]]:
    for _ in range(150):
        included: set[str] = set()
        excluded: set[str] = set()
        for operation_id in sorted(EXPECTED_OPERATION_IDS):
            row = panel.locator(".api-curation-list > li", has_text=operation_id)
            if await row.get_by_role("radio", name="Include", exact=True).is_checked():
                included.add(operation_id)
            if await row.get_by_role("radio", name="Exclude", exact=True).is_checked():
                excluded.add(operation_id)
        if included == expected_included and excluded == expected_excluded:
            return included, excluded
        await asyncio.sleep(0.1)
    raise TimeoutError("The active curation surface did not adopt the authoritative decisions.")


async def _saved_version_count(panel, *, expected: int) -> int:
    row = panel.locator(".api-curation-identity > div", has_text="Saved versions")
    for _ in range(150):
        value = (await row.locator("dd").inner_text()).strip()
        if value.isdigit() and int(value) == expected:
            return int(value)
        await asyncio.sleep(0.1)
    raise TimeoutError("The visible saved-version count is unavailable.")


async def _observed_curation(
    observations: dict[str, object],
    source_id: str,
    *,
    minimum_history: int,
    current_not: str | None = None,
) -> dict[str, object]:
    for _ in range(300):
        curations = observations.get("curations")
        if isinstance(curations, dict):
            value = curations.get(source_id)
            if isinstance(value, dict):
                history = value.get("history")
                current = value.get("current")
                current_id = current.get("id") if isinstance(current, dict) else None
                if (
                    isinstance(history, list)
                    and len(history) >= minimum_history
                    and (current_not is None or current_id != current_not)
                ):
                    return value
        await asyncio.sleep(0.1)
    raise TimeoutError("The exact owner-scoped operation curation was not observed.")


def _selection(value: dict[str, object]) -> tuple[set[str], set[str]]:
    current = value.get("current")
    if not isinstance(current, dict):
        return set(), set()
    return (
        {str(item) for item in current.get("included_operation_ids", [])},
        {str(item) for item in current.get("excluded_operation_ids", [])},
    )


async def _selected_conversation_id(page: Page) -> str:
    value = await page.evaluate(
        "() => sessionStorage.getItem('corpus.selected-conversation.v1')"
    )
    if not isinstance(value, str) or not value:
        raise RuntimeError("The authenticated Corpus conversation identity is unavailable.")
    return value


def _concurrent_entry_url(primary_url: str, configured_url: str) -> str:
    primary = urlsplit(primary_url)
    configured = urlsplit(configured_url)
    if (primary.scheme, primary.netloc) != (configured.scheme, configured.netloc):
        raise RuntimeError("The concurrent page cannot leave the configured Corpus origin.")
    if primary.path in {"", "/"} or not parse_qs(primary.query).get("resume_handle"):
        raise RuntimeError(
            "The primary Sources conversation has no exact session-bound entry URL."
        )
    return primary_url


async def _capture_group(
    page: Page,
    surface,
    targets,
    width: int,
    height: int,
    repository: Path,
    directory: Path,
    screenshots: list[str],
    name: str,
) -> dict[str, dict[str, float] | None]:
    await page.set_viewport_size({"width": width, "height": height})
    await surface.scroll_into_view_if_needed()
    dock = page.locator("[data-agent-surface-dock]")
    await dock.wait_for()
    bounds = {key: await locator.bounding_box() for key, locator in targets.items()}
    container = await dock.bounding_box()
    delta = _scroll_delta_for_group(bounds, container, margin=16)
    await dock.evaluate(
        "(element, value) => element.scrollBy({top: value, left: 0, behavior: 'instant'})",
        delta,
    )
    bounds = {key: await locator.bounding_box() for key, locator in targets.items()}
    if not all(_inside_viewport(value, width, height) for value in bounds.values()):
        raise RuntimeError(f"The {name} evidence is outside the viewport: {bounds}")
    await _capture(
        page,
        repository,
        directory,
        screenshots,
        name,
        full_page=False,
    )
    return bounds


def _attach_diagnostics(page: Page, page_name: str, diagnostics, trace, observations) -> None:
    response_statuses: dict[tuple[str, str], int] = {}

    async def response_event(response) -> None:
        path = urlsplit(response.url).path
        if not path.startswith("/api/"):
            return
        response_statuses[(response.request.method, path)] = response.status
        observations["sequence"] = int(observations["sequence"]) + 1
        event: dict[str, object] = {
            "sequence": observations["sequence"],
            "page": page_name,
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
                event["failureCode"] = (
                    failure.get("code") if isinstance(failure, dict) else None
                )
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
                elif (
                    len(parts) == 4
                    and parts[:2] == ["api", "sources"]
                    and parts[3] == "operation-curation"
                    and isinstance(body, dict)
                ):
                    observations["curations"][parts[2]] = _safe_curation(body)
            except Exception:
                pass
        trace.append(event)
        if response.status >= 400:
            item = {
                "page": page_name,
                "status": response.status,
                "method": response.request.method,
                "path": path,
                "operationId": event.get("operationId"),
                "failureCode": event.get("failureCode"),
            }
            key = (
                "expectedBusinessFailures"
                if _is_expected_stale_failure(item)
                else "httpErrors"
            )
            diagnostics[key].append(item)

    page.on("response", response_event)

    def console_event(message) -> None:
        if message.type not in {"warning", "error"}:
            return
        location = message.location or {}
        diagnostics["consoleErrors"].append(
            {
                "type": message.type,
                "page": page_name,
                "text": message.text[:500],
                "locationPath": urlsplit(str(location.get("url", ""))).path,
            }
        )

    page.on("console", console_event)
    page.on(
        "pageerror",
        lambda exception: diagnostics["pageErrors"].append(
            {"message": str(exception)[:500]}
        ),
    )

    def request_failed(request) -> None:
        item = {
            "method": request.method,
            "path": urlsplit(request.url).path,
            "failure": request.failure,
        }
        key = (
            "expectedAbortedRequests"
            if is_expected_aborted_request(item, response_statuses)
            else "requestFailures"
        )
        diagnostics[key].append(item)

    page.on("requestfailed", request_failed)


def _safe_curation(body: dict[str, object]) -> dict[str, object]:
    operations = body.get("operations")
    history = body.get("history")
    current = body.get("current")
    return {
        "source_id": body.get("source_id"),
        "source_revision_id": body.get("source_revision_id"),
        "artifact_revision_id": body.get("artifact_revision_id"),
        "inventory_fingerprint": body.get("inventory_fingerprint"),
        "operations": [
            {
                key: item.get(key)
                for key in (
                    "operation_id",
                    "graph_node_id",
                    "method",
                    "path_template",
                    "operation_class",
                )
            }
            for item in operations
            if isinstance(item, dict)
        ]
        if isinstance(operations, list)
        else [],
        "current": _safe_record(current),
        "history": [
            _safe_record(item) for item in history if isinstance(item, dict)
        ]
        if isinstance(history, list)
        else [],
    }


def _safe_record(value: object) -> dict[str, object] | None:
    if not isinstance(value, dict):
        return None
    return {
        key: value.get(key)
        for key in (
            "id",
            "source_id",
            "source_revision_id",
            "artifact_revision_id",
            "inventory_fingerprint",
            "included_operation_ids",
            "excluded_operation_ids",
            "selected_at",
            "previous_curation_id",
        )
    }


def _is_expected_stale_failure(item: dict[str, object]) -> bool:
    return (
        item.get("status") == 409
        and item.get("method") == "POST"
        and str(item.get("path", "")).endswith("/dispatch")
        and item.get("operationId") == "sources.save_api_operation_curation"
        and item.get("failureCode") == "api_operation_curation_selection_stale"
    )


def _classify_expected_console_errors(diagnostics) -> None:
    remaining_by_page: dict[str, int] = {}
    for item in diagnostics["expectedBusinessFailures"]:
        page_name = str(item.get("page", ""))
        remaining_by_page[page_name] = remaining_by_page.get(page_name, 0) + 1
    retained: list[dict[str, object]] = []
    for item in diagnostics["consoleErrors"]:
        page_name = str(item.get("page", ""))
        if (
            remaining_by_page.get(page_name, 0) > 0
            and "Failed to load resource" in str(item.get("text", ""))
            and "409" in str(item.get("text", ""))
            and str(item.get("locationPath", "")).endswith("/dispatch")
        ):
            remaining_by_page[page_name] -= 1
            continue
        retained.append(item)
    diagnostics["consoleErrors"] = retained


def _assemble_video(
    *,
    repository: Path,
    directory: Path,
    primary: Path,
    secondary: Path,
    race_start: float,
    race_end: float,
) -> tuple[str | None, dict[str, object]]:
    output = directory / "api-operation-curation-continuous.webm"
    manifest_path = directory / "video-assembly.json"
    ffmpeg = shutil.which("ffmpeg")
    manifest: dict[str, object] = {
        "status": "failed",
        "primaryRaceStartSeconds": race_start,
        "primaryRaceEndSeconds": race_end,
        "primaryRaw": str(primary.relative_to(repository)),
        "concurrentConversationRaw": str(secondary.relative_to(repository)),
        "output": str(output.relative_to(repository)),
        "command": None,
        "error": None,
    }
    try:
        if ffmpeg is None:
            raise RuntimeError("ffmpeg is required for chronological video evidence.")
        command = chronological_ffmpeg_command(
            ffmpeg, primary, secondary, output, race_start, race_end
        )
        manifest["command"] = command
        completed = subprocess.run(
            command,
            cwd=repository,
            check=True,
            capture_output=True,
            text=True,
        )
        if not output.is_file() or output.stat().st_size == 0:
            raise RuntimeError("ffmpeg did not produce the chronological video.")
        manifest["status"] = "passed"
        manifest["stderrTail"] = completed.stderr[-2000:]
    except Exception as caught:
        manifest["error"] = f"{type(caught).__name__}: {caught}"
    manifest_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    return (
        str(output.relative_to(repository)) if manifest["status"] == "passed" else None,
        manifest,
    )


if __name__ == "__main__":
    asyncio.run(main())
