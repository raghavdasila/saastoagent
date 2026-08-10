from __future__ import annotations

import ast
import asyncio
import subprocess
import sys
from pathlib import Path

import pytest

from scripts.run_api_connection_check_journey import _scroll_delta_for_group
from scripts.run_api_operation_curation_journey import (
    EXPECTED_ASSERTION_COUNT,
    EXPECTED_OPERATION_IDS,
    EXPECTED_PHASE_OPERATION_IDS,
    _classify_expected_console_errors,
    _concurrent_entry_url,
    _is_expected_stale_failure,
    _safe_curation,
    _saved_version_count,
    _visible_selection,
)


ROOT = Path(__file__).resolve().parents[3]
SCRIPT = ROOT / "scripts" / "run_api_operation_curation_journey.py"
SURFACE = ROOT / "frontend" / "src" / "features" / "sources" / "ApiOperationCurationPanel.tsx"


def test_direct_entrypoint_loads_without_starting_browser() -> None:
    completed = subprocess.run(
        [sys.executable, str(SCRIPT), "--help"],
        cwd=ROOT,
        check=False,
        capture_output=True,
        text=True,
    )
    assert completed.returncode == 0
    assert "Record exact API operation curation" in completed.stdout


def test_journey_has_nine_behavior_assertions_and_phase_trace_starts_after_auth() -> None:
    source = SCRIPT.read_text(encoding="utf-8")
    tree = ast.parse(source)
    assertion_calls = [
        node
        for node in ast.walk(tree)
        if isinstance(node, ast.Call)
        and isinstance(node.func, ast.Name)
        and node.func.id == "_record"
        and len(node.args) >= 2
        and isinstance(node.args[0], ast.Name)
        and node.args[0].id == "assertions"
    ]
    assert EXPECTED_ASSERTION_COUNT == 9
    assert len(assertion_calls) == EXPECTED_ASSERTION_COUNT
    assert source.index("await _register(primary, args.url, owner)") < source.index(
        "phase_trace_start = len(safe_trace)"
    ) < source.index("hub = await _open_sources(primary)")
    assert source.count("await _register(") == 2


def test_probe_and_operation_allowlist_match_the_real_surface_contract() -> None:
    source = SCRIPT.read_text(encoding="utf-8")
    surface = SURFACE.read_text(encoding="utf-8")
    assert EXPECTED_OPERATION_IDS == {"createOrder", "listOrders", "trackShipment"}
    assert EXPECTED_PHASE_OPERATION_IDS == {
        "workspace.open_sources",
        "sources.open_api_creation",
        "sources.save_api_operation_curation",
    }
    assert 'section.api-operation-curation[aria-labelledby="api-operation-curation-title"]' in source
    assert 'className="api-operation-curation"' in surface
    assert 'aria-labelledby="api-operation-curation-title"' in surface
    assert "set_input_files" in source
    assert "development probe" in source


def test_desktop_evidence_is_split_into_strict_top_and_bottom_viewports_before_save() -> None:
    source = SCRIPT.read_text(encoding="utf-8")
    top = source.index('"01a-curation-identity-desktop"')
    bottom = source.index('"01b-curation-decisions-save-desktop"')
    save = source.index(
        'await panel.get_by_role("button", name="Save operation selection", exact=True).click()'
    )
    assert top < bottom < save

    container = {"x": 0.0, "y": 100.0, "width": 900.0, "height": 600.0}
    top_bounds = {
        "heading": {"x": 10.0, "y": 120.0, "width": 300.0, "height": 40.0},
        "inventory": {"x": 10.0, "y": 250.0, "width": 300.0, "height": 40.0},
    }
    bottom_bounds = {
        "firstDecision": {"x": 10.0, "y": 400.0, "width": 300.0, "height": 50.0},
        "save": {"x": 10.0, "y": 780.0, "width": 300.0, "height": 50.0},
    }
    assert isinstance(_scroll_delta_for_group(top_bounds, container, margin=16), float)
    assert isinstance(_scroll_delta_for_group(bottom_bounds, container, margin=16), float)
    with pytest.raises(RuntimeError, match="cannot fit"):
        _scroll_delta_for_group(
            {"heading": top_bounds["heading"], "save": bottom_bounds["save"]},
            container,
            margin=16,
        )


def test_concurrent_page_enters_through_exact_primary_session_bound_sources_url() -> None:
    source = SCRIPT.read_text(encoding="utf-8")
    exact = "http://127.0.0.1:5199/sources?resume_handle=opaque-session-handle"
    assert _concurrent_entry_url(exact, "http://127.0.0.1:5199") == exact
    with pytest.raises(RuntimeError, match="session-bound"):
        _concurrent_entry_url("http://127.0.0.1:5199/", "http://127.0.0.1:5199")
    with pytest.raises(RuntimeError, match="configured Corpus origin"):
        _concurrent_entry_url(
            "http://foreign.invalid/sources?resume_handle=opaque",
            "http://127.0.0.1:5199",
        )
    assert "await race_page.goto(_concurrent_entry_url(primary.url, args.url))" in source
    assert "await race_page.goto(args.url)" not in source


def test_safe_curation_retains_only_contract_identity_and_no_private_owner_or_body() -> None:
    value = _safe_curation(
        {
            "source_id": "sourceopaque0001",
            "source_revision_id": "revisionopaque01",
            "artifact_revision_id": "artifactopaque01",
            "inventory_fingerprint": "a" * 64,
            "operations": [
                {
                    "operation_id": "listOrders",
                    "graph_node_id": "api:listOrders",
                    "method": "GET",
                    "path_template": "/orders",
                    "operation_class": "list",
                    "authorization": "must-not-retain",
                }
            ],
            "current": {
                "id": "curationopaque01",
                "source_id": "sourceopaque0001",
                "source_revision_id": "revisionopaque01",
                "artifact_revision_id": "artifactopaque01",
                "inventory_fingerprint": "a" * 64,
                "included_operation_ids": ["listOrders"],
                "excluded_operation_ids": [],
                "selected_at": "2026-08-08T00:00:00Z",
                "previous_curation_id": None,
                "selected_by_owner_id": "private-owner",
                "credential": "must-not-retain",
            },
            "history": [],
            "response_body": "must-not-retain",
        }
    )
    encoded = repr(value)
    assert "must-not-retain" not in encoded
    assert "private-owner" not in encoded
    assert "response_body" not in encoded
    assert value["operations"][0]["operation_id"] == "listOrders"


def test_only_exact_typed_stale_dispatch_is_an_expected_business_failure() -> None:
    exact = {
        "status": 409,
        "method": "POST",
        "path": "/api/routedeck/session/example/dispatch",
        "operationId": "sources.save_api_operation_curation",
        "failureCode": "api_operation_curation_selection_stale",
    }
    assert _is_expected_stale_failure(exact)
    for field, value in (
        ("status", 500),
        ("method", "GET"),
        ("path", "/api/sources"),
        ("operationId", "sources.test_api_connection"),
        ("failureCode", "api_operation_curation_unavailable"),
    ):
        changed = dict(exact)
        changed[field] = value
        assert not _is_expected_stale_failure(changed)


def test_console_409_suppression_is_bounded_one_for_one_to_typed_failure() -> None:
    diagnostics = {
        "expectedBusinessFailures": [
            {
                "page": "primary",
                "status": 409,
                "method": "POST",
                "path": "/api/routedeck/session/example/dispatch",
                "operationId": "sources.save_api_operation_curation",
                "failureCode": "api_operation_curation_selection_stale",
            }
        ],
        "consoleErrors": [
            {
                "page": "concurrent",
                "text": "Failed to load resource: the server responded with a status of 409",
                "locationPath": "/api/routedeck/session/example/dispatch",
            },
            {
                "page": "primary",
                "text": "Failed to load resource: the server responded with a status of 409",
                "locationPath": "/api/routedeck/session/example/dispatch",
            },
            {"page": "primary", "text": "unrelated", "locationPath": "/api/sources"},
        ],
    }
    _classify_expected_console_errors(diagnostics)
    assert diagnostics["consoleErrors"] == [
        {
            "page": "concurrent",
            "text": "Failed to load resource: the server responded with a status of 409",
            "locationPath": "/api/routedeck/session/example/dispatch",
        },
        {"page": "primary", "text": "unrelated", "locationPath": "/api/sources"},
    ]


def test_visible_authoritative_decisions_and_version_are_required_after_stale_refetch() -> None:
    panel = _FakePanel(
        decisions={
            "createOrder": "included",
            "listOrders": "included",
            "trackShipment": "excluded",
        },
        saved_versions="2",
    )
    included, excluded = asyncio.run(
        _visible_selection(
            panel,
            expected_included={"createOrder", "listOrders"},
            expected_excluded={"trackShipment"},
        )
    )
    assert included == {"createOrder", "listOrders"}
    assert excluded == {"trackShipment"}
    assert asyncio.run(_saved_version_count(panel, expected=2)) == 2


class _FakePanel:
    def __init__(self, *, decisions: dict[str, str], saved_versions: str) -> None:
        self.decisions = decisions
        self.saved_versions = saved_versions

    def locator(self, selector: str, *, has_text: str | None = None):
        if selector == ".api-curation-list > li":
            return _FakeRow(self, has_text or "")
        if selector == ".api-curation-identity > div":
            return _FakeVersionRow(self)
        raise AssertionError(selector)


class _FakeRow:
    def __init__(self, panel: _FakePanel, operation_id: str) -> None:
        self.panel = panel
        self.operation_id = operation_id

    def get_by_role(self, role: str, *, name: str, exact: bool):
        assert role == "radio" and exact
        return _FakeRadio(
            self.panel.decisions.get(self.operation_id) == f"{name.casefold()}d"
        )


class _FakeRadio:
    def __init__(self, checked: bool) -> None:
        self.checked = checked

    async def is_checked(self) -> bool:
        return self.checked


class _FakeVersionRow:
    def __init__(self, panel: _FakePanel) -> None:
        self.panel = panel

    def locator(self, selector: str):
        assert selector == "dd"
        return self

    async def inner_text(self) -> str:
        return self.panel.saved_versions
