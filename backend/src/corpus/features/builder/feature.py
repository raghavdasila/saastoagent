from routedeck_core.app import Feature
from routedeck_core.contracts.application import Capability, Node
from routedeck_core.contracts.navigation import DeepLinkPolicy, NodeKind, NodeRef, Route, Transition
from routedeck_core.contracts.projection import FrozenJsonObject
from routedeck_core.contracts.surfaces import Surface, SurfaceAffordance, SurfaceLifecycle, SurfaceSlots

from corpus.auth.contracts import OWNER_CONTEXT_PROVIDER
from corpus.features.agents.declarations import AGENT_ENTITY_PROVIDER, OPEN_AGENT_SANDBOX, OPEN_ATTACHED_SOURCE, RETURN_TO_AGENT_HUB
from corpus.features.sources.declarations import SOURCES_API_REF

from .contracts import BUILDER_HOME_REF
from .declarations import ASSEMBLE_BUILD, DELETE_BUILD, RUN_BUILD, STOP_BUILD
from corpus.features.evaluation.declarations import GENERATE_SET


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
        SurfaceAffordance(id="open_source_prerequisite", event="open", operation=OPEN_ATTACHED_SOURCE.ref),
        SurfaceAffordance(id="run", event="submit", operation=RUN_BUILD.ref),
        SurfaceAffordance(id="stop", event="submit", operation=STOP_BUILD.ref),
        SurfaceAffordance(id="delete", event="submit", operation=DELETE_BUILD.ref),
        SurfaceAffordance(id="generate_evaluation_set", event="submit", operation=GENERATE_SET.ref),
        SurfaceAffordance(id="continue_to_sandbox", event="open", operation=OPEN_AGENT_SANDBOX.ref),
    ),
)
BUILDER_DELETE_REVIEW_SURFACE = Surface(
    id="builder.delete_review",
    component="builder.delete_review",
    lifecycle=SurfaceLifecycle.STABLE,
    public_props_schema=FrozenJsonObject({
        "type": "object",
        "properties": {
            "state": {"type": "string", "const": "pending"},
            "review_id": {"type": "string", "minLength": 1},
            "expires_at": {"type": "string", "minLength": 1},
        },
        "additionalProperties": False,
    }),
)
BUILDER_CAPABILITY = Capability(
    id="builder.assembly", title="Assemble and control one immutable Agent build",
    operations=(
        RETURN_TO_AGENT_HUB.ref, ASSEMBLE_BUILD.ref, OPEN_ATTACHED_SOURCE.ref, RUN_BUILD.ref,
        STOP_BUILD.ref, DELETE_BUILD.ref, OPEN_AGENT_SANDBOX.ref,
        GENERATE_SET.ref,
    ),
    surfaces=(BUILDER_HOME_SURFACE.ref, BUILDER_DELETE_REVIEW_SURFACE.ref),
)


def create_builder_feature(agents_home_ref: NodeRef, sandbox_home_ref: NodeRef) -> Feature:
    home = Node(
        id=BUILDER_HOME_REF.id, title="Agent Builds", kind=NodeKind.SECTION,
        parent=agents_home_ref,
        route=Route(template="/agents/builds", deep_link_policy=DeepLinkPolicy.SESSION_BOUND),
        context_providers=(OWNER_CONTEXT_PROVIDER,), entity_providers=(AGENT_ENTITY_PROVIDER,),
        operations=(
            RETURN_TO_AGENT_HUB, ASSEMBLE_BUILD, OPEN_ATTACHED_SOURCE, RUN_BUILD,
            STOP_BUILD, DELETE_BUILD, OPEN_AGENT_SANDBOX,
            GENERATE_SET,
        ),
        outgoing=(
            Transition(operation=RETURN_TO_AGENT_HUB.ref, outcome="opened", target=agents_home_ref),
            Transition(operation=ASSEMBLE_BUILD.ref, outcome="assembled", target=BUILDER_HOME_REF),
            Transition(operation=OPEN_ATTACHED_SOURCE.ref, outcome="opened", target=SOURCES_API_REF),
            Transition(operation=RUN_BUILD.ref, outcome="running", target=BUILDER_HOME_REF),
            Transition(operation=STOP_BUILD.ref, outcome="stopped", target=BUILDER_HOME_REF),
            Transition(operation=DELETE_BUILD.ref, outcome="removed", target=BUILDER_HOME_REF),
            Transition(operation=GENERATE_SET.ref, outcome="queued", target=BUILDER_HOME_REF),
            Transition(operation=OPEN_AGENT_SANDBOX.ref, outcome="opened", target=sandbox_home_ref),
        ),
        capabilities=(BUILDER_CAPABILITY,),
        surfaces=SurfaceSlots(
            active=BUILDER_HOME_SURFACE,
            review=(BUILDER_DELETE_REVIEW_SURFACE,),
        ),
    )
    return Feature(namespace="builder", nodes=(home,))


__all__ = [
    "BUILDER_DELETE_REVIEW_SURFACE",
    "BUILDER_HOME_SURFACE",
    "create_builder_feature",
]
