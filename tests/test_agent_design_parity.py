from __future__ import annotations

from routedeck_core.app import Application, Feature, compile_app
from routedeck_core.contracts.agent import AgentPolicy
from routedeck_core.contracts.application import Capability, Node
from routedeck_core.contracts.navigation import (
    DeepLinkPolicy,
    NodeKind,
    NodeRef,
    Route,
    Transition,
)
from routedeck_core.contracts.operations import Operation, OperationSource, SafetyClass
from routedeck_core.contracts.suggestions import SuggestedAction
from routedeck_core.contracts.surfaces import Surface, SurfaceSlots

from scripts.check_agent_design_parity import (
    check_parity,
    format_failure_report,
    group_failures,
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


def _design_state():
    return {
        "features": [
            {
                "name": "Demo",
                "prompt": "You are in Demo.",
                "policies": ["Feature policy."],
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
                                "policies": ["Operation policy."],
                            }
                        ],
                        "suggestedActions": [
                            {
                                "label": "Run it",
                                "operationName": "Run",
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
        "features": [
            {
                "designFeature": "Demo",
                "routeDeckFeature": "demo",
                "featurePromptPolicy": "demo.feature_prompt",
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


def test_agent_design_parity_accepts_matching_shape_and_scopes() -> None:
    assert check_parity(_design_state(), _manifest(), _compiled_app()) == []


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
