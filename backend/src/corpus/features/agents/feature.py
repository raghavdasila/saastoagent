from __future__ import annotations

from routedeck_core.app import Feature
from routedeck_core.contracts.application import Capability, Node
from routedeck_core.contracts.navigation import DeepLinkPolicy, NodeKind, NodeRef, Route, Transition
from routedeck_core.contracts.projection import FrozenJsonObject
from routedeck_core.contracts.suggestions import SuggestedAction
from routedeck_core.contracts.surfaces import Surface, SurfaceAffordance, SurfaceLifecycle, SurfaceSlots

from corpus.auth.contracts import OWNER_CONTEXT_PROVIDER
from corpus.shared.schemas import EMPTY_OBJECT_SCHEMA

from . import policies
from .contracts import AGENTS_CREATE_REF, AGENTS_HOME_REF
from .declarations import (
    CANCEL_CREATE,
    CREATE_AGENT,
    OPEN_CREATE,
    RETURN_TO_WORKSPACE,
    SAVE_AGENT_CHANGES,
)


AGENTS_HOME_SURFACE = Surface(
    id="agents.home",
    component="agents.home",
    lifecycle=SurfaceLifecycle.STABLE,
    public_props_schema=FrozenJsonObject(EMPTY_OBJECT_SCHEMA),
    affordances=(
        SurfaceAffordance(id="open_create", event="open", operation=OPEN_CREATE.ref),
        SurfaceAffordance(id="save_changes", event="submit", operation=SAVE_AGENT_CHANGES.ref),
        SurfaceAffordance(id="return_to_workspace", event="open", operation=RETURN_TO_WORKSPACE.ref),
    ),
)
AGENTS_CREATE_SURFACE = Surface(
    id="agents.create",
    component="agents.create",
    lifecycle=SurfaceLifecycle.STABLE,
    public_props_schema=FrozenJsonObject(EMPTY_OBJECT_SCHEMA),
    affordances=(
        SurfaceAffordance(id="create_agent", event="submit", operation=CREATE_AGENT.ref),
        SurfaceAffordance(id="cancel_create", event="open", operation=CANCEL_CREATE.ref),
    ),
)
AGENT_INVENTORY = Capability(
    id="agents.inventory",
    title="Inspect and edit agents in this Workspace",
    operations=(OPEN_CREATE.ref, SAVE_AGENT_CHANGES.ref, RETURN_TO_WORKSPACE.ref),
    surfaces=(AGENTS_HOME_SURFACE.ref,),
    policy_refs=(policies.HOME_TRUTH.ref, policies.VERSION_TRUTH.ref),
)
AGENT_CREATION = Capability(
    id="agents.creation",
    title="Create an agent configuration",
    operations=(CREATE_AGENT.ref, CANCEL_CREATE.ref),
    surfaces=(AGENTS_CREATE_SURFACE.ref,),
    policy_refs=(policies.VERSION_TRUTH.ref,),
)


def create_agents_feature(workspace_home_ref: NodeRef) -> Feature:
    home = Node(
        id=AGENTS_HOME_REF.id,
        title="Agents",
        kind=NodeKind.SECTION,
        parent=workspace_home_ref,
        route=Route(template="/agents", deep_link_policy=DeepLinkPolicy.SESSION_BOUND),
        context_providers=(OWNER_CONTEXT_PROVIDER,),
        operations=(OPEN_CREATE, SAVE_AGENT_CHANGES, RETURN_TO_WORKSPACE),
        outgoing=(
            Transition(operation=OPEN_CREATE.ref, outcome="opened", target=AGENTS_CREATE_REF),
            Transition(operation=SAVE_AGENT_CHANGES.ref, outcome="saved", target=AGENTS_HOME_REF),
            Transition(operation=RETURN_TO_WORKSPACE.ref, outcome="opened", target=workspace_home_ref),
        ),
        capabilities=(AGENT_INVENTORY,),
        surfaces=SurfaceSlots(active=AGENTS_HOME_SURFACE),
        suggested_actions=(
            SuggestedAction(id="agents.create", operation_id=OPEN_CREATE.id, label="Create agent"),
        ),
        policy_refs=(policies.HOME_TRUTH.ref, policies.VERSION_TRUTH.ref),
    )
    create = Node(
        id=AGENTS_CREATE_REF.id,
        title="Create agent",
        kind=NodeKind.SECTION,
        parent=AGENTS_HOME_REF,
        route=Route(template="/agents/new", deep_link_policy=DeepLinkPolicy.SESSION_BOUND),
        context_providers=(OWNER_CONTEXT_PROVIDER,),
        operations=(CREATE_AGENT, CANCEL_CREATE),
        outgoing=(
            Transition(operation=CREATE_AGENT.ref, outcome="created", target=AGENTS_HOME_REF),
            Transition(operation=CANCEL_CREATE.ref, outcome="opened", target=AGENTS_HOME_REF),
        ),
        capabilities=(AGENT_CREATION,),
        surfaces=SurfaceSlots(active=AGENTS_CREATE_SURFACE),
        policy_refs=(policies.VERSION_TRUTH.ref, policies.EDIT_CONFLICT.ref),
    )
    return Feature(
        namespace="agents",
        nodes=(home, create),
        agent_policies=policies.AGENTS_AGENT_POLICIES,
        policy_refs=(
            policies.FEATURE_PROMPT.ref,
            policies.OWNER_SCOPE.ref,
            policies.VERSION_TRUTH.ref,
        ),
    )


__all__ = [
    "AGENTS_CREATE_SURFACE",
    "AGENTS_HOME_SURFACE",
    "create_agents_feature",
]
