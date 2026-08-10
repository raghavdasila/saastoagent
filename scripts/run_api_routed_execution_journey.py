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
from urllib.parse import urlsplit
from uuid import uuid4

from playwright.async_api import Error as PlaywrightError
from playwright.async_api import Page, TimeoutError as PlaywrightTimeoutError, async_playwright

REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
if str(REPOSITORY_ROOT) not in sys.path:
    sys.path.insert(0, str(REPOSITORY_ROOT))

from scripts.run_api_connection_check_journey import (
    MEDUSA_ENV,
    _load_required_value,
    _profiles,
    _publish_evidence,
    _save_profile,
)
from scripts.run_api_contract_revision_journey import (
    EXPECTED_FINAL,
    EXPECTED_RAW,
    MEDUSA_SPEC,
    _capture,
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
from scripts.run_api_operation_curation_journey import (
    _capture_group,
    _concurrent_entry_url,
    _curation_panel,
    _observed_curation,
    _selected_conversation_id,
)
from scripts.run_api_route_planning_journey import (
    _attach_diagnostics,
    _create_plan,
    _new_conversation,
    _open_sources,
    _planner,
    _safe_plan,
    _wait_for_agent_idle,
)


READ_OPERATION = "GetProductTypes"
WRITE_OPERATION = "PostCarts"
EXPECTED_PHASE_OPERATIONS = frozenset(
    {
        "workspace.open_sources",
        "sources.open_api_creation",
        "sources.propose_contract_revision",
        "sources.approve_contract_revision",
        "sources.save_api_connection",
        "sources.save_api_operation_curation",
        "sources.prepare_routed_api_test",
        "sources.test_routed_api_read",
        "sources.test_routed_api_write",
    }
)
EXPECTED_ASSERTION_COUNT = 12


async def main() -> None:
    parser = argparse.ArgumentParser(
        description="Record one-call routed API read and reviewed write execution."
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
    run_id = f"{datetime.now(UTC).strftime('%Y%m%dT%H%M%SZ')}-{uuid4().hex[:10]}"
    directory = repository / "artifacts" / "api-routed-execution" / run_id
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
        "display_name": "API Routed Execution Evidence Owner",
        "email": f"api-routed-execution-{uuid4().hex}@example.com",
        "password": f"Corpus-Routed-Execution-{uuid4().hex}!8",
    }
    other_owner = {
        "display_name": "API Routed Execution Isolation Owner",
        "email": f"api-routed-isolation-{uuid4().hex}@example.com",
        "password": f"Corpus-Routed-Isolation-{uuid4().hex}!8",
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
            hub = await _provision_api_source(
                primary,
                observations,
                assertions,
                ids,
                medusa_key,
                safe_trace,
                diagnostics,
            )

            read_curation = await _save_curation(
                primary, observations, ids, included={READ_OPERATION}, minimum_history=1
            )
            ids["readCurationId"] = str(read_curation["current"]["id"])
            ids["curationId"] = ids["readCurationId"]
            planner = await _open_planner(primary, ids)
            read_plan_sequence = _latest_plan_response_sequence(observations)
            await _create_plan(planner, request_text="list product types")
            read_plan = await _wait_created_plan(
                primary,
                observations,
                page_name="primary",
                conversation_id=ids["setupConversationId"],
                after_sequence=read_plan_sequence,
                excluded_plan_ids=set(),
                operation_id=READ_OPERATION,
                method="GET",
                path_template="/store/product-types",
                safety="read",
                state="ready",
            )
            ids["readPlanId"] = str(read_plan["plan_id"])
            _require_single_step(read_plan, READ_OPERATION, "read")
            read_binding = _plan_binding(read_plan, ids, ids["readCurationId"])
            await planner.get_by_role("button", name="Run routed read", exact=True).click()
            read_result = await _wait_execution(observations, ids["readPlanId"])
            await _capture_execution(
                primary, planner, repository, directory, screenshots,
                "01-routed-read-result-desktop",
            )
            _record(
                assertions,
                "direct routed read uses the exact fresh plan and one validated call",
                read_binding["matches"]
                and _execution_matches(
                    read_result,
                    ids,
                    ids["readPlanId"],
                    READ_OPERATION,
                    "GET",
                    "/store/product-types",
                    "read",
                    "succeeded",
                    1,
                ),
                {"planBinding": read_binding, "result": read_result},
            )

            ids["writeRejectConversationId"] = await _new_conversation(primary)
            hub = await _open_sources(primary)
            write_curation = await _save_curation(
                primary, observations, ids, included={WRITE_OPERATION}, minimum_history=2
            )
            ids["writeCurationId"] = str(write_curation["current"]["id"])
            ids["curationId"] = ids["writeCurationId"]
            planner = await _open_planner(primary, ids)
            reject_plan_sequence = _latest_plan_response_sequence(observations)
            await _create_plan(planner, request_text="create a cart")
            reject_plan = await _wait_created_plan(
                primary,
                observations,
                page_name="primary",
                conversation_id=ids["writeRejectConversationId"],
                after_sequence=reject_plan_sequence,
                excluded_plan_ids={ids["readPlanId"]},
                operation_id=WRITE_OPERATION,
                method="POST",
                path_template="/store/carts",
                safety="write",
                state="ready",
            )
            ids["writeRejectPlanId"] = str(reject_plan["plan_id"])
            _require_single_step(reject_plan, WRITE_OPERATION, "write")
            reject_binding = _plan_binding(
                reject_plan, ids, ids["writeCurationId"]
            )
            await planner.get_by_role("button", name="Review routed write", exact=True).click()
            await primary.reload()
            review = _routed_review(primary)
            await review.get_by_role(
                "heading", name="Send this routed API write?", exact=True
            ).wait_for(timeout=60_000)
            ids["writeRejectReviewId"] = await _routed_review_id(review)
            await _capture_review(
                primary, review, repository, directory, screenshots,
                "02-routed-write-review-reloaded-desktop",
            )
            await review.get_by_role("button", name="Reject without sending", exact=True).click()
            await review.wait_for(state="detached", timeout=30_000)
            reject_query_sequence = _latest_execution_query_sequence(observations)
            await primary.reload()
            planner = _planner(primary)
            await planner.get_by_role(
                "heading", name="API operation test", exact=True
            ).wait_for(timeout=30_000)
            await planner.get_by_text(
                f"Plan {ids['writeRejectPlanId']} · record {reject_plan['record_id']}",
                exact=True,
            ).wait_for(timeout=30_000)
            reject_query = await _wait_execution_query(
                observations,
                ids["writeRejectPlanId"],
                after_sequence=reject_query_sequence,
                has_result=False,
            )
            _record(
                assertions,
                "reloaded durable write review rejects without a claim or API call",
                reject_binding["matches"]
                and reject_query.get("status") == 200
                and _review_rejection_seen(
                    safe_trace,
                    ids["writeRejectReviewId"],
                )
                and ids["writeRejectPlanId"] not in _executions(observations),
                {
                    "planBinding": reject_binding,
                    "reviewId": ids["writeRejectReviewId"],
                    "recordId": reject_plan["record_id"],
                    "authoritativeExecutionQuery": reject_query,
                    "httpCallCount": 0,
                },
            )

            ids["writeAcceptConversationId"] = await _new_conversation(primary)
            await _open_sources(primary)
            planner = await _open_planner(primary, ids)
            accept_plan_sequence = _latest_plan_response_sequence(observations)
            await _create_plan(planner, request_text="create a cart")
            accept_plan = await _wait_created_plan(
                primary,
                observations,
                page_name="primary",
                conversation_id=ids["writeAcceptConversationId"],
                after_sequence=accept_plan_sequence,
                excluded_plan_ids={
                    ids["readPlanId"],
                    ids["writeRejectPlanId"],
                },
                operation_id=WRITE_OPERATION,
                method="POST",
                path_template="/store/carts",
                safety="write",
                state="ready",
            )
            ids["writeAcceptPlanId"] = str(accept_plan["plan_id"])
            _require_single_step(accept_plan, WRITE_OPERATION, "write")
            accept_binding = _plan_binding(
                accept_plan, ids, ids["writeCurationId"]
            )
            await planner.get_by_role("button", name="Review routed write", exact=True).click()
            review = _routed_review(primary)
            await review.get_by_role(
                "heading", name="Send this routed API write?", exact=True
            ).wait_for(timeout=30_000)
            ids["writeAcceptReviewId"] = await _routed_review_id(review)
            await review.get_by_role("button", name="Accept and send one write", exact=True).click()
            accept_result = await _wait_execution(observations, ids["writeAcceptPlanId"])
            planner = _planner(primary)
            await planner.get_by_text("Routed API request succeeded", exact=True).wait_for(
                timeout=60_000
            )
            await _capture_execution(
                primary, planner, repository, directory, screenshots,
                "03-reviewed-cart-create-result-desktop",
            )
            _record(
                assertions,
                "fresh reviewed write creates one local cart with one retained call",
                accept_binding["matches"]
                and _execution_matches(
                    accept_result,
                    ids,
                    ids["writeAcceptPlanId"],
                    WRITE_OPERATION,
                    "POST",
                    "/store/carts",
                    "write",
                    "succeeded",
                    1,
                ),
                {"planBinding": accept_binding, "result": accept_result},
            )
            _record(
                assertions,
                "terminal result removes every repeat or retry control",
                await planner.get_by_role("button", name="Review routed write", exact=True).count() == 0,
                {"planId": ids["writeAcceptPlanId"], "repeatControls": 0},
            )

            subprocess.run(
                ["docker", "compose", "restart", "backend"],
                cwd=repository,
                check=True,
                capture_output=True,
                text=True,
            )
            await asyncio.to_thread(_wait_ready, f"{args.backend_url}/readyz")
            restart_query_sequence = _latest_execution_query_sequence(observations)
            _executions(observations).pop(ids["writeAcceptPlanId"], None)
            await primary.reload()
            planner = _planner(primary)
            await planner.get_by_text("Routed API request succeeded", exact=True).wait_for(
                timeout=60_000
            )
            restart_query = await _wait_execution_query(
                observations,
                ids["writeAcceptPlanId"],
                after_sequence=restart_query_sequence,
                has_result=True,
            )
            replayed = await _wait_execution(observations, ids["writeAcceptPlanId"])
            await _capture_execution(
                primary, planner, repository, directory, screenshots,
                "04-retained-result-after-restart-desktop",
            )
            _record(
                assertions,
                "backend restart replays the same immutable result without a second call",
                restart_query.get("status") == 200
                and replayed == accept_result
                and replayed.get("http_call_count") == 1,
                {
                    "planId": ids["writeAcceptPlanId"],
                    "resultId": replayed.get("result_id"),
                    "httpCallCount": 1,
                    "postRestartExecutionQuery": restart_query,
                },
            )

            ids["staleConversationId"] = await _new_conversation(primary)
            await _open_sources(primary)
            planner = await _open_planner(primary, ids)
            _record(
                assertions,
                "a distinct owner conversation does not inherit another conversation result",
                await planner.get_by_text("Routed API request succeeded", exact=True).count() == 0,
                {"conversationId": ids["staleConversationId"], "visibleRetainedResults": 0},
            )
            stale_plan_sequence = _latest_plan_response_sequence(observations)
            await _create_plan(planner, request_text="create a cart")
            stale_plan = await _wait_created_plan(
                primary,
                observations,
                page_name="primary",
                conversation_id=ids["staleConversationId"],
                after_sequence=stale_plan_sequence,
                excluded_plan_ids={
                    ids["readPlanId"],
                    ids["writeRejectPlanId"],
                    ids["writeAcceptPlanId"],
                },
                operation_id=WRITE_OPERATION,
                method="POST",
                path_template="/store/carts",
                safety="write",
                state="ready",
            )
            ids["stalePlanId"] = str(stale_plan["plan_id"])
            _require_single_step(stale_plan, WRITE_OPERATION, "write")
            stale_binding = _plan_binding(
                stale_plan, ids, ids["writeCurationId"]
            )
            await planner.get_by_role("button", name="Review routed write", exact=True).click()
            review = _routed_review(primary)
            await review.get_by_role(
                "heading", name="Send this routed API write?", exact=True
            ).wait_for(timeout=30_000)
            ids["staleReviewId"] = await _routed_review_id(review)
            race_page = await context.new_page()
            _attach_diagnostics(race_page, "curation-race", diagnostics, safe_trace, observations)
            _attach_execution_observer(race_page, "curation-race", observations)
            _attach_plan_response_observer(race_page, "curation-race", observations)
            race_start = round(time.monotonic() - video_clock, 3)
            await race_page.goto(_concurrent_entry_url(primary.url, args.url))
            await _wait_for_restored_conversation(
                race_page,
                ids["staleConversationId"],
            )
            await _new_conversation(race_page)
            await _open_sources(race_page)
            advanced = await _save_curation(
                race_page,
                observations,
                ids,
                included={WRITE_OPERATION},
                minimum_history=3,
                current_not=ids["writeCurationId"],
            )
            ids["staleCurationId"] = str(advanced["current"]["id"])
            race_end = round(time.monotonic() - video_clock, 3)
            race_window = {"startSeconds": race_start, "endSeconds": race_end}
            await review.get_by_role("button", name="Accept and send one write", exact=True).click()
            await review.get_by_role("alert").wait_for(timeout=30_000)
            _record(
                assertions,
                "accept-time stale curation is visibly blocked with zero API calls",
                stale_binding["matches"]
                and ids["stalePlanId"] not in _executions(observations)
                and _failure_seen(safe_trace, "review_stale"),
                {
                    "planBinding": stale_binding,
                    "httpCallCount": 0,
                    "failureCode": "review_stale",
                },
            )
            await _capture_review(
                primary, review, repository, directory, screenshots,
                "05-stale-write-review-blocked-desktop",
            )

            await primary.set_viewport_size({"width": 390, "height": 844})
            mobile_bounds = await _capture_review_mobile(
                primary,
                review,
                repository,
                directory,
                screenshots,
                "06-stale-write-mobile",
            )
            _record(
                assertions,
                "mobile viewport retains the routed review failure without an execute fallback",
                await primary.get_by_role("button", name="Execute", exact=True).count() == 0,
                {
                    "viewport": [390, 844],
                    "executeControls": 0,
                    "bounds": mobile_bounds,
                },
            )

            _record(
                assertions,
                "all retained execution records are exact one-step bindings with no response body",
                _all_execution_records_safe(observations, ids),
                {"executionPlanIds": sorted(_executions(observations)), "forbiddenFields": observations["publicForbiddenFields"]},
            )
            _record(
                assertions,
                "only the exact compiled Phase F operations were dispatched",
                _observed_operations(safe_trace, phase_trace_start) <= EXPECTED_PHASE_OPERATIONS,
                {"operationIds": sorted(_observed_operations(safe_trace, phase_trace_start))},
            )

            await primary.set_viewport_size({"width": 1440, "height": 1000})
            sign_out = primary.get_by_label("Sign out", exact=True)
            await sign_out.click()
            await primary.get_by_role("heading", name="Explore Corpus", exact=True).wait_for(timeout=30_000)
            await sign_out.wait_for(state="detached", timeout=30_000)
            await _register(primary, args.url, other_owner)
            other_hub = await _open_sources(primary)
            await other_hub.get_by_text("No API sources yet.", exact=True).wait_for(timeout=30_000)
            await _capture(
                primary, repository, directory, screenshots,
                "07-second-owner-empty-inventory-desktop", full_page=True,
            )
            _record(
                assertions,
                "second owner cannot inspect the first owner's plans or execution results",
                await other_hub.get_by_text("Reviewed local Medusa Store", exact=True).count() == 0,
                {"firstOwnerSourceId": ids["sourceId"], "visibleSourceCount": 0},
            )
        except Exception as caught:
            error = f"{type(caught).__name__}: {caught}"
        finally:
            if race_page is not None:
                race_video = race_page.video
                await race_page.close()
                if race_video is not None:
                    raw = Path(await race_video.path())
                    final = directory / "api-routed-execution-race.webm"
                    raw.replace(final)
                    race_video_path = str(final.relative_to(repository))
            if primary is not None:
                primary_video = primary.video
                await primary.close()
                if primary_video is not None:
                    raw = Path(await primary_video.path())
                    final = directory / "api-routed-execution-continuous.webm"
                    raw.replace(final)
                    primary_video_path = str(final.relative_to(repository))
            await context.close()
            await browser.close()

    primary_video_duration = (
        _video_duration_seconds(repository / primary_video_path)
        if primary_video_path is not None
        else None
    )
    race_video_duration = (
        _video_duration_seconds(repository / race_video_path)
        if race_video_path is not None
        else None
    )
    valid_video_chronology = (
        primary_video_duration is not None
        and primary_video_duration > 0
        and race_video_duration is not None
        and race_video_duration > 0
        and race_window is not None
        and 0 <= race_window["startSeconds"]
        < race_window["endSeconds"]
        <= primary_video_duration
    )
    _classify_expected_review_outcomes(diagnostics)
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
        and primary_video_path is not None
        and race_video_path is not None
        and valid_video_chronology
    )
    trace_path = directory / "corpus-trace.json"
    result_path = directory / "result.json"
    result = {
        "schema": "corpus.api-routed-execution-journey.v1",
        "runId": run_id,
        "status": "passed" if passed else "failed",
        "runtime": {
            "location": "local Docker Compose",
            "frontend": args.url,
            "backend": args.backend_url,
            "medusa": "http://127.0.0.1:9100",
            "command": ".\\.venv\\Scripts\\python.exe scripts\\run_api_routed_execution_journey.py --url http://127.0.0.1:5199",
        },
        "ids": ids,
        "assertions": assertions,
        "diagnostics": diagnostics,
        "screenshots": screenshots,
        "video": primary_video_path,
        "supplementalVideos": [race_video_path] if race_video_path else [],
        "raceWindow": race_window,
        "videoDurationsSeconds": {
            "primary": primary_video_duration,
            "curationRace": race_video_duration,
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
            "Exactly one reviewed local Medusa cart creation is intentionally retained; no rollback or delete is attempted.",
            "The deterministic unknown/POSSIBLY_SENT transport path is covered by adapter and SQL tests only; this recorder never induces or retries an ambiguous real write.",
            "The primary video is continuous; the concurrent curation mutation is retained as a supplemental page clip and monotonic offsets from primary recording start.",
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
    print(f"run={run_id} status={result['status']} assertions={len(assertions)}")
    print(f"artifact={result_path}")
    print("ids=" + json.dumps(ids, sort_keys=True))
    if error is not None:
        print(f"error={error}")
    raise SystemExit(0 if passed else 1)


async def _provision_api_source(
    page,
    observations,
    assertions,
    ids,
    medusa_key,
    safe_trace,
    diagnostics,
):
    hub = await _open_sources(page)
    await _upload(page, hub)
    await hub.get_by_text("ready", exact=True).first.wait_for(timeout=180_000)
    ids.update(await _source_ids(page, observations))
    _record(
        assertions,
        "fresh Source processing publishes a coherent ready inventory",
        not any(
            item.get("status") == 500
            and item.get("method") == "GET"
            and item.get("path") == "/api/sources"
            for item in diagnostics["httpErrors"]
        ),
        {
            "sourceId": ids["sourceId"],
            "parentRevisionId": ids["parentRevisionId"],
            "jobId": ids.get("jobId"),
            "inventory500Count": sum(
                1
                for item in diagnostics["httpErrors"]
                if item.get("status") == 500
                and item.get("method") == "GET"
                and item.get("path") == "/api/sources"
            ),
        },
    )
    await hub.get_by_role("button", name="Prepare contract revision", exact=True).click()
    proposal = _proposal_panel(page)
    await proposal.get_by_role("heading", name="API contract revision proposal", exact=True).wait_for(timeout=90_000)
    proposals = await _observed_proposals(observations, ids["sourceId"])
    ids["proposalId"] = str(proposals[0]["proposal_id"])
    await proposal.get_by_role("button", name="Review this revision", exact=True).click()
    review = _review_surface(page)
    await review.get_by_role("heading", name="Create this immutable API contract revision?", exact=True).wait_for(timeout=30_000)
    ids["contractReviewId"] = await _latest_review_id(safe_trace)
    await review.get_by_role("button", name="Accept and create new revision", exact=True).click()
    await hub.get_by_text("Reviewed contract revision", exact=True).wait_for(timeout=60_000)
    current = await _observed_current_source(observations, ids["sourceId"], excluding_revision_id=ids["parentRevisionId"])
    ids["approvedRevisionId"] = str(current["revision"]["revision_id"])
    if current["revision"]["summary"].get("final_canonical_sha256") != EXPECTED_FINAL:
        raise RuntimeError("The approved Source is not the exact 6fca contract.")
    connection = hub.locator("section.api-connection-panel")
    await connection.get_by_role("heading", name="API connections", exact=True).wait_for(timeout=30_000)
    await _save_profile(connection, "Local Medusa routed execution", medusa_key)
    profiles = await _profiles(observations, ids["sourceId"], minimum_count=1)
    profile = next(item for item in profiles if item.get("profile_name") == "Local Medusa routed execution")
    ids["profileId"] = str(profile["id"])
    return hub


async def _save_curation(
    page,
    observations,
    ids,
    *,
    included: set[str],
    minimum_history: int,
    current_not: str | None = None,
):
    panel = _curation_panel(page)
    await panel.get_by_role("heading", name="API operation curation", exact=True).wait_for(timeout=30_000)
    operation_ids = await _observed_operation_ids(observations, ids["sourceId"])
    await _classify_curation(panel, operation_ids, included)
    await panel.get_by_role("button", name="Save operation selection", exact=True).click()
    value = await _observed_curation(
        observations,
        ids["sourceId"],
        minimum_history=minimum_history,
        current_not=current_not,
    )
    await panel.get_by_text(re.compile(r"Saved \d+ included and \d+ excluded operations"), exact=False).wait_for(timeout=30_000)
    current = value.get("current") if isinstance(value, dict) else None
    actual_included = {
        str(item)
        for item in (
            current.get("included_operation_ids", [])
            if isinstance(current, dict)
            else []
        )
    }
    actual_excluded = {
        str(item)
        for item in (
            current.get("excluded_operation_ids", [])
            if isinstance(current, dict)
            else []
        )
    }
    if actual_included != included or actual_included | actual_excluded != operation_ids:
        raise RuntimeError(
            "The persisted curation does not match the exact exhaustive Phase F selection."
        )
    return value


async def _observed_operation_ids(observations, source_id: str) -> set[str]:
    for _ in range(300):
        curations = observations.get("curations")
        value = curations.get(source_id) if isinstance(curations, dict) else None
        operations = value.get("operations") if isinstance(value, dict) else None
        if isinstance(operations, list) and operations:
            operation_ids = {
                str(item["operation_id"])
                for item in operations
                if isinstance(item, dict) and item.get("operation_id")
            }
            if len(operation_ids) != len(operations):
                raise RuntimeError("The curation inventory has missing or duplicate operation IDs.")
            return operation_ids
        await asyncio.sleep(0.1)
    raise TimeoutError("The exact operation curation inventory was not observed.")


async def _classify_curation(
    panel,
    operation_ids: set[str],
    included: set[str],
) -> None:
    missing = included - operation_ids
    if missing:
        raise RuntimeError(
            "The requested exact curation operations are absent: "
            + ", ".join(sorted(missing))
        )
    for operation_id in sorted(operation_ids):
        group = panel.get_by_role(
            "group",
            name=f"Availability for {operation_id}",
            exact=True,
        )
        decision = "Include" if operation_id in included else "Exclude"
        await group.get_by_role("radio", name=decision, exact=True).click()
    await panel.get_by_text(
        "Every discovered operation is explicitly classified.", exact=True
    ).wait_for(timeout=30_000)


async def _open_planner(page, ids):
    hub = _source_hub(page)
    await hub.get_by_role("button", name="Plan routed operation", exact=True).click()
    panel = _planner(page)
    await panel.get_by_role("heading", name="API operation test", exact=True).wait_for(timeout=30_000)
    await _bind_phase_f_planner_context(panel, ids, expected_included=1)
    return panel


def _is_detachment_error(error: BaseException) -> bool:
    message = str(error).casefold()
    return any(
        marker in message
        for marker in ("not attached", "detached from", "element was detached")
    )


async def _bind_phase_f_planner_context(
    panel,
    ids: dict[str, object],
    *,
    expected_included: int,
) -> None:
    source = panel.get_by_label("Effective API revision", exact=True)
    await _select_exact_when_ready(
        source,
        str(ids["sourceId"]),
        label="approved Source revision",
    )

    profile = panel.get_by_label("Saved connection profile", exact=True)
    await _select_exact_when_ready(
        profile,
        str(ids["profileId"]),
        label="saved connection profile",
    )

    await panel.get_by_text(
        f"Current curation {ids['curationId']} · included {expected_included}",
        exact=True,
    ).wait_for(timeout=30_000)


async def _select_exact_when_ready(
    select,
    expected_value: str,
    *,
    label: str,
    timeout_ms: int = 30_000,
) -> None:
    deadline = asyncio.get_running_loop().time() + timeout_ms / 1000
    last_error: BaseException | None = None
    while asyncio.get_running_loop().time() < deadline:
        try:
            ready = (
                await select.is_visible()
                and await select.is_enabled()
                and await select.evaluate(
                    "(element, expected) => Array.from(element.options).some((option) => option.value === expected)",
                    expected_value,
                )
            )
            if ready:
                remaining_ms = max(
                    1,
                    int((deadline - asyncio.get_running_loop().time()) * 1000),
                )
                try:
                    await select.select_option(
                        expected_value,
                        timeout=min(1_500, remaining_ms),
                    )
                except PlaywrightTimeoutError as error:
                    last_error = error
                except PlaywrightError as error:
                    if not _is_detachment_error(error):
                        raise
                    last_error = error
                else:
                    if await select.input_value() == expected_value:
                        return
        except PlaywrightTimeoutError as error:
            last_error = error
        except PlaywrightError as error:
            if not _is_detachment_error(error):
                raise
            last_error = error
        await asyncio.sleep(0.05)
    raise TimeoutError(
        f"The exact {label} option was not visible, enabled, present, and "
        "selected before the bounded deadline."
    ) from last_error


async def _wait_for_restored_conversation(
    page: Page,
    expected_conversation_id: str,
    *,
    timeout_ms: int = 30_000,
) -> None:
    try:
        await page.wait_for_function(
            "([key, expected]) => sessionStorage.getItem(key) === expected",
            arg=["corpus.selected-conversation.v1", expected_conversation_id],
            timeout=timeout_ms,
        )
    except PlaywrightTimeoutError as error:
        observed = await page.evaluate(
            "() => sessionStorage.getItem('corpus.selected-conversation.v1')"
        )
        if observed is None:
            raise TimeoutError(
                "The supplemental tab conversation was not restored."
            ) from error
        raise RuntimeError(
            "The supplemental tab restored the wrong conversation."
        ) from error

    await _wait_for_agent_idle(page)
    observed = await page.evaluate(
        "() => sessionStorage.getItem('corpus.selected-conversation.v1')"
    )
    if observed is None:
        raise TimeoutError(
            "The supplemental tab conversation disappeared before it became idle."
        )
    if observed != expected_conversation_id:
        raise RuntimeError(
            "The supplemental tab conversation changed before it became idle."
        )


def _routed_review(page: Page):
    return page.locator("section.routed-api-write-review")


async def _routed_review_id(review) -> str:
    labelled_by = await review.get_attribute("aria-labelledby")
    match = re.fullmatch(r"routed-write-review-(review_[A-Za-z0-9_-]+)", labelled_by or "")
    if match is None:
        raise RuntimeError("The exact routed write review ID is unavailable from its surface.")
    return match.group(1)


async def _capture_execution(page, panel, repository, directory, screenshots, name):
    result = panel.locator("article.api-routed-result")
    return await _capture_group(
        page, result,
        {
            "status": result.locator("strong"),
            "delivery": result.locator("dl > div", has_text="Delivery"),
            "calls": result.locator("dl > div", has_text="HTTP calls"),
        },
        1440, 1000, repository, directory, screenshots, name,
    )


async def _capture_review(page, review, repository, directory, screenshots, name):
    return await _capture_group(
        page, review,
        {
            "heading": review.get_by_role("heading", name="Send this routed API write?", exact=True),
            "accept": review.get_by_role("button", name="Accept and send one write", exact=True),
            "reject": review.get_by_role("button", name="Reject without sending", exact=True),
        },
        1440, 1000, repository, directory, screenshots, name,
    )


async def _capture_review_mobile(page, review, repository, directory, screenshots, name):
    return await _capture_group(
        page,
        review,
        {
            "heading": review.get_by_role(
                "heading", name="Send this routed API write?", exact=True
            ),
            "failure": review.get_by_role("alert"),
            "accept": review.get_by_role(
                "button", name="Accept and send one write", exact=True
            ),
            "reject": review.get_by_role(
                "button", name="Reject without sending", exact=True
            ),
        },
        390,
        844,
        repository,
        directory,
        screenshots,
        name,
    )


def _attach_plan_response_observer(
    page: Page,
    page_name: str,
    observations: dict[str, object],
) -> None:
    async def response_event(response) -> None:
        path = urlsplit(response.url).path
        if (
            response.request.method != "POST"
            or response.status != 201
            or re.fullmatch(r"/api/sources/[^/]+/route-plans", path) is None
        ):
            return
        try:
            body = await response.json()
        except Exception:
            return
        if not isinstance(body, dict) or not body.get("plan_id"):
            return
        responses = observations.get("planResponses")
        if isinstance(responses, list):
            responses.append(
                {
                    "sequence": len(responses) + 1,
                    "page": page_name,
                    "path": path,
                    "plan": _safe_plan(body),
                }
            )

    page.on("response", response_event)


def _latest_plan_response_sequence(observations) -> int:
    responses = observations.get("planResponses")
    if not isinstance(responses, list) or not responses:
        return 0
    return int(responses[-1]["sequence"])


def _select_created_plan_response(
    responses,
    *,
    page_name: str,
    after_sequence: int,
    excluded_plan_ids: set[str],
    operation_id: str,
    method: str,
    path_template: str,
    safety: str,
    state: str,
):
    matches = []
    for item in responses if isinstance(responses, list) else []:
        plan = item.get("plan") if isinstance(item, dict) else None
        steps = plan.get("steps") if isinstance(plan, dict) else None
        step = steps[0] if isinstance(steps, list) and len(steps) == 1 else None
        if (
            isinstance(plan, dict)
            and isinstance(step, dict)
            and int(item.get("sequence", 0)) > after_sequence
            and item.get("page") == page_name
            and plan.get("plan_id") not in excluded_plan_ids
            and plan.get("state") == state
            and step.get("selected_operation_id") == operation_id
            and step.get("method") == method
            and step.get("path_template") == path_template
            and step.get("http_safety") == safety
        ):
            matches.append((int(item["sequence"]), plan))
    if len(matches) > 1:
        raise RuntimeError("More than one exact route-plan creation response matched.")
    return matches[0][1] if matches else None


async def _wait_created_plan(
    page: Page,
    observations,
    *,
    page_name: str,
    conversation_id: str,
    after_sequence: int,
    excluded_plan_ids: set[str],
    operation_id: str,
    method: str,
    path_template: str,
    safety: str,
    state: str,
):
    for _ in range(300):
        plan = _select_created_plan_response(
            observations.get("planResponses"),
            page_name=page_name,
            after_sequence=after_sequence,
            excluded_plan_ids=excluded_plan_ids,
            operation_id=operation_id,
            method=method,
            path_template=path_template,
            safety=safety,
            state=state,
        )
        if plan is not None:
            current_conversation_id = await _selected_conversation_id(page)
            if current_conversation_id != conversation_id:
                raise RuntimeError(
                    "The route-plan creation response crossed its initiating conversation."
                )
            return {**plan, "observed_conversation_id": conversation_id}
        await asyncio.sleep(0.1)
    raise TimeoutError(
        "The exact page- and conversation-bound route-plan creation response was not observed."
    )


def _attach_execution_observer(
    page: Page,
    page_name: str,
    observations: dict[str, object],
) -> None:
    async def response_event(response) -> None:
        path = urlsplit(response.url).path
        match = re.fullmatch(
            r"/api/sources/[^/]+/route-plans/([^/]+)/execution", path
        )
        if match is None:
            return
        try:
            body = await response.json()
        except Exception:
            body = None
        queries = observations.get("executionQueries")
        if isinstance(queries, list):
            queries.append(
                {
                    "sequence": len(queries) + 1,
                    "page": page_name,
                    "planId": match.group(1),
                    "status": response.status,
                    "hasResult": isinstance(body, dict) and bool(body.get("plan_id")),
                }
            )
        if response.status >= 400:
            return
        if not isinstance(body, dict) or not body.get("plan_id"):
            return
        safe = _safe_execution(body)
        executions = observations.get("executions")
        if isinstance(executions, dict):
            executions[str(safe["plan_id"])] = safe

    page.on("response", response_event)


def _safe_execution(value: dict[str, object]) -> dict[str, object]:
    allowed = {
        "result_id", "plan_id", "source_id", "source_revision_id", "operation_id",
        "method", "path_template", "safety", "status", "delivery", "status_code",
        "response_media_type", "response_byte_count", "response_body_sha256",
        "error_code", "public_message", "validation_issue_count", "validation_phases",
        "outcome_verified", "http_call_count", "started_at", "finished_at",
    }
    return {key: value.get(key) for key in sorted(allowed)}


def _executions(observations) -> dict[str, dict[str, object]]:
    value = observations.get("executions")
    return value if isinstance(value, dict) else {}


async def _wait_execution(observations, plan_id: str) -> dict[str, object]:
    for _ in range(300):
        value = _executions(observations).get(plan_id)
        if isinstance(value, dict):
            return value
        await asyncio.sleep(0.1)
    raise TimeoutError(f"The redacted execution result for {plan_id} was not observed.")


def _latest_execution_query_sequence(observations) -> int:
    queries = observations.get("executionQueries")
    if not isinstance(queries, list) or not queries:
        return 0
    return int(queries[-1]["sequence"])


async def _wait_execution_query(
    observations,
    plan_id: str,
    *,
    after_sequence: int,
    has_result: bool,
) -> dict[str, object]:
    for _ in range(300):
        queries = observations.get("executionQueries")
        if isinstance(queries, list):
            for item in queries:
                if (
                    int(item.get("sequence", 0)) > after_sequence
                    and item.get("page") == "primary"
                    and item.get("planId") == plan_id
                    and item.get("hasResult") is has_result
                ):
                    return item
        await asyncio.sleep(0.1)
    raise TimeoutError(
        f"No fresh authoritative execution response was observed for {plan_id}."
    )


def _plan_binding(plan, ids, curation_id: str) -> dict[str, object]:
    expected = {
        "source_id": ids.get("sourceId"),
        "source_revision_id": ids.get("approvedRevisionId"),
        "profile_id": ids.get("profileId"),
        "curation_id": curation_id,
    }
    actual = {key: plan.get(key) for key in expected}
    return {"matches": actual == expected, "expected": expected, "actual": actual}


def _require_single_step(plan, operation_id: str, safety: str) -> None:
    steps = plan.get("steps")
    if not isinstance(steps, list) or len(steps) != 1:
        raise RuntimeError("The route plan is not an exact single operation.")
    step = steps[0]
    if not isinstance(step, dict) or step.get("selected_operation_id") != operation_id or step.get("http_safety") != safety:
        raise RuntimeError("The route plan selected an unexpected operation or safety class.")


def _execution_matches(
    result,
    ids,
    plan_id,
    operation_id,
    method,
    path_template,
    safety,
    status,
    count,
) -> bool:
    return (
        result.get("plan_id") == plan_id
        and result.get("source_id") == ids.get("sourceId")
        and result.get("source_revision_id") == ids.get("approvedRevisionId")
        and result.get("operation_id") == operation_id
        and result.get("method") == method
        and result.get("path_template") == path_template
        and result.get("safety") == safety
        and result.get("status") == status
        and result.get("delivery") == "response_received"
        and result.get("http_call_count") == count
        and result.get("validation_issue_count") == 0
    )


def _all_execution_records_safe(observations, ids) -> bool:
    executions = _executions(observations)
    expected = {ids.get("readPlanId"), ids.get("writeAcceptPlanId")}
    return (
        set(executions) == expected
        and not observations.get("publicForbiddenFields")
        and all(item.get("http_call_count") == 1 for item in executions.values())
    )


def _failure_seen(trace, code: str) -> bool:
    return any(item.get("failureCode") == code for item in trace)


def _review_rejection_seen(trace, review_id: str) -> bool:
    expected_path = f"/api/routedeck/reviews/{review_id}/reject"
    return any(
        item.get("page") == "primary"
        and item.get("event") == "response"
        and item.get("method") == "POST"
        and item.get("path") == expected_path
        and item.get("status") == 409
        and item.get("operationId") == "sources.test_routed_api_write"
        and item.get("failureCode") == "review_rejected"
        for item in trace
    )


def _observed_operations(trace, start: int) -> set[str]:
    return {
        str(item["operationId"])
        for item in trace[start:]
        if item.get("operationId")
    }


def _classify_expected_review_outcomes(diagnostics) -> None:
    expected_paths = Counter()
    retained_http = []
    for item in diagnostics["httpErrors"]:
        path = str(item.get("path") or "")
        expected_stale = (
            item.get("status") == 409
            and item.get("method") == "POST"
            and item.get("operationId") == "sources.test_routed_api_write"
            and item.get("failureCode") == "review_stale"
            and re.fullmatch(r"/api/routedeck/reviews/[^/]+/accept", path)
        )
        expected_rejection = (
            item.get("status") == 409
            and item.get("method") == "POST"
            and item.get("operationId") == "sources.test_routed_api_write"
            and item.get("failureCode") == "review_rejected"
            and re.fullmatch(r"/api/routedeck/reviews/[^/]+/reject", path)
        )
        if expected_stale or expected_rejection:
            diagnostics["expectedHttpOutcomes"].append(item)
            expected_paths[(str(item.get("page")), path)] += 1
        else:
            retained_http.append(item)
    diagnostics["httpErrors"] = retained_http
    retained_console = []
    for item in diagnostics["consoleErrors"]:
        key = (str(item.get("page")), str(item.get("locationPath") or item.get("path") or ""))
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


def _video_duration_seconds(path: Path) -> float | None:
    if not path.is_file() or path.stat().st_size == 0:
        return None
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
        check=False,
        capture_output=True,
        text=True,
    )
    if completed.returncode != 0:
        return None
    try:
        duration = float(completed.stdout.strip())
    except ValueError:
        return None
    return duration if duration > 0 else None


if __name__ == "__main__":
    asyncio.run(main())
