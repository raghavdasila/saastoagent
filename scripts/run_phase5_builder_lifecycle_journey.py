from __future__ import annotations

import argparse
import asyncio
import json
import secrets
import shutil
import subprocess
import time
from datetime import UTC, datetime
from pathlib import Path
from urllib.parse import urlsplit

from playwright.async_api import Page, Response, async_playwright


ROOT = Path(__file__).resolve().parents[1]
ARTIFACT_ROOT = ROOT / "artifacts" / "phase5-builder-lifecycle"
CONTAINER = "corpus-development-backend-1"
OWNER_EMAIL = "horizontal-d01394ad1d284d44bd866caa5bcab7ac@example.com"
ORGANIZATION_ID = "11463d61-c275-425e-aecc-5a6df41c9372"
AGENT_ID = "c7a10ce0-b230-43f1-87d3-c79e71a84d34"
AGENT_NAME = "Shopping Assistant"
BUILD_ID = "c86897ee-daf6-44a5-95cc-5310370a24b5"


RESET_CODE = r"""
import asyncio, json, sqlite3, sys
from datetime import timedelta
from corpus.auth.service import AuthService
from corpus.persistence import CorpusDatabase
from corpus.auth.config import AuthSettings
from corpus.persistence.config import CorpusDatabaseSettings
email, agent_id, expected_organization = sys.argv[1:4]
password = sys.stdin.read().strip()
def identity():
    db=sqlite3.connect('/var/lib/corpus/corpus.sqlite3'); db.row_factory=sqlite3.Row
    row=db.execute('''SELECT u.email, lower(m.organization_id) organization_id
      FROM users u JOIN memberships m ON m.user_id=u.id
      JOIN agents a ON a.organization_id=m.organization_id
      WHERE lower(u.email)=lower(?) AND replace(lower(a.id),'-','')=replace(lower(?),'-','')''',(email,agent_id)).fetchone()
    db.close()
    if row is None or row['organization_id'].replace('-','') != expected_organization.replace('-','').lower():
        raise RuntimeError('The retained Builder owner lineage is unavailable.')
    return dict(row)
async def run():
    owner=identity(); settings=AuthSettings.from_env(); database=CorpusDatabase(CorpusDatabaseSettings.from_env().url)
    service=AuthService(database,reset_secret=settings.reset_secret.get_secret_value(),verification_secret=settings.verification_secret.get_secret_value(),access_lifetime=timedelta(minutes=settings.access_token_minutes),idle_lifetime=timedelta(days=settings.idle_session_days),absolute_lifetime=timedelta(days=settings.absolute_session_days),reset_token_lifetime=timedelta(hours=settings.reset_token_hours),verification_token_lifetime=timedelta(hours=settings.verification_token_hours))
    try:
        reset=await service.request_password_reset(owner['email'])
        if reset is None: raise RuntimeError('The retained owner reset token is unavailable.')
        await service.confirm_password_reset(reset.token,password); print(json.dumps(owner))
    finally: await database.close()
asyncio.run(run())
"""


def arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Record isolated Builder runtime lifecycle evidence.")
    parser.add_argument("--url", default="http://127.0.0.1:5199")
    parser.add_argument("--headed", action="store_true")
    parser.add_argument("--verify-existing", action="store_true")
    return parser.parse_args()


def _owner_reset(password: str) -> dict[str, str]:
    completed = subprocess.run(
        ["docker", "exec", "-i", "-w", "/workspace/corpus/backend", CONTAINER,
         "python", "-c", RESET_CODE, OWNER_EMAIL, AGENT_ID, ORGANIZATION_ID],
        input=password, text=True, capture_output=True, timeout=60, check=False,
    )
    if completed.returncode != 0:
        raise RuntimeError("The exact local Builder owner could not be recovered.")
    return json.loads(completed.stdout.strip())


def _lineage() -> dict[str, object]:
    code = r"""
import json,sqlite3,sys
organization_id,agent_id,build_id=sys.argv[1:]
db=sqlite3.connect('/var/lib/corpus/corpus.sqlite3'); db.row_factory=sqlite3.Row
build=db.execute('''SELECT id,agent_id,status,runtime_lifecycle,runtime_build_hash,navgraph_hash,source_bindings,allowed_operation_ids
 FROM agent_runnable_builds WHERE replace(lower(organization_id),'-','')=replace(lower(?),'-','')
 AND replace(lower(agent_id),'-','')=replace(lower(?),'-','') AND replace(lower(id),'-','')=replace(lower(?),'-','')''',(organization_id,agent_id,build_id)).fetchone()
lineage=db.execute('''SELECT id,build_id,agent_version FROM agent_build_lineages WHERE replace(lower(build_id),'-','')=replace(lower(?),'-','')''',(build_id,)).fetchall()
cases=db.execute('''SELECT id,build_id,removed_at FROM agent_evaluation_cases WHERE replace(lower(build_id),'-','')=replace(lower(?),'-','')''',(build_id,)).fetchall()
print(json.dumps({'build':dict(build) if build else None,'lineage':[dict(x) for x in lineage],'cases':[dict(x) for x in cases]})); db.close()
"""
    completed = subprocess.run(
        ["docker", "exec", "-w", "/workspace/corpus/backend", CONTAINER,
         "python", "-c", code, ORGANIZATION_ID, AGENT_ID, BUILD_ID],
        text=True, capture_output=True, timeout=30, check=False,
    )
    if completed.returncode != 0:
        raise RuntimeError("The exact Builder lineage is unavailable.")
    return json.loads(completed.stdout)


async def _maximize(page: Page) -> None:
    shell = page.locator("[data-agent-shell]")
    if await shell.get_attribute("data-surface-layout") != "split":
        await page.get_by_role("button", name="Maximize surface", exact=True).click()
    if await shell.get_attribute("data-surface-layout") != "split":
        raise RuntimeError("Builder did not maximize beside chat.")


async def _capture(page: Page, directory: Path, name: str, screenshots: list[str]) -> None:
    await page.wait_for_timeout(1_000)
    path = directory / f"{name}.png"
    await page.screenshot(path=path, full_page=False)
    screenshots.append(str(path.relative_to(ROOT)))
    await page.wait_for_timeout(900)


async def _submit_sign_in(page: Page, email: str, password: str) -> None:
    deadline = asyncio.get_running_loop().time() + 30
    last_error: Exception | None = None
    while asyncio.get_running_loop().time() < deadline:
        try:
            form = page.locator("form").filter(has=page.get_by_label("Email", exact=True))
            if await form.count() != 1:
                raise RuntimeError("The exact sign-in private form is unavailable or ambiguous.")
            email_input = form.get_by_label("Email", exact=True)
            password_input = form.get_by_label("Password", exact=True)
            await email_input.fill(email, timeout=1_500)
            await password_input.fill(password, timeout=1_500)
            if await email_input.input_value() != email or await password_input.input_value() != password:
                raise RuntimeError("The exact sign-in values did not survive the private-form render.")
            await form.get_by_role("button", name="Sign in", exact=True).click(timeout=1_500)
            return
        except Exception as caught:
            last_error = caught
            await page.wait_for_timeout(250)
    raise RuntimeError("The exact sign-in values could not be bound before submit.") from last_error


async def _wait_lifecycle(card, value: str) -> None:
    for _ in range(120):
        if await card.get_attribute("data-runtime-lifecycle") == value:
            return
        await card.page.wait_for_timeout(250)
    raise RuntimeError(f"The exact build did not reach runtime lifecycle {value}.")


async def run(args: argparse.Namespace) -> int:
    run_id = datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ") + "-" + secrets.token_hex(4)
    directory = ARTIFACT_ROOT / run_id; videos = directory / "raw-video"; videos.mkdir(parents=True)
    screenshots: list[str] = []; operations: list[dict[str, object]] = []
    diagnostics: dict[str, list[dict[str, object]]] = {"httpErrors": [], "consoleErrors": [], "pageErrors": [], "requestFailures": []}
    password = "Corpus-Builder-" + secrets.token_urlsafe(24) + "!9"
    destroy_password = "Corpus-Builder-Destroy-" + secrets.token_urlsafe(24) + "!9"
    before = _lineage(); after: dict[str, object] | None = None
    browser = context = page = None; video_path: Path | None = None; error: str | None = None; recovered = False
    tasks: set[asyncio.Task[None]] = set(); started = time.monotonic()

    async def observe(response: Response) -> None:
        path = urlsplit(response.url).path
        if response.status >= 400 and not (path.startswith("/api/routedeck/reviews/") and path.endswith("/reject") and response.status == 409):
            diagnostics["httpErrors"].append({"method": response.request.method, "path": path, "status": response.status})
        if response.status == 200 and response.request.method == "POST" and path == "/api/routedeck/dispatch":
            try:
                body = await response.json(); operation_id = body.get("operation_id") or body.get("operationId")
                if isinstance(operation_id, str): operations.append({"operationId": operation_id, "disposition": body.get("disposition"), "outcome": body.get("outcome")})
            except Exception: pass
    def schedule(response: Response) -> None:
        task=asyncio.create_task(observe(response)); tasks.add(task); task.add_done_callback(tasks.discard)

    try:
        expected_preflight = "removed" if args.verify_existing else "stopped"
        if before.get("build", {}).get("runtime_lifecycle") != expected_preflight:
            raise RuntimeError(f"The disposable Builder runtime is not {expected_preflight} at preflight.")
        if len(before.get("lineage", [])) != 1 or len(before.get("cases", [])) < 1:
            raise RuntimeError("The disposable Builder lineage/history preflight failed.")
        identity=_owner_reset(password); recovered=True
        async with async_playwright() as playwright:
            browser=await playwright.chromium.launch(headless=not args.headed)
            context=await browser.new_context(viewport={"width":1440,"height":1000},record_video_dir=videos,record_video_size={"width":1440,"height":1000})
            page=await context.new_page(); page.on("response",schedule)
            page.on("console",lambda item: diagnostics["consoleErrors"].append({"type":item.type,"text":item.text}) if item.type in {"warning","error"} else None)
            page.on("pageerror",lambda item: diagnostics["pageErrors"].append({"message":str(item)}))
            page.on("requestfailed",lambda request: diagnostics["requestFailures"].append({"method":request.method,"path":urlsplit(request.url).path,"failure":request.failure}))
            await page.goto(args.url); await page.get_by_role("heading",name="Explore Corpus",exact=True).wait_for(timeout=30_000)
            await page.get_by_role("button",name="Sign in",exact=True).click(); await page.get_by_role("heading",name="Sign in",exact=True).wait_for()
            await _submit_sign_in(page, identity["email"], password)
            await page.get_by_label("Sign out",exact=True).wait_for(timeout=30_000)
            await page.locator("section.workspace-home").get_by_role("button",name="Open Agents",exact=True).click()
            agents=page.locator("section.agents-home"); await agents.locator("#agents-home-title").wait_for(timeout=30_000)
            exact_agent=agents.get_by_label("Agent inventory").get_by_role("button").filter(has_text=AGENT_NAME)
            await exact_agent.wait_for(state="visible", timeout=30_000)
            if await exact_agent.count()!=1: raise RuntimeError("The exact Builder Agent is unavailable or ambiguous.")
            await exact_agent.click(); builds_button=agents.get_by_role("button",name="Builds",exact=True)
            for _ in range(120):
                if await builds_button.is_enabled(): break
                await page.wait_for_timeout(250)
            await builds_button.click(); await page.locator("#builder-title").wait_for(timeout=60_000); await _maximize(page)
            builder=page.locator("section.builder-home"); card=builder.locator("li.builder-build-card").filter(has_text=BUILD_ID)
            await card.wait_for(state="visible", timeout=30_000)
            if await card.count()!=1: raise RuntimeError("The exact disposable build is unavailable or ambiguous.")
            await card.scroll_into_view_if_needed()
            if not args.verify_existing:
                await _capture(page,directory,"01-stopped-runtime",screenshots)
                await card.get_by_role("button",name="Start runtime",exact=True).click(); await _wait_lifecycle(card,"running")
                await card.get_by_role("button",name="Pause runtime",exact=True).click(); await _wait_lifecycle(card,"paused"); await _capture(page,directory,"02-paused-runtime",screenshots)
                await page.reload(wait_until="domcontentloaded"); await page.locator("#builder-title").wait_for(timeout=60_000); await _maximize(page)
                builder=page.locator("section.builder-home"); card=builder.locator("li.builder-build-card").filter(has_text=BUILD_ID); await _wait_lifecycle(card,"paused")
                await card.get_by_role("button",name="Resume runtime",exact=True).click(); await _wait_lifecycle(card,"running")
                await card.get_by_role("button",name="Stop runtime",exact=True).click(); await _wait_lifecycle(card,"stopped"); await _capture(page,directory,"03-stopped-after-resume",screenshots)
                await card.get_by_role("button",name="Delete build runtime",exact=True).click()
                review=page.locator("section.builder-delete-review"); await review.get_by_role("heading",name="Remove this draft runtime?",exact=True).wait_for(timeout=30_000)
                await _capture(page,directory,"04-removal-review",screenshots); await review.get_by_role("button",name="Keep build unchanged",exact=True).click()
                await review.wait_for(state="detached",timeout=30_000); await _wait_lifecycle(card,"stopped")
                await card.get_by_role("button",name="Delete build runtime",exact=True).click(); review=page.locator("section.builder-delete-review")
                await review.get_by_role("button",name="Remove draft runtime",exact=True).click(); await review.wait_for(state="detached",timeout=30_000)
                await _wait_lifecycle(card,"removed")
                await page.reload(wait_until="domcontentloaded"); await page.locator("#builder-title").wait_for(timeout=60_000); await _maximize(page)
                builder=page.locator("section.builder-home"); card=builder.locator("li.builder-build-card").filter(has_text=BUILD_ID); await _wait_lifecycle(card,"removed")
            await card.get_by_text("The draft runtime was removed.",exact=False).wait_for()
            await _capture(page,directory,"05-removed-runtime-lineage-retained",screenshots)
            if tasks: await asyncio.gather(*tuple(tasks),return_exceptions=True)
            after=_lineage()
            if after.get("build",{}).get("runtime_lifecycle")!="removed": raise RuntimeError("The exact runtime removal was not retained.")
            if before["build"]["runtime_build_hash"]!=after["build"]["runtime_build_hash"] or before["build"]["navgraph_hash"]!=after["build"]["navgraph_hash"]: raise RuntimeError("Immutable build identity changed during runtime lifecycle control.")
            if before["lineage"]!=after["lineage"] or before["cases"]!=after["cases"]: raise RuntimeError("Immutable build or Evaluation history changed during runtime removal.")
            exact=[x.get("operationId") for x in operations]
            if not args.verify_existing:
                required=["builder.run","builder.pause","builder.run","builder.stop","builder.delete","builder.delete"]
                cursor=0
                for value in exact:
                    if cursor<len(required) and value==required[cursor]: cursor+=1
                if cursor!=len(required): raise RuntimeError("The exact supervised Builder lifecycle sequence was not observed.")
            if diagnostics["httpErrors"] or diagnostics["consoleErrors"] or diagnostics["pageErrors"]: raise RuntimeError("The Builder interval contains unexpected diagnostics.")
    except Exception as caught: error=f"{type(caught).__name__}: {caught}"
    finally:
        if page is not None and error is not None:
            try: await page.screenshot(path=directory/"99-failure.png",full_page=False)
            except Exception: pass
        if page is not None:
            try:
                raw=page.video
                if raw is not None: await page.close(); video_path=Path(await raw.path())
            except Exception: pass
        if context is not None:
            try: await context.close()
            except Exception: pass
        if browser is not None:
            try: await browser.close()
            except Exception: pass
        if recovered:
            try: _owner_reset(destroy_password)
            except Exception as reset_error: error=error or f"RuntimeError: temporary owner credential cleanup failed: {reset_error}"
    if video_path is not None and video_path.is_file():
        final=directory/"phase5-builder-lifecycle-normal-speed.webm"; video_path.replace(final); video_path=final
    result={"runId":run_id,"status":"passed" if error is None else "failed","scope":"isolated Phase 5 Builder runtime lifecycle" if not args.verify_existing else "isolated Phase 5 durable Builder lifecycle verification","ids":{"organizationId":ORGANIZATION_ID,"agentId":AGENT_ID,"buildId":BUILD_ID},"before":before,"after":after,"operations":operations,"screenshots":screenshots,"video":None if video_path is None else str(video_path.relative_to(ROOT)),"videoMetadata":{"playbackRate":1.0,"width":1440,"height":1000,"maximizedSurface":True},"diagnostics":diagnostics,"elapsedSeconds":round(time.monotonic()-started,3),"error":error}
    result_path=directory/"result.json"; result_path.write_text(json.dumps(result,indent=2)+"\n",encoding="utf-8")
    for artifact in directory.rglob("*"):
        if artifact.is_file() and (password.encode() in artifact.read_bytes() or destroy_password.encode() in artifact.read_bytes()): shutil.rmtree(directory); raise RuntimeError("Credential canary reached the Builder evidence directory; evidence was removed.")
    print(f"run={run_id} status={result['status']}"); print(f"artifact={result_path}"); print(f"video={result['video']}")
    if error is not None: print("error="+error.encode("ascii","backslashreplace").decode("ascii"))
    return 0 if error is None else 1


async def main() -> int:
    async with asyncio.timeout(13*60): return await run(arguments())


if __name__ == "__main__": raise SystemExit(asyncio.run(main()))
