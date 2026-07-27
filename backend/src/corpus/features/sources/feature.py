from __future__ import annotations

from routedeck_core.app import Feature
from routedeck_core.contracts.application import Capability, Node
from routedeck_core.contracts.navigation import DeepLinkPolicy, NodeKind, Route, Transition
from routedeck_core.contracts.projection import FrozenJsonObject
from routedeck_core.contracts.surfaces import (
    Surface,
    SurfaceAffordance,
    SurfaceLifecycle,
    SurfaceSlots,
)

from corpus.features.workspace.declarations import (
    EMPTY_OBJECT_SCHEMA,
    HOME_REF,
    OWNER_CONTEXT_PROVIDER,
)

from .declarations import RETURN_TO_HOME, SOURCES_HOME_REF


SOURCES_DEBUG_SURFACE = Surface(
    id="sources.debug",
    component="sources.debug",
    lifecycle=SurfaceLifecycle.STABLE,
    public_props_schema=FrozenJsonObject(EMPTY_OBJECT_SCHEMA),
    affordances=(
        SurfaceAffordance(
            id="return_to_home",
            event="open",
            operation=RETURN_TO_HOME.ref,
        ),
    ),
)

SOURCES_CAPABILITY = Capability(
    id="sources.manage",
    title="Manage owner Sources through registered connectors",
    operations=(RETURN_TO_HOME.ref,),
    surfaces=(SOURCES_DEBUG_SURFACE.ref,),
)

SOURCES_HOME_NODE = Node(
    id=SOURCES_HOME_REF.id,
    title="Sources",
    kind=NodeKind.SECTION,
    parent=HOME_REF,
    route=Route(
        template="/sources",
        deep_link_policy=DeepLinkPolicy.SESSION_BOUND,
    ),
    context_providers=(OWNER_CONTEXT_PROVIDER,),
    operations=(RETURN_TO_HOME,),
    outgoing=(
        Transition(
            operation=RETURN_TO_HOME.ref,
            outcome="opened",
            target=HOME_REF,
        ),
    ),
    capabilities=(SOURCES_CAPABILITY,),
    surfaces=SurfaceSlots(active=SOURCES_DEBUG_SURFACE),
)

SOURCES_FEATURE = Feature(
    namespace="sources",
    nodes=(SOURCES_HOME_NODE,),
)


__all__ = [
    "SOURCES_DEBUG_SURFACE",
    "SOURCES_FEATURE",
    "SOURCES_HOME_NODE",
]
