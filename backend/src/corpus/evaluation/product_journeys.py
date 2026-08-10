from __future__ import annotations

import asyncio
import hashlib
import json
import re
import sqlite3
import time
from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Awaitable, Callable
from urllib.parse import urlparse
from uuid import uuid4

from .evidence_index import update_latest_evidence

from playwright.async_api import Browser, BrowserContext, Page, async_playwright

from .mailbox import MailTmMailbox


class ProductJourneyError(RuntimeError):
    pass


@dataclass
class JourneyEvidence:
    transcript: list[dict[str, str]] = field(default_factory=list)
    screenshots: list[str] = field(default_factory=list)
    assertions: list[dict[str, Any]] = field(default_factory=list)

    def action(self, text: str) -> None:
        self.transcript.append({"role": "tester", "content": text})

    def observed(self, text: str) -> None:
        self.transcript.append({"role": "corpus", "content": text})

    def assert_that(self, criterion: str, passed: bool, evidence: str) -> None:
        self.assertions.append(
            {"criterion": criterion, "passed": passed, "evidence": evidence}
        )
        if not passed:
            raise ProductJourneyError(f"{criterion}: {evidence}")


class LoungeProductJourneyRunner:
    """Run Studio-owned Lounge product journeys through the rendered UI.

    This runner targets an explicitly isolated Corpus runtime. It never creates
    schema, rewrites product state, or substitutes a mock mail/model provider.
    """

    def __init__(
        self,
        *,
        repository: Path,
        frontend_url: str,
        database_url: str,
        headless: bool = True,
        mail_outage_frontend_url: str | None = None,
    ) -> None:
        self.repository = repository
        self.frontend_url = frontend_url.rstrip("/")
        self.database_path = _sqlite_path(database_url)
        self.headless = headless
        self.mail_outage_frontend_url = (
            mail_outage_frontend_url.rstrip("/")
            if mail_outage_frontend_url is not None
            else None
        )
        self.design_path = (
            repository / "docs/corpus-agent-design/workbench/design-state.json"
        )
        self.results_root = repository / ".runtime/evaluations"

    async def run(self, journey_id: str | None = None) -> dict[str, Any]:
        definitions = self._definitions(journey_id)
        run_id = f"{datetime.now(UTC).strftime('%Y%m%dT%H%M%SZ')}-{uuid4().hex[:10]}"
        run_dir = self.results_root / run_id
        run_dir.mkdir(parents=True, exist_ok=False)
        started = datetime.now(UTC).isoformat()
        async with async_playwright() as playwright:
            browser = await playwright.chromium.launch(headless=self.headless)
            try:
                results = [
                    await self._run_one(browser, definition, run_dir)
                    for definition in definitions
                ]
            finally:
                await browser.close()
        artifact = {
            "schema": "corpus.product-journey-evaluation.v1",
            "runId": run_id,
            "evaluationLevel": "product-journey",
            "status": (
                "passed"
                if results and all(item["status"] == "passed" for item in results)
                else "failed"
            ),
            "startedAt": started,
            "completedAt": datetime.now(UTC).isoformat(),
            "identities": {
                "designSha256": _sha256(self.design_path),
                "frontend": self.frontend_url,
                "browser": "playwright-chromium",
                "mailbox": "Mail.tm public API",
                "mailboxAttribution": "https://mail.tm",
            },
            "usage": _aggregate_usage(results),
            "results": results,
        }
        artifact_path = run_dir / "result.json"
        artifact_path.write_text(json.dumps(artifact, indent=2) + "\n", encoding="utf-8")
        self._update_latest(artifact, artifact_path)
        return artifact

    async def _run_one(
        self, browser: Browser, definition: dict[str, Any], run_dir: Path
    ) -> dict[str, Any]:
        evidence = JourneyEvidence()
        journey_dir = run_dir / definition["id"]
        journey_dir.mkdir()
        context = await browser.new_context(viewport={"width": 1440, "height": 1000})
        await context.tracing.start(screenshots=True, snapshots=True, sources=False)
        page = await context.new_page()
        started = time.monotonic()
        try:
            handler = self._handlers()[definition["id"]]
            await handler(page, context, evidence, journey_dir)
            await self._capture(page, evidence, journey_dir, "final")
            status = "passed"
            error = None
        except Exception as caught:
            status = "failed"
            error = f"{type(caught).__name__}: {caught}"
            await self._capture(page, evidence, journey_dir, "failure")
        finally:
            usage = await _read_browser_usage(page)
            trace_path = journey_dir / "trace.zip"
            await context.tracing.stop(path=trace_path)
            await context.close()
        result = {
            "evaluationId": definition["id"],
            "title": definition["title"],
            "status": status,
            "definitionSha256": _json_sha256(definition),
            "durationSeconds": round(time.monotonic() - started, 2),
            "transcript": evidence.transcript,
            "deterministicAssertions": evidence.assertions,
            "evidence": {
                "screenshots": evidence.screenshots,
                "trace": str(trace_path.relative_to(self.repository)),
            },
            "usage": usage,
        }
        if error is not None:
            result["error"] = _redact(error)
        return result

    def _handlers(self) -> dict[str, Callable[..., Awaitable[None]]]:
        return {
            "lounge-journey-register-sign-in": self._register_sign_in,
            "lounge-journey-duplicate-registration": self._duplicate_registration,
            "lounge-journey-password-reset": self._password_reset,
            "lounge-journey-unknown-reset": self._unknown_reset,
            "lounge-journey-mail-outage": self._mail_outage,
            "lounge-journey-email-verification": self._email_verification,
            "lounge-journey-verification-rate-limit": self._verification_rate_limit,
            "lounge-journey-invalid-verification": self._invalid_verification,
        }

    async def _register_sign_in(self, page: Page, _context: BrowserContext, evidence: JourneyEvidence, _directory: Path) -> None:
        async with await MailTmMailbox.create() as mailbox:
            password = _password()
            before = self._owner_state(mailbox.address)
            await self._register(page, mailbox.address, password, evidence)
            await page.get_by_label("Sign out", exact=True).click()
            await page.get_by_role("heading", name="Explore Corpus").wait_for()
            evidence.action("Signed out, then reopened sign in.")
            await self._sign_in(page, mailbox.address, password, evidence)
            after = self._owner_state(mailbox.address)
            evidence.assert_that("one owner exists", after["users"] - before["users"] == 1, str(after))
            evidence.assert_that("one personal Workspace exists", after["organizations"] - before["organizations"] == 1, str(after))
            evidence.assert_that("owner membership exists", after["memberships"] - before["memberships"] == 1, str(after))
            evidence.assert_that("an active owner session exists", after["active_sessions"] >= 1, str(after))

    async def _duplicate_registration(self, page: Page, _context: BrowserContext, evidence: JourneyEvidence, _directory: Path) -> None:
        async with await MailTmMailbox.create() as mailbox:
            password = _password()
            await self._register(page, mailbox.address, password, evidence)
            await page.get_by_label("Sign out", exact=True).click()
            await page.get_by_role("heading", name="Explore Corpus").wait_for()
            before = self._owner_state(mailbox.address)
            await page.get_by_role("button", name="Create account").click()
            await page.get_by_role("heading", name="Create account").wait_for()
            await self._fill_registration(page, mailbox.address, password)
            await page.locator("form").get_by_role("button", name="Create account").click()
            alert = await page.locator("section.workspace-auth").get_by_role("alert").inner_text()
            evidence.observed(alert)
            after = self._owner_state(mailbox.address)
            evidence.assert_that("duplicate registration stays account-neutral", "already" not in alert.lower() and "exists" not in alert.lower(), alert)
            evidence.assert_that("no duplicate owner or Workspace is created", after == before, str(after))

    async def _password_reset(self, page: Page, _context: BrowserContext, evidence: JourneyEvidence, _directory: Path) -> None:
        async with await MailTmMailbox.create() as mailbox:
            old_password, new_password = _password(), _password()
            await self._register(page, mailbox.address, old_password, evidence)
            await page.get_by_label("Sign out", exact=True).click()
            sent_after = time.time()
            await self._open_reset(page, mailbox.address, evidence)
            await page.locator("section.workspace-auth").get_by_role("status").wait_for()
            message = await mailbox.wait_for_message(subject="Reset your Corpus password", after=sent_after)
            evidence.observed("A password-reset message arrived in the public test mailbox.")
            await page.goto(message.first_link("/reset-password"))
            await page.get_by_label("New password").fill(new_password)
            await page.locator("form").get_by_role("button", name="Change password").click()
            await page.get_by_role("heading", name="Sign in").wait_for()
            evidence.observed("Corpus returned to sign in after changing the password.")
            await self._sign_in(page, mailbox.address, new_password, evidence)
            await page.get_by_label("Sign out", exact=True).click()
            await page.get_by_role("heading", name="Explore Corpus").wait_for()
            await self._open_lounge_path(page, "Sign in", "Sign in")
            await self._fill_sign_in(page, mailbox.address, old_password)
            await page.locator("form").get_by_role("button", name="Sign in", exact=True).click()
            alert = await page.locator("section.workspace-auth").get_by_role("alert").inner_text()
            evidence.assert_that("the old password no longer authenticates", "invalid" in alert.lower(), alert)

    async def _unknown_reset(self, page: Page, _context: BrowserContext, evidence: JourneyEvidence, _directory: Path) -> None:
        async with await MailTmMailbox.create() as mailbox:
            before = self._owner_state(mailbox.address)
            await self._open_reset(page, mailbox.address, evidence)
            status = await page.locator("section.workspace-auth").get_by_role("status").inner_text()
            after = self._owner_state(mailbox.address)
            evidence.observed(status)
            evidence.assert_that("unknown-account recovery uses generic acceptance", "if that account exists" in status.lower(), status)
            evidence.assert_that("unknown recovery creates no owner state", before == after, str(after))

    async def _mail_outage(self, page: Page, _context: BrowserContext, evidence: JourneyEvidence, _directory: Path) -> None:
        if self.mail_outage_frontend_url is None:
            raise ProductJourneyError("A separately configured real mail-outage runtime URL is required.")
        async with await MailTmMailbox.create() as mailbox:
            password = _password()
            await page.context.clear_cookies()
            await self._register(
                page,
                mailbox.address,
                password,
                evidence,
                base_url=self.mail_outage_frontend_url,
            )
            await page.get_by_label("Sign out", exact=True).click()
            await self._open_reset(
                page,
                mailbox.address,
                evidence,
                base_url=self.mail_outage_frontend_url,
            )
            await page.locator("section.workspace-auth").get_by_role("status").wait_for()
            await page.locator("form").get_by_role("button", name="Request reset").click()
            visible = await page.locator("section.workspace-auth").get_by_role("alert").inner_text()
            evidence.observed(visible)
            evidence.assert_that("known mail outage is visible", "delivery" in visible.lower() and "unavailable" in visible.lower(), visible)
            evidence.assert_that("outage copy remains account-neutral", mailbox.address.lower() not in visible.lower() and "exists" not in visible.lower(), visible)

    async def _email_verification(self, page: Page, _context: BrowserContext, evidence: JourneyEvidence, _directory: Path) -> None:
        async with await MailTmMailbox.create() as mailbox:
            await self._register(page, mailbox.address, _password(), evidence)
            sent_after = time.time()
            await self._open_verification_pending(page, evidence)
            await page.get_by_role("button", name="Resend verification").click()
            message = await mailbox.wait_for_message(subject="Verify your Corpus email", after=sent_after)
            evidence.observed("A verification message arrived in the public test mailbox.")
            await page.goto(message.first_link("/verify"))
            await page.locator("section.workspace-auth").get_by_role("button", name="Verify email").click()
            status = await page.locator("section.workspace-auth").get_by_role("status").inner_text()
            evidence.observed(status)
            state = self._owner_state(mailbox.address)
            evidence.assert_that("owner state confirms verified email", state["verified_users"] == 1, str(state))
            evidence.assert_that("verification token is removed from the visible URL", "token=" not in page.url, page.url)

    async def _verification_rate_limit(self, page: Page, _context: BrowserContext, evidence: JourneyEvidence, _directory: Path) -> None:
        async with await MailTmMailbox.create() as mailbox:
            await self._register(page, mailbox.address, _password(), evidence)
            await self._open_verification_pending(page, evidence)
            for _ in range(3):
                await page.get_by_role("button", name="Resend verification").click()
            await page.get_by_role("button", name="Resend verification").click()
            alert = await page.locator("main").get_by_role("alert").inner_text()
            evidence.observed(alert)
            state = self._owner_state(mailbox.address)
            evidence.assert_that("verification resend is visibly rate-limited", "rate" in alert.lower() or "too many" in alert.lower(), alert)
            evidence.assert_that("owner remains unverified", state["verified_users"] == 0, str(state))

    async def _invalid_verification(self, page: Page, _context: BrowserContext, evidence: JourneyEvidence, _directory: Path) -> None:
        async with await MailTmMailbox.create() as mailbox:
            await self._register(page, mailbox.address, _password(), evidence)
            await page.goto(f"{self.frontend_url}/verify#token=invalid-evaluation-token")
            await page.locator("section.workspace-auth").get_by_role("button", name="Verify email").click()
            status = await page.locator("section.workspace-auth").get_by_role("status").inner_text()
            evidence.observed(status)
            state = self._owner_state(mailbox.address)
            evidence.assert_that(
                "invalid verification is rejected explicitly",
                any(
                    phrase in status.lower()
                    for phrase in ("failed", "invalid", "could not be confirmed")
                ),
                status,
            )
            evidence.assert_that("owner remains unverified", state["verified_users"] == 0, str(state))
            evidence.assert_that("invalid token is removed from the visible URL", "token=" not in page.url, page.url)

    async def _register(
        self,
        page: Page,
        email: str,
        password: str,
        evidence: JourneyEvidence,
        *,
        base_url: str | None = None,
    ) -> None:
        await page.goto(base_url or self.frontend_url)
        await page.get_by_role("heading", name="Explore Corpus").wait_for()
        await page.wait_for_timeout(750)
        await self._open_lounge_path(page, "Create account", "Create account")
        await self._fill_registration(page, email, password)
        evidence.action("Submitted a unique mailbox, display name, and strong password through Create account.")
        await page.locator("form").get_by_role("button", name="Create account").click()
        await page.get_by_label("Sign out", exact=True).wait_for(timeout=30_000)
        evidence.observed("Corpus entered an authenticated owner Workspace.")

    async def _sign_in(self, page: Page, email: str, password: str, evidence: JourneyEvidence) -> None:
        await self._open_lounge_path(page, "Sign in", "Sign in")
        await self._fill_sign_in(page, email, password)
        evidence.action("Submitted the owner credentials through Sign in.")
        await page.locator("form").get_by_role("button", name="Sign in", exact=True).click()
        await page.get_by_label("Sign out", exact=True).wait_for(timeout=30_000)
        evidence.observed("Corpus restored an authenticated owner Workspace.")

    async def _open_reset(
        self,
        page: Page,
        email: str,
        evidence: JourneyEvidence,
        *,
        base_url: str | None = None,
    ) -> None:
        await page.goto(base_url or self.frontend_url)
        await page.get_by_role("heading", name="Explore Corpus").wait_for()
        await page.wait_for_timeout(750)
        await self._open_lounge_path(page, "Sign in", "Sign in")
        await page.get_by_role("button", name="Forgot password").click()
        await page.get_by_role("heading", name="Forgot password").wait_for()
        await page.get_by_label("Email").fill(email)
        evidence.action("Requested password recovery through the private email form.")
        await page.locator("form").get_by_role("button", name="Request reset").click()

    async def _open_lounge_path(
        self, page: Page, button_name: str, heading_name: str
    ) -> None:
        heading = page.get_by_role("heading", name=heading_name)
        if await heading.is_visible():
            return
        for attempt in range(3):
            await page.get_by_role(
                "button", name=button_name, exact=True
            ).click()
            try:
                await heading.wait_for(timeout=5_000)
                return
            except Exception:
                dispatch_error = page.get_by_text(
                    "RouteDeck dispatch requires a live bootstrapped store."
                )
                if await dispatch_error.count() == 0 or attempt == 2:
                    raise
                await page.wait_for_timeout(1_000)

    async def _open_verification_pending(
        self, page: Page, evidence: JourneyEvidence
    ) -> None:
        evidence.action("Opened Manage verification from the owner Workspace.")
        await page.get_by_role("button", name="Manage verification").click()
        await page.get_by_role("button", name="Resend verification").wait_for(
            timeout=30_000
        )

    async def _fill_registration(self, page: Page, email: str, password: str) -> None:
        await page.get_by_label("Display name").fill("Corpus Evaluation Owner")
        await page.get_by_label("Email").fill(email)
        await page.get_by_label("Password").fill(password)

    async def _fill_sign_in(self, page: Page, email: str, password: str) -> None:
        await page.get_by_label("Email").fill(email)
        await page.get_by_label("Password").fill(password)

    async def _capture(self, page: Page, evidence: JourneyEvidence, directory: Path, name: str) -> None:
        path = directory / f"{name}.png"
        try:
            await page.screenshot(path=path, full_page=True)
            evidence.screenshots.append(str(path.relative_to(self.repository)))
        except Exception:
            return

    def _owner_state(self, email: str) -> dict[str, int]:
        with sqlite3.connect(self.database_path) as connection:
            user = connection.execute(
                "SELECT id, is_verified FROM users WHERE lower(email) = lower(?)", (email,)
            ).fetchone()
            if user is None:
                return {"users": 0, "verified_users": 0, "organizations": 0, "memberships": 0, "active_sessions": 0}
            user_id, verified = user
            organizations = connection.execute(
                "SELECT COUNT(*) FROM organizations o JOIN memberships m ON m.organization_id=o.id WHERE m.user_id=?",
                (user_id,),
            ).fetchone()[0]
            memberships = connection.execute(
                "SELECT COUNT(*) FROM memberships WHERE user_id=?", (user_id,)
            ).fetchone()[0]
            sessions = connection.execute(
                "SELECT COUNT(*) FROM auth_sessions WHERE user_id=? AND revoked_at IS NULL",
                (user_id,),
            ).fetchone()[0]
            return {"users": 1, "verified_users": int(bool(verified)), "organizations": organizations, "memberships": memberships, "active_sessions": sessions}

    def _definitions(self, journey_id: str | None) -> list[dict[str, Any]]:
        design = json.loads(self.design_path.read_text(encoding="utf-8"))
        lounge = next(item for item in design["features"] if item["name"] == "Lounge")
        definitions = [item for item in lounge["productJourneyEvals"] if item["enabled"]]
        if journey_id is not None:
            definitions = [item for item in definitions if item["id"] == journey_id]
            if not definitions:
                raise ValueError(f"Unknown enabled Lounge product journey: {journey_id}")
        unknown = sorted({item["id"] for item in definitions} - set(self._handlers()))
        if unknown:
            raise ValueError(f"No browser journey implementation for: {unknown}")
        return definitions

    def _update_latest(self, artifact: dict[str, Any], artifact_path: Path) -> None:
        _update_latest(self.repository, artifact, artifact_path)


def enabled_lounge_product_journey_ids(repository: Path) -> tuple[str, ...]:
    design_path = repository / "docs/corpus-agent-design/workbench/design-state.json"
    design = json.loads(design_path.read_text(encoding="utf-8"))
    lounge = next(item for item in design["features"] if item["name"] == "Lounge")
    return tuple(
        item["id"] for item in lounge["productJourneyEvals"] if item["enabled"]
    )


def aggregate_product_journey_artifacts(
    repository: Path,
    artifacts: list[dict[str, Any]],
) -> dict[str, Any]:
    if not artifacts:
        raise ValueError("At least one product-journey artifact is required.")
    design_hashes = {
        item["identities"]["designSha256"] for item in artifacts
    }
    if len(design_hashes) != 1:
        raise ValueError("Product-journey artifacts do not share one design identity.")
    results = [
        result
        for artifact in artifacts
        for result in artifact["results"]
    ]
    evaluation_ids = [item["evaluationId"] for item in results]
    if len(evaluation_ids) != len(set(evaluation_ids)):
        raise ValueError("Product-journey artifacts contain duplicate evaluations.")
    run_id = f"{datetime.now(UTC).strftime('%Y%m%dT%H%M%SZ')}-{uuid4().hex[:10]}"
    run_dir = repository / ".runtime" / "evaluations" / run_id
    run_dir.mkdir(parents=True, exist_ok=False)
    artifact = {
        "schema": "corpus.product-journey-evaluation.v1",
        "runId": run_id,
        "evaluationLevel": "product-journey",
        "status": (
            "passed"
            if results and all(item["status"] == "passed" for item in results)
            else "failed"
        ),
        "startedAt": min(item["startedAt"] for item in artifacts),
        "completedAt": max(item["completedAt"] for item in artifacts),
        "identities": {
            "designSha256": design_hashes.pop(),
            "frontend": "fresh isolated local runtime per journey",
            "browser": "playwright-chromium",
            "mailbox": "Mail.tm public API",
            "mailboxAttribution": "https://mail.tm",
            "runtimeIsolation": "fresh Corpus processes and persistent state per journey",
            "componentRunIds": [item["runId"] for item in artifacts],
        },
        "usage": _aggregate_usage(results),
        "results": results,
    }
    artifact_path = run_dir / "result.json"
    artifact_path.write_text(json.dumps(artifact, indent=2) + "\n", encoding="utf-8")
    _update_latest(repository, artifact, artifact_path)
    return artifact


def _update_latest(
    repository: Path,
    artifact: dict[str, Any],
    artifact_path: Path,
) -> None:
    latest_path = repository / ".runtime" / "evaluations" / "latest.json"
    update_latest_evidence(
        repository=repository,
        latest_path=latest_path,
        artifact=artifact,
        artifact_path=artifact_path,
    )


def _sqlite_path(database_url: str) -> Path:
    prefix = "sqlite+aiosqlite:///"
    if not database_url.startswith(prefix):
        raise ValueError("Product journey state assertions currently require an isolated SQLite Corpus database.")
    value = database_url[len(prefix):]
    if re.match(r"^[A-Za-z]:/", value):
        return Path(value)
    return Path("/" + value) if database_url.startswith(prefix + "/") else Path(value)


def _password() -> str:
    return f"Corpus-Eval-{uuid4().hex}!9"


def _redact(value: str) -> str:
    value = re.sub(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+", "[redacted-email]", value)
    return re.sub(r"token=[^\s&#]+", "token=[redacted]", value)


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _json_sha256(value: Any) -> str:
    payload = json.dumps(value, sort_keys=True, separators=(",", ":")).encode()
    return hashlib.sha256(payload).hexdigest()


async def _read_browser_usage(page: Page) -> dict[str, Any]:
    try:
        inspection = await page.evaluate(
            """async () => {
                const response = await fetch('/api/routedeck/inspect');
                return response.ok ? await response.json() : null;
            }"""
        )
    except Exception:
        inspection = None
    if inspection is None:
        return {
            "modelInvocations": None,
            "inputTokens": None,
            "outputTokens": None,
            "exactCostUsd": None,
            "costStatus": "protected invocation evidence was not available to the browser runner",
        }
    input_tokens, output_tokens, invocations = _find_usage(inspection)
    return {
        "modelInvocations": invocations,
        "inputTokens": input_tokens,
        "outputTokens": output_tokens,
        "exactCostUsd": None,
        "costStatus": "not_returned_by_runtime",
    }


def _find_usage(value: Any) -> tuple[int, int, int]:
    input_tokens = output_tokens = invocations = 0
    if isinstance(value, dict):
        if "input_tokens" in value or "output_tokens" in value:
            input_tokens += int(value.get("input_tokens") or 0)
            output_tokens += int(value.get("output_tokens") or 0)
            invocations += 1
        for nested in value.values():
            nested_input, nested_output, nested_invocations = _find_usage(nested)
            input_tokens += nested_input
            output_tokens += nested_output
            invocations += nested_invocations
    elif isinstance(value, list):
        for nested in value:
            nested_input, nested_output, nested_invocations = _find_usage(nested)
            input_tokens += nested_input
            output_tokens += nested_output
            invocations += nested_invocations
    return input_tokens, output_tokens, invocations


def _aggregate_usage(results: list[dict[str, Any]]) -> dict[str, Any]:
    observed = all(
        item["usage"]["modelInvocations"] is not None for item in results
    )
    return {
        "modelInvocations": sum(item["usage"]["modelInvocations"] for item in results) if observed else None,
        "inputTokens": sum(item["usage"]["inputTokens"] for item in results) if observed else None,
        "outputTokens": sum(item["usage"]["outputTokens"] for item in results) if observed else None,
        "exactCostUsd": None,
        "costStatus": (
            "Token usage is runtime-observed. Exact billed cost requires a matching "
            "OpenAI organization usage/cost record and is not estimated."
        ),
    }


__all__ = [
    "LoungeProductJourneyRunner",
    "ProductJourneyError",
    "aggregate_product_journey_artifacts",
    "enabled_lounge_product_journey_ids",
]
