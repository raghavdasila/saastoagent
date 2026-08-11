from __future__ import annotations

import argparse
import asyncio
import hashlib
import json
import re
import shutil
import subprocess
import sys
import time
from datetime import UTC, datetime
from pathlib import Path
from urllib.parse import urljoin, urlsplit
from urllib.request import urlopen
from uuid import uuid4

from playwright.async_api import Locator, Page, async_playwright


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
if str(REPOSITORY_ROOT) not in sys.path:
    sys.path.insert(0, str(REPOSITORY_ROOT))

from scripts.run_api_connection_check_journey import (  # noqa: E402
    MEDUSA_ENV,
    _load_required_value,
    _profiles,
)
from scripts.run_api_contract_revision_journey import (  # noqa: E402
    EXPECTED_FINAL,
    EXPECTED_RAW,
    MEDUSA_SPEC,
    _observed_current_source,
    _observed_proposals,
    _proposal_panel,
    _register,
    _review_surface,
)
from scripts.run_api_operation_curation_journey import (  # noqa: E402
    _curation_panel,
    _observed_curation,
    _selected_conversation_id,
)
from scripts.run_api_route_planning_journey import (  # noqa: E402
    _attach_diagnostics,
    _open_sources,
    _wait_for_agent_idle,
)


EXPECTED_CHECKS = 25
CHAT_EVIDENCE_BACKEND_URL = "http://127.0.0.1:8099"
ROUTEDECK_MANIFEST = (
    REPOSITORY_ROOT / "contracts" / "corpus-agent-design-routedeck-manifest.json"
)
FRONTEND_ROUTEDECK_CONTRACT = (
    REPOSITORY_ROOT
    / "frontend"
    / "src"
    / "routedeck"
    / "corpus-frontend-contract.generated.json"
)
INCLUDED_OPERATIONS = frozenset({"GetProductTags", "GetProductTypes"})
REVIEW_STAGE_OPERATIONS = frozenset(
    {"sources.approve_contract_revision", "designer.approve", "deployment.deploy"}
)
FEATURE_SURFACE_SELECTORS = {
    "Agent Designer": "section.designer-home",
    "Agent Builds": "section.builder-home",
    "Agent Sandbox": "section.sandbox-home",
    "Evaluation": "section.evaluation-home",
    "Channels and Deployment": "section.channels-home",
    "Operations": "section.operations-home",
}

CHAT_PROMPTS = {
    "setup_from_file": "Use this file please. Also set up the agent for me.",
    "choose_new_agent": "Create a new one.",
    "create_agent": "It is a shopping assistant. It answers product taxonomy questions and must not invent missing information.",
    "resume_api": "Continue with the store API we just added and show me its analyzed structure.",
    "prepare_api_update": "Prepare the safest API correction for me to review, but do not apply it yet.",
    "request_api_update_decision": "What would that API correction change?",
    "stage_api_update": "I am ready to review that API correction. Keep it pending until I decide.",
    "accept_api_update": "That API correction looks right. Apply it.",
    "curate_api": "Use only the collection endpoints that list all product tags and all product types. Exclude every other API operation.",
    "attach_source": "Attach this prepared store API to the shopping assistant.",
    "enter_design": "Turn my requirements into proposed assistant behavior that I can review.",
    "propose_design": "Turn what we've agreed into a draft design for me to review.",
    "request_design_decision": "Put that proposed behavior up for my approval without accepting it.",
    "accept_design": "Those changes match what I want. Save them.",
    "request_build": "Save this approved design as the version I want built next.",
    "enter_build": "I want to try the approved assistant privately now.",
    "assemble_build": "Create the runnable build from that approved design and its store access.",
    "enter_private_trial": "Before customers see it, I want to try a real taxonomy question.",
    "start_private_trial": "Run a private trial with this request: get product taxonomy.",
    "clarify_types": "Use product types.",
    "enter_evaluation": "Keep that successful trial in the Baseline set as a required easy routing case called Store taxonomy success for future versions.",
    "create_evaluation": "Keep that trial in the Baseline set as a required easy routing case called Store taxonomy success for future versions.",
    "run_evaluation": "Check this version against that saved case.",
    "enter_delivery": "Set up /{slug} as a hosted address called Store Taxonomy, but do not publish it yet.",
    "create_channel": "Use /{slug} for a hosted address called Store Taxonomy.",
    "request_deployment": "Put the eligible version on that address. Show me the consequences for approval before anything goes live.",
    "accept_deployment": "Those publishing consequences are acceptable. Go ahead.",
    "enter_operations": "Show me how that public request to this assistant actually ran.",
}

CHAT_FORBIDDEN_PHRASES = (
    "source hub",
    "agent designer",
    "agent builds",
    "agent sandbox",
    "channels and deployment",
    "operations",
    "routedeck",
    "navgraph",
    "toolrouter",
    "open ",
    "stage ",
    "manage ",
    "navigate ",
    "take me ",
    "go to ",
    "screen",
    "page",
    "surface",
    "feature",
    "exact current",
)

CHAT_AUTONOMOUS_SAFETY_CLASSES = frozenset({"navigation", "state_selection"})


def _manifest_operation_safety_classes() -> dict[str, str]:
    manifest = json.loads(ROUTEDECK_MANIFEST.read_text(encoding="utf-8"))
    safety_classes: dict[str, str] = {}

    def visit(value: object) -> None:
        if isinstance(value, list):
            for item in value:
                visit(item)
            return
        if not isinstance(value, dict):
            return
        for operation_id, contract in value.items():
            if (
                isinstance(operation_id, str)
                and "." in operation_id
                and isinstance(contract, dict)
                and isinstance(contract.get("safetyClass"), str)
            ):
                safety_class = str(contract["safetyClass"])
                previous = safety_classes.setdefault(operation_id, safety_class)
                if previous != safety_class:
                    raise RuntimeError(
                        f"Operation {operation_id} has conflicting safety classes."
                    )
        operations = value.get("operations")
        if isinstance(operations, dict):
            for operation_id, contract in operations.items():
                if not isinstance(operation_id, str) or not isinstance(contract, dict):
                    continue
                safety_class = contract.get("safetyClass")
                if not isinstance(safety_class, str):
                    continue
                previous = safety_classes.setdefault(operation_id, safety_class)
                if previous != safety_class:
                    raise RuntimeError(
                        f"Operation {operation_id} has conflicting safety classes."
                    )
        for item in value.values():
            visit(item)

    visit(manifest)
    if not safety_classes:
        raise RuntimeError("The RouteDeck manifest exposes no operation safety classes.")
    return safety_classes


def _compiled_operation_ids() -> frozenset[str]:
    document = json.loads(FRONTEND_ROUTEDECK_CONTRACT.read_text(encoding="utf-8"))
    nodes = document.get("nodes")
    if not isinstance(nodes, dict):
        raise RuntimeError("The compiled RouteDeck node contract is unavailable.")
    operation_ids = frozenset(
        operation_id
        for node in nodes.values()
        if isinstance(node, dict)
        for raw_operation_ids in [node.get("operation_ids")]
        if isinstance(raw_operation_ids, list)
        for operation_id in raw_operation_ids
        if isinstance(operation_id, str) and operation_id
    )
    if not operation_ids:
        raise RuntimeError("The compiled RouteDeck contract exposes no operations.")
    return operation_ids


CHAT_OPERATION_SAFETY_CLASSES = _manifest_operation_safety_classes()
CHAT_EVIDENCE_OPERATION_IDS = _compiled_operation_ids()


def arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Record one joined Corpus Source-to-Operations lifecycle."
    )
    parser.add_argument("--url", default="http://127.0.0.1:5199")
    parser.add_argument("--backend-url", default="http://127.0.0.1:8099")
    parser.add_argument(
        "--mode",
        choices=("surface", "chat", "hybrid"),
        default="surface",
        help="Exercise a surface-only, ordinary-chat, or mixed chat/surface lifecycle.",
    )
    parser.add_argument("--headed", action="store_true")
    return parser.parse_args()


def _validate_chat_prompts() -> None:
    if len(CHAT_PROMPTS) != len(set(CHAT_PROMPTS.values())):
        raise RuntimeError("Horizontal chat evidence contains a repeated canned prompt.")
    for key, prompt in CHAT_PROMPTS.items():
        normalized = f" {prompt.casefold()} "
        forbidden = tuple(
            phrase for phrase in CHAT_FORBIDDEN_PHRASES if phrase in normalized
        )
        if forbidden:
            raise RuntimeError(
                f"Horizontal chat prompt {key!r} spoonfeeds product plumbing: "
                + ", ".join(forbidden)
            )
        if len(prompt.split()) > 28:
            raise RuntimeError(
                f"Horizontal chat prompt {key!r} is a scripted mega-prompt."
            )
        if any(token in prompt for token in ("_", "sources.", "agents.", "review_")):
            raise RuntimeError(
                f"Horizontal chat prompt {key!r} exposes an internal identity."
            )


async def main() -> None:
    global CHAT_EVIDENCE_BACKEND_URL
    args = arguments()
    CHAT_EVIDENCE_BACKEND_URL = args.backend_url.rstrip("/")
    _validate_chat_prompts()
    if (
        not MEDUSA_SPEC.is_file()
        or hashlib.sha256(MEDUSA_SPEC.read_bytes()).hexdigest() != EXPECTED_RAW
    ):
        raise SystemExit("The exact reviewed Medusa Source is unavailable.")
    medusa_key = _load_required_value(MEDUSA_ENV, "MEDUSA_PUBLISHABLE_KEY")
    runtime_model_provider = _runtime_model_provider()
    run_id = f"{datetime.now(UTC).strftime('%Y%m%dT%H%M%SZ')}-{uuid4().hex[:10]}"
    artifact_family = f"horizontal-product-{args.mode}"
    directory = REPOSITORY_ROOT / "artifacts" / artifact_family / run_id
    directory.mkdir(parents=True, exist_ok=False)
    videos = directory / "raw-video"
    screenshots: list[str] = []
    checks: list[dict[str, object]] = []
    safe_trace: list[dict[str, object]] = []
    diagnostics: dict[str, list[dict[str, object]]] = {
        "httpErrors": [],
        "consoleErrors": [],
        "pageErrors": [],
        "requestFailures": [],
        "expectedAbortedRequests": [],
        "expectedConsoleWarnings": [],
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
    interaction_events: list[dict[str, object]] = []
    ids: dict[str, str] = {}
    error: str | None = None
    video: str | None = None
    video_files: list[str] = []
    recording_started_at = datetime.now(UTC)
    recording_ended_at: datetime | None = None
    recording_metadata: list[dict[str, object]] = []
    owner = {
        "display_name": "Horizontal Lifecycle Owner",
        "email": f"horizontal-{uuid4().hex}@example.com",
        "password": f"Corpus-Horizontal-{uuid4().hex}!8",
    }
    slug = f"horizontal-{uuid4().hex[:12]}"

    async with async_playwright() as playwright:
        browser = await playwright.chromium.launch(headless=not args.headed)
        context = await browser.new_context(
            viewport={"width": 1440, "height": 1000},
            record_video_dir=videos,
            record_video_size={"width": 1440, "height": 1000},
        )
        page = await context.new_page()
        _attach_diagnostics(
            page, "horizontal", diagnostics, safe_trace, observations
        )
        _observe_horizontal(page, observations, safe_trace)
        try:
            await _register(page, args.url, owner)
            ids["conversationId"] = await _selected_conversation_id(page)
            setup_response: str | None = None
            if args.mode in {"chat", "hybrid"}:
                await _open_chat_evidence_inspector(page, safe_trace)
                setup_response = await _chat_upload_source(
                    page,
                    MEDUSA_SPEC,
                    CHAT_PROMPTS["setup_from_file"],
                    (
                        "workspace.open_sources",
                        "sources.open_api_creation",
                        "sources.accept_staged_api",
                        "sources.process_api",
                    ),
                    safe_trace,
                    interaction_events,
                )
                if not _asks_for_agent_choice(setup_response):
                    raise RuntimeError(
                        "Corpus did not ask whether to use an existing Agent or create a new one."
                    )
                hub = page.locator("section.sources-debug.api-source-workspace")
                await hub.wait_for(state="visible", timeout=90_000)
            else:
                hub = await _open_sources(page)
                await _surface_add_and_analyze_api(
                    page,
                    hub,
                    directory,
                    screenshots,
                )
            await hub.get_by_text("ready", exact=True).first.wait_for(timeout=180_000)
            ids.update(await _observed_source_ids(observations))
            _check(
                checks,
                "fresh API Source reaches coherent ready inventory",
                not any(
                    item.get("path") == "/api/sources" and item.get("status") == 500
                    for item in diagnostics["httpErrors"]
                ),
                {"sourceId": ids["sourceId"], "jobId": ids.get("jobId")},
            )

            if args.mode in {"chat", "hybrid"}:
                _check(
                    checks,
                    "ordinary file chat adds and explicitly analyzes the staged API before asking for Agent choice",
                    all(
                        any(item.get("operationId") == operation_id for item in interaction_events)
                        for operation_id in (
                            "workspace.open_sources",
                            "sources.open_api_creation",
                            "sources.accept_staged_api",
                            "sources.process_api",
                        )
                    ) and setup_response is not None and _asks_for_agent_choice(setup_response),
                    {"message": CHAT_PROMPTS["setup_from_file"]},
                )
            else:
                _check(
                    checks,
                    "surface-only file acceptance stays visibly separate from explicit analysis",
                    any(Path(path).name.startswith("00-api-definition-saved") for path in screenshots),
                    {"sourceId": ids["sourceId"]},
                )

            if args.mode == "chat":
                choice_response = await _chat_dispatch(
                    page,
                    CHAT_PROMPTS["choose_new_agent"],
                    "agents.open_create",
                    safe_trace,
                    interaction_events,
                )
                if not _asks_for_agent_details(choice_response):
                    raise RuntimeError("Corpus did not ask for the new Agent's goal or responsibilities.")
                await _chat_dispatch(
                    page,
                    CHAT_PROMPTS["create_agent"],
                    ("agents.create_agent", "agents.attach_source"),
                    safe_trace,
                    interaction_events,
                )
                await _chat_dispatch(
                    page,
                    CHAT_PROMPTS["resume_api"],
                    (
                        "agents.open_attached_source",
                        "sources.inspect_current_api",
                    ),
                    safe_trace,
                    interaction_events,
                )
            else:
                await hub.get_by_role(
                    "button", name="Create a new Agent", exact=True
                ).click()
                await _create_agent_from_surface(page)
                await _return_to_only_api_source(page)
                hub = page.locator("section.sources-debug.api-source-workspace")
                await hub.wait_for(state="visible", timeout=90_000)

            agent_button = page.get_by_role(
                "button", name="Store Taxonomy Assistant Version 1", exact=True
            )
            ids["agentId"] = await _latest_agent_id(observations)

            if args.mode in {"chat", "hybrid"}:
                await _chat_dispatch(
                    page,
                    CHAT_PROMPTS["prepare_api_update"],
                    "sources.propose_contract_revision",
                    safe_trace,
                    interaction_events,
                )
            else:
                await hub.get_by_role(
                    "button", name="Review API changes", exact=True
                ).click()
            proposal = _proposal_panel(page)
            await proposal.get_by_role(
                "heading", name="Proposed API version update", exact=True
            ).wait_for(timeout=90_000)
            proposals = await _observed_proposals(observations, ids["sourceId"])
            ids["proposalId"] = str(proposals[0]["proposal_id"])
            if args.mode in {"chat", "hybrid"}:
                await _chat_dispatch(
                    page,
                    CHAT_PROMPTS["request_api_update_decision"],
                    None,
                    safe_trace,
                    interaction_events,
                )
                await _chat_dispatch(
                    page,
                    CHAT_PROMPTS["stage_api_update"],
                    "sources.approve_contract_revision",
                    safe_trace,
                    interaction_events,
                )
            else:
                await proposal.get_by_role(
                    "button", name="Review this API update", exact=True
                ).click()
            review = _review_surface(page)
            await review.get_by_role(
                "heading", name="Create this immutable API version?", exact=True
            ).wait_for(timeout=30_000)
            ids["sourceReviewId"] = await _contract_review_id(review)
            if args.mode == "chat":
                await _chat_dispatch(
                    page,
                    CHAT_PROMPTS["accept_api_update"],
                    "sources.approve_contract_revision",
                    safe_trace,
                    interaction_events,
                    expected_disposition="completed",
                )
            else:
                await review.get_by_role(
                    "button", name="Accept and create new version", exact=True
                ).click()
            await hub.get_by_text("Validated API version", exact=True).wait_for(
                timeout=60_000
            )
            current = await _observed_current_source(
                observations,
                ids["sourceId"],
                excluding_revision_id=ids["parentRevisionId"],
            )
            ids["approvedRevisionId"] = str(current["revision"]["revision_id"])
            _check(
                checks,
                "exact 6fca API version is approved",
                current["revision"]["summary"].get("final_canonical_sha256")
                == EXPECTED_FINAL,
                {"revisionId": ids["approvedRevisionId"]},
            )

            connection = hub.locator("section.api-connection-panel")
            await connection.get_by_role(
                "heading", name="API connections", exact=True
            ).wait_for(timeout=30_000)
            await _save_profile_exact(
                page,
                connection,
                "Horizontal local Medusa",
                medusa_key,
            )
            profiles = await _profiles(observations, ids["sourceId"], minimum_count=1)
            ids["profileId"] = str(
                next(
                    item
                    for item in profiles
                    if item.get("profile_name") == "Horizontal local Medusa"
                )["id"]
            )
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
            if args.mode in {"chat", "hybrid"}:
                await _chat_dispatch(
                    page,
                    CHAT_PROMPTS["curate_api"],
                    "sources.save_api_operation_curation",
                    safe_trace,
                    interaction_events,
                )
            else:
                await _classify_operations(curation, operation_ids, INCLUDED_OPERATIONS)
                await curation.get_by_role(
                    "button", name="Save operation selection", exact=True
                ).click()
            saved = await _observed_curation(
                observations, ids["sourceId"], minimum_history=1
            )
            ids["curationId"] = str(saved["current"]["id"])
            _check(
                checks,
                "profile and exact two-operation curation are current",
                set(saved["current"]["included_operation_ids"])
                == INCLUDED_OPERATIONS,
                {"profileId": ids["profileId"], "curationId": ids["curationId"]},
            )
            _check(
                checks,
                "Source shows the persisted semantic node-edge graph",
                await page.get_by_role("img", name="Semantic graph visualization", exact=True).is_visible(),
                {"graphSurface": "semantic-node-edge-visualization"},
            )
            semantic_graph = page.get_by_role(
                "img", name="Semantic graph visualization", exact=True
            )
            await semantic_graph.scroll_into_view_if_needed()
            await _capture(page, directory, screenshots, "01-source-semantic-graph")
            split_proven = await _prove_split_surface(
                page,
                directory,
                screenshots,
            )
            _check(
                checks,
                "API Source maximizes beside the continuing chat without changing workflow state",
                split_proven,
                {"layout": "chat-left-surface-right"},
            )

            if args.mode in {"chat", "hybrid"}:
                await _chat_dispatch(
                    page,
                    CHAT_PROMPTS["attach_source"],
                    ("workspace.open_agents", "agents.attach_source"),
                    safe_trace,
                    interaction_events,
                )
            else:
                await hub.get_by_role(
                    "button", name="Use an existing Agent", exact=True
                ).click()
                await page.get_by_role(
                    "heading", name="Agents", exact=True
                ).last.wait_for(timeout=90_000)
                await agent_button.click()
                await page.get_by_label("Ready Workspace Source", exact=True).select_option(
                    ids["sourceId"]
                )
                await page.get_by_role("button", name="Attach Source", exact=True).click()
            await page.get_by_text(
                f"API version {ids['approvedRevisionId']}", exact=True
            ).wait_for(timeout=30_000)
            _check(
                checks,
                "Agent is created and pins the exact approved Source revision",
                bool(ids["agentId"]),
                {"agentId": ids["agentId"], "revisionId": ids["approvedRevisionId"]},
            )

            if args.mode == "chat":
                await _chat_dispatch(
                    page,
                    CHAT_PROMPTS["enter_design"],
                    ("agents.open_designer", "designer.propose"),
                    safe_trace,
                    interaction_events,
                )
                await _feature_surface(page, "Agent Designer").get_by_role(
                    "heading", name="Agent Designer", exact=True
                ).wait_for(timeout=90_000)
            else:
                await _open_bound_agent_area(page, "Designer", "Agent Designer")
            if args.mode == "chat":
                pass
            elif args.mode == "hybrid":
                await _chat_dispatch(
                    page,
                    CHAT_PROMPTS["propose_design"],
                    "designer.propose",
                    safe_trace,
                    interaction_events,
                )
            else:
                await page.get_by_role("button", name="Propose design", exact=True).click()
            await page.get_by_label("Goal", exact=True).wait_for(timeout=30_000)
            if args.mode != "chat":
                await page.get_by_label("Goal", exact=True).fill(
                    "Answer exact product lookup questions through the accepted Source."
                )
                await page.get_by_role(
                    "button", name="Save customization", exact=True
                ).click()
                await page.get_by_text("2 immutable revisions", exact=True).wait_for(
                    timeout=30_000
                )
                await page.get_by_role(
                    "button", name="Review for approval", exact=True
                ).click()
            else:
                await _chat_dispatch(
                    page,
                    CHAT_PROMPTS["request_design_decision"],
                    "designer.approve",
                    safe_trace,
                    interaction_events,
                )
            await page.get_by_role(
                "heading", name="Approve exact Agent design", exact=True
            ).wait_for(timeout=30_000)
            if args.mode == "chat":
                await _chat_dispatch(
                    page,
                    CHAT_PROMPTS["accept_design"],
                    "designer.approve",
                    safe_trace,
                    interaction_events,
                    expected_disposition="completed",
                )
            else:
                await page.get_by_role(
                    "button", name="Approve design", exact=True
                ).click()
            request_build = page.get_by_role(
                "button", name="Request build", exact=True
            )
            await request_build.wait_for(timeout=30_000)
            if args.mode == "chat":
                await _chat_dispatch(
                    page,
                    CHAT_PROMPTS["request_build"],
                    "designer.request_build",
                    safe_trace,
                    interaction_events,
                )
            else:
                await request_build.click()
            await page.get_by_text("Build pending", exact=True).wait_for(timeout=30_000)
            _check(
                checks,
                "Designer appends, reviews, accepts and requests one immutable build",
                True,
                {},
            )
            _check(
                checks,
                "Designer shows the RouteDeck blueprint before build",
                await page.get_by_role("region", name="Agent design blueprint", exact=True).is_visible(),
                {"blueprint": "feature-capability-tool-policy"},
            )
            designer_blueprint = page.get_by_role(
                "region", name="Agent design blueprint", exact=True
            )
            await designer_blueprint.scroll_into_view_if_needed()
            await _capture(page, directory, screenshots, "02-designer-routedeck-blueprint")
            designer_topology = designer_blueprint.get_by_role(
                "region", name="Proposed RouteDeck topology", exact=True
            )
            await designer_topology.scroll_into_view_if_needed()
            await _capture(page, directory, screenshots, "02a-designer-topology")
            designer_navgraph = designer_blueprint.get_by_role(
                "region", name="Compiled RouteDeck NavGraph preview", exact=True
            )
            await designer_navgraph.scroll_into_view_if_needed()
            await _capture(page, directory, screenshots, "02b-designer-navgraph")

            if args.mode == "chat":
                await _chat_dispatch(
                    page,
                    CHAT_PROMPTS["assemble_build"],
                    (
                        "designer.return_to_agent",
                        "agents.open_builds",
                        "builder.assemble",
                    ),
                    safe_trace,
                    interaction_events,
                )
            else:
                await _open_agent_area_for_mode(
                    page,
                    args.mode,
                    label="Builds",
                    heading="Agent Builds",
                    return_operation_id="designer.return_to_agent",
                    open_operation_id="agents.open_builds",
                    prompt=CHAT_PROMPTS["enter_build"],
                    trace=safe_trace,
                    interactions=interaction_events,
                    continuation="Continue to Builds",
                )
                if args.mode == "hybrid":
                    await _chat_dispatch(
                        page,
                        CHAT_PROMPTS["assemble_build"],
                        "builder.assemble",
                        safe_trace,
                        interaction_events,
                    )
                else:
                    await page.get_by_role(
                        "button", name="Assemble accepted build", exact=True
                    ).click()
            ready_build = page.locator(".builder-home li[data-status='ready']")
            await ready_build.wait_for(timeout=180_000)
            ids["buildId"] = await _latest_build_id(observations)
            _check(
                checks,
                "Builder materializes the exact accepted design and Source bindings",
                bool(ids["buildId"]),
                {"buildId": ids["buildId"]},
            )
            _check(
                checks,
                "Builder shows the immutable compiled RouteDeck NavGraph",
                await ready_build.get_by_role("heading", name="NavGraph", exact=True).is_visible(),
                {"buildId": ids["buildId"]},
            )
            await ready_build.scroll_into_view_if_needed()
            await _capture(page, directory, screenshots, "03-build-navgraph")

            if args.mode == "chat":
                await _chat_dispatch(
                    page,
                    CHAT_PROMPTS["start_private_trial"],
                    (
                        "agents.return_to_hub",
                        "agents.open_sandbox",
                        "sandbox.start",
                    ),
                    safe_trace,
                    interaction_events,
                )
            else:
                await _open_agent_area_for_mode(
                    page,
                    args.mode,
                    label="Sandbox",
                    heading="Agent Sandbox",
                    return_operation_id="agents.return_to_hub",
                    open_operation_id="agents.open_sandbox",
                    prompt=CHAT_PROMPTS["enter_private_trial"],
                    trace=safe_trace,
                    interactions=interaction_events,
                    continuation="Continue to Sandbox",
                )
                if args.mode == "hybrid":
                    await _chat_dispatch(
                        page,
                        CHAT_PROMPTS["start_private_trial"],
                        "sandbox.start",
                        safe_trace,
                        interaction_events,
                    )
                else:
                    await page.get_by_label("Message", exact=True).fill(
                        "get product taxonomy"
                    )
                    await page.get_by_role(
                        "button", name="Start isolated run", exact=True
                    ).click()
            waiting_run = await _wait_for_sandbox_clarification(page)
            await waiting_run.get_by_role(
                "region", name="ToolRouter clarification subagent", exact=True
            ).wait_for(timeout=30_000)
            _check(
                checks,
                "Sandbox exposes a real ToolRouter clarification before any API call",
                await waiting_run.get_by_text("0 API calls", exact=True).is_visible(),
                {},
            )
            await waiting_run.scroll_into_view_if_needed()
            await _capture(page, directory, screenshots, "04-sandbox-waiting")
            if args.mode == "chat":
                await _chat_dispatch(
                    page,
                    CHAT_PROMPTS["clarify_types"],
                    "sandbox.resume",
                    safe_trace,
                    interaction_events,
                )
            else:
                await waiting_run.get_by_label("Operation", exact=True).select_option(
                    "GetProductTypes"
                )
                await waiting_run.get_by_role(
                    "button", name="Continue same run", exact=True
                ).click()
            sandbox_result = page.locator(".sandbox-home li[data-status='succeeded']").first
            await sandbox_result.wait_for(timeout=180_000)
            await sandbox_result.get_by_text("1 API calls", exact=True).wait_for()
            ids["sandboxRunId"] = await _latest_sandbox_id(observations)
            _check(
                checks,
                "Sandbox completes one validated API call through the assembled build",
                bool(ids["sandboxRunId"]),
                {"sandboxRunId": ids["sandboxRunId"], "apiCallCount": 1},
            )
            _check(
                checks,
                "Sandbox shows isolated RouteDeck and ToolRouter clarification plumbing",
                await sandbox_result.get_by_role("heading", name="RouteDeck runtime", exact=True).is_visible()
                and await sandbox_result.get_by_role("region", name="ToolRouter clarification subagent", exact=True).is_visible(),
                {"sandboxRunId": ids["sandboxRunId"]},
            )
            await sandbox_result.scroll_into_view_if_needed()
            await _capture(page, directory, screenshots, "05-sandbox-resolved")

            if args.mode == "chat":
                await _chat_dispatch(
                    page,
                    CHAT_PROMPTS["enter_evaluation"],
                    (
                        "agents.return_to_hub",
                        "agents.open_evaluation",
                        "evaluation.create_case",
                    ),
                    safe_trace,
                    interaction_events,
                )
            else:
                await _open_agent_area_for_mode(
                    page,
                    args.mode,
                    label="Evaluation",
                    heading="Evaluation",
                    return_operation_id="agents.return_to_hub",
                    open_operation_id="agents.open_evaluation",
                    prompt=CHAT_PROMPTS["enter_evaluation"],
                    trace=safe_trace,
                    interactions=interaction_events,
                    continuation="Continue to Evaluation",
                )
            if args.mode == "hybrid":
                await _chat_dispatch(
                    page,
                    CHAT_PROMPTS["create_evaluation"],
                    "evaluation.create_case",
                    safe_trace,
                    interaction_events,
                )
            elif args.mode == "surface":
                await page.get_by_role(
                    "button", name="Create evaluation case", exact=True
                ).click()
            if args.mode in {"chat", "hybrid"}:
                await _chat_dispatch(
                    page,
                    CHAT_PROMPTS["run_evaluation"],
                    "evaluation.run_case",
                    safe_trace,
                    interaction_events,
                )
            else:
                await page.get_by_role("button", name="Run exact case", exact=True).click()
            await page.get_by_text("Eligible for deployment", exact=True).wait_for(
                timeout=180_000
            )
            _check(
                checks,
                "Evaluation derives deployment eligibility from the exact Sandbox run",
                True,
                {},
            )
            await _capture(page, directory, screenshots, "06-evaluation")
            evaluation_navgraph = page.get_by_role(
                "region",
                name=f"RouteDeck NavGraph for build {ids['buildId']}",
                exact=True,
            )
            await evaluation_navgraph.scroll_into_view_if_needed()
            _check(
                checks,
                "Evaluation shows the immutable build RouteDeck NavGraph it evaluated",
                await evaluation_navgraph.is_visible(),
                {"buildId": ids["buildId"]},
            )
            await _capture(page, directory, screenshots, "06b-evaluation-navgraph")

            slug = f"store-taxonomy-{run_id[-6:].casefold()}"
            delivery_prompt = CHAT_PROMPTS["enter_delivery"].format(slug=slug)
            if args.mode == "chat":
                await _chat_dispatch(
                    page,
                    delivery_prompt,
                    (
                        "agents.return_to_hub",
                        "agents.open_channels",
                        "channels.create",
                    ),
                    safe_trace,
                    interaction_events,
                )
            else:
                await _open_agent_area_for_mode(
                    page,
                    args.mode,
                    label="Channels",
                    heading="Channels and Deployment",
                    return_operation_id="agents.return_to_hub",
                    open_operation_id="agents.open_channels",
                    prompt=delivery_prompt,
                    trace=safe_trace,
                    interactions=interaction_events,
                    continuation="Continue to Channels",
                )
            channel_name = page.get_by_label("Name", exact=True)
            channel_address = page.get_by_label("Address", exact=True)
            if args.mode == "chat":
                pass
            elif args.mode == "hybrid":
                await _chat_dispatch(
                    page,
                    CHAT_PROMPTS["create_channel"].format(slug=slug),
                    "channels.create",
                    safe_trace,
                    interaction_events,
                )
            else:
                await page.wait_for_timeout(1_500)
                await _type_exact(
                    channel_name, "Horizontal hosted Agent", "hosted channel name"
                )
                await _type_exact(channel_address, slug, "hosted channel address")
                create_channel = page.get_by_role("button", name="Create channel", exact=True)
                await create_channel.wait_for(state="visible", timeout=30_000)
                for _ in range(300):
                    if await create_channel.is_enabled():
                        break
                    await asyncio.sleep(0.1)
                else:
                    raise TimeoutError("The exact hosted channel was not ready to create.")
                await create_channel.click()
            channel_address = page.locator(
                "section.channels-home li[data-status='ready'] > span"
            ).filter(has_text=re.compile(rf"^/{re.escape(slug)}$"))
            await _wait_for_unique_locator(
                channel_address,
                label="persisted hosted channel",
                timeout_ms=30_000,
            )
            if args.mode in {"chat", "hybrid"}:
                await _chat_dispatch(
                    page,
                    CHAT_PROMPTS["request_deployment"],
                    "deployment.deploy",
                    safe_trace,
                    interaction_events,
                )
            elif args.mode == "surface":
                await page.get_by_role("button", name="Review deployment", exact=True).click()
            await page.get_by_role(
                "heading", name="Approve hosted Agent deployment", exact=True
            ).wait_for(timeout=30_000)
            await _capture(page, directory, screenshots, "07-deployment-review")
            if args.mode == "chat":
                await _chat_dispatch(
                    page,
                    CHAT_PROMPTS["accept_deployment"],
                    "deployment.deploy",
                    safe_trace,
                    interaction_events,
                    expected_disposition="completed",
                )
            else:
                await page.get_by_role(
                    "button", name="Deploy reviewed build", exact=True
                ).click()
            await page.get_by_text("Hosted Agent enabled", exact=True).wait_for(
                timeout=180_000
            )
            _check(
                checks,
                "eligible build is review-gated and deployed to hosted Web",
                True,
                {"slug": slug},
            )
            await _capture(page, directory, screenshots, "08-deployed-channel")
            deployed_navgraph = page.get_by_role(
                "region",
                name=f"RouteDeck NavGraph for build {ids['buildId']}",
                exact=True,
            )
            await deployed_navgraph.scroll_into_view_if_needed()
            _check(
                checks,
                "active deployment shows its exact immutable RouteDeck NavGraph",
                await deployed_navgraph.is_visible(),
                {"buildId": ids["buildId"], "slug": slug},
            )
            await _capture(page, directory, screenshots, "08b-deployed-navgraph")

            _restart_runtime(args.backend_url)
            _wait_ready(args.backend_url)
            await page.reload()
            await page.get_by_role(
                "heading", name="Channels and Deployment", exact=True
            ).wait_for(timeout=90_000)
            await page.get_by_text("Hosted Agent enabled", exact=True).wait_for()
            _check(checks, "deployment survives backend and worker restart", True, {})

            hosted_link = page.get_by_role("link", name="Open hosted Agent", exact=True)
            hosted_href = await hosted_link.get_attribute("href")
            if not hosted_href:
                raise RuntimeError("The deployed Agent address is unavailable.")
            await page.goto(urljoin(args.url, hosted_href))
            await page.get_by_text(
                "Ask the deployed Agent a question.", exact=True
            ).wait_for(timeout=90_000)
            waiting_response = await _public_send(page, "get product taxonomy")
            clarification = page.get_by_role(
                "region", name="Agent needs more information", exact=True
            )
            await clarification.get_by_role(
                "heading", name="One detail needed", exact=True
            ).wait_for(timeout=90_000)
            _check(
                checks,
                "deployed Agent visibly waits for ToolRouter clarification without an API call",
                waiting_response.startswith("Should I use")
                and "product types" in waiting_response.casefold()
                and "product tags" in waiting_response.casefold()
                and "GetProduct" not in waiting_response
                and await clarification.is_visible(),
                {"responseLength": len(waiting_response)},
            )
            await _capture(page, directory, screenshots, "09-public-clarification")
            final_response = await _public_send(page, "Use product types.")
            _check(
                checks,
                "public hosted session completes the deployed read without secrets",
                bool(final_response)
                and "Should I use" not in final_response
                and "What value should I use for id" not in final_response,
                {"responseLength": len(final_response)},
            )
            public_copy = await page.locator("main.public-agent").inner_text()
            _check(
                checks,
                "deployed Agent keeps owner-only runtime diagnostics out of the public session",
                all(token not in public_copy for token in (
                    "RouteDeck", "NavGraph", "ToolRouter", "agent_runtime.",
                    "GetProductTags", "GetProductTypes",
                )),
                {"slug": slug},
            )
            await _capture(page, directory, screenshots, "10-public-resolved")
            await page.go_back(wait_until="domcontentloaded")
            await page.get_by_role(
                "heading", name="Channels and Deployment", exact=True
            ).wait_for(timeout=90_000)
            await _wait_for_product_idle(page)
            await asyncio.to_thread(_wait_ready, args.backend_url)

            await _open_agent_area_for_mode(
                page,
                args.mode,
                label="Operations",
                heading="Operations",
                return_operation_id="agents.return_to_hub",
                open_operation_id="agents.open_operations",
                prompt=CHAT_PROMPTS["enter_operations"],
                trace=safe_trace,
                interactions=interaction_events,
                continuation="View Operations",
            )
            await page.get_by_text(
                "Deployed Agent interactions and redacted execution evidence",
                exact=True,
            ).wait_for(timeout=60_000)
            interaction = page.locator(".operations-home ol > li").first
            await interaction.wait_for(timeout=60_000)
            _check(
                checks,
                "Operations shows deployed interactions and promotion controls",
                await interaction.get_by_role(
                    "button", name="Create evaluation case", exact=True
                ).is_visible(),
                {},
            )
            await _capture(page, directory, screenshots, "11-operations-evidence")
            deployed_runtime = page.get_by_role(
                "region", name=re.compile(r"^Deployed RouteDeck evidence for interaction ")
            ).first
            await deployed_runtime.scroll_into_view_if_needed()
            deployed_toolrouter = deployed_runtime.get_by_role(
                "region", name="Deployed ToolRouter clarification subagent", exact=True
            )
            _check(
                checks,
                "Operations shows owner-only deployed RouteDeck and ToolRouter evidence",
                await deployed_runtime.get_by_role(
                    "heading", name="NavGraph", exact=True
                ).is_visible()
                and await deployed_toolrouter.is_visible(),
                {"buildId": ids["buildId"]},
            )
            await _capture(page, directory, screenshots, "11b-deployed-runtime-plumbing")
            await deployed_toolrouter.scroll_into_view_if_needed()
            await _capture(page, directory, screenshots, "11c-deployed-toolrouter")

            await page.set_viewport_size({"width": 390, "height": 844})
            await page.get_by_role("heading", name="Operations", exact=True).scroll_into_view_if_needed()
            await _capture(page, directory, screenshots, "12-mobile-operations")
            _check(checks, "joined lifecycle renders at 390x844", True, {})
            if args.mode == "hybrid":
                current_conversation = await _selected_conversation_id(page)
                chat_operation_ids = [
                    str(item["operationId"]) for item in interaction_events
                ]
                _check(
                    checks,
                    "hybrid chat and surface actions preserve one conversation without repeating an operation for one request",
                    current_conversation == ids["conversationId"]
                    and _hybrid_chat_ledger_is_coherent(
                        interaction_events,
                        expected_conversation_id=str(ids["conversationId"]),
                    ),
                    {
                        "conversationId": current_conversation,
                        "chatOperationIds": chat_operation_ids,
                    },
                )
        except Exception as caught:
            error = f"{type(caught).__name__}: {caught}"
            try:
                await _capture(page, directory, screenshots, "99-failure")
            except Exception:
                pass
        finally:
            await context.close()
            candidates = sorted(videos.glob("*.webm"), key=lambda item: item.stat().st_mtime)
            if candidates:
                video_files = [
                    str(candidate.relative_to(REPOSITORY_ROOT))
                    for candidate in candidates
                ]
                video = video_files[0]
            await browser.close()
            recording_ended_at = datetime.now(UTC)

    recording_metadata = _video_metadata(video_files)
    _classify_expected_graph_capture_warnings(diagnostics)

    expected_checks = EXPECTED_CHECKS + (1 if args.mode == "hybrid" else 0)
    passed = (
        error is None
        and len(checks) == expected_checks
        and all(bool(item["passed"]) for item in checks)
        and not diagnostics["httpErrors"]
        and not diagnostics["consoleErrors"]
        and not diagnostics["pageErrors"]
        and not diagnostics["requestFailures"]
        and len(recording_metadata) == 1
        and float(recording_metadata[0]["durationSeconds"]) > 0
    )
    result = {
        "runId": run_id,
        "status": "passed" if passed else "failed",
        "assertions": checks,
        "ids": ids,
        "interactionMode": args.mode,
        "interactionEvents": interaction_events,
        "chatInspectionTools": observations["chatInspectionTools"],
        "screenshots": screenshots,
        "video": video,
        "videos": video_files,
        "recording": {
            "kind": "continuous raw Playwright page video",
            "postProcessed": False,
            "playbackRate": 1.0,
            "startedAt": recording_started_at.isoformat(),
            "endedAt": (
                recording_ended_at.isoformat()
                if recording_ended_at is not None
                else None
            ),
            "files": recording_metadata,
        },
        "diagnostics": diagnostics,
        "safeTrace": safe_trace,
        "error": error,
        "runtime": {
            "frontend": args.url,
            "backend": args.backend_url,
            "medusa": "http://127.0.0.1:9100",
            "modelProvider": runtime_model_provider,
        },
    }
    result_path = directory / "result.json"
    result_path.write_text(
        json.dumps(result, indent=2, default=str) + "\n", encoding="utf-8"
    )
    forbidden = (owner["password"], medusa_key)
    _require_secret_free_evidence(directory, forbidden)
    print(f"run={run_id} status={result['status']} assertions={len(checks)}/{expected_checks}")
    print(f"artifact={result_path}")
    if error:
        print(f"error={error}")
    raise SystemExit(0 if passed else 1)


def _classify_expected_graph_capture_warnings(
    diagnostics: dict[str, list[dict[str, object]]],
) -> None:
    unexpected: list[dict[str, object]] = []
    expected = diagnostics.setdefault("expectedConsoleWarnings", [])
    for item in diagnostics.get("consoleErrors", []):
        text = item.get("text")
        if (
            item.get("type") == "warning"
            and item.get("locationPath") == "/sources/api"
            and isinstance(text, str)
            and text.startswith("[.WebGL-")
            and "GL Driver Message" in text
            and "GPU stall due to ReadPixels" in text
        ):
            expected.append(item)
        else:
            unexpected.append(item)
    diagnostics["consoleErrors"] = unexpected


def _require_secret_free_evidence(
    directory: Path,
    forbidden_values: tuple[str, ...],
) -> None:
    canaries = tuple(value.encode("utf-8") for value in forbidden_values if value)
    leaked = any(
        any(canary in path.read_bytes() for canary in canaries)
        for path in directory.rglob("*")
        if path.is_file()
    )
    if leaked:
        shutil.rmtree(directory)
        raise RuntimeError("Horizontal evidence retained a forbidden input value.")


def _video_metadata(paths: list[str]) -> list[dict[str, object]]:
    values: list[dict[str, object]] = []
    for value in paths:
        path = REPOSITORY_ROOT / value
        completed = subprocess.run(
            [
                "ffprobe", "-v", "error", "-show_entries", "format=duration",
                "-of", "default=noprint_wrappers=1:nokey=1", str(path),
            ],
            cwd=REPOSITORY_ROOT,
            text=True,
            capture_output=True,
            timeout=30,
            check=False,
        )
        if completed.returncode != 0:
            raise RuntimeError("The uncut horizontal video could not be verified.")
        duration = float(completed.stdout.strip())
        values.append(
            {
                "path": value,
                "durationSeconds": round(duration, 3),
                "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
                "bytes": path.stat().st_size,
            }
        )
    return values


async def _open_agent_area(page: Page, label: str, heading: str) -> None:
    back = page.get_by_role("button", name="Back to Agent", exact=True)
    await back.wait_for(state="visible", timeout=90_000)
    await back.click()
    await page.locator("section.agents-home").get_by_role(
        "heading", name="Agents", exact=True
    ).wait_for(
        timeout=90_000
    )
    await _open_bound_agent_area(page, label, heading)


async def _open_agent_area_for_mode(
    page: Page,
    mode: str,
    *,
    label: str,
    heading: str,
    return_operation_id: str,
    open_operation_id: str,
    prompt: str,
    trace: list[dict[str, object]],
    interactions: list[dict[str, object]],
    continuation: str | None = None,
) -> None:
    if mode != "chat":
        if continuation is None:
            await _open_agent_area(page, label, heading)
        else:
            await _wait_for_product_idle(page)
            action = page.get_by_role("button", name=continuation, exact=True)
            await action.wait_for(state="visible", timeout=90_000)
            if not await action.is_enabled():
                raise RuntimeError(f"The guided continuation {continuation!r} is disabled.")
            await action.click()
            await _feature_surface(page, heading).get_by_role(
                "heading", name=heading, exact=True
            ).wait_for(timeout=90_000)
            await _wait_for_product_idle(page)
        return
    await _chat_dispatch(
        page,
        prompt,
        (return_operation_id, open_operation_id),
        trace,
        interactions,
    )
    await _feature_surface(page, heading).get_by_role(
        "heading", name=heading, exact=True
    ).wait_for(
        timeout=90_000
    )


async def _open_bound_agent_area(page: Page, label: str, heading: str) -> None:
    await _wait_for_product_idle(page)
    action = page.locator(
        "section.agents-home section.agent-operations"
    ).get_by_role("button", name=label, exact=True)
    await action.wait_for(state="visible", timeout=30_000)
    for _ in range(300):
        if await action.is_enabled():
            break
        await asyncio.sleep(0.1)
    else:
        raise TimeoutError(f"The {label} navigation action did not become enabled.")
    await action.click()
    await _feature_surface(page, heading).get_by_role(
        "heading", name=heading, exact=True
    ).wait_for(
        timeout=90_000
    )
    await _wait_for_product_idle(page)


def _feature_surface(page: Page, heading: str) -> Locator:
    selector = FEATURE_SURFACE_SELECTORS.get(heading)
    if selector is None:
        raise RuntimeError(f"No exact product surface owns heading {heading!r}.")
    return page.locator(selector)


async def _wait_for_product_idle(page: Page) -> None:
    await _wait_for_agent_idle(page)
    await page.locator(".corpus-status[data-status='ready']").wait_for(
        state="visible",
        timeout=120_000,
    )


async def _wait_for_unique_locator(
    locator: Locator,
    *,
    label: str,
    timeout_ms: int,
) -> None:
    attempts = max(1, timeout_ms // 100)
    for _ in range(attempts):
        count = await locator.count()
        if count > 1:
            raise RuntimeError(f"The exact {label} was not unique.")
        if count == 1:
            await locator.wait_for(state="visible", timeout=timeout_ms)
            return
        await asyncio.sleep(0.1)
    raise TimeoutError(f"The exact {label} did not appear.")


async def _observed_source_ids(
    observations: dict[str, object],
) -> dict[str, str]:
    for _ in range(300):
        inventory = observations.get("sourceInventory")
        if isinstance(inventory, list):
            matches = [
                item
                for item in inventory
                if isinstance(item, dict)
                and isinstance(item.get("revision"), dict)
                and item["revision"].get("state") == "ready"
            ]
            if len(matches) > 1:
                raise RuntimeError("The fresh owner has multiple ready API Sources.")
            if len(matches) == 1:
                revision = matches[0]["revision"]
                source_id = matches[0].get("source_id")
                revision_id = revision.get("revision_id")
                job_id = revision.get("job_id")
                if all(isinstance(value, str) and value for value in (
                    source_id,
                    revision_id,
                    job_id,
                )):
                    return {
                        "sourceId": source_id,
                        "parentRevisionId": revision_id,
                        "jobId": job_id,
                    }
        await asyncio.sleep(0.1)
    raise RuntimeError("The exact ready API Source identity was not observed.")


async def _surface_add_and_analyze_api(
    page: Page,
    hub: Locator,
    directory: Path,
    screenshots: list[str],
) -> None:
    await hub.locator(".sources-header-actions").get_by_role(
        "button", name="Add API source", exact=True
    ).click()
    intake = page.locator("section.sources-debug.api-source-workspace")
    await intake.get_by_role(
        "heading", name="Add API source", exact=True
    ).wait_for(timeout=90_000)
    await _type_exact(
        intake.get_by_label("Source name", exact=True),
        "Reviewed local Medusa Store",
        "Source name",
    )
    definition = intake.get_by_label(
        "OpenAPI or Swagger definition", exact=True
    )
    await definition.set_input_files(MEDUSA_SPEC)
    if await definition.input_value() == "":
        raise RuntimeError("The exact API definition was not bound to API intake.")
    await intake.get_by_role(
        "button", name="Add API definition", exact=True
    ).click()
    await intake.get_by_text("Ready to analyze", exact=True).wait_for(
        timeout=90_000
    )
    if not await intake.get_by_text("Not started", exact=True).is_visible():
        raise RuntimeError("Adding the API definition started analysis implicitly.")
    await _capture(
        page,
        directory,
        screenshots,
        "00-api-definition-saved-before-analysis",
    )
    await intake.get_by_role(
        "button", name="Analyze API operations", exact=True
    ).click()


async def _create_agent_from_surface(page: Page) -> None:
    await page.get_by_role(
        "heading", name="Create an agent", exact=True
    ).wait_for(timeout=90_000)
    await _wait_for_product_idle(page)
    form = page.locator("section.agent-create form")
    await _type_exact(
        form.get_by_label("Name", exact=True),
        "Store Taxonomy Assistant",
        "Agent name",
    )
    await _type_exact(
        form.get_by_label("Description", exact=True),
        "Answers product taxonomy questions from an approved API.",
        "Agent description",
    )
    await _type_exact(
        form.get_by_label("Instructions", exact=True),
        "For product lookup requests, use the user's exact words and never invent an identifier.",
        "Agent instructions",
    )
    await form.get_by_role("button", name="Create agent", exact=True).click()
    await page.get_by_role(
        "button", name="Store Taxonomy Assistant Version 1", exact=True
    ).wait_for(timeout=90_000)


async def _return_to_only_api_source(page: Page) -> None:
    await page.get_by_role("button", name="Back to Workspace", exact=True).click()
    await page.get_by_role(
        "heading", name="Corpus Workspace", exact=True
    ).wait_for(timeout=90_000)
    hub = await _open_sources(page)
    inventory = hub.get_by_role("list", name="API sources", exact=True)
    rows = inventory.get_by_role("listitem")
    if await rows.count() != 1:
        raise RuntimeError("The fresh owner does not have exactly one API Source row.")
    action = rows.get_by_role("button", name="Open API source", exact=True)
    await _wait_for_unique_locator(
        action,
        label="only API source action",
        timeout_ms=30_000,
    )
    await action.click()
    api = page.locator("section.sources-debug.api-source-workspace")
    await api.locator("#source-detail-title").filter(
        has_text=re.compile(r"^Reviewed local Medusa Store$")
    ).wait_for(timeout=90_000)


def _asks_for_agent_choice(message: str) -> bool:
    normalized = message.casefold()
    return (
        "agent" in normalized
        and ("existing" in normalized or "already have" in normalized)
        and ("new" in normalized or "create" in normalized)
    )


def _asks_for_agent_details(message: str) -> bool:
    normalized = message.casefold()
    return "agent" in normalized and (
        "goal" in normalized
        or "responsib" in normalized
        or "purpose" in normalized
        or re.search(r"\bdo\b", normalized) is not None
    )


async def _chat_upload_source(
    page: Page,
    source_path: Path,
    message: str,
    expected_operation_id: str | tuple[str, ...],
    trace: list[dict[str, object]],
    interactions: list[dict[str, object]],
) -> str:
    attachment = page.get_by_label("Attach API definition", exact=True)
    await attachment.wait_for(state="visible", timeout=120_000)
    await attachment.set_input_files(source_path)
    if await attachment.input_value() == "":
        raise RuntimeError("The exact API definition was not attached to chat.")
    return await _chat_dispatch(
        page,
        message,
        expected_operation_id,
        trace,
        interactions,
        attachment_name=source_path.stem,
    )


async def _chat_dispatch(
    page: Page,
    message: str,
    expected_operation_id: str | tuple[str, ...] | None,
    trace: list[dict[str, object]],
    interactions: list[dict[str, object]],
    *,
    attachment_name: str | None = None,
    expected_disposition: str | None = None,
) -> str:
    conversation_id = await _selected_conversation_id(page)
    durable_message = _durable_chat_message(message, attachment_name)
    authenticated_inspection = await _refresh_chat_evidence_inspector(page, trace)
    before_inspection = await authenticated_inspection.json()
    if not isinstance(before_inspection, dict):
        raise RuntimeError("The pre-turn RouteDeck inspection was invalid.")
    before_sequence = max(
        (int(item.get("sequence", 0)) for item in trace),
        default=0,
    )
    composer = page.get_by_label("Message the assistant", exact=True)
    await composer.wait_for(state="visible", timeout=360_000)
    deadline = asyncio.get_running_loop().time() + 360
    while asyncio.get_running_loop().time() < deadline:
        if await composer.is_enabled():
            break
        await asyncio.sleep(0.25)
    else:
        raise TimeoutError("The exact chat composer did not become available.")
    await _type_exact(composer, message, "chat request")
    chat_request = lambda request: (
        request.method == "POST"
        and urlsplit(request.url).path == "/api/routedeck/chat"
    )
    async with page.expect_response(
        lambda response: chat_request(response.request),
        timeout=360_000,
    ) as pending_chat:
        await page.get_by_role("button", name="Send message", exact=True).click()
    chat_response = await pending_chat.value
    if chat_response.status != 200:
        raise RuntimeError(
            f"The chat request returned HTTP {chat_response.status}, not 200."
        )
    snapshot = await _wait_for_inspected_chat_turn(
        page,
        authenticated_inspection,
        before_inspection,
        durable_message,
        backend_url=CHAT_EVIDENCE_BACKEND_URL,
    )
    await _wait_for_agent_idle(page)
    trace.append({
        "sequence": max(
            (int(item.get("sequence", 0)) for item in trace),
            default=0,
        ) + 1,
        "page": "horizontal",
        "event": "response",
        "method": "GET",
        "path": "/api/routedeck/inspect",
        "status": 200,
        "source": "authenticated_post_turn_verifier",
    })
    _record_chat_inspection(
        snapshot,
        None,
        trace,
        prior_inspection=before_inspection,
        current_user_message=durable_message,
    )
    if expected_operation_id is None:
        operations = [
            item
            for item in trace
            if int(item.get("sequence", 0)) > before_sequence
            and item.get("event") == "chat_operation"
        ]
        operation_ids = [str(item["operationId"]) for item in operations]
        unexpected = [
            operation_id
            for operation_id in operation_ids
            if CHAT_OPERATION_SAFETY_CLASSES.get(operation_id)
            not in CHAT_AUTONOMOUS_SAFETY_CLASSES
        ]
        if unexpected:
            raise RuntimeError(
                "An informational chat turn performed an unrequested mutation."
            )
        if len(operation_ids) != len(set(operation_ids)):
            raise RuntimeError("Chat repeated an operation in one user turn.")
    else:
        expected_operation_ids = (
            expected_operation_id
            if isinstance(expected_operation_id, tuple)
            else (expected_operation_id,)
        )
        operations = await _chat_operations_after(
            trace,
            before_sequence,
            expected_operation_ids,
        )
    current_conversation = await _selected_conversation_id(page)
    if current_conversation != conversation_id:
        raise RuntimeError("The chat action changed the active Corpus conversation.")
    for operation in operations:
        operation_id = str(operation["operationId"])
        required_disposition = expected_disposition or (
            "requires_review"
            if operation_id in REVIEW_STAGE_OPERATIONS
            else "completed"
        )
        if operation.get("disposition") != required_disposition:
            raise RuntimeError(
                f"Chat operation {operation_id} ended as "
                f"{operation.get('disposition')!r}, not {required_disposition!r}."
            )
        interactions.append(
            {
                "conversationId": conversation_id,
                "message": message,
                "attachmentName": attachment_name,
                "operationId": operation_id,
                "responseSequence": int(operation.get("sequence", 0)),
                "disposition": operation.get("disposition"),
                "outcome": operation.get("outcome"),
            }
        )
    # Keep the unprocessed recording readable at the operation boundary.
    await asyncio.sleep(1.5)
    return _terminal_assistant_content(before_inspection, snapshot, durable_message)


async def _save_profile_exact(
    page: Page,
    panel: Locator,
    name: str,
    credential: str,
) -> None:
    """Bind the protected surface form and prove its real private-form write."""
    form = panel.get_by_role(
        "heading", name="Add connection profile", exact=True
    ).locator("xpath=ancestor::form[1]")
    if await form.count() != 1:
        raise RuntimeError("The exact API connection form is unavailable.")

    fields = {
        "Profile name": name,
        "Environment": "local",
        "Base URL": "http://host.docker.internal:9100",
        "Header name": "x-publishable-api-key",
    }
    await form.get_by_label("Authentication", exact=True).select_option("api_key")
    for label, value in fields.items():
        control = form.get_by_label(label, exact=True)
        await control.wait_for(state="visible", timeout=30_000)
        await control.fill(value)
    secret = form.get_by_label("API key", exact=True)
    await secret.wait_for(state="visible", timeout=30_000)
    await secret.fill(credential)

    # A review/session resync may remount this uncontrolled form. Require a
    # stable, exact readback immediately before the visible user click.
    await page.wait_for_timeout(500)
    for label, expected in fields.items():
        if await form.get_by_label(label, exact=True).input_value() != expected:
            raise RuntimeError(
                f"The exact API connection {label.casefold()} was not retained."
            )
    if await form.get_by_label("Authentication", exact=True).input_value() != "api_key":
        raise RuntimeError("The exact API connection authentication was not retained.")
    if await secret.input_value() != credential:
        raise RuntimeError("The protected API credential was not retained by its form.")
    validity = await form.evaluate(
        """form => ({
          valid: form.checkValidity(),
          invalid: Array.from(form.elements)
            .filter(element => typeof element.checkValidity === 'function' && !element.checkValidity())
            .map(element => element.getAttribute('name') || element.getAttribute('id') || 'unnamed')
        })"""
    )
    if not isinstance(validity, dict) or validity.get("valid") is not True:
        invalid = validity.get("invalid", []) if isinstance(validity, dict) else []
        raise RuntimeError(
            "The API connection form is not valid: " + ", ".join(map(str, invalid))
        )

    async with page.expect_response(
        lambda response: response.request.method == "PUT"
        and urlsplit(response.url).path
        == "/api/routedeck/private-forms/sources-api-connection",
        timeout=30_000,
    ) as pending_private_write:
        await form.get_by_role("button", name="Save connection", exact=True).click()
    private_write = await pending_private_write.value
    if private_write.status != 200:
        raise RuntimeError("The protected API connection form was not accepted.")
    await panel.get_by_text(name, exact=True).wait_for(timeout=30_000)


async def _chat_operations_after(
    trace: list[dict[str, object]],
    after_sequence: int,
    expected_operation_ids: tuple[str, ...],
) -> list[dict[str, object]]:
    if not expected_operation_ids or len(set(expected_operation_ids)) != len(
        expected_operation_ids
    ):
        raise RuntimeError("Chat evidence requires distinct expected operations.")
    deadline = asyncio.get_running_loop().time() + 30
    while asyncio.get_running_loop().time() < deadline:
        operations = [
            item
            for item in trace
            if int(item.get("sequence", 0)) > after_sequence
            and item.get("event") == "chat_operation"
        ]
        observed_ids = [str(item["operationId"]) for item in operations]
        unexpected = [
            operation_id
            for operation_id in observed_ids
            if operation_id not in expected_operation_ids
            and CHAT_OPERATION_SAFETY_CLASSES.get(operation_id)
            not in CHAT_AUTONOMOUS_SAFETY_CLASSES
        ]
        if unexpected:
            raise RuntimeError(
                "Chat dispatched an unexpected operation before the requested result."
            )
        effective_operations = _one_blocked_correction_per_operation(
            operations,
            expected_operation_ids=expected_operation_ids,
        )
        effective_ids = [str(item["operationId"]) for item in effective_operations]
        required_ids = tuple(
            operation_id
            for operation_id in effective_ids
            if operation_id in expected_operation_ids
        )
        if set(expected_operation_ids).issubset(effective_ids):
            if required_ids != expected_operation_ids:
                raise RuntimeError(
                    "Chat dispatched the requested operations in an invalid order."
                )
            return effective_operations
        await asyncio.sleep(0.1)
    missing = sorted(set(expected_operation_ids) - set(effective_ids))
    raise TimeoutError(
        "Chat did not persist the exact operations: " + ", ".join(missing)
    )


def _one_blocked_correction_per_operation(
    operations: list[dict[str, object]],
    *,
    expected_operation_ids: tuple[str, ...],
) -> list[dict[str, object]]:
    grouped: dict[str, list[dict[str, object]]] = {}
    for item in operations:
        grouped.setdefault(str(item["operationId"]), []).append(item)
    for operation_id, attempts in grouped.items():
        if len(attempts) == 1:
            continue
        dispositions = tuple(str(item.get("disposition")) for item in attempts)
        if not (
            operation_id in expected_operation_ids
            and len(attempts) == 2
            and dispositions[0] == "blocked"
            and dispositions[1] != "blocked"
        ):
            raise RuntimeError("Chat repeated an operation in one user turn.")
    return [item for item in operations if item.get("disposition") != "blocked"]


async def _chat_operation_after(
    trace: list[dict[str, object]],
    after_sequence: int,
    expected_operation_id: str,
) -> dict[str, object]:
    deadline = asyncio.get_running_loop().time() + 30
    while asyncio.get_running_loop().time() < deadline:
        dispatches = [
            item
            for item in trace
            if int(item.get("sequence", 0)) > after_sequence
            and item.get("event") == "chat_operation"
        ]
        unexpected = [
            item
            for item in dispatches
            if item.get("operationId") != expected_operation_id
        ]
        if unexpected:
            raise RuntimeError(
                "Chat dispatched an unexpected operation before the exact requested action."
            )
        matches = [
            item
            for item in dispatches
            if item.get("operationId") == expected_operation_id
        ]
        if len(matches) == 1:
            return matches[0]
        if len(matches) > 1:
            raise RuntimeError(
                f"Chat repeated the exact operation {expected_operation_id}."
            )
        await asyncio.sleep(0.1)
    raise TimeoutError(
        f"Chat did not dispatch the exact operation {expected_operation_id}."
    )


async def _wait_for_sandbox_clarification(
    page: Page, *, timeout_ms: int = 180_000
) -> Locator:
    waiting = page.locator(".sandbox-home li[data-status='waiting']").first
    terminal = page.locator(
        ".sandbox-home li[data-status='succeeded'], "
        ".sandbox-home li[data-status='failed']"
    ).first
    deadline = asyncio.get_running_loop().time() + timeout_ms / 1_000
    while asyncio.get_running_loop().time() < deadline:
        if await waiting.is_visible():
            return waiting
        if await terminal.is_visible():
            status = await terminal.get_attribute("data-status") or "terminal"
            raise RuntimeError(
                "The natural Sandbox request resolved as "
                f"{status} instead of producing ToolRouter clarification."
            )
        await asyncio.sleep(0.1)
    raise TimeoutError(
        "The Sandbox produced neither clarification nor a terminal result."
    )


async def _public_send(page: Page, text: str) -> str:
    content = page.locator(".public-agent article p").last
    previous = await content.inner_text() if await content.is_visible() else ""
    await page.get_by_label("Message", exact=True).fill(text)
    await page.get_by_role("button", name="Send", exact=True).click()
    deadline = asyncio.get_running_loop().time() + 180
    while asyncio.get_running_loop().time() < deadline:
        if await content.is_visible():
            current = await content.inner_text()
            if current.strip() and current != previous:
                return current
        await page.wait_for_timeout(250)
    raise TimeoutError("The deployed Agent did not publish its next response.")


def _observe_horizontal(page: Page, observations: dict, trace: list[dict]) -> None:
    async def observe(response) -> None:
        try:
            path = urlsplit(response.url).path
            if response.request.method != "GET" or response.status != 200:
                return
            if path == "/api/routedeck/inspect":
                body = await response.json()
                _record_chat_inspection(
                    body,
                    observations,
                    trace,
                    record_operations=False,
                )
                return
            if not path.startswith("/api/agents/") and path != "/api/agents":
                return
            body = await response.json()
            key = (
                "agents" if path == "/api/agents" else
                "designs" if path.endswith("/design") else
                "builds" if path.endswith("/runtime-builds") else
                "sandbox" if path.endswith("/sandbox") else
                "evaluations" if path.endswith("/evaluations") else
                "channels" if path.endswith("/channels") else
                "deployments" if path.endswith("/deployments") else
                "operations" if path.endswith("/operations") else None
            )
            if key:
                observations[key].append(body)
                trace.append({"event": "observation", "method": "GET", "path": path, "status": 200})
        except Exception:
            return

    page.on("response", lambda response: asyncio.create_task(observe(response)))


def _chat_operation_evidence(
    inspection: object,
    *,
    prior_inspection: object | None = None,
    current_user_message: str | None = None,
) -> list[dict[str, object]]:
    if not isinstance(inspection, dict):
        return []
    recent = _recent_operation_evidence(inspection)
    durable = _durable_chat_operation_evidence(
        inspection,
        prior_inspection=prior_inspection,
        current_user_message=current_user_message,
    )
    traced: list[dict[str, object]] = []
    history = inspection.get("invocation_traces")
    traces = history.get("traces", []) if isinstance(history, dict) else []
    if current_user_message is not None:
        if not isinstance(prior_inspection, dict):
            raise RuntimeError(
                "Current-turn chat evidence requires the exact pre-turn inspection."
            )
        prior_history = prior_inspection.get("invocation_traces")
        prior_traces = (
            prior_history.get("traces", [])
            if isinstance(prior_history, dict)
            else []
        )
        if not isinstance(traces, list) or not isinstance(prior_traces, list):
            raise RuntimeError("The current-turn invocation trace history is invalid.")
        if prior_traces:
            overlap = next((
                size
                for size in range(min(len(traces), len(prior_traces)), 0, -1)
                if traces[-size:] == prior_traces[:size]
            ), 0)
            if overlap == 0:
                raise RuntimeError(
                    "The invocation trace history changed before the current chat turn."
                )
            dropped = len(prior_traces) - overlap
            retention = history.get("retention_per_session")
            prior_retention = (
                prior_history.get("retention_per_session")
                if isinstance(prior_history, dict)
                else None
            )
            if dropped and not (
                isinstance(retention, int)
                and retention > 0
                and retention == prior_retention
                and len(traces) == retention
            ):
                raise RuntimeError(
                    "The invocation trace history was truncated outside its declared bound."
                )
            traces = list(reversed(traces[:-overlap]))
        else:
            traces = list(reversed(traces))
    for invocation in traces if isinstance(traces, list) else []:
        if not isinstance(invocation, dict):
            continue
        captured = _current_turn_invocation_values(
            invocation,
            current_user_message=current_user_message,
        )
        for payload in _operation_result_payloads(captured):
            operation_id = payload.get("operation_id")
            disposition = payload.get("disposition")
            if not isinstance(operation_id, str) or not isinstance(disposition, str):
                continue
            traced.append(
                {
                    "operationId": operation_id,
                    "disposition": disposition,
                    "outcome": payload.get("outcome"),
                    "sessionVersion": payload.get("session_version"),
                    "projectionVersion": payload.get("projection_version"),
                }
            )
    if current_user_message is not None:
        unique_traced: dict[tuple[object, ...], dict[str, object]] = {}
        for item in traced:
            unique_traced.setdefault(
                (
                    item.get("operationId"),
                    item.get("disposition"),
                    item.get("outcome"),
                    item.get("sessionVersion"),
                    item.get("projectionVersion"),
                ),
                item,
            )
        traced = list(unique_traced.values())
    traced_by_operation: dict[str, list[dict[str, object]]] = {}
    for item in traced:
        traced_by_operation.setdefault(str(item["operationId"]), []).append(item)
    detailed: list[dict[str, object]] = []
    for item in durable:
        operation_id = str(item["operationId"])
        replacements = traced_by_operation.get(operation_id, [])
        detailed.append(replacements.pop(0) if replacements else item)
    if current_user_message is None:
        for replacements in traced_by_operation.values():
            detailed.extend(replacements)
    if recent and detailed:
        # Public session events also contain SURFACE dispatches. They are not
        # chat evidence. Keep only events whose operation identity is present
        # in an actual model tool result, then use the durable event cursor as
        # corroboration. A failed guard still emits OPERATION_CHANGED, so the
        # exact model result remains authoritative for its disposition.
        recent_by_commit = {
            (
                item.get("operationId"),
                item.get("sessionVersion"),
                item.get("projectionVersion"),
            ): item
            for item in recent
        }
        prior_event_ids = {
            item.get("evidenceId")
            for item in (
                _recent_operation_evidence(prior_inspection)
                if isinstance(prior_inspection, dict)
                else []
            )
        }
        prior_durable_ids = {
            item.get("evidenceId")
            for item in (
                _durable_chat_operation_evidence(prior_inspection)
                if isinstance(prior_inspection, dict)
                else []
            )
        }
        new_review_events_by_operation: dict[
            str, list[dict[str, object]]
        ] = {}
        for item in recent:
            if (
                item.get("evidenceId") not in prior_event_ids
                and item.get("disposition") == "requires_review"
            ):
                new_review_events_by_operation.setdefault(
                    str(item["operationId"]), []
                ).append(item)
        consumed_review_operations: set[str] = set()
        correlated: list[dict[str, object]] = []
        for item in detailed:
            commit = (
                item.get("operationId"),
                item.get("sessionVersion"),
                item.get("projectionVersion"),
            )
            exact = recent_by_commit.get(commit)
            if exact is None:
                pending_candidates = new_review_events_by_operation.get(
                    str(item["operationId"]), []
                )
                operation_id = str(item["operationId"])
                if (
                    item.get("sessionVersion") is None
                    and item.get("projectionVersion") is None
                    and isinstance(item.get("evidenceId"), str)
                    and item.get("evidenceId") not in prior_durable_ids
                    and len(pending_candidates) == 1
                    and operation_id not in consumed_review_operations
                ):
                    consumed_review_operations.add(operation_id)
                    correlated.append({**pending_candidates[0], "source": "agent"})
                    continue
                correlated.append({**item, "source": "agent"})
                continue
            merged = {**exact, "source": "agent"}
            if exact.get("disposition") != "requires_review":
                merged.update(
                    disposition=item.get("disposition"),
                    outcome=item.get("outcome"),
                )
            correlated.append(merged)
        unique_correlated: dict[tuple[object, ...], dict[str, object]] = {}
        for item in correlated:
            unique_correlated.setdefault(_chat_evidence_signature(item), item)
        return list(unique_correlated.values())
    evidence = detailed
    unique: dict[tuple[object, ...], dict[str, object]] = {}
    for item in evidence:
        signature = _chat_evidence_signature(item)
        unique.setdefault(signature, item)
    return [{**item, "source": "agent"} for item in unique.values()]


def _current_turn_invocation_values(
    invocation: dict[str, object],
    *,
    current_user_message: str | None,
) -> list[object]:
    if current_user_message is None:
        return [
            stage["value"]
            for stage_name in ("model_boundary_request", "provider_result")
            if isinstance((stage := invocation.get(stage_name)), dict)
            and "value" in stage
        ]
    boundary = invocation.get("model_boundary_request")
    boundary_value = boundary.get("value") if isinstance(boundary, dict) else None
    messages = (
        boundary_value.get("messages")
        if isinstance(boundary_value, dict)
        else None
    )
    if not isinstance(messages, list):
        return []
    current_indices = [
        index
        for index, message in enumerate(messages)
        if isinstance(message, dict)
        and (message.get("role") in {"human", "user"}
             or message.get("type") in {"human", "user"})
        and message.get("content") == current_user_message
    ]
    if not current_indices:
        return []
    current_index = current_indices[-1]
    if any(
        isinstance(message, dict)
        and (message.get("role") in {"human", "user"}
             or message.get("type") in {"human", "user"})
        for message in messages[current_index + 1:]
    ):
        return []
    captured: list[object] = [{
        **boundary_value,
        "messages": messages[current_index + 1:],
    }]
    provider = invocation.get("provider_result")
    if isinstance(provider, dict) and "value" in provider:
        captured.append(provider["value"])
    return captured


def _recent_operation_evidence(
    inspection: dict[str, object],
) -> list[dict[str, object]]:
    values = inspection.get("recent_operations")
    evidence: list[dict[str, object]] = []
    for value in values if isinstance(values, list) else []:
        if not isinstance(value, dict):
            continue
        event_id = value.get("event_id")
        operation_id = value.get("operation_id")
        status_code = value.get("status_code")
        cursor = value.get("cursor")
        if (
            not isinstance(event_id, str)
            or not event_id
            or not isinstance(operation_id, str)
            or not operation_id
            or not isinstance(cursor, int)
        ):
            continue
        evidence.append(
            {
                "operationId": operation_id,
                "evidenceId": event_id,
                "eventCursor": cursor,
                "disposition": (
                    "requires_review"
                    if status_code == "review_pending"
                    else "completed"
                ),
                "outcome": None,
                "sessionVersion": value.get("session_version"),
                "projectionVersion": value.get("projection_version"),
            }
        )
    return evidence


def _chat_evidence_signature(item: dict[str, object]) -> tuple[object, ...]:
    evidence_id = item.get("evidenceId")
    if isinstance(evidence_id, str) and evidence_id:
        return ("durable_tool_turn", evidence_id)
    return (
        "invocation_trace",
        item.get("operationId"),
        item.get("sessionVersion"),
        item.get("projectionVersion"),
    )


def _durable_chat_operation_evidence(
    inspection: dict[str, object],
    *,
    prior_inspection: object | None = None,
    current_user_message: str | None = None,
) -> list[dict[str, object]]:
    context = inspection.get("agent_context")
    if not isinstance(context, dict):
        return []
    messages = context.get("messages")
    if not isinstance(messages, list):
        return []
    selected_messages = messages
    if current_user_message is not None:
        if not isinstance(prior_inspection, dict):
            raise RuntimeError(
                "Current-turn durable evidence requires the exact pre-turn inspection."
            )
        prior_context = prior_inspection.get("agent_context")
        prior_messages = (
            prior_context.get("messages")
            if isinstance(prior_context, dict)
            else None
        )
        if not isinstance(prior_messages, list):
            raise RuntimeError("The pre-turn durable message history is invalid.")
        if messages[:len(prior_messages)] != prior_messages:
            raise RuntimeError(
                "The durable message history changed before the current chat turn."
            )
        new_messages = messages[len(prior_messages):]
        user_indices = [
            index
            for index, message in enumerate(new_messages)
            if isinstance(message, dict)
            and message.get("role") in {"human", "user"}
            and message.get("content") == current_user_message
        ]
        if len(user_indices) != 1:
            raise RuntimeError(
                "The exact current user message was not uniquely durable."
            )
        selected_messages = new_messages[user_indices[0] + 1:]
    tool_names = {
        _provider_safe_operation_name(operation_id): operation_id
        for operation_id in CHAT_EVIDENCE_OPERATION_IDS
    }
    evidence: list[dict[str, object]] = []
    for message in selected_messages:
        if not isinstance(message, dict) or message.get("role") != "tool":
            continue
        evidence_id = message.get("id")
        operation_id = tool_names.get(message.get("name"))
        status = message.get("status")
        if (
            not isinstance(evidence_id, str)
            or not evidence_id
            or not isinstance(operation_id, str)
        ):
            continue
        evidence.append(
            {
                "operationId": operation_id,
                "evidenceId": evidence_id,
                "disposition": (
                    "completed" if status in (None, "success") else "failed"
                ),
                "outcome": None,
                "sessionVersion": None,
                "projectionVersion": None,
            }
        )
    return evidence


def _chat_inspection_tool_shapes(
    inspection: dict[str, object],
) -> list[dict[str, object]]:
    context = inspection.get("agent_context")
    if not isinstance(context, dict):
        return []
    messages = context.get("messages")
    shapes: list[dict[str, object]] = []
    for message in messages if isinstance(messages, list) else []:
        if not isinstance(message, dict) or message.get("role") != "tool":
            continue
        evidence_id = message.get("id")
        name = message.get("name")
        status = message.get("status")
        if not isinstance(evidence_id, str) or not isinstance(name, str):
            continue
        shapes.append(
            {
                "evidenceId": evidence_id,
                "providerSafeName": name,
                "status": status if isinstance(status, str) else None,
            }
        )
    return shapes


async def _contract_review_id(review: Locator) -> str:
    labelled_by = await review.get_attribute("aria-labelledby")
    match = re.fullmatch(
        r"contract-review-(review_[A-Za-z0-9_-]+)", labelled_by or ""
    )
    if match is None:
        raise RuntimeError(
            "The exact contract review ID is unavailable from its visible surface."
        )
    return match.group(1)


def _provider_safe_operation_name(operation_id: str) -> str:
    readable = "".join(
        character
        if character.isascii()
        and (character.isalnum() or character in {"_", "-"})
        else "_"
        for character in operation_id
    ).strip("_-") or "operation"
    digest = hashlib.sha256(operation_id.encode("utf-8")).hexdigest()[:12]
    readable_limit = 64 - len("rd_") - 1 - len(digest)
    return f"rd_{readable[:readable_limit]}_{digest}"


def _operation_result_payloads(value: object) -> list[dict[str, object]]:
    payloads: list[dict[str, object]] = []

    def visit(item: object) -> None:
        if isinstance(item, dict):
            if item.get("type") == "routedeck_operation_result":
                payloads.append(item)
                return
            for nested in item.values():
                visit(nested)
            return
        if isinstance(item, list):
            for nested in item:
                visit(nested)
            return
        if isinstance(item, str) and item.lstrip().startswith("{"):
            try:
                parsed = json.loads(item)
            except (TypeError, ValueError):
                return
            visit(parsed)

    visit(value)
    return payloads


async def _open_chat_evidence_inspector(
    page: Page,
    trace: list[dict[str, object]],
) -> None:
    opener = page.get_by_role(
        "button", name="Open docked Navgraph", exact=True
    )
    await opener.wait_for(state="visible", timeout=30_000)
    await opener.click()
    await _refresh_chat_evidence_inspector(page, trace)


async def _refresh_chat_evidence_inspector(
    page: Page,
    trace: list[dict[str, object]],
):
    region = page.get_by_role(
        "region", name="Invocation traces", exact=True
    )
    if not await region.is_visible():
        tab = page.get_by_role(
            "button", name="Invocation trace", exact=True
        )
        if not await tab.is_visible():
            opener = page.get_by_role(
                "button", name="Open docked Navgraph", exact=True
            )
            await opener.wait_for(state="visible", timeout=30_000)
            await opener.click()
        await tab.wait_for(state="visible", timeout=30_000)
        await tab.click()
    await region.wait_for(state="visible", timeout=30_000)
    refresh = region.get_by_role("button", name="Refresh", exact=True)
    async with page.expect_response(
        lambda response: (
            response.request.method == "GET"
            and urlsplit(response.url).path == "/api/routedeck/inspect"
            and response.status == 200
        ),
        timeout=30_000,
    ) as pending_inspection:
        await refresh.click()
    inspection_response = await pending_inspection.value
    snapshot = await inspection_response.json()
    if not isinstance(snapshot, dict):
        raise RuntimeError("The authenticated RouteDeck inspection was invalid.")
    _record_chat_inspection(snapshot, None, trace)
    return inspection_response


async def _load_authenticated_chat_inspection(
    page: Page,
    authenticated_response,
    *,
    backend_url: str,
) -> dict[str, object]:
    request_headers = await authenticated_response.request.all_headers()
    authorization = request_headers.get("authorization")
    if not isinstance(authorization, str) or not authorization.startswith("Bearer "):
        raise RuntimeError("The authenticated RouteDeck inspection bearer is unavailable.")
    conversation_id = request_headers.get("x-corpus-conversation-id")
    if not isinstance(conversation_id, str) or not conversation_id:
        raise RuntimeError("The authenticated Corpus conversation selector is unavailable.")
    response = await page.context.request.get(
        urljoin(f"{backend_url.rstrip('/')}/", "api/routedeck/inspect"),
        headers={
            "Authorization": authorization,
            "X-Corpus-Conversation-ID": conversation_id,
            "Accept": "application/json",
            "Cache-Control": "no-cache",
        },
        fail_on_status_code=True,
    )
    snapshot = await response.json()
    if not isinstance(snapshot, dict):
        raise RuntimeError("The authenticated RouteDeck inspection was invalid.")
    return snapshot


def _durable_chat_message(message: str, attachment_name: str | None) -> str:
    if attachment_name is None:
        return message
    return (
        f'{message}\n\nI attached the API definition "{attachment_name}" '
        "to this conversation."
    )


def _terminal_assistant_content(
    before: object,
    after: object,
    message: str,
) -> str:
    if not isinstance(before, dict) or not isinstance(after, dict):
        raise RuntimeError("The chat inspection cannot prove the assistant response.")
    before_context = before.get("agent_context")
    after_context = after.get("agent_context")
    if not isinstance(before_context, dict) or not isinstance(after_context, dict):
        raise RuntimeError("The chat inspection has no durable Agent context.")
    before_messages = before_context.get("messages")
    after_messages = after_context.get("messages")
    if not isinstance(before_messages, list) or not isinstance(after_messages, list):
        raise RuntimeError("The chat inspection has no durable message history.")
    new_messages = after_messages[len(before_messages):]
    user_index = next((
        index
        for index, item in enumerate(new_messages)
        if isinstance(item, dict)
        and item.get("role") in {"human", "user"}
        and item.get("content") == message
    ), None)
    if user_index is None:
        raise RuntimeError("The exact owner message is absent from durable chat history.")
    assistant_messages = [
        str(item["content"]).strip()
        for item in new_messages[user_index + 1:]
        if isinstance(item, dict)
        and item.get("role") in {"ai", "assistant"}
        and isinstance(item.get("content"), str)
        and bool(str(item["content"]).strip())
    ]
    if not assistant_messages:
        raise RuntimeError("The exact chat turn has no terminal assistant response.")
    return assistant_messages[-1]


def _inspection_has_terminal_chat_turn(
    before: object,
    after: object,
    message: str,
) -> bool:
    if not isinstance(before, dict) or not isinstance(after, dict):
        return False
    before_context = before.get("agent_context")
    after_context = after.get("agent_context")
    if not isinstance(before_context, dict) or not isinstance(after_context, dict):
        return False
    before_snapshot = before_context.get("snapshot")
    after_snapshot = after_context.get("snapshot")
    before_messages = before_context.get("messages")
    after_messages = after_context.get("messages")
    if (
        not isinstance(before_snapshot, dict)
        or not isinstance(after_snapshot, dict)
        or not isinstance(before_messages, list)
        or not isinstance(after_messages, list)
    ):
        return False
    before_version = before_snapshot.get("session_version")
    after_version = after_snapshot.get("session_version")
    if (
        not isinstance(before_version, int)
        or not isinstance(after_version, int)
        or after_version <= before_version
        or after_snapshot.get("interaction_phase") != "idle"
        or len(after_messages) <= len(before_messages)
    ):
        return False
    new_messages = after_messages[len(before_messages):]
    user_index = next((
        index
        for index, item in enumerate(new_messages)
        if isinstance(item, dict)
        and item.get("role") in {"human", "user"}
        and item.get("content") == message
    ), None)
    if user_index is None:
        return False
    return any(
        isinstance(item, dict)
        and item.get("role") in {"ai", "assistant"}
        and isinstance(item.get("content"), str)
        and bool(item["content"].strip())
        for item in new_messages[user_index + 1:]
    )


async def _wait_for_inspected_chat_turn(
    page: Page,
    authenticated_response,
    before_inspection: dict[str, object],
    message: str,
    *,
    backend_url: str,
) -> dict[str, object]:
    deadline = asyncio.get_running_loop().time() + 360
    while asyncio.get_running_loop().time() < deadline:
        snapshot = await _load_authenticated_chat_inspection(
            page,
            authenticated_response,
            backend_url=backend_url,
        )
        if _inspection_has_terminal_chat_turn(before_inspection, snapshot, message):
            return snapshot
        if await page.locator("[data-agent-chat-error]").count() > 0:
            raise RuntimeError(
                "Corpus reported a chat failure before the exact turn became durable."
            )
        await asyncio.sleep(0.5)
    raise TimeoutError(
        "The exact user chat turn did not become durably idle with a terminal response."
    )


def _record_chat_inspection(
    inspection: object,
    observations: dict[str, object] | None,
    trace: list[dict[str, object]],
    *,
    prior_inspection: object | None = None,
    current_user_message: str | None = None,
    record_operations: bool = True,
) -> None:
    observed_tools = (
        observations.get("chatInspectionTools", [])
        if observations is not None
        else []
    )
    if not isinstance(observed_tools, list):
        raise RuntimeError("The chat inspection tool evidence store is invalid.")
    known_tool_ids = {
        item.get("evidenceId")
        for item in observed_tools
        if isinstance(item, dict)
    }
    for tool in _chat_inspection_tool_shapes(inspection):
        if tool["evidenceId"] not in known_tool_ids:
            known_tool_ids.add(tool["evidenceId"])
            observed_tools.append(tool)

    if not record_operations:
        return

    observed_operations = (
        observations.get("chatOperations", [])
        if observations is not None
        else []
    )
    if not isinstance(observed_operations, list):
        raise RuntimeError("The chat operation evidence store is invalid.")
    known_trace = {
        _chat_evidence_signature(item)
        for item in trace
        if item.get("event") == "chat_operation"
    }
    known_observations = {
        _chat_evidence_signature(item)
        for item in observed_operations
        if isinstance(item, dict)
    }
    for evidence in _chat_operation_evidence(
        inspection,
        prior_inspection=prior_inspection,
        current_user_message=current_user_message,
    ):
        signature = _chat_evidence_signature(evidence)
        if signature not in known_observations:
            known_observations.add(signature)
            observed_operations.append(evidence)
        if signature in known_trace:
            continue
        known_trace.add(signature)
        sequence = max(
            (int(item.get("sequence", 0)) for item in trace),
            default=0,
        ) + 1
        event = {
            "sequence": sequence,
            "page": "horizontal",
            "event": "chat_operation",
            **evidence,
        }
        trace.append(event)
        if observations is not None:
            observations["sequence"] = sequence


def _attach_public_diagnostics(page: Page, diagnostics, trace) -> None:
    def response_observer(response) -> None:
        path = urlsplit(response.url).path
        trace.append({"event": "response", "page": "public", "method": response.request.method, "path": path, "status": response.status})
        if response.status >= 400:
            diagnostics["httpErrors"].append({"method": response.request.method, "path": path, "status": response.status})

    page.on("response", response_observer)
    page.on("console", lambda item: diagnostics["consoleErrors"].append({"type": item.type, "text": item.text[:240]}) if item.type == "error" else None)
    page.on("pageerror", lambda error: diagnostics["pageErrors"].append({"message": str(error)[:240]}))


async def _latest_agent_id(observations: dict) -> str:
    for _ in range(100):
        for body in reversed(observations["agents"]):
            values = body.get("agents", []) if isinstance(body, dict) else []
            if values:
                return str(values[0]["id"])
        await asyncio.sleep(0.1)
    return ""


async def _latest_build_id(observations: dict) -> str:
    for _ in range(100):
        for body in reversed(observations["builds"]):
            values = body.get("builds", []) if isinstance(body, dict) else []
            ready = [item for item in values if item.get("status") == "ready"]
            if ready:
                return str(ready[0]["id"])
        await asyncio.sleep(0.1)
    return ""


async def _latest_sandbox_id(observations: dict) -> str:
    for _ in range(100):
        for body in reversed(observations["sandbox"]):
            values = body.get("runs", []) if isinstance(body, dict) else []
            succeeded = [item for item in values if item.get("status") == "succeeded"]
            if succeeded:
                return str(succeeded[0]["id"])
        await asyncio.sleep(0.1)
    return ""


async def _latest_build_request_id(observations: dict) -> str:
    for _ in range(300):
        for body in reversed(observations["designs"]):
            if not isinstance(body, dict):
                continue
            request = body.get("build_request")
            if isinstance(request, dict) and request.get("id"):
                return str(request["id"])
        await asyncio.sleep(0.1)
    raise TimeoutError("The exact accepted design build request was not observed.")


async def _latest_evaluation_case_id(observations: dict) -> str:
    for _ in range(300):
        for body in reversed(observations["evaluations"]):
            sets = body.get("evaluation_sets", []) if isinstance(body, dict) else []
            for item in reversed(sets):
                cases = item.get("cases", []) if isinstance(item, dict) else []
                if cases:
                    return str(cases[-1]["id"])
        await asyncio.sleep(0.1)
    raise TimeoutError("The exact evaluation case was not observed.")


async def _latest_channel_id(observations: dict) -> str:
    for _ in range(300):
        for body in reversed(observations["channels"]):
            channels = body.get("channels", []) if isinstance(body, dict) else []
            if channels:
                return str(channels[0]["id"])
        await asyncio.sleep(0.1)
    raise TimeoutError("The exact hosted channel was not observed.")


async def _prove_split_surface(
    page: Page,
    directory: Path,
    output: list[str],
) -> bool:
    maximize = page.get_by_role("button", name="Maximize surface", exact=True)
    await maximize.wait_for(state="visible", timeout=30_000)
    await maximize.click()
    shell = page.locator("[data-agent-shell]")
    await shell.locator("[data-agent-conversation]").wait_for(
        state="visible", timeout=30_000
    )
    await shell.locator("[data-agent-surface-dock]").wait_for(
        state="visible", timeout=30_000
    )
    split = await shell.get_attribute("data-surface-layout") == "split"
    await _capture(page, directory, output, "01b-source-chat-split")
    await page.get_by_role("button", name="Return to dock", exact=True).click()
    docked = await shell.get_attribute("data-surface-layout") == "dock"
    return split and docked


async def _capture(page: Page, directory: Path, output: list[str], name: str) -> None:
    path = directory / f"{name}.png"
    # Keep the raw, unprocessed recording at normal speed while giving a
    # reviewer enough time to read each architecture/product proof state.
    await page.wait_for_timeout(2_500)
    await page.screenshot(path=path, full_page=False)
    await page.wait_for_timeout(2_500)
    output.append(str(path.relative_to(REPOSITORY_ROOT)))


async def _type_exact(locator: Locator, value: str, label: str) -> None:
    await locator.click()
    await locator.press("Control+A")
    await locator.press("Backspace")
    await locator.press_sequentially(value, delay=25)
    if await locator.input_value() != value:
        raise RuntimeError(f"The exact {label} was not bound to the form.")
    # Preserve a normal-speed review pause in the continuous raw recording.
    await asyncio.sleep(1.5)


def _hybrid_chat_ledger_is_coherent(
    events: list[dict[str, object]],
    *,
    expected_conversation_id: str,
) -> bool:
    if not events or not expected_conversation_id:
        return False
    seen_requests: set[tuple[str, str]] = set()
    for event in events:
        message = event.get("message")
        operation_id = event.get("operationId")
        if (
            event.get("conversationId") != expected_conversation_id
            or not isinstance(message, str)
            or not message
            or not isinstance(operation_id, str)
            or not operation_id
        ):
            return False
        request_operation = (message, operation_id)
        if request_operation in seen_requests:
            return False
        seen_requests.add(request_operation)
    return True


def _check(checks: list[dict[str, object]], name: str, passed: bool, observed) -> None:
    checks.append({"name": name, "passed": bool(passed), "observed": observed})
    if not passed:
        raise RuntimeError(name)


async def _classify_operations(
    panel,
    operation_ids: set[str],
    included: frozenset[str],
) -> None:
    if not operation_ids:
        raise RuntimeError("The exact curation inventory is empty.")
    missing = included - operation_ids
    if missing:
        raise RuntimeError(
            "The requested exact curation operations are unavailable: "
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


def _restart_runtime(backend_url: str) -> None:
    previous_backend_generation = _compose_service_generation("backend")
    previous_worker_generation = _compose_service_generation("source-worker")
    if previous_backend_generation is None or previous_worker_generation is None:
        raise RuntimeError("The current Corpus runtime generation is unavailable.")
    for command in (
        ["docker", "compose", "stop", "--timeout", "60", "backend", "source-worker"],
        ["docker", "compose", "up", "-d", "backend", "source-worker"],
    ):
        completed = subprocess.run(
            command,
            cwd=REPOSITORY_ROOT,
            text=True,
            capture_output=True,
            timeout=120,
            check=False,
        )
        if completed.returncode != 0:
            raise RuntimeError("The local Corpus runtime restart failed.")
    _wait_for_runtime_generation(
        backend_url,
        previous_backend_generation=previous_backend_generation,
        previous_worker_generation=previous_worker_generation,
    )


def _compose_service_generation(service: str) -> str | None:
    selected = subprocess.run(
        ["docker", "compose", "ps", "-q", service],
        cwd=REPOSITORY_ROOT,
        text=True,
        capture_output=True,
        timeout=30,
        check=False,
    )
    container_ids = tuple(
        line.strip() for line in selected.stdout.splitlines() if line.strip()
    )
    if selected.returncode != 0 or len(container_ids) != 1:
        return None
    inspected = subprocess.run(
        [
            "docker",
            "inspect",
            container_ids[0],
            "--format",
            "{{.State.StartedAt}}|{{.State.Running}}|{{.State.Restarting}}",
        ],
        cwd=REPOSITORY_ROOT,
        text=True,
        capture_output=True,
        timeout=30,
        check=False,
    )
    if inspected.returncode != 0:
        return None
    values = inspected.stdout.strip().split("|")
    if len(values) != 3 or values[1:] != ["true", "false"] or not values[0]:
        return None
    return values[0]


def _wait_for_runtime_generation(
    base_url: str,
    *,
    previous_backend_generation: str,
    previous_worker_generation: str,
    timeout_seconds: float = 240,
    poll_seconds: float = 1,
    required_ready_successes: int = 3,
) -> None:
    deadline = time.monotonic() + timeout_seconds
    consecutive_ready = 0
    observed_generation: tuple[str, str] | None = None
    target = base_url.rstrip("/") + "/readyz"
    while time.monotonic() < deadline:
        backend_generation = _compose_service_generation("backend")
        worker_generation = _compose_service_generation("source-worker")
        current_generation = (
            backend_generation,
            worker_generation,
        )
        generations_are_new = (
            backend_generation is not None
            and worker_generation is not None
            and backend_generation != previous_backend_generation
            and worker_generation != previous_worker_generation
        )
        ready = False
        if generations_are_new:
            try:
                with urlopen(target, timeout=5) as response:
                    ready = response.status == 200
            except Exception:
                ready = False
        if ready and current_generation == observed_generation:
            consecutive_ready += 1
        elif ready:
            observed_generation = current_generation
            consecutive_ready = 1
        else:
            observed_generation = current_generation if generations_are_new else None
            consecutive_ready = 0
        if consecutive_ready >= required_ready_successes:
            return
        time.sleep(poll_seconds)
    raise RuntimeError(
        "Corpus backend and Source worker did not reach a new stable runtime generation."
    )


def _runtime_model_provider() -> str:
    completed = subprocess.run(
        [
            "docker", "inspect", "corpus-development-backend-1",
            "--format", "{{range .Config.Env}}{{println .}}{{end}}",
        ],
        cwd=REPOSITORY_ROOT,
        text=True,
        capture_output=True,
        timeout=30,
        check=False,
    )
    if completed.returncode != 0:
        raise RuntimeError("The local Corpus model provider is unavailable.")
    values = tuple(
        line.split("=", 1)[1]
        for line in completed.stdout.splitlines()
        if line.startswith("CORPUS_MODEL_PROVIDER=")
    )
    if len(values) != 1 or values[0] not in {"ollama", "openai"}:
        raise RuntimeError("The local Corpus model provider identity is invalid.")
    return values[0]


def _wait_ready(
    base_url: str,
    *,
    timeout_seconds: float = 240,
    poll_seconds: float = 1,
    required_ready_successes: int = 3,
) -> None:
    deadline = time.monotonic() + timeout_seconds
    target = base_url.rstrip("/") + "/readyz"
    consecutive_ready = 0
    while time.monotonic() < deadline:
        try:
            with urlopen(target, timeout=5) as response:
                if response.status == 200:
                    consecutive_ready += 1
                    if consecutive_ready >= required_ready_successes:
                        return
                else:
                    consecutive_ready = 0
        except Exception:
            consecutive_ready = 0
        time.sleep(poll_seconds)
    raise RuntimeError("Corpus did not remain stably ready after restart.")


if __name__ == "__main__":
    asyncio.run(main())
