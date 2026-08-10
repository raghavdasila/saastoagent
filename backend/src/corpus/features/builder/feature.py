from routedeck_core.app import Feature
from routedeck_core.contracts.application import Capability, Node
from routedeck_core.contracts.navigation import DeepLinkPolicy, NodeKind, NodeRef, Route, Transition
from routedeck_core.contracts.projection import FrozenJsonObject
from routedeck_core.contracts.surfaces import Surface, SurfaceAffordance, SurfaceLifecycle, SurfaceSlots

from corpus.auth.contracts import OWNER_CONTEXT_PROVIDER
from corpus.features.agents.declarations import AGENT_ENTITY_PROVIDER, RETURN_TO_AGENT_HUB

from .contracts import BUILDER_HOME_REF
from .declarations import ASSEMBLE_BUILD


BUILDER_HOME_SURFACE = Surface(
    id="builder.home", component="builder.home", lifecycle=SurfaceLifecycle.STABLE,
    public_props_schema=FrozenJsonObject({
        "type": "object",
        "properties": {"selected_agent_ref": {"type": "string", "minLength": 1}},
        "required": ["selected_agent_ref"], "additionalProperties": False,
    }),
    affordances=(
        SurfaceAffordance(id="return_to_agent", event="open", operation=RETURN_TO_AGENT_HUB.ref),
        SurfaceAffordance(id="assemble", event="submit", operation=ASSEMBLE_BUILD.ref),
    ),
)
BUILDER_CAPABILITY = Capability(
    id="builder.assembly", title="Assemble one accepted immutable Agent build",
    operations=(RETURN_TO_AGENT_HUB.ref, ASSEMBLE_BUILD.ref,), surfaces=(BUILDER_HOME_SURFACE.ref,),
)


def create_builder_feature(agents_home_ref: NodeRef) -> Feature:
    home = Node(
        id=BUILDER_HOME_REF.id, title="Agent Builds", kind=NodeKind.SECTION,
        parent=agents_home_ref,
        route=Route(template="/agents/builds", deep_link_policy=DeepLinkPolicy.SESSION_BOUND),
        context_providers=(OWNER_CONTEXT_PROVIDER,), entity_providers=(AGENT_ENTITY_PROVIDER,),
        operations=(RETURN_TO_AGENT_HUB, ASSEMBLE_BUILD),
        outgoing=(
            Transition(operation=RETURN_TO_AGENT_HUB.ref, outcome="opened", target=agents_home_ref),
            Transition(operation=ASSEMBLE_BUILD.ref, outcome="assembled", target=BUILDER_HOME_REF),
        ),
        capabilities=(BUILDER_CAPABILITY,), surfaces=SurfaceSlots(active=BUILDER_HOME_SURFACE),
    )
    return Feature(namespace="builder", nodes=(home,))


__all__ = ["BUILDER_HOME_SURFACE", "create_builder_feature"]
