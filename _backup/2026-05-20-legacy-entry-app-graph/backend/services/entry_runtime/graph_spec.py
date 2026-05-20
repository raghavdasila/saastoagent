from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any

from backend.services.route_deck import build_route_deck_manifest

GRAPH_VERSION = "entry_v1"


class EntryLane(str, Enum):
    system = "system"
    auth = "auth"
    saas_agent = "saas_agent"
    terminal = "terminal"


class EntryStageId(str, Enum):
    bootstrap = "bootstrap"
    intent = "intent"
    display_name = "display_name"
    email = "email"
    password = "password"
    saas_agent_select = "saas_agent_select"
    saas_agent_job = "saas_agent_job"
    saas_agent_confirm = "saas_agent_confirm"
    setup_intro = "setup_intro"
    connection_confirm = "connection_confirm"
    operator_ready = "operator_ready"


@dataclass(frozen=True)
class EntryNodeSpec:
    id: EntryStageId
    label: str
    lane: EntryLane
    parent: str | None = None


@dataclass(frozen=True)
class EntryEdgeSpec:
    from_stage: EntryStageId
    to_stage: EntryStageId
    edge_type: str
    condition: str | None = None


ENTRY_NODE_SPECS = {
    EntryStageId.bootstrap: EntryNodeSpec(
        id=EntryStageId.bootstrap,
        label="Bootstrap",
        lane=EntryLane.system,
    ),
    EntryStageId.intent: EntryNodeSpec(
        id=EntryStageId.intent,
        label="Intent",
        lane=EntryLane.auth,
    ),
    EntryStageId.display_name: EntryNodeSpec(
        id=EntryStageId.display_name,
        label="Display Name",
        lane=EntryLane.auth,
    ),
    EntryStageId.email: EntryNodeSpec(
        id=EntryStageId.email,
        label="Email",
        lane=EntryLane.auth,
    ),
    EntryStageId.password: EntryNodeSpec(
        id=EntryStageId.password,
        label="Password",
        lane=EntryLane.auth,
    ),
    EntryStageId.saas_agent_select: EntryNodeSpec(
        id=EntryStageId.saas_agent_select,
        label="SaaS Agent Select",
        lane=EntryLane.saas_agent,
    ),
    EntryStageId.saas_agent_job: EntryNodeSpec(
        id=EntryStageId.saas_agent_job,
        label="SaaS Agent Setup",
        lane=EntryLane.saas_agent,
    ),
    EntryStageId.saas_agent_confirm: EntryNodeSpec(
        id=EntryStageId.saas_agent_confirm,
        label="SaaS Agent Confirm",
        lane=EntryLane.saas_agent,
    ),
    EntryStageId.operator_ready: EntryNodeSpec(
        id=EntryStageId.operator_ready,
        label="Operator Ready",
        lane=EntryLane.terminal,
    ),
    EntryStageId.setup_intro: EntryNodeSpec(
        id=EntryStageId.setup_intro,
        label="REST Setup",
        lane=EntryLane.saas_agent,
    ),
    EntryStageId.connection_confirm: EntryNodeSpec(
        id=EntryStageId.connection_confirm,
        label="Connection Confirm",
        lane=EntryLane.saas_agent,
    ),
}

def _entry_edge_specs_from_route_deck() -> tuple[EntryEdgeSpec, ...]:
    specs: list[EntryEdgeSpec] = []
    for edge in build_route_deck_manifest().edges:
        specs.append(
            EntryEdgeSpec(
                from_stage=EntryStageId(edge.from_stage),
                to_stage=EntryStageId(edge.to_stage),
                edge_type=edge.edge_type,
                condition=edge.condition,
            )
        )
    return tuple(specs)


ENTRY_EDGE_SPECS = _entry_edge_specs_from_route_deck()


def get_node_spec(stage_id: str) -> EntryNodeSpec:
    return ENTRY_NODE_SPECS[EntryStageId(stage_id)]


def build_graph_manifest() -> dict[str, Any]:
    return build_route_deck_manifest().model_dump(mode="json", by_alias=True)
