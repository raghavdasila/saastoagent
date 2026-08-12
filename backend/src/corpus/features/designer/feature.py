from __future__ import annotations

from routedeck_core.app import Feature
from routedeck_core.contracts.application import Capability, Node
from routedeck_core.contracts.navigation import DeepLinkPolicy, NodeKind, NodeRef, Route, Transition
from routedeck_core.contracts.projection import FrozenJsonObject
from routedeck_core.contracts.surfaces import Surface, SurfaceAffordance, SurfaceLifecycle, SurfaceSlots

from corpus.auth.contracts import OWNER_CONTEXT_PROVIDER
from corpus.features.agents.declarations import (
    AGENT_ENTITY_PROVIDER,
    OPEN_AGENT_BUILDS,
    OPEN_ATTACHED_SOURCE,
)

from .contracts import DESIGNER_HOME_REF
from .declarations import APPROVE_DESIGN, CUSTOMIZE_DESIGN, DESIGN_CURRENT_PROVIDER, GENERATE_FEATURE, PROPOSE_DESIGN, REQUEST_BUILD, RETURN_TO_AGENT
from . import policies
from .policies import DESIGNER_POLICIES


DESIGNER_HOME_SURFACE = Surface(
    id="designer.home",
    component="designer.home",
    lifecycle=SurfaceLifecycle.STABLE,
    public_props_schema=FrozenJsonObject({
        "type": "object",
        "properties": {"selected_agent_ref": {"type": "string", "minLength": 1}},
        "required": ["selected_agent_ref"],
        "additionalProperties": False,
    }),
    affordances=(
        SurfaceAffordance(id="propose", event="submit", operation=PROPOSE_DESIGN.ref),
        SurfaceAffordance(id="generate_feature", event="submit", operation=GENERATE_FEATURE.ref),
        SurfaceAffordance(id="customize", event="submit", operation=CUSTOMIZE_DESIGN.ref),
        SurfaceAffordance(id="approve", event="submit", operation=APPROVE_DESIGN.ref),
        SurfaceAffordance(id="request_build", event="submit", operation=REQUEST_BUILD.ref),
        SurfaceAffordance(id="open_source_prerequisite", event="open", operation=OPEN_ATTACHED_SOURCE.ref),
        SurfaceAffordance(id="continue_to_builds", event="open", operation=OPEN_AGENT_BUILDS.ref),
        SurfaceAffordance(id="return_to_agent", event="open", operation=RETURN_TO_AGENT.ref),
    ),
    policy_refs=(policies.EXACT_INPUTS.ref, policies.IMMUTABLE_REVISIONS.ref),
)
DESIGNER_REVIEW_SURFACE = Surface(
    id="designer.review",
    component="designer.review",
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
    policy_refs=(policies.EXACT_REVIEW.ref, policies.EXACT_BUILD_REQUEST.ref),
)
DESIGNER_AUTHORING = Capability(
    id="designer.authoring",
    title="Propose, customize, approve, and request an Agent build",
    operations=(PROPOSE_DESIGN.ref, GENERATE_FEATURE.ref, CUSTOMIZE_DESIGN.ref, APPROVE_DESIGN.ref, REQUEST_BUILD.ref, OPEN_ATTACHED_SOURCE.ref, OPEN_AGENT_BUILDS.ref, RETURN_TO_AGENT.ref),
    surfaces=(DESIGNER_HOME_SURFACE.ref, DESIGNER_REVIEW_SURFACE.ref),
    policy_refs=tuple(item.ref for item in DESIGNER_POLICIES[1:6]),
)


def create_designer_feature(
    agents_home_ref: NodeRef,
    builder_home_ref: NodeRef,
    sources_api_ref: NodeRef,
) -> Feature:
    home = Node(
        id=DESIGNER_HOME_REF.id,
        title="Agent Designer",
        kind=NodeKind.SECTION,
        parent=agents_home_ref,
        route=Route(template="/agents/designer", deep_link_policy=DeepLinkPolicy.SESSION_BOUND),
        context_providers=(OWNER_CONTEXT_PROVIDER, DESIGN_CURRENT_PROVIDER),
        entity_providers=(AGENT_ENTITY_PROVIDER,),
        operations=(PROPOSE_DESIGN, GENERATE_FEATURE, CUSTOMIZE_DESIGN, APPROVE_DESIGN, REQUEST_BUILD, OPEN_ATTACHED_SOURCE, OPEN_AGENT_BUILDS, RETURN_TO_AGENT),
        outgoing=(
            Transition(operation=PROPOSE_DESIGN.ref, outcome="proposed", target=DESIGNER_HOME_REF),
            Transition(operation=GENERATE_FEATURE.ref, outcome="generated", target=DESIGNER_HOME_REF),
            Transition(operation=CUSTOMIZE_DESIGN.ref, outcome="customized", target=DESIGNER_HOME_REF),
            Transition(operation=APPROVE_DESIGN.ref, outcome="accepted", target=DESIGNER_HOME_REF),
            Transition(operation=REQUEST_BUILD.ref, outcome="requested", target=DESIGNER_HOME_REF),
            Transition(operation=OPEN_ATTACHED_SOURCE.ref, outcome="opened", target=sources_api_ref),
            Transition(operation=OPEN_AGENT_BUILDS.ref, outcome="opened", target=builder_home_ref),
            Transition(operation=RETURN_TO_AGENT.ref, outcome="opened", target=agents_home_ref),
        ),
        capabilities=(DESIGNER_AUTHORING,),
        surfaces=SurfaceSlots(active=DESIGNER_HOME_SURFACE, review=(DESIGNER_REVIEW_SURFACE,)),
        policy_refs=tuple(item.ref for item in DESIGNER_POLICIES[1:6]),
    )
    return Feature(
        namespace="designer",
        nodes=(home,),
        agent_policies=DESIGNER_POLICIES,
        policy_refs=tuple(item.ref for item in DESIGNER_POLICIES),
    )


__all__ = ["DESIGNER_HOME_SURFACE", "DESIGNER_REVIEW_SURFACE", "create_designer_feature"]
