from __future__ import annotations

import ast
import json
import subprocess
import sys
from pathlib import Path

import pytest

from scripts.run_api_connection_check_journey import _publish_evidence
from scripts.run_api_routed_execution_stale_supplement_journey import (
    EXPECTED_ASSERTION_COUNT,
    _cart_count_from_stdout,
    _classify_expected_stale_outcome,
    _finalize_evidence_inputs,
    _review_stale_seen,
    _trace_has_zero_target_calls,
)


ROOT = Path(__file__).resolve().parents[3]
SCRIPT = ROOT / "scripts" / "run_api_routed_execution_stale_supplement_journey.py"


def test_direct_entrypoint_loads_without_starting_browser() -> None:
    completed = subprocess.run(
        [sys.executable, str(SCRIPT), "--help"],
        cwd=ROOT,
        check=False,
        capture_output=True,
        text=True,
    )
    assert completed.returncode == 0, completed.stderr
    assert "non-executing stale routed write" in completed.stdout


def test_assertion_count_and_nonexecuting_operation_boundary_are_exact() -> None:
    tree = ast.parse(SCRIPT.read_text(encoding="utf-8"))
    records = [
        node
        for node in ast.walk(tree)
        if isinstance(node, ast.Call)
        and isinstance(node.func, ast.Name)
        and node.func.id == "_record"
    ]
    assert EXPECTED_ASSERTION_COUNT == 9
    assert len(records) == 8  # Fresh Source coherence is recorded by the reused provisioner.
    source = SCRIPT.read_text(encoding="utf-8")
    assert 'name="Run routed read"' not in source
    assert source.count('name="Accept and send one write"') == 1
    assert "PostCarts" in source
    assert "included={READ_OPERATION}" in source


def test_stale_accept_occurs_only_after_authoritative_curation_advance() -> None:
    source = SCRIPT.read_text(encoding="utf-8")
    stage = source.index('name="Review routed write"')
    advance = source.index('ids["staleCurationId"] =')
    accept = source.index('name="Accept and send one write"')
    assert stage < advance < accept
    before_accept = source[stage:accept]
    assert "_wait_for_restored_conversation(" in before_accept
    assert "current_not=ids[\"writeCurationId\"]" in before_accept


def test_stale_failure_moves_to_exact_planner_owner_after_review_teardown() -> None:
    source = SCRIPT.read_text(encoding="utf-8")
    component = (
        ROOT / "frontend/src/features/sources/ApiOperationTestPanel.tsx"
    ).read_text(encoding="utf-8")
    accept = source.index('name="Accept and send one write"')
    detached = source.index('review.wait_for(state="detached"', accept)
    planner_alert = source.index('locator("section.api-routed-execution")', detached)
    desktop = source.index('"01-stale-write-failure-desktop"', planner_alert)
    mobile = source.index('"02-stale-write-failure-mobile"', desktop)
    assert accept < detached < planner_alert < desktop < mobile
    assert "The exact route plan changed before approval. No API request was sent." in source
    assert '"POST /store/carts · no automatic retry"' in source
    assert "{step.method} {step.path_template} · no automatic retry" in component


def test_every_supplemental_tab_restores_exact_identity_before_new_conversation() -> None:
    source = SCRIPT.read_text(encoding="utf-8")
    assert source.count("context.new_page()") == 2
    assert source.count("race_page = await context.new_page()") == 1
    tab = source.index("race_page = await context.new_page()")
    navigation = source.index("await race_page.goto(_concurrent_entry_url(primary.url, args.url))", tab)
    restore = source.index("await _wait_for_restored_conversation(", navigation)
    new_conversation = source.index("await _new_conversation(race_page)", restore)
    assert tab < navigation < restore < new_conversation


def test_cart_count_and_trace_zero_call_guards_fail_closed() -> None:
    assert _cart_count_from_stdout("17\n") == 17
    with pytest.raises(RuntimeError, match="cart count"):
        _cart_count_from_stdout("not-a-count")
    assert _trace_has_zero_target_calls([
        {"event": "response", "operationId": "sources.test_routed_api_write"},
        {"event": "response", "apiCallCount": 0},
    ])
    assert not _trace_has_zero_target_calls([{"apiCallCount": 1}])


def test_stale_diagnostics_are_exact_review_page_path_and_failure_only() -> None:
    review_id = "review_exact"
    expected_path = f"/api/routedeck/reviews/{review_id}/accept"
    expected = {
        "page": "primary",
        "status": 409,
        "method": "POST",
        "path": expected_path,
        "operationId": "sources.test_routed_api_write",
        "failureCode": "review_stale",
    }
    unrelated_reject = {
        **expected,
        "path": "/api/routedeck/reviews/review_other/reject",
        "failureCode": "review_rejected",
    }
    unrelated_stale = {
        **expected,
        "page": "curation-race",
        "path": "/api/routedeck/reviews/review_other/accept",
    }
    diagnostics = {
        "httpErrors": [expected, unrelated_reject, unrelated_stale],
        "consoleErrors": [
            {
                "page": "primary",
                "locationPath": expected_path,
                "text": "Failed to load resource: the server responded with a status of 409 (Conflict)",
            },
            {
                "page": "primary",
                "locationPath": unrelated_reject["path"],
                "text": "Failed to load resource: the server responded with a status of 409 (Conflict)",
            },
        ],
        "expectedHttpOutcomes": [],
        "expectedConsoleErrors": [],
    }
    _classify_expected_stale_outcome(diagnostics, review_id)
    assert diagnostics["expectedHttpOutcomes"] == [expected]
    assert diagnostics["httpErrors"] == [unrelated_reject, unrelated_stale]
    assert len(diagnostics["expectedConsoleErrors"]) == 1
    assert diagnostics["consoleErrors"][0]["locationPath"] == unrelated_reject["path"]
    assert _review_stale_seen([{"event": "response", **expected}], review_id)
    assert not _review_stale_seen([{"event": "response", **unrelated_stale}], review_id)


def test_restart_and_second_owner_proofs_remain_after_stale_zero_result() -> None:
    source = SCRIPT.read_text(encoding="utf-8")
    stale_query = source.index("stale_query = await _wait_execution_query(")
    restart = source.index('["docker", "compose", "restart", "backend"]', stale_query)
    restarted_query = source.index("restart_query = await _wait_execution_query(", restart)
    sign_out = source.index('get_by_label("Sign out"', restarted_query)
    other_owner = source.index("await _register(primary, args.url, other_owner)", sign_out)
    assert stale_query < restart < restarted_query < sign_out < other_owner
    assert "has_result=False" in source[stale_query:other_owner]


def test_secret_scan_removes_supplement_before_publication(tmp_path: Path) -> None:
    directory = tmp_path / "phase-f-stale-supplement"
    directory.mkdir()
    canary = "phase-f-stale-secret-canary"
    (directory / "diagnostic.txt").write_text(canary, encoding="utf-8")
    with pytest.raises(RuntimeError, match="removed before publication"):
        _publish_evidence(
            directory=directory,
            result_path=directory / "result.json",
            trace_path=directory / "corpus-trace.json",
            result_json=json.dumps({"safe": True}),
            trace_json="[]\n",
            secrets=(canary,),
        )
    assert not directory.exists()


def test_late_probe_failures_still_enter_secret_safe_publication_cleanup(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    import scripts.run_api_routed_execution_stale_supplement_journey as journey

    monkeypatch.setattr(
        journey,
        "_medusa_cart_count",
        lambda: (_ for _ in ()).throw(RuntimeError("late cart probe")),
    )
    monkeypatch.setattr(
        journey,
        "_video_duration_seconds",
        lambda _path: (_ for _ in ()).throw(RuntimeError("late video probe")),
    )
    cart_count, primary_duration, race_duration, error = _finalize_evidence_inputs(
        tmp_path,
        "primary.webm",
        "race.webm",
    )
    assert cart_count is None
    assert primary_duration is None
    assert race_duration is None
    assert error == (
        "cart_count_finalization_failed:RuntimeError;"
        "primary_video_finalization_failed:RuntimeError;"
        "race_video_finalization_failed:RuntimeError"
    )

    directory = tmp_path / "late-failure-run"
    directory.mkdir()
    canary = "late-probe-secret-canary"
    (directory / "retained-video.webm").write_bytes(canary.encode())
    with pytest.raises(RuntimeError, match="removed before publication"):
        _publish_evidence(
            directory=directory,
            result_path=directory / "result.json",
            trace_path=directory / "corpus-trace.json",
            result_json=json.dumps({"status": "failed", "error": error}),
            trace_json="[]\n",
            secrets=(canary,),
        )
    assert not directory.exists()
