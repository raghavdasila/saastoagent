from __future__ import annotations

import argparse
import asyncio
import json
from datetime import UTC, datetime
from pathlib import Path
from uuid import uuid4

from playwright.async_api import async_playwright


async def main() -> None:
    parser = argparse.ArgumentParser(description="Record the live Corpus Design Studio.")
    parser.add_argument("--url", default="http://127.0.0.1:8782/")
    parser.add_argument("--headed", action="store_true")
    args = parser.parse_args()

    repository = Path(__file__).resolve().parents[1]
    run_id = f"{datetime.now(UTC).strftime('%Y%m%dT%H%M%SZ')}-{uuid4().hex[:10]}"
    directory = repository / ".runtime" / "evaluations" / run_id
    directory.mkdir(parents=True, exist_ok=False)
    screenshots: list[str] = []
    assertions: list[dict[str, object]] = []
    diagnostics: dict[str, list[dict[str, object]]] = {
        "httpErrors": [],
        "consoleErrors": [],
        "pageErrors": [],
    }
    trace_path = directory / "browser-trace.zip"
    error: str | None = None
    video_path: str | None = None
    try:
        async with async_playwright() as playwright:
            browser = await playwright.chromium.launch(headless=not args.headed)
            context = await browser.new_context(
                viewport={"width": 1440, "height": 1000},
                record_video_dir=directory / "videos",
                record_video_size={"width": 1440, "height": 1000},
            )
            await context.tracing.start(screenshots=True, snapshots=True, sources=True)
            page = await context.new_page()
            page.on(
                "response",
                lambda response: diagnostics["httpErrors"].append(
                    {"status": response.status, "url": response.url}
                )
                if response.status >= 400
                else None,
            )
            page.on(
                "console",
                lambda message: diagnostics["consoleErrors"].append(
                    {"type": message.type, "text": message.text}
                )
                if message.type in {"warning", "error"}
                else None,
            )
            page.on(
                "pageerror",
                lambda exception: diagnostics["pageErrors"].append(
                    {"message": str(exception)}
                ),
            )
            try:
                await page.goto(args.url)
                await page.get_by_role(
                    "heading", name="RouteDeck Agent Design Studio"
                ).wait_for(timeout=30_000)
                await _capture(page, repository, directory, screenshots, "01-studio-overview")
                _record(
                    assertions,
                    "the repository-owned Studio state loads without the invalid-state alert",
                    await page.get_by_text("The saved studio data is invalid.").count() == 0
                    and await page.get_by_text("Saved", exact=True).is_visible(),
                    {"url": page.url},
                )

                await page.get_by_role("button", name="Agents 9", exact=True).click()
                await page.get_by_role("button", name="View agents · 10 blocking issues").wait_for()
                await _capture(page, repository, directory, screenshots, "02-studio-agents-boundary")
                _record(
                    assertions,
                    "the Agents feature exposes nine product behaviors in the Studio",
                    await page.get_by_text("Agents · 9 behaviors", exact=True).is_visible(),
                    {"feature": "Agents", "behaviorCount": 9},
                )

                await page.get_by_role(
                    "button", name="Create an agent · 10 blocking issues", exact=True
                ).click()
                await page.get_by_role("heading", name="Create an agent", exact=True).first.wait_for()
                await _capture(page, repository, directory, screenshots, "03-studio-create-agent")

                eval_region = page.get_by_role("region", name="Evals")
                await eval_region.scroll_into_view_if_needed()
                await page.wait_for_timeout(500)
                await _capture(page, repository, directory, screenshots, "04-studio-state-evaluator")
                state_case = page.get_by_role(
                    "button",
                    name="Create persists one Agent and configuration version 1 Blocking Normal · State 6 issues Stale",
                    exact=True,
                )
                _record(
                    assertions,
                    "the implemented create behavior has an explicit Normal and State evaluator definition",
                    await state_case.is_visible(),
                    {
                        "case": "Create persists one Agent and configuration version 1",
                        "coverage": ["normal", "state"],
                    },
                )
                await state_case.click()
                await page.wait_for_timeout(400)
                await _capture(page, repository, directory, screenshots, "05-studio-state-eval-case")
            except Exception as caught:
                error = f"{type(caught).__name__}: {caught}"
            finally:
                await context.tracing.stop(path=trace_path)
                video = page.video
                await page.close()
                if video is not None:
                    raw_video = Path(await video.path())
                    final_video = directory / "design-studio-walkthrough.webm"
                    raw_video.replace(final_video)
                    video_path = str(final_video.relative_to(repository))
                await context.close()
                await browser.close()
    finally:
        pass

    blocking_diagnostics = (
        diagnostics["httpErrors"]
        + diagnostics["consoleErrors"]
        + diagnostics["pageErrors"]
    )
    passed = (
        error is None
        and not blocking_diagnostics
        and len(assertions) == 3
        and all(bool(item["passed"]) for item in assertions)
    )
    artifact = {
        "schema": "corpus.design-studio-walkthrough.v1",
        "runId": run_id,
        "status": "passed" if passed else "failed",
        "runtime": {"location": "local development server", "url": args.url},
        "assertions": assertions,
        "diagnostics": diagnostics,
        "screenshots": screenshots,
        "video": video_path,
        "trace": str(trace_path.relative_to(repository)),
        "error": error,
    }
    artifact_path = directory / "result.json"
    artifact_path.write_text(json.dumps(artifact, indent=2) + "\n", encoding="utf-8")
    print(f"run={run_id} status={artifact['status']}")
    print(f"url={args.url}")
    print(f"artifact={artifact_path}")
    print(f"video={video_path}")
    if error is not None:
        print(f"error={error}")
    raise SystemExit(0 if passed else 1)


async def _capture(
    page, repository: Path, directory: Path, output: list[str], name: str
) -> None:
    path = directory / f"{name}.png"
    await page.screenshot(path=path, full_page=True)
    output.append(str(path.relative_to(repository)))


def _record(
    assertions: list[dict[str, object]], name: str, passed: bool, observed: object
) -> None:
    assertions.append({"name": name, "passed": passed, "observed": observed})


if __name__ == "__main__":
    asyncio.run(main())
