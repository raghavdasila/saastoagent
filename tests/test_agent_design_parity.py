from __future__ import annotations

import copy

import pytest
from routedeck_core.app import Application, Feature, compile_app
from routedeck_core.contracts.agent import AgentPolicy
from routedeck_core.contracts.application import Capability, Node
from routedeck_core.contracts.navigation import (
    DeepLinkPolicy,
    NodeKind,
    NodeRef,
    RecoveryPolicy,
    Route,
    Transition,
)
from routedeck_core.contracts.operations import (
    Operation,
    OperationSource,
    ReviewPolicy,
    SafetyClass,
)
from routedeck_core.contracts.projection import FrozenJsonObject
from routedeck_core.contracts.suggestions import SuggestedAction
from routedeck_core.contracts.surfaces import Surface, SurfaceSlots

from scripts.check_agent_design_parity import (
    ParityInputError,
    check_parity,
    format_failure_report,
    group_failures,
)


EMPTY_INPUT_SCHEMA = FrozenJsonObject(
    {
        "type": "object",
        "properties": {},
        "additionalProperties": False,
    }
)
PLAN_INPUT_SCHEMA = FrozenJsonObject(
    {
        "type": "object",
        "properties": {"plan_id": {"type": "string", "minLength": 1}},
        "required": ["plan_id"],
        "additionalProperties": False,
    }
)
OPTIONAL_PLAN_INPUT_SCHEMA = FrozenJsonObject(
    {
        "type": "object",
        "properties": {"plan_id": {"type": "string", "minLength": 1}},
        "additionalProperties": False,
    }
)
EXTRA_PLAN_INPUT_SCHEMA = FrozenJsonObject(
    {
        "type": "object",
        "properties": {
            "plan_id": {"type": "string", "minLength": 1},
            "unresolved": {"type": "string"},
        },
        "required": ["plan_id"],
        "additionalProperties": False,
    }
)
CONSTRAINED_PLAN_INPUT_SCHEMA = FrozenJsonObject(
    {
        "type": "object",
        "properties": {
            "plan_id": {"type": "string", "minLength": 1, "maxLength": 128}
        },
        "required": ["plan_id"],
        "additionalProperties": False,
    }
)
ANNOTATED_PLAN_INPUT_SCHEMA = FrozenJsonObject(
    {
        "type": "object",
        "properties": {
            "plan_id": {
                "type": "string",
                "minLength": 1,
                "description": "Opaque plan identifier.",
            }
        },
        "required": ["plan_id"],
        "additionalProperties": False,
    }
)


def _compiled_app():
    policies = {
        scope: AgentPolicy(
            id=f"demo.{scope}_policy",
            instruction=f"{scope.title()} policy.",
        )
        for scope in ("feature", "node", "capability", "surface", "operation")
    }
    policies["prompt"] = AgentPolicy(
        id="demo.feature_prompt",
        instruction="You are in Demo.",
    )
    operation = Operation(
        id="demo.run",
        title="Run",
        description="Run the designed action.",
        safety_class=SafetyClass.READ_EXTERNAL,
        allowed_sources=frozenset(
            {OperationSource.AGENT, OperationSource.SURFACE}
        ),
        outcomes=("completed",),
        policy_refs=(policies["operation"].ref,),
    )
    surface = Surface(
        id="demo.home_surface",
        component="demo.home_surface",
        policy_refs=(policies["surface"].ref,),
    )
    capability = Capability(
        id="demo.use",
        title="Use demo",
        operations=(operation.ref,),
        surfaces=(surface.ref,),
        policy_refs=(policies["capability"].ref,),
    )
    node = Node(
        id="demo.home",
        title="Demo home",
        kind=NodeKind.SECTION,
        route=Route(template="/", deep_link_policy=DeepLinkPolicy.SHAREABLE),
        operations=(operation,),
        outgoing=(
            Transition(
                operation=operation.ref,
                outcome="completed",
                target=NodeRef(id="demo.home"),
            ),
        ),
        capabilities=(capability,),
        surfaces=SurfaceSlots(active=surface),
        policy_refs=(policies["node"].ref,),
        suggested_actions=(
            SuggestedAction(
                id="demo.run_action",
                label="Run it",
                operation_id=operation.id,
            ),
        ),
    )
    return compile_app(
        Application(
            name="demo",
            entry_node=node.ref,
            features=(
                Feature(
                    namespace="demo",
                    nodes=(node,),
                    agent_policies=tuple(policies.values()),
                    policy_refs=(policies["prompt"].ref, policies["feature"].ref),
                ),
            ),
        )
    )


def _compiled_variant_app(
    *,
    action_safety: SafetyClass = SafetyClass.STATE_SELECTION,
    action_schema: FrozenJsonObject = EMPTY_INPUT_SCHEMA,
    action_outcome: str = "opened",
    read_outcome: str = "observed",
    write_outcome: str = "observed",
    read_schema: FrozenJsonObject = PLAN_INPUT_SCHEMA,
    write_schema: FrozenJsonObject = PLAN_INPUT_SCHEMA,
    suggested_operation_id: str | None = None,
    suggested_arguments: FrozenJsonObject = FrozenJsonObject({}),
    include_suggested_action: bool = True,
    include_execution_variants: bool = True,
):
    policies = {
        scope: AgentPolicy(
            id=f"demo.{scope}_policy",
            instruction=f"{scope.title()} policy.",
        )
        for scope in ("feature", "node", "capability", "surface", "operation")
    }
    policies["prompt"] = AgentPolicy(
        id="demo.feature_prompt",
        instruction="You are in Demo.",
    )
    sources = frozenset({OperationSource.AGENT, OperationSource.SURFACE})
    action = Operation(
        id="demo.prepare_run",
        title="Prepare run",
        description="Open the non-executing planner.",
        input_schema=action_schema,
        safety_class=action_safety,
        allowed_sources=sources,
        outcomes=(action_outcome,),
        policy_refs=(policies["operation"].ref,),
    )
    read = Operation(
        id="demo.run_read",
        title="Run read",
        description="Execute an immutable read plan.",
        input_schema=read_schema,
        safety_class=SafetyClass.READ_EXTERNAL,
        allowed_sources=sources,
        outcomes=(read_outcome,),
        policy_refs=(policies["operation"].ref,),
    )
    write = Operation(
        id="demo.run_write",
        title="Run write",
        description="Execute an immutable reviewed write plan.",
        input_schema=write_schema,
        safety_class=SafetyClass.WRITE_EXTERNAL,
        allowed_sources=sources,
        review_policy=ReviewPolicy.REQUIRED,
        outcomes=(write_outcome,),
        unknown_recovery_directive="Verify external state before another attempt.",
        policy_refs=(policies["operation"].ref,),
    )
    surface = Surface(
        id="demo.home_surface",
        component="demo.home_surface",
        policy_refs=(policies["surface"].ref,),
    )
    operations = (
        (action, read, write) if include_execution_variants else (action,)
    )
    capability = Capability(
        id="demo.use",
        title="Use demo",
        operations=tuple(operation.ref for operation in operations),
        surfaces=(surface.ref,),
        policy_refs=(policies["capability"].ref,),
    )
    node_ref = NodeRef(id="demo.home")
    node = Node(
        id=node_ref.id,
        title="Demo home",
        kind=NodeKind.SECTION,
        route=Route(template="/", deep_link_policy=DeepLinkPolicy.SHAREABLE),
        operations=operations,
        outgoing=tuple(
            Transition(operation=operation.ref, outcome=outcome, target=node_ref)
            for operation, outcome in (
                (action, action_outcome),
                (read, read_outcome),
                (write, write_outcome),
            )
            if operation in operations
        ),
        capabilities=(capability,),
        surfaces=SurfaceSlots(active=surface),
        policy_refs=(policies["node"].ref,),
        suggested_actions=(
            (
                SuggestedAction(
                    id="demo.run_action",
                    label="Run it",
                    operation_id=suggested_operation_id or action.id,
                    arguments=suggested_arguments,
                ),
            )
            if include_suggested_action
            else ()
        ),
        recovery=RecoveryPolicy(
            directives=("Verify external state before another attempt.",),
            failure_surface=surface.ref,
        ),
    )
    return compile_app(
        Application(
            name="demo",
            entry_node=node.ref,
            features=(
                Feature(
                    namespace="demo",
                    nodes=(node,),
                    agent_policies=tuple(policies.values()),
                    policy_refs=(policies["prompt"].ref, policies["feature"].ref),
                ),
            ),
        )
    )


def _design_state():
    return {
        "features": [
            {
                "name": "Demo",
                "prompt": "You are in Demo.",
                "policies": ["Feature policy."],
                "conversationEvals": [],
                "stories": [
                    {
                        "title": "Use Demo",
                        "nodePolicies": ["Node policy."],
                        "capabilities": [
                            {
                                "name": "Use demo",
                                "operationNames": ["Run"],
                                "surfaceNames": ["Demo home"],
                                "policies": ["Capability policy."],
                            }
                        ],
                        "surfaces": [
                            {
                                "name": "Demo home",
                                "policies": ["Surface policy."],
                            }
                        ],
                        "operations": [
                            {
                                "name": "Run",
                                "availableThrough": "both",
                                "policies": ["Operation policy."],
                            }
                        ],
                        "suggestedActions": [
                            {
                                "id": "demo.run_action",
                                "label": "Run it",
                                "operationName": "Run",
                            }
                        ],
                        "behaviorEvals": [
                            {
                                "id": "demo-run",
                                "actionPlan": {
                                    "steps": [
                                        {
                                            "id": "demo-run-opening",
                                            "kind": "message",
                                        },
                                        {
                                            "id": "demo-run-action",
                                            "kind": "suggested-action",
                                            "behavior": "Use Demo",
                                            "action": "Run it",
                                        },
                                        {
                                            "id": "demo-run-final",
                                            "kind": "checkpoint",
                                        },
                                    ]
                                },
                            }
                        ],
                    }
                ],
            }
        ]
    }


def _manifest():
    return {
        "version": 1,
        "unimplementedDesignFeatures": [],
        "features": [
            {
                "designFeature": "Demo",
                "routeDeckFeature": "demo",
                "implementationStatus": "complete",
                "featurePromptPolicy": "demo.feature_prompt",
                "evaluationBindings": {
                    "demo-run": {
                        "setupAdapter": "demo.ready",
                        "steps": {
                            "demo-run-action": {"operation": "demo.run"}
                        },
                    }
                },
                "behaviors": [
                    {
                        "designBehavior": "Use Demo",
                        "node": "demo.home",
                        "capabilities": {"Use demo": "demo.use"},
                        "surfaces": {"Demo home": "demo.home_surface"},
                        "operations": {"Run": "demo.run"},
                    }
                ],
            }
        ],
    }


def test_pending_external_evidence_does_not_invent_runtime_binding():
    manifest = _manifest()
    manifest["features"][0]["evaluationBindings"] = {
        "demo-run": {
            "implementationStatus": "pending_external_evidence",
            "externalEvidenceOwner": "scripts/run_demo.py",
        }
    }

    assert check_parity(_design_state(), manifest, _compiled_app()) == []


def test_pending_external_evidence_rejects_fake_executable_binding():
    manifest = _manifest()
    manifest["features"][0]["evaluationBindings"]["demo-run"] = {
        "implementationStatus": "pending_external_evidence",
        "externalEvidenceOwner": "scripts/run_demo.py",
        "setupAdapter": "demo.ready",
        "steps": {},
    }

    with pytest.raises(ParityInputError, match="must not declare executable"):
        check_parity(_design_state(), manifest, _compiled_app())


def _variant_manifest():
    manifest = _manifest()
    manifest["features"][0]["behaviors"][0]["operations"] = {
        "Run": {
            "selector": "resolved_http_safety_v1",
            "actionOperation": "demo.prepare_run",
            "suggestedActionId": "demo.run_action",
            "variants": {
                "read": "demo.run_read",
                "write": "demo.run_write",
            },
        }
    }
    manifest["features"][0]["evaluationBindings"]["demo-run"]["steps"][
        "demo-run-action"
    ]["operation"] = "demo.prepare_run"
    return manifest


def _planned_design_state():
    design = _design_state()
    planned_feature = copy.deepcopy(design["features"][0])
    planned_feature["name"] = "Planned API"
    planned_feature["stories"][0]["title"] = "Route and test an API operation"
    planned_feature["stories"][0]["operations"][0]["name"] = (
        "Test routed API operation"
    )
    planned_feature["stories"][0]["capabilities"][0]["operationNames"] = [
        "Test routed API operation"
    ]
    planned_feature["stories"][0]["suggestedActions"][0]["operationName"] = (
        "Test routed API operation"
    )
    planned_feature["stories"][0]["suggestedActions"][0]["id"] = "demo.run_action"
    planned_feature["conversationEvals"] = []
    planned_feature["stories"][0]["behaviorEvals"] = []
    design["features"].append(planned_feature)
    return design


def _planned_manifest():
    manifest = _manifest()
    manifest["unimplementedDesignFeatures"] = ["Planned API"]
    mapping = {
        "selector": "resolved_http_safety_v1",
        "actionOperation": "sources.prepare_routed_api_test",
        "suggestedActionId": "demo.run_action",
        "variants": {
            "read": "sources.test_routed_api_read",
            "write": "sources.test_routed_api_write",
        },
    }
    sources = ["agent", "surface"]
    manifest["designOnlyMappings"] = {
        "Planned API": {
            "plannedOperationMappings": [
                {
                    "designBehavior": "Route and test an API operation",
                    "operations": {"Test routed API operation": mapping},
                    "suggestedActions": {
                        "demo.run_action": {
                            "operation": "sources.prepare_routed_api_test",
                            "arguments": {},
                        }
                    },
                    "plannedContracts": {
                        "sources.prepare_routed_api_test": {
                            "implementationStatus": "planned",
                            "safetyClass": "state_selection",
                            "review": "none",
                            "allowedSources": sources,
                            "inputKind": "empty",
                            "outcomes": ["opened"],
                            "externalExecution": False,
                        },
                        "sources.test_routed_api_read": {
                            "implementationStatus": "planned",
                            "safetyClass": "read_external",
                            "review": "none",
                            "allowedSources": sources,
                            "inputKind": "opaque_plan_id",
                            "outcomes": ["observed"],
                            "externalExecution": True,
                        },
                        "sources.test_routed_api_write": {
                            "implementationStatus": "planned",
                            "safetyClass": "write_external",
                            "review": "required",
                            "allowedSources": sources,
                            "inputKind": "opaque_plan_id",
                            "outcomes": ["observed"],
                            "externalExecution": True,
                            "unknownRecoveryDirective": (
                                "Do not retry automatically; verify external state."
                            ),
                        },
                    },
                }
            ]
        }
    }
    return manifest


def _mixed_current_action_manifest():
    manifest = _planned_manifest()
    planned = manifest["designOnlyMappings"]["Planned API"][
        "plannedOperationMappings"
    ][0]
    mapping = planned["operations"]["Test routed API operation"]
    mapping["actionOperation"] = "demo.prepare_run"
    mapping["variants"] = {
        "read": "demo.run_read",
        "write": "demo.run_write",
    }
    planned["suggestedActions"]["demo.run_action"]["operation"] = (
        "demo.prepare_run"
    )
    contracts = planned["plannedContracts"]
    action_contract = contracts.pop("sources.prepare_routed_api_test")
    action_contract["implementationStatus"] = "implemented_browser_behavior_validated"
    contracts["demo.run_read"] = contracts.pop("sources.test_routed_api_read")
    contracts["demo.run_write"] = contracts.pop("sources.test_routed_api_write")
    planned["currentContracts"] = {"demo.prepare_run": action_contract}
    return manifest


def test_agent_design_parity_accepts_matching_shape_and_scopes() -> None:
    assert check_parity(_design_state(), _manifest(), _compiled_app()) == []


def test_agent_design_parity_accepts_safety_selected_operation_variants() -> None:
    assert (
        check_parity(
            _design_state(),
            _variant_manifest(),
            _compiled_variant_app(),
        )
        == []
    )


def test_agent_design_parity_rejects_variant_with_unsafe_action_contract() -> None:
    failures = check_parity(
        _design_state(),
        _variant_manifest(),
        _compiled_variant_app(action_safety=SafetyClass.DRAFT),
    )

    assert any(
        "variant action operation must be empty-input state_selection" in failure
        for failure in failures
    )


@pytest.mark.parametrize(
    ("mutation", "expected"),
    [
        ({"action_outcome": "started"}, "variant action operation"),
        ({"read_outcome": "completed"}, "read variant must"),
        ({"write_outcome": "completed"}, "write variant must"),
        ({"read_schema": OPTIONAL_PLAN_INPUT_SCHEMA}, "read variant must"),
        ({"write_schema": OPTIONAL_PLAN_INPUT_SCHEMA}, "write variant must"),
        ({"read_schema": EXTRA_PLAN_INPUT_SCHEMA}, "read variant must"),
        ({"write_schema": EXTRA_PLAN_INPUT_SCHEMA}, "write variant must"),
        ({"read_schema": CONSTRAINED_PLAN_INPUT_SCHEMA}, "read variant must"),
        ({"write_schema": ANNOTATED_PLAN_INPUT_SCHEMA}, "write variant must"),
    ],
)
def test_agent_design_parity_rejects_incomplete_variant_contracts(
    mutation, expected
) -> None:
    failures = check_parity(
        _design_state(),
        _variant_manifest(),
        _compiled_variant_app(**mutation),
    )

    assert any(expected in failure for failure in failures)


@pytest.mark.parametrize(
    "mutation",
    [
        {
            "suggested_operation_id": "demo.run_read",
            "suggested_arguments": FrozenJsonObject({"plan_id": "unresolved"}),
        },
        {
            "action_schema": OPTIONAL_PLAN_INPUT_SCHEMA,
            "suggested_arguments": FrozenJsonObject({"plan_id": "unresolved"}),
        },
        {"include_suggested_action": False},
    ],
)
def test_agent_design_parity_rejects_compiled_variant_suggestion_drift(
    mutation,
) -> None:
    failures = check_parity(
        _design_state(),
        _variant_manifest(),
        _compiled_variant_app(**mutation),
    )

    assert any("compiled SuggestedAction" in failure for failure in failures)


def test_agent_design_parity_rejects_compiled_variant_missing_studio_action_id() -> None:
    manifest = _variant_manifest()
    manifest["features"][0]["behaviors"][0]["operations"]["Run"][
        "suggestedActionId"
    ] = "demo.missing"

    with pytest.raises(ParityInputError, match="must exist exactly once"):
        check_parity(_design_state(), manifest, _compiled_variant_app())


def test_agent_design_parity_rejects_compiled_variant_duplicate_studio_action_id() -> None:
    design = _design_state()
    actions = design["features"][0]["stories"][0]["suggestedActions"]
    actions.append(copy.deepcopy(actions[0]))

    with pytest.raises(ParityInputError, match="must exist exactly once"):
        check_parity(design, _variant_manifest(), _compiled_variant_app())


def test_agent_design_parity_rejects_compiled_variant_studio_action_retarget() -> None:
    design = _design_state()
    story = design["features"][0]["stories"][0]
    other = copy.deepcopy(story["operations"][0])
    other["name"] = "Other"
    story["operations"].append(other)
    story["suggestedActions"][0]["operationName"] = "Other"

    with pytest.raises(ParityInputError, match="must target Studio operation 'Run'"):
        check_parity(design, _variant_manifest(), _compiled_variant_app())


def test_agent_design_parity_accepts_truthful_uncompiled_planned_variants() -> None:
    assert (
        check_parity(
            _planned_design_state(),
            _planned_manifest(),
            _compiled_app(),
        )
        == []
    )


def test_agent_design_parity_checks_suggestion_for_mixed_current_action() -> None:
    failures = check_parity(
        _planned_design_state(),
        _mixed_current_action_manifest(),
        _compiled_variant_app(include_execution_variants=False),
    )
    assert not any("compiled SuggestedAction" in failure for failure in failures)

    with pytest.raises(
        ParityInputError,
        match="compiled SuggestedAction .* must exist exactly once",
    ):
        check_parity(
            _planned_design_state(),
            _mixed_current_action_manifest(),
            _compiled_variant_app(
                include_execution_variants=False,
                include_suggested_action=False,
            ),
        )


def test_agent_design_parity_rejects_planned_variant_with_unresolved_action_input() -> None:
    manifest = _planned_manifest()
    planned = manifest["designOnlyMappings"]["Planned API"][
        "plannedOperationMappings"
    ][0]
    planned["plannedContracts"]["sources.prepare_routed_api_test"][
        "inputKind"
    ] = "opaque_plan_id"

    with pytest.raises(ParityInputError, match="invalid planned action contract"):
        check_parity(_planned_design_state(), manifest, _compiled_app())


def test_agent_design_parity_rejects_unknown_variant_selector() -> None:
    manifest = _planned_manifest()
    planned = manifest["designOnlyMappings"]["Planned API"][
        "plannedOperationMappings"
    ][0]
    planned["operations"]["Test routed API operation"]["selector"] = "dynamic"

    with pytest.raises(ParityInputError, match="resolved_http_safety_v1"):
        check_parity(_planned_design_state(), manifest, _compiled_app())


def test_agent_design_parity_rejects_planned_suggestion_retargeted_to_execution() -> None:
    manifest = _planned_manifest()
    planned = manifest["designOnlyMappings"]["Planned API"][
        "plannedOperationMappings"
    ][0]
    planned["suggestedActions"]["demo.run_action"]["operation"] = (
        "sources.test_routed_api_read"
    )

    with pytest.raises(ParityInputError, match="resolve only to actionOperation"):
        check_parity(_planned_design_state(), manifest, _compiled_app())


def test_agent_design_parity_rejects_planned_suggestion_dynamic_arguments() -> None:
    manifest = _planned_manifest()
    planned = manifest["designOnlyMappings"]["Planned API"][
        "plannedOperationMappings"
    ][0]
    planned["suggestedActions"]["demo.run_action"]["arguments"] = {
        "plan_id": "unresolved"
    }

    with pytest.raises(ParityInputError, match="dynamic or unresolved arguments"):
        check_parity(_planned_design_state(), manifest, _compiled_app())


def test_agent_design_parity_rejects_removed_planned_suggestion_binding() -> None:
    manifest = _planned_manifest()
    planned = manifest["designOnlyMappings"]["Planned API"][
        "plannedOperationMappings"
    ][0]
    planned["suggestedActions"] = {}

    with pytest.raises(ParityInputError, match="must exactly cover"):
        check_parity(_planned_design_state(), manifest, _compiled_app())


def test_agent_design_parity_rejects_planned_variant_missing_studio_action_id() -> None:
    manifest = _planned_manifest()
    planned = manifest["designOnlyMappings"]["Planned API"][
        "plannedOperationMappings"
    ][0]
    planned["operations"]["Test routed API operation"]["suggestedActionId"] = (
        "api-test-operation-missing"
    )

    with pytest.raises(ParityInputError, match="must exist exactly once"):
        check_parity(_planned_design_state(), manifest, _compiled_app())


def test_agent_design_parity_rejects_planned_variant_duplicate_studio_action_id() -> None:
    design = _planned_design_state()
    actions = design["features"][1]["stories"][0]["suggestedActions"]
    actions.append(copy.deepcopy(actions[0]))

    with pytest.raises(ParityInputError, match="must exist exactly once"):
        check_parity(design, _planned_manifest(), _compiled_app())


def test_agent_design_parity_rejects_planned_variant_studio_action_retarget() -> None:
    design = _planned_design_state()
    story = design["features"][1]["stories"][0]
    other = copy.deepcopy(story["operations"][0])
    other["name"] = "Other planned operation"
    story["operations"].append(other)
    story["suggestedActions"][0]["operationName"] = "Other planned operation"

    with pytest.raises(
        ParityInputError,
        match="must target Studio operation 'Test routed API operation'",
    ):
        check_parity(design, _planned_manifest(), _compiled_app())


def test_agent_design_parity_reports_policy_scope_drift() -> None:
    design_state = _design_state()
    design_state["features"][0]["stories"][0]["operations"][0]["policies"] = [
        "Changed operation policy."
    ]

    failures = check_parity(design_state, _manifest(), _compiled_app())

    assert any("missing" in failure and "Changed operation policy" in failure for failure in failures)
    assert any("undesigned" in failure and "Operation policy" in failure for failure in failures)


def test_agent_design_parity_groups_policy_drift_without_hiding_its_direction() -> None:
    failures = [
        "Feature 'Demo' policies: missing 2 policy activation(s): 'Designed policy.'",
        "Feature 'Demo' policies: has 1 undesigned policy activation(s): 'Old policy.'",
        "Compiled RouteDeck features missing implementation-manifest mappings: sources",
    ]

    groups = {group.key: items for group, items in group_failures(failures)}
    report = "\n".join(format_failure_report(failures, verbose=False))

    assert len(groups["policy"]) == 2
    assert len(groups["feature_coverage"]) == 1
    assert "Policy activation drift: 2" in report
    assert "2 designed activations missing; 1 compiled activations undesigned" in report
    assert "Designed policy." not in report
    assert "Run again with --verbose" in report


def test_agent_design_parity_verbose_report_retains_every_mismatch() -> None:
    failures = [
        "Feature 'Demo' policies: missing 1 policy activation(s): 'Designed policy.'",
        "Feature 'Demo' Nodes: contains objects absent from Studio mapping: demo.extra",
    ]

    report = "\n".join(format_failure_report(failures, verbose=True))

    assert "Mismatch details:" in report
    assert all(failure in report for failure in failures)
    assert "Run again with --verbose" not in report
