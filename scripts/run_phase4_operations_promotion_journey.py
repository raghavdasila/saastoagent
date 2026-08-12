from __future__ import annotations

import argparse
import asyncio
import hashlib
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
ARTIFACT_ROOT = ROOT / "artifacts" / "phase4-operations-promotion"
CONTAINER = "corpus-development-backend-1"
RETAINED_CONVERSATION_ID = "Ttzpd0t0NBNtzYcXEDSoKj3a3zl901ZA"
OWNER_EMAIL = "horizontal-f644228a58384de4a067adde260c1f6a@example.com"
AGENT_ID = "1f99c29b-0097-436e-af59-0dd6d0966ebf"
AGENT_NAME = "Shopping assistant"
BUILD_ID = "bc1bd233-c2ac-48cd-ba36-8ab23f84c496"
ORGANIZATION_ID = "04abb0ca-49c3-4af0-a181-e010c995f5e7"
RUNTIME_DEPLOYMENT_ID = "dep_91cf72a9dfa54804b4c8f6528c768f11"
INTERACTION_ID = "int_78f435f2522e47c5836a0e58ce7e88ed"
PUBLIC_SESSION_ID = "ses_07af5273655c49af96c6cc2a67d120aa"
SET_NAME = "Phase 4 deployed interaction evidence"
CATEGORY = "deployed-interaction"


RESET_CODE = r"""
import asyncio, json, os, sqlite3, sys
from datetime import timedelta
from corpus.auth.service import AuthService
from corpus.persistence import CorpusDatabase
from corpus.auth.config import AuthSettings
from corpus.persistence.config import CorpusDatabaseSettings

email, agent_id, expected_organization = sys.argv[1:4]
password = sys.stdin.read().strip()

def identity():
    db = sqlite3.connect('/var/lib/corpus/corpus.sqlite3')
    db.row_factory = sqlite3.Row
    row = db.execute('''
      SELECT u.email, lower(u.id) AS user_id,
             lower(m.organization_id) AS organization_id
      FROM users u
      JOIN memberships m ON m.user_id = u.id
      JOIN agents a ON a.organization_id = m.organization_id
      WHERE lower(u.email) = lower(?)
        AND replace(lower(a.id), '-', '') = replace(lower(?), '-', '')
    ''', (email, agent_id)).fetchone()
    db.close()
    if row is None or row['organization_id'] != expected_organization.replace('-', '').lower():
        raise RuntimeError('The retained Phase 4 owner lineage is unavailable.')
    return dict(row)

async def run():
    owner = identity()
    database_settings = CorpusDatabaseSettings.from_env()
    auth_settings = AuthSettings.from_env()
    database = CorpusDatabase(database_settings.url)
    service = AuthService(
        database,
        reset_secret=auth_settings.reset_secret.get_secret_value(),
        verification_secret=auth_settings.verification_secret.get_secret_value(),
        access_lifetime=timedelta(minutes=auth_settings.access_token_minutes),
        idle_lifetime=timedelta(days=auth_settings.idle_session_days),
        absolute_lifetime=timedelta(days=auth_settings.absolute_session_days),
        reset_token_lifetime=timedelta(hours=auth_settings.reset_token_hours),
        verification_token_lifetime=timedelta(hours=auth_settings.verification_token_hours),
    )
    try:
        reset = await service.request_password_reset(owner['email'])
        if reset is None or reset.recipient != owner['email']:
            raise RuntimeError('Corpus did not issue the exact owner reset token.')
        await service.confirm_password_reset(reset.token, password)
        print(json.dumps({'email': owner['email'], 'organization_id': owner['organization_id']}))
    finally:
        await database.close()

asyncio.run(run())
"""


def arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Record the isolated exact-owner Phase 4 Operations promotion."
    )
    parser.add_argument("--url", default="http://127.0.0.1:5199")
    parser.add_argument("--headed", action="store_true")
    parser.add_argument("--verify-existing", action="store_true")
    return parser.parse_args()


def _owner_reset(password: str) -> dict[str, str]:
    completed = subprocess.run(
        [
            "docker", "exec", "-i", "-w", "/workspace/corpus/backend",
            CONTAINER, "python", "-c", RESET_CODE,
            OWNER_EMAIL, AGENT_ID, ORGANIZATION_ID,
        ],
        input=password,
        text=True,
        capture_output=True,
        timeout=60,
        check=False,
    )
    if completed.returncode != 0:
        raise RuntimeError("The exact local test owner could not be recovered.")
    value = json.loads(completed.stdout.strip())
    if value.get("organization_id") != ORGANIZATION_ID.replace("-", ""):
        raise RuntimeError("The recovered owner organization changed.")
    return value


def _promotion_record() -> dict[str, object]:
    code = r"""
import json, sqlite3, sys
organization_id, agent_id, build_id, interaction_id = sys.argv[1:]
db = sqlite3.connect('/var/lib/corpus/corpus.sqlite3')
db.row_factory = sqlite3.Row
rows = db.execute('''
  SELECT c.id AS case_id, c.organization_id, s.agent_id, c.build_id,
         c.source_kind, c.source_record_id, c.title, c.category,
         c.difficulty, c.mandatory, c.expected_operation_ids
  FROM agent_evaluation_cases c
  JOIN agent_evaluation_sets s ON s.id = c.evaluation_set_id
  WHERE replace(lower(c.organization_id), '-', '') = replace(lower(?), '-', '')
    AND replace(lower(s.agent_id), '-', '') = replace(lower(?), '-', '')
    AND replace(lower(c.build_id), '-', '') = replace(lower(?), '-', '')
    AND c.source_kind = 'operations' AND c.source_record_id = ?
''', (organization_id, agent_id, build_id, interaction_id)).fetchall()
print(json.dumps([{
  **dict(row),
  'case_id': str(row['case_id']),
  'organization_id': str(row['organization_id']),
  'agent_id': str(row['agent_id']),
  'build_id': str(row['build_id']),
  'expected_operation_ids': json.loads(row['expected_operation_ids']),
} for row in rows]))
db.close()
"""
    completed = subprocess.run(
        [
            "docker", "exec", "-w", "/workspace/corpus/backend", CONTAINER,
            "python", "-c", code, ORGANIZATION_ID, AGENT_ID, BUILD_ID,
            INTERACTION_ID,
        ],
        text=True,
        capture_output=True,
        timeout=30,
        check=False,
    )
    if completed.returncode != 0:
        raise RuntimeError("The exact Operations promotion record is unavailable.")
    rows = json.loads(completed.stdout)
    if len(rows) != 1:
        raise RuntimeError("Operations promotion did not create exactly one case.")
    return rows[0]


async def _maximize(page: Page) -> None:
    shell = page.locator("[data-agent-shell]")
    if await shell.get_attribute("data-surface-layout") != "split":
        await page.get_by_role("button", name="Maximize surface", exact=True).click()
    await shell.locator("[data-agent-conversation]").wait_for(state="visible")
    await shell.locator("[data-agent-surface-dock]").wait_for(state="visible")
    if await shell.get_attribute("data-surface-layout") != "split":
        raise RuntimeError("Operations did not maximize beside chat.")


async def _capture(page: Page, directory: Path, name: str, output: list[str]) -> None:
    await page.wait_for_timeout(1_500)
    path = directory / f"{name}.png"
    await page.screenshot(path=path, full_page=False)
    await page.wait_for_timeout(1_500)
    output.append(str(path.relative_to(ROOT)))


def _safe_dispatch(body: object) -> dict[str, object] | None:
    if not isinstance(body, dict):
        return None
    operation_id = body.get("operation_id") or body.get("operationId")
    if not isinstance(operation_id, str):
        result = body.get("result")
        if isinstance(result, dict):
            operation_id = result.get("operation_id") or result.get("operationId")
    if not isinstance(operation_id, str):
        return None
    return {
        "operationId": operation_id,
        "disposition": body.get("disposition"),
        "outcome": body.get("outcome"),
        "sessionVersion": body.get("session_version") or body.get("sessionVersion"),
        "projectionVersion": body.get("projection_version") or body.get("projectionVersion"),
    }


async def run(args: argparse.Namespace) -> int:
    run_id = datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ") + "-" + secrets.token_hex(4)
    directory = ARTIFACT_ROOT / run_id
    videos = directory / "raw-video"
    videos.mkdir(parents=True)
    screenshots: list[str] = []
    operations: list[dict[str, object]] = []
    operation_snapshots: list[dict[str, object]] = []
    evaluation_snapshots: list[dict[str, object]] = []
    diagnostics: dict[str, list[dict[str, object]]] = {
        "httpErrors": [], "consoleErrors": [], "pageErrors": [],
        "requestFailures": [],
    }
    password = "Corpus-Phase4-" + secrets.token_urlsafe(24) + "!9"
    destroy_password = "Corpus-Phase4-Destroy-" + secrets.token_urlsafe(24) + "!9"
    recovered = False
    browser = None
    context = None
    page = None
    video_path: Path | None = None
    error: str | None = None
    promotion: dict[str, object] | None = None
    evidence_conversation_id: str | None = None
    tasks: set[asyncio.Task[None]] = set()

    async def observe(response: Response) -> None:
        path = urlsplit(response.url).path
        if response.status >= 400:
            diagnostics["httpErrors"].append({
                "method": response.request.method, "path": path,
                "status": response.status,
            })
        if response.status != 200:
            return
        try:
            if response.request.method == "POST" and path == "/api/routedeck/dispatch":
                safe = _safe_dispatch(await response.json())
                if safe is not None:
                    operations.append(safe)
            elif path == f"/api/agents/{AGENT_ID}/operations":
                operation_snapshots.append(await response.json())
            elif path == f"/api/agents/{AGENT_ID}/evaluations":
                evaluation_snapshots.append(await response.json())
        except Exception:
            return

    def schedule(response: Response) -> None:
        task = asyncio.create_task(observe(response))
        tasks.add(task)
        task.add_done_callback(tasks.discard)

    started = time.monotonic()
    try:
        identity = _owner_reset(password)
        recovered = True
        async with async_playwright() as playwright:
            browser = await playwright.chromium.launch(headless=not args.headed)
            context = await browser.new_context(
                viewport={"width": 1440, "height": 1000},
                record_video_dir=videos,
                record_video_size={"width": 1440, "height": 1000},
            )
            page = await context.new_page()
            page.on("response", schedule)
            page.on("console", lambda item: diagnostics["consoleErrors"].append(
                {"type": item.type, "text": item.text}
            ) if item.type in {"warning", "error"} else None)
            page.on("pageerror", lambda item: diagnostics["pageErrors"].append(
                {"message": str(item)}
            ))
            page.on("requestfailed", lambda request: diagnostics["requestFailures"].append(
                {"method": request.method, "path": urlsplit(request.url).path,
                 "failure": request.failure}
            ))

            await page.goto(args.url)
            await page.get_by_role("heading", name="Explore Corpus", exact=True).wait_for(timeout=30_000)
            await page.get_by_role("button", name="Sign in", exact=True).click()
            await page.get_by_role("heading", name="Sign in", exact=True).wait_for()
            await page.get_by_label("Email", exact=True).fill(identity["email"])
            await page.get_by_label("Password", exact=True).fill(password)
            await page.locator("form").get_by_role("button", name="Sign in", exact=True).click()
            await page.get_by_label("Sign out", exact=True).wait_for(timeout=30_000)

            workspace = page.locator("section.workspace-home")
            await workspace.get_by_role("button", name="Open Agents", exact=True).click()
            agents = page.locator("section.agents-home")
            await agents.locator("#agents-home-title").wait_for(timeout=30_000)
            inventory = agents.get_by_label("Agent inventory")
            exact_agent = inventory.get_by_role("button").filter(has_text=AGENT_NAME)
            await exact_agent.wait_for(state="visible", timeout=30_000)
            if await exact_agent.count() != 1:
                raise RuntimeError("The retained exact Agent is unavailable or ambiguous.")
            await exact_agent.click()
            open_operations = agents.get_by_role("button", name="Operations", exact=True)
            await open_operations.wait_for(state="visible")
            for _ in range(120):
                if await open_operations.is_enabled():
                    break
                await page.wait_for_timeout(250)
            if not await open_operations.is_enabled():
                raise RuntimeError("The retained exact Agent selection did not bind.")
            await open_operations.click()
            await page.locator("#operations-title").wait_for(timeout=60_000)
            evidence_conversation_id = await page.evaluate(
                "() => sessionStorage.getItem('corpus.selected-conversation.v1')"
            )
            if not isinstance(evidence_conversation_id, str) or not evidence_conversation_id:
                raise RuntimeError("The current owner conversation is unavailable.")
            await _maximize(page)
            operations_surface = page.locator("section.operations-home")
            await operations_surface.get_by_text(
                "Deployed Agent interactions and redacted execution evidence", exact=True
            ).wait_for()
            loading_operations = operations_surface.locator(".operations-home__loading")
            if await loading_operations.count() == 1:
                await loading_operations.wait_for(state="hidden", timeout=30_000)
            interaction = operations_surface.locator(
                ".operations-home__interactions > li"
            ).filter(has_text=PUBLIC_SESSION_ID)
            await interaction.wait_for(state="visible", timeout=30_000)
            if await interaction.count() != 1:
                raise RuntimeError("The exact retained deployed interaction is ambiguous.")
            await interaction.scroll_into_view_if_needed()
            outcome = interaction.locator("section.operations-home__outcome")
            if not await outcome.get_by_text("Apparel", exact=False).is_visible():
                raise RuntimeError("The exact retained deployed result is unavailable.")
            await interaction.locator("details.operations-home__lineage > summary").click()
            await interaction.get_by_text(BUILD_ID, exact=True).wait_for()
            await _capture(page, directory, "01-exact-operations-interaction", screenshots)

            promotion_details = interaction.locator("details.operations-home__promotion")
            await promotion_details.locator("summary").click()
            if not args.verify_existing:
                await promotion_details.get_by_label("Evaluation set", exact=True).fill(SET_NAME)
                await promotion_details.get_by_label("Category", exact=True).fill(CATEGORY)
                await promotion_details.get_by_label("Difficulty", exact=True).select_option("medium")
                await promotion_details.get_by_role(
                    "button", name="Create Evaluation case", exact=True
                ).click()
                await promotion_details.get_by_role("status").filter(
                    has_text="Evaluation case created from this interaction."
                ).wait_for(timeout=30_000)
                await _capture(page, directory, "02-promotion-completed", screenshots)

                await page.reload(wait_until="domcontentloaded")
                await page.locator("#operations-title").wait_for(timeout=60_000)
                await _maximize(page)
                operations_surface = page.locator("section.operations-home")
                interaction = operations_surface.locator(
                    ".operations-home__interactions > li"
                ).filter(has_text=PUBLIC_SESSION_ID)
                await interaction.scroll_into_view_if_needed()
                promotion_details = interaction.locator("details.operations-home__promotion")
                await promotion_details.locator("summary").click()
            await promotion_details.get_by_role(
                "button", name="Evaluation case created", exact=True
            ).wait_for(timeout=30_000)
            if await interaction.get_by_role(
                "button", name="Evaluation case created", exact=True
            ).is_enabled():
                raise RuntimeError("The promoted interaction remained actionable after reload.")
            await _capture(page, directory, "03-promotion-survives-reload", screenshots)

            await operations_surface.get_by_role(
                "button", name="Back to Agent", exact=True
            ).click()
            hub = page.locator("section.agents-home section.agent-operations")
            await hub.get_by_role("button", name="Evaluation", exact=True).click()
            evaluation = page.locator("section.evaluation-home")
            await evaluation.get_by_role("heading", name="Evaluation", exact=True).wait_for(timeout=60_000)
            await _maximize(page)
            case_row = evaluation.get_by_role("row").filter(has_text=CATEGORY).filter(
                has_text="Recorded interaction"
            )
            if await case_row.count() != 1:
                raise RuntimeError("The promoted Evaluation case is unavailable or duplicated.")
            await case_row.scroll_into_view_if_needed()
            await _capture(page, directory, "04-exact-evaluation-case", screenshots)
            await page.wait_for_timeout(1_500)

            if tasks:
                await asyncio.gather(*tuple(tasks), return_exceptions=True)
            promotion = _promotion_record()
            if promotion.get("source_kind") != "operations":
                raise RuntimeError("The promoted case has the wrong source kind.")
            if promotion.get("source_record_id") != INTERACTION_ID:
                raise RuntimeError("The promoted case lost its interaction lineage.")
            if promotion.get("build_id", "").replace("-", "") != BUILD_ID.replace("-", ""):
                raise RuntimeError("The promoted case lost its exact build lineage.")
            if promotion.get("category") != CATEGORY or promotion.get("difficulty") != "medium":
                raise RuntimeError("The promoted case metadata changed.")
            if "GetProductTypes" not in promotion.get("expected_operation_ids", []):
                raise RuntimeError("The promoted case lost its exact API operation.")
            if not args.verify_existing and not any(item.get("operationId") == "operations.promote_evaluation_case" for item in operations):
                raise RuntimeError("The exact supervised promotion operation was not observed.")
            if diagnostics["httpErrors"] or diagnostics["consoleErrors"] or diagnostics["pageErrors"]:
                raise RuntimeError("The Operations interval contains unexpected diagnostics.")
    except Exception as caught:
        error = f"{type(caught).__name__}: {caught}"
    finally:
        if page is not None and error is not None:
            try:
                await page.screenshot(path=directory / "99-failure.png", full_page=False)
            except Exception:
                pass
        if page is not None:
            try:
                raw_video = page.video
                if raw_video is not None:
                    await page.close()
                    video_path = Path(await raw_video.path())
            except Exception:
                pass
        if context is not None:
            try:
                await context.close()
            except Exception:
                pass
        if browser is not None:
            try:
                await browser.close()
            except Exception:
                pass
        if recovered:
            try:
                _owner_reset(destroy_password)
            except Exception as reset_error:
                error = error or f"RuntimeError: temporary owner credential cleanup failed: {reset_error}"

    if video_path is not None and video_path.is_file():
        final_video = directory / "phase4-operations-promotion-normal-speed.webm"
        video_path.replace(final_video)
        video_path = final_video
    result = {
        "runId": run_id,
        "status": "passed" if error is None else "failed",
        "scope": "isolated Phase 4 exact-owner Operations promotion" if not args.verify_existing else "isolated Phase 4 durable Operations promotion verification",
        "testAdministration": {
            "localOwnerPasswordReset": True,
            "authEvidenceClaimed": False,
            "temporaryCredentialRevoked": recovered,
        },
        "ids": {
            "retiredConversationId": RETAINED_CONVERSATION_ID,
            "evidenceConversationId": evidence_conversation_id,
            "organizationId": ORGANIZATION_ID,
            "agentId": AGENT_ID, "buildId": BUILD_ID,
            "runtimeDeploymentId": RUNTIME_DEPLOYMENT_ID,
            "interactionId": INTERACTION_ID, "publicSessionId": PUBLIC_SESSION_ID,
            "evaluationCaseId": None if promotion is None else promotion.get("case_id"),
        },
        "promotion": promotion,
        "operations": operations,
        "screenshots": screenshots,
        "video": None if video_path is None else str(video_path.relative_to(ROOT)),
        "videoMetadata": {
            "playbackRate": 1.0, "width": 1440, "height": 1000,
            "maximizedSurface": True,
        },
        "diagnostics": diagnostics,
        "elapsedSeconds": round(time.monotonic() - started, 3),
        "error": error,
    }
    result_path = directory / "result.json"
    result_path.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    for artifact in directory.rglob("*"):
        if artifact.is_file() and (password.encode() in artifact.read_bytes() or destroy_password.encode() in artifact.read_bytes()):
            shutil.rmtree(directory)
            raise RuntimeError("Credential canary reached the evidence directory; evidence was removed.")
    print(f"run={run_id} status={result['status']}")
    print(f"artifact={result_path}")
    print(f"video={result['video']}")
    if error is not None:
        print("error=" + error.encode("ascii", "backslashreplace").decode("ascii"))
    return 0 if error is None else 1


async def main() -> int:
    async with asyncio.timeout(13 * 60):
        return await run(arguments())


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
