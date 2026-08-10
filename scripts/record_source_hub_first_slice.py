from __future__ import annotations

import argparse
import asyncio
import json
import subprocess
from datetime import UTC, datetime
from pathlib import Path
from uuid import uuid4

from playwright.async_api import Page, async_playwright


VALID_OPENAPI = """openapi: 3.0.3
info:
  title: Corpus Source Hub evidence probe
  version: 1.0.0
paths:
  /products:
    get:
      operationId: listProducts
      responses:
        '200':
          description: Products returned
"""

INVALID_OPENAPI = """openapi: 3.0.3
info:
  title: Corpus Source Hub failure probe
  version: 1.0.0
paths: {}
"""

DESCRIPTION = """# Source Hub evidence probe

This temporary development probe exists only to exercise Source Hub evidence capture.
"""


async def main() -> None:
    parser = argparse.ArgumentParser(
        description="Record the real local Source Hub durable-processing slice."
    )
    parser.add_argument("--url", default="http://127.0.0.1:5199/")
    parser.add_argument("--headed", action="store_true")
    args = parser.parse_args()

    repository = Path(__file__).resolve().parents[1]
    run_id = f"{datetime.now(UTC).strftime('%Y%m%dT%H%M%SZ')}-{uuid4().hex[:10]}"
    directory = repository / ".runtime" / "evaluations" / run_id
    directory.mkdir(parents=True, exist_ok=False)
    inputs = directory / "inputs"
    inputs.mkdir()
    valid_path = inputs / "source-hub-evidence.yaml"
    invalid_path = inputs / "source-hub-failure.yaml"
    description_path = inputs / "source-hub-evidence.md"
    valid_path.write_text(VALID_OPENAPI, encoding="utf-8", newline="\n")
    invalid_path.write_text(INVALID_OPENAPI, encoding="utf-8", newline="\n")
    description_path.write_text(DESCRIPTION, encoding="utf-8", newline="\n")

    screenshots: list[str] = []
    assertions: list[dict[str, object]] = []
    diagnostics: dict[str, list[dict[str, object]]] = {
        "httpErrors": [],
        "consoleErrors": [],
        "pageErrors": [],
        "requestFailures": [],
    }
    connection_secret = f"Corpus-Connection-{uuid4().hex}!9"
    secret_boundary: dict[str, object] = {
        "privateFormReceivedSecret": False,
        "saveDispatchContainedSecret": False,
        "saveDispatchArguments": None,
    }
    trace_path = directory / "browser-trace.zip"
    tracing_active = False
    video_path: str | None = None
    error: str | None = None
    worker_was_stopped = False
    owner = {
        "display_name": "Source Hub Evidence Owner",
        "email": f"source-hub-{uuid4().hex}@example.com",
        "password": f"Corpus-Source-{uuid4().hex}!7",
    }

    try:
        async with async_playwright() as playwright:
            browser = await playwright.chromium.launch(headless=not args.headed)
            context = await browser.new_context(
                viewport={"width": 1440, "height": 1000},
                record_video_dir=directory / "videos",
                record_video_size={"width": 1440, "height": 1000},
            )
            await context.tracing.start(screenshots=True, snapshots=True, sources=True)
            tracing_active = True
            page = await context.new_page()
            _attach_diagnostics(page, diagnostics)
            page.on(
                "request",
                lambda request: _observe_secret_boundary(
                    request,
                    secret=connection_secret,
                    evidence=secret_boundary,
                ),
            )
            try:
                await _register(page, args.url, owner)
                await page.get_by_role("button", name="Open Sources", exact=True).click()
                await page.get_by_role("heading", name="Source Hub", exact=True).wait_for(
                    timeout=30_000
                )
                await _capture(page, repository, directory, screenshots, "01-source-hub-empty")

                _compose(repository, "stop", "source-worker")
                worker_was_stopped = True
                await _upload(
                    page,
                    name="Durable catalog probe",
                    definition=valid_path,
                    description=description_path,
                )
                await page.get_by_text("queued", exact=True).first.wait_for(timeout=30_000)
                await _capture(page, repository, directory, screenshots, "02-source-queued")
                _record(
                    assertions,
                    "upload remains visibly queued while the durable worker is stopped",
                    await page.get_by_text("queued", exact=True).first.is_visible(),
                    {"worker": "stopped", "state": "queued"},
                )

                _compose(repository, "start", "source-worker")
                worker_was_stopped = False
                await page.get_by_text("ready", exact=True).first.wait_for(timeout=60_000)
                await page.get_by_text(
                    "The ToolRouter artifacts linked to this revision are available.",
                    exact=True,
                ).wait_for(timeout=30_000)
                await page.get_by_text(
                    "The ToolRouter artifacts linked to this revision are available.",
                    exact=True,
                ).scroll_into_view_if_needed()
                await _capture(page, repository, directory, screenshots, "03-source-ready")
                _record(
                    assertions,
                    "the same persisted source becomes ready after the durable worker resumes",
                    await page.get_by_label("Source Hub").get_by_text(
                        "Ready", exact=True
                    ).is_visible()
                    and await page.get_by_label("Source Hub").get_by_text(
                        "source-hub-evidence.md", exact=True
                    ).is_visible(),
                    {"state": "ready", "description": "source-hub-evidence.md"},
                )

                graph = page.get_by_role("heading", name="Semantic graph", exact=True)
                await graph.wait_for(timeout=30_000)
                playback = page.locator(".api-playback-steps button")
                await playback.first.wait_for(timeout=30_000)
                selected_stage = (
                    await playback.nth(1 if await playback.count() > 1 else 0).inner_text()
                )
                await playback.nth(1 if await playback.count() > 1 else 0).click()
                await page.locator(".api-playback-stage").get_by_text(
                    selected_stage.split(". ", 1)[-1], exact=True
                ).wait_for(timeout=30_000)
                await graph.scroll_into_view_if_needed()
                await _capture(
                    page,
                    repository,
                    directory,
                    screenshots,
                    "04-semantic-graph-stages",
                )
                _record(
                    assertions,
                    "persisted graph groups and selected construction stage are rendered",
                    await page.get_by_role(
                        "heading", name="Semantic groups", exact=True
                    ).is_visible()
                    and await page.get_by_role(
                        "heading", name="Recorded construction stages", exact=True
                    ).is_visible(),
                    {"selectedStage": selected_stage},
                )

                # End the retained trace before protected credential entry. Playwright
                # traces preserve request payloads, so the private-form secret must not
                # be retained in an evidence artifact.
                await context.tracing.stop(path=trace_path)
                tracing_active = False

                await page.get_by_label("Profile name").fill("Evidence profile")
                await page.get_by_label("Environment").fill("local-evidence")
                await page.get_by_label("Base URL").fill("http://127.0.0.1:9000/api")
                await page.get_by_label("Authentication").select_option("api_key")
                await page.get_by_label("Header name").fill("X-Corpus-Evidence-Key")
                await page.get_by_label("API key").fill(connection_secret)
                await page.get_by_role(
                    "button", name="Save connection", exact=True
                ).click()
                await page.get_by_text(
                    "Saved profile metadata is revision-bound. Credentials remain protected. No connection check was run.",
                    exact=True,
                ).wait_for(timeout=30_000)
                await page.get_by_text("Evidence profile", exact=True).wait_for()
                await page.get_by_text(
                    "Protected api key · credential v1", exact=True
                ).wait_for()
                await page.get_by_role(
                    "heading", name="API connections", exact=True
                ).scroll_into_view_if_needed()
                await _capture(
                    page,
                    repository,
                    directory,
                    screenshots,
                    "05-protected-api-connection",
                )
                detail_rows = page.locator(".source-detail-list > div")
                revision_id = await detail_rows.filter(
                    has_text="Revision"
                ).locator("code").inner_text()
                job_id = await detail_rows.filter(
                    has_text="Job"
                ).locator("code").inner_text()
                revision_paths = list(
                    (repository / ".runtime" / "sources").glob(
                        f"*/*/r/{revision_id}"
                    )
                )
                if len(revision_paths) != 1:
                    raise RuntimeError(
                        "The recorded Source revision could not be resolved uniquely."
                    )
                source_id = revision_paths[0].parents[1].name
                persisted_profiles = revision_paths[0] / "connections.json"
                persisted_profile_text = persisted_profiles.read_text(encoding="utf-8")
                secret_absent = (
                    connection_secret not in await page.locator("body").inner_text()
                    and connection_secret not in persisted_profile_text
                )
                _record(
                    assertions,
                    "protected profile save uses the private form and an empty public operation payload",
                    bool(secret_boundary["privateFormReceivedSecret"])
                    and not bool(secret_boundary["saveDispatchContainedSecret"])
                    and secret_boundary["saveDispatchArguments"] == {}
                    and secret_absent,
                    {
                        "privateFormReceivedSecret": bool(
                            secret_boundary["privateFormReceivedSecret"]
                        ),
                        "saveDispatchContainedSecret": bool(
                            secret_boundary["saveDispatchContainedSecret"]
                        ),
                        "saveDispatchArguments": secret_boundary[
                            "saveDispatchArguments"
                        ],
                        "secretAbsentFromPublicProfiles": secret_absent,
                        "sourceId": source_id,
                        "revisionId": revision_id,
                        "jobId": job_id,
                        "profileCount": await page.locator(
                            ".api-connection-list > li"
                        ).count(),
                        "credentialVersion": 1,
                    },
                )

                await _upload(
                    page,
                    name="Deliberate failure probe",
                    definition=invalid_path,
                    description=None,
                )
                await page.get_by_text("failed", exact=True).first.wait_for(timeout=60_000)
                await page.get_by_role("button", name="Retry processing", exact=True).wait_for()
                await page.get_by_role(
                    "button", name="Retry processing", exact=True
                ).scroll_into_view_if_needed()
                await _capture(page, repository, directory, screenshots, "06-source-failed")
                _record(
                    assertions,
                    "a real processing failure is visible and offers an explicit retry",
                    await page.get_by_text("source_processing_failed", exact=True).is_visible()
                    and await page.get_by_role(
                        "button", name="Retry processing", exact=True
                    ).is_visible(),
                    {"state": "failed", "failureCode": "source_processing_failed"},
                )

                await page.get_by_role("button", name="Retry processing", exact=True).click()
                retry_button = page.get_by_role(
                    "button", name="Retry processing", exact=True
                )
                await retry_button.wait_for(state="hidden", timeout=30_000)
                await retry_button.wait_for(state="visible", timeout=60_000)
                _record(
                    assertions,
                    "retry runs the same invalid source again and truthfully remains failed",
                    await retry_button.is_visible() and await retry_button.is_enabled(),
                    {"stateAfterRetry": "failed"},
                )

                await page.set_viewport_size({"width": 390, "height": 844})
                await page.get_by_role("heading", name="Source Hub", exact=True).scroll_into_view_if_needed()
                await page.wait_for_timeout(500)
                await _capture(
                    page,
                    repository,
                    directory,
                    screenshots,
                    "07-source-hub-mobile-390x844",
                )
                await page.get_by_role(
                    "button", name="Retry processing", exact=True
                ).scroll_into_view_if_needed()
                await page.wait_for_timeout(500)
                await _capture(
                    page,
                    repository,
                    directory,
                    screenshots,
                    "08-source-failure-mobile-390x844",
                )
                _record(
                    assertions,
                    "Source Hub remains usable at the representative mobile viewport",
                    await page.get_by_role("heading", name="Source Hub", exact=True).is_visible()
                    and await page.get_by_role(
                        "button", name="Retry processing", exact=True
                    ).is_visible(),
                    {"viewport": {"width": 390, "height": 844}},
                )
            except Exception as caught:
                error = f"{type(caught).__name__}: {caught}"
            finally:
                if worker_was_stopped:
                    _compose(repository, "start", "source-worker")
                if tracing_active:
                    await context.tracing.stop(path=trace_path)
                video = page.video
                await page.close()
                if video is not None:
                    raw_video = Path(await video.path())
                    final_video = directory / "source-hub-first-slice.webm"
                    raw_video.replace(final_video)
                    video_path = str(final_video.relative_to(repository))
                await context.close()
                await browser.close()
    finally:
        pass

    blocking = (
        diagnostics["httpErrors"]
        + diagnostics["consoleErrors"]
        + diagnostics["pageErrors"]
        + [
            failure
            for failure in diagnostics["requestFailures"]
            if failure.get("failure") != "net::ERR_ABORTED"
        ]
    )
    passed = (
        error is None
        and not blocking
        and len(assertions) == 7
        and all(bool(item["passed"]) for item in assertions)
    )
    result = {
        "schema": "corpus.source-hub-first-slice.v2",
        "runId": run_id,
        "status": "passed" if passed else "failed",
        "classification": "temporary development probes, not real Medusa execution evidence",
        "runtime": {
            "location": "local Docker Compose",
            "frontend": args.url,
            "backend": "http://127.0.0.1:8099",
            "worker": "source-worker",
            "command": "docker compose up --build -d backend source-worker frontend",
        },
        "assertions": assertions,
        "diagnostics": diagnostics,
        "screenshots": screenshots,
        "video": video_path,
        "trace": str(trace_path.relative_to(repository)),
        "error": error,
        "limitations": [
            "The OpenAPI documents are explicitly labeled development probes.",
            "This run does not prove real local Medusa operation execution.",
            "Saving a profile does not run a connection check.",
            "This slice does not execute API operations.",
            "Recorded stages can be inspected individually; ordered pause, resume, and step replay is not implemented.",
            "The browser trace ends before protected credential entry so no secret-bearing private-form request is retained.",
        ],
    }
    result_path = directory / "result.json"
    result_path.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(f"run={run_id} status={result['status']}")
    print(f"url={args.url}")
    print(f"artifact={result_path}")
    print(f"video={video_path}")
    if error is not None:
        print(f"error={error}")
    raise SystemExit(0 if passed else 1)


def _compose(repository: Path, action: str, service: str) -> None:
    subprocess.run(
        ["docker", "compose", action, service],
        cwd=repository,
        check=True,
        capture_output=True,
        text=True,
    )


def _attach_diagnostics(page: Page, diagnostics: dict[str, list[dict[str, object]]]) -> None:
    async def capture_error_response(response) -> None:
        if response.status < 400:
            return
        entry: dict[str, object] = {
            "status": response.status,
            "url": response.url,
        }
        try:
            entry["body"] = (await response.text())[:2_000]
        except Exception:
            entry["body"] = "unavailable"
        diagnostics["httpErrors"].append(entry)

    page.on("response", capture_error_response)
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
        lambda exception: diagnostics["pageErrors"].append({"message": str(exception)}),
    )
    page.on(
        "requestfailed",
        lambda request: diagnostics["requestFailures"].append(
            {"url": request.url, "method": request.method, "failure": request.failure}
        ),
    )


def _observe_secret_boundary(request, *, secret: str, evidence: dict[str, object]) -> None:
    post_data = request.post_data or ""
    if "/private-forms/sources-api-connection" in request.url:
        evidence["privateFormReceivedSecret"] = bool(
            evidence["privateFormReceivedSecret"]
        ) or secret in post_data
    if request.url.endswith("/api/routedeck/dispatch") and "sources.save_api_connection" in post_data:
        evidence["saveDispatchContainedSecret"] = secret in post_data
        try:
            evidence["saveDispatchArguments"] = json.loads(post_data).get("arguments")
        except (TypeError, json.JSONDecodeError):
            evidence["saveDispatchArguments"] = "invalid-json"


async def _register(page: Page, url: str, owner: dict[str, str]) -> None:
    await page.goto(url)
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
            await page.wait_for_timeout(1_000)
    await page.get_by_label("Display name").fill(owner["display_name"])
    await page.get_by_label("Email").fill(owner["email"])
    await page.get_by_label("Password").fill(owner["password"])
    await page.wait_for_timeout(1_000)
    sign_out = page.get_by_label("Sign out", exact=True)
    submit = page.locator("form").get_by_role(
        "button", name="Create account", exact=True
    )
    for attempt in range(3):
        await submit.click()
        try:
            await sign_out.wait_for(timeout=10_000)
            break
        except Exception:
            if attempt == 2:
                raise
            await page.wait_for_timeout(1_000)


async def _upload(
    page: Page,
    *,
    name: str,
    definition: Path,
    description: Path | None,
) -> None:
    source_hub = page.get_by_label("Source Hub")
    await source_hub.get_by_role("button", name="Add API source", exact=True).click()
    await page.get_by_role("heading", name="Add an API source", exact=True).wait_for()
    await page.get_by_label("Source name").fill(name)
    await page.get_by_label("OpenAPI or Swagger definition").set_input_files(definition)
    if description is not None:
        await page.get_by_label("Markdown description (optional)").set_input_files(
            description
        )
    await page.get_by_role("button", name="Upload and process", exact=True).click()


async def _capture(
    page: Page,
    repository: Path,
    directory: Path,
    output: list[str],
    name: str,
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
