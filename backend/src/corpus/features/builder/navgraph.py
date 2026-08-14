from __future__ import annotations

import copy
import hashlib
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Mapping

from routedeck_core.app import Application, CompiledApplication, Feature, compile_app
from routedeck_core.contracts.agent import AgentPolicy
from routedeck_core.contracts.application import Capability, Node
from routedeck_core.contracts.navigation import DeepLinkPolicy, NodeKind, NodeRef, RecoveryPolicy, Route, Transition
from routedeck_core.contracts.operations import Operation, OperationSource, ReviewPolicy, SafetyClass
from routedeck_core.contracts.projection import FrozenJsonObject
from routedeck_core.contracts.suggestions import SuggestedAction
from routedeck_core.contracts.surfaces import Surface, SurfaceAffordance, SurfaceLifecycle, SurfaceSlots

from corpus.features.designer.contracts import DesignContent, compile_design_topology

from .domain import BuilderInputSnapshot, BuilderSourceBinding
from .ports import BuilderConflict, BuilderUnavailable


_READ_METHODS = frozenset({"get", "head", "options"})
_HTTP_METHODS = _READ_METHODS | frozenset({"post", "put", "patch", "delete"})
_EMPTY_SCHEMA = {"type": "object", "properties": {}, "additionalProperties": False}
_OBSERVED_SCHEMA = {
    "type": "object",
    "properties": {
        "operation_id": {"type": "string", "minLength": 1},
        "status": {"type": "string", "const": "succeeded"},
        "http_status": {"type": ["integer", "null"]},
        "outcome_verified": {"type": "boolean"},
    },
    "required": ["operation_id", "status", "http_status", "outcome_verified"],
    "additionalProperties": False,
}
_UNKNOWN_WRITE_RECOVERY = "Do not retry automatically. Inspect the retained delivery state and prepare a new reviewed action."
_CLARIFICATION_SCHEMA = {
    "type": "object",
    "properties": {
        "state": {"type": "string", "enum": ["idle", "needs_input", "needs_operation_choice"]},
        "question": {"type": "string"},
        "candidate_operation_ids": {"type": "array", "items": {"type": "string"}},
        "missing_input_names": {"type": "array", "items": {"type": "string"}},
    },
    "additionalProperties": False,
}
_TOOLROUTER_STATUS_SCHEMA = {
    "type": "object",
    "properties": {
        "state": {"type": "string", "enum": ["idle", "routing", "waiting", "completed", "failed"]},
        "event_count": {"type": "integer", "minimum": 0},
        "last_resolution": {"type": "string"},
    },
    "additionalProperties": False,
}
_WRITE_REVIEW_SCHEMA = {
    "type": "object",
    "properties": {
        "state": {"type": "string", "enum": ["pending"]},
        "review_id": {"type": "string", "minLength": 1},
        "expires_at": {"type": "string", "minLength": 1},
    },
    "additionalProperties": False,
}


@dataclass(frozen=True)
class AgentNavGraphArtifact:
    navgraph_hash: str
    compiled_navgraph: dict[str, object]
    frontend_contract: dict[str, object]


def compile_agent_navgraph(snapshot: BuilderInputSnapshot) -> AgentNavGraphArtifact:
    topology = compile_design_topology(DesignContent(
        goal=snapshot.goal,
        instructions=snapshot.instructions,
        features=snapshot.features,
        behaviors=snapshot.behaviors,
        policies=snapshot.policies,
        capabilities=snapshot.capabilities,
        tools=snapshot.tools,
        runtime_areas=snapshot.runtime_areas,
    ))
    declarations = tuple(
        _operation_declaration(binding, operation_id)
        for binding in snapshot.source_bindings
        for operation_id in binding.included_operation_ids
    )
    if not declarations:
        raise BuilderUnavailable("The accepted design has no operations to compile.")
    if {item[0] for item in declarations} != set(snapshot.tools):
        raise BuilderConflict("The accepted Designer tools do not match the exact Source curation.")

    home_ref = NodeRef(id=topology.entry_node_id)
    error_surface = Surface(
        id="agent_runtime.delivery_status",
        component="agent_runtime.delivery_status",
        lifecycle=SurfaceLifecycle.STABLE,
        public_props_schema=FrozenJsonObject(_EMPTY_SCHEMA),
    )
    clarification_surface = Surface(
        id="agent_runtime.clarification",
        component="agent_runtime.clarification",
        lifecycle=SurfaceLifecycle.STABLE,
        public_props_schema=FrozenJsonObject(_CLARIFICATION_SCHEMA),
    )
    router_status_surface = Surface(
        id="agent_runtime.toolrouter_status",
        component="agent_runtime.toolrouter_status",
        lifecycle=SurfaceLifecycle.STABLE,
        public_props_schema=FrozenJsonObject(_TOOLROUTER_STATUS_SCHEMA),
    )
    write_review_surface = Surface(
        id="agent_runtime.write_review",
        component="agent_runtime.write_review",
        lifecycle=SurfaceLifecycle.STABLE,
        public_props_schema=FrozenJsonObject(_WRITE_REVIEW_SCHEMA),
    )
    policies = _policies(snapshot)
    metadata = FrozenJsonObject({
        "accepted_design": {
            "design_revision_id": str(snapshot.design_revision_id),
            "goal": snapshot.goal,
            "instructions": snapshot.instructions,
            "features": list(snapshot.features),
            "behaviors": list(snapshot.behaviors),
            "policies": list(snapshot.policies),
            "capabilities": list(snapshot.capabilities),
            "tools": list(snapshot.tools),
            "runtime_areas": [dict(item) for item in snapshot.runtime_areas],
        },
        "designer_topology": topology.model_dump(mode="json"),
    })
    operation_by_source_id = {
        source_operation_id: operation
        for source_operation_id, operation in declarations
    }
    navigation_operations = _navigation_operations(topology)
    operation_by_topology_id = {
        **operation_by_source_id,
        **{operation.id: operation for operation in navigation_operations},
    }
    active_surfaces = {
        node.id: Surface(
            id=node.surface_ids[0],
            component="agent_runtime.home",
            lifecycle=SurfaceLifecycle.STABLE,
            affordances=tuple(
                SurfaceAffordance(
                    id=f"action-{_identity(operation_id)}",
                    event="submit",
                    operation=operation_by_topology_id[operation_id].ref,
                )
                for operation_id in (*node.navigation_operation_ids, *node.operation_ids)
            ),
            public_props_schema=FrozenJsonObject(_EMPTY_SCHEMA),
        )
        for node in topology.nodes
    }
    capability_by_id = {item.id: item for item in topology.capabilities}
    nodes = tuple(
        _node(
            topology_node=topology_node,
            topology=topology,
            operation_by_topology_id=operation_by_topology_id,
            capability_by_id=capability_by_id,
            active_surface=active_surfaces[topology_node.id],
            clarification_surface=clarification_surface,
            router_status_surface=router_status_surface,
            write_review_surface=write_review_surface,
            error_surface=error_surface,
            policies=policies,
            metadata=metadata,
        )
        for topology_node in topology.nodes
    )
    compiled = compile_app(Application(
        name=f"corpus-agent-{snapshot.build_id}",
        entry_node=home_ref,
        features=(Feature(namespace="agent_runtime", nodes=nodes, agent_policies=policies),),
    ))
    documents = compiled.contract_documents()
    navgraph = _stable(json.loads(documents["compiled-navgraph.json"]))
    frontend = _stable(json.loads(documents["frontend-contract.json"]))
    navgraph_bytes = json.dumps(navgraph, ensure_ascii=False, separators=(",", ":"), sort_keys=True).encode("utf-8")
    return AgentNavGraphArtifact(
        navgraph_hash=hashlib.sha256(navgraph_bytes).hexdigest(),
        compiled_navgraph=navgraph,
        frontend_contract=frontend,
    )


def load_agent_navgraph(navgraph_hash: str, compiled_navgraph: Mapping[str, object]) -> CompiledApplication:
    raw_nodes = compiled_navgraph.get("nodes")
    entry = compiled_navgraph.get("entry_node")
    name = compiled_navgraph.get("name")
    if not isinstance(raw_nodes, list) or not isinstance(entry, Mapping) or not isinstance(name, str):
        raise BuilderUnavailable("The immutable RouteDeck NavGraph is invalid.")
    try:
        nodes = _canonical_contract_nodes(raw_nodes)
    except (TypeError, ValueError) as error:
        raise BuilderUnavailable("The immutable RouteDeck NavGraph cannot be reconstructed.") from error
    entry_id = NodeRef.model_validate(entry).id
    entry_nodes = tuple(node for node in nodes if node.id == entry_id)
    if len(entry_nodes) != 1:
        raise BuilderUnavailable("The immutable RouteDeck NavGraph entry area is unavailable.")
    accepted = entry_nodes[0].public_metadata_value().get("accepted_design")
    if not isinstance(accepted, Mapping):
        raise BuilderUnavailable("The compiled Agent design identity is unavailable.")
    instructions = accepted.get("instructions")
    raw_policies = accepted.get("policies")
    if not isinstance(instructions, str) or not isinstance(raw_policies, list) or any(not isinstance(item, str) for item in raw_policies):
        raise BuilderUnavailable("The compiled Agent policy set is unavailable.")
    policies = tuple(
        AgentPolicy(id=f"agent_runtime.policy.{index}", instruction=value)
        for index, value in enumerate(tuple(dict.fromkeys((instructions, *raw_policies))), start=1)
        if value.strip()
    )
    compiled = compile_app(Application(
        name=name,
        entry_node=NodeRef(id=entry_id),
        features=(Feature(namespace="agent_runtime", nodes=nodes, agent_policies=policies),),
    ))
    if _compiled_navgraph_hash(compiled) != navgraph_hash:
        raise BuilderConflict("The immutable RouteDeck NavGraph hash does not match its contract.")
    return compiled


def _policies(snapshot: BuilderInputSnapshot) -> tuple[AgentPolicy, ...]:
    instructions = tuple(dict.fromkeys((snapshot.instructions, *snapshot.policies)))
    return tuple(
        AgentPolicy(id=f"agent_runtime.policy.{index}", instruction=value)
        for index, value in enumerate(instructions, start=1)
        if value.strip()
    )


def _canonical_contract_nodes(raw_nodes: list[object]) -> tuple[Node, ...]:
    parsed = tuple(Node.model_validate(item) for item in raw_nodes)
    operations: dict[str, Operation] = {}
    surfaces: dict[str, Surface] = {}
    for node in parsed:
        for operation in node.operations:
            existing = operations.setdefault(operation.id, operation)
            if existing != operation:
                raise BuilderUnavailable("The immutable RouteDeck NavGraph repeats an inconsistent operation.")
        for surface in _slot_surfaces(node.surfaces):
            existing = surfaces.setdefault(surface.id, surface)
            if existing != surface:
                raise BuilderUnavailable("The immutable RouteDeck NavGraph repeats an inconsistent surface.")
    return tuple(
        node.model_copy(update={
            "operations": tuple(operations[item.id] for item in node.operations),
            "surfaces": node.surfaces.model_copy(update={
                field_name: (
                    None
                    if value is None
                    else surfaces[value.id]
                    if isinstance(value, Surface)
                    else tuple(surfaces[item.id] for item in value)
                )
                for field_name in node.surfaces.__class__.model_fields
                for value in (getattr(node.surfaces, field_name),)
            }),
        })
        for node in parsed
    )


def _slot_surfaces(slots: SurfaceSlots) -> tuple[Surface, ...]:
    return tuple(
        item
        for field_name in slots.__class__.model_fields
        for value in (getattr(slots, field_name),)
        for item in (
            ()
            if value is None
            else (value,)
            if isinstance(value, Surface)
            else value
        )
    )


def _navigation_operations(topology) -> tuple[Operation, ...]:
    titles = {node.id: node.title for node in topology.nodes}
    operations: dict[str, Operation] = {}
    for transition in topology.transitions:
        if transition.outcome != "opened":
            continue
        operation = Operation(
            id=transition.operation_id,
            title=(
                "Return to agent home"
                if transition.target_node_id == topology.entry_node_id
                else f"Open {titles[transition.target_node_id]}"
            ),
            description=(
                "Return to the general Agent area without invoking an external API."
                if transition.target_node_id == topology.entry_node_id
                else f"Open the {titles[transition.target_node_id]} runtime area without invoking an external API."
            ),
            input_schema=FrozenJsonObject(_EMPTY_SCHEMA),
            safety_class=SafetyClass.NAVIGATION,
            allowed_sources=frozenset({OperationSource.AGENT, OperationSource.SURFACE}),
            review_policy=ReviewPolicy.NONE,
            outcomes=("opened",),
            outcome_schemas=FrozenJsonObject({"opened": _EMPTY_SCHEMA}),
            public_outcome_schemas=FrozenJsonObject({"opened": _EMPTY_SCHEMA}),
            public_metadata=FrozenJsonObject({
                "navigation_kind": "runtime_area",
                "target_node_id": transition.target_node_id,
            }),
        )
        existing = operations.get(operation.id)
        if existing is not None and existing != operation:
            raise BuilderConflict("One navigation operation cannot target multiple runtime areas.")
        operations[operation.id] = operation
    return tuple(operations.values())


def _node(
    *,
    topology_node,
    topology,
    operation_by_topology_id,
    capability_by_id,
    active_surface,
    clarification_surface,
    router_status_surface,
    write_review_surface,
    error_surface,
    policies,
    metadata,
) -> Node:
    local_operation_ids = (*topology_node.navigation_operation_ids, *topology_node.operation_ids)
    operations = tuple(operation_by_topology_id[operation_id] for operation_id in local_operation_ids)
    capabilities = tuple(
        Capability(
            id=(definition := capability_by_id[capability_id]).id,
            title=definition.title,
            operations=tuple(operation_by_topology_id[operation_id].ref for operation_id in definition.operation_ids),
            surfaces=(active_surface.ref,),
            policy_refs=tuple(policy.ref for policy in policies),
        )
        for capability_id in topology_node.capability_ids
    )
    outgoing = tuple(
        Transition(
            operation=operation_by_topology_id[transition.operation_id].ref,
            outcome=transition.outcome,
            target=NodeRef(id=transition.target_node_id),
        )
        for transition in topology.transitions
        if transition.source_node_id == topology_node.id
    )
    return Node(
        id=topology_node.id,
        title=topology_node.title,
        kind=NodeKind.SECTION,
        route=Route(template=topology_node.route_template, deep_link_policy=DeepLinkPolicy.SHAREABLE),
        operations=operations,
        outgoing=outgoing,
        capabilities=capabilities,
        surfaces=SurfaceSlots(
            active=active_surface,
            detail=(clarification_surface,),
            review=(write_review_surface,),
            status=(router_status_surface,),
            error=(error_surface,),
        ),
        policy_refs=tuple(item.ref for item in policies),
        suggested_actions=tuple(
            SuggestedAction(
                id=f"invoke-{_identity(operation.id)}",
                operation_id=operation.id,
                label=operation.title,
                arguments=FrozenJsonObject({}),
            )
            for operation in operations
            if not operation.input_schema_value().get("required")
        ),
        public_metadata=metadata,
        recovery=RecoveryPolicy(
            directives=(_UNKNOWN_WRITE_RECOVERY,),
            failure_surface=error_surface.ref,
        ),
    )


def _operation_declaration(binding: BuilderSourceBinding, operation_id: str) -> tuple[str, Operation]:
    document = _document(binding.document_path)
    matches: list[tuple[str, Mapping[str, object], Mapping[str, object]]] = []
    for path_template, raw_path_item in document.get("paths", {}).items():
        if not isinstance(path_template, str) or not isinstance(raw_path_item, Mapping):
            continue
        for method, raw_operation in raw_path_item.items():
            if method.casefold() not in _HTTP_METHODS or not isinstance(raw_operation, Mapping):
                continue
            if raw_operation.get("operationId") == operation_id:
                matches.append((path_template, raw_path_item, raw_operation | {"__method": method.casefold()}))
    if len(matches) != 1:
        raise BuilderUnavailable("Every accepted tool must resolve to one exact API operation.")
    path_template, path_item, raw = matches[0]
    method = str(raw["__method"])
    safety = SafetyClass.READ_EXTERNAL if method in _READ_METHODS else SafetyClass.WRITE_EXTERNAL
    review = ReviewPolicy.NONE if safety is SafetyClass.READ_EXTERNAL else ReviewPolicy.REQUIRED
    title = str(raw.get("summary") or operation_id)
    schema = _input_schema(document, path_item, raw, managed_header=binding.credential_name)
    operation = Operation(
        id=f"agent_runtime.tool.{_identity(operation_id)}",
        title=title,
        description=str(raw.get("description") or title),
        input_schema=FrozenJsonObject(schema),
        safety_class=safety,
        allowed_sources=frozenset({OperationSource.AGENT, OperationSource.SURFACE}),
        review_policy=review,
        outcomes=("observed",),
        outcome_schemas=FrozenJsonObject({"observed": _OBSERVED_SCHEMA}),
        public_outcome_schemas=FrozenJsonObject({"observed": _OBSERVED_SCHEMA}),
        unknown_recovery_directive=(
            _UNKNOWN_WRITE_RECOVERY
            if safety is SafetyClass.WRITE_EXTERNAL else None
        ),
        public_metadata=FrozenJsonObject({
            "source_operation_id": operation_id,
            "source_id": binding.source_id,
            "source_revision_id": binding.source_revision_id,
            "method": method.upper(),
            "path_template": path_template,
            **(
                {"review_surface_id": "agent_runtime.write_review"}
                if review is ReviewPolicy.REQUIRED else {}
            ),
        }),
    )
    return operation_id, operation


def _input_schema(document: Mapping[str, object], path_item: Mapping[str, object], operation: Mapping[str, object], *, managed_header: str | None) -> dict[str, object]:
    properties: dict[str, object] = {}
    required_locations: list[str] = []
    by_location: dict[str, dict[str, object]] = {key: {} for key in ("path", "query", "header", "cookie")}
    required_names: dict[str, list[str]] = {key: [] for key in by_location}
    parameters = [*(path_item.get("parameters") or ()), *(operation.get("parameters") or ())]
    for raw_parameter in parameters:
        parameter = _resolve(document, raw_parameter)
        if not isinstance(parameter, Mapping):
            raise BuilderUnavailable("An accepted API parameter is invalid.")
        location, name = str(parameter.get("in", "")), str(parameter.get("name", ""))
        if location not in by_location or not name:
            continue
        if location == "header" and managed_header and name.casefold() == managed_header.casefold():
            continue
        by_location[location][name] = _schema(document, parameter.get("schema", {"type": "string"}))
        if parameter.get("required") is True:
            required_names[location].append(name)
    for location, values in by_location.items():
        if not values:
            continue
        location_schema: dict[str, object] = {"type": "object", "properties": values, "additionalProperties": False}
        if required_names[location]:
            location_schema["required"] = required_names[location]
            required_locations.append(location)
        properties[location] = location_schema
    request_body = operation.get("requestBody")
    if request_body is not None:
        body = _resolve(document, request_body)
        if not isinstance(body, Mapping):
            raise BuilderUnavailable("The accepted API request body is invalid.")
        content = body.get("content")
        media = content.get("application/json") if isinstance(content, Mapping) else None
        if not isinstance(media, Mapping) or "schema" not in media:
            raise BuilderUnavailable("Only an exact JSON request body can be compiled for an Agent tool.")
        properties["body"] = _schema(document, media["schema"])
        if body.get("required") is True:
            required_locations.append("body")
    result: dict[str, object] = {"type": "object", "properties": properties, "additionalProperties": False}
    if required_locations:
        result["required"] = required_locations
    return result


def _schema(document: Mapping[str, object], value: object) -> dict[str, object]:
    resolved = _resolve(document, value)
    if not isinstance(resolved, Mapping):
        raise BuilderUnavailable("An accepted API schema is invalid.")
    return _rewrite_schema(document, copy.deepcopy(dict(resolved)))


def _rewrite_schema(document: Mapping[str, object], value: object) -> object:
    if isinstance(value, dict):
        if set(value) == {"$ref"}:
            resolved = _resolve(document, value)
            return _rewrite_schema(document, copy.deepcopy(resolved))
        return {key: _rewrite_schema(document, item) for key, item in value.items()}
    if isinstance(value, list):
        return [_rewrite_schema(document, item) for item in value]
    return value


def _resolve(document: Mapping[str, object], value: object) -> object:
    if not isinstance(value, Mapping) or "$ref" not in value:
        return value
    reference = value.get("$ref")
    if not isinstance(reference, str) or not reference.startswith("#/" ):
        raise BuilderUnavailable("Only local API schema references are supported.")
    current: object = document
    for part in reference[2:].split("/"):
        if not isinstance(current, Mapping) or part not in current:
            raise BuilderUnavailable("An accepted API schema reference is unavailable.")
        current = current[part]
    return current


def _document(path: Path) -> dict[str, object]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise BuilderUnavailable("The accepted API document is unavailable.") from error
    if not isinstance(value, dict):
        raise BuilderUnavailable("The accepted API document is invalid.")
    return value


def _identity(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()[:20]


def _stable(value: object) -> object:
    if isinstance(value, dict):
        return {
            key: sorted(item) if key == "allowed_sources" and isinstance(item, list) else _stable(item)
            for key, item in value.items()
        }
    if isinstance(value, list):
        return [_stable(item) for item in value]
    return value


def _compiled_navgraph_hash(compiled: CompiledApplication) -> str:
    value = _stable(json.loads(compiled.contract_documents()["compiled-navgraph.json"]))
    encoded = json.dumps(value, ensure_ascii=False, separators=(",", ":"), sort_keys=True).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


__all__ = ["AgentNavGraphArtifact", "compile_agent_navgraph", "load_agent_navgraph"]
