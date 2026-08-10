from __future__ import annotations

import ast
from pathlib import Path

from scripts.run_api_contract_revision_journey import (
    ALLOWED_OPERATION_IDS,
    _inside_viewport,
    _is_expected_abort,
)


SCRIPT = (
    Path(__file__).resolve().parents[3]
    / "scripts"
    / "run_api_contract_revision_journey.py"
)


def test_recorder_keeps_mobile_proof_before_restart_and_retains_restart() -> None:
    text = SCRIPT.read_text(encoding="utf-8")
    mobile = text.index('"05-review-mobile-390x844"')
    restart = text.index('["docker", "compose", "restart", "backend"]')
    persistence = text.index('"approved revision survives backend restart"')

    assert mobile < restart < persistence


def test_recorder_requires_all_eight_declared_assertions() -> None:
    text = SCRIPT.read_text(encoding="utf-8")

    assert text.count("_record(assertions,") == 8
    assert "len(assertions) == 8" in text


def test_reject_proof_requires_a_strictly_newer_owner_inventory() -> None:
    text = SCRIPT.read_text(encoding="utf-8")
    reject = text.index("await reject.click()")
    reload = text.index("await page.reload()", reject)
    version = text.index("minimum_inventory_version=inventory_version + 1", reload)
    rejection_assertion = text.index('"review rejection leaves the parent revision current"', version)

    assert reject < reload < version < rejection_assertion


def test_no_execution_proof_uses_exact_operation_allowlist() -> None:
    assert ALLOWED_OPERATION_IDS == {
        "workspace.open_sources",
        "sources.open_api_creation",
        "sources.propose_contract_revision",
        "sources.approve_contract_revision",
    }
    text = SCRIPT.read_text(encoding="utf-8")
    registration = text.index("await _register(page, args.url, owner)")
    bounded_start = text.index("phase_trace_start = len(safe_trace)", registration)
    open_sources = text.index('name="Open Sources"', bounded_start)
    bounded_slice = text.index("phase_trace = safe_trace[phase_trace_start:]", open_sources)
    assert registration < bounded_start < open_sources < bounded_slice
    assert "observed_operation_ids - ALLOWED_OPERATION_IDS" in text
    assert '"execute" in path.casefold()' not in text


def test_recorder_does_not_create_raw_trace_or_direct_authenticated_requests() -> None:
    text = SCRIPT.read_text(encoding="utf-8")
    tree = ast.parse(text)
    attributes = {
        node.attr
        for node in ast.walk(tree)
        if isinstance(node, ast.Attribute)
    }

    assert "tracing" not in attributes
    assert "page.request." not in text
    assert '"corpus-trace.json"' in text
    assert '"rawPlaywrightTrace": None' in text


def test_source_actions_are_scoped_to_the_source_hub_surface() -> None:
    text = SCRIPT.read_text(encoding="utf-8")
    source_surface = (
        Path(__file__).resolve().parents[3]
        / "frontend"
        / "src"
        / "features"
        / "sources"
        / "SourceHubSurface.tsx"
    ).read_text(encoding="utf-8")
    assert 'section.sources-debug[aria-labelledby="source-hub-title"]' in text
    assert 'className="sources-debug source-hub" aria-labelledby="source-hub-title"' in source_surface
    assert 'className="sources-debug api-source-workspace" aria-labelledby="source-hub-title"' in source_surface
    assert 'hub.get_by_role("button", name="Add API source", exact=True)' in text
    assert 'page.get_by_role("button", name="Add API source", exact=True)' not in text
    assert 'hub.get_by_role("button", name="Prepare contract revision", exact=True)' in text


def test_desktop_proposal_and_review_capture_key_surface_content_in_viewport() -> None:
    text = SCRIPT.read_text(encoding="utf-8")
    proposal_surface = (
        Path(__file__).resolve().parents[3]
        / "frontend"
        / "src"
        / "features"
        / "sources"
        / "ApiContractRevisionPanel.tsx"
    ).read_text(encoding="utf-8")
    review_surface = (
        Path(__file__).resolve().parents[3]
        / "frontend"
        / "src"
        / "features"
        / "sources"
        / "ApiContractRevisionReviewSurface.tsx"
    ).read_text(encoding="utf-8")

    assert 'proposal_top_bounds = await _capture_desktop_viewport(' in text
    assert 'proposal_bottom_bounds = await _capture_desktop_viewport(' in text
    assert 'review_bounds = await _capture_desktop_viewport(' in text
    assert '"02-proposal-top-desktop"' in text
    assert '"03-proposal-patches-review-desktop"' in text
    assert '"04-review-reloaded-desktop"' in text
    assert 'await page.screenshot(path=path, full_page=False)' in text
    assert 'if not all(_inside_viewport(value, width, height) for value in bounds.values())' in text
    for label in ("Proposed API version update", "Review this API update"):
        assert label in proposal_surface
        assert label in text
    assert "Shared-schema impact:" in proposal_surface
    assert "Shared-schema impact: 2" in text
    assert 'aria-label="Ordered reviewed patches"' in proposal_surface
    assert "3f4de4aa354d0324" in text
    assert 'proposal_review_button,' in text
    for label in (
        "Create this immutable API version?",
        "Accept and create new revision",
        "Keep current revision unchanged",
    ):
        assert label in review_surface
        assert label in text
    assert "Explicit shared-schema impact:" in review_surface
    assert "Explicit shared-schema impact: 2" in text


def test_desktop_viewport_bounds_are_strict() -> None:
    assert _inside_viewport(
        {"x": 0, "y": 0, "width": 1440, "height": 1000}, 1440, 1000
    )
    assert not _inside_viewport(
        {"x": 0, "y": 0, "width": 1440.1, "height": 1000}, 1440, 1000
    )
    assert not _inside_viewport(
        {"x": 0, "y": -0.1, "width": 100, "height": 100}, 1440, 1000
    )


def test_recorder_trace_allowlist_excludes_headers_bodies_and_credentials() -> None:
    text = SCRIPT.read_text(encoding="utf-8")
    forbidden = (
        'event["headers"]',
        'event["body"]',
        'event["authorization"]',
        'event["cookie"]',
        'event["password"]',
    )

    assert all(value not in text.casefold() for value in forbidden)


def test_expected_abort_classification_is_narrow() -> None:
    assert _is_expected_abort(
        {
            "failure": "net::ERR_ABORTED",
            "path": "/api/routedeck/session-1/events",
        }
    )
    assert not _is_expected_abort(
        {"failure": "net::ERR_ABORTED", "path": "/api/sources"}
    )
    assert not _is_expected_abort(
        {"failure": "net::ERR_FAILED", "path": "/api/routedeck/session-1/events"}
    )
