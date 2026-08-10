from routedeck_core.app import Feature
from routedeck_core.contracts.application import Capability, Node
from routedeck_core.contracts.navigation import DeepLinkPolicy, NodeKind, NodeRef, Route, Transition
from routedeck_core.contracts.projection import FrozenJsonObject
from routedeck_core.contracts.surfaces import Surface, SurfaceAffordance, SurfaceLifecycle, SurfaceSlots

from corpus.auth.contracts import OWNER_CONTEXT_PROVIDER
from corpus.features.agents.declarations import AGENT_ENTITY_PROVIDER, RETURN_TO_AGENT_HUB

from .contracts import EVALUATION_HOME_REF
from .declarations import CREATE_CASE, RUN_CASE
from .policies import EVALUATION_POLICIES, EXACT_STATE


EVALUATION_HOME_SURFACE = Surface(
    id="evaluation.home", component="evaluation.home", lifecycle=SurfaceLifecycle.STABLE,
    public_props_schema=FrozenJsonObject({
        "type": "object", "properties": {"selected_agent_ref": {"type": "string", "minLength": 1}},
        "required": ["selected_agent_ref"], "additionalProperties": False,
    }),
    affordances=(
        SurfaceAffordance(id="return_to_agent", event="open", operation=RETURN_TO_AGENT_HUB.ref),
        SurfaceAffordance(id="create_case", event="submit", operation=CREATE_CASE.ref),
        SurfaceAffordance(id="run_case", event="submit", operation=RUN_CASE.ref),
    ),
    policy_refs=(EXACT_STATE.ref,),
)
EVALUATION_CAPABILITY = Capability(
    id="evaluation.manage", title="Manage exact-build evaluation cases and eligibility",
    operations=(RETURN_TO_AGENT_HUB.ref, CREATE_CASE.ref, RUN_CASE.ref), surfaces=(EVALUATION_HOME_SURFACE.ref,),
    policy_refs=(EXACT_STATE.ref,),
)


def create_evaluation_feature(agents_home_ref: NodeRef) -> Feature:
    home = Node(
        id=EVALUATION_HOME_REF.id, title="Evaluation", kind=NodeKind.SECTION,
        parent=agents_home_ref,
        route=Route(template="/agents/evaluation", deep_link_policy=DeepLinkPolicy.SESSION_BOUND),
        context_providers=(OWNER_CONTEXT_PROVIDER,), entity_providers=(AGENT_ENTITY_PROVIDER,),
        operations=(RETURN_TO_AGENT_HUB, CREATE_CASE, RUN_CASE),
        outgoing=(
            Transition(operation=RETURN_TO_AGENT_HUB.ref, outcome="opened", target=agents_home_ref),
            Transition(operation=CREATE_CASE.ref, outcome="created", target=EVALUATION_HOME_REF),
            Transition(operation=RUN_CASE.ref, outcome="evaluated", target=EVALUATION_HOME_REF),
        ),
        capabilities=(EVALUATION_CAPABILITY,), surfaces=SurfaceSlots(active=EVALUATION_HOME_SURFACE),
        policy_refs=(EXACT_STATE.ref,),
    )
    return Feature(
        namespace="evaluation",
        nodes=(home,),
        agent_policies=EVALUATION_POLICIES,
        policy_refs=tuple(item.ref for item in EVALUATION_POLICIES),
    )

__all__ = ["EVALUATION_HOME_SURFACE", "create_evaluation_feature"]
