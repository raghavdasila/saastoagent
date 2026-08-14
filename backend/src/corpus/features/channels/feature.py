from routedeck_core.app import Feature
from routedeck_core.contracts.application import Capability, Node
from routedeck_core.contracts.navigation import DeepLinkPolicy, NodeKind, NodeRef, RecoveryPolicy, Route, Transition
from routedeck_core.contracts.projection import FrozenJsonObject
from routedeck_core.contracts.surfaces import Surface, SurfaceAffordance, SurfaceLifecycle, SurfaceSlots

from corpus.auth.contracts import OWNER_CONTEXT_PROVIDER
from corpus.features.agents.contracts import (
    AGENT_ENTITY_PROVIDER,
    OPEN_AGENT_BUILDS,
    OPEN_AGENT_EVALUATION,
    OPEN_AGENT_OPERATIONS,
    RETURN_TO_AGENT_HUB,
)

from .contracts import CHANNELS_HOME_REF
from .declarations import CREATE_CHANNEL, SET_CHANNEL_ENABLED
from .policies import CHANNEL_POLICIES
from corpus.features.deployment.contracts import DEPLOY_AGENT, RETRY_DEPLOYMENT, ROLLBACK_DEPLOYMENT


CHANNELS_HOME_SURFACE = Surface(
    id="channels.home", component="channels.home", lifecycle=SurfaceLifecycle.STABLE,
    public_props_schema=FrozenJsonObject({
        "type": "object", "properties": {"selected_agent_ref": {"type": "string", "minLength": 1}},
        "required": ["selected_agent_ref"], "additionalProperties": False,
    }),
    affordances=(
        SurfaceAffordance(id="return_to_agent", event="open", operation=RETURN_TO_AGENT_HUB.ref),
        SurfaceAffordance(id="continue_to_evaluation", event="open", operation=OPEN_AGENT_EVALUATION.ref),
        SurfaceAffordance(id="continue_to_builds", event="open", operation=OPEN_AGENT_BUILDS.ref),
        SurfaceAffordance(id="create", event="submit", operation=CREATE_CHANNEL.ref),
        SurfaceAffordance(id="set_enabled", event="submit", operation=SET_CHANNEL_ENABLED.ref),
        SurfaceAffordance(id="deploy", event="submit", operation=DEPLOY_AGENT.ref),
        SurfaceAffordance(id="retry_deployment", event="submit", operation=RETRY_DEPLOYMENT.ref),
        SurfaceAffordance(id="rollback", event="submit", operation=ROLLBACK_DEPLOYMENT.ref),
        SurfaceAffordance(id="continue_to_operations", event="open", operation=OPEN_AGENT_OPERATIONS.ref),
    ),
)
def _review_surface(surface_id: str, component: str) -> Surface:
    return Surface(
        id=surface_id, component=component, lifecycle=SurfaceLifecycle.STABLE,
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


DEPLOY_REVIEW_SURFACE = _review_surface("deployment.deploy_review", "deployment.deploy_review")
RETRY_DEPLOYMENT_REVIEW_SURFACE = _review_surface(
    "deployment.retry_review", "deployment.retry_review"
)
ROLLBACK_REVIEW_SURFACE = _review_surface("deployment.rollback_review", "deployment.rollback_review")
AVAILABILITY_REVIEW_SURFACE = _review_surface("channels.availability_review", "channels.availability_review")
CHANNELS_CAPABILITY = Capability(
    id="channels.manage", title="Manage hosted Web channels",
    operations=(RETURN_TO_AGENT_HUB.ref, OPEN_AGENT_EVALUATION.ref, OPEN_AGENT_BUILDS.ref, CREATE_CHANNEL.ref, SET_CHANNEL_ENABLED.ref, DEPLOY_AGENT.ref, RETRY_DEPLOYMENT.ref, ROLLBACK_DEPLOYMENT.ref, OPEN_AGENT_OPERATIONS.ref),
    surfaces=(CHANNELS_HOME_SURFACE.ref,),
)


def create_channels_feature(
    agents_home_ref: NodeRef,
    builder_home_ref: NodeRef,
    evaluation_home_ref: NodeRef,
    operations_home_ref: NodeRef,
) -> Feature:
    home = Node(
        id=CHANNELS_HOME_REF.id, title="Channels and Deployment", kind=NodeKind.SECTION,
        parent=agents_home_ref,
        route=Route(template="/agents/channels", deep_link_policy=DeepLinkPolicy.SESSION_BOUND),
        context_providers=(OWNER_CONTEXT_PROVIDER,), entity_providers=(AGENT_ENTITY_PROVIDER,),
        operations=(RETURN_TO_AGENT_HUB, OPEN_AGENT_EVALUATION, OPEN_AGENT_BUILDS, CREATE_CHANNEL, SET_CHANNEL_ENABLED, DEPLOY_AGENT, RETRY_DEPLOYMENT, ROLLBACK_DEPLOYMENT, OPEN_AGENT_OPERATIONS),
        outgoing=(
            Transition(operation=RETURN_TO_AGENT_HUB.ref, outcome="opened", target=agents_home_ref),
            Transition(operation=OPEN_AGENT_EVALUATION.ref, outcome="opened", target=evaluation_home_ref),
            Transition(operation=OPEN_AGENT_BUILDS.ref, outcome="opened", target=builder_home_ref),
            Transition(operation=CREATE_CHANNEL.ref, outcome="created", target=CHANNELS_HOME_REF),
            Transition(operation=SET_CHANNEL_ENABLED.ref, outcome="availability_set", target=CHANNELS_HOME_REF),
            Transition(operation=DEPLOY_AGENT.ref, outcome="queued", target=CHANNELS_HOME_REF),
            Transition(operation=RETRY_DEPLOYMENT.ref, outcome="queued", target=CHANNELS_HOME_REF),
            Transition(operation=ROLLBACK_DEPLOYMENT.ref, outcome="rolled_back", target=CHANNELS_HOME_REF),
            Transition(operation=OPEN_AGENT_OPERATIONS.ref, outcome="opened", target=operations_home_ref),
        ),
        capabilities=(CHANNELS_CAPABILITY,),
        surfaces=SurfaceSlots(
            active=CHANNELS_HOME_SURFACE,
            review=(
                DEPLOY_REVIEW_SURFACE,
                RETRY_DEPLOYMENT_REVIEW_SURFACE,
                ROLLBACK_REVIEW_SURFACE,
                AVAILABILITY_REVIEW_SURFACE,
            ),
        ),
        recovery=RecoveryPolicy(directives=(
            "Do not retry deployment automatically. Reload the exact durable deployment status and verify the hosted activation before any new reviewed attempt.",
            "Do not retry deployment automatically. Reload the exact failed deployment and stage a new owner review only when its external outcome is definite.",
            "Do not repeat rollback automatically. Reload the channel's exact active deployment before any new reviewed action.",
            "Do not repeat an availability change automatically. Reload the exact channel state before any new reviewed action.",
        ), failure_surface=CHANNELS_HOME_SURFACE.ref),
    )
    return Feature(
        namespace="channels",
        nodes=(home,),
        agent_policies=CHANNEL_POLICIES,
        policy_refs=tuple(policy.ref for policy in CHANNEL_POLICIES),
    )


__all__ = [
    "AVAILABILITY_REVIEW_SURFACE",
    "CHANNELS_HOME_SURFACE",
    "DEPLOY_REVIEW_SURFACE",
    "RETRY_DEPLOYMENT_REVIEW_SURFACE",
    "ROLLBACK_REVIEW_SURFACE",
    "create_channels_feature",
]
