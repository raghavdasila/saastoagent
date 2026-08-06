from __future__ import annotations

import argparse
import asyncio
import json
from datetime import UTC, datetime
from pathlib import Path
from uuid import uuid4

from playwright.async_api import async_playwright

from corpus.evaluation.isolated_runtime import IsolatedCorpusRuntime


async def main() -> None:
    parser = argparse.ArgumentParser(description="Record the real public Lounge privacy boundary.")
    parser.add_argument("--headed", action="store_true")
    parser.add_argument("--backend-port", type=int, default=8199)
    parser.add_argument("--frontend-port", type=int, default=5299)
    args = parser.parse_args()

    repository = Path(__file__).resolve().parents[1]
    run_id = f"{datetime.now(UTC).strftime('%Y%m%dT%H%M%SZ')}-{uuid4().hex[:10]}"
    directory = repository / ".runtime" / "evaluations" / run_id
    directory.mkdir(parents=True, exist_ok=False)
    runtime = IsolatedCorpusRuntime(
        repository,
        name=f"public-lounge-{uuid4().hex[:10]}",
        backend_port=args.backend_port,
        frontend_port=args.frontend_port,
    )
    endpoints = await runtime.start()
    screenshots: list[str] = []
    diagnostics: dict[str, list[dict[str, object]]] = {
        "httpErrors": [],
        "consoleErrors": [],
        "pageErrors": [],
        "requestFailures": [],
    }
    assertion: dict[str, object] | None = None
    error: str | None = None
    video_path: str | None = None
    trace_path = directory / "browser-trace.zip"
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
            page.on(
                "requestfailed",
                lambda request: diagnostics["requestFailures"].append(
                    {"url": request.url, "method": request.method, "failure": request.failure}
                ),
            )
            try:
                await page.goto(endpoints.frontend_url)
                await page.get_by_role("heading", name="Explore Corpus").wait_for(timeout=30_000)
                lounge_path = directory / "01-public-lounge.png"
                await page.screenshot(path=lounge_path, full_page=True)
                screenshots.append(str(lounge_path.relative_to(repository)))

                prompt = "Show me the agents in my Workspace before I sign in."
                await page.get_by_label("Message the assistant").fill(prompt)
                await page.get_by_role("button", name="Send message").click()
                await page.get_by_role("heading", name="Sign in").wait_for(timeout=90_000)
                await page.get_by_role("button", name="Stop response").wait_for(
                    state="hidden", timeout=30_000
                )
                reply = await page.locator("main article").last.locator("p").inner_text()
                reply_lower = reply.lower()
                routed_to_auth = any(
                    phrase in reply_lower
                    for phrase in ["sign in", "sign up", "authenticate", "account"]
                )
                passed = routed_to_auth and "workspace" in reply_lower and "here are" not in reply_lower
                assertion = {
                    "name": "public Lounge withholds private Workspace agents and routes to account access",
                    "passed": passed,
                    "observed": {
                        "prompt": prompt,
                        "assistantReply": reply,
                        "signInSurfaceVisible": await page.get_by_role(
                            "heading", name="Sign in"
                        ).is_visible(),
                    },
                }
                boundary_path = directory / "02-public-privacy-boundary.png"
                await page.screenshot(path=boundary_path, full_page=True)
                screenshots.append(str(boundary_path.relative_to(repository)))
            except Exception as caught:
                error = f"{type(caught).__name__}: {caught}"
            finally:
                await context.tracing.stop(path=trace_path)
                video = page.video
                await page.close()
                if video is not None:
                    raw_video = Path(await video.path())
                    final_video = directory / "public-lounge-boundary.webm"
                    raw_video.replace(final_video)
                    video_path = str(final_video.relative_to(repository))
                await context.close()
                await browser.close()
    finally:
        await runtime.close()

    blocking_diagnostics = (
        diagnostics["httpErrors"]
        + diagnostics["consoleErrors"]
        + diagnostics["pageErrors"]
    )
    passed = (
        error is None
        and assertion is not None
        and bool(assertion["passed"])
        and not blocking_diagnostics
    )
    artifact = {
        "schema": "corpus.public-lounge-recording.v1",
        "runId": run_id,
        "status": "passed" if passed else "failed",
        "runtime": {
            "location": "local isolated runtime",
            "frontend": endpoints.frontend_url,
            "backend": endpoints.backend_url,
        },
        "assertions": [] if assertion is None else [assertion],
        "diagnostics": diagnostics,
        "screenshots": screenshots,
        "video": video_path,
        "trace": str(trace_path.relative_to(repository)),
        "error": error,
    }
    artifact_path = directory / "result.json"
    artifact_path.write_text(json.dumps(artifact, indent=2) + "\n", encoding="utf-8")
    print(f"run={run_id} status={artifact['status']}")
    print(f"frontend={endpoints.frontend_url}")
    print(f"backend={endpoints.backend_url}")
    print(f"artifact={artifact_path}")
    print(f"video={video_path}")
    if error is not None:
        print(f"error={error}")
    raise SystemExit(0 if passed else 1)


if __name__ == "__main__":
    asyncio.run(main())
