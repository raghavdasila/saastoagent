from __future__ import annotations

import subprocess
import sys
from pathlib import Path

from scripts.run_api_connection_check_journey import (
    ALLOWED_PHASE_OPERATION_IDS,
    EXPECTED_ASSERTION_COUNT,
    _scroll_delta_for_group,
    classify_expected_console_errors,
    is_expected_aborted_request,
    is_expected_invalid_credential_failure,
    _publish_evidence,
)


ROOT = Path(__file__).resolve().parents[3]


def test_mobile_control_alignment_moves_observed_fractional_overflow_inside_with_margin() -> None:
    observed = {
        "heading": {"x": 57.0, "y": 577.03125, "width": 276.0, "height": 24.0},
        "button": {"x": 57.0, "y": 812.53125, "width": 276.0, "height": 32.0},
    }
    dock = {"x": 45.0, "y": 480.0, "width": 300.0, "height": 364.0}

    delta = _scroll_delta_for_group(observed, dock, margin=16.0)
    aligned = {
        name: {**bounds, "y": bounds["y"] - delta}
        for name, bounds in observed.items()
    }

    assert delta == 81.03125
    assert all(bounds["y"] >= dock["y"] + 16.0 for bounds in aligned.values())
    assert all(bounds["y"] + bounds["height"] <= dock["y"] + dock["height"] - 16.0 for bounds in aligned.values())
    assert all(bounds["y"] + bounds["height"] <= 844.0 for bounds in aligned.values())


def test_recorder_direct_entrypoint_loads_before_browser_start() -> None:
    completed = subprocess.run(
        [sys.executable, str(ROOT / "scripts" / "run_api_connection_check_journey.py"), "--help"],
        cwd=ROOT,
        capture_output=True,
        text=True,
        timeout=30,
        check=False,
    )

    assert completed.returncode == 0, completed.stderr
    assert "Record the safe API connection-check lifecycle." in completed.stdout


def test_recorder_declares_exact_safe_operation_boundary_and_eight_assertions() -> None:
    assert EXPECTED_ASSERTION_COUNT == 8
    assert ALLOWED_PHASE_OPERATION_IDS == {
        "workspace.open_sources",
        "sources.open_api_creation",
        "sources.propose_contract_revision",
        "sources.approve_contract_revision",
        "sources.save_api_connection",
        "sources.test_api_connection",
    }
    source = (ROOT / "scripts" / "run_api_connection_check_journey.py").read_text(encoding="utf-8")
    assert "genericExecutionOperationObserved" in source
    assert '"rawPlaywrightTrace": None' in source
    assert "record_video_dir" in source
    assert "docker\", \"compose\", \"restart\", \"backend" in source


def test_desktop_result_evidence_is_scoped_and_viewport_bounded() -> None:
    source = (ROOT / "scripts" / "run_api_connection_check_journey.py").read_text(encoding="utf-8")
    component = (ROOT / "frontend" / "src" / "features" / "sources" / "ApiConnectionPanel.tsx").read_text(encoding="utf-8")

    assert 'data-status={check.status}' in component
    assert source.count("await _capture_result_viewport(") == 2
    assert 'status="succeeded"' in source
    assert 'status="failed"' in source
    helper = source[source.index("async def _capture_result_viewport"):]
    assert 'li[data-status="{status}"]' in helper
    assert "_scroll_delta_for_group" in helper
    assert "_inside_viewport" in helper
    assert "full_page=False" in helper


def test_second_owner_handoff_uses_the_persistent_authenticated_header() -> None:
    source = (ROOT / "scripts" / "run_api_connection_check_journey.py").read_text(encoding="utf-8")
    header = (ROOT / "frontend" / "src" / "app" / "CorpusHeader.tsx").read_text(encoding="utf-8")

    assert 'aria-label="Sign out"' in header
    assert 'page.get_by_label("Sign out", exact=True)' in source
    assert 'page.locator("section.workspace-home").get_by_role("button", name="Sign out"' not in source
    click = source.index("await sign_out.click()")
    signed_out = source.index(
        'await page.get_by_role("heading", name="Explore Corpus", exact=True).wait_for(timeout=30_000)',
        click,
    )
    absent = source.index('await sign_out.wait_for(state="detached", timeout=30_000)', signed_out)
    register = source.index("await _register(page, args.url, other_owner)", absent)
    assert click < signed_out < absent < register


def test_expected_invalid_credential_failure_requires_exact_route_payload() -> None:
    exact = {
        "status": 409,
        "method": "POST",
        "path": "/api/routedeck/session/dispatch",
        "operationId": "sources.test_api_connection",
        "failureCode": "api_connection_check_failed",
    }
    assert is_expected_invalid_credential_failure(exact)
    for key, value in (
        ("status", 500),
        ("method", "GET"),
        ("path", "/api/sources"),
        ("operationId", "sources.save_api_connection"),
        ("failureCode", "other_failure"),
    ):
        changed = dict(exact)
        changed[key] = value
        assert not is_expected_invalid_credential_failure(changed)


def test_sign_out_abort_is_expected_only_after_exact_completed_response() -> None:
    item = {
        "method": "POST",
        "path": "/api/auth/sign-out",
        "failure": "net::ERR_ABORTED",
    }

    assert is_expected_aborted_request(
        item,
        {("POST", "/api/auth/sign-out"): 204},
    )
    assert not is_expected_aborted_request(item, {})
    assert not is_expected_aborted_request(
        item,
        {("POST", "/api/auth/sign-out"): 500},
    )
    assert not is_expected_aborted_request(
        {**item, "method": "GET"},
        {("POST", "/api/auth/sign-out"): 204},
    )
    assert not is_expected_aborted_request(
        {**item, "path": "/api/auth/refresh"},
        {("POST", "/api/auth/sign-out"): 204},
    )


def test_console_classification_consumes_only_one_matching_409_per_exact_failure() -> None:
    diagnostics = {
        "expectedBusinessFailures": [{"failureCode": "api_connection_check_failed"}],
        "consoleErrors": [
            {"type": "error", "text": "Failed to load resource: 409 (Conflict)", "locationPath": "/api/routedeck/session/dispatch"},
            {"type": "error", "text": "Failed to load resource: 409 (Conflict)", "locationPath": "/api/other/dispatch"},
            {"type": "error", "text": "Unrelated product error", "locationPath": ""},
        ],
    }
    classify_expected_console_errors(diagnostics)
    assert diagnostics["consoleErrors"] == [
        {"type": "error", "text": "Failed to load resource: 409 (Conflict)", "locationPath": "/api/other/dispatch"},
        {"type": "error", "text": "Unrelated product error", "locationPath": ""},
    ]


def test_recorder_retains_no_header_body_cookie_or_raw_trace_fields() -> None:
    source = (ROOT / "scripts" / "run_api_connection_check_journey.py").read_text(encoding="utf-8")
    assert '"headers": False' in source
    assert '"query": False' in source
    assert '"requestBodies": False' in source
    assert '"responseBodies": False' in source
    assert "context.tracing" not in source
    assert "storage_state" not in source
    assert "Authorization" not in source


def test_secret_scan_removes_the_recorder_run_before_publishing(tmp_path: Path) -> None:
    directory = tmp_path / "run"
    directory.mkdir()
    (directory / "screenshot.png").write_bytes(b"compressed-prefix-secret-canary-suffix")

    try:
        _publish_evidence(
            directory=directory,
            result_path=directory / "result.json",
            trace_path=directory / "corpus-trace.json",
            result_json="{}\n",
            trace_json="[]\n",
            secrets=("secret-canary",),
        )
    except RuntimeError as error:
        assert "removed before publication" in str(error)
    else:
        raise AssertionError("A credential canary must abort evidence publication.")
    assert not directory.exists()


def test_safe_publication_writes_both_reported_json_artifacts(tmp_path: Path) -> None:
    directory = tmp_path / "run"
    directory.mkdir()
    result_path = directory / "result.json"
    trace_path = directory / "corpus-trace.json"
    result_json = '{"status":"passed"}\n'
    trace_json = '[]\n'

    _publish_evidence(
        directory=directory,
        result_path=result_path,
        trace_path=trace_path,
        result_json=result_json,
        trace_json=trace_json,
        secrets=("credential-canary-not-present",),
    )

    assert result_path.is_file()
    assert trace_path.is_file()
    assert result_path.read_text(encoding="utf-8") == result_json
    assert trace_path.read_text(encoding="utf-8") == trace_json
