from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any

GRAPH_VERSION = "entry_v1"


class EntryLane(str, Enum):
    system = "system"
    auth = "auth"
    workspace = "workspace"
    terminal = "terminal"


class EntryStageId(str, Enum):
    bootstrap = "bootstrap"
    intent = "intent"
    display_name = "display_name"
    email = "email"
    password = "password"
    workspace_select = "workspace_select"
    workspace_job = "workspace_job"
    workspace_confirm = "workspace_confirm"
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
    EntryStageId.workspace_select: EntryNodeSpec(
        id=EntryStageId.workspace_select,
        label="Workspace Select",
        lane=EntryLane.workspace,
    ),
    EntryStageId.workspace_job: EntryNodeSpec(
        id=EntryStageId.workspace_job,
        label="Workspace Draft",
        lane=EntryLane.workspace,
    ),
    EntryStageId.workspace_confirm: EntryNodeSpec(
        id=EntryStageId.workspace_confirm,
        label="Workspace Confirm",
        lane=EntryLane.workspace,
    ),
    EntryStageId.operator_ready: EntryNodeSpec(
        id=EntryStageId.operator_ready,
        label="Operator Ready",
        lane=EntryLane.terminal,
    ),
    EntryStageId.setup_intro: EntryNodeSpec(
        id=EntryStageId.setup_intro,
        label="REST Setup",
        lane=EntryLane.workspace,
    ),
    EntryStageId.connection_confirm: EntryNodeSpec(
        id=EntryStageId.connection_confirm,
        label="Connection Confirm",
        lane=EntryLane.workspace,
    ),
}

ENTRY_EDGE_SPECS = (
    EntryEdgeSpec(EntryStageId.bootstrap, EntryStageId.intent, "conditional", "anonymous_start"),
    EntryEdgeSpec(EntryStageId.bootstrap, EntryStageId.email, "conditional", "login_initial_intent"),
    EntryEdgeSpec(
        EntryStageId.bootstrap,
        EntryStageId.display_name,
        "conditional",
        "register_initial_intent",
    ),
    EntryEdgeSpec(
        EntryStageId.bootstrap,
        EntryStageId.workspace_select,
        "conditional",
        "authenticated_many_workspaces",
    ),
    EntryEdgeSpec(
        EntryStageId.bootstrap,
        EntryStageId.workspace_job,
        "conditional",
        "authenticated_no_workspaces",
    ),
    EntryEdgeSpec(
        EntryStageId.bootstrap,
        EntryStageId.operator_ready,
        "conditional",
        "authenticated_single_workspace",
    ),
    EntryEdgeSpec(EntryStageId.intent, EntryStageId.display_name, "conditional", "register"),
    EntryEdgeSpec(EntryStageId.intent, EntryStageId.email, "conditional", "login"),
    EntryEdgeSpec(EntryStageId.display_name, EntryStageId.email, "sequence"),
    EntryEdgeSpec(EntryStageId.email, EntryStageId.password, "sequence"),
    EntryEdgeSpec(
        EntryStageId.password,
        EntryStageId.workspace_select,
        "conditional",
        "authenticated_many_workspaces",
    ),
    EntryEdgeSpec(
        EntryStageId.password,
        EntryStageId.workspace_job,
        "conditional",
        "authenticated_no_workspaces",
    ),
    EntryEdgeSpec(
        EntryStageId.password,
        EntryStageId.operator_ready,
        "conditional",
        "authenticated_single_workspace",
    ),
    EntryEdgeSpec(
        EntryStageId.workspace_select,
        EntryStageId.operator_ready,
        "conditional",
        "existing_workspace_selected",
    ),
    EntryEdgeSpec(
        EntryStageId.workspace_select,
        EntryStageId.workspace_confirm,
        "conditional",
        "new_workspace_requested",
    ),
    EntryEdgeSpec(EntryStageId.workspace_job, EntryStageId.workspace_confirm, "sequence"),
    EntryEdgeSpec(
        EntryStageId.workspace_confirm,
        EntryStageId.operator_ready,
        "conditional",
        "workspace_created",
    ),
    EntryEdgeSpec(EntryStageId.setup_intro, EntryStageId.connection_confirm, "conditional", "rest_details_ready"),
    EntryEdgeSpec(EntryStageId.connection_confirm, EntryStageId.operator_ready, "conditional", "connection_activated"),
)


def get_node_spec(stage_id: str) -> EntryNodeSpec:
    return ENTRY_NODE_SPECS[EntryStageId(stage_id)]


def build_graph_manifest() -> dict[str, Any]:
    return {
        "version": GRAPH_VERSION,
        "nodes": [
            {
                "id": spec.id.value,
                "label": spec.label,
                "lane": spec.lane.value,
                "parent": spec.parent,
            }
            for spec in ENTRY_NODE_SPECS.values()
        ],
        "edges": [
            {
                "from": edge.from_stage.value,
                "to": edge.to_stage.value,
                "type": edge.edge_type,
                "condition": edge.condition,
            }
            for edge in ENTRY_EDGE_SPECS
        ],
    }
