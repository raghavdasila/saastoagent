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
from .contracts import HOME_REF, WORKSPACE_OVERVIEW_PROVIDER
from .declarations import OPEN_AGENTS, OPEN_SOURCES, OPEN_VERIFICATION


HOME_SURFACE = Surface(
    id="workspace.home",
    component="workspace.home",
    lifecycle=SurfaceLifecycle.STABLE,
    public_props_schema=FrozenJsonObject(EMPTY_OBJECT_SCHEMA),
    affordances=(
        SurfaceAffordance(id="open_agents", event="open", operation=OPEN_AGENTS.ref),
        SurfaceAffordance(id="open_sources", event="open", operation=OPEN_SOURCES.ref),
        SurfaceAffordance(id="open_verification", event="open", operation=OPEN_VERIFICATION.ref),
    ),
    policy_refs=(policies.TRUTHFUL_STATE.ref, policies.OVERVIEW_ONLY.ref),
)
WORKSPACE_CAPABILITY = Capability(
    id="workspace.overview",
    title="Use the authenticated owner Workspace overview",
    operations=(OPEN_AGENTS.ref, OPEN_SOURCES.ref, OPEN_VERIFICATION.ref),
    surfaces=(HOME_SURFACE.ref,),
    policy_refs=(policies.TRUTHFUL_STATE.ref, policies.OVERVIEW_ONLY.ref),
)


def create_workspace_feature(
    *,
    agents_home_ref: NodeRef,
    sources_home_ref: NodeRef,
    verification_ref: NodeRef,
) -> Feature:
    home = Node(
        id=HOME_REF.id,
        title="Home",
        kind=NodeKind.SECTION,
        route=Route(template="/home", deep_link_policy=DeepLinkPolicy.SESSION_BOUND),
        context_providers=(OWNER_CONTEXT_PROVIDER, WORKSPACE_OVERVIEW_PROVIDER),
        operations=(OPEN_AGENTS, OPEN_SOURCES, OPEN_VERIFICATION),
        outgoing=(
            Transition(operation=OPEN_AGENTS.ref, outcome="opened", target=agents_home_ref),
            Transition(operation=OPEN_SOURCES.ref, outcome="opened", target=sources_home_ref),
            Transition(operation=OPEN_VERIFICATION.ref, outcome="opened", target=verification_ref),
        ),
        capabilities=(WORKSPACE_CAPABILITY,),
        surfaces=SurfaceSlots(active=HOME_SURFACE),
        suggested_actions=(
            SuggestedAction(
                id="workspace.manage_agents",
                operation_id=OPEN_AGENTS.id,
                label="Manage agents",
            ),
            SuggestedAction(
                id="workspace.manage_sources",
                operation_id=OPEN_SOURCES.id,
                label="Manage sources",
            ),
        ),
        policy_refs=(policies.TRUTHFUL_STATE.ref, policies.OVERVIEW_ONLY.ref),
    )
    return Feature(
        namespace="workspace",
        nodes=(home,),
        agent_policies=policies.WORKSPACE_AGENT_POLICIES,
        policy_refs=(
            policies.FEATURE_PROMPT.ref,
            policies.OWNER_SCOPE.ref,
            policies.OVERVIEW_ONLY.ref,
            policies.FILE_FIRST_TASK_ROUTING.ref,
        ),
    )


__all__ = ["HOME_SURFACE", "create_workspace_feature"]
