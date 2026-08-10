from __future__ import annotations

import asyncio
import shutil
import subprocess

import pytest
from playwright.async_api import TimeoutError as PlaywrightTimeoutError

from scripts.run_agents_archive_delete_journey import (
    AGENTS_HOME_TITLE_SELECTOR,
    AgentLifecycleControls,
    AgentLifecycleReview,
    AgentSourcesPanel,
    JOURNEY_STEPS,
    REQUIRED_ID_KEYS,
    _ids_complete,
    _inside_viewport,
    _expected_http_outcome,
    _is_expected_aborted_request,
    _record_request_failure,
    assemble_chronological_video,
    chronological_ffmpeg_command,
    open_agents,
    classify_expected_console_errors,
    review_id,
    route_deck_failure_seen,
    write_corpus_trace,
)


def test_journey_order_keeps_review_and_race_mutations_behavioral() -> None:
    assert JOURNEY_STEPS == (
        "create_agents",
        "archive_stage",
        "archive_reload",
        "archive_accept",
        "delete_stage_reject",
        "delete_stage_accept",
        "create_ready_source_and_attach_blocked",
        "dependency_guard_block",
        "race_stage",
        "race_attach_in_second_conversation",
        "race_accept_stale",
        "restart_persistence",
    )
    assert JOURNEY_STEPS.index("delete_stage_reject") < JOURNEY_STEPS.index(
        "delete_stage_accept"
    )
    assert JOURNEY_STEPS.index("race_stage") < JOURNEY_STEPS.index(
        "race_attach_in_second_conversation"
    ) < JOURNEY_STEPS.index("race_accept_stale")


def test_required_identity_gate_rejects_partial_product_observations() -> None:
    identities = {key: f"observed-{key}" for key in REQUIRED_ID_KEYS}
    assert _ids_complete(identities, REQUIRED_ID_KEYS)
    identities["sourceJobId"] = None
    assert not _ids_complete(identities, REQUIRED_ID_KEYS)


def test_viewport_gate_rejects_clipped_or_missing_controls() -> None:
    viewport = {"width": 390, "height": 844}
    assert _inside_viewport(
        {"x": 12, "y": 20, "width": 300, "height": 44}, viewport
    )
    assert not _inside_viewport(
        {"x": 12, "y": 820, "width": 300, "height": 44}, viewport
    )
    assert not _inside_viewport(None, viewport)


def test_route_deck_failure_gate_requires_exact_stale_code() -> None:
    diagnostics = {
        "routeDeckResults": [
            {
                "disposition": "failed",
                "failureCode": "review_stale",
                "failureMessage": "The authoritative facts changed after review.",
            }
        ]
    }
    assert route_deck_failure_seen(diagnostics, "review_stale")
    assert not route_deck_failure_seen(diagnostics, "agent_dependency_conflict")


def test_video_assembly_command_splices_secondary_between_primary_segments(
    tmp_path,
) -> None:
    command = chronological_ffmpeg_command(
        "ffmpeg",
        tmp_path / "primary.webm",
        tmp_path / "race.webm",
        tmp_path / "assembled.webm",
        12.25,
        18.75,
    )
    graph = command[command.index("-filter_complex") + 1]
    assert "trim=start=0:end=12.250" in graph
    assert "trim=start=18.750" in graph
    assert "[v0][v1][v2]concat=n=3:v=1:a=0[outv]" in graph
    assert command[-1] == str(tmp_path / "assembled.webm")


def test_installed_ffmpeg_assembles_real_chronological_webm(tmp_path) -> None:
    ffmpeg = shutil.which("ffmpeg")
    assert ffmpeg is not None, "ffmpeg is required by the recorder evidence contract"
    primary = tmp_path / "primary.webm"
    race = tmp_path / "race.webm"
    for output, color in ((primary, "blue"), (race, "orange")):
        subprocess.run(
            [
                ffmpeg,
                "-y",
                "-f",
                "lavfi",
                "-i",
                f"color=c={color}:s=160x90:d=1:r=10",
                "-an",
                "-c:v",
                "libvpx-vp9",
                "-crf",
                "30",
                "-b:v",
                "0",
                str(output),
            ],
            check=True,
            capture_output=True,
            text=True,
        )
    directory = tmp_path / "artifacts"
    directory.mkdir()
    output, manifest = assemble_chronological_video(
        repository=tmp_path,
        directory=directory,
        primary=primary,
        secondary=race,
        race_start=0.25,
        race_end=0.75,
    )
    assert manifest["status"] == "passed"
    assert output == "artifacts\\agents-archive-delete-journey.webm"
    assert (tmp_path / output).stat().st_size > 0


def test_open_agents_does_not_accept_persistent_navigation_label() -> None:
    page = _OpenAgentsPage()

    asyncio.run(open_agents(page, timeout_ms=100))

    assert page.scoped_selectors == [AGENTS_HOME_TITLE_SELECTOR]
    assert page.open_agents_clicks == 1
    assert ("heading", "Agents") not in page.unscoped_role_queries


def test_open_agents_observes_surface_after_completed_click_detaches() -> None:
    page = _OpenAgentsPage(raise_after_open=True)

    asyncio.run(open_agents(page, timeout_ms=100))

    assert page.surface_visible
    assert page.open_agents_clicks == 1


def test_open_agents_preserves_actionability_timeout_without_navigation() -> None:
    page = _OpenAgentsPage(timeout_without_open=True)

    with pytest.raises(PlaywrightTimeoutError, match="actionability blocked"):
        asyncio.run(open_agents(page, timeout_ms=5))

    assert not page.surface_visible
    assert page.open_agents_clicks > 0


def test_lifecycle_page_objects_keep_identical_labels_surface_scoped() -> None:
    page = _ScopedPage()
    controls = AgentLifecycleControls(page)
    review = AgentLifecycleReview(page, "archive")

    assert controls.archive.path.endswith("role=button;name=Archive Agent;exact=True")
    assert review.accept.path.endswith("role=button;name=Archive Agent;exact=True")
    assert controls.archive.path != review.accept.path
    assert controls.archive.path.startswith(".agents-home .agent-lifecycle")
    assert controls.blocker.path.startswith(".agents-home .agent-lifecycle")
    assert review.accept.path.startswith(".agent-lifecycle-review")


def test_review_page_object_tracks_empty_pending_and_reloaded_states() -> None:
    page = _ScopedPage()
    archive = AgentLifecycleReview(page, "archive")
    assert asyncio.run(archive.root.count()) == 0

    page.review_state = "pending"
    page.review_dom_id = "review-first"
    assert asyncio.run(archive.root.count()) == 1
    assert asyncio.run(review_id(archive.heading)) == "first"

    page.review_dom_id = "review-reloaded"
    reloaded = AgentLifecycleReview(page, "archive")
    assert asyncio.run(reloaded.root.count()) == 1
    assert asyncio.run(review_id(reloaded.heading)) == "reloaded"


def test_source_page_object_scopes_attachment_names_and_actions() -> None:
    page = _ScopedPage()
    sources = AgentSourcesPanel(page)

    assert sources.ready_source.path.startswith(".agents-home .agent-sources")
    assert sources.attach_source.path.startswith(".agents-home .agent-sources")
    assert sources.source("Lifecycle Guard Source").path.startswith(
        ".agents-home .agent-sources"
    )


def test_expected_route_deck_abort_classification_retains_paths() -> None:
    expected_urls = (
        "http://127.0.0.1:5199/api/routedeck/events?after=2",
        "http://127.0.0.1:5199/api/routedeck/conversation",
        "http://127.0.0.1:5199/api/routedeck/conversation/runs/run-1/events?after=3",
        "http://127.0.0.1:5199/api/routedeck/private-forms/lounge-register",
    )
    diagnostics = {"expectedAbortedRequests": [], "requestFailures": []}
    for url in expected_urls:
        assert _is_expected_aborted_request(url, "net::ERR_ABORTED")
        _record_request_failure(
            diagnostics,
            page_name="primary",
            url=url,
            failure="net::ERR_ABORTED",
        )

    assert [item["path"] for item in diagnostics["expectedAbortedRequests"]] == [
        "/api/routedeck/events",
        "/api/routedeck/conversation",
        "/api/routedeck/conversation/runs/run-1/events",
        "/api/routedeck/private-forms/lounge-register",
    ]
    assert diagnostics["requestFailures"] == []


def test_non_routedeck_or_non_abort_request_failure_remains_unexpected() -> None:
    diagnostics = {"expectedAbortedRequests": [], "requestFailures": []}
    cases = (
        ("http://127.0.0.1:5199/api/agents", "net::ERR_ABORTED"),
        ("http://127.0.0.1:5199/api/routedeck/events?after=2", "net::ERR_FAILED"),
    )
    for url, failure in cases:
        assert not _is_expected_aborted_request(url, failure)
        _record_request_failure(
            diagnostics,
            page_name="primary",
            url=url,
            failure=failure,
        )
    assert diagnostics["expectedAbortedRequests"] == []
    assert len(diagnostics["requestFailures"]) == 2


def test_expected_409_business_outcomes_require_exact_path_and_payload() -> None:
    rejected = _expected_http_outcome(
        "/api/routedeck/reviews/review-1/reject",
        409,
        {
            "disposition": "failed",
            "operation_id": "agents.delete_agent",
            "failure": {"code": "review_rejected"},
        },
    )
    blocked = _expected_http_outcome(
        "/api/routedeck/dispatch",
        409,
        {
            "disposition": "blocked",
            "operation_id": "agents.delete_agent",
            "failure": {"code": "agent_dependency_conflict"},
        },
    )
    stale = _expected_http_outcome(
        "/api/routedeck/reviews/review-2/accept",
        409,
        {
            "disposition": "failed",
            "operation_id": "agents.delete_agent",
            "failure": {"code": "review_stale"},
        },
    )

    assert rejected == "review_rejected"
    assert blocked == "agent_dependency_conflict"
    assert stale == "review_stale"
    assert _expected_http_outcome(
        "/api/routedeck/dispatch",
        409,
        {
            "disposition": "failed",
            "operation_id": "agents.delete_agent",
            "failure": {"code": "review_rejected"},
        },
    ) is None
    assert _expected_http_outcome(
        "/api/routedeck/reviews/review-1/reject",
        500,
        {
            "disposition": "failed",
            "operation_id": "agents.delete_agent",
            "failure": {"code": "review_rejected"},
        },
    ) is None


def test_expected_409_console_classification_consumes_only_matching_count() -> None:
    diagnostics = {
        "expectedHttpOutcomes": [
            {
                "page": "primary",
                "status": 409,
                "path": "/api/routedeck/reviews/review-1/reject",
                "code": "review_rejected",
            },
            {
                "page": "primary",
                "status": 409,
                "path": "/api/routedeck/dispatch",
                "code": "agent_dependency_conflict",
            },
        ],
        "consoleErrors": [
            {
                "page": "primary",
                "type": "error",
                "text": "Failed to load resource: the server responded with a status of 409 (Conflict)",
                "path": "/api/routedeck/reviews/review-1/reject",
            },
            {
                "page": "primary",
                "type": "error",
                "text": "Failed to load resource: the server responded with a status of 409 (Conflict)",
                "path": "/api/routedeck/dispatch",
            },
            {
                "page": "primary",
                "type": "error",
                "text": "Failed to load resource: the server responded with a status of 409 (Conflict)",
                "path": "/api/unexpected-conflict",
            },
            {"page": "primary", "type": "warning", "text": "real warning"},
        ],
        "expectedConsoleErrors": [],
    }

    classify_expected_console_errors(diagnostics)

    assert len(diagnostics["expectedConsoleErrors"]) == 2
    assert len(diagnostics["consoleErrors"]) == 2
    assert diagnostics["consoleErrors"][-1]["text"] == "real warning"


def test_expected_409_console_classification_keeps_unscoped_conflicts() -> None:
    diagnostics = {
        "expectedHttpOutcomes": [
            {
                "page": "primary",
                "status": 409,
                "path": "/api/routedeck/dispatch",
                "code": "agent_dependency_conflict",
            }
        ],
        "consoleErrors": [
            {
                "page": "primary",
                "type": "error",
                "text": "Failed to load resource: the server responded with a status of 409 (Conflict)",
            }
        ],
        "expectedConsoleErrors": [],
    }

    classify_expected_console_errors(diagnostics)

    assert diagnostics["expectedConsoleErrors"] == []
    assert len(diagnostics["consoleErrors"]) == 1


def test_corpus_trace_is_chronological_and_never_serializes_headers_or_bodies(
    tmp_path,
) -> None:
    output = tmp_path / "corpus-trace.json"
    diagnostics = {
        "chronologicalTrace": [
            {
                "observedAt": "2026-08-07T14:00:02+00:00",
                "page": "primary",
                "kind": "response",
                "method": "GET",
                "path": "/api/agents",
                "status": 200,
            },
            {
                "observedAt": "2026-08-07T14:00:01+00:00",
                "page": "primary",
                "kind": "response",
                "method": "POST",
                "path": "/api/conversations",
                "status": 201,
            },
        ],
        "headers": {"Authorization": "Bearer must-not-appear"},
        "body": {"api_key": "must-not-appear"},
    }

    write_corpus_trace(output, "run-safe", diagnostics)
    raw = output.read_text(encoding="utf-8")
    parsed = __import__("json").loads(raw)

    assert "must-not-appear" not in raw
    assert [event["path"] for event in parsed["events"]] == [
        "/api/conversations",
        "/api/agents",
    ]
    assert set(parsed) == {"runId", "format", "events"}


class _OpenAgentsPage:
    def __init__(
        self,
        *,
        raise_after_open: bool = False,
        timeout_without_open: bool = False,
    ) -> None:
        self.surface_visible = False
        self.open_agents_clicks = 0
        self.raise_after_open = raise_after_open
        self.timeout_without_open = timeout_without_open
        self.scoped_selectors: list[str] = []
        self.unscoped_role_queries: list[tuple[str, str]] = []

    def locator(self, selector: str):
        self.scoped_selectors.append(selector)
        return _SurfaceTitle(self)

    def get_by_role(self, role: str, *, name: str, exact: bool):
        assert exact
        self.unscoped_role_queries.append((role, name))
        if role == "heading" and name == "Agents":
            return _Action(self, visible=True)
        if name == "Continue to Workspace":
            return _Action(self, visible=False)
        if name == "Open Agents":
            return _Action(self, visible=True, opens_agents=True)
        raise AssertionError(f"Unexpected role query: {role} {name}")

    async def wait_for_timeout(self, _milliseconds: int) -> None:
        return None


class _SurfaceTitle:
    def __init__(self, page: _OpenAgentsPage) -> None:
        self.page = page

    async def is_visible(self) -> bool:
        return self.page.surface_visible


class _Action:
    def __init__(
        self,
        page: _OpenAgentsPage,
        *,
        visible: bool,
        opens_agents: bool = False,
    ) -> None:
        self.page = page
        self.visible = visible
        self.opens_agents = opens_agents

    @property
    def last(self):
        return self

    async def is_visible(self) -> bool:
        return self.visible

    async def is_enabled(self) -> bool:
        return True

    async def click(self, *, timeout: int) -> None:
        assert 0 < timeout <= 1_500
        if self.opens_agents:
            self.page.open_agents_clicks += 1
            if self.page.timeout_without_open:
                raise PlaywrightTimeoutError("actionability blocked")
            self.page.surface_visible = True
            if self.page.raise_after_open:
                raise PlaywrightTimeoutError("button detached after completed navigation")


class _ScopedPage:
    def __init__(self) -> None:
        self.review_state = "empty"
        self.review_dom_id = "review-unset"

    def locator(self, selector: str):
        return _ScopedLocator(self, selector)

    def get_by_role(self, role: str, *, name: str, exact: bool):
        return _ScopedLocator(self, f"page::role={role};name={name};exact={exact}")


class _ScopedLocator:
    def __init__(self, page: _ScopedPage, path: str) -> None:
        self.page = page
        self.path = path

    def get_by_role(self, role: str, *, name: str, exact: bool):
        return _ScopedLocator(
            self.page,
            f"{self.path} >> role={role};name={name};exact={exact}",
        )

    def get_by_label(self, name: str, *, exact: bool):
        return _ScopedLocator(
            self.page,
            f"{self.path} >> label={name};exact={exact}",
        )

    def get_by_text(self, text: str, *, exact: bool):
        return _ScopedLocator(
            self.page,
            f"{self.path} >> text={text};exact={exact}",
        )

    def filter(self, *, has):
        return _ScopedLocator(self.page, f"{self.path} >> has=({has.path})")

    async def count(self) -> int:
        return 1 if self.page.review_state == "pending" else 0

    async def get_attribute(self, name: str):
        assert name == "id"
        return self.page.review_dom_id
