from __future__ import annotations

from routedeck_core.app import Feature
from routedeck_core.contracts.application import Capability, Node
from routedeck_core.contracts.navigation import DeepLinkPolicy, NodeKind, NodeRef, Route, Transition
from routedeck_core.contracts.projection import FrozenJsonObject
from routedeck_core.contracts.surfaces import Surface, SurfaceAffordance, SurfaceLifecycle, SurfaceSlots

from .declarations import (
    EMPTY_OBJECT_SCHEMA,
    HOME_REF,
    OPEN_SOURCES,
    OPEN_VERIFICATION,
    OWNER_CONTEXT_PROVIDER,
)


HOME_SURFACE = Surface(
    id="workspace.home",
    component="workspace.home",
    lifecycle=SurfaceLifecycle.STABLE,
    public_props_schema=FrozenJsonObject(EMPTY_OBJECT_SCHEMA),
    affordances=(
        SurfaceAffordance(id="open_sources", event="open", operation=OPEN_SOURCES.ref),
        SurfaceAffordance(id="open_verification", event="open", operation=OPEN_VERIFICATION.ref),
    ),
)
WORKSPACE_CAPABILITY = Capability(
    id="workspace.access",
    title="Use the authenticated owner Workspace",
    operations=(OPEN_SOURCES.ref, OPEN_VERIFICATION.ref),
    surfaces=(HOME_SURFACE.ref,),
)
HOME_NODE = Node(
    id=HOME_REF.id,
    title="Home",
    kind=NodeKind.SECTION,
    route=Route(template="/home", deep_link_policy=DeepLinkPolicy.SESSION_BOUND),
    context_providers=(OWNER_CONTEXT_PROVIDER,),
    operations=(OPEN_SOURCES, OPEN_VERIFICATION),
    outgoing=(
        Transition(operation=OPEN_SOURCES.ref, outcome="opened", target=NodeRef(id="sources.home")),
        Transition(
            operation=OPEN_VERIFICATION.ref,
            outcome="opened",
            target=NodeRef(id="lounge.verification_pending"),
        ),
    ),
    capabilities=(WORKSPACE_CAPABILITY,),
    surfaces=SurfaceSlots(active=HOME_SURFACE),
)
WORKSPACE_FEATURE = Feature(namespace="workspace", nodes=(HOME_NODE,))

__all__ = ["HOME_NODE", "HOME_SURFACE", "WORKSPACE_FEATURE"]
