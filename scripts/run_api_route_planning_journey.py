from __future__ import annotations

import argparse
import asyncio
import hashlib
import json
import subprocess
import sys
from datetime import UTC, datetime
from pathlib import Path
from urllib.parse import urlsplit
from uuid import uuid4

from playwright.async_api import Page, async_playwright

REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
if str(REPOSITORY_ROOT) not in sys.path:
    sys.path.insert(0, str(REPOSITORY_ROOT))

from scripts.run_api_connection_check_journey import (
    MEDUSA_ENV,
    _load_required_value,
    _profiles,
    _publish_evidence,
    _save_profile,
    is_expected_aborted_request,
)
from scripts.run_api_contract_revision_journey import (
    EXPECTED_FINAL,
    EXPECTED_RAW,
    MEDUSA_SPEC,
    _latest_review_id,
    _capture,
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
    _curation_panel,
    _observed_curation,
    _select_source,
    _selected_conversation_id,
)


INCLUDED_OPERATIONS = frozenset({"GetProductTagsId", "GetProductTypesId"})
EXPECTED_PHASE_OPERATIONS = frozenset(
    {
        "workspace.open_sources",
        "sources.open_api_creation",
        "sources.propose_contract_revision",
        "sources.approve_contract_revision",
        "sources.save_api_connection",
        "sources.save_api_operation_curation",
        "sources.prepare_routed_api_test",
    }
)
EXPECTED_ASSERTION_COUNT = 13


async def main() -> None:
    parser = argparse.ArgumentParser(
        description="Record non-executing API route preparation and clarification."
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
    directory = repository / "artifacts" / "api-route-planning" / run_id
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
        "sequence": 0,
        "sourceInventory": [],
        "sourceInventoryVersion": 0,
        "currentSources": {},
        "contractProposals": {},
        "profiles": {},
        "curations": {},
        "plans": [],
        "publicForbiddenFields": [],
    }
    ids: dict[str, str] = {}
    owner = {
        "display_name": "API Route Planning Evidence Owner",
        "email": f"api-route-planning-{uuid4().hex}@example.com",
        "password": f"Corpus-Api-Route-Planning-{uuid4().hex}!8",
    }
    other_owner = {
        "display_name": "API Route Planning Isolation Owner",
        "email": f"api-route-planning-isolation-{uuid4().hex}@example.com",
        "password": f"Corpus-Api-Route-Isolation-{uuid4().hex}!8",
    }
    clarified_input_canary = f"ptyp-phase-e-clarified-{uuid4().hex}"
    current_input_canary = f"ptyp-phase-e-current-{uuid4().hex}"
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
        _attach_diagnostics(page, "primary", diagnostics, safe_trace, observations)
        try:
            await _register(page, args.url, owner)
            phase_trace_start = len(safe_trace)
            ids["setupConversationId"] = await _selected_conversation_id(page)
            hub = await _open_sources(page)
            await _upload(page, hub)
            await hub.get_by_text("ready", exact=True).first.wait_for(timeout=180_000)
            ids.update(await _source_ids(page, observations))
            _record(
                assertions,
                "fresh Source processing publishes a coherent ready inventory",
                not any(
                    item.get("method") == "GET"
                    and item.get("path") == "/api/sources"
                    and item.get("status") == 500
                    for item in diagnostics["httpErrors"]
                ),
                {
                    "sourceId": ids["sourceId"],
                    "parentRevisionId": ids["parentRevisionId"],
                    "jobId": ids.get("jobId"),
                },
            )

            await hub.get_by_role(
                "button", name="Prepare contract revision", exact=True
            ).click()
            proposal = _proposal_panel(page)
            await proposal.get_by_role(
                "heading", name="API contract revision proposal", exact=True
            ).wait_for(timeout=90_000)
            proposals = await _observed_proposals(observations, ids["sourceId"])
            ids["proposalId"] = str(proposals[0]["proposal_id"])
            await proposal.get_by_role(
                "button", name="Review this revision", exact=True
            ).click()
            review = _review_surface(page)
            await review.get_by_role(
                "heading",
                name="Create this immutable API contract revision?",
                exact=True,
            ).wait_for(timeout=30_000)
            ids["reviewId"] = await _latest_review_id(safe_trace)
            await review.get_by_role(
                "button", name="Accept and create new revision", exact=True
            ).click()
            await hub.get_by_text("Reviewed contract revision", exact=True).wait_for(
                timeout=60_000
            )
            current = await _observed_current_source(
                observations,
                ids["sourceId"],
                excluding_revision_id=ids["parentRevisionId"],
            )
            ids["approvedRevisionId"] = str(current["revision"]["revision_id"])
            _record(
                assertions,
                "owner approves the exact effective immutable API revision",
                current["revision"]["summary"].get("final_canonical_sha256")
                == EXPECTED_FINAL,
                {
                    "proposalId": ids["proposalId"],
                    "reviewId": ids["reviewId"],
                    "approvedRevisionId": ids["approvedRevisionId"],
                    "finalHash": EXPECTED_FINAL,
                },
            )

            connection_panel = hub.locator("section.api-connection-panel")
            await connection_panel.get_by_role(
                "heading", name="API connections", exact=True
            ).wait_for(timeout=30_000)
            await _save_profile(connection_panel, "Local Medusa planning", medusa_key)
            profiles = await _profiles(observations, ids["sourceId"], minimum_count=1)
            profile = next(
                item
                for item in profiles
                if item.get("profile_name") == "Local Medusa planning"
            )
            ids["profileId"] = str(profile["id"])

            curation_panel = _curation_panel(page)
            await curation_panel.get_by_role(
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
            if not INCLUDED_OPERATIONS < operation_ids:
                raise RuntimeError("The exact Medusa taxonomy operations are unavailable.")
            await _classify_exact(curation_panel, operation_ids)
            await curation_panel.get_by_role(
                "button", name="Save operation selection", exact=True
            ).click()
            await curation_panel.get_by_text(
                f"Saved {len(INCLUDED_OPERATIONS)} included and "
                f"{len(operation_ids) - len(INCLUDED_OPERATIONS)} excluded operations for this exact revision.",
                exact=True,
            ).wait_for(timeout=30_000)
            saved_curation = await _observed_curation(
                observations, ids["sourceId"], minimum_history=1
            )
            ids["curationId"] = str(saved_curation["current"]["id"])
            _record(
                assertions,
                "exact curation makes only TagsId and TypesId the retrieval corpus",
                set(saved_curation["current"]["included_operation_ids"])
                == INCLUDED_OPERATIONS,
                {
                    "curationId": ids["curationId"],
                    "includedOperationIds": sorted(INCLUDED_OPERATIONS),
                    "excludedCount": len(operation_ids) - len(INCLUDED_OPERATIONS),
                },
            )

            await page.get_by_label("Message the assistant", exact=True).fill(
                "Open the non-executing routed API operation planner for this Source."
            )
            await page.get_by_role("button", name="Send message", exact=True).click()
            planner = _planner(page)
            await planner.get_by_role(
                "heading", name="API operation test", exact=True
            ).wait_for(timeout=90_000)
            await _wait_for_agent_idle(page)
            _record(
                assertions,
                "agent-origin preparation opens the stable non-executing planner",
                await planner.get_by_text(
                    "Planning only; no API request has been sent.", exact=True
                ).is_visible(),
                {"conversationId": ids["setupConversationId"]},
            )

            await _bind_planner_context(planner, ids)
            await _create_plan(planner, request_text="get product taxonomy")
            await planner.get_by_text(
                "Waiting for an operation choice", exact=True
            ).wait_for(timeout=60_000)
            ambiguous = await _latest_plan(observations, state="needs_operation_choice")
            ids["ambiguityPlanId"] = str(ambiguous["plan_id"])
            ids["ambiguityRecordId"] = str(ambiguous["record_id"])
            candidate_ids = _ranked_operation_ids(ambiguous)
            ambiguity_bounds = await _capture_group(
                page,
                planner,
                {
                    "state": planner.get_by_text(
                        "Waiting for an operation choice", exact=True
                    ),
                    "unselected": planner.get_by_text(
                        "No operation selected", exact=True
                    ).first,
                    "choice": planner.get_by_label(
                        "Which of these included operations did you mean?", exact=True
                    ),
                    "calls": planner.get_by_text("External calls: 0", exact=True),
                },
                1440,
                1000,
                repository,
                directory,
                screenshots,
                "01-real-ambiguity-no-preselection-desktop",
            )
            _record(
                assertions,
                "real Tags/Types ambiguity exposes candidates without preselection",
                candidate_ids == INCLUDED_OPERATIONS
                and _binding_matches(ambiguous, ids)
                and all(step.get("selected_operation_id") is None for step in ambiguous["steps"]),
                {
                    "planId": ids["ambiguityPlanId"],
                    "recordId": ids["ambiguityRecordId"],
                    "candidateOperationIds": sorted(candidate_ids),
                    "bounds": ambiguity_bounds,
                },
            )

            choice = planner.get_by_label(
                "Which of these included operations did you mean?", exact=True
            )
            await choice.select_option("GetProductTypesId")
            await planner.get_by_role(
                "button", name="Continue this plan", exact=True
            ).click()
            await planner.get_by_text(
                "Waiting for one required value", exact=True
            ).wait_for(timeout=60_000)
            needs_id = await _latest_plan(observations, state="needs_input")
            ids["operationChoiceRecordId"] = str(needs_id["record_id"])
            missing_bounds = await _capture_group(
                page,
                planner,
                {
                    "state": planner.get_by_text(
                        "Waiting for one required value", exact=True
                    ),
                    "id": planner.get_by_label(
                        "What should Corpus use for id?", exact=True
                    ),
                    "managed": planner.get_by_text(
                        "Managed by selected connection profile", exact=True
                    ),
                    "calls": planner.get_by_text("External calls: 0", exact=True),
                },
                1440,
                1000,
                repository,
                directory,
                screenshots,
                "02-choice-needs-only-id-desktop",
            )
            _record(
                assertions,
                "typed operation choice keeps lineage and needs only id while auth is profile-managed",
                needs_id["plan_id"] == ambiguous["plan_id"]
                and needs_id["previous_record_id"] == ambiguous["record_id"]
                and needs_id["missing_inputs"] == ["id"]
                and needs_id["operation_choice"] == "GetProductTypesId"
                and needs_id["managed_parameters"]
                == [
                    {
                        "name": "x-publishable-api-key",
                        "location": "header",
                        "authentication_method": "api_key",
                        "source": "managed_by_profile",
                    }
                ],
                {"recordId": ids["operationChoiceRecordId"], "bounds": missing_bounds},
            )

            await planner.get_by_label(
                "What should Corpus use for id?", exact=True
            ).fill(clarified_input_canary)
            await planner.get_by_role(
                "button", name="Continue this plan", exact=True
            ).click()
            await planner.get_by_text(
                "Route ready — execution is not enabled in this slice", exact=True
            ).wait_for(timeout=60_000)
            ready = await _latest_plan(observations, state="ready")
            ids["clarifiedReadyRecordId"] = str(ready["record_id"])
            _record(
                assertions,
                "id clarification completes the same immutable lineage without execution",
                ready["plan_id"] == ambiguous["plan_id"]
                and _binding_matches(ready, ids)
                and ready["previous_record_id"] == needs_id["record_id"]
                and ready["api_call_count"] == 0
                and ready["input_provenance"]
                == [{"name": "id", "source": "user_clarification"}],
                {"recordId": ids["clarifiedReadyRecordId"], "apiCallCount": 0},
            )

            ids["currentRequestConversationId"] = await _new_conversation(page)
            hub = await _open_sources(page)
            await _select_source(hub, "Reviewed local Medusa Store")
            await hub.get_by_role(
                "button", name="Plan routed operation", exact=True
            ).click()
            planner = _planner(page)
            await planner.get_by_role(
                "heading", name="API operation test", exact=True
            ).wait_for(timeout=30_000)
            await _bind_planner_context(planner, ids)
            await _create_plan(
                planner,
                request_text="get product type by id",
                known_name="id",
                known_value=current_input_canary,
            )
            await planner.get_by_text(
                "Route ready — execution is not enabled in this slice", exact=True
            ).wait_for(timeout=60_000)
            current_ready = await _latest_plan(
                observations,
                state="ready",
                plan_not=ids["ambiguityPlanId"],
            )
            ids["currentRequestPlanId"] = str(current_ready["plan_id"])
            ids["currentRequestRecordId"] = str(current_ready["record_id"])
            ready_bounds = await _capture_group(
                page,
                planner,
                {
                    "state": planner.get_by_text(
                        "Route ready — execution is not enabled in this slice", exact=True
                    ),
                    "operation": planner.get_by_text("GetProductTypesId", exact=True),
                    "request": planner.get_by_text("Current request", exact=True),
                    "managed": planner.get_by_text(
                        "Managed by selected connection profile", exact=True
                    ),
                    "calls": planner.get_by_text("External calls: 0", exact=True),
                },
                1440,
                1000,
                repository,
                directory,
                screenshots,
                "03-current-request-ready-desktop",
            )
            _record(
                assertions,
                "surface-origin preparation records current-request provenance and a ready read route",
                current_ready["input_provenance"]
                == [{"name": "id", "source": "current_request"}]
                and _binding_matches(current_ready, ids)
                and _selected_operations(current_ready) == {"GetProductTypesId"}
                and current_ready["api_call_count"] == 0,
                {
                    "conversationId": ids["currentRequestConversationId"],
                    "planId": ids["currentRequestPlanId"],
                    "recordId": ids["currentRequestRecordId"],
                    "bounds": ready_bounds,
                },
            )

            await page.reload()
            planner = _planner(page)
            await planner.get_by_text(
                "Route ready — execution is not enabled in this slice", exact=True
            ).wait_for(timeout=60_000)
            subprocess.run(
                ["docker", "compose", "restart", "backend"],
                cwd=repository,
                check=True,
                capture_output=True,
                text=True,
            )
            await asyncio.to_thread(_wait_ready, f"{args.backend_url}/readyz")
            await page.reload()
            planner = _planner(page)
            await planner.get_by_text(
                "Route ready — execution is not enabled in this slice", exact=True
            ).wait_for(timeout=60_000)
            restarted = await _latest_plan(
                observations,
                state="ready",
                plan_id=ids["currentRequestPlanId"],
            )
            await page.set_viewport_size({"width": 390, "height": 844})
            mobile_bounds = await _capture_group(
                page,
                planner,
                {
                    "state": planner.get_by_text(
                        "Route ready — execution is not enabled in this slice", exact=True
                    ),
                    "operation": planner.get_by_text("GetProductTypesId", exact=True),
                    "calls": planner.get_by_text("External calls: 0", exact=True),
                },
                390,
                844,
                repository,
                directory,
                screenshots,
                "04-ready-after-restart-mobile-390x844",
            )
            _record(
                assertions,
                "reload and backend restart preserve the exact non-executing plan on mobile",
                restarted["record_id"] == ids["currentRequestRecordId"],
                {"viewport": {"width": 390, "height": 844}, "bounds": mobile_bounds},
            )

            await page.set_viewport_size({"width": 1440, "height": 1000})
            ids["multiStepConversationId"] = await _new_conversation(page)
            hub = await _open_sources(page)
            await _select_source(hub, "Reviewed local Medusa Store")
            await hub.get_by_role(
                "button", name="Plan routed operation", exact=True
            ).click()
            planner = _planner(page)
            await planner.get_by_role(
                "heading", name="API operation test", exact=True
            ).wait_for(timeout=30_000)
            await _bind_planner_context(planner, ids)
            await _create_plan(
                planner, request_text="get product taxonomy then get product taxonomy"
            )
            await planner.get_by_text(
                "No included operation can route this request", exact=True
            ).wait_for(timeout=60_000)
            multi = await _latest_plan(observations, state="not_routable")
            ids["multiStepPlanId"] = str(multi["plan_id"])
            multi_bounds = await _capture_group(
                page,
                planner,
                {
                    "state": planner.get_by_text(
                        "No included operation can route this request", exact=True
                    ),
                    "steps": planner.get_by_role(
                        "list", name="Ordered routed operations", exact=True
                    ),
                    "calls": planner.get_by_text("External calls: 0", exact=True),
                },
                1440,
                1000,
                repository,
                directory,
                screenshots,
                "05-unresolved-multi-step-desktop",
            )
            _record(
                assertions,
                "unresolved multi-step planning is atomic and non-executing",
                len(multi["steps"]) == 2 and multi["api_call_count"] == 0,
                {"planId": ids["multiStepPlanId"], "stepCount": 2, "bounds": multi_bounds},
            )

            plans = [item for item in observations["plans"] if isinstance(item, dict)]
            ranked = set().union(*(_ranked_operation_ids(item) for item in plans))
            phase_trace_end = len(safe_trace)
            phase_trace = safe_trace[phase_trace_start:phase_trace_end]
            observed_operations = {
                str(item["operationId"])
                for item in phase_trace
                if isinstance(item.get("operationId"), str)
            }
            _record(
                assertions,
                "excluded operations never influence routing and all retained plans have zero calls",
                ranked <= INCLUDED_OPERATIONS
                and all(item.get("api_call_count") == 0 for item in plans)
                and all(_binding_matches(item, ids) for item in plans)
                and observed_operations <= EXPECTED_PHASE_OPERATIONS
                and "sources.prepare_routed_api_test" in observed_operations
                and not any("execute" in value.casefold() for value in observed_operations)
                and not observations["publicForbiddenFields"]
                and not await planner.get_by_role(
                    "button", name="Execute", exact=True
                ).count(),
                {
                    "rankedOperationIds": sorted(ranked),
                    "planCount": len(plans),
                    "apiCallCounts": sorted(
                        {int(item["api_call_count"]) for item in plans}
                    ),
                    "observedOperationIds": sorted(observed_operations),
                    "publicForbiddenFields": observations["publicForbiddenFields"],
                },
            )

            conversation_ids = {
                ids["setupConversationId"],
                ids["currentRequestConversationId"],
                ids["multiStepConversationId"],
            }
            _record(
                assertions,
                "plan state remains isolated across three authenticated conversations",
                len(conversation_ids) == 3
                and len(
                    {
                        ids["ambiguityPlanId"],
                        ids["currentRequestPlanId"],
                        ids["multiStepPlanId"],
                    }
                )
                == 3
                and _binding_matches(ambiguous, ids)
                and _binding_matches(current_ready, ids)
                and _binding_matches(multi, ids),
                {
                    "bindings": [
                        {
                            "conversationId": ids["setupConversationId"],
                            "planId": ids["ambiguityPlanId"],
                            "sourceId": ambiguous["source_id"],
                            "revisionId": ambiguous["source_revision_id"],
                            "profileId": ambiguous["profile_id"],
                            "curationId": ambiguous["curation_id"],
                        },
                        {
                            "conversationId": ids["currentRequestConversationId"],
                            "planId": ids["currentRequestPlanId"],
                            "sourceId": current_ready["source_id"],
                            "revisionId": current_ready["source_revision_id"],
                            "profileId": current_ready["profile_id"],
                            "curationId": current_ready["curation_id"],
                        },
                        {
                            "conversationId": ids["multiStepConversationId"],
                            "planId": ids["multiStepPlanId"],
                            "sourceId": multi["source_id"],
                            "revisionId": multi["source_revision_id"],
                            "profileId": multi["profile_id"],
                            "curationId": multi["curation_id"],
                        },
                    ]
                },
            )

            sign_out = page.get_by_label("Sign out", exact=True)
            await sign_out.click()
            await page.get_by_role(
                "heading", name="Explore Corpus", exact=True
            ).wait_for(timeout=30_000)
            await sign_out.wait_for(state="detached", timeout=30_000)
            await _register(page, args.url, other_owner)
            other_hub = await _open_sources(page)
            await other_hub.get_by_text("No API sources yet.", exact=True).wait_for(
                timeout=30_000
            )
            await _capture(
                page,
                repository,
                directory,
                screenshots,
                "06-second-owner-empty-inventory-desktop",
                full_page=True,
            )
            _record(
                assertions,
                "second owner cannot see the first owner's Source, profile, curation, or plans",
                await other_hub.get_by_text(
                    "Reviewed local Medusa Store", exact=True
                ).count()
                == 0,
                {"firstOwnerSourceId": ids["sourceId"], "visibleSourceCount": 0},
            )
        except Exception as caught:
            error = f"{type(caught).__name__}: {caught}"
        finally:
            video = page.video
            await page.close()
            if video is not None:
                raw = Path(await video.path())
                final = directory / "api-route-planning-continuous.webm"
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
    passed = (
        error is None
        and not unexpected
        and len(assertions) == EXPECTED_ASSERTION_COUNT
        and all(bool(item["passed"]) for item in assertions)
    )
    trace_path = directory / "corpus-trace.json"
    result_path = directory / "result.json"
    result = {
        "schema": "corpus.api-route-planning-journey.v1",
        "runId": run_id,
        "status": "passed" if passed else "failed",
        "runtime": {
            "location": "local Docker Compose",
            "frontend": args.url,
            "backend": args.backend_url,
            "command": ".\\.venv\\Scripts\\python.exe scripts\\run_api_route_planning_journey.py --url http://127.0.0.1:5199",
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
            "credentialValues": False,
            "inputValues": False,
        },
        "error": error,
        "limitations": [
            "This slice prepares routes and clarifications only; it does not resolve credentials or execute an API operation.",
            "Zero target calls are enforced structurally by the route-plan service and immutable records; browser diagnostics cannot independently observe server outbound traffic.",
            "Expired-plan and stale-CAS replacement semantics remain covered by focused deterministic tests, not this bounded browser journey.",
        ],
    }
    _publish_evidence(
        directory=directory,
        result_path=result_path,
        trace_path=trace_path,
        result_json=json.dumps(result, indent=2) + "\n",
        trace_json=json.dumps(safe_trace, indent=2) + "\n",
        secrets=(
            medusa_key,
            owner["password"],
            other_owner["password"],
            clarified_input_canary,
            current_input_canary,
        ),
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
    await hub.get_by_role("heading", name="Source Hub", exact=True).wait_for(
        timeout=30_000
    )
    return hub


async def _classify_exact(panel, operation_ids: set[str]) -> None:
    for operation_id in sorted(operation_ids):
        group = panel.get_by_role(
            "group",
            name=f"Availability for {operation_id}",
            exact=True,
        )
        decision = "Include" if operation_id in INCLUDED_OPERATIONS else "Exclude"
        await group.get_by_role("radio", name=decision, exact=True).click()
    await panel.get_by_text(
        "Every discovered operation is explicitly classified.", exact=True
    ).wait_for(timeout=30_000)


def _planner(page: Page):
    return page.locator(
        'section.api-operation-test[aria-labelledby="api-operation-test-title"]'
    )


async def _create_plan(
    panel,
    *,
    request_text: str,
    known_name: str = "",
    known_value: str = "",
) -> None:
    request = panel.get_by_label("What should Corpus route?", exact=True)
    await request.fill(request_text)
    if bool(known_name) != bool(known_value):
        raise RuntimeError("Current-request input name and value must be paired.")
    if known_name:
        name_input = panel.get_by_label(
            "Known input name (optional)", exact=True
        )
        value_input = panel.get_by_label(
            "Known input value (optional)", exact=True
        )
        await name_input.fill(known_name)
        await value_input.fill(known_value)
        if await name_input.input_value() != known_name:
            raise RuntimeError(
                "The exact current-request input name was not bound to the planner."
            )
        if await value_input.input_value() != known_value:
            raise RuntimeError(
                "The exact current-request input value was not bound to the planner."
            )
    if await request.input_value() != request_text:
        raise RuntimeError("The exact route request was not bound to the planner.")
    button = panel.get_by_role("button", name="Prepare route", exact=True)
    for _ in range(300):
        if await button.is_enabled():
            break
        await asyncio.sleep(0.1)
    else:
        raise RuntimeError(
            "Prepare route remained disabled after exact Source, profile, "
            "curation, and request bindings."
        )
    await button.click()


async def _bind_planner_context(panel, ids: dict[str, object]) -> None:
    source = panel.get_by_label("Effective API revision", exact=True)
    await source.select_option(ids["sourceId"])
    if await source.input_value() != ids["sourceId"]:
        raise RuntimeError("The planner did not bind the exact approved Source revision.")

    profile = panel.get_by_label("Saved connection profile", exact=True)
    await profile.select_option(ids["profileId"])
    if await profile.input_value() != ids["profileId"]:
        raise RuntimeError("The planner did not bind the exact saved connection profile.")

    await panel.get_by_text(
        f"Current curation {ids['curationId']} · included {len(INCLUDED_OPERATIONS)}",
        exact=True,
    ).wait_for(timeout=30_000)


async def _new_conversation(page: Page) -> str:
    previous = await _selected_conversation_id(page)
    await page.get_by_role("button", name="New conversation", exact=True).click()
    await page.wait_for_function(
        "([key, old]) => sessionStorage.getItem(key) !== old",
        arg=["corpus.selected-conversation.v1", previous],
        timeout=30_000,
    )
    current = await _selected_conversation_id(page)
    if current == previous:
        raise RuntimeError("Corpus did not create a distinct conversation.")
    return current


async def _wait_for_agent_idle(page: Page) -> None:
    await page.get_by_role(
        "button", name="Stop response", exact=True
    ).wait_for(state="detached", timeout=120_000)
    send = page.get_by_role("button", name="Send message", exact=True)
    await send.wait_for(state="visible", timeout=30_000)
    composer = page.get_by_label("Message the assistant", exact=True)
    await composer.wait_for(state="visible", timeout=30_000)
    for _ in range(300):
        if await composer.is_enabled():
            return
        await asyncio.sleep(0.1)
    raise TimeoutError("The agent conversation did not return to an idle composer.")


async def _latest_plan(
    observations: dict[str, object],
    *,
    state: str,
    plan_not: str | None = None,
    plan_id: str | None = None,
) -> dict[str, object]:
    for _ in range(300):
        plans = observations.get("plans")
        if isinstance(plans, list):
            for item in reversed(plans):
                if (
                    isinstance(item, dict)
                    and item.get("state") == state
                    and (plan_not is None or item.get("plan_id") != plan_not)
                    and (plan_id is None or item.get("plan_id") == plan_id)
                ):
                    return item
        await asyncio.sleep(0.1)
    raise TimeoutError(f"The redacted {state} route plan was not observed.")


def _ranked_operation_ids(plan: dict[str, object]) -> set[str]:
    return {
        str(item["operation_id"])
        for step in plan.get("steps", [])
        if isinstance(step, dict)
        for item in step.get("ranked_operations", [])
        if isinstance(item, dict) and item.get("operation_id")
    }


def _selected_operations(plan: dict[str, object]) -> set[str]:
    return {
        str(step["selected_operation_id"])
        for step in plan.get("steps", [])
        if isinstance(step, dict) and step.get("selected_operation_id")
    }


def _binding_matches(plan: dict[str, object], ids: dict[str, str]) -> bool:
    return (
        plan.get("source_id") == ids.get("sourceId")
        and plan.get("source_revision_id") == ids.get("approvedRevisionId")
        and plan.get("profile_id") == ids.get("profileId")
        and plan.get("curation_id") == ids.get("curationId")
    )


def _safe_plan(value: dict[str, object]) -> dict[str, object]:
    request_text = str(value.get("request_text") or "")
    return {
        "plan_id": value.get("plan_id"),
        "record_id": value.get("record_id"),
        "previous_record_id": value.get("previous_record_id"),
        "source_id": value.get("source_id"),
        "source_revision_id": value.get("source_revision_id"),
        "profile_id": value.get("profile_id"),
        "curation_id": value.get("curation_id"),
        "request_sha256": hashlib.sha256(request_text.encode("utf-8")).hexdigest(),
        "state": value.get("state"),
        "steps": [
            {
                "selected_operation_id": step.get("selected_operation_id"),
                "method": step.get("method"),
                "path_template": step.get("path_template"),
                "http_safety": step.get("http_safety"),
                "ranked_operations": [
                    {
                        "operation_id": item.get("operation_id"),
                        "endpoint_id": item.get("endpoint_id"),
                    }
                    for item in step.get("ranked_operations", [])
                    if isinstance(item, dict)
                ],
            }
            for step in value.get("steps", [])
            if isinstance(step, dict)
        ],
        "missing_inputs": list(value.get("missing_inputs") or []),
        "input_provenance": [
            {"name": item.get("name"), "source": item.get("source")}
            for item in value.get("input_provenance", [])
            if isinstance(item, dict)
        ],
        "managed_parameters": [
            {
                "name": item.get("name"),
                "location": item.get("location"),
                "authentication_method": item.get("authentication_method"),
                "source": item.get("source"),
            }
            for item in value.get("managed_parameters", [])
            if isinstance(item, dict)
        ],
        "operation_choice": (
            value["operation_choice"].get("operation_id")
            if isinstance(value.get("operation_choice"), dict)
            else None
        ),
        "plan_fingerprint": value.get("plan_fingerprint"),
        "api_call_count": value.get("api_call_count"),
    }


def _attach_diagnostics(page: Page, page_name: str, diagnostics, trace, observations) -> None:
    response_statuses: dict[tuple[str, str], int] = {}
    completed_chat_requests: list[object] = []

    def completed_response_event(response) -> None:
        if (
            response.status == 200
            and response.request.method == "POST"
            and urlsplit(response.url).path == "/api/routedeck/chat"
        ):
            completed_chat_requests.append(response.request)

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
        try:
            body = await response.json() if response.status < 500 else None
            parts = [part for part in path.split("/") if part]
            if path.endswith("/dispatch") or "/reviews/" in path:
                if isinstance(body, dict):
                    event["disposition"] = body.get("disposition")
                    event["operationId"] = body.get("operation_id")
                    event["outcome"] = body.get("outcome")
                    failure = body.get("failure")
                    event["failureCode"] = (
                        failure.get("code") if isinstance(failure, dict) else None
                    )
                    review = body.get("review")
                    if isinstance(review, dict):
                        event["reviewId"] = review.get("id")
            elif response.status < 400 and isinstance(body, list):
                if parts == ["api", "sources"]:
                    observations["sourceInventory"] = body
                    observations["sourceInventoryVersion"] = int(
                        observations["sourceInventoryVersion"]
                    ) + 1
                elif len(parts) == 4 and parts[:2] == ["api", "sources"]:
                    source_id = parts[2]
                    if parts[3] == "contract-revisions":
                        observations["contractProposals"][source_id] = body
                    elif parts[3] == "connections":
                        observations["profiles"][source_id] = [
                            {
                                "id": item.get("id"),
                                "profile_name": item.get("profile_name"),
                                "revision_id": item.get("revision_id"),
                            }
                            for item in body
                            if isinstance(item, dict)
                        ]
            elif response.status < 400 and isinstance(body, dict):
                if len(parts) == 3 and parts[:2] == ["api", "sources"]:
                    observations["currentSources"][parts[2]] = body
                elif len(parts) >= 4 and parts[:2] == ["api", "sources"]:
                    source_id = parts[2]
                    if parts[3] == "operation-curation":
                        observations["curations"][source_id] = body
                    elif parts[3] == "route-plans" and body.get("plan_id"):
                        forbidden = sorted(
                            {
                                "router_decision",
                                "router_evidence",
                                "credential_reference_id",
                                "credential_version",
                            }
                            & set(body)
                        )
                        if forbidden:
                            observations["publicForbiddenFields"].append(forbidden)
                        safe = _safe_plan(body)
                        observations["plans"].append(safe)
                        event.update(
                            {
                                "planId": safe["plan_id"],
                                "recordId": safe["record_id"],
                                "planState": safe["state"],
                                "apiCallCount": safe["api_call_count"],
                            }
                        )
        except Exception:
            event["parse"] = "unavailable"
        trace.append(event)
        if response.status >= 400:
            diagnostics["httpErrors"].append(
                {
                    "page": page_name,
                    "status": response.status,
                    "method": response.request.method,
                    "path": path,
                    "operationId": event.get("operationId"),
                    "failureCode": event.get("failureCode"),
                }
            )

    page.on("response", completed_response_event)
    page.on("response", response_event)

    def console_event(message) -> None:
        if message.type in {"warning", "error"}:
            location = message.location or {}
            diagnostics["consoleErrors"].append(
                {
                    "page": page_name,
                    "type": message.type,
                    "text": message.text[:500],
                    "locationPath": urlsplit(str(location.get("url", ""))).path,
                }
            )

    page.on("console", console_event)
    page.on(
        "pageerror",
        lambda error: diagnostics["pageErrors"].append(
            {"page": page_name, "message": str(error)[:500]}
        ),
    )

    def request_failed(request) -> None:
        item = {
            "page": page_name,
            "method": request.method,
            "path": urlsplit(request.url).path,
            "failure": request.failure,
        }
        key = (
            "expectedAbortedRequests"
            if (
                is_expected_completed_chat_abort(
                    item,
                    response_completed=any(
                        completed is request for completed in completed_chat_requests
                    ),
                )
                or is_expected_aborted_request(item, response_statuses)
            )
            else "requestFailures"
        )
        diagnostics[key].append(item)

    page.on("requestfailed", request_failed)


def is_expected_completed_chat_abort(
    item: dict[str, object],
    *,
    response_completed: bool,
) -> bool:
    return (
        response_completed
        and item.get("failure") == "net::ERR_ABORTED"
        and item.get("method") == "POST"
        and item.get("path") == "/api/routedeck/chat"
    )


if __name__ == "__main__":
    asyncio.run(main())
