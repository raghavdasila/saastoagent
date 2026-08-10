from __future__ import annotations

import ast
import asyncio
import json
import subprocess
import sys
from pathlib import Path

import pytest
from playwright.async_api import Error as PlaywrightError
from playwright.async_api import TimeoutError as PlaywrightTimeoutError

from corpus.features.sources.connectors.api.contract_revisions import (
    MEDUSA_EFFECTIVE_CONTRACT_PLAN,
)
from corpus.features.sources.connectors.api.toolrouter import load_api_contract_documents
from corpus.integrations.api_execution._snapshot.contract_revision import (
    approve_contract_patches,
)
from scripts.run_api_connection_check_journey import _publish_evidence
from scripts.run_api_routed_execution_journey import (
    EXPECTED_ASSERTION_COUNT,
    EXPECTED_PHASE_OPERATIONS,
    READ_OPERATION,
    WRITE_OPERATION,
    MEDUSA_SPEC,
    _bind_phase_f_planner_context,
    _classify_curation,
    _classify_expected_review_outcomes,
    _execution_matches,
    _plan_binding,
    _review_rejection_seen,
    _routed_review_id,
    _select_exact_when_ready,
    _select_created_plan_response,
    _require_single_step,
    _safe_execution,
    _wait_execution_query,
    _wait_for_restored_conversation,
)


ROOT = Path(__file__).resolve().parents[3]
SCRIPT = ROOT / "scripts" / "run_api_routed_execution_journey.py"


class _WaitTarget:
    async def wait_for(self, *, timeout: int) -> None:
        assert 0 < timeout <= 30_000


class _DecisionGroup:
    def __init__(self, operation_id: str, decisions: list[tuple[str, str]]) -> None:
        self.operation_id = operation_id
        self.decisions = decisions

    def get_by_role(self, role: str, *, name: str, exact: bool):
        assert role == "radio"
        assert exact is True
        operation_id = self.operation_id
        decisions = self.decisions

        class _Radio:
            async def click(self) -> None:
                decisions.append((operation_id, name))

        return _Radio()


class _CurationPanel:
    def __init__(self) -> None:
        self.groups: list[str] = []
        self.decisions: list[tuple[str, str]] = []

    def get_by_role(self, role: str, *, name: str, exact: bool):
        assert role == "group"
        assert exact is True
        operation_id = name.removeprefix("Availability for ")
        self.groups.append(operation_id)
        return _DecisionGroup(operation_id, self.decisions)

    def get_by_text(self, text: str, *, exact: bool):
        assert text == "Every discovered operation is explicitly classified."
        assert exact is True
        return _WaitTarget()


class _Select:
    def __init__(
        self,
        *,
        visible: list[bool] | None = None,
        enabled: list[bool] | None = None,
        option_present: list[bool] | None = None,
        detach_once: bool = False,
    ) -> None:
        self.value = ""
        self.visible = list(visible or [True])
        self.enabled = list(enabled or [True])
        self.option_present = list(option_present or [True])
        self.detach_once = detach_once
        self.select_calls = 0

    @staticmethod
    def _next(values: list[bool]) -> bool:
        if len(values) > 1:
            return values.pop(0)
        return values[0]

    async def is_visible(self) -> bool:
        return self._next(self.visible)

    async def is_enabled(self) -> bool:
        return self._next(self.enabled)

    async def evaluate(self, script: str, expected: str) -> bool:
        assert "element.options" in script
        assert expected
        return self._next(self.option_present)

    async def select_option(self, value: str, *, timeout: int) -> None:
        assert 0 < timeout <= 1_500
        self.select_calls += 1
        if self.detach_once:
            self.detach_once = False
            raise PlaywrightError("Element was detached from the DOM during selection")
        self.value = value

    async def input_value(self) -> str:
        return self.value


class _PlannerContextPanel:
    def __init__(self) -> None:
        self.source = _Select()
        self.profile = _Select()
        self.expected_copy = ""

    def get_by_label(self, name: str, *, exact: bool):
        assert exact is True
        return {
            "Effective API revision": self.source,
            "Saved connection profile": self.profile,
        }[name]

    def get_by_text(self, text: str, *, exact: bool):
        assert exact is True
        self.expected_copy = text
        return _WaitTarget()


class _ReviewSurface:
    def __init__(self, labelled_by: str | None) -> None:
        self.labelled_by = labelled_by

    async def get_attribute(self, name: str) -> str | None:
        assert name == "aria-labelledby"
        return self.labelled_by


class _ConversationRestorePage:
    def __init__(
        self,
        values: list[str | None],
        *,
        wait_error: BaseException | None = None,
        evaluated_value: str | None | object = ...,
    ) -> None:
        self.values = list(values)
        self.wait_error = wait_error
        self.evaluated_value = evaluated_value
        self.events: list[str] = []

    async def wait_for_function(
        self,
        script: str,
        *,
        arg: list[str],
        timeout: int,
    ) -> None:
        self.events.append("wait-for-exact-conversation")
        assert "sessionStorage.getItem(key) === expected" in script
        assert arg[0] == "corpus.selected-conversation.v1"
        assert 0 < timeout <= 30_000
        if self.wait_error is not None:
            raise self.wait_error
        expected = arg[1]
        while len(self.values) > 1:
            value = self.values.pop(0)
            if value == expected:
                return
        if self.values[0] != expected:
            raise PlaywrightTimeoutError("Timeout 5ms exceeded")

    async def evaluate(self, script: str) -> str | None:
        self.events.append("read-conversation")
        assert "sessionStorage.getItem('corpus.selected-conversation.v1')" in script
        if self.evaluated_value is not ...:
            return self.evaluated_value  # type: ignore[return-value]
        return self.values[-1]


async def _record_idle(page: _ConversationRestorePage) -> None:
    page.events.append("idle")


def test_direct_entrypoint_loads_without_starting_browser() -> None:
    completed = subprocess.run(
        [sys.executable, str(SCRIPT), "--help"],
        cwd=ROOT,
        check=False,
        capture_output=True,
        text=True,
    )
    assert completed.returncode == 0, completed.stderr
    assert "reviewed write execution" in completed.stdout


def test_supplemental_tab_waits_for_exact_restored_conversation_before_idle(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    import scripts.run_api_routed_execution_journey as journey

    page = _ConversationRestorePage([None, None, "conversation-exact"])
    monkeypatch.setattr(journey, "_wait_for_agent_idle", _record_idle)
    asyncio.run(
        _wait_for_restored_conversation(
            page,
            "conversation-exact",
            timeout_ms=25,
        )
    )
    assert page.events == [
        "wait-for-exact-conversation",
        "idle",
        "read-conversation",
    ]


@pytest.mark.parametrize(
    ("observed", "error", "message"),
    [
        (None, PlaywrightTimeoutError("Timeout 5ms exceeded"), "was not restored"),
        ("conversation-wrong", PlaywrightTimeoutError("Timeout 5ms exceeded"), "restored the wrong conversation"),
    ],
)
def test_supplemental_tab_restore_fails_closed_for_missing_or_wrong_identity(
    monkeypatch: pytest.MonkeyPatch,
    observed: str | None,
    error: BaseException,
    message: str,
) -> None:
    import scripts.run_api_routed_execution_journey as journey

    page = _ConversationRestorePage([observed], wait_error=error)
    monkeypatch.setattr(journey, "_wait_for_agent_idle", _record_idle)
    with pytest.raises((RuntimeError, TimeoutError), match=message):
        asyncio.run(
            _wait_for_restored_conversation(
                page,
                "conversation-exact",
                timeout_ms=5,
            )
        )
    assert "idle" not in page.events


def test_supplemental_tab_restore_rechecks_identity_after_idle(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    import scripts.run_api_routed_execution_journey as journey

    page = _ConversationRestorePage(
        ["conversation-exact"],
        evaluated_value="conversation-remounted-wrong",
    )
    monkeypatch.setattr(journey, "_wait_for_agent_idle", _record_idle)
    with pytest.raises(RuntimeError, match="changed before it became idle"):
        asyncio.run(
            _wait_for_restored_conversation(
                page,
                "conversation-exact",
                timeout_ms=25,
            )
        )
    assert page.events == [
        "wait-for-exact-conversation",
        "idle",
        "read-conversation",
    ]


def test_every_supplemental_tab_restores_exact_identity_before_new_conversation() -> None:
    source = SCRIPT.read_text(encoding="utf-8")
    assert source.count("context.new_page()") == 2  # Primary owner page plus one supplemental tab.
    assert source.count("race_page = await context.new_page()") == 1
    tab = source.index("race_page = await context.new_page()")
    navigation = source.index("await race_page.goto(_concurrent_entry_url(primary.url, args.url))", tab)
    restore = source.index("await _wait_for_restored_conversation(", navigation)
    new_conversation = source.index("await _new_conversation(race_page)", restore)
    assert tab < navigation < restore < new_conversation


def test_declared_assertions_and_exact_operation_boundary_match_source() -> None:
    tree = ast.parse(SCRIPT.read_text(encoding="utf-8"))
    records = [
        node
        for node in ast.walk(tree)
        if isinstance(node, ast.Call)
        and isinstance(node.func, ast.Name)
        and node.func.id == "_record"
    ]
    assert EXPECTED_ASSERTION_COUNT == 12 == len(records)
    assert READ_OPERATION == "GetProductTypes"
    assert WRITE_OPERATION == "PostCarts"
    assert {
        "sources.test_routed_api_read",
        "sources.test_routed_api_write",
    } <= EXPECTED_PHASE_OPERATIONS


def test_single_step_gate_rejects_extra_or_wrong_safety() -> None:
    plan = {
        "steps": [{
            "selected_operation_id": "GetProductTypes",
            "http_safety": "read",
        }]
    }
    _require_single_step(plan, "GetProductTypes", "read")
    with pytest.raises(RuntimeError, match="exact single operation"):
        _require_single_step({"steps": [plan["steps"][0], plan["steps"][0]]}, "GetProductTypes", "read")
    with pytest.raises(RuntimeError, match="unexpected operation"):
        _require_single_step(plan, "PostCarts", "write")


def test_phase_f_classifier_exhausts_inventory_and_uses_explicit_include_set() -> None:
    panel = _CurationPanel()
    asyncio.run(
        _classify_curation(
            panel,
            {"GetProductTypes", "PostCarts", "GetProductTags"},
            {"PostCarts"},
        )
    )
    assert panel.groups == ["GetProductTags", "GetProductTypes", "PostCarts"]
    assert panel.decisions == [
        ("GetProductTags", "Exclude"),
        ("GetProductTypes", "Exclude"),
        ("PostCarts", "Include"),
    ]
    with pytest.raises(RuntimeError, match="absent: MissingOperation"):
        asyncio.run(
            _classify_curation(panel, {"GetProductTypes"}, {"MissingOperation"})
        )
    component = (
        ROOT / "frontend/src/features/sources/ApiOperationCurationPanel.tsx"
    ).read_text(encoding="utf-8")
    assert "<legend>Availability for {item.operation_id}</legend>" in component


def test_exact_6fca_effective_contract_names_the_real_cart_write_postcarts() -> None:
    bundle = load_api_contract_documents(MEDUSA_SPEC)
    source_name = next(iter(bundle.repaired_specs))
    plan = MEDUSA_EFFECTIVE_CONTRACT_PLAN
    revision = approve_contract_patches(
        bundle.repaired_specs[source_name],
        tuple(item.runtime_patch() for item in plan.patches),
        approved_patch_ids=tuple(item.patch_id for item in plan.patches),
        approved_by="phase-f-recorder-contract-regression",
        source_hash=plan.source_canonical_sha256,
        parent_hash=plan.repaired_parent_sha256,
    )
    assert revision.revision_hash == plan.final_canonical_sha256
    assert revision.document["paths"]["/store/carts"]["post"]["operationId"] == "PostCarts"


def test_phase_f_planner_context_binds_exact_single_operation_curation() -> None:
    panel = _PlannerContextPanel()
    asyncio.run(
        _bind_phase_f_planner_context(
            panel,
            {
                "sourceId": "source-exact",
                "profileId": "profile-exact",
                "curationId": "curation-exact",
            },
            expected_included=1,
        )
    )
    assert panel.source.value == "source-exact"
    assert panel.profile.value == "profile-exact"
    assert panel.expected_copy == "Current curation curation-exact · included 1"


def test_exact_select_waits_for_delayed_enable_and_expected_option() -> None:
    select = _Select(
        enabled=[False, False, True],
        option_present=[False, True],
    )
    asyncio.run(
        _select_exact_when_ready(
            select,
            "exact-value",
            label="test option",
        )
    )
    assert select.value == "exact-value"
    assert select.select_calls == 1


def test_exact_select_tolerates_detachment_and_revalidates_readback() -> None:
    select = _Select(detach_once=True)
    asyncio.run(
        _select_exact_when_ready(
            select,
            "exact-value",
            label="test option",
        )
    )
    assert select.value == "exact-value"
    assert select.select_calls == 2


def test_exact_select_times_out_without_expected_option() -> None:
    select = _Select(option_present=[False])
    with pytest.raises(TimeoutError, match="exact test option option"):
        asyncio.run(
            _select_exact_when_ready(
                select,
                "missing-value",
                label="test option",
                timeout_ms=5,
            )
        )


def test_routed_review_id_comes_from_exact_surface_identity() -> None:
    assert (
        asyncio.run(
            _routed_review_id(
                _ReviewSurface("routed-write-review-review_exact-123")
            )
        )
        == "review_exact-123"
    )
    with pytest.raises(RuntimeError, match="review ID is unavailable"):
        asyncio.run(_routed_review_id(_ReviewSurface("other-review-review_123")))


def test_reject_proof_uses_exact_review_event_and_never_rebinds_after_reload() -> None:
    review_id = "review_exact-123"
    trace = [
        {
            "page": "primary",
            "event": "response",
            "method": "POST",
            "path": f"/api/routedeck/reviews/{review_id}/reject",
            "status": 409,
            "operationId": "sources.test_routed_api_write",
            "failureCode": "review_rejected",
        }
    ]
    assert _review_rejection_seen(trace, review_id)
    assert not _review_rejection_seen(trace, "review_other")

    source = SCRIPT.read_text(encoding="utf-8")
    reject = source.index('name="Reject without sending"')
    reload_after_reject = source.index("await primary.reload()", reject)
    fresh_query = source.index("reject_query = await _wait_execution_query(", reload_after_reject)
    proof = source[reload_after_reject:fresh_query]
    assert "_open_planner" not in proof
    assert "_bind_phase_f_planner_context" not in proof
    assert "select_option" not in proof
    assert 'f"Plan {ids[\'writeRejectPlanId\']} · record {reject_plan[\'record_id\']}"' in proof


def test_every_phase_f_plan_create_is_preceded_by_the_phase_f_context_binder() -> None:
    source = SCRIPT.read_text(encoding="utf-8")
    assert "_bind_planner_context" not in source
    assert "await _bind_phase_f_planner_context(panel, ids, expected_included=1)" in source
    creates = []
    start = 0
    while True:
        found = source.find("await _create_plan(", start)
        if found < 0:
            break
        creates.append(found)
        start = found + 1
    opens = []
    start = 0
    while True:
        found = source.find("await _open_planner(primary, ids)", start)
        if found < 0:
            break
        opens.append(found)
        start = found + 1
    assert len(creates) == 4
    assert len(opens) == 4  # Reject proof observes the locked plan without rebinding.
    bound_opens = [max(opened for opened in opens if opened < create) for create in creates]
    assert len(set(bound_opens)) == 4
    assert "_latest_plan(" not in source
    assert source.count("_wait_created_plan(") == 5  # Four calls plus definition.


def test_safe_execution_is_body_header_credential_and_trace_free() -> None:
    safe = _safe_execution(
        {
            "result_id": "result-1",
            "plan_id": "plan-1",
            "source_id": "source-1",
            "source_revision_id": "revision-1",
            "operation_id": "PostCarts",
            "method": "POST",
            "path_template": "/store/carts",
            "safety": "write",
            "status": "succeeded",
            "delivery": "response_received",
            "status_code": 200,
            "response_media_type": "application/json",
            "response_byte_count": 42,
            "response_body_sha256": "a" * 64,
            "error_code": None,
            "public_message": None,
            "validation_issue_count": 0,
            "validation_phases": [],
            "outcome_verified": None,
            "http_call_count": 1,
            "started_at": "2026-08-08T00:00:00Z",
            "finished_at": "2026-08-08T00:00:01Z",
            "headers": {"x-publishable-api-key": "secret-canary"},
            "query": {"token": "secret-canary"},
            "request_body": {"secret": "secret-canary"},
            "response_body": {"cart": {"id": "cart-secret-canary"}},
            "credential_reference_id": "credential-secret-canary",
            "traces": [{"safe_details": {"secret": "secret-canary"}}],
        }
    )
    encoded = json.dumps(safe)
    assert safe["http_call_count"] == 1
    assert safe["response_body_sha256"] == "a" * 64
    assert "secret-canary" not in encoded
    assert "headers" not in safe
    assert "response_body" not in safe
    assert "traces" not in safe


def test_execution_match_requires_response_received_and_exact_one_call() -> None:
    ids = {"sourceId": "source-1", "approvedRevisionId": "revision-1"}
    result = {
        "plan_id": "plan-1",
        "source_id": "source-1",
        "source_revision_id": "revision-1",
        "operation_id": "PostCarts",
        "method": "POST",
        "path_template": "/store/carts",
        "safety": "write",
        "status": "succeeded",
        "delivery": "response_received",
        "http_call_count": 1,
        "validation_issue_count": 0,
    }
    args = (ids, "plan-1", "PostCarts", "POST", "/store/carts", "write", "succeeded", 1)
    assert _execution_matches(result, *args)
    assert not _execution_matches({**result, "delivery": "possibly_sent"}, *args)
    assert not _execution_matches({**result, "http_call_count": 2}, *args)
    assert not _execution_matches({**result, "source_revision_id": "wrong"}, *args)


def test_plan_binding_requires_exact_source_revision_profile_and_curation() -> None:
    ids = {
        "sourceId": "source-1",
        "approvedRevisionId": "revision-1",
        "profileId": "profile-1",
    }
    plan = {
        "source_id": "source-1",
        "source_revision_id": "revision-1",
        "profile_id": "profile-1",
        "curation_id": "curation-1",
    }
    assert _plan_binding(plan, ids, "curation-1")["matches"] is True
    assert _plan_binding({**plan, "profile_id": "wrong"}, ids, "curation-1")["matches"] is False


def test_created_plan_response_is_page_sequence_operation_and_prior_id_exact() -> None:
    def response(sequence: int, page: str, plan_id: str, operation: str, safety: str):
        return {
            "sequence": sequence,
            "page": page,
            "plan": {
                "plan_id": plan_id,
                "state": "ready",
                "steps": [
                    {
                        "selected_operation_id": operation,
                        "method": "POST" if safety == "write" else "GET",
                        "path_template": "/store/carts" if safety == "write" else "/store/product-types",
                        "http_safety": safety,
                    }
                ],
            },
        }

    responses = [
        response(5, "primary", "plan-exact", "PostCarts", "write"),
        response(1, "primary", "plan-old", "PostCarts", "write"),
        response(4, "primary", "plan-wrong-op", "GetProductTypes", "read"),
        response(3, "curation-race", "plan-other-page", "PostCarts", "write"),
    ]
    selected = _select_created_plan_response(
        responses,
        page_name="primary",
        after_sequence=2,
        excluded_plan_ids={"plan-old"},
        operation_id="PostCarts",
        method="POST",
        path_template="/store/carts",
        safety="write",
        state="ready",
    )
    assert selected is not None
    assert selected["plan_id"] == "plan-exact"


def test_fresh_execution_query_ignores_cached_pre_restart_response() -> None:
    observations = {
        "executionQueries": [
            {
                "sequence": 1,
                "page": "primary",
                "planId": "plan-1",
                "status": 200,
                "hasResult": True,
            },
            {
                "sequence": 2,
                "page": "primary",
                "planId": "plan-1",
                "status": 200,
                "hasResult": True,
            },
        ]
    }
    observed = asyncio.run(
        _wait_execution_query(
            observations,
            "plan-1",
            after_sequence=1,
            has_result=True,
        )
    )
    assert observed["sequence"] == 2


def test_review_outcome_classifier_is_same_page_path_operation_and_failure_specific() -> None:
    expected = {
        "page": "primary",
        "status": 409,
        "method": "POST",
        "path": "/api/routedeck/reviews/review-1/accept",
        "operationId": "sources.test_routed_api_write",
        "failureCode": "review_stale",
    }
    unrelated = {
        **expected,
        "page": "curation-race",
        "path": "/api/routedeck/reviews/review-2/accept",
        "failureCode": "other_conflict",
    }
    rejected = {
        **expected,
        "path": "/api/routedeck/reviews/review-3/reject",
        "failureCode": "review_rejected",
    }
    diagnostics = {
        "httpErrors": [expected, rejected, unrelated],
        "consoleErrors": [
            {
                "page": "primary",
                "locationPath": expected["path"],
                "text": "Failed to load resource: the server responded with a status of 409 (Conflict)",
            },
            {
                "page": "primary",
                "locationPath": rejected["path"],
                "text": "Failed to load resource: the server responded with a status of 409 (Conflict)",
            },
            {
                "page": "curation-race",
                "locationPath": unrelated["path"],
                "text": "Failed to load resource: the server responded with a status of 409 (Conflict)",
            },
        ],
        "expectedHttpOutcomes": [],
        "expectedConsoleErrors": [],
    }
    _classify_expected_review_outcomes(diagnostics)
    assert diagnostics["expectedHttpOutcomes"] == [expected, rejected]
    assert [item["page"] for item in diagnostics["expectedConsoleErrors"]] == [
        "primary",
        "primary",
    ]
    assert diagnostics["httpErrors"] == [unrelated]
    assert diagnostics["consoleErrors"][0]["page"] == "curation-race"


def test_journey_order_keeps_one_real_write_and_never_fault_injects_it() -> None:
    source = SCRIPT.read_text(encoding="utf-8")
    ordered = [
        'name="Run routed read"',
        'name="Reject without sending"',
        'name="Accept and send one write"',
        '["docker", "compose", "restart", "backend"]',
        '"accept-time stale curation is visibly blocked with zero API calls"',
        'get_by_label("Sign out"',
    ]
    positions = [source.index(value) for value in ordered]
    assert positions == sorted(positions)
    assert source.count('name="Accept and send one write"') == 4  # two clicks + desktop/mobile capture locators
    assert "transport_outcome_unknown" not in source
    assert "MockTransport" not in source
    assert "context.request" not in source


def test_visual_video_restart_isolation_and_publication_boundaries_are_retained() -> None:
    source = SCRIPT.read_text(encoding="utf-8")
    assert source.count("_capture_execution(") == 4
    assert source.count("_capture_review(") == 3
    assert source.count("_capture_review_mobile(") == 2
    assert '"failure": review.get_by_role("alert")' in source
    assert '390, "height": 844' in source
    assert 'api-routed-execution-continuous.webm' in source
    assert 'api-routed-execution-race.webm' in source
    assert "time.monotonic() - video_clock" in source
    assert "valid_video_chronology" in source
    assert '"videoDurationsSeconds"' in source
    assert "_wait_execution_query(" in source
    assert "_executions(observations).pop" in source
    assert source.count("_plan_binding(") == 5
    assert source.count("_execution_matches(") == 3
    assert 'item.get("path") == "/api/sources"' in source
    assert '"inventory500Count"' in source
    assert '"rawPlaywrightTrace": None' in source
    assert "_publish_evidence(" in source
    assert "second owner cannot inspect" in source


def test_secret_scan_removes_only_the_new_run_before_publication(tmp_path: Path) -> None:
    directory = tmp_path / "phase-f-run"
    directory.mkdir()
    canary = "phase-f-secret-canary"
    (directory / "diagnostic.txt").write_text(canary, encoding="utf-8")
    with pytest.raises(RuntimeError, match="removed before publication"):
        _publish_evidence(
            directory=directory,
            result_path=directory / "result.json",
            trace_path=directory / "corpus-trace.json",
            result_json="{}\n",
            trace_json="[]\n",
            secrets=(canary,),
        )
    assert not directory.exists()
