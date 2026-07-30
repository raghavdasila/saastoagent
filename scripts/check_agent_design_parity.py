"""Compare the product-semantic Design Studio state with compiled RouteDeck shape.

RouteDeck identifiers live only in the implementation-owned manifest. The
Design Studio remains responsible for prompts, product objects, policies, and
their scopes without prescribing source files, transports, handlers, or IDs.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from collections import Counter
from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_DESIGN_STATE = (
    PROJECT_ROOT / "docs" / "corpus-agent-design" / "workbench" / "design-state.json"
)
DEFAULT_MANIFEST = PROJECT_ROOT / "contracts" / "corpus-agent-design-routedeck-manifest.json"
BACKEND_SOURCE = PROJECT_ROOT / "backend" / "src"


class ParityInputError(ValueError):
    """Raised when design or manifest input does not have the required shape."""


@dataclass(frozen=True)
class FailureGroup:
    """One actionable class of parity mismatch in the CLI report."""

    key: str
    title: str


FAILURE_GROUPS = (
    FailureGroup("feature_coverage", "Feature manifest coverage"),
    FailureGroup("behavior_node", "Behavior-to-Node boundary"),
    FailureGroup("prompt", "Feature prompt parity"),
    FailureGroup("policy", "Policy activation drift"),
    FailureGroup("missing_target", "Manifest targets missing from compiled app"),
    FailureGroup(
        "missing_membership", "Designed shape missing from compiled membership"
    ),
    FailureGroup("extra_shape", "Compiled shape absent from Studio mapping"),
    FailureGroup("suggested_action", "SuggestedAction parity"),
    FailureGroup("mapping_integrity", "Manifest mapping integrity"),
    FailureGroup("other", "Other parity mismatches"),
)


def _load_object(path: Path) -> dict[str, Any]:
    try:
        value: Any = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as error:
        raise ParityInputError(f"Input file does not exist: {path}") from error
    except json.JSONDecodeError as error:
        raise ParityInputError(f"Input file is not valid JSON: {path}: {error}") from error
    if not isinstance(value, dict):
        raise ParityInputError(f"Input file must contain a JSON object: {path}")
    return value


def _required_string(value: Mapping[str, Any], key: str, owner: str) -> str:
    candidate = value.get(key)
    if not isinstance(candidate, str) or not candidate.strip():
        raise ParityInputError(f"{owner} requires non-empty string {key!r}")
    return candidate


def _required_list(value: Mapping[str, Any], key: str, owner: str) -> list[Any]:
    candidate = value.get(key)
    if not isinstance(candidate, list):
        raise ParityInputError(f"{owner} requires array {key!r}")
    return candidate


def _required_mapping(
    value: Mapping[str, Any], key: str, owner: str
) -> dict[str, str]:
    candidate = value.get(key)
    if not isinstance(candidate, dict) or any(
        not isinstance(name, str)
        or not name.strip()
        or not isinstance(identifier, str)
        or not identifier.strip()
        for name, identifier in candidate.items()
    ):
        raise ParityInputError(f"{owner} requires string-to-string object {key!r}")
    return dict(candidate)


def _named(items: Sequence[Any], key: str, owner: str) -> dict[str, dict[str, Any]]:
    result: dict[str, dict[str, Any]] = {}
    for index, item in enumerate(items):
        if not isinstance(item, dict):
            raise ParityInputError(f"{owner}[{index}] must be an object")
        name = _required_string(item, key, f"{owner}[{index}]")
        if name in result:
            raise ParityInputError(f"{owner} contains duplicate {key} {name!r}")
        result[name] = item
    return result


def _normalized(text: str) -> str:
    return " ".join(text.split())


def _policy_instructions(compiled, refs: Iterable[Any]) -> list[str]:
    return [compiled.agent_policies[ref.id].instruction for ref in refs]


def _compare_text(
    failures: list[str], label: str, expected: str, actual: str | None
) -> None:
    if actual is None:
        failures.append(f"{label}: implementation value is missing")
    elif _normalized(expected) != _normalized(actual):
        failures.append(f"{label}: implementation text differs from Studio text")


def _compare_policies(
    failures: list[str], label: str, expected: Sequence[Any], actual: Sequence[str]
) -> None:
    if any(not isinstance(item, str) for item in expected):
        raise ParityInputError(f"{label}: Studio policies must be strings")
    expected_counter = Counter(_normalized(item) for item in expected)
    actual_counter = Counter(_normalized(item) for item in actual)
    for instruction, count in (expected_counter - actual_counter).items():
        failures.append(
            f"{label}: missing {count} policy activation(s): {instruction!r}"
        )
    for instruction, count in (actual_counter - expected_counter).items():
        failures.append(
            f"{label}: has {count} undesigned policy activation(s): {instruction!r}"
        )


def _compare_ids(
    failures: list[str], label: str, expected: Iterable[str], actual: Iterable[str]
) -> None:
    expected_set = set(expected)
    actual_set = set(actual)
    missing = sorted(expected_set - actual_set)
    extra = sorted(actual_set - expected_set)
    if missing:
        failures.append(f"{label}: missing mapped objects: {', '.join(missing)}")
    if extra:
        failures.append(f"{label}: contains objects absent from Studio mapping: {', '.join(extra)}")


def _require_compiled_object(
    failures: list[str], catalog: Mapping[str, Any], identifier: str, label: str
) -> Any | None:
    value = catalog.get(identifier)
    if value is None:
        failures.append(f"{label}: mapped RouteDeck object {identifier!r} is missing")
    return value


def check_parity(
    design_state: Mapping[str, Any], manifest: Mapping[str, Any], compiled
) -> list[str]:
    failures: list[str] = []
    if manifest.get("version") != 1:
        raise ParityInputError("Manifest version must be 1")

    design_features = _named(
        _required_list(design_state, "features", "design state"),
        "name",
        "design features",
    )
    manifest_features = _required_list(manifest, "features", "manifest")
    mapped_namespaces: set[str] = set()

    for feature_index, raw_feature_mapping in enumerate(manifest_features):
        owner = f"manifest.features[{feature_index}]"
        if not isinstance(raw_feature_mapping, dict):
            raise ParityInputError(f"{owner} must be an object")
        design_name = _required_string(raw_feature_mapping, "designFeature", owner)
        namespace = _required_string(raw_feature_mapping, "routeDeckFeature", owner)
        if namespace in mapped_namespaces:
            raise ParityInputError(
                f"Manifest maps RouteDeck feature {namespace!r} more than once"
            )
        mapped_namespaces.add(namespace)

        design_feature = design_features.get(design_name)
        if design_feature is None:
            failures.append(f"Feature {design_name!r}: missing from Design Studio state")
            continue
        compiled_features = [
            feature
            for feature in compiled.application.features
            if feature.namespace == namespace
        ]
        if len(compiled_features) != 1:
            failures.append(
                f"Feature {design_name!r}: expected one compiled RouteDeck feature "
                f"{namespace!r}, found {len(compiled_features)}"
            )
            continue
        compiled_feature = compiled_features[0]
        feature_label = f"Feature {design_name!r}"

        _compare_text(
            failures,
            f"{feature_label} prompt",
            _required_string(design_feature, "prompt", feature_label),
            compiled_feature.agent_prompt,
        )
        _compare_policies(
            failures,
            f"{feature_label} policies",
            _required_list(design_feature, "policies", feature_label),
            _policy_instructions(compiled, compiled_feature.policy_refs),
        )

        design_behaviors = _named(
            _required_list(design_feature, "stories", feature_label),
            "title",
            f"{feature_label} behaviors",
        )
        behavior_mappings = _named(
            _required_list(raw_feature_mapping, "behaviors", owner),
            "designBehavior",
            f"{owner}.behaviors",
        )
        _compare_ids(
            failures,
            f"{feature_label} behavior mapping",
            design_behaviors,
            behavior_mappings,
        )

        mapped_node_ids = [
            _required_string(mapping, "node", f"{feature_label} behavior mapping")
            for mapping in behavior_mappings.values()
        ]
        duplicate_nodes = sorted(
            node_id for node_id, count in Counter(mapped_node_ids).items() if count > 1
        )
        if duplicate_nodes:
            failures.append(
                f"{feature_label}: multiple Studio behaviors map to the same Node: "
                + ", ".join(duplicate_nodes)
            )
        _compare_ids(
            failures,
            f"{feature_label} Nodes",
            mapped_node_ids,
            (node.id for node in compiled_feature.nodes),
        )

        for behavior_name, behavior_mapping in behavior_mappings.items():
            design_behavior = design_behaviors.get(behavior_name)
            if design_behavior is None:
                continue
            behavior_label = f"{feature_label} / Behavior {behavior_name!r}"
            node_id = _required_string(behavior_mapping, "node", behavior_label)
            node = compiled.nodes.get(node_id)
            if node is None:
                failures.append(f"{behavior_label}: mapped Node {node_id!r} is missing")
                continue
            if node not in compiled_feature.nodes:
                failures.append(
                    f"{behavior_label}: Node {node_id!r} belongs to another feature"
                )
                continue

            _compare_policies(
                failures,
                f"{behavior_label} Node policies",
                _required_list(design_behavior, "nodePolicies", behavior_label),
                _policy_instructions(compiled, node.policy_refs),
            )

            design_capabilities = _named(
                _required_list(design_behavior, "capabilities", behavior_label),
                "name",
                f"{behavior_label} capabilities",
            )
            design_surfaces = _named(
                _required_list(design_behavior, "surfaces", behavior_label),
                "name",
                f"{behavior_label} surfaces",
            )
            design_operations = _named(
                _required_list(design_behavior, "operations", behavior_label),
                "name",
                f"{behavior_label} operations",
            )
            capability_mapping = _required_mapping(
                behavior_mapping, "capabilities", behavior_label
            )
            surface_mapping = _required_mapping(
                behavior_mapping, "surfaces", behavior_label
            )
            operation_mapping = _required_mapping(
                behavior_mapping, "operations", behavior_label
            )
            _compare_ids(
                failures,
                f"{behavior_label} Capability mapping",
                design_capabilities,
                capability_mapping,
            )
            _compare_ids(
                failures,
                f"{behavior_label} Surface mapping",
                design_surfaces,
                surface_mapping,
            )
            _compare_ids(
                failures,
                f"{behavior_label} Operation mapping",
                design_operations,
                operation_mapping,
            )
            _compare_ids(
                failures,
                f"{behavior_label} Node Capabilities",
                capability_mapping.values(),
                (capability.id for capability in node.capabilities),
            )
            _compare_ids(
                failures,
                f"{behavior_label} Node Surfaces",
                surface_mapping.values(),
                (surface.id for surface in node.surfaces.declared_surfaces()),
            )
            _compare_ids(
                failures,
                f"{behavior_label} Node Operations",
                operation_mapping.values(),
                (operation.id for operation in node.operations),
            )

            compiled_capabilities = {item.id: item for item in node.capabilities}
            for design_capability_name, capability_id in capability_mapping.items():
                design_capability = design_capabilities.get(design_capability_name)
                if design_capability is None:
                    continue
                capability = _require_compiled_object(
                    failures,
                    compiled_capabilities,
                    capability_id,
                    f"{behavior_label} / Capability {design_capability_name!r}",
                )
                if capability is None:
                    continue
                capability_label = (
                    f"{behavior_label} / Capability {design_capability_name!r}"
                )
                _compare_policies(
                    failures,
                    f"{capability_label} policies",
                    _required_list(design_capability, "policies", capability_label),
                    _policy_instructions(compiled, capability.policy_refs),
                )
                expected_operation_ids: list[str] = []
                for name in _required_list(
                    design_capability, "operationNames", capability_label
                ):
                    if not isinstance(name, str) or name not in operation_mapping:
                        failures.append(
                            f"{capability_label}: references unmapped Studio "
                            f"Operation {name!r}"
                        )
                    else:
                        expected_operation_ids.append(operation_mapping[name])
                expected_surface_ids: list[str] = []
                for name in _required_list(
                    design_capability, "surfaceNames", capability_label
                ):
                    if not isinstance(name, str) or name not in surface_mapping:
                        failures.append(
                            f"{capability_label}: references unmapped Studio "
                            f"Surface {name!r}"
                        )
                    else:
                        expected_surface_ids.append(surface_mapping[name])
                _compare_ids(
                    failures,
                    f"{capability_label} Operations",
                    expected_operation_ids,
                    (ref.id for ref in capability.operations),
                )
                _compare_ids(
                    failures,
                    f"{capability_label} Surfaces",
                    expected_surface_ids,
                    (ref.id for ref in capability.surfaces),
                )

            for design_surface_name, surface_id in surface_mapping.items():
                design_surface = design_surfaces.get(design_surface_name)
                if design_surface is None:
                    continue
                surface = _require_compiled_object(
                    failures,
                    compiled.surfaces,
                    surface_id,
                    f"{behavior_label} / Surface {design_surface_name!r}",
                )
                if surface is not None:
                    surface_label = f"{behavior_label} / Surface {design_surface_name!r}"
                    _compare_policies(
                        failures,
                        f"{surface_label} policies",
                        _required_list(design_surface, "policies", surface_label),
                        _policy_instructions(compiled, surface.policy_refs),
                    )

            for design_operation_name, operation_id in operation_mapping.items():
                design_operation = design_operations.get(design_operation_name)
                if design_operation is None:
                    continue
                operation = _require_compiled_object(
                    failures,
                    compiled.operations,
                    operation_id,
                    f"{behavior_label} / Operation {design_operation_name!r}",
                )
                if operation is not None:
                    operation_label = (
                        f"{behavior_label} / Operation {design_operation_name!r}"
                    )
                    _compare_policies(
                        failures,
                        f"{operation_label} policies",
                        _required_list(design_operation, "policies", operation_label),
                        _policy_instructions(compiled, operation.policy_refs),
                    )

            expected_actions: Counter[tuple[str, str]] = Counter()
            for raw_action in _required_list(
                design_behavior, "suggestedActions", behavior_label
            ):
                if not isinstance(raw_action, dict):
                    raise ParityInputError(
                        f"{behavior_label} Suggested Actions must be objects"
                    )
                label = _required_string(raw_action, "label", behavior_label)
                operation_name = _required_string(
                    raw_action, "operationName", behavior_label
                )
                operation_id = operation_mapping.get(operation_name)
                if operation_id is None:
                    failures.append(
                        f"{behavior_label} / Suggested Action {label!r}: "
                        f"Operation {operation_name!r} has no manifest mapping"
                    )
                    continue
                expected_actions[(label, operation_id)] += 1
            actual_actions = Counter(
                (action.label, action.operation_id) for action in node.suggested_actions
            )
            for action, count in (expected_actions - actual_actions).items():
                failures.append(
                    f"{behavior_label}: missing {count} Suggested Action(s) "
                    f"{action[0]!r} -> {action[1]!r}"
                )
            for action, count in (actual_actions - expected_actions).items():
                failures.append(
                    f"{behavior_label}: has {count} undesigned Suggested Action(s) "
                    f"{action[0]!r} -> {action[1]!r}"
                )

    compiled_namespaces = {
        feature.namespace for feature in compiled.application.features
    }
    missing_feature_mappings = sorted(compiled_namespaces - mapped_namespaces)
    if missing_feature_mappings:
        failures.append(
            "Compiled RouteDeck features missing implementation-manifest mappings: "
            + ", ".join(missing_feature_mappings)
        )
    unknown_feature_mappings = sorted(mapped_namespaces - compiled_namespaces)
    if unknown_feature_mappings:
        failures.append(
            "Implementation manifest maps uncompiled RouteDeck features: "
            + ", ".join(unknown_feature_mappings)
        )
    return failures


def _failure_group_key(failure: str) -> str:
    if "policy activation(s)" in failure:
        return "policy"
    if failure.startswith("Compiled RouteDeck features missing") or failure.startswith(
        "Implementation manifest maps uncompiled"
    ):
        return "feature_coverage"
    if "missing from Design Studio state" in failure or (
        "expected one compiled RouteDeck feature" in failure
    ):
        return "feature_coverage"
    if "multiple Studio behaviors map to the same Node" in failure or (
        "belongs to another feature" in failure
    ):
        return "behavior_node"
    if " prompt: implementation" in failure:
        return "prompt"
    if "mapped RouteDeck object" in failure and "is missing" in failure:
        return "missing_target"
    if ": mapped Node " in failure and failure.endswith(" is missing"):
        return "missing_target"
    if "missing mapped objects:" in failure:
        return "missing_membership"
    if "contains objects absent from Studio mapping:" in failure:
        return "extra_shape"
    if "Suggested Action" in failure or "SuggestedAction" in failure:
        return "suggested_action"
    if "references unmapped Studio" in failure or "has no manifest mapping" in failure:
        return "mapping_integrity"
    return "other"


def group_failures(failures: Sequence[str]) -> list[tuple[FailureGroup, list[str]]]:
    """Group exhaustive mismatch evidence into stable, actionable CLI categories."""

    grouped: dict[str, list[str]] = {group.key: [] for group in FAILURE_GROUPS}
    for failure in failures:
        grouped[_failure_group_key(failure)].append(failure)
    return [(group, grouped[group.key]) for group in FAILURE_GROUPS if grouped[group.key]]


def _policy_activation_count(failures: Sequence[str], kind: str) -> int:
    pattern = (
        re.compile(r"missing (\d+) policy activation\(s\)")
        if kind == "missing"
        else re.compile(r"(\d+) undesigned policy activation\(s\)")
    )
    return sum(
        int(match.group(1))
        for failure in failures
        if (match := pattern.search(failure)) is not None
    )


def format_failure_report(failures: Sequence[str], *, verbose: bool) -> list[str]:
    """Format a concise diagnosis, with exhaustive evidence only when requested."""

    lines = [f"Mismatches: {len(failures)}", "Mismatch groups:"]
    for group, grouped_failures in group_failures(failures):
        detail = ""
        if group.key == "policy":
            missing = _policy_activation_count(grouped_failures, "missing")
            undesigned = _policy_activation_count(grouped_failures, "undesigned")
            detail = (
                f" ({missing} designed activations missing; "
                f"{undesigned} compiled activations undesigned)"
            )
        lines.append(f"- {group.title}: {len(grouped_failures)}{detail}")

    if verbose:
        lines.append("Mismatch details:")
        lines.extend(f"- {failure}" for failure in failures)
    else:
        lines.append(
            f"Run again with --verbose to print all {len(failures)} mismatch details."
        )
    return lines


def _compiled_corpus_app():
    if str(BACKEND_SOURCE) not in sys.path:
        sys.path.insert(0, str(BACKEND_SOURCE))
    from corpus.composition import compile_corpus_app

    return compile_corpus_app()


def _arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Check Design Studio product shape and policy scopes against the "
            "compiled Corpus RouteDeck application."
        )
    )
    parser.add_argument("--design-state", type=Path, default=DEFAULT_DESIGN_STATE)
    parser.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST)
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Print every mismatch after the grouped summary.",
    )
    return parser.parse_args()


def main() -> int:
    arguments = _arguments()
    try:
        failures = check_parity(
            _load_object(arguments.design_state),
            _load_object(arguments.manifest),
            _compiled_corpus_app(),
        )
    except ParityInputError as error:
        print(f"Agent design parity input failed: {error}", file=sys.stderr)
        return 2

    if failures:
        print("Corpus Agent Design Studio parity failed")
        print(f"Design state: {arguments.design_state}")
        print(f"Implementation manifest: {arguments.manifest}")
        for line in format_failure_report(failures, verbose=arguments.verbose):
            print(line)
        return 1

    print("Corpus Agent Design Studio parity passed")
    print(f"Design state: {arguments.design_state}")
    print(f"Implementation manifest: {arguments.manifest}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
