from __future__ import annotations

import argparse
import asyncio
import json
import sqlite3
from datetime import UTC, datetime
from pathlib import Path
from uuid import uuid4

from playwright.async_api import Page, async_playwright

from corpus.evaluation.isolated_runtime import IsolatedCorpusRuntime


async def main() -> None:
    parser = argparse.ArgumentParser(
        description="Record the real owner, Workspace, and Agents acceptance journey."
    )
    parser.add_argument("--headed", action="store_true")
    parser.add_argument(
        "--skip-public",
        action="store_true",
        help="Record only the deterministic owner, Workspace, and Agents journey.",
    )
    parser.add_argument("--backend-port", type=int, default=8149)
    parser.add_argument("--frontend-port", type=int, default=5249)
    parser.add_argument(
        "--review-pause-ms",
        type=int,
        default=3_000,
        help="Pause on important completed states so the recording is reviewable.",
    )
    args = parser.parse_args()

    repository = Path(__file__).resolve().parents[1]
    run_id = f"{datetime.now(UTC).strftime('%Y%m%dT%H%M%SZ')}-{uuid4().hex[:10]}"
    directory = repository / ".runtime" / "evaluations" / run_id
    directory.mkdir(parents=True, exist_ok=False)
    runtime = IsolatedCorpusRuntime(
        repository,
        name=f"owner-agents-{uuid4().hex[:10]}",
        backend_port=args.backend_port,
        frontend_port=args.frontend_port,
    )

    started = datetime.now(UTC).isoformat()
    assertions: list[dict[str, object]] = []
    screenshots: list[str] = []
    diagnostics: dict[str, list[dict[str, object]]] = {
        "httpErrors": [],
        "consoleErrors": [],
        "pageErrors": [],
        "requestFailures": [],
        "documentRequests": [],
    }
    error: str | None = None
    video_paths: list[str] = []
    trace_path = directory / "browser-trace.zip"
    endpoints = await runtime.start()

    owner_one = {
        "display_name": "Acceptance Owner One",
        "email": f"owner-one-{uuid4().hex}@example.com",
        "password": f"Corpus-Acceptance-{uuid4().hex}!7",
    }
    owner_two = {
        "display_name": "Acceptance Owner Two",
        "email": f"owner-two-{uuid4().hex}@example.com",
        "password": f"Corpus-Isolation-{uuid4().hex}!8",
    }
    first_agent = f"Returns Operations Agent {uuid4().hex[:6]}"
    second_agent = f"Catalog QA Agent {uuid4().hex[:6]}"

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
            _observe(page, diagnostics)
            try:
                await page.goto(endpoints.frontend_url)
                await page.get_by_role("heading", name="Explore Corpus").wait_for(
                    timeout=30_000
                )
                if not args.skip_public:
                    await _capture(page, directory, screenshots, "01-public-lounge")

                    prompt = "Show me the agents in my Workspace before I sign in."
                    await page.get_by_label("Message the assistant").fill(prompt)
                    await page.get_by_role("button", name="Send message").click()
                    await page.get_by_role("heading", name="Sign in").wait_for(
                        timeout=90_000
                    )
                    assistant_reply = (
                        await page.locator("main article").last.locator("p").inner_text()
                    )
                    reply_lower = assistant_reply.lower()
                    routed_to_auth = any(
                        phrase in reply_lower
                        for phrase in ["sign in", "sign up", "authenticate", "account"]
                    )
                    _record(
                        assertions,
                        "public Lounge refuses private Workspace disclosure and routes to account access",
                        routed_to_auth
                        and "workspace" in reply_lower
                        and "here are" not in reply_lower,
                        {
                            "prompt": prompt,
                            "assistantReply": assistant_reply,
                            "signInSurfaceVisible": await page.get_by_role(
                                "heading", name="Sign in"
                            ).is_visible(),
                        },
                    )
                    await _capture(
                        page, directory, screenshots, "02-public-privacy-boundary"
                    )

                    public_video = page.video
                    await page.close()
                    if public_video is not None:
                        video_paths.append(
                            await _save_video(
                                public_video,
                                repository,
                                directory / "public-lounge-boundary.webm",
                            )
                        )

                    page = await context.new_page()
                    _observe(page, diagnostics)
                    await page.goto(endpoints.frontend_url)
                    await page.get_by_role("heading", name="Explore Corpus").wait_for(
                        timeout=30_000
                    )

                signup_document_requests = len(diagnostics["documentRequests"])
                await _register(page, owner_one)
                _record(
                    assertions,
                    "signup transitions into Workspace without a document reload",
                    len(diagnostics["documentRequests"]) == signup_document_requests,
                    {
                        "before": signup_document_requests,
                        "after": len(diagnostics["documentRequests"]),
                    },
                )
                await _assert_visible(
                    page,
                    page.get_by_label("Workspace overview"),
                    assertions,
                    "fresh signup establishes and opens the personal Workspace",
                )
                await _assert_text(
                    page,
                    "No agents have been created in this Workspace.",
                    assertions,
                    "fresh Workspace reports the real zero-agent state",
                )
                await _capture(page, directory, screenshots, "03-owner-one-workspace-zero")
                await _review_pause(page, args.review_pause_ms)

                await page.get_by_label("Sign out", exact=True).click()
                await page.get_by_role("heading", name="Explore Corpus").wait_for(timeout=30_000)
                signin_document_requests = len(diagnostics["documentRequests"])
                await _sign_in(page, owner_one)
                _record(
                    assertions,
                    "sign-in transitions into Workspace without a document reload",
                    len(diagnostics["documentRequests"]) == signin_document_requests,
                    {
                        "before": signin_document_requests,
                        "after": len(diagnostics["documentRequests"]),
                    },
                )
                await _assert_visible(
                    page,
                    page.get_by_label("Workspace overview"),
                    assertions,
                    "the created owner can sign out and sign back in",
                )
                await _capture(page, directory, screenshots, "04-owner-one-signed-in")
                await _review_pause(page, args.review_pause_ms)

                await page.get_by_role("button", name="Open Agents", exact=True).click()
                await page.locator("section.agents-home").wait_for(timeout=30_000)
                await _assert_text(
                    page,
                    "No agents yet",
                    assertions,
                    "Agents renders an honest owner-scoped empty state",
                )
                await _capture(page, directory, screenshots, "05-agents-empty")
                await _review_pause(page, args.review_pause_ms)

                await _open_create(page)
                await page.locator("section.agent-create form").get_by_role(
                    "button", name="Create agent", exact=True
                ).click()
                create_form = page.locator("section.agent-create form")
                name_validation = await create_form.get_by_label("Name").evaluate(
                    "element => element.validationMessage"
                )
                instructions_validation = await create_form.get_by_label(
                    "Instructions"
                ).evaluate("element => element.validationMessage")
                _record(
                    assertions,
                    "required Agent fields block an empty submission without persistence",
                    bool(name_validation) and bool(instructions_validation),
                    {
                        "nameValidation": name_validation,
                        "instructionsValidation": instructions_validation,
                    },
                )
                await _review_pause(page, min(args.review_pause_ms, 2_000))

                await _fill_create(
                    page,
                    first_agent,
                    "Handles returns triage for the owner Workspace.",
                    "Classify return requests, preserve owner boundaries, and report completion evidence.",
                )
                await _submit_create(page)
                await _assert_text(
                    page,
                    "Version 1",
                    assertions,
                    "creating an Agent persists and renders immutable configuration version 1",
                )
                await _capture(page, directory, screenshots, "06-first-agent-version-1")
                await _review_pause(page, args.review_pause_ms)

                version_one_url = page.url
                revised_instructions = (
                    "Classify return requests, preserve owner boundaries, record evidence, "
                    "and summarize the completed action."
                )
                await page.get_by_label("Instructions").fill(revised_instructions)
                await page.get_by_role("button", name="Save new version", exact=True).click()
                await page.get_by_text("Version 2", exact=True).last.wait_for(timeout=30_000)
                version_two_url = page.url
                _record(
                    assertions,
                    "saving an edit advances the RouteDeck resume handle",
                    version_two_url != version_one_url,
                    {"versionOneUrl": version_one_url, "versionTwoUrl": version_two_url},
                )
                await page.reload()
                await page.locator("section.agents-home").wait_for(timeout=30_000)
                await page.get_by_text("Version 2", exact=True).last.wait_for(timeout=30_000)
                _record(
                    assertions,
                    "version 2 survives a full browser reload",
                    await page.get_by_label("Instructions").input_value() == revised_instructions,
                    {"urlAfterReload": page.url},
                )
                await _capture(page, directory, screenshots, "07-first-agent-version-2-reloaded")
                await _review_pause(page, args.review_pause_ms)

                await _open_create(page)
                await _fill_create(
                    page,
                    second_agent,
                    "Checks product catalog records for quality issues.",
                    "Inspect catalog records and report only observed quality issues.",
                )
                await _submit_create(page)
                await page.get_by_text(second_agent, exact=True).first.wait_for(timeout=30_000)
                await page.get_by_text(first_agent, exact=True).first.click()
                _record(
                    assertions,
                    "the Agent inventory switches between independent Agent records",
                    await page.get_by_role("heading", name=first_agent, exact=True).is_visible()
                    and await page.get_by_text("Version 2", exact=True).last.is_visible(),
                    {"firstAgent": first_agent, "secondAgent": second_agent},
                )
                await _capture(page, directory, screenshots, "08-two-agent-management")
                await _review_pause(page, args.review_pause_ms)

                unsupported = {
                    label: await page.get_by_role("button", name=label, exact=True).count()
                    for label in [
                        "Archive",
                        "Delete",
                        "Attach source",
                        "Rollback",
                        "Version history",
                    ]
                }
                _record(
                    assertions,
                    "designed-only management actions are not exposed as fake working controls",
                    all(count == 0 for count in unsupported.values()),
                    unsupported,
                )

                await page.locator(".agents-heading").get_by_role(
                    "button", name="Back to Workspace", exact=True
                ).click()
                await page.get_by_label("Workspace overview").wait_for(timeout=30_000)
                await _assert_text(
                    page,
                    "2 active agents in this Workspace.",
                    assertions,
                    "Workspace reflects both persisted Agent identities",
                )
                await _capture(page, directory, screenshots, "09-owner-one-workspace-two")
                await _review_pause(page, args.review_pause_ms)

                await page.get_by_label("Sign out", exact=True).click()
                await page.get_by_role("heading", name="Explore Corpus").wait_for(timeout=30_000)
                await _register(page, owner_two)
                await page.get_by_role("button", name="Open Agents", exact=True).click()
                await page.locator("section.agents-home").wait_for(timeout=30_000)
                await _assert_text(
                    page,
                    "No agents yet",
                    assertions,
                    "a second owner sees an isolated empty Agent inventory",
                )
                await _capture(page, directory, screenshots, "10-owner-two-isolated-empty")
                await _review_pause(page, args.review_pause_ms)
            except Exception as caught:
                error = f"{type(caught).__name__}: {caught}"
            finally:
                await context.tracing.stop(path=trace_path)
                owner_video = page.video
                await page.close()
                if owner_video is not None:
                    video_paths.append(
                        await _save_video(
                            owner_video,
                            repository,
                            directory / "owner-agents-acceptance.webm",
                        )
                    )
                await context.close()
                await browser.close()

        database_state = _database_state(_sqlite_path(endpoints.database_url))
        _record(
            assertions,
            "database contains two Agent identities owned by one of two organizations",
            database_state["agents"] == 2
            and database_state["organizations"] == 2
            and database_state["agent_organizations"] == 1,
            database_state,
        )
        _record(
            assertions,
            "database retains three immutable Agent configurations",
            database_state["agent_versions"] == 3,
            database_state,
        )
    finally:
        await runtime.close()

    blocking_diagnostics = (
        diagnostics["httpErrors"]
        + diagnostics["consoleErrors"]
        + diagnostics["pageErrors"]
    )
    passed = (
        error is None
        and not blocking_diagnostics
        and bool(assertions)
        and all(bool(item["passed"]) for item in assertions)
    )
    artifact = {
        "schema": "corpus.owner-agents-acceptance.v1",
        "scope": "owner-agents" if args.skip_public else "public-and-owner-agents",
        "runId": run_id,
        "status": "passed" if passed else "failed",
        "startedAt": started,
        "completedAt": datetime.now(UTC).isoformat(),
        "runtime": {
            "location": "local isolated runtime",
            "frontend": endpoints.frontend_url,
            "backend": endpoints.backend_url,
            "database": endpoints.database_url,
        },
        "assertions": assertions,
        "diagnostics": diagnostics,
        "screenshots": screenshots,
        "videos": video_paths,
        "trace": str(trace_path.relative_to(repository)),
        "databaseState": _database_state(_sqlite_path(endpoints.database_url)),
        "error": error,
    }
    artifact_path = directory / "result.json"
    artifact_path.write_text(json.dumps(artifact, indent=2) + "\n", encoding="utf-8")
    print(f"run={run_id} status={artifact['status']}")
    print(f"frontend={endpoints.frontend_url}")
    print(f"backend={endpoints.backend_url}")
    print(f"artifact={artifact_path}")
    print(f"videos={','.join(video_paths)}")
    if error is not None:
        print(f"error={error}")
    raise SystemExit(0 if passed else 1)


def _observe(page: Page, diagnostics: dict[str, list[dict[str, object]]]) -> None:
    page.on(
        "request",
        lambda request: diagnostics["documentRequests"].append(
            {
                "method": request.method,
                "url": request.url,
                "observedAt": datetime.now(UTC).isoformat(),
            }
        )
        if request.resource_type == "document"
        else None,
    )
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
            {
                "url": request.url,
                "method": request.method,
                "failure": request.failure,
            }
        ),
    )


async def _register(page: Page, owner: dict[str, str]) -> None:
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
    await page.locator("form").get_by_role(
        "button", name="Create account", exact=True
    ).click()
    await page.get_by_label("Sign out", exact=True).wait_for(timeout=30_000)


async def _sign_in(page: Page, owner: dict[str, str]) -> None:
    await page.get_by_role("button", name="Sign in", exact=True).click()
    surface = page.get_by_role("region", name="Sign in")
    await surface.get_by_label("Email").fill(owner["email"])
    await surface.get_by_label("Password").fill(owner["password"])
    await surface.get_by_role("button", name="Sign in", exact=True).click()
    await page.get_by_label("Sign out", exact=True).wait_for(timeout=30_000)


async def _open_create(page: Page) -> None:
    await page.locator(".agents-heading").get_by_role(
        "button", name="Create agent", exact=True
    ).click()
    await page.locator("section.agent-create").wait_for(timeout=30_000)
    # Let the RouteDeck surface transition settle before typing. Otherwise a
    # late surface-state update can replace the just-edited form controls.
    await page.wait_for_timeout(750)


async def _fill_create(
    page: Page, name: str, description: str, instructions: str
) -> None:
    form = page.locator("section.agent-create form")
    await form.get_by_label("Name").fill(name)
    await form.get_by_label("Description").fill(description)
    await form.get_by_label("Instructions").fill(instructions)


async def _submit_create(page: Page) -> None:
    await page.locator("section.agent-create form").get_by_role(
        "button", name="Create agent", exact=True
    ).click()
    await page.locator("section.agents-home").wait_for(timeout=30_000)


async def _capture(
    page: Page, directory: Path, output: list[str], name: str
) -> None:
    path = directory / f"{name}.png"
    await page.screenshot(path=path, full_page=True)
    output.append(str(path.relative_to(directory.parents[2])))


async def _review_pause(page: Page, duration_ms: int) -> None:
    if duration_ms > 0:
        await page.wait_for_timeout(duration_ms)


async def _save_video(video, repository: Path, final_path: Path) -> str:
    raw_path = Path(await video.path())
    raw_path.replace(final_path)
    return str(final_path.relative_to(repository))


async def _assert_text(
    page: Page, value: str, assertions: list[dict[str, object]], name: str
) -> None:
    locator = page.get_by_text(value, exact=True)
    try:
        await locator.last.wait_for(timeout=15_000)
    except Exception:
        pass
    count = await locator.count()
    _record(assertions, name, count > 0, {"text": value, "count": count})


async def _assert_visible(
    page: Page, locator, assertions: list[dict[str, object]], name: str
) -> None:
    visible = await locator.is_visible()
    _record(assertions, name, visible, {"visible": visible})


def _record(
    assertions: list[dict[str, object]], name: str, passed: bool, observed: object
) -> None:
    assertions.append({"name": name, "passed": passed, "observed": observed})


def _sqlite_path(database_url: str) -> Path:
    return Path(database_url.removeprefix("sqlite+aiosqlite:///"))


def _database_state(path: Path) -> dict[str, int | None]:
    if not path.exists():
        return {
            "organizations": 0,
            "agents": 0,
            "agent_versions": 0,
            "agent_organizations": 0,
            "current_version": None,
        }
    with sqlite3.connect(path) as connection:
        organizations = connection.execute(
            "SELECT COUNT(*) FROM organizations"
        ).fetchone()[0]
        agents = connection.execute("SELECT COUNT(*) FROM agents").fetchone()[0]
        versions = connection.execute(
            "SELECT COUNT(*) FROM agent_versions"
        ).fetchone()[0]
        agent_organizations = connection.execute(
            "SELECT COUNT(DISTINCT organization_id) FROM agents"
        ).fetchone()[0]
        current = connection.execute(
            "SELECT MAX(current_version) FROM agents"
        ).fetchone()[0]
    return {
        "organizations": organizations,
        "agents": agents,
        "agent_versions": versions,
        "agent_organizations": agent_organizations,
        "current_version": current,
    }


if __name__ == "__main__":
    asyncio.run(main())
