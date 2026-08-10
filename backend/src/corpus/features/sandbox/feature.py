from routedeck_core.app import Feature
from routedeck_core.contracts.application import Capability, Node
from routedeck_core.contracts.navigation import DeepLinkPolicy, NodeKind, NodeRef, Route, Transition
from routedeck_core.contracts.projection import FrozenJsonObject
from routedeck_core.contracts.surfaces import Surface, SurfaceAffordance, SurfaceLifecycle, SurfaceSlots

from corpus.auth.contracts import OWNER_CONTEXT_PROVIDER
from corpus.features.agents.declarations import AGENT_ENTITY_PROVIDER, RETURN_TO_AGENT_HUB

from .contracts import SANDBOX_HOME_REF
from .declarations import RESUME_SANDBOX, START_SANDBOX


SANDBOX_HOME_SURFACE = Surface(
    id="sandbox.home", component="sandbox.home", lifecycle=SurfaceLifecycle.STABLE,
    public_props_schema=FrozenJsonObject({
        "type": "object", "properties": {"selected_agent_ref": {"type": "string", "minLength": 1}},
        "required": ["selected_agent_ref"], "additionalProperties": False,
    }),
    affordances=(
        SurfaceAffordance(id="return_to_agent", event="open", operation=RETURN_TO_AGENT_HUB.ref),
        SurfaceAffordance(id="start", event="submit", operation=START_SANDBOX.ref),
        SurfaceAffordance(id="resume", event="submit", operation=RESUME_SANDBOX.ref),
    ),
)
SANDBOX_CAPABILITY = Capability(
    id="sandbox.execution", title="Run one immutable Agent build in Sandbox",
    operations=(RETURN_TO_AGENT_HUB.ref, START_SANDBOX.ref, RESUME_SANDBOX.ref), surfaces=(SANDBOX_HOME_SURFACE.ref,),
)


def create_sandbox_feature(agents_home_ref: NodeRef) -> Feature:
    home = Node(
        id=SANDBOX_HOME_REF.id, title="Agent Sandbox", kind=NodeKind.SECTION,
        parent=agents_home_ref,
        route=Route(template="/agents/sandbox", deep_link_policy=DeepLinkPolicy.SESSION_BOUND),
        context_providers=(OWNER_CONTEXT_PROVIDER,), entity_providers=(AGENT_ENTITY_PROVIDER,),
        operations=(RETURN_TO_AGENT_HUB, START_SANDBOX, RESUME_SANDBOX),
        outgoing=(
            Transition(operation=RETURN_TO_AGENT_HUB.ref, outcome="opened", target=agents_home_ref),
            Transition(operation=START_SANDBOX.ref, outcome="started", target=SANDBOX_HOME_REF),
            Transition(operation=RESUME_SANDBOX.ref, outcome="resumed", target=SANDBOX_HOME_REF),
        ),
        capabilities=(SANDBOX_CAPABILITY,), surfaces=SurfaceSlots(active=SANDBOX_HOME_SURFACE),
    )
    return Feature(namespace="sandbox", nodes=(home,))


__all__ = ["SANDBOX_HOME_SURFACE", "create_sandbox_feature"]
