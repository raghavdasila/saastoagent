from __future__ import annotations

import hashlib
import json
from typing import Protocol

from pydantic import BaseModel, ConfigDict


_ENTRY_NODE_ID = "agent_runtime.home"
_SURFACE_IDS = (
    "agent_runtime.home",
    "agent_runtime.clarification",
    "agent_runtime.toolrouter_status",
    "agent_runtime.delivery_status",
)


class DesignerTopologyError(ValueError):
    pass


class DesignTopologyCapability(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    id: str
    title: str
    operation_ids: tuple[str, ...]


class DesignTopologyNode(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    id: str
    title: str
    capability_ids: tuple[str, ...]
    operation_ids: tuple[str, ...]
    surface_ids: tuple[str, ...]
    policy_count: int


class DesignTopology(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    topology_hash: str
    entry_node_id: str
    nodes: tuple[DesignTopologyNode, ...]
    capabilities: tuple[DesignTopologyCapability, ...]
    operation_ids: tuple[str, ...]


class _DesignContent(Protocol):
    goal: str
    instructions: str
    features: tuple[str, ...]
    behaviors: tuple[str, ...]
    policies: tuple[str, ...]
    capabilities: tuple[str, ...]
    tools: tuple[str, ...]


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

    capability_views = tuple(
        DesignTopologyCapability(
            id=f"agent_runtime.capability.{_identity(item.title, item.operation_ids)}",
            title=item.title,
            operation_ids=item.operation_ids,
        )
        for item in capabilities
    )
    node = DesignTopologyNode(
        id=_ENTRY_NODE_ID,
        title=content.goal.strip() or "Agent runtime",
        capability_ids=tuple(item.id for item in capability_views),
        operation_ids=tools,
        surface_ids=_SURFACE_IDS,
        policy_count=len(tuple(dict.fromkeys((content.instructions, *content.policies)))),
    )
    payload = {
        "entry_node_id": _ENTRY_NODE_ID,
        "nodes": [node.model_dump(mode="json")],
        "capabilities": [item.model_dump(mode="json") for item in capability_views],
        "operation_ids": list(tools),
        "features": list(content.features),
        "behaviors": list(content.behaviors),
        "policies": list(content.policies),
    }
    encoded = json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return DesignTopology(
        topology_hash=hashlib.sha256(encoded).hexdigest(),
        entry_node_id=_ENTRY_NODE_ID,
        nodes=(node,),
        capabilities=capability_views,
        operation_ids=tools,
    )


class _ParsedCapability(BaseModel):
    model_config = ConfigDict(frozen=True)

    title: str
    operation_ids: tuple[str, ...]


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


def _identity(title: str, operation_ids: tuple[str, ...]) -> str:
    value = f"{title.casefold()}\0{','.join(operation_ids)}"
    return hashlib.sha256(value.encode("utf-8")).hexdigest()[:20]


__all__ = [
    "DesignTopology",
    "DesignTopologyCapability",
    "DesignTopologyNode",
    "DesignerTopologyError",
    "compile_design_topology",
]
