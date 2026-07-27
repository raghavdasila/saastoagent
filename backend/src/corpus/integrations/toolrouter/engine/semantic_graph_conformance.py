from __future__ import annotations

from collections import Counter, defaultdict
from typing import Any

from .openapi_loader import NormalizedBundle
from .semantic_graph import EDGE_STATUSES, SemanticGraph


CONFORMANCE_VERSION = 1
STAGE_ORDER = ("ingest", "reconcile", "consolidate", "connect", "retrieve")


def _issue(code: str, message: str, *, stage: str, count: int = 1) -> dict[str, Any]:
    return {
        "code": code,
        "message": message,
        "stage": stage,
        "count": int(count),
    }


def _stage(
    metrics: dict[str, Any],
    *,
    violations: list[dict[str, Any]],
    warnings: list[dict[str, Any]],
    stage_name: str,
) -> dict[str, Any]:
    stage_violations = [value for value in violations if value["stage"] == stage_name]
    stage_warnings = [value for value in warnings if value["stage"] == stage_name]
    status = "fail" if stage_violations else ("warning" if stage_warnings else "pass")
    return {
        "status": status,
        "metrics": metrics,
        "violations": stage_violations,
        "warnings": stage_warnings,
    }


def build_semantic_graph_conformance_report(
    bundle: NormalizedBundle,
    graph: SemanticGraph,
) -> dict[str, Any]:
    """Check the active graph one construction stage at a time.

    Structural contract violations fail the report. Explicitly retained source
    limitations, such as unresolved references or ambiguous equal shapes, are
    warnings so the graph remains inspectable without presenting the warning as
    a successful evidence path.
    """

    violations: list[dict[str, Any]] = []
    warnings: list[dict[str, Any]] = []
    metadata = graph.metadata or {}
    schema_analysis = metadata.get("schema_analysis") or {}

    if not bundle.endpoints:
        violations.append(_issue("no_endpoints", "The normalized bundle contains no endpoints.", stage="ingest"))
    manifest_endpoint_count = bundle.manifest.get("endpoint_count")
    if manifest_endpoint_count is not None and int(manifest_endpoint_count) != len(bundle.endpoints):
        violations.append(
            _issue(
                "manifest_endpoint_mismatch",
                "The loader manifest endpoint count does not match the normalized bundle.",
                stage="ingest",
            )
        )

    source_names = sorted({endpoint.source for endpoint in bundle.endpoints if endpoint.source})
    spec_summaries = bundle.manifest.get("specs", []) if isinstance(bundle.manifest, dict) else []
    validation_warning_count = sum(
        1
        for value in spec_summaries
        if isinstance(value, dict)
        and isinstance(value.get("spec_validation"), dict)
        and value["spec_validation"].get("ok") is False
    )
    if validation_warning_count:
        warnings.append(
            _issue(
                "source_validation_warnings",
                "One or more source specifications reported validation diagnostics.",
                stage="ingest",
                count=validation_warning_count,
            )
        )

    unresolved_relations = int(schema_analysis.get("unresolved_relations", 0))
    schema_warning_count = len(metadata.get("schema_warnings") or [])
    if unresolved_relations:
        warnings.append(
            _issue(
                "unresolved_schema_relations",
                "Some schema relationships could not be resolved and were retained as warnings.",
                stage="reconcile",
                count=unresolved_relations,
            )
        )
    if schema_warning_count:
        warnings.append(
            _issue(
                "schema_identity_warnings",
                "Canonical schema analysis retained identity or reference warnings.",
                stage="reconcile",
                count=schema_warning_count,
            )
        )

    if metadata.get("assembler") != "resource_first_v1":
        violations.append(
            _issue(
                "wrong_assembler",
                "The active conformance gate requires resource_first_v1.",
                stage="consolidate",
            )
        )
    api_field_count = sum(node.node_type == "api_field" for node in graph.nodes)
    if api_field_count:
        violations.append(
            _issue(
                "global_api_field_nodes",
                "The active resource-first graph must not materialize api_field nodes.",
                stage="consolidate",
                count=api_field_count,
            )
        )
    unreachable_ids = metadata.get("unreachable_component_ids") or []
    expected_unreachable = int(schema_analysis.get("unreachable_component_schemas", len(unreachable_ids)))
    if len(unreachable_ids) != expected_unreachable:
        violations.append(
            _issue(
                "unreachable_inventory_mismatch",
                "The explicit unreachable-component inventory does not match schema analysis.",
                stage="consolidate",
            )
        )
    ambiguous_shape_count = len(metadata.get("ambiguous_equal_shape_groups") or [])
    if ambiguous_shape_count:
        warnings.append(
            _issue(
                "ambiguous_equal_shapes",
                "Structurally equal cross-stem schemas remain unmerged pending explicit identity evidence.",
                stage="consolidate",
                count=ambiguous_shape_count,
            )
        )

    node_ids = [node.id for node in graph.nodes]
    duplicate_node_ids = sum(count - 1 for count in Counter(node_ids).values() if count > 1)
    if duplicate_node_ids:
        violations.append(
            _issue(
                "duplicate_node_ids",
                "Graph node identifiers are not unique.",
                stage="connect",
                count=duplicate_node_ids,
            )
        )
    node_id_set = set(node_ids)
    dangling_edges = [edge for edge in graph.edges if edge.source not in node_id_set or edge.target not in node_id_set]
    if dangling_edges:
        violations.append(
            _issue(
                "dangling_edges",
                "One or more edges refer to missing graph nodes.",
                stage="connect",
                count=len(dangling_edges),
            )
        )
    invalid_status_edges = [edge for edge in graph.edges if edge.status not in EDGE_STATUSES]
    if invalid_status_edges:
        violations.append(
            _issue(
                "invalid_edge_status",
                "One or more edges use an unknown evidence status.",
                stage="connect",
                count=len(invalid_status_edges),
            )
        )
    invalid_confidence_edges = [edge for edge in graph.edges if not 0.0 < float(edge.confidence) <= 1.0]
    if invalid_confidence_edges:
        violations.append(
            _issue(
                "invalid_edge_confidence",
                "One or more edges have confidence outside (0, 1].",
                stage="connect",
                count=len(invalid_confidence_edges),
            )
        )
    missing_edge_evidence = [edge for edge in graph.edges if not edge.evidence]
    if missing_edge_evidence:
        violations.append(
            _issue(
                "missing_edge_evidence",
                "Every relationship must retain source evidence.",
                stage="connect",
                count=len(missing_edge_evidence),
            )
        )
    missing_node_evidence = [node for node in graph.nodes if not node.evidence]
    if missing_node_evidence:
        violations.append(
            _issue(
                "missing_node_evidence",
                "Every materialized graph node must retain source evidence.",
                stage="connect",
                count=len(missing_node_evidence),
            )
        )

    nodes_by_endpoint_and_type: dict[tuple[str, str], int] = defaultdict(int)
    operation_nodes_by_endpoint: dict[str, list[Any]] = defaultdict(list)
    for node in graph.nodes:
        if node.endpoint_id:
            nodes_by_endpoint_and_type[(node.endpoint_id, node.node_type)] += 1
            if node.node_type == "api_operation":
                operation_nodes_by_endpoint[node.endpoint_id].append(node)
    required_input_descriptor_count = 0
    endpoints_with_required_inputs = 0
    for endpoint in bundle.endpoints:
        for node_type in ("api_operation", "action", "doc_chunk"):
            count = nodes_by_endpoint_and_type[(endpoint.id, node_type)]
            if count != 1:
                violations.append(
                    _issue(
                        "endpoint_neighborhood_incomplete",
                        f"Endpoint {endpoint.id} has {count} {node_type} nodes; expected exactly one.",
                        stage="connect",
                    )
                )
        operation_nodes = operation_nodes_by_endpoint.get(endpoint.id, [])
        if len(operation_nodes) != 1:
            continue
        required_inputs = operation_nodes[0].facets.get("required_inputs")
        if not isinstance(required_inputs, list):
            violations.append(
                _issue(
                    "required_input_contract_missing",
                    f"Endpoint {endpoint.id} has no structured required-input descriptor list.",
                    stage="connect",
                )
            )
            continue
        malformed_inputs = [
            value
            for value in required_inputs
            if not isinstance(value, dict)
            or not value.get("name")
            or not value.get("location")
            or not value.get("json_pointer")
        ]
        if malformed_inputs:
            violations.append(
                _issue(
                    "required_input_descriptor_malformed",
                    f"Endpoint {endpoint.id} has malformed required-input descriptors.",
                    stage="connect",
                    count=len(malformed_inputs),
                )
            )
        explicit_required = {
            (str(parameter.location).casefold(), str(parameter.name).casefold())
            for parameter in endpoint.params
            if parameter.required
        }
        described_required = {
            (str(value.get("location")).casefold(), str(value.get("name")).casefold())
            for value in required_inputs
            if isinstance(value, dict)
        }
        missing_explicit = explicit_required - described_required
        if missing_explicit:
            violations.append(
                _issue(
                    "required_openapi_parameter_missing",
                    f"Endpoint {endpoint.id} is missing explicit required OpenAPI parameter evidence.",
                    stage="connect",
                    count=len(missing_explicit),
                )
            )
        required_input_descriptor_count += len(required_inputs)
        endpoints_with_required_inputs += int(bool(required_inputs))

    resource_inference_ambiguities = len(metadata.get("resource_inference_ambiguities") or [])
    if resource_inference_ambiguities:
        warnings.append(
            _issue(
                "resource_identity_ambiguities",
                "Some endpoint resources could not be connected to one canonical schema without guessing.",
                stage="connect",
                count=resource_inference_ambiguities,
            )
        )

    card_ids = [card.card_id for card in graph.cards]
    duplicate_card_ids = sum(count - 1 for count in Counter(card_ids).values() if count > 1)
    if duplicate_card_ids:
        violations.append(
            _issue(
                "duplicate_card_ids",
                "Semantic node card identifiers are not unique.",
                stage="retrieve",
                count=duplicate_card_ids,
            )
        )
    card_node_ids = [card.node_id for card in graph.cards]
    duplicate_card_nodes = sum(count - 1 for count in Counter(card_node_ids).values() if count > 1)
    if duplicate_card_nodes:
        violations.append(
            _issue(
                "duplicate_cards_per_node",
                "More than one retrieval card exists for a graph node.",
                stage="retrieve",
                count=duplicate_card_nodes,
            )
        )
    missing_card_nodes = sorted(node_id_set - set(card_node_ids))
    unknown_card_nodes = sorted(set(card_node_ids) - node_id_set)
    if missing_card_nodes or unknown_card_nodes:
        violations.append(
            _issue(
                "card_node_bijection_failed",
                "Semantic node cards must have a one-to-one relationship with graph nodes.",
                stage="retrieve",
                count=len(missing_card_nodes) + len(unknown_card_nodes),
            )
        )
    cards_without_evidence = [card for card in graph.cards if not card.evidence]
    if cards_without_evidence:
        violations.append(
            _issue(
                "card_provenance_missing",
                "Every retrieval card must retain its node provenance.",
                stage="retrieve",
                count=len(cards_without_evidence),
            )
        )

    stage_metrics = {
        "ingest": {
            "source_count": len(source_names),
            "endpoint_count": len(bundle.endpoints),
            "schema_entry_count": len(bundle.schemas),
            "security_scheme_count": len(bundle.security_schemes),
            "source_validation_warning_count": validation_warning_count,
        },
        "reconcile": {
            "canonical_component_schema_count": int(schema_analysis.get("canonical_component_schemas", 0)),
            "collapsed_alias_entry_count": int(schema_analysis.get("collapsed_alias_entries", 0)),
            "resolved_relation_count": int(schema_analysis.get("resolved_relations", 0)),
            "unresolved_relation_count": unresolved_relations,
            "schema_warning_count": schema_warning_count,
        },
        "consolidate": {
            "materialized_node_count": len(graph.nodes),
            "api_field_node_count": api_field_count,
            "unreachable_component_count": len(unreachable_ids),
            "ambiguous_equal_shape_group_count": ambiguous_shape_count,
        },
        "connect": {
            "edge_count": len(graph.edges),
            "dangling_edge_count": len(dangling_edges),
            "invalid_edge_status_count": len(invalid_status_edges),
            "missing_edge_evidence_count": len(missing_edge_evidence),
            "missing_node_evidence_count": len(missing_node_evidence),
            "resource_identity_ambiguity_count": resource_inference_ambiguities,
            "required_input_descriptor_count": required_input_descriptor_count,
            "endpoints_with_required_inputs": endpoints_with_required_inputs,
        },
        "retrieve": {
            "card_count": len(graph.cards),
            "node_count": len(graph.nodes),
            "missing_card_node_count": len(missing_card_nodes),
            "unknown_card_node_count": len(unknown_card_nodes),
            "cards_without_evidence_count": len(cards_without_evidence),
        },
    }
    stages = {
        stage_name: _stage(
            stage_metrics[stage_name],
            violations=violations,
            warnings=warnings,
            stage_name=stage_name,
        )
        for stage_name in STAGE_ORDER
    }
    return {
        "version": CONFORMANCE_VERSION,
        "assembler": metadata.get("assembler"),
        "valid": not violations,
        "stage_order": list(STAGE_ORDER),
        "stages": stages,
        "violation_count": len(violations),
        "warning_count": len(warnings),
        "violations": violations,
        "warnings": warnings,
    }


def assert_semantic_graph_conformance(report: dict[str, Any]) -> None:
    if report.get("valid"):
        return
    details = "\n".join(
        f"- {value.get('stage')}:{value.get('code')}: {value.get('message')}"
        for value in report.get("violations", [])
    )
    raise ValueError(f"Semantic graph construction conformance failed:\n{details}")
