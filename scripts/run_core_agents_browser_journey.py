from __future__ import annotations

import argparse
import asyncio
import hashlib
import json
import sqlite3
import time
from datetime import UTC, datetime
from pathlib import Path
from uuid import uuid4

from playwright.async_api import async_playwright

from corpus.evaluation.isolated_runtime import IsolatedCorpusRuntime


async def main() -> None:
    parser = argparse.ArgumentParser(
        description=(
            "Run the core Workspace and Agents journey through the rendered "
            "Corpus browser product."
        )
    )
    parser.add_argument("--headed", action="store_true")
    parser.add_argument("--backend-port", type=int, default=8139)
    parser.add_argument("--frontend-port", type=int, default=5239)
    args = parser.parse_args()
    repository = Path(__file__).resolve().parents[1]
    name = f"agents-browser-{uuid4().hex[:10]}"
    runtime = IsolatedCorpusRuntime(
        repository,
        name=name,
        backend_port=args.backend_port,
        frontend_port=args.frontend_port,
    )
    endpoints = await runtime.start()
    run_id = f"{datetime.now(UTC).strftime('%Y%m%dT%H%M%SZ')}-{uuid4().hex[:10]}"
    directory = repository / ".runtime" / "evaluations" / run_id
    directory.mkdir(parents=True, exist_ok=False)
    started = datetime.now(UTC).isoformat()
    assertions: list[dict[str, object]] = []
    screenshots: list[str] = []
    trace_path = directory / "browser-trace.zip"
    error: str | None = None
    try:
        async with async_playwright() as playwright:
            browser = await playwright.chromium.launch(headless=not args.headed)
            context = await browser.new_context(viewport={"width": 1440, "height": 1000})
            await context.tracing.start(screenshots=True, snapshots=True, sources=True)
            page = await context.new_page()
            try:
                await _register(page, endpoints.frontend_url)
                await _assert(
                    page.get_by_label("Workspace overview").is_visible(),
                    assertions,
                    "Workspace overview renders after registration",
                )
                await _assert_text(
                    page,
                    "Sources overview is not connected to Workspace in this core slice.",
                    assertions,
                    "Workspace reports the excluded Sources overview explicitly",
                )
                await page.get_by_role("button", name="Open Agents", exact=True).click()
                await page.locator("section.agents-home").wait_for(timeout=30_000)
                await _capture(page, directory, screenshots, "agents-empty-desktop")
                await _assert_text(
                    page,
                    "No agents yet",
                    assertions,
                    "Agents renders an honest empty state",
                )

                await page.locator(".agents-heading").get_by_role(
                    "button", name="Create agent", exact=True
                ).click()
                await page.locator("section.agent-create").wait_for(timeout=30_000)
                await page.get_by_label("Name").fill("Browser Journey Agent")
                await page.get_by_label("Description").fill(
                    "Created through the rendered Corpus product."
                )
                await page.get_by_label("Instructions").fill(
                    "Complete the owner task and record evidence."
                )
                await page.locator("section.agent-create form").get_by_role(
                    "button", name="Create agent", exact=True
                ).click()
                await page.locator("section.agents-home").wait_for(timeout=30_000)
                await page.get_by_text("Browser Journey Agent", exact=True).first.wait_for()
                await _assert_text(
                    page,
                    "Version 1",
                    assertions,
                    "Created Agent renders at configuration version 1",
                )

                instructions = page.get_by_label("Instructions")
                await instructions.fill(
                    "Complete the owner task, record evidence, and report completion."
                )
                await page.get_by_role(
                    "button", name="Save new version", exact=True
                ).click()
                await page.get_by_text("Version 2", exact=True).last.wait_for(
                    timeout=30_000
                )
                await _capture(page, directory, screenshots, "agents-version-2-desktop")
                await _assert_text(
                    page,
                    "Version 2",
                    assertions,
                    "Saved edit renders as configuration version 2",
                )

                await page.set_viewport_size({"width": 390, "height": 844})
                await _capture(page, directory, screenshots, "agents-version-2-mobile")
                await _assert(
                    page.locator("section.agents-home").is_visible(),
                    assertions,
                    "Agents remains usable at a mobile viewport",
                )

                await page.locator(".agents-heading").get_by_role(
                    "button", name="Back to Workspace", exact=True
                ).click()
                await page.get_by_label("Workspace overview").wait_for(timeout=30_000)
                await _capture(page, directory, screenshots, "workspace-final-mobile")
                await _assert_text(
                    page,
                    "1 active agent in this Workspace.",
                    assertions,
                    "Workspace reloads the persisted Agent count",
                )
            except Exception as caught:
                error = f"{type(caught).__name__}: {caught}"
            finally:
                await context.tracing.stop(path=trace_path)
                await context.close()
                await browser.close()

        state = _database_state(_sqlite_path(endpoints.database_url))
        _record_assertion(
            assertions,
            "one Agent identity is persisted",
            state["agents"] == 1,
            state,
        )
        _record_assertion(
            assertions,
            "two immutable Agent configurations are persisted",
            state["agent_versions"] == 2,
            state,
        )
        _record_assertion(
            assertions,
            "the current Agent version is 2",
            state["current_version"] == 2,
            state,
        )
    finally:
        await runtime.close()

    passed = error is None and all(item["passed"] for item in assertions)
    completed = datetime.now(UTC).isoformat()
    artifact = {
        "schema": "corpus.core-agents-browser-journey.v1",
        "runId": run_id,
        "status": "passed" if passed else "failed",
        "startedAt": started,
        "completedAt": completed,
        "runtime": {
            "location": "local isolated runtime",
            "frontend": endpoints.frontend_url,
            "backend": endpoints.backend_url,
            "database": endpoints.database_url,
        },
        "assertions": assertions,
        "screenshots": screenshots,
        "trace": str(trace_path.relative_to(repository)),
        "databaseState": _database_state(_sqlite_path(endpoints.database_url)),
        "error": error,
    }
    artifact_path = directory / "result.json"
    artifact_path.write_text(
        json.dumps(artifact, indent=2) + "\n",
        encoding="utf-8",
        newline="\n",
    )
    print(f"run={run_id} status={artifact['status']}")
    print(f"artifact={artifact_path}")
    if error is not None:
        print(f"error={error}")
    raise SystemExit(0 if passed else 1)


async def _register(page, frontend_url: str) -> None:
    await page.goto(frontend_url)
    await page.get_by_role("heading", name="Explore Corpus").wait_for(timeout=30_000)
    await page.wait_for_timeout(750)
    heading = page.get_by_role("heading", name="Create account")
    for attempt in range(3):
        await page.get_by_role("button", name="Create account", exact=True).click()
        try:
            await heading.wait_for(timeout=5_000)
            break
        except Exception:
            if attempt == 2:
                raise
            await page.wait_for_timeout(1000)
    await page.get_by_label("Display name").fill("Browser Journey Owner")
    await page.get_by_label("Email").fill(
        f"browser-journey-{uuid4().hex}@example.com"
    )
    await page.get_by_label("Password").fill(f"Corpus-Browser-{uuid4().hex}!7")
    await page.locator("form").get_by_role(
        "button", name="Create account", exact=True
    ).click()
    await page.get_by_label("Sign out", exact=True).wait_for(timeout=30_000)


async def _capture(page, directory: Path, output: list[str], name: str) -> None:
    path = directory / f"{name}.png"
    await page.screenshot(path=path, full_page=True)
    output.append(str(path.relative_to(directory.parents[2])))


async def _assert_text(page, text: str, assertions, name: str) -> None:
    count = await page.get_by_text(text, exact=True).count()
    _record_assertion(assertions, name, count > 0, {"text": text, "count": count})


async def _assert(awaitable, assertions, name: str) -> None:
    observed = await awaitable
    _record_assertion(assertions, name, bool(observed), {"visible": bool(observed)})


def _record_assertion(assertions, name: str, passed: bool, observed) -> None:
    assertions.append({"name": name, "passed": passed, "observed": observed})


def _sqlite_path(database_url: str) -> Path:
    return Path(database_url.removeprefix("sqlite+aiosqlite:///"))


def _database_state(path: Path) -> dict[str, int | None]:
    if not path.exists():
        return {"agents": 0, "agent_versions": 0, "current_version": None}
    with sqlite3.connect(path) as connection:
        agents = connection.execute("SELECT COUNT(*) FROM agents").fetchone()[0]
        versions = connection.execute(
            "SELECT COUNT(*) FROM agent_versions"
        ).fetchone()[0]
        current = connection.execute(
            "SELECT MAX(current_version) FROM agents"
        ).fetchone()[0]
    return {
        "agents": agents,
        "agent_versions": versions,
        "current_version": current,
    }


if __name__ == "__main__":
    asyncio.run(main())
