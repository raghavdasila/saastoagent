from routedeck_core.app import Feature
from routedeck_core.contracts.application import Capability, Node
from routedeck_core.contracts.navigation import DeepLinkPolicy, NodeKind, NodeRef, Route, Transition
from routedeck_core.contracts.projection import FrozenJsonObject
from routedeck_core.contracts.surfaces import Surface, SurfaceAffordance, SurfaceLifecycle, SurfaceSlots

from corpus.auth.contracts import OWNER_CONTEXT_PROVIDER
from corpus.features.agents.contracts import (
    AGENT_ENTITY_PROVIDER,
    OPEN_AGENT_BUILDS,
    OPEN_AGENT_CHANNELS,
    RETURN_TO_AGENT_HUB,
)

from .contracts import EVALUATION_HOME_REF
from .declarations import CREATE_CASE, DELETE_CASE, EDIT_CASE, GENERATE_SET, RETRY_CASE_RUN, RETRY_GENERATION, RUN_CASE
from .policies import EVALUATION_POLICIES, EXACT_STATE


EVALUATION_HOME_SURFACE = Surface(
    id="evaluation.home", component="evaluation.home", lifecycle=SurfaceLifecycle.STABLE,
    public_props_schema=FrozenJsonObject({
        "type": "object", "properties": {"selected_agent_ref": {"type": "string", "minLength": 1}},
        "required": ["selected_agent_ref"], "additionalProperties": False,
    }),
    affordances=(
        SurfaceAffordance(id="return_to_agent", event="open", operation=RETURN_TO_AGENT_HUB.ref),
        SurfaceAffordance(id="continue_to_builds", event="open", operation=OPEN_AGENT_BUILDS.ref),
        SurfaceAffordance(id="create_case", event="submit", operation=CREATE_CASE.ref),
        SurfaceAffordance(id="generate_set", event="submit", operation=GENERATE_SET.ref),
        SurfaceAffordance(id="retry_generation", event="submit", operation=RETRY_GENERATION.ref),
        SurfaceAffordance(id="edit_case", event="submit", operation=EDIT_CASE.ref),
        SurfaceAffordance(id="delete_case", event="submit", operation=DELETE_CASE.ref),
        SurfaceAffordance(id="run_case", event="submit", operation=RUN_CASE.ref),
        SurfaceAffordance(id="retry_case_run", event="submit", operation=RETRY_CASE_RUN.ref),
        SurfaceAffordance(id="continue_to_channels", event="open", operation=OPEN_AGENT_CHANNELS.ref),
    ),
    policy_refs=(EXACT_STATE.ref,),
)
EVALUATION_DELETE_REVIEW_SURFACE = Surface(
    id="evaluation.delete_case_review",
    component="evaluation.delete_case_review",
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
EVALUATION_CAPABILITY = Capability(
    id="evaluation.manage", title="Manage exact-build evaluation cases and eligibility",
    operations=(
        RETURN_TO_AGENT_HUB.ref, OPEN_AGENT_BUILDS.ref, GENERATE_SET.ref, RETRY_GENERATION.ref,
        CREATE_CASE.ref, EDIT_CASE.ref, DELETE_CASE.ref, RUN_CASE.ref,
        RETRY_CASE_RUN.ref,
        OPEN_AGENT_CHANNELS.ref,
    ),
    surfaces=(EVALUATION_HOME_SURFACE.ref, EVALUATION_DELETE_REVIEW_SURFACE.ref),
    policy_refs=(EXACT_STATE.ref,),
)


def create_evaluation_feature(
    agents_home_ref: NodeRef,
    builder_home_ref: NodeRef,
    channels_home_ref: NodeRef,
) -> Feature:
    home = Node(
        id=EVALUATION_HOME_REF.id, title="Evaluation", kind=NodeKind.SECTION,
        parent=agents_home_ref,
        route=Route(template="/agents/evaluation", deep_link_policy=DeepLinkPolicy.SESSION_BOUND),
        context_providers=(OWNER_CONTEXT_PROVIDER,), entity_providers=(AGENT_ENTITY_PROVIDER,),
        operations=(
            RETURN_TO_AGENT_HUB, OPEN_AGENT_BUILDS, GENERATE_SET, RETRY_GENERATION,
            CREATE_CASE, EDIT_CASE, DELETE_CASE, RUN_CASE, OPEN_AGENT_CHANNELS,
            RETRY_CASE_RUN,
        ),
        outgoing=(
            Transition(operation=RETURN_TO_AGENT_HUB.ref, outcome="opened", target=agents_home_ref),
            Transition(operation=OPEN_AGENT_BUILDS.ref, outcome="opened", target=builder_home_ref),
            Transition(operation=CREATE_CASE.ref, outcome="created", target=EVALUATION_HOME_REF),
            Transition(operation=GENERATE_SET.ref, outcome="queued", target=EVALUATION_HOME_REF),
            Transition(operation=RETRY_GENERATION.ref, outcome="queued", target=EVALUATION_HOME_REF),
            Transition(operation=EDIT_CASE.ref, outcome="edited", target=EVALUATION_HOME_REF),
            Transition(operation=DELETE_CASE.ref, outcome="removed", target=EVALUATION_HOME_REF),
            Transition(operation=RUN_CASE.ref, outcome="queued", target=EVALUATION_HOME_REF),
            Transition(operation=RETRY_CASE_RUN.ref, outcome="queued", target=EVALUATION_HOME_REF),
            Transition(operation=OPEN_AGENT_CHANNELS.ref, outcome="opened", target=channels_home_ref),
        ),
        capabilities=(EVALUATION_CAPABILITY,),
        surfaces=SurfaceSlots(
            active=EVALUATION_HOME_SURFACE,
            review=(EVALUATION_DELETE_REVIEW_SURFACE,),
        ),
        policy_refs=(EXACT_STATE.ref,),
    )
    return Feature(
        namespace="evaluation",
        nodes=(home,),
        agent_policies=EVALUATION_POLICIES,
        policy_refs=tuple(item.ref for item in EVALUATION_POLICIES),
    )

__all__ = ["EVALUATION_DELETE_REVIEW_SURFACE", "EVALUATION_HOME_SURFACE", "create_evaluation_feature"]
