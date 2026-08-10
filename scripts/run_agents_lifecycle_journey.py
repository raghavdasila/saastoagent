from __future__ import annotations

import argparse
import asyncio
import json
import subprocess
import time
from collections.abc import Awaitable, Callable
from datetime import UTC, datetime
from pathlib import Path
from urllib.request import urlopen
from uuid import uuid4

from playwright.async_api import Page, async_playwright


OPENAPI = """openapi: 3.0.3
info: {title: Lifecycle Catalog API, version: 1.0.0}
servers: [{url: 'http://host.docker.internal:9000'}]
paths:
  /products:
    get:
      operationId: listProducts
      responses:
        '200': {description: Product list}
"""


def arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--url", default="http://127.0.0.1:5199")
    parser.add_argument("--headed", action="store_true")
    return parser.parse_args()


async def run(args: argparse.Namespace) -> int:
    repository = Path(__file__).resolve().parents[1]
    run_id = datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ") + "-" + uuid4().hex[:10]
    directory = repository / "artifacts" / "agents-lifecycle" / run_id
    videos = directory / "videos"
    videos.mkdir(parents=True)
    definition = directory / "lifecycle-catalog.yaml"
    definition.write_text(OPENAPI, encoding="utf-8", newline="\n")
    screenshots: list[str] = []
    checks: list[dict[str, object]] = []
    diagnostics: dict[str, list[dict[str, object]]] = {
        "httpErrors": [], "consoleErrors": [], "pageErrors": [], "requestFailures": []
    }
    ids: dict[str, str | None] = {"agentId": None, "sourceId": None, "sourceRevisionId": None}
    observed: dict[str, str | None] = dict(ids)
    error: str | None = None
    trace = directory / "browser-trace.zip"
    video: str | None = None

    try:
        async with async_playwright() as playwright:
            browser = await playwright.chromium.launch(headless=not args.headed)
            context = await browser.new_context(
                viewport={"width": 1440, "height": 1000},
                record_video_dir=videos,
                record_video_size={"width": 1440, "height": 1000},
            )
            await context.tracing.start(screenshots=True, snapshots=True, sources=True)
            page = await context.new_page()
            attach_diagnostics(page, diagnostics, observed)
            await register(page, args.url)
            await page.get_by_role("button", name="Open Agents", exact=True).click()
            await page.get_by_role("heading", name="Agents", exact=True).last.wait_for()
            await page.get_by_role("button", name="Create agent", exact=True).last.click()
            await page.get_by_role("heading", name="Create an agent", exact=True).wait_for()
            await page.get_by_label("Name", exact=True).fill("Lifecycle Agent")
            await page.get_by_label("Description", exact=True).fill("Exercises Source attachment lifecycle.")
            await page.get_by_label("Instructions", exact=True).fill("Use only explicitly attached Source revisions.")
            await page.locator("form").get_by_role("button", name="Create agent", exact=True).click()
            agent_button = page.get_by_role("button", name="Lifecycle Agent Version 1", exact=True)
            await agent_button.wait_for()
            await agent_button.click()
            await page.get_by_role("heading", name="Attached Sources", exact=True).wait_for()
            await capture(page, repository, directory, screenshots, "01-agent-empty-attachments")

            await page.get_by_role("button", name="Create and attach", exact=True).click()
            await page.get_by_role("heading", name="Add an API source", exact=True).wait_for()
            await page.get_by_label("Source name", exact=True).fill("Lifecycle Catalog API")
            await page.get_by_label("OpenAPI or Swagger definition", exact=True).set_input_files(definition)
            await page.get_by_role("button", name="Upload and process", exact=True).click()
            await page.get_by_text("ready", exact=True).first.wait_for(timeout=90_000)
            attach = page.get_by_role("button", name="Attach and return to Agent", exact=True)
            await attach.wait_for(timeout=30_000)
            await capture(page, repository, directory, screenshots, "02-ready-create-handoff")
            await attach.click()
            await page.get_by_role("heading", name="Attached Sources", exact=True).wait_for(timeout=30_000)
            await page.get_by_text("Lifecycle Catalog API", exact=True).wait_for()
            await page.locator(".agent-sources").scroll_into_view_if_needed()
            await capture(page, repository, directory, screenshots, "03-agent-attached-revision")
            record(checks, "ready Source attaches and returns to exact Agent", True)

            await page.get_by_role("button", name="Open Source", exact=True).click()
            await page.get_by_role("heading", name="Lifecycle Catalog API", exact=True).wait_for()
            await page.get_by_role("button", name="Back to Agent", exact=True).wait_for()
            await capture(page, repository, directory, screenshots, "04-open-attached-source")
            record(checks, "attached Source opens with Agent return context", True)
            await page.get_by_role("button", name="Back to Agent", exact=True).click()
            await page.get_by_role("heading", name="Attached Sources", exact=True).wait_for()

            for _ in range(20):
                if all(observed.values()):
                    break
                await page.wait_for_timeout(100)
            ids.update(observed)
            record(checks, "attachment exposes exact immutable identities", all(ids.values()), dict(ids))

            await page.reload()
            await restore_agents(page)
            await page.get_by_role("button", name="Lifecycle Agent Version 1", exact=True).click()
            await page.get_by_text(f"Revision {ids['sourceRevisionId']}", exact=True).wait_for()
            record(checks, "attachment persists across reload", True)

            async def capture_mobile_evidence() -> None:
                await page.set_viewport_size({"width": 390, "height": 844})
                attachment_region = page.locator(".agent-sources")
                await attachment_region.evaluate(
                    "element => element.scrollIntoView({block: 'start', inline: 'nearest'})"
                )
                mobile_targets = {
                    "heading": attachment_region.get_by_role(
                        "heading", name="Attached Sources", exact=True
                    ),
                    "revision": attachment_region.get_by_text(
                        f"Revision {ids['sourceRevisionId']}", exact=True
                    ),
                    "attach": attachment_region.get_by_role(
                        "button", name="Attach Source", exact=True
                    ),
                    "open": attachment_region.get_by_role(
                        "button", name="Open Source", exact=True
                    ),
                }
                mobile_bounds = {
                    name: await locator.bounding_box()
                    for name, locator in mobile_targets.items()
                }
                mobile_viewport = page.viewport_size
                mobile_controls_visible = (
                    mobile_viewport is not None
                    and all(
                        _inside_viewport(bounds, mobile_viewport)
                        for bounds in mobile_bounds.values()
                    )
                )
                await capture(
                    page,
                    repository,
                    directory,
                    screenshots,
                    "05-mobile-agent-attachments",
                    full_page=False,
                )
                record(
                    checks,
                    "mobile screenshot contains attachment heading, pinned revision, Attach and Open controls",
                    mobile_controls_visible,
                    {"viewport": mobile_viewport, "bounds": mobile_bounds},
                )

            async def verify_restart_evidence() -> None:
                await page.set_viewport_size({"width": 1440, "height": 1000})
                compose(repository, "restart", "backend")
                wait_ready("http://127.0.0.1:8099/readyz", 90)
                await page.reload()
                await restore_agents(page)
                await page.get_by_role(
                    "button", name="Lifecycle Agent Version 1", exact=True
                ).click()
                await page.get_by_text(
                    f"Revision {ids['sourceRevisionId']}", exact=True
                ).wait_for(timeout=30_000)
                await capture(
                    page,
                    repository,
                    directory,
                    screenshots,
                    "06-restart-persistence",
                )
                record(checks, "attachment persists after backend restart", True)

            await _run_post_reload_evidence(
                capture_mobile_evidence,
                verify_restart_evidence,
            )
            await context.tracing.stop(path=trace)
            await context.close()
            candidates = sorted(videos.glob("*.webm"), key=lambda path: path.stat().st_mtime)
            video = str(candidates[-1].relative_to(repository)) if candidates else None
            await browser.close()
    except Exception as caught:
        error = f"{type(caught).__name__}: {caught}"
        if "page" in locals():
            try:
                await capture(page, repository, directory, screenshots, "99-failure-state")
            except Exception:
                pass

    passed = error is None and checks and all(bool(check["passed"]) for check in checks)
    result = {
        "runId": run_id, "status": "passed" if passed else "failed", "url": args.url,
        **ids, "screenshots": screenshots, "video": video,
        "trace": str(trace.relative_to(repository)) if trace.exists() else None,
        "checks": checks, "diagnostics": diagnostics, "error": error,
        "limitations": [
            "Archive, delete, operations hub, and build lineage are outside this bounded slice.",
            "Chat and mixed continuation are not claimed by this surface-first capture.",
            "Duplicate/newer-revision conflict and owner isolation are proven by focused backend tests.",
        ],
    }
    result_path = directory / "result.json"
    result_path.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(f"run={run_id} status={result['status']}")
    print(f"url={args.url}")
    print(f"artifact={result_path}")
    print(f"agent_id={ids['agentId']} source_id={ids['sourceId']} revision_id={ids['sourceRevisionId']}")
    print(f"video={video}")
    if error:
        print(f"error={error}")
    return 0 if passed else 1


async def register(page: Page, url: str) -> None:
    await page.goto(url)
    await page.get_by_role("heading", name="Explore Corpus", exact=True).wait_for(timeout=30_000)
    await page.get_by_role("button", name="Create account", exact=True).click()
    await page.get_by_role("heading", name="Create account", exact=True).wait_for()
    await page.get_by_label("Display name", exact=True).fill("Agents Lifecycle Evidence Owner")
    await page.get_by_label("Email", exact=True).fill(f"agents-{uuid4().hex}@example.com")
    await page.get_by_label("Password", exact=True).fill(f"Corpus-Agents-{uuid4().hex}!7")
    await page.locator("form").get_by_role("button", name="Create account", exact=True).click()
    await page.get_by_label("Sign out", exact=True).wait_for(timeout=20_000)


async def restore_agents(
    page: Page,
    *,
    timeout_ms: int = 90_000,
    poll_interval_ms: int = 250,
) -> None:
    agents = page.get_by_role("heading", name="Agents", exact=True).last
    recovery_actions = (
        page.get_by_role("button", name="Sign in", exact=True),
        page.get_by_role("button", name="Continue to Workspace", exact=True).last,
        page.get_by_role("button", name="Open Agents", exact=True),
    )
    deadline = asyncio.get_running_loop().time() + (timeout_ms / 1_000)
    while asyncio.get_running_loop().time() < deadline:
        if await agents.is_visible():
            return
        for action in recovery_actions:
            if await action.is_visible():
                await action.click()
                break
        await page.wait_for_timeout(poll_interval_ms)
    raise TimeoutError("Agents navigation did not recover before the recorder deadline.")


def compose(repository: Path, action: str, service: str) -> None:
    subprocess.run(["docker", "compose", action, service], cwd=repository, check=True, capture_output=True, text=True)


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


async def capture(
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


async def _run_post_reload_evidence(
    capture_mobile: Callable[[], Awaitable[None]],
    verify_restart: Callable[[], Awaitable[None]],
) -> None:
    await capture_mobile()
    await verify_restart()


def record(checks: list[dict[str, object]], name: str, passed: bool, details: object | None = None) -> None:
    checks.append({"name": name, "passed": passed, "details": details})


def attach_diagnostics(
    page: Page,
    diagnostics: dict[str, list[dict[str, object]]],
    observed: dict[str, str | None],
) -> None:
    async def response(item) -> None:
        if item.status == 200 and item.url.endswith("/api/agents"):
            payload = await item.json()
            agent = next((value for value in payload.get("agents", []) if value.get("name") == "Lifecycle Agent"), None)
            if agent:
                observed["agentId"] = agent["id"]
        if item.status == 200 and "/api/agents/" in item.url and item.url.endswith("/sources"):
            payload = await item.json()
            if payload.get("attachments"):
                attachment = payload["attachments"][0]
                observed["sourceId"] = attachment["source_id"]
                observed["sourceRevisionId"] = attachment["source_revision_id"]
        if item.status >= 400:
            try:
                body = (await item.text())[:2000]
            except Exception:
                body = "unavailable"
            diagnostics["httpErrors"].append({"status": item.status, "url": item.url, "body": body})
    page.on("response", response)
    page.on("console", lambda item: diagnostics["consoleErrors"].append({"type": item.type, "text": item.text}) if item.type in {"warning", "error"} else None)
    page.on("pageerror", lambda item: diagnostics["pageErrors"].append({"message": str(item)}))
    page.on("requestfailed", lambda item: diagnostics["requestFailures"].append({"url": item.url, "failure": item.failure}))


if __name__ == "__main__":
    raise SystemExit(asyncio.run(run(arguments())))
