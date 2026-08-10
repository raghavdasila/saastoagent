from __future__ import annotations

import ast
import asyncio
import json
import subprocess
import sys
from pathlib import Path

from scripts.run_api_route_planning_journey import (
    EXPECTED_ASSERTION_COUNT,
    EXPECTED_PHASE_OPERATIONS,
    INCLUDED_OPERATIONS,
    _classify_exact,
    _create_plan,
    _ranked_operation_ids,
    _binding_matches,
    _publish_evidence,
    _safe_plan,
    _selected_operations,
    _wait_for_agent_idle,
)


ROOT = Path(__file__).resolve().parents[3]
SCRIPT = ROOT / "scripts" / "run_api_route_planning_journey.py"


def _positions(source: str, value: str) -> list[int]:
    positions: list[int] = []
    start = 0
    while True:
        found = source.find(value, start)
        if found < 0:
            return positions
        positions.append(found)
        start = found + len(value)


class _WaitTarget:
    async def wait_for(self, *, timeout: int) -> None:
        assert timeout == 30_000


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
        prefix = "Availability for "
        assert name.startswith(prefix)
        operation_id = name.removeprefix(prefix)
        self.groups.append(operation_id)
        return _DecisionGroup(operation_id, self.decisions)

    def get_by_text(self, text: str, *, exact: bool):
        assert text == "Every discovered operation is explicitly classified."
        assert exact is True
        return _WaitTarget()


class _PlannerInput:
    def __init__(self) -> None:
        self.value = ""

    async def fill(self, value: str) -> None:
        self.value = value

    async def input_value(self) -> str:
        return self.value


class _PlannerButton:
    def __init__(self) -> None:
        self.click_count = 0

    async def is_enabled(self) -> bool:
        return True

    async def click(self) -> None:
        self.click_count += 1


class _PlannerPanel:
    def __init__(self) -> None:
        self.inputs = {
            "What should Corpus route?": _PlannerInput(),
            "Known input name (optional)": _PlannerInput(),
            "Known input value (optional)": _PlannerInput(),
        }
        self.button = _PlannerButton()

    def get_by_label(self, name: str, *, exact: bool):
        assert exact is True
        return self.inputs[name]

    def get_by_role(self, role: str, *, name: str, exact: bool):
        assert role == "button"
        assert name == "Prepare route"
        assert exact is True
        return self.button


class _AgentButton:
    def __init__(self, name: str, events: list[tuple[str, object]]) -> None:
        self.name = name
        self.events = events
        self.enabled_checks = 0

    async def wait_for(self, *, state: str, timeout: int) -> None:
        self.events.append((self.name, (state, timeout)))

    async def is_enabled(self) -> bool:
        self.enabled_checks += 1
        self.events.append((self.name, f"enabled-{self.enabled_checks}"))
        return self.enabled_checks >= 2


class _StreamingPage:
    def __init__(self) -> None:
        self.events: list[tuple[str, object]] = []
        self.buttons = {
            "Stop response": _AgentButton("Stop response", self.events),
            "Send message": _AgentButton("Send message", self.events),
        }
        self.composer = _AgentButton("Message the assistant", self.events)

    def get_by_role(self, role: str, *, name: str, exact: bool):
        assert role == "button"
        assert exact is True
        return self.buttons[name]

    def get_by_label(self, name: str, *, exact: bool):
        assert name == "Message the assistant"
        assert exact is True
        return self.composer


def test_direct_entrypoint_loads_without_starting_a_browser() -> None:
    completed = subprocess.run(
        [sys.executable, str(SCRIPT), "--help"],
        cwd=ROOT,
        check=False,
        capture_output=True,
        text=True,
    )
    assert completed.returncode == 0, completed.stderr
    assert "non-executing API route preparation" in completed.stdout


def test_declared_assertion_count_matches_the_journey() -> None:
    tree = ast.parse(SCRIPT.read_text(encoding="utf-8"))
    calls = [
        node
        for node in ast.walk(tree)
        if isinstance(node, ast.Call)
        and isinstance(node.func, ast.Name)
        and node.func.id == "_record"
    ]
    assert EXPECTED_ASSERTION_COUNT == 13 == len(calls)


def test_real_ambiguity_choice_id_and_current_request_order_is_locked() -> None:
    source = SCRIPT.read_text(encoding="utf-8")
    ordered = [
        '"get product taxonomy"',
        'select_option("GetProductTypesId")',
        '"What should Corpus use for id?"',
        ").fill(clarified_input_canary)",
        '"get product type by id"',
        'known_name="id"',
        '"get product taxonomy then get product taxonomy"',
    ]
    positions = [source.index(value) for value in ordered]
    assert positions == sorted(positions)
    assert INCLUDED_OPERATIONS == {"GetProductTagsId", "GetProductTypesId"}


def test_deep_operation_classification_uses_exact_accessible_group() -> None:
    panel = _CurationPanel()
    asyncio.run(
        _classify_exact(
            panel,
            {"GetProductTypesId", "DeleteCartsIdGiftCards"},
        )
    )
    assert panel.groups == ["DeleteCartsIdGiftCards", "GetProductTypesId"]
    assert panel.decisions == [
        ("DeleteCartsIdGiftCards", "Exclude"),
        ("GetProductTypesId", "Include"),
    ]
    component = (
        ROOT / "frontend/src/features/sources/ApiOperationCurationPanel.tsx"
    ).read_text(encoding="utf-8")
    assert "<legend>Availability for {item.operation_id}</legend>" in component


def test_agent_and_surface_openers_both_precede_plan_creation() -> None:
    source = SCRIPT.read_text(encoding="utf-8")
    agent = source.index('name="Send message"')
    terminal = source.index("await _wait_for_agent_idle(page)", agent)
    first_create = source.index("await _create_plan(")
    surface = source.index('name="Plan routed operation"')
    second_create = source.index("await _create_plan(", first_create + 1)
    assert agent < terminal < first_create < surface < second_create
    assert "sources.prepare_routed_api_test" in EXPECTED_PHASE_OPERATIONS


def test_agent_terminal_barrier_waits_for_detach_visibility_and_enabled() -> None:
    page = _StreamingPage()
    asyncio.run(_wait_for_agent_idle(page))
    assert page.events == [
        ("Stop response", ("detached", 120_000)),
        ("Send message", ("visible", 30_000)),
        ("Message the assistant", ("visible", 30_000)),
        ("Message the assistant", "enabled-1"),
        ("Message the assistant", "enabled-2"),
    ]


def test_agent_planner_binds_exact_source_profile_and_curation_before_create() -> None:
    source = SCRIPT.read_text(encoding="utf-8")
    agent_open = source.index('"agent-origin preparation opens the stable non-executing planner"')
    bind_calls = _positions(source, "await _bind_planner_context(planner, ids)")
    create_calls = _positions(source, "await _create_plan(")
    assert len(bind_calls) == len(create_calls) == 3
    assert all(agent_open < bound < created for bound, created in zip(bind_calls, create_calls))
    source_select = source.index('select_option(ids["sourceId"])', create_calls[0])
    profile_select = source.index('select_option(ids["profileId"])', source_select)
    curation_wait = source.index(
        'f"Current curation {ids[\'curationId\']} · included',
        profile_select,
    )
    assert create_calls[0] < source_select < profile_select < curation_wait


def test_current_request_inputs_are_exactly_bound_before_prepare() -> None:
    panel = _PlannerPanel()
    asyncio.run(
        _create_plan(
            panel,
            request_text="get product type by id",
            known_name="id",
            known_value="ptyp-recorder-canary",
        )
    )
    assert panel.inputs["What should Corpus route?"].value == "get product type by id"
    assert panel.inputs["Known input name (optional)"].value == "id"
    assert panel.inputs["Known input value (optional)"].value == "ptyp-recorder-canary"
    assert panel.button.click_count == 1


def test_safe_plan_retains_identity_but_drops_values_and_internal_fields() -> None:
    safe = _safe_plan(
        {
            "plan_id": "plan-1",
            "record_id": "record-1",
            "previous_record_id": None,
            "source_id": "source-1",
            "source_revision_id": "revision-1",
            "profile_id": "profile-1",
            "curation_id": "curation-1",
            "request_text": "get product type by id",
            "state": "ready",
            "steps": [
                {
                    "selected_operation_id": "GetProductTypesId",
                    "method": "GET",
                    "path_template": "/store/product-types/{id}",
                    "http_safety": "read",
                    "ranked_operations": [
                        {
                            "operation_id": "GetProductTypesId",
                            "endpoint_id": "medusa_store:GetProductTypesId",
                            "score": 0.9,
                        }
                    ],
                }
            ],
            "missing_inputs": [],
            "input_provenance": [
                {"name": "id", "value": "ptyp-sensitive-probe", "source": "current_request"}
            ],
            "managed_parameters": [
                {
                    "name": "x-publishable-api-key",
                    "location": "header",
                    "authentication_method": "api_key",
                    "source": "managed_by_profile",
                }
            ],
            "operation_choice": None,
            "plan_fingerprint": "f" * 64,
            "api_call_count": 0,
            "router_decision": "ROUTE",
            "router_evidence": {"secret": "not-retained"},
            "credential_reference_id": "not-retained",
        }
    )
    encoded = json.dumps(safe)
    assert safe["input_provenance"] == [{"name": "id", "source": "current_request"}]
    assert safe["managed_parameters"] == [
        {
            "name": "x-publishable-api-key",
            "location": "header",
            "authentication_method": "api_key",
            "source": "managed_by_profile",
        }
    ]
    assert "ptyp-sensitive-probe" not in encoded
    assert "router_decision" not in encoded
    assert "router_evidence" not in encoded
    assert "credential_reference_id" not in encoded
    assert _ranked_operation_ids(safe) == {"GetProductTypesId"}
    assert _selected_operations(safe) == {"GetProductTypesId"}


def test_exact_plan_binding_requires_source_revision_profile_and_curation() -> None:
    ids = {
        "sourceId": "source-1",
        "approvedRevisionId": "revision-1",
        "profileId": "profile-1",
        "curationId": "curation-1",
    }
    plan = {
        "source_id": "source-1",
        "source_revision_id": "revision-1",
        "profile_id": "profile-1",
        "curation_id": "curation-1",
    }
    assert _binding_matches(plan, ids)
    for field in ("source_id", "source_revision_id", "profile_id", "curation_id"):
        changed = {**plan, field: "stale"}
        assert not _binding_matches(changed, ids)
    source = SCRIPT.read_text(encoding="utf-8")
    assert "all(_binding_matches(item, ids) for item in plans)" in source


def test_evidence_is_published_only_through_secret_scanning_boundary() -> None:
    source = SCRIPT.read_text(encoding="utf-8")
    assert "context.tracing.start" not in source
    assert '"rawPlaywrightTrace": None' in source
    assert "_publish_evidence(" in source
    assert "clarified_input_canary" in source
    assert "current_input_canary" in source
    assert '"requestBodies": False' in source
    assert '"responseBodies": False' in source
    assert '"credentialValues": False' in source


def test_user_input_canary_removes_run_before_publication(tmp_path: Path) -> None:
    directory = tmp_path / "run"
    directory.mkdir()
    canary = "ptyp-phase-e-current-secret-canary"
    (directory / "diagnostic.txt").write_text(
        f"page error accidentally echoed {canary}", encoding="utf-8"
    )
    try:
        _publish_evidence(
            directory=directory,
            result_path=directory / "result.json",
            trace_path=directory / "corpus-trace.json",
            result_json="{}\n",
            trace_json="[]\n",
            secrets=(canary,),
        )
    except RuntimeError as error:
        assert "removed before publication" in str(error)
    else:
        raise AssertionError("An input canary leak must abort publication.")
    assert not directory.exists()


def test_strict_visual_and_persistence_proof_remains_in_the_journey() -> None:
    source = SCRIPT.read_text(encoding="utf-8")
    assert source.count("_capture_group(") == 5
    assert '"06-second-owner-empty-inventory-desktop"' in source
    assert '390,\n                844' in source
    assert '["docker", "compose", "restart", "backend"]' in source
    assert 'name="Execute"' in source
    assert "second owner cannot see" in source
