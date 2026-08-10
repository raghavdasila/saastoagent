from __future__ import annotations

import argparse
import asyncio
import hashlib
import json
import re
import subprocess
import sys
import time
from collections import Counter
from datetime import UTC, datetime
from pathlib import Path
from uuid import uuid4

from playwright.async_api import Page, async_playwright

REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
if str(REPOSITORY_ROOT) not in sys.path:
    sys.path.insert(0, str(REPOSITORY_ROOT))

from scripts.run_api_connection_check_journey import (
    MEDUSA_ENV,
    _load_required_value,
    _publish_evidence,
)
from scripts.run_api_contract_revision_journey import (
    EXPECTED_RAW,
    _capture,
    _record,
    _register,
    _source_hub,
    _wait_ready,
)
from scripts.run_api_operation_curation_journey import (
    _capture_group,
    _concurrent_entry_url,
    _selected_conversation_id,
)
from scripts.run_api_route_planning_journey import (
    _create_plan,
    _new_conversation,
)
from scripts.run_api_routed_execution_journey import (
    EXPECTED_PHASE_OPERATIONS,
    MEDUSA_SPEC,
    READ_OPERATION,
    WRITE_OPERATION,
    _attach_diagnostics,
    _attach_execution_observer,
    _attach_plan_response_observer,
    _executions,
    _latest_execution_query_sequence,
    _latest_plan_response_sequence,
    _observed_operations,
    _open_planner,
    _open_sources,
    _plan_binding,
    _provision_api_source,
    _require_single_step,
    _routed_review,
    _routed_review_id,
    _save_curation,
    _video_duration_seconds,
    _wait_created_plan,
    _wait_execution_query,
    _wait_for_restored_conversation,
)


EXPECTED_ASSERTION_COUNT = 9
STALE_MESSAGE = (
    "The exact route plan changed before approval. No API request was sent."
)


async def main() -> None:
    parser = argparse.ArgumentParser(
        description="Record a non-executing stale routed write and isolation supplement."
    )
    parser.add_argument("--url", default="http://127.0.0.1:5199")
    parser.add_argument("--backend-url", default="http://127.0.0.1:8099")
    parser.add_argument("--headed", action="store_true")
    args = parser.parse_args()
    if (
        not MEDUSA_SPEC.is_file()
        or hashlib.sha256(MEDUSA_SPEC.read_bytes()).hexdigest() != EXPECTED_RAW
    ):
        raise SystemExit("The exact reviewed Medusa Source is unavailable.")

    medusa_key = _load_required_value(MEDUSA_ENV, "MEDUSA_PUBLISHABLE_KEY")
    repository = REPOSITORY_ROOT
    run_id = (
        f"{datetime.now(UTC).strftime('%Y%m%dT%H%M%SZ')}-{uuid4().hex[:10]}"
    )
    directory = repository / "artifacts" / "api-routed-execution-stale-supplement" / run_id
    cart_count_before = await asyncio.to_thread(_medusa_cart_count)
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
        "expectedHttpOutcomes": [],
        "expectedConsoleErrors": [],
    }
    observations: dict[str, object] = {
        "sequence": 0,
        "sourceInventory": [],
        "sourceInventoryVersion": 0,
        "currentSources": {},
        "contractProposals": {},
        "profiles": {},
        "curations": {},
        "plans": [],
        "planResponses": [],
        "executions": {},
        "executionQueries": [],
        "publicForbiddenFields": [],
    }
    ids: dict[str, str] = {}
    owner = {
        "display_name": "API Routed Stale Evidence Owner",
        "email": f"api-routed-stale-{uuid4().hex}@example.com",
        "password": f"Corpus-Routed-Stale-{uuid4().hex}!8",
    }
    other_owner = {
        "display_name": "API Routed Stale Isolation Owner",
        "email": f"api-routed-stale-isolation-{uuid4().hex}@example.com",
        "password": f"Corpus-Routed-Stale-Isolation-{uuid4().hex}!8",
    }
    error: str | None = None
    primary_video_path: str | None = None
    race_video_path: str | None = None
    race_window: dict[str, float] | None = None
    phase_trace_start = 0
    primary: Page | None = None
    race_page: Page | None = None

    async with async_playwright() as playwright:
        browser = await playwright.chromium.launch(headless=not args.headed)
        context = await browser.new_context(
            viewport={"width": 1440, "height": 1000},
            record_video_dir=directory / "raw-video",
            record_video_size={"width": 1440, "height": 1000},
        )
        primary = await context.new_page()
        _attach_diagnostics(primary, "primary", diagnostics, safe_trace, observations)
        _attach_execution_observer(primary, "primary", observations)
        _attach_plan_response_observer(primary, "primary", observations)
        video_clock = time.monotonic()
        try:
            await _register(primary, args.url, owner)
            phase_trace_start = len(safe_trace)
            ids["setupConversationId"] = await _selected_conversation_id(primary)
            await _provision_api_source(
                primary,
                observations,
                assertions,
                ids,
                medusa_key,
                safe_trace,
                diagnostics,
            )
            curation = await _save_curation(
                primary,
                observations,
                ids,
                included={WRITE_OPERATION},
                minimum_history=1,
            )
            ids["writeCurationId"] = str(curation["current"]["id"])
            ids["curationId"] = ids["writeCurationId"]
            planner = await _open_planner(primary, ids)
            plan_sequence = _latest_plan_response_sequence(observations)
            await _create_plan(planner, request_text="create a cart")
            plan = await _wait_created_plan(
                primary,
                observations,
                page_name="primary",
                conversation_id=ids["setupConversationId"],
                after_sequence=plan_sequence,
                excluded_plan_ids=set(),
                operation_id=WRITE_OPERATION,
                method="POST",
                path_template="/store/carts",
                safety="write",
                state="ready",
            )
            ids["stalePlanId"] = str(plan["plan_id"])
            _require_single_step(plan, WRITE_OPERATION, "write")
            plan_binding = _plan_binding(plan, ids, ids["writeCurationId"])
            _require_cart_count(cart_count_before)
            _record(
                assertions,
                "one exact PostCarts plan is staged for review without execution",
                plan_binding["matches"] and not _executions(observations),
                {
                    "planBinding": plan_binding,
                    "httpCallCount": 0,
                    "cartCount": cart_count_before,
                },
            )
            await planner.get_by_role(
                "button", name="Review routed write", exact=True
            ).click()
            review = _routed_review(primary)
            await review.get_by_role(
                "heading", name="Send this routed API write?", exact=True
            ).wait_for(timeout=30_000)
            ids["staleReviewId"] = await _routed_review_id(review)

            race_page = await context.new_page()
            _attach_diagnostics(
                race_page, "curation-race", diagnostics, safe_trace, observations
            )
            _attach_execution_observer(race_page, "curation-race", observations)
            _attach_plan_response_observer(race_page, "curation-race", observations)
            race_start = round(time.monotonic() - video_clock, 3)
            await race_page.goto(_concurrent_entry_url(primary.url, args.url))
            await _wait_for_restored_conversation(
                race_page,
                ids["setupConversationId"],
            )
            ids["raceConversationId"] = await _new_conversation(race_page)
            await _open_sources(race_page)
            advanced = await _save_curation(
                race_page,
                observations,
                ids,
                included={READ_OPERATION},
                minimum_history=2,
                current_not=ids["writeCurationId"],
            )
            ids["staleCurationId"] = str(advanced["current"]["id"])
            race_end = round(time.monotonic() - video_clock, 3)
            race_window = {
                "startSeconds": race_start,
                "endSeconds": race_end,
            }
            _require_cart_count(cart_count_before)
            _record(
                assertions,
                "a second conversation advances curation without executing the staged write",
                ids["staleCurationId"] != ids["writeCurationId"]
                and not _executions(observations),
                {
                    "raceConversationId": ids["raceConversationId"],
                    "priorCurationId": ids["writeCurationId"],
                    "staleCurationId": ids["staleCurationId"],
                    "httpCallCount": 0,
                    "cartCount": cart_count_before,
                },
            )
            race_video = race_page.video
            await race_page.close()
            if race_video is not None:
                raw = Path(await race_video.path())
                final = directory / "api-routed-stale-curation-race.webm"
                raw.replace(final)
                race_video_path = str(final.relative_to(repository))
            race_page = None

            query_sequence = _latest_execution_query_sequence(observations)
            await review.get_by_role(
                "button", name="Accept and send one write", exact=True
            ).click()
            await _wait_for_stale_review_failure(
                safe_trace,
                ids["staleReviewId"],
            )
            stale_query = await _wait_execution_query(
                observations,
                ids["stalePlanId"],
                after_sequence=query_sequence,
                has_result=False,
            )
            await review.wait_for(state="detached", timeout=30_000)
            planner = _open_planner_surface(primary)
            planner_failure = planner.locator("section.api-routed-execution")
            alert = _planner_failure_alert(planner_failure)
            await alert.wait_for(timeout=30_000)
            if (await alert.inner_text()).strip() != STALE_MESSAGE:
                raise RuntimeError("The planner-owned stale failure copy is not exact.")
            _require_cart_count(cart_count_before)
            desktop_bounds = await _capture_planner_failure(
                primary,
                planner_failure,
                repository,
                directory,
                screenshots,
                "01-stale-write-failure-desktop",
                width=1440,
                height=1000,
            )
            _record(
                assertions,
                "stale acceptance fails visibly with no execution result or target call",
                stale_query.get("status") == 200
                and stale_query.get("hasResult") is False
                and _review_stale_seen(safe_trace, ids["staleReviewId"])
                and not _executions(observations),
                {
                    "planId": ids["stalePlanId"],
                    "reviewId": ids["staleReviewId"],
                    "executionQuery": stale_query,
                    "httpCallCount": 0,
                    "cartCount": cart_count_before,
                    "desktopBounds": desktop_bounds,
                },
            )
            mobile_bounds = await _capture_planner_failure(
                primary,
                planner_failure,
                repository,
                directory,
                screenshots,
                "02-stale-write-failure-mobile",
                width=390,
                height=844,
            )
            _record(
                assertions,
                "mobile viewport contains the planner-owned stale failure without Execute",
                await primary.get_by_role(
                    "button", name="Execute", exact=True
                ).count()
                == 0,
                {
                    "viewport": [390, 844],
                    "executeControls": 0,
                    "bounds": mobile_bounds,
                },
            )

            restart_sequence = _latest_execution_query_sequence(observations)
            subprocess.run(
                ["docker", "compose", "restart", "backend"],
                cwd=repository,
                check=True,
                capture_output=True,
                text=True,
            )
            await asyncio.to_thread(_wait_ready, f"{args.backend_url}/readyz")
            await primary.set_viewport_size({"width": 1440, "height": 1000})
            await primary.reload()
            planner = _open_planner_surface(primary)
            await planner.get_by_text(
                f"Plan {ids['stalePlanId']} · record {plan['record_id']}",
                exact=True,
            ).wait_for(timeout=60_000)
            restart_query = await _wait_execution_query(
                observations,
                ids["stalePlanId"],
                after_sequence=restart_sequence,
                has_result=False,
            )
            _require_cart_count(cart_count_before)
            await _capture(
                primary,
                repository,
                directory,
                screenshots,
                "03-stale-plan-zero-result-after-restart-desktop",
                full_page=True,
            )
            _record(
                assertions,
                "backend restart preserves the exact stale plan and zero-result state",
                restart_query.get("status") == 200
                and restart_query.get("hasResult") is False
                and not _executions(observations),
                {
                    "planId": ids["stalePlanId"],
                    "recordId": plan["record_id"],
                    "executionQuery": restart_query,
                    "httpCallCount": 0,
                    "cartCount": cart_count_before,
                },
            )
            _record(
                assertions,
                "the entire supplement retains zero routed target calls and zero results",
                _trace_has_zero_target_calls(safe_trace[phase_trace_start:])
                and not _executions(observations),
                {
                    "executionPlanIds": sorted(_executions(observations)),
                    "httpCallCount": 0,
                    "cartCount": cart_count_before,
                },
            )
            operations = _observed_operations(safe_trace, phase_trace_start)
            _record(
                assertions,
                "only non-executing compiled Source and stale-review operations were dispatched",
                operations <= EXPECTED_PHASE_OPERATIONS
                and "sources.test_routed_api_write" in operations
                and "sources.test_routed_api_read" not in operations,
                {"operationIds": sorted(operations)},
            )

            sign_out = primary.get_by_label("Sign out", exact=True)
            await sign_out.click()
            await primary.get_by_role(
                "heading", name="Explore Corpus", exact=True
            ).wait_for(timeout=30_000)
            await sign_out.wait_for(state="detached", timeout=30_000)
            await _register(primary, args.url, other_owner)
            other_hub = await _open_sources(primary)
            await other_hub.get_by_text(
                "No API sources yet.", exact=True
            ).wait_for(timeout=30_000)
            await _capture(
                primary,
                repository,
                directory,
                screenshots,
                "04-second-owner-empty-inventory-desktop",
                full_page=True,
            )
            _require_cart_count(cart_count_before)
            _record(
                assertions,
                "second owner cannot inspect the first owner's Source plan or result",
                await other_hub.get_by_text(
                    "Reviewed local Medusa Store", exact=True
                ).count()
                == 0
                and not _executions(observations),
                {
                    "firstOwnerSourceId": ids["sourceId"],
                    "visibleSourceCount": 0,
                    "httpCallCount": 0,
                    "cartCount": cart_count_before,
                },
            )
        except Exception as caught:
            error = f"{type(caught).__name__}: {caught}"
        finally:
            if race_page is not None:
                race_video = race_page.video
                await race_page.close()
                if race_video is not None:
                    raw = Path(await race_video.path())
                    final = directory / "api-routed-stale-curation-race.webm"
                    raw.replace(final)
                    race_video_path = str(final.relative_to(repository))
            if primary is not None:
                primary_video = primary.video
                await primary.close()
                if primary_video is not None:
                    raw = Path(await primary_video.path())
                    final = directory / "api-routed-stale-continuous.webm"
                    raw.replace(final)
                    primary_video_path = str(final.relative_to(repository))
            await context.close()
            await browser.close()

    (
        cart_count_after,
        primary_duration,
        race_duration,
        finalization_error,
    ) = await asyncio.to_thread(
        _finalize_evidence_inputs,
        repository,
        primary_video_path,
        race_video_path,
    )
    if finalization_error is not None:
        error = (
            finalization_error
            if error is None
            else f"{error}; {finalization_error}"
        )
    valid_video = (
        primary_duration is not None
        and primary_duration > 0
        and race_duration is not None
        and race_duration > 0
        and race_window is not None
        and 0
        <= race_window["startSeconds"]
        < race_window["endSeconds"]
        <= primary_duration
    )
    _classify_expected_stale_outcome(diagnostics, ids.get("staleReviewId"))
    unexpected = (
        diagnostics["httpErrors"]
        + diagnostics["consoleErrors"]
        + diagnostics["pageErrors"]
        + diagnostics["requestFailures"]
    )
    passed = (
        error is None
        and not unexpected
        and cart_count_after is not None
        and cart_count_after == cart_count_before
        and len(assertions) == EXPECTED_ASSERTION_COUNT
        and all(bool(item["passed"]) for item in assertions)
        and primary_video_path is not None
        and race_video_path is not None
        and valid_video
    )
    trace_path = directory / "corpus-trace.json"
    result_path = directory / "result.json"
    result = {
        "schema": "corpus.api-routed-execution-stale-supplement.v1",
        "runId": run_id,
        "status": "passed" if passed else "failed",
        "runtime": {
            "location": "local Docker Compose",
            "frontend": args.url,
            "backend": args.backend_url,
            "medusa": "http://127.0.0.1:9100",
            "command": ".\\.venv\\Scripts\\python.exe scripts\\run_api_routed_execution_stale_supplement_journey.py --url http://127.0.0.1:5199",
        },
        "ids": ids,
        "assertions": assertions,
        "cartCounts": {
            "before": cart_count_before,
            "after": cart_count_after,
            "delta": (
                cart_count_after - cart_count_before
                if cart_count_after is not None
                else None
            ),
        },
        "diagnostics": diagnostics,
        "screenshots": screenshots,
        "video": primary_video_path,
        "supplementalVideos": [race_video_path] if race_video_path else [],
        "raceWindow": race_window,
        "videoDurationsSeconds": {
            "primary": primary_duration,
            "curationRace": race_duration,
        },
        "trace": str(trace_path.relative_to(repository)),
        "rawPlaywrightTrace": None,
        "redaction": {
            "headers": False,
            "query": False,
            "cookies": False,
            "requestBodies": False,
            "responseBodies": False,
            "credentialValues": False,
        },
        "error": error,
        "limitations": [
            "This supplemental journey never accepts a current write and must not call the Medusa target API.",
            "The retained cart count is a read-only local PostgreSQL count; no cart ID, body, delete, or rollback is retained or performed.",
            "The primary video is continuous and the curation mutation uses one supplemental page clip with monotonic offsets.",
        ],
    }
    _publish_evidence(
        directory=directory,
        result_path=result_path,
        trace_path=trace_path,
        result_json=json.dumps(result, indent=2) + "\n",
        trace_json=json.dumps(safe_trace, indent=2) + "\n",
        secrets=(medusa_key, owner["password"], other_owner["password"]),
    )
    print(
        f"run={run_id} status={result['status']} assertions={len(assertions)} "
        f"cart_delta={cart_count_after - cart_count_before if cart_count_after is not None else 'unknown'}"
    )
    print(f"artifact={result_path}")
    print("ids=" + json.dumps(ids, sort_keys=True))
    if error is not None:
        print(f"error={error}")
    raise SystemExit(0 if passed else 1)


def _open_planner_surface(page: Page):
    return page.locator("section.api-operation-test")


def _planner_failure_alert(surface):
    return surface.get_by_role("alert").filter(
        has_text=re.compile(rf"^{re.escape(STALE_MESSAGE)}$")
    )


async def _capture_planner_failure(
    page: Page,
    surface,
    repository: Path,
    directory: Path,
    screenshots: list[str],
    name: str,
    *,
    width: int,
    height: int,
):
    return await _capture_group(
        page,
        surface,
        {
            "heading": surface.get_by_role(
                "heading", name="Run the selected routed operation", exact=True
            ),
            "operation": surface.get_by_text(
                "POST /store/carts · no automatic retry", exact=True
            ),
            "failure": _planner_failure_alert(surface),
        },
        width,
        height,
        repository,
        directory,
        screenshots,
        name,
    )


async def _wait_for_stale_review_failure(
    trace: list[dict[str, object]],
    review_id: str,
) -> None:
    for _ in range(300):
        if _review_stale_seen(trace, review_id):
            return
        await asyncio.sleep(0.1)
    raise TimeoutError("The exact stale review failure was not observed.")


def _review_stale_seen(trace: list[dict[str, object]], review_id: str) -> bool:
    expected_path = f"/api/routedeck/reviews/{review_id}/accept"
    return any(
        item.get("page") == "primary"
        and item.get("event") == "response"
        and item.get("method") == "POST"
        and item.get("path") == expected_path
        and item.get("status") == 409
        and item.get("operationId") == "sources.test_routed_api_write"
        and item.get("failureCode") == "review_stale"
        for item in trace
    )


def _classify_expected_stale_outcome(
    diagnostics: dict[str, list[dict[str, object]]],
    review_id: str | None,
) -> None:
    if review_id is None:
        return
    expected_path = f"/api/routedeck/reviews/{review_id}/accept"
    expected_paths: Counter[tuple[str, str]] = Counter()
    retained_http: list[dict[str, object]] = []
    for item in diagnostics["httpErrors"]:
        expected = (
            item.get("page") == "primary"
            and item.get("status") == 409
            and item.get("method") == "POST"
            and item.get("path") == expected_path
            and item.get("operationId") == "sources.test_routed_api_write"
            and item.get("failureCode") == "review_stale"
        )
        if expected:
            diagnostics["expectedHttpOutcomes"].append(item)
            expected_paths[("primary", expected_path)] += 1
        else:
            retained_http.append(item)
    diagnostics["httpErrors"] = retained_http

    retained_console: list[dict[str, object]] = []
    for item in diagnostics["consoleErrors"]:
        key = (
            str(item.get("page")),
            str(item.get("locationPath") or item.get("path") or ""),
        )
        if (
            expected_paths[key] > 0
            and "Failed to load resource" in str(item.get("text", ""))
            and "409" in str(item.get("text", ""))
        ):
            diagnostics["expectedConsoleErrors"].append(item)
            expected_paths[key] -= 1
        else:
            retained_console.append(item)
    diagnostics["consoleErrors"] = retained_console


def _finalize_evidence_inputs(
    repository: Path,
    primary_video_path: str | None,
    race_video_path: str | None,
) -> tuple[int | None, float | None, float | None, str | None]:
    failures: list[str] = []
    cart_count: int | None = None
    primary_duration: float | None = None
    race_duration: float | None = None
    try:
        cart_count = _medusa_cart_count()
    except Exception as error:
        failures.append(f"cart_count_finalization_failed:{type(error).__name__}")
    try:
        if primary_video_path is not None:
            primary_duration = _video_duration_seconds(
                repository / primary_video_path
            )
    except Exception as error:
        failures.append(f"primary_video_finalization_failed:{type(error).__name__}")
    try:
        if race_video_path is not None:
            race_duration = _video_duration_seconds(repository / race_video_path)
    except Exception as error:
        failures.append(f"race_video_finalization_failed:{type(error).__name__}")
    return (
        cart_count,
        primary_duration,
        race_duration,
        ";".join(failures) if failures else None,
    )


def _medusa_cart_count() -> int:
    completed = subprocess.run(
        [
            "docker",
            "exec",
            "routedeck-medusa-demo-postgres-1",
            "psql",
            "-U",
            "routedeck_medusa",
            "-d",
            "routedeck_medusa_demo",
            "-At",
            "-c",
            "select count(*) from cart where deleted_at is null;",
        ],
        check=True,
        capture_output=True,
        text=True,
    )
    return _cart_count_from_stdout(completed.stdout)


def _cart_count_from_stdout(value: str) -> int:
    stripped = value.strip()
    if not stripped.isdigit():
        raise RuntimeError("The read-only Medusa cart count is unavailable.")
    return int(stripped)


def _require_cart_count(expected: int) -> None:
    actual = _medusa_cart_count()
    if actual != expected:
        raise RuntimeError(
            f"The Medusa cart count changed during the non-executing supplement: "
            f"expected {expected}, observed {actual}."
        )


def _trace_has_zero_target_calls(trace: list[dict[str, object]]) -> bool:
    return all(item.get("apiCallCount") in {None, 0} for item in trace)


if __name__ == "__main__":
    asyncio.run(main())
