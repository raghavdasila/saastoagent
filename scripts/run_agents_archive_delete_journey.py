from __future__ import annotations

import argparse
import asyncio
import json
import re
import shutil
import subprocess
import time
from collections import Counter
from collections.abc import Iterable
from datetime import UTC, datetime
from pathlib import Path
from urllib.parse import urlparse
from urllib.request import urlopen
from uuid import uuid4

from playwright.async_api import Error as PlaywrightError
from playwright.async_api import Locator, Page, TimeoutError as PlaywrightTimeoutError, async_playwright


OPENAPI = """openapi: 3.0.3
info: {title: Agent Lifecycle Guard API, version: 1.0.0}
servers: [{url: 'http://host.docker.internal:9000'}]
paths:
  /products:
    get:
      operationId: listProducts
      responses:
        '200': {description: Product list}
"""

AGENT_NAMES = {
    "archiveAgentId": "Archive Agent",
    "deleteAgentId": "Delete Agent",
    "blockedAgentId": "Blocked Agent",
    "raceAgentId": "Race Agent",
}
AGENTS_HOME_TITLE_SELECTOR = ".agents-home #agents-home-title"

JOURNEY_STEPS = (
    "create_agents",
    "archive_stage",
    "archive_reload",
    "archive_accept",
    "delete_stage_reject",
    "delete_stage_accept",
    "create_ready_source_and_attach_blocked",
    "dependency_guard_block",
    "race_stage",
    "race_attach_in_second_conversation",
    "race_accept_stale",
    "restart_persistence",
)

REQUIRED_ID_KEYS = (
    *AGENT_NAMES.keys(),
    "sourceId",
    "sourceRevisionId",
    "sourceJobId",
    "primaryConversationId",
    "raceConversationId",
)


class AgentInventory:
    """Locators owned by the active Agents inventory surface."""

    def __init__(self, page: Page) -> None:
        self.root = page.locator('.agents-home aside[aria-label="Agent inventory"]')

    def agent(self, name: str) -> Locator:
        return self.root.get_by_role("button", name=f"{name} Version 1", exact=True)


class AgentSourcesPanel:
    """Locators owned by the selected Agent's Source attachment panel."""

    def __init__(self, page: Page) -> None:
        self.root = page.locator(".agents-home .agent-sources")
        self.heading = self.root.get_by_role("heading", name="Attached Sources", exact=True)
        self.create_and_attach = self.root.get_by_role(
            "button", name="Create and attach", exact=True
        )
        self.ready_source = self.root.get_by_label("Ready Workspace Source", exact=True)
        self.attach_source = self.root.get_by_role("button", name="Attach Source", exact=True)

    def source(self, name: str) -> Locator:
        return self.root.get_by_text(name, exact=True)


class AgentLifecycleControls:
    """Locators owned by the selected Agent's lifecycle controls."""

    def __init__(self, page: Page) -> None:
        self.root = page.locator(".agents-home .agent-lifecycle")
        self.heading = self.root.get_by_role("heading", name="Agent lifecycle", exact=True)
        self.archive = self.root.get_by_role("button", name="Archive Agent", exact=True)
        self.delete = self.root.get_by_role(
            "button", name="Delete permanently", exact=True
        )
        self.blocker = self.root.get_by_text(
            "Delete blocked: 1 Source attachment remains.", exact=True
        )


class AgentLifecycleReview:
    """Locators owned by one exact projected lifecycle review surface."""

    def __init__(self, page: Page, action: str) -> None:
        if action == "archive":
            heading_name = "Confirm archive"
            accept_name = "Archive Agent"
        elif action == "delete":
            heading_name = "Confirm permanent deletion"
            accept_name = "Delete Agent permanently"
        else:
            raise ValueError(f"Unsupported lifecycle review action: {action}")
        heading = page.get_by_role("heading", name=heading_name, exact=True)
        self.root = page.locator(".agent-lifecycle-review").filter(has=heading)
        self.heading = self.root.get_by_role("heading", name=heading_name, exact=True)
        self.accept = self.root.get_by_role("button", name=accept_name, exact=True)
        self.reject = self.root.get_by_role(
            "button", name="Keep Agent unchanged", exact=True
        )


def arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--url", default="http://127.0.0.1:5199")
    parser.add_argument("--backend-url", default="http://127.0.0.1:8099")
    parser.add_argument("--headed", action="store_true")
    return parser.parse_args()


async def run(args: argparse.Namespace) -> int:
    repository = Path(__file__).resolve().parents[1]
    run_id = datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ") + "-" + uuid4().hex[:10]
    directory = repository / "artifacts" / "agents-archive-delete" / run_id
    videos = directory / "videos"
    videos.mkdir(parents=True)
    definition = directory / "agent-lifecycle-guard.yaml"
    definition.write_text(OPENAPI, encoding="utf-8", newline="\n")

    screenshots: list[str] = []
    checks: list[dict[str, object]] = []
    diagnostics: dict[str, list[dict[str, object]]] = {
        "httpErrors": [],
        "expectedHttpOutcomes": [],
        "consoleErrors": [],
        "expectedConsoleErrors": [],
        "pageErrors": [],
        "requestFailures": [],
        "expectedAbortedRequests": [],
        "routeDeckResults": [],
        "productObservations": [],
        "chronologicalTrace": [],
    }
    ids: dict[str, str | None] = {key: None for key in REQUIRED_ID_KEYS}
    ids.update({
        "archiveReviewId": None,
        "deleteRejectedReviewId": None,
        "deleteAcceptedReviewId": None,
        "raceReviewId": None,
    })
    error: str | None = None
    trace = directory / "corpus-trace.json"
    video_paths: dict[str, str | None] = {"primary": None, "raceConversation": None}
    assembled_video: str | None = None
    video_assembly: dict[str, object] = {
        "status": "not_attempted",
        "primaryRaceStartSeconds": None,
        "primaryRaceEndSeconds": None,
        "command": None,
        "manifest": None,
    }
    account_email = f"agents-lifecycle-{uuid4().hex}@example.com"
    account_password = f"Corpus-Agents-{uuid4().hex}!7"

    try:
        async with async_playwright() as playwright:
            browser = await playwright.chromium.launch(headless=not args.headed)
            context = await browser.new_context(
                viewport={"width": 1440, "height": 1000},
                record_video_dir=videos,
                record_video_size={"width": 1440, "height": 1000},
            )
            primary = await context.new_page()
            primary_video_clock = time.monotonic()
            attach_diagnostics(primary, "primary", diagnostics, ids)
            race_page: Page | None = None
            try:
                await register(primary, args.url, account_email, account_password)
                ids["primaryConversationId"] = await selected_conversation_id(primary)
                await open_agents(primary)

                for name in AGENT_NAMES.values():
                    await create_agent(primary, name)
                await assert_agents_present(primary, AGENT_NAMES.values())
                record(checks, "four lifecycle Agents are created through the real surface", True)

                await select_agent(primary, "Archive Agent")
                lifecycle = AgentLifecycleControls(primary)
                await capture_bound_state(
                    primary,
                    repository,
                    directory,
                    screenshots,
                    checks,
                    "01-lifecycle-controls",
                    lifecycle.root,
                    {
                        "heading": lifecycle.heading,
                        "archive": lifecycle.archive,
                        "delete": lifecycle.delete,
                    },
                )
                await lifecycle.archive.click()
                archive_review = AgentLifecycleReview(primary, "archive")
                await archive_review.heading.wait_for()
                ids["archiveReviewId"] = await review_id(archive_review.heading)
                await capture_desktop(primary, repository, directory, screenshots, "02-archive-review-pending")

                await primary.reload()
                archive_review = AgentLifecycleReview(primary, "archive")
                await archive_review.heading.wait_for(timeout=30_000)
                reloaded_review_id = await review_id(archive_review.heading)
                record(
                    checks,
                    "exact archive review survives reload",
                    reloaded_review_id == ids["archiveReviewId"],
                    {"before": ids["archiveReviewId"], "after": reloaded_review_id},
                )
                await capture_bound_state(
                    primary,
                    repository,
                    directory,
                    screenshots,
                    checks,
                    "03-archive-review-reloaded",
                    archive_review.root,
                    {
                        "heading": archive_review.heading,
                        "accept": archive_review.accept,
                        "reject": archive_review.reject,
                    },
                )
                await archive_review.accept.click()
                await archive_review.heading.wait_for(state="detached", timeout=30_000)
                await assert_agent_absent(primary, "Archive Agent")
                record(checks, "accepted archive removes Agent from active inventory", True)

                await select_agent(primary, "Delete Agent")
                lifecycle = AgentLifecycleControls(primary)
                await lifecycle.delete.click()
                delete_review = AgentLifecycleReview(primary, "delete")
                await delete_review.heading.wait_for()
                ids["deleteRejectedReviewId"] = await review_id(delete_review.heading)
                await capture_bound_state(
                    primary,
                    repository,
                    directory,
                    screenshots,
                    checks,
                    "04-delete-review-reject",
                    delete_review.root,
                    {
                        "heading": delete_review.heading,
                        "accept": delete_review.accept,
                        "reject": delete_review.reject,
                    },
                )
                await delete_review.reject.click()
                await delete_review.heading.wait_for(state="detached", timeout=30_000)
                await assert_agent_present(primary, "Delete Agent")
                record(checks, "rejected delete leaves Agent unchanged", True)

                await select_agent(primary, "Delete Agent")
                lifecycle = AgentLifecycleControls(primary)
                await lifecycle.delete.click()
                delete_review = AgentLifecycleReview(primary, "delete")
                await delete_review.heading.wait_for()
                ids["deleteAcceptedReviewId"] = await review_id(delete_review.heading)
                record(
                    checks,
                    "delete retry stages a fresh review",
                    ids["deleteAcceptedReviewId"] != ids["deleteRejectedReviewId"],
                    {
                        "rejected": ids["deleteRejectedReviewId"],
                        "accepted": ids["deleteAcceptedReviewId"],
                    },
                )
                await delete_review.accept.click()
                await delete_review.heading.wait_for(state="detached", timeout=30_000)
                await assert_agent_absent(primary, "Delete Agent")
                record(checks, "accepted delete removes Agent", True)

                await select_agent(primary, "Blocked Agent")
                await create_ready_source_and_attach(
                    primary,
                    definition,
                    "Lifecycle Guard Source",
                )
                await wait_for_ids(ids, ("sourceId", "sourceRevisionId", "sourceJobId"))
                record(
                    checks,
                    "actual Source Hub worker exposes exact Source revision and job identities",
                    _ids_complete(ids, ("sourceId", "sourceRevisionId", "sourceJobId")),
                    {key: ids[key] for key in ("sourceId", "sourceRevisionId", "sourceJobId")},
                )
                lifecycle = AgentLifecycleControls(primary)
                await lifecycle.blocker.wait_for(timeout=30_000)
                await capture_bound_state(
                    primary,
                    repository,
                    directory,
                    screenshots,
                    checks,
                    "05-dependency-blocker",
                    lifecycle.root,
                    {
                        "blocker": lifecycle.blocker,
                        "archive": lifecycle.archive,
                        "delete": lifecycle.delete,
                    },
                )
                await lifecycle.delete.click()
                dependency_alert = primary.locator(".agents-home").get_by_role("alert").filter(
                    has_text=re.compile("Delete is blocked by 1 Source attachment", re.I)
                )
                await dependency_alert.wait_for(timeout=30_000)
                await assert_agent_present(primary, "Blocked Agent")
                await AgentSourcesPanel(primary).source("Lifecycle Guard Source").wait_for()
                record(
                    checks,
                    "explicit delete dispatch reaches dependency guard without review or mutation",
                    await AgentLifecycleReview(primary, "delete").root.count() == 0,
                )

                await select_agent(primary, "Race Agent")
                lifecycle = AgentLifecycleControls(primary)
                await lifecycle.delete.click()
                race_review = AgentLifecycleReview(primary, "delete")
                await race_review.heading.wait_for()
                ids["raceReviewId"] = await review_id(race_review.heading)

                race_page = await context.new_page()
                video_assembly["primaryRaceStartSeconds"] = round(
                    time.monotonic() - primary_video_clock, 3
                )
                attach_diagnostics(race_page, "race-conversation", diagnostics, ids)
                await race_page.goto(args.url)
                await race_page.get_by_label("Sign out", exact=True).wait_for(timeout=30_000)
                inherited = await selected_conversation_id(race_page)
                await race_page.get_by_role("button", name="New conversation", exact=True).click()
                await race_page.wait_for_function(
                    "([key, previous]) => sessionStorage.getItem(key) !== previous",
                    arg=["corpus.selected-conversation.v1", inherited],
                    timeout=30_000,
                )
                ids["raceConversationId"] = await selected_conversation_id(race_page)
                record(
                    checks,
                    "race uses a distinct authenticated Corpus conversation",
                    ids["raceConversationId"] not in {None, ids["primaryConversationId"]},
                    {
                        "primary": ids["primaryConversationId"],
                        "race": ids["raceConversationId"],
                    },
                )
                await open_agents(race_page)
                await select_agent(race_page, "Race Agent")
                race_sources = AgentSourcesPanel(race_page)
                await race_sources.ready_source.select_option(
                    label="Lifecycle Guard Source"
                )
                await race_sources.attach_source.click()
                await race_sources.source("Lifecycle Guard Source").wait_for(timeout=30_000)
                await AgentLifecycleControls(race_page).blocker.wait_for()
                video_assembly["primaryRaceEndSeconds"] = round(
                    time.monotonic() - primary_video_clock, 3
                )
                record(checks, "second conversation attaches the ready Source through product UI", True)

                await primary.bring_to_front()
                await race_review.accept.click()
                stale_alert = primary.locator(".agents-home").get_by_role("alert").filter(
                    has_text=re.compile(
                        "authoritative facts changed|reviewed operation.*(changed|no longer current)|review.*(stale|changed|no longer current)|dependencies changed",
                        re.I,
                    )
                )
                await stale_alert.wait_for(timeout=30_000)
                await capture_desktop(primary, repository, directory, screenshots, "06-race-review-stale")
                record(
                    checks,
                    "stale review failure is visible and returned by RouteDeck",
                    route_deck_failure_seen(diagnostics, "review_stale"),
                )
                await primary.reload()
                await open_agents(primary)
                await select_agent(primary, "Race Agent")
                await AgentSourcesPanel(primary).source("Lifecycle Guard Source").wait_for(timeout=30_000)
                record(checks, "stale review preserves Race Agent and Source attachment", True)

                await primary.set_viewport_size({"width": 1440, "height": 1000})
                compose(repository, "restart", "backend")
                wait_ready(args.backend_url.rstrip("/") + "/readyz", 90)
                await primary.reload()
                await open_agents(primary)
                await assert_agent_absent(primary, "Archive Agent")
                await assert_agent_absent(primary, "Delete Agent")
                await assert_agents_present(primary, ("Blocked Agent", "Race Agent"))
                await select_agent(primary, "Race Agent")
                await AgentSourcesPanel(primary).source("Lifecycle Guard Source").wait_for(timeout=30_000)
                await capture_desktop(primary, repository, directory, screenshots, "07-restart-persistence")
                record(
                    checks,
                    "archive/delete absence and blocked/race preservation survive backend restart",
                    True,
                )
            except Exception as caught:
                error = f"{type(caught).__name__}: {caught}"
                try:
                    await capture_desktop(
                        primary, repository, directory, screenshots, "99-failure-state"
                    )
                except Exception:
                    pass
            finally:
                if race_page is not None:
                    race_video = race_page.video
                    await race_page.close()
                    if race_video is not None:
                        video_paths["raceConversation"] = await save_video(
                            race_video,
                            repository,
                            directory / "race-conversation-supplement.webm",
                        )
                primary_video = primary.video
                await primary.close()
                if primary_video is not None:
                    video_paths["primary"] = await save_video(
                        primary_video,
                        repository,
                        directory / "agents-archive-delete-continuous.webm",
                    )
                await context.close()
                await browser.close()
                if (
                    video_paths["primary"] is not None
                    and video_paths["raceConversation"] is not None
                    and isinstance(video_assembly["primaryRaceStartSeconds"], float)
                    and isinstance(video_assembly["primaryRaceEndSeconds"], float)
                ):
                    assembled_video, video_assembly = assemble_chronological_video(
                        repository=repository,
                        directory=directory,
                        primary=repository / video_paths["primary"],
                        secondary=repository / video_paths["raceConversation"],
                        race_start=video_assembly["primaryRaceStartSeconds"],
                        race_end=video_assembly["primaryRaceEndSeconds"],
                    )
    except Exception as caught:
        if error is None:
            error = f"{type(caught).__name__}: {caught}"

    classify_expected_console_errors(diagnostics)
    write_corpus_trace(trace, run_id, diagnostics)
    record(
        checks,
        "all required product identities were observed",
        _ids_complete(ids, REQUIRED_ID_KEYS),
        {key: ids[key] for key in REQUIRED_ID_KEYS},
    )
    for diagnostic_key in (
        "httpErrors",
        "consoleErrors",
        "pageErrors",
        "requestFailures",
    ):
        record(
            checks,
            f"no unexpected {diagnostic_key}",
            len(diagnostics[diagnostic_key]) == 0,
            diagnostics[diagnostic_key],
        )
    passed = (
        error is None
        and bool(checks)
        and all(bool(check["passed"]) for check in checks)
        and assembled_video is not None
        and trace.exists()
    )
    result = {
        "runId": run_id,
        "status": "passed" if passed else "failed",
        "url": args.url,
        "backendUrl": args.backend_url,
        "account": {"email": account_email, "freshAccount": True},
        "journeySteps": list(JOURNEY_STEPS),
        "commands": {
            "recorder": (
                f".\\.venv\\Scripts\\python.exe scripts\\run_agents_archive_delete_journey.py "
                f"--url {args.url} --backend-url {args.backend_url}"
            ),
            "backendRestart": "docker compose restart backend",
        },
        "smokeTestUrls": {
            "frontend": args.url.rstrip("/") + "/",
            "backendReadiness": args.backend_url.rstrip("/") + "/readyz",
        },
        "identities": ids,
        "screenshots": screenshots,
        "video": assembled_video,
        "rawVideos": [value for value in video_paths.values() if value is not None],
        "videoAssembly": video_assembly,
        "trace": str(trace.relative_to(repository)) if trace.exists() else None,
        "checks": checks,
        "diagnostics": diagnostics,
        "restart": {
            "command": "docker compose restart backend",
            "readinessUrl": args.backend_url.rstrip("/") + "/readyz",
        },
        "limitations": [
            "This surface-led journey does not claim chat or mixed chat/surface continuation.",
            "The necessary second-conversation race uses two real Pages. Raw clips are retained, while the reported continuous video is assembled chronologically from measured switch offsets; the exact ffmpeg command and offsets are retained in the assembly manifest.",
            "No database write, direct product API mutation, fixture Source result, or synthetic fallback is used; the OpenAPI file is only real upload input for the actual Source Hub worker.",
            "The published Corpus trace is chronological and header/body-free; raw Playwright tracing is disabled because it records credential-bearing request headers.",
        ],
        "error": error,
    }
    result_path = directory / "result.json"
    result_path.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(f"run={run_id} status={result['status']}")
    print(f"url={args.url}")
    print(f"backend={args.backend_url}")
    print(f"artifact={result_path}")
    print(f"video={assembled_video}")
    print(f"trace={result['trace']}")
    print("ids=" + json.dumps({key: ids[key] for key in REQUIRED_ID_KEYS}, sort_keys=True))
    if error:
        print(f"error={error}")
    return 0 if passed else 1


async def register(page: Page, url: str, email: str, password: str) -> None:
    await page.goto(url)
    await page.get_by_role("heading", name="Explore Corpus", exact=True).wait_for(timeout=30_000)
    await page.get_by_role("button", name="Create account", exact=True).click()
    await page.get_by_role("heading", name="Create account", exact=True).wait_for()
    await page.get_by_label("Display name", exact=True).fill("Agent Lifecycle Evidence Owner")
    await page.get_by_label("Email", exact=True).fill(email)
    await page.get_by_label("Password", exact=True).fill(password)
    await page.locator("form").get_by_role("button", name="Create account", exact=True).click()
    await page.get_by_label("Sign out", exact=True).wait_for(timeout=30_000)


async def open_agents(page: Page, *, timeout_ms: int = 90_000) -> None:
    agents = page.locator(AGENTS_HOME_TITLE_SELECTOR)
    actions = (
        page.get_by_role("button", name="Continue to Workspace", exact=True).last,
        page.get_by_role("button", name="Open Agents", exact=True),
    )
    deadline = asyncio.get_running_loop().time() + timeout_ms / 1_000
    last_timeout: PlaywrightTimeoutError | None = None
    while asyncio.get_running_loop().time() < deadline:
        if await agents.is_visible():
            return
        for action in actions:
            if await action.is_visible() and await action.is_enabled():
                remaining_ms = max(
                    100,
                    int((deadline - asyncio.get_running_loop().time()) * 1_000),
                )
                try:
                    await action.click(timeout=min(1_500, remaining_ms))
                except PlaywrightTimeoutError as caught:
                    if await agents.is_visible():
                        return
                    last_timeout = caught
                except PlaywrightError as caught:
                    if "detached" not in str(caught).casefold():
                        raise
                    if await agents.is_visible():
                        return
                break
        await page.wait_for_timeout(250)
    if last_timeout is not None:
        raise last_timeout
    raise TimeoutError("Agents navigation did not recover before the recorder deadline.")


async def create_agent(page: Page, name: str) -> None:
    await page.locator(".agents-home > .agents-heading").get_by_role(
        "button", name="Create agent", exact=True
    ).click()
    await page.get_by_role("heading", name="Create an agent", exact=True).wait_for()
    await page.get_by_label("Name", exact=True).fill(name)
    await page.get_by_label("Description", exact=True).fill(
        f"Exercises the {name} lifecycle behavior."
    )
    await page.get_by_label("Instructions", exact=True).fill(
        "Use only explicitly selected owner-scoped records."
    )
    await page.locator("form").get_by_role("button", name="Create agent", exact=True).click()
    await AgentInventory(page).agent(name).wait_for(
        timeout=30_000
    )


async def select_agent(page: Page, name: str) -> None:
    button = AgentInventory(page).agent(name)
    await button.wait_for(timeout=30_000)
    await button.click()
    await page.locator(".agents-home main").get_by_role(
        "heading", name=name, exact=True
    ).wait_for()
    await AgentLifecycleControls(page).heading.wait_for()


async def create_ready_source_and_attach(page: Page, definition: Path, name: str) -> None:
    await AgentSourcesPanel(page).create_and_attach.click()
    await page.get_by_role("heading", name="Add an API source", exact=True).wait_for()
    await page.get_by_label("Source name", exact=True).fill(name)
    await page.get_by_label("OpenAPI or Swagger definition", exact=True).set_input_files(definition)
    await page.get_by_role("button", name="Upload and process", exact=True).click()
    await page.get_by_text("ready", exact=True).first.wait_for(timeout=90_000)
    attach = page.get_by_role("button", name="Attach and return to Agent", exact=True)
    await attach.wait_for(timeout=30_000)
    await attach.click()
    sources = AgentSourcesPanel(page)
    await sources.heading.wait_for(timeout=30_000)
    await sources.source(name).wait_for()


async def assert_agent_present(page: Page, name: str) -> None:
    await AgentInventory(page).agent(name).wait_for(
        timeout=30_000
    )


async def assert_agents_present(page: Page, names: Iterable[str]) -> None:
    for name in names:
        await assert_agent_present(page, name)


async def assert_agent_absent(page: Page, name: str) -> None:
    locator = AgentInventory(page).agent(name)
    await locator.wait_for(state="detached", timeout=30_000)


async def selected_conversation_id(page: Page) -> str | None:
    return await page.evaluate(
        "sessionStorage.getItem('corpus.selected-conversation.v1')"
    )


async def review_id(heading: Locator) -> str:
    value = await heading.get_attribute("id")
    if value is None or not value.startswith("review-"):
        raise AssertionError("The exact RouteDeck review id is absent from the review heading.")
    return value.removeprefix("review-")


async def capture_bound_state(
    page: Page,
    repository: Path,
    directory: Path,
    screenshots: list[str],
    checks: list[dict[str, object]],
    name: str,
    region: Locator,
    targets: dict[str, Locator],
) -> None:
    for width, height, suffix in ((1440, 1000, "desktop"), (390, 844, "mobile")):
        await page.set_viewport_size({"width": width, "height": height})
        await region.scroll_into_view_if_needed()
        bounds = {key: await locator.bounding_box() for key, locator in targets.items()}
        viewport = page.viewport_size
        inside = viewport is not None and all(
            _inside_viewport(value, viewport) for value in bounds.values()
        )
        await capture_desktop(
            page,
            repository,
            directory,
            screenshots,
            f"{name}-{suffix}",
            full_page=False,
        )
        record(
            checks,
            f"{name} {suffix} targets are inside the viewport",
            inside,
            {"viewport": viewport, "bounds": bounds},
        )
    await page.set_viewport_size({"width": 1440, "height": 1000})


async def capture_desktop(
    page: Page,
    repository: Path,
    directory: Path,
    output: list[str],
    name: str,
    *,
    full_page: bool = True,
) -> None:
    path = directory / f"{name}.png"
    await page.screenshot(path=path, full_page=full_page)
    output.append(str(path.relative_to(repository)))


def _inside_viewport(
    bounds: dict[str, float] | None,
    viewport: dict[str, int],
) -> bool:
    if bounds is None:
        return False
    return (
        bounds["x"] >= 0
        and bounds["y"] >= 0
        and bounds["x"] + bounds["width"] <= viewport["width"]
        and bounds["y"] + bounds["height"] <= viewport["height"]
    )


def compose(repository: Path, action: str, service: str) -> None:
    subprocess.run(
        ["docker", "compose", action, service],
        cwd=repository,
        check=True,
        capture_output=True,
        text=True,
    )


def wait_ready(url: str, timeout: int) -> None:
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        try:
            with urlopen(url, timeout=3) as response:
                if response.status == 200:
                    return
        except Exception:
            time.sleep(1)
    raise TimeoutError(f"Backend did not become ready: {url}")


async def wait_for_ids(
    ids: dict[str, str | None],
    keys: Iterable[str],
    *,
    timeout_ms: int = 10_000,
) -> None:
    required = tuple(keys)
    deadline = asyncio.get_running_loop().time() + timeout_ms / 1_000
    while asyncio.get_running_loop().time() < deadline:
        if _ids_complete(ids, required):
            return
        await asyncio.sleep(0.1)


def _ids_complete(ids: dict[str, str | None], keys: Iterable[str]) -> bool:
    return all(isinstance(ids.get(key), str) and bool(ids[key]) for key in keys)


def route_deck_failure_seen(
    diagnostics: dict[str, list[dict[str, object]]], code: str
) -> bool:
    return any(item.get("failureCode") == code for item in diagnostics["routeDeckResults"])


def _expected_http_outcome(
    path: str,
    status: int,
    payload: object,
) -> str | None:
    if status != 409 or not isinstance(payload, dict):
        return None
    failure = payload.get("failure")
    if not isinstance(failure, dict):
        return None
    code = failure.get("code")
    operation_id = payload.get("operation_id")
    disposition = payload.get("disposition")
    if operation_id != "agents.delete_agent":
        return None
    if (
        code == "review_rejected"
        and disposition == "failed"
        and re.fullmatch(r"/api/routedeck/reviews/[^/]+/reject", path)
    ):
        return code
    if (
        code == "agent_dependency_conflict"
        and disposition == "blocked"
        and path == "/api/routedeck/dispatch"
    ):
        return code
    if (
        code == "review_stale"
        and disposition == "failed"
        and re.fullmatch(r"/api/routedeck/reviews/[^/]+/accept", path)
    ):
        return code
    return None


def classify_expected_console_errors(
    diagnostics: dict[str, list[dict[str, object]]],
) -> None:
    expected_by_location = Counter(
        (str(item.get("page")), str(item.get("path")))
        for item in diagnostics["expectedHttpOutcomes"]
        if item.get("status") == 409 and item.get("path")
    )
    remaining: list[dict[str, object]] = []
    expected_message = (
        "Failed to load resource: the server responded with a status of 409 (Conflict)"
    )
    for item in diagnostics["consoleErrors"]:
        page_name = str(item.get("page"))
        path = str(item.get("path")) if item.get("path") else ""
        if (
            item.get("type") == "error"
            and item.get("text") == expected_message
            and path
            and expected_by_location[(page_name, path)] > 0
        ):
            diagnostics["expectedConsoleErrors"].append(item)
            expected_by_location[(page_name, path)] -= 1
        else:
            remaining.append(item)
    diagnostics["consoleErrors"][:] = remaining


def write_corpus_trace(
    path: Path,
    run_id: str,
    diagnostics: dict[str, object],
) -> None:
    raw_events = diagnostics.get("chronologicalTrace", [])
    events = raw_events if isinstance(raw_events, list) else []
    allowed = {
        "observedAt",
        "page",
        "kind",
        "method",
        "path",
        "status",
        "operationId",
        "disposition",
        "outcome",
        "failureCode",
        "expectedOutcome",
        "requestFailure",
    }
    sanitized = [
        {key: event[key] for key in allowed if key in event}
        for event in sorted(
            (item for item in events if isinstance(item, dict)),
            key=lambda item: str(item.get("observedAt", "")),
        )
    ]
    path.write_text(
        json.dumps(
            {
                "runId": run_id,
                "format": "corpus-redacted-trace.v1",
                "events": sanitized,
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )


def _is_expected_aborted_request(url: str, failure: str | None) -> bool:
    if failure != "net::ERR_ABORTED":
        return False
    path = urlparse(url).path
    return (
        path == "/api/routedeck/events"
        or path == "/api/routedeck/conversation"
        or path.startswith("/api/routedeck/conversation/")
        or path.startswith("/api/routedeck/private-forms/")
    )


def _record_request_failure(
    diagnostics: dict[str, list[dict[str, object]]],
    *,
    page_name: str,
    url: str,
    failure: str | None,
) -> None:
    item = {"page": page_name, "url": url, "path": urlparse(url).path, "failure": failure}
    key = "expectedAbortedRequests" if _is_expected_aborted_request(url, failure) else "requestFailures"
    diagnostics[key].append(item)


def record(
    checks: list[dict[str, object]],
    name: str,
    passed: bool,
    details: object | None = None,
) -> None:
    checks.append({"name": name, "passed": passed, "details": details})


def attach_diagnostics(
    page: Page,
    page_name: str,
    diagnostics: dict[str, list[dict[str, object]]],
    ids: dict[str, str | None],
) -> None:
    def trace_event(kind: str, **values: object) -> None:
        diagnostics["chronologicalTrace"].append(
            {
                "observedAt": datetime.now(UTC).isoformat(),
                "page": page_name,
                "kind": kind,
                **values,
            }
        )

    async def response(item) -> None:
        try:
            path = urlparse(item.url).path
            payload = None
            content_type = item.headers.get("content-type", "")
            if "application/json" in content_type:
                payload = await item.json()
            if item.status == 200 and path == "/api/agents" and isinstance(payload, dict):
                for agent in payload.get("agents", []):
                    for key, name in AGENT_NAMES.items():
                        if agent.get("name") == name:
                            ids[key] = str(agent["id"])
            if item.status == 200 and path == "/api/sources":
                sources = payload if isinstance(payload, list) else []
                source = next(
                    (value for value in sources if value.get("display_name") == "Lifecycle Guard Source"),
                    None,
                )
                if source is not None:
                    ids["sourceId"] = source.get("source_id")
                    revision = source.get("revision") or {}
                    ids["sourceRevisionId"] = revision.get("revision_id")
                    ids["sourceJobId"] = revision.get("job_id")
            if "/api/routedeck/" in path and isinstance(payload, dict):
                failure = payload.get("failure") or {}
                diagnostics["routeDeckResults"].append(
                    {
                        "page": page_name,
                        "url": item.url,
                        "status": item.status,
                        "operationId": payload.get("operation_id"),
                        "requestId": payload.get("request_id"),
                        "disposition": payload.get("disposition"),
                        "outcome": payload.get("outcome"),
                        "reviewId": (payload.get("review") or {}).get("id"),
                        "failureCode": failure.get("code"),
                        "failureMessage": failure.get("public_message"),
                    }
                )
            if path.startswith("/api/agents") or path.startswith("/api/sources"):
                diagnostics["productObservations"].append(
                    {"page": page_name, "method": item.request.method, "status": item.status, "url": item.url}
                )
            failure = payload.get("failure") if isinstance(payload, dict) else None
            failure_code = failure.get("code") if isinstance(failure, dict) else None
            expected_outcome = _expected_http_outcome(path, item.status, payload)
            trace_event(
                "response",
                method=item.request.method,
                path=path,
                status=item.status,
                operationId=(payload.get("operation_id") if isinstance(payload, dict) else None),
                disposition=(payload.get("disposition") if isinstance(payload, dict) else None),
                outcome=(payload.get("outcome") if isinstance(payload, dict) else None),
                failureCode=failure_code,
                expectedOutcome=expected_outcome,
            )
            if item.status >= 400:
                diagnostic = {
                    "page": page_name,
                    "method": item.request.method,
                    "status": item.status,
                    "path": path,
                    "failureCode": failure_code,
                }
                diagnostics[
                    "expectedHttpOutcomes" if expected_outcome is not None else "httpErrors"
                ].append(
                    {**diagnostic, "code": expected_outcome}
                    if expected_outcome is not None
                    else diagnostic
                )
        except Exception as caught:
            diagnostics["pageErrors"].append(
                {"page": page_name, "message": f"response observer failed: {caught}"}
            )

    page.on("response", response)
    def console(item) -> None:
        if item.type not in {"warning", "error"}:
            return
        location = item.location if isinstance(item.location, dict) else {}
        path = urlparse(str(location.get("url", ""))).path or None
        diagnostics["consoleErrors"].append(
            {
                "page": page_name,
                "type": item.type,
                "text": item.text,
                "path": path,
            }
        )
        trace_event("console", disposition=item.type)

    page.on("console", console)
    page.on(
        "pageerror",
        lambda item: (
            diagnostics["pageErrors"].append(
                {"page": page_name, "message": str(item)}
            ),
            trace_event("page_error"),
        ),
    )
    page.on(
        "requestfailed",
        lambda item: _record_request_failure(
            diagnostics,
            page_name=page_name,
            url=item.url,
            failure=item.failure,
        ),
    )


async def save_video(video, repository: Path, final_path: Path) -> str:
    raw_path = Path(await video.path())
    raw_path.replace(final_path)
    return str(final_path.relative_to(repository))


def chronological_ffmpeg_command(
    ffmpeg: str,
    primary: Path,
    secondary: Path,
    output: Path,
    race_start: float,
    race_end: float,
) -> list[str]:
    if race_start <= 0 or race_end <= race_start:
        raise ValueError("The recorded race switch offsets are invalid.")
    graph = (
        f"[0:v]trim=start=0:end={race_start:.3f},setpts=PTS-STARTPTS[v0];"
        "[1:v]setpts=PTS-STARTPTS[v1];"
        f"[0:v]trim=start={race_end:.3f},setpts=PTS-STARTPTS[v2];"
        "[v0][v1][v2]concat=n=3:v=1:a=0[outv]"
    )
    return [
        ffmpeg,
        "-y",
        "-i",
        str(primary),
        "-i",
        str(secondary),
        "-filter_complex",
        graph,
        "-map",
        "[outv]",
        "-c:v",
        "libvpx-vp9",
        "-crf",
        "30",
        "-b:v",
        "0",
        str(output),
    ]


def assemble_chronological_video(
    *,
    repository: Path,
    directory: Path,
    primary: Path,
    secondary: Path,
    race_start: float,
    race_end: float,
) -> tuple[str | None, dict[str, object]]:
    manifest_path = directory / "video-assembly.json"
    output = directory / "agents-archive-delete-journey.webm"
    ffmpeg = shutil.which("ffmpeg")
    manifest: dict[str, object] = {
        "status": "failed",
        "primaryRaceStartSeconds": race_start,
        "primaryRaceEndSeconds": race_end,
        "primaryRaw": str(primary.relative_to(repository)),
        "raceConversationRaw": str(secondary.relative_to(repository)),
        "output": str(output.relative_to(repository)),
        "command": None,
        "manifest": str(manifest_path.relative_to(repository)),
        "error": None,
    }
    try:
        if ffmpeg is None:
            raise RuntimeError("ffmpeg is required for truthful chronological video assembly.")
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
            raise RuntimeError("ffmpeg completed without producing a non-empty video.")
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
    raise SystemExit(asyncio.run(run(arguments())))
