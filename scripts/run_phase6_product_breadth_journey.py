from __future__ import annotations

import argparse
import asyncio
import json
import secrets
import shutil
import time
from datetime import UTC, datetime
from pathlib import Path
from urllib.parse import urlsplit

from playwright.async_api import Browser, BrowserContext, Page, Response, async_playwright

from run_phase5_builder_lifecycle_journey import (
    AGENT_ID,
    ORGANIZATION_ID,
    OWNER_EMAIL,
    RESET_CODE,
    _submit_sign_in,
)


ROOT = Path(__file__).resolve().parents[1]
ARTIFACT_ROOT = ROOT / "artifacts" / "phase6-product-breadth"
CONTAINER = "corpus-development-backend-1"
SOURCE_ID = "B4Uwj6IJNPZAv1-0"
SOURCE_NAME = "medusa_store"
SOURCE_DEFINITION = (
    ROOT / ".runtime" / "sources" / "920bd5e5d50f9292" / SOURCE_ID /
    "r" / "BxW04oV4785hpVA1" / "i" / "medusa_store.yaml"
)


def arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Record isolated Phase 6 Agent and Source lifecycle evidence.")
    parser.add_argument("--url", default="http://127.0.0.1:5199")
    parser.add_argument("--headed", action="store_true")
    parser.add_argument("--module", choices=("agents", "sources", "all"), default="all")
    return parser.parse_args()


def reset_owner(password: str) -> dict[str, str]:
    import subprocess

    completed = subprocess.run(
        ["docker", "exec", "-i", "-w", "/workspace/corpus/backend", CONTAINER,
         "python", "-c", RESET_CODE, OWNER_EMAIL, AGENT_ID, ORGANIZATION_ID],
        input=password,
        text=True,
        capture_output=True,
        timeout=60,
        check=False,
    )
    if completed.returncode != 0:
        raise RuntimeError("The exact retained owner could not be recovered for Phase 6.")
    return json.loads(completed.stdout.strip())


async def maximize(page: Page) -> None:
    shell = page.locator("[data-agent-shell]")
    if await shell.get_attribute("data-surface-layout") != "split":
        await page.get_by_role("button", name="Maximize surface", exact=True).click()
    if await shell.get_attribute("data-surface-layout") != "split":
        raise RuntimeError("The Phase 6 surface did not maximize beside chat.")


async def screenshot(page: Page, directory: Path, name: str, retained: list[str]) -> None:
    path = directory / f"{name}.png"
    await page.screenshot(path=path, full_page=False)
    retained.append(str(path.relative_to(ROOT)))
    await page.wait_for_timeout(700)


async def sign_in(page: Page, url: str, email: str, password: str) -> None:
    await page.goto(url)
    await page.get_by_role("heading", name="Explore Corpus", exact=True).wait_for(timeout=30_000)
    await page.get_by_role("button", name="Sign in", exact=True).click()
    await page.get_by_role("heading", name="Sign in", exact=True).wait_for()
    await _submit_sign_in(page, email, password)
    await page.get_by_label("Sign out", exact=True).wait_for(timeout=30_000)


async def create_agent(page: Page, name: str) -> None:
    agents = page.locator("section.agents-home")
    await agents.locator(".agents-heading").get_by_role("button", name="Create agent", exact=True).click()
    form = page.locator("section.agent-create form")
    await form.get_by_label("Name", exact=True).fill(name)
    await form.get_by_label("Description", exact=True).fill("Disposable Phase 6 lifecycle evidence record.")
    await form.get_by_label("Instructions", exact=True).fill("Use only explicitly attached owner-scoped API sources.")
    await form.get_by_role("button", name="Create agent", exact=True).click()
    await page.locator("section.agents-home").get_by_label("Agent inventory").get_by_role("button", name=name, exact=False).wait_for(timeout=30_000)


async def select_agent(page: Page, name: str) -> None:
    inventory = page.locator("section.agents-home").get_by_label("Agent inventory")
    button = inventory.get_by_role("button", name=name, exact=False)
    if await button.count() != 1:
        raise RuntimeError(f"The exact disposable Agent {name!r} is unavailable or ambiguous.")
    await button.click()
    await page.locator("section.agents-home main").get_by_role("heading", name=name, exact=True).wait_for()


async def request_agent_review(page: Page, action: str) -> None:
    lifecycle = page.locator("section.agent-lifecycle")
    await lifecycle.get_by_role("button", name=action, exact=True).click()


async def agent_evidence(page: Page, directory: Path, screenshots: list[str]) -> None:
    await page.locator("section.workspace-home").get_by_role("button", name="Open Agents", exact=True).click()
    await page.locator("#agents-home-title").wait_for(timeout=30_000)
    await maximize(page)

    editable = f"Phase 6 Editable {secrets.token_hex(2)}"
    await create_agent(page, editable)
    await select_agent(page, editable)
    main = page.locator("section.agents-home main")
    await main.get_by_label("Description", exact=True).fill("Updated durable Agent configuration.")
    await main.get_by_label("Instructions", exact=True).fill("Answer only from explicitly attached Sources and preserve missing-data truth.")
    await main.get_by_role("button", name="Save new version", exact=True).click()
    await main.get_by_text("Version 2", exact=True).wait_for(timeout=30_000)

    source_select = main.get_by_label("Ready Workspace Source", exact=True)
    await source_select.select_option(SOURCE_ID)
    await main.get_by_role("button", name="Attach Source", exact=True).click()
    attachment = main.locator("section.agent-sources li").filter(has_text=SOURCE_NAME)
    await attachment.wait_for(timeout=30_000)
    await main.get_by_text("Delete blocked: 1 Source attachment remains.", exact=True).wait_for()
    await screenshot(page, directory, "01-agent-version-and-dependency", screenshots)

    await attachment.get_by_role("button", name=f"Detach {SOURCE_NAME} API version", exact=False).click()
    await attachment.wait_for(state="detached", timeout=30_000)
    await main.get_by_text("No current deletion blockers were found.", exact=True).wait_for()
    await request_agent_review(page, "Archive Agent")
    review = page.locator("section.agent-lifecycle-review")
    await review.get_by_role("heading", name="Confirm archive", exact=True).wait_for()
    await screenshot(page, directory, "02-agent-archive-review", screenshots)
    await review.get_by_role("button", name="Keep Agent unchanged", exact=True).click()
    await review.wait_for(state="detached", timeout=30_000)
    await request_agent_review(page, "Archive Agent")
    review = page.locator("section.agent-lifecycle-review")
    await review.get_by_role("button", name="Archive Agent", exact=True).click()
    await review.wait_for(state="detached", timeout=30_000)
    await page.locator("section.agents-home").get_by_label("Agent inventory").get_by_role("button", name=editable, exact=False).wait_for(state="detached")

    removable = f"Phase 6 Removable {secrets.token_hex(2)}"
    await create_agent(page, removable)
    await select_agent(page, removable)
    await request_agent_review(page, "Delete permanently")
    review = page.locator("section.agent-lifecycle-review")
    await review.get_by_role("heading", name="Confirm permanent deletion", exact=True).wait_for()
    await review.get_by_role("button", name="Keep Agent unchanged", exact=True).click()
    await review.wait_for(state="detached", timeout=30_000)
    await request_agent_review(page, "Delete permanently")
    review = page.locator("section.agent-lifecycle-review")
    await screenshot(page, directory, "03-agent-delete-review", screenshots)
    await review.get_by_role("button", name="Delete Agent permanently", exact=True).click()
    await review.wait_for(state="detached", timeout=30_000)
    await page.locator("section.agents-home").get_by_label("Agent inventory").get_by_role("button", name=removable, exact=False).wait_for(state="detached")
    await screenshot(page, directory, "04-agent-lifecycle-complete", screenshots)


async def source_evidence(page: Page, directory: Path, screenshots: list[str], description: Path) -> None:
    await page.locator("section.workspace-home").get_by_role("button", name="Open Sources", exact=True).click()
    hub = page.locator("section.source-hub")
    await hub.locator("#source-hub-title").wait_for(timeout=30_000)
    await maximize(page)

    retained = await exact_source_row(hub, SOURCE_NAME)
    await retained.get_by_role("button", name="Open API source", exact=True).click()
    workspace = page.locator("section.api-source-workspace")
    await workspace.get_by_role("button", name="Delete API source", exact=True).click()
    await workspace.get_by_role("heading", name="This API source is still part of saved Agent work", exact=True).wait_for()
    await screenshot(page, directory, "05-source-dependency-block", screenshots)
    await workspace.get_by_role("button", name="Source Hub", exact=True).click()
    await hub.locator("#source-hub-title").wait_for()

    disposable = f"Phase 6 disposable {secrets.token_hex(2)}"
    await hub.get_by_role("button", name="Add API source", exact=True).first.click()
    intake = page.locator("section.api-source-workspace form.source-intake")
    await intake.get_by_label("Source name", exact=True).fill(disposable)
    await intake.get_by_label("OpenAPI or Swagger definition", exact=True).set_input_files(SOURCE_DEFINITION)
    await intake.get_by_role("button", name="Add API definition", exact=True).click()
    await workspace.locator("#source-detail-title").get_by_text(disposable, exact=True).wait_for(timeout=30_000)
    await workspace.get_by_text("Ready to analyze", exact=True).wait_for()
    await workspace.get_by_role("button", name="Add or update description", exact=True).click()
    await workspace.get_by_label("Markdown description", exact=True).set_input_files(description)
    await workspace.get_by_role("button", name="Save API description", exact=True).click()
    await workspace.get_by_text("Phase 6 owner context", exact=False).wait_for(timeout=30_000)
    await screenshot(page, directory, "06-source-description-version", screenshots)

    await workspace.get_by_role("button", name="Delete API source", exact=True).click()
    review = page.locator("section.source-delete-review")
    await review.get_by_role("heading", name="Confirm permanent Source deletion", exact=True).wait_for()
    await review.get_by_role("button", name="Keep API source unchanged", exact=True).click()
    await review.wait_for(state="detached", timeout=30_000)
    await workspace.get_by_role("button", name="Delete API source", exact=True).click()
    review = page.locator("section.source-delete-review")
    await screenshot(page, directory, "07-source-delete-review", screenshots)
    await review.get_by_role("button", name="Delete API source permanently", exact=True).click()
    await review.wait_for(state="detached", timeout=30_000)
    await hub.locator("#source-hub-title").wait_for(timeout=30_000)
    await hub.locator("article.source-hub-row").filter(has_text=disposable).wait_for(state="detached")
    await screenshot(page, directory, "08-source-delete-complete", screenshots)


async def exact_source_row(hub, name: str):
    rows = hub.locator("article.source-hub-row")
    matches = []
    for index in range(await rows.count()):
        row = rows.nth(index)
        if await row.locator("strong").first.inner_text() == name:
            matches.append(row)
    if len(matches) != 1:
        raise RuntimeError(f"The exact Source row {name!r} is unavailable or ambiguous.")
    return matches[0]


async def new_recording_context(
    browser: Browser,
    directory: Path,
    stem: str,
) -> tuple[BrowserContext, Page]:
    raw = directory / f"raw-{stem}"
    raw.mkdir()
    context = await browser.new_context(
        viewport={"width": 1440, "height": 1000},
        record_video_dir=raw,
        record_video_size={"width": 1440, "height": 1000},
    )
    return context, await context.new_page()


async def run(args: argparse.Namespace) -> int:
    run_id = datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ") + "-" + secrets.token_hex(4)
    directory = ARTIFACT_ROOT / run_id
    directory.mkdir(parents=True)
    description = directory / "phase6-description.md"
    description.write_text("# Phase 6 owner context\nLifecycle evidence without API analysis.\n", encoding="utf-8")
    password = "Corpus-Phase6-" + secrets.token_urlsafe(24) + "!9"
    destroy_password = "Corpus-Phase6-Destroy-" + secrets.token_urlsafe(24) + "!9"
    screenshots: list[str] = []
    operations: list[dict[str, object]] = []
    diagnostics: dict[str, list[dict[str, object]]] = {
        "httpErrors": [], "consoleErrors": [], "pageErrors": [], "requestFailures": [],
        "expectedHttp": [], "expectedConsole": [],
    }
    videos: list[str] = []
    error: str | None = None
    started = time.monotonic()
    recovered = False

    async def observe(response: Response) -> None:
        path = urlsplit(response.url).path
        expected_reject = path.startswith("/api/routedeck/reviews/") and path.endswith("/reject") and response.status == 409
        if expected_reject:
            diagnostics["expectedHttp"].append({"method": response.request.method, "path": path, "status": response.status})
        elif response.status >= 400:
            diagnostics["httpErrors"].append({"method": response.request.method, "path": path, "status": response.status})
        if response.status == 200 and response.request.method == "POST" and path == "/api/routedeck/dispatch":
            try:
                body = await response.json()
                operations.append({
                    "operationId": body.get("operation_id") or body.get("operationId"),
                    "disposition": body.get("disposition"),
                    "outcome": body.get("outcome"),
                })
            except Exception:
                pass

    try:
        if not SOURCE_DEFINITION.is_file():
            raise RuntimeError("The exact retained real Source definition is unavailable.")
        identity = reset_owner(password)
        recovered = True
        async with async_playwright() as playwright:
            browser = await playwright.chromium.launch(headless=not args.headed)
            modules = (("agents", agent_evidence), ("sources", None)) if args.module == "all" else ((args.module, agent_evidence if args.module == "agents" else None),)
            for stem, feature in modules:
                context, page = await new_recording_context(browser, directory, stem)
                tasks: set[asyncio.Task[None]] = set()
                def schedule(response: Response) -> None:
                    task = asyncio.create_task(observe(response)); tasks.add(task); task.add_done_callback(tasks.discard)
                page.on("response", schedule)
                def record_console(item) -> None:
                    if item.type not in {"warning", "error"}:
                        return
                    target = "expectedConsole" if (
                        "409 (Conflict)" in item.text or "GPU stall due to ReadPixels" in item.text
                    ) else "consoleErrors"
                    diagnostics[target].append({"type": item.type, "text": item.text})
                page.on("console", record_console)
                page.on("pageerror", lambda item: diagnostics["pageErrors"].append({"message": str(item)}))
                page.on("requestfailed", lambda request: diagnostics["requestFailures"].append({"method": request.method, "path": urlsplit(request.url).path, "failure": request.failure}))
                await sign_in(page, args.url, identity["email"], password)
                if feature is not None:
                    await feature(page, directory, screenshots)
                else:
                    await source_evidence(page, directory, screenshots, description)
                if tasks:
                    await asyncio.gather(*tuple(tasks), return_exceptions=True)
                video = page.video
                await page.close()
                path = Path(await video.path()) if video is not None else None
                await context.close()
                if path is None or not path.is_file():
                    raise RuntimeError(f"The isolated {stem} video is unavailable.")
                final = directory / f"phase6-{stem}-normal-speed.webm"
                path.replace(final)
                videos.append(str(final.relative_to(ROOT)))
            await browser.close()
        if diagnostics["httpErrors"] or diagnostics["consoleErrors"] or diagnostics["pageErrors"]:
            raise RuntimeError("The Phase 6 evidence interval contains unexpected diagnostics.")
        actual = [item.get("operationId") for item in operations]
        required_by_module = {
            "agents": {"agents.create_agent", "agents.save_changes", "agents.attach_source", "agents.detach_source", "agents.archive_agent", "agents.delete_agent"},
            "sources": {"sources.accept_staged_api", "sources.open_api_description", "sources.save_api_description", "sources.delete_api_source"},
        }
        required = set().union(*(required_by_module[name] for name in required_by_module if args.module in {name, "all"}))
        if not required.issubset(set(actual)):
            raise RuntimeError(f"The Phase 6 operation evidence is incomplete: {sorted(required - set(actual))}")
    except Exception as caught:
        error = f"{type(caught).__name__}: {caught}"
    finally:
        if recovered:
            try:
                reset_owner(destroy_password)
            except Exception as caught:
                error = error or f"RuntimeError: temporary owner credential cleanup failed: {caught}"

    description.unlink(missing_ok=True)
    result = {
        "runId": run_id,
        "status": "passed" if error is None else "failed",
        "scope": f"isolated Phase 6 {args.module} product breadth",
        "ids": {"organizationId": ORGANIZATION_ID, "retainedAgentId": AGENT_ID, "retainedSourceId": SOURCE_ID},
        "operations": operations,
        "screenshots": screenshots,
        "videos": videos,
        "videoMetadata": {"playbackRate": 1.0, "width": 1440, "height": 1000, "maximizedSurface": True},
        "diagnostics": diagnostics,
        "elapsedSeconds": round(time.monotonic() - started, 3),
        "error": error,
    }
    result_path = directory / "result.json"
    result_path.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    canaries = (password.encode(), destroy_password.encode())
    for artifact in directory.rglob("*"):
        if artifact.is_file() and any(canary in artifact.read_bytes() for canary in canaries):
            shutil.rmtree(directory)
            raise RuntimeError("A credential canary reached Phase 6 evidence; the run was removed.")
    print(f"run={run_id} status={result['status']}")
    print(f"artifact={result_path}")
    for video in videos:
        print(f"video={video}")
    if error is not None:
        print("error=" + error.encode("ascii", "backslashreplace").decode("ascii"))
    return 0 if error is None else 1


async def main() -> int:
    async with asyncio.timeout(13 * 60):
        return await run(arguments())


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
