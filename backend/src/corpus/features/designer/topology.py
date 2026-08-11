from __future__ import annotations

import hashlib
import json
from typing import Protocol

from pydantic import BaseModel, ConfigDict


_ENTRY_NODE_ID = "agent_runtime.home"
_SHARED_SURFACE_IDS = (
    "agent_runtime.home",
    "agent_runtime.clarification",
    "agent_runtime.toolrouter_status",
    "agent_runtime.delivery_status",
)
_RETURN_HOME_OPERATION_ID = "agent_runtime.return_home"


class DesignerTopologyError(ValueError):
    pass


class DesignTopologyCapability(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    id: str
    title: str
    operation_ids: tuple[str, ...]
    node_id: str


class DesignTopologyNode(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    id: str
    title: str
    route_template: str
    capability_ids: tuple[str, ...]
    operation_ids: tuple[str, ...]
    navigation_operation_ids: tuple[str, ...]
    surface_ids: tuple[str, ...]
    policy_count: int


class DesignTopologyTransition(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    source_node_id: str
    target_node_id: str
    operation_id: str
    outcome: str


class DesignTopology(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    topology_hash: str
    mode: str
    entry_node_id: str
    nodes: tuple[DesignTopologyNode, ...]
    capabilities: tuple[DesignTopologyCapability, ...]
    transitions: tuple[DesignTopologyTransition, ...]
    operation_ids: tuple[str, ...]


class _DesignContent(Protocol):
    goal: str
    instructions: str
    features: tuple[str, ...]
    behaviors: tuple[str, ...]
    policies: tuple[str, ...]
    capabilities: tuple[str, ...]
    tools: tuple[str, ...]
    runtime_areas: tuple[object, ...]


def compile_design_topology(content: _DesignContent) -> DesignTopology:
    tools = tuple(content.tools)
    if not tools:
        raise DesignerTopologyError("The accepted design must contain at least one tool.")
    if len(set(tools)) != len(tools):
        raise DesignerTopologyError("Each accepted tool must have one unique identity.")

    raw_capabilities = tuple(content.capabilities)
    if not raw_capabilities:
        raise DesignerTopologyError("The accepted design must contain at least one capability.")
    capabilities = (
        (_ParsedCapability(title=raw_capabilities[0].strip(), operation_ids=tools),)
        if len(raw_capabilities) == 1 and ":" not in raw_capabilities[0]
        else tuple(_capability(value) for value in raw_capabilities)
    )
    if any(not item.title for item in capabilities):
        raise DesignerTopologyError("Each accepted capability must have a title.")
    if len({item.title.casefold() for item in capabilities}) != len(capabilities):
        raise DesignerTopologyError("Each accepted capability must have one unique title.")

    assigned = tuple(operation for item in capabilities for operation in item.operation_ids)
    if len(assigned) != len(set(assigned)) or set(assigned) != set(tools):
        raise DesignerTopologyError(
            "Every accepted tool must belong to exactly one capability."
        )

    if not content.runtime_areas:
        return _legacy_topology(content, capabilities, tools)

    parsed_areas = tuple(_runtime_area(value) for value in content.runtime_areas)
    if len({item.title.casefold() for item in parsed_areas}) != len(parsed_areas):
        raise DesignerTopologyError("Each runtime area must have one unique title.")
    capability_by_title = {item.title.casefold(): item for item in capabilities}
    assigned_capabilities = tuple(
        title.casefold()
        for area in parsed_areas
        for title in area.capability_titles
    )
    if (
        len(assigned_capabilities) != len(set(assigned_capabilities))
        or set(assigned_capabilities) != set(capability_by_title)
    ):
        raise DesignerTopologyError(
            "Every capability must belong to exactly one runtime area."
        )

    policy_count = len(tuple(dict.fromkeys((content.instructions, *content.policies))))
    area_records = tuple(
        _runtime_area_record(area, capability_by_title)
        for area in parsed_areas
    )
    capability_views = tuple(
        DesignTopologyCapability(
            id=_capability_id(item),
            title=item.title,
            operation_ids=item.operation_ids,
            node_id=area.node_id,
        )
        for area in area_records
        for item in area.capabilities
    )
    capability_view_by_title = {
        item.title.casefold(): item for item in capability_views
    }
    entry_navigation_ids = tuple(area.open_operation_id for area in area_records)
    entry = DesignTopologyNode(
        id=_ENTRY_NODE_ID,
        title="Agent home",
        route_template="/",
        capability_ids=(),
        operation_ids=(),
        navigation_operation_ids=entry_navigation_ids,
        surface_ids=_SHARED_SURFACE_IDS,
        policy_count=policy_count,
    )
    area_nodes = tuple(
        DesignTopologyNode(
            id=area.node_id,
            title=area.title,
            route_template=f"/areas/{area.node_id.rsplit('.', 1)[-1]}",
            capability_ids=tuple(
                capability_view_by_title[title.casefold()].id
                for title in area.capability_titles
            ),
            operation_ids=tuple(
                operation_id
                for title in area.capability_titles
                for operation_id in capability_view_by_title[title.casefold()].operation_ids
            ),
            navigation_operation_ids=(_RETURN_HOME_OPERATION_ID,),
            surface_ids=(
                f"{area.node_id}.home",
                *_SHARED_SURFACE_IDS[1:],
            ),
            policy_count=policy_count,
        )
        for area in area_records
    )
    transitions = tuple(
        transition
        for area, node in zip(area_records, area_nodes, strict=True)
        for transition in (
            DesignTopologyTransition(
                source_node_id=_ENTRY_NODE_ID,
                target_node_id=node.id,
                operation_id=area.open_operation_id,
                outcome="opened",
            ),
            DesignTopologyTransition(
                source_node_id=node.id,
                target_node_id=_ENTRY_NODE_ID,
                operation_id=_RETURN_HOME_OPERATION_ID,
                outcome="opened",
            ),
            *(
                DesignTopologyTransition(
                    source_node_id=node.id,
                    target_node_id=node.id,
                    operation_id=operation_id,
                    outcome="observed",
                )
                for operation_id in node.operation_ids
            ),
        )
    )
    nodes = (entry, *area_nodes)
    payload = {
        "mode": "capability_areas",
        "entry_node_id": _ENTRY_NODE_ID,
        "nodes": [node.model_dump(mode="json") for node in nodes],
        "capabilities": [item.model_dump(mode="json") for item in capability_views],
        "transitions": [item.model_dump(mode="json") for item in transitions],
        "operation_ids": list(tools),
        "features": list(content.features),
        "behaviors": list(content.behaviors),
        "policies": list(content.policies),
    }
    encoded = json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return DesignTopology(
        topology_hash=hashlib.sha256(encoded).hexdigest(),
        mode="capability_areas",
        entry_node_id=_ENTRY_NODE_ID,
        nodes=nodes,
        capabilities=capability_views,
        transitions=transitions,
        operation_ids=tools,
    )


class _ParsedCapability(BaseModel):
    model_config = ConfigDict(frozen=True)

    title: str
    operation_ids: tuple[str, ...]


class _ParsedRuntimeArea(BaseModel):
    model_config = ConfigDict(frozen=True)

    title: str
    capability_titles: tuple[str, ...]


class _RuntimeAreaRecord(BaseModel):
    model_config = ConfigDict(frozen=True)

    title: str
    node_id: str
    open_operation_id: str
    capability_titles: tuple[str, ...]
    capabilities: tuple[_ParsedCapability, ...]


def _capability(value: str) -> _ParsedCapability:
    title, separator, raw_operations = value.partition(":")
    clean_title = title.strip()
    operations = tuple(item.strip() for item in raw_operations.split(",") if item.strip())
    if not separator or not clean_title or not operations:
        raise DesignerTopologyError(
            "Each capability must use 'Capability title: operation_id, operation_id'."
        )
    if len(set(operations)) != len(operations):
        raise DesignerTopologyError("A capability cannot repeat one tool identity.")
    return _ParsedCapability(title=clean_title, operation_ids=operations)


def _runtime_area(value: object) -> _ParsedRuntimeArea:
    title = getattr(value, "title", None)
    capability_titles = getattr(value, "capability_titles", None)
    if not isinstance(title, str) or not title.strip():
        raise DesignerTopologyError("Each runtime area must have a title.")
    if not isinstance(capability_titles, tuple) or not capability_titles:
        raise DesignerTopologyError("Each runtime area must contain at least one capability.")
    clean_capabilities = tuple(item.strip() for item in capability_titles if isinstance(item, str) and item.strip())
    if len(clean_capabilities) != len(capability_titles) or len(set(item.casefold() for item in clean_capabilities)) != len(clean_capabilities):
        raise DesignerTopologyError("A runtime area cannot repeat a capability.")
    return _ParsedRuntimeArea(title=title.strip(), capability_titles=clean_capabilities)


def _runtime_area_record(
    area: _ParsedRuntimeArea,
    capability_by_title: dict[str, _ParsedCapability],
) -> _RuntimeAreaRecord:
    try:
        capabilities = tuple(capability_by_title[title.casefold()] for title in area.capability_titles)
    except KeyError as error:
        raise DesignerTopologyError("A runtime area references an unknown capability.") from error
    identity = _identity(area.title, tuple(item.title for item in capabilities))
    return _RuntimeAreaRecord(
        title=area.title,
        node_id=f"agent_runtime.area.{identity}",
        open_operation_id=f"agent_runtime.open_area.{identity}",
        capability_titles=area.capability_titles,
        capabilities=capabilities,
    )


def _legacy_topology(
    content: _DesignContent,
    capabilities: tuple[_ParsedCapability, ...],
    tools: tuple[str, ...],
) -> DesignTopology:
    capability_views = tuple(
        DesignTopologyCapability(
            id=_capability_id(item),
            title=item.title,
            operation_ids=item.operation_ids,
            node_id=_ENTRY_NODE_ID,
        )
        for item in capabilities
    )
    node = DesignTopologyNode(
        id=_ENTRY_NODE_ID,
        title=content.goal.strip() or "Agent runtime",
        route_template="/",
        capability_ids=tuple(item.id for item in capability_views),
        operation_ids=tools,
        navigation_operation_ids=(),
        surface_ids=_SHARED_SURFACE_IDS,
        policy_count=len(tuple(dict.fromkeys((content.instructions, *content.policies)))),
    )
    legacy_payload = {
        "entry_node_id": _ENTRY_NODE_ID,
        "nodes": [{
            "id": node.id,
            "title": node.title,
            "capability_ids": list(node.capability_ids),
            "operation_ids": list(node.operation_ids),
            "surface_ids": list(node.surface_ids),
            "policy_count": node.policy_count,
        }],
        "capabilities": [{
            "id": item.id,
            "title": item.title,
            "operation_ids": list(item.operation_ids),
        } for item in capability_views],
        "operation_ids": list(tools),
        "features": list(content.features),
        "behaviors": list(content.behaviors),
        "policies": list(content.policies),
    }
    encoded = json.dumps(legacy_payload, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return DesignTopology(
        topology_hash=hashlib.sha256(encoded).hexdigest(),
        mode="legacy_single_area",
        entry_node_id=_ENTRY_NODE_ID,
        nodes=(node,),
        capabilities=capability_views,
        transitions=tuple(
            DesignTopologyTransition(
                source_node_id=_ENTRY_NODE_ID,
                target_node_id=_ENTRY_NODE_ID,
                operation_id=operation_id,
                outcome="observed",
            )
            for operation_id in tools
        ),
        operation_ids=tools,
    )


def _capability_id(item: _ParsedCapability) -> str:
    return f"agent_runtime.capability.{_identity(item.title, item.operation_ids)}"


def _identity(title: str, operation_ids: tuple[str, ...]) -> str:
    value = f"{title.casefold()}\0{','.join(operation_ids)}"
    return hashlib.sha256(value.encode("utf-8")).hexdigest()[:20]


__all__ = [
    "DesignTopology",
    "DesignTopologyCapability",
    "DesignTopologyNode",
    "DesignTopologyTransition",
    "DesignerTopologyError",
    "compile_design_topology",
]
