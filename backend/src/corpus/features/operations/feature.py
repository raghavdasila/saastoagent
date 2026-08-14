from routedeck_core.app import Feature
from routedeck_core.contracts.application import Capability, Node
from routedeck_core.contracts.navigation import DeepLinkPolicy, NodeKind, NodeRef, Route, Transition
from routedeck_core.contracts.projection import FrozenJsonObject
from routedeck_core.contracts.surfaces import Surface, SurfaceAffordance, SurfaceLifecycle, SurfaceSlots

from corpus.auth.contracts import OWNER_CONTEXT_PROVIDER
from corpus.features.agents.contracts import AGENT_ENTITY_PROVIDER, RETURN_TO_AGENT_HUB
from corpus.shared.schemas import EMPTY_OBJECT_SCHEMA

from .contracts import OPERATIONS_HOME_REF
from .declarations import PROMOTE_INTERACTION
from .policies import EXACT_STATE, OPERATIONS_POLICIES


OPERATIONS_HOME_SURFACE = Surface(
    id="operations.home", component="operations.home", lifecycle=SurfaceLifecycle.STABLE,
    public_props_schema=FrozenJsonObject({
        "type": "object",
        "properties": {
            "selected_agent_ref": {"type": "string", "minLength": 1},
        },
        "required": ["selected_agent_ref"],
        "additionalProperties": False,
    }),
    affordances=(
        SurfaceAffordance(id="return_to_agent", event="open", operation=RETURN_TO_AGENT_HUB.ref),
        SurfaceAffordance(id="promote", event="submit", operation=PROMOTE_INTERACTION.ref),
    ),
    policy_refs=(EXACT_STATE.ref,),
)
OPERATIONS_CAPABILITY = Capability(
    id="operations.inspect", title="Inspect deployed Agent interactions",
    operations=(RETURN_TO_AGENT_HUB.ref, PROMOTE_INTERACTION.ref,), surfaces=(OPERATIONS_HOME_SURFACE.ref,),
    policy_refs=(EXACT_STATE.ref,),
)


def create_operations_feature(agents_home_ref: NodeRef) -> Feature:
    home = Node(
        id=OPERATIONS_HOME_REF.id, title="Operations", kind=NodeKind.SECTION,
        parent=agents_home_ref,
        route=Route(template="/operations", deep_link_policy=DeepLinkPolicy.SESSION_BOUND),
        context_providers=(OWNER_CONTEXT_PROVIDER,),
        entity_providers=(AGENT_ENTITY_PROVIDER,),
        operations=(RETURN_TO_AGENT_HUB, PROMOTE_INTERACTION),
        outgoing=(
            Transition(operation=RETURN_TO_AGENT_HUB.ref, outcome="opened", target=agents_home_ref),
            Transition(operation=PROMOTE_INTERACTION.ref, outcome="promoted", target=OPERATIONS_HOME_REF),
        ),
        capabilities=(OPERATIONS_CAPABILITY,), surfaces=SurfaceSlots(active=OPERATIONS_HOME_SURFACE),
        policy_refs=(EXACT_STATE.ref,),
    )
    return Feature(
        namespace="operations",
        nodes=(home,),
        agent_policies=OPERATIONS_POLICIES,
        policy_refs=tuple(item.ref for item in OPERATIONS_POLICIES),
    )

__all__ = ["OPERATIONS_HOME_SURFACE", "create_operations_feature"]
