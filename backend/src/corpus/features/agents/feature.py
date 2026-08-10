from __future__ import annotations

from routedeck_core.app import Feature
from routedeck_core.contracts.application import Capability, Node
from routedeck_core.contracts.navigation import (
    DeepLinkPolicy,
    NodeKind,
    NodeRef,
    RecoveryPolicy,
    Route,
    Transition,
)
from routedeck_core.contracts.projection import FrozenJsonObject
from routedeck_core.contracts.suggestions import SuggestedAction
from routedeck_core.contracts.surfaces import Surface, SurfaceAffordance, SurfaceLifecycle, SurfaceSlots

from corpus.auth.contracts import OWNER_CONTEXT_PROVIDER
from corpus.shared.schemas import EMPTY_OBJECT_SCHEMA

from . import policies
from .contracts import AGENTS_CREATE_REF, AGENTS_HOME_REF
from .declarations import (
    AGENT_ENTITY_PROVIDER,
    ARCHIVE_AGENT,
    ARCHIVE_CURRENT_GUARD,
    ATTACH_CREATED_SOURCE,
    ATTACH_SOURCE,
    CANCEL_CREATE,
    CREATE_AGENT,
    DELETE_AGENT,
    DELETE_DEPENDENCIES_GUARD,
    OPEN_ATTACHED_SOURCE,
    OPEN_AGENT_BUILDS,
    OPEN_AGENT_CHANNELS,
    OPEN_AGENT_DESIGNER,
    OPEN_AGENT_EVALUATION,
    OPEN_AGENT_OPERATIONS,
    OPEN_AGENT_SANDBOX,
    OPEN_BUILD_SOURCE_REVISION,
    OPEN_CREATE,
    OPEN_SOURCE_CREATION,
    RETURN_TO_WORKSPACE,
    SAVE_AGENT_CHANGES,
    SELECT_AGENT,
)


AGENTS_HOME_SURFACE = Surface(
    id="agents.home",
    component="agents.home",
    lifecycle=SurfaceLifecycle.STABLE,
    public_props_schema=FrozenJsonObject(
        {
            "type": "object",
            "properties": {
                "selected_agent_ref": {"type": "string", "minLength": 1},
                "selected_agent_area": {
                    "type": "string",
                    "enum": ["hub", "designer", "builds", "sandbox", "evaluation", "channels"],
                },
            },
            "additionalProperties": False,
        }
    ),
    affordances=(
        SurfaceAffordance(id="open_create", event="open", operation=OPEN_CREATE.ref),
        SurfaceAffordance(id="save_changes", event="submit", operation=SAVE_AGENT_CHANGES.ref),
        SurfaceAffordance(id="return_to_workspace", event="open", operation=RETURN_TO_WORKSPACE.ref),
        SurfaceAffordance(id="select_agent", event="select", operation=SELECT_AGENT.ref),
        SurfaceAffordance(id="attach_source", event="submit", operation=ATTACH_SOURCE.ref),
        SurfaceAffordance(id="open_source_creation", event="open", operation=OPEN_SOURCE_CREATION.ref),
        SurfaceAffordance(id="open_attached_source", event="open", operation=OPEN_ATTACHED_SOURCE.ref),
        SurfaceAffordance(id="archive_agent", event="submit", operation=ARCHIVE_AGENT.ref),
        SurfaceAffordance(id="delete_agent", event="submit", operation=DELETE_AGENT.ref),
        SurfaceAffordance(id="open_operations", event="open", operation=OPEN_AGENT_OPERATIONS.ref),
        SurfaceAffordance(id="open_designer", event="open", operation=OPEN_AGENT_DESIGNER.ref),
        SurfaceAffordance(id="open_builds", event="open", operation=OPEN_AGENT_BUILDS.ref),
        SurfaceAffordance(id="open_sandbox", event="open", operation=OPEN_AGENT_SANDBOX.ref),
        SurfaceAffordance(id="open_evaluation", event="open", operation=OPEN_AGENT_EVALUATION.ref),
        SurfaceAffordance(id="open_channels", event="open", operation=OPEN_AGENT_CHANNELS.ref),
        SurfaceAffordance(id="open_build_source_revision", event="open", operation=OPEN_BUILD_SOURCE_REVISION.ref),
    ),
    policy_refs=(policies.SOURCE_PICKER_ELIGIBILITY.ref,),
)
AGENTS_CREATE_SURFACE = Surface(
    id="agents.create",
    component="agents.create",
    lifecycle=SurfaceLifecycle.STABLE,
    public_props_schema=FrozenJsonObject(EMPTY_OBJECT_SCHEMA),
    affordances=(
        SurfaceAffordance(id="create_agent", event="submit", operation=CREATE_AGENT.ref),
        SurfaceAffordance(id="cancel_create", event="open", operation=CANCEL_CREATE.ref),
    ),
)
AGENTS_ARCHIVE_REVIEW_SURFACE = Surface(
    id="agents.archive_review",
    component="agents.lifecycle_review",
    lifecycle=SurfaceLifecycle.STABLE,
    public_props_schema=FrozenJsonObject(
        {
            "type": "object",
            "properties": {
                "state": {"type": "string", "const": "pending"},
                "review_id": {"type": "string", "minLength": 1},
                "expires_at": {"type": "string", "minLength": 1},
            },
            "additionalProperties": False,
        }
    ),
    policy_refs=(policies.LIFECYCLE_REVIEW_TRUTH.ref,),
)
AGENTS_DELETE_REVIEW_SURFACE = AGENTS_ARCHIVE_REVIEW_SURFACE.model_copy(
    update={"id": "agents.delete_review"}
)
AGENT_INVENTORY = Capability(
    id="agents.inventory",
    title="Inspect and edit agents in this Workspace",
    operations=(
        OPEN_CREATE.ref,
        SAVE_AGENT_CHANGES.ref,
        RETURN_TO_WORKSPACE.ref,
        SELECT_AGENT.ref,
        ATTACH_SOURCE.ref,
        OPEN_SOURCE_CREATION.ref,
        ATTACH_CREATED_SOURCE.ref,
        OPEN_ATTACHED_SOURCE.ref,
        ARCHIVE_AGENT.ref,
        DELETE_AGENT.ref,
        OPEN_AGENT_OPERATIONS.ref,
        OPEN_AGENT_DESIGNER.ref,
        OPEN_AGENT_BUILDS.ref,
        OPEN_AGENT_SANDBOX.ref,
        OPEN_AGENT_EVALUATION.ref,
        OPEN_AGENT_CHANNELS.ref,
        OPEN_BUILD_SOURCE_REVISION.ref,
    ),
    surfaces=(AGENTS_HOME_SURFACE.ref,),
    policy_refs=(
        policies.HOME_TRUTH.ref,
        policies.VERSION_TRUTH.ref,
        policies.ATTACHMENT_ELIGIBILITY.ref,
        policies.SOURCE_HANDOFF_CONTEXT.ref,
        policies.LIFECYCLE_DEPENDENCY_TRUTH.ref,
    ),
)
AGENT_CREATION = Capability(
    id="agents.creation",
    title="Create an agent configuration",
    operations=(CREATE_AGENT.ref, CANCEL_CREATE.ref),
    surfaces=(AGENTS_CREATE_SURFACE.ref,),
    policy_refs=(policies.VERSION_TRUTH.ref,),
)


def create_agents_feature(
    workspace_home_ref: NodeRef,
    sources_home_ref: NodeRef,
    designer_home_ref: NodeRef | None = None,
    builder_home_ref: NodeRef | None = None,
    sandbox_home_ref: NodeRef | None = None,
    evaluation_home_ref: NodeRef | None = None,
    channels_home_ref: NodeRef | None = None,
    operations_home_ref: NodeRef | None = None,
) -> Feature:
    home = Node(
        id=AGENTS_HOME_REF.id,
        title="Agents",
        kind=NodeKind.SECTION,
        parent=workspace_home_ref,
        route=Route(template="/agents", deep_link_policy=DeepLinkPolicy.SESSION_BOUND),
        context_providers=(OWNER_CONTEXT_PROVIDER,),
        operations=(
            OPEN_CREATE,
            SAVE_AGENT_CHANGES,
            RETURN_TO_WORKSPACE,
            SELECT_AGENT,
            ATTACH_SOURCE,
            OPEN_SOURCE_CREATION,
            ATTACH_CREATED_SOURCE,
            OPEN_ATTACHED_SOURCE,
            ARCHIVE_AGENT,
            DELETE_AGENT,
            OPEN_AGENT_OPERATIONS,
            OPEN_AGENT_DESIGNER,
            OPEN_AGENT_BUILDS,
            OPEN_AGENT_SANDBOX,
            OPEN_AGENT_EVALUATION,
            OPEN_AGENT_CHANNELS,
            OPEN_BUILD_SOURCE_REVISION,
        ),
        outgoing=(
            Transition(operation=OPEN_CREATE.ref, outcome="opened", target=AGENTS_CREATE_REF),
            Transition(operation=SAVE_AGENT_CHANGES.ref, outcome="saved", target=AGENTS_HOME_REF),
            Transition(operation=RETURN_TO_WORKSPACE.ref, outcome="opened", target=workspace_home_ref),
            Transition(operation=SELECT_AGENT.ref, outcome="selected", target=AGENTS_HOME_REF),
            Transition(operation=ATTACH_SOURCE.ref, outcome="attached", target=AGENTS_HOME_REF),
            Transition(operation=OPEN_SOURCE_CREATION.ref, outcome="opened", target=sources_home_ref),
            Transition(operation=ATTACH_CREATED_SOURCE.ref, outcome="attached", target=AGENTS_HOME_REF),
            Transition(operation=OPEN_ATTACHED_SOURCE.ref, outcome="opened", target=sources_home_ref),
            Transition(operation=ARCHIVE_AGENT.ref, outcome="archived", target=AGENTS_HOME_REF),
            Transition(operation=DELETE_AGENT.ref, outcome="deleted", target=AGENTS_HOME_REF),
            Transition(operation=OPEN_AGENT_OPERATIONS.ref, outcome="opened", target=operations_home_ref or AGENTS_HOME_REF),
            Transition(
                operation=OPEN_AGENT_DESIGNER.ref,
                outcome="opened",
                target=designer_home_ref or AGENTS_HOME_REF,
            ),
            Transition(operation=OPEN_AGENT_BUILDS.ref, outcome="opened", target=builder_home_ref or AGENTS_HOME_REF),
            Transition(operation=OPEN_AGENT_SANDBOX.ref, outcome="opened", target=sandbox_home_ref or AGENTS_HOME_REF),
            Transition(operation=OPEN_AGENT_EVALUATION.ref, outcome="opened", target=evaluation_home_ref or AGENTS_HOME_REF),
            Transition(operation=OPEN_AGENT_CHANNELS.ref, outcome="opened", target=channels_home_ref or AGENTS_HOME_REF),
            Transition(operation=OPEN_BUILD_SOURCE_REVISION.ref, outcome="opened", target=sources_home_ref),
        ),
        capabilities=(AGENT_INVENTORY,),
        entity_providers=(AGENT_ENTITY_PROVIDER,),
        guards=(ARCHIVE_CURRENT_GUARD, DELETE_DEPENDENCIES_GUARD),
        surfaces=SurfaceSlots(
            active=AGENTS_HOME_SURFACE,
            review=(AGENTS_ARCHIVE_REVIEW_SURFACE, AGENTS_DELETE_REVIEW_SURFACE),
        ),
        suggested_actions=(
            SuggestedAction(id="agents.create", operation_id=OPEN_CREATE.id, label="Create agent"),
        ),
        policy_refs=(
            policies.HOME_TRUTH.ref,
            policies.VERSION_TRUTH.ref,
            policies.SELECTED_AGENT_TRUTH.ref,
            policies.LIFECYCLE_STATE_TRUTH.ref,
        ),
        recovery=RecoveryPolicy(
            directives=(
                "Refresh the selected Agent and its dependencies before retrying archive or deletion.",
                "A rejected or failed lifecycle action leaves the Agent and every dependency unchanged.",
            ),
            failure_surface=AGENTS_HOME_SURFACE.ref,
        ),
    )
    create = Node(
        id=AGENTS_CREATE_REF.id,
        title="Create agent",
        kind=NodeKind.SECTION,
        parent=AGENTS_HOME_REF,
        route=Route(template="/agents/new", deep_link_policy=DeepLinkPolicy.SESSION_BOUND),
        context_providers=(OWNER_CONTEXT_PROVIDER,),
        operations=(CREATE_AGENT, CANCEL_CREATE),
        outgoing=(
            Transition(operation=CREATE_AGENT.ref, outcome="created", target=AGENTS_HOME_REF),
            Transition(operation=CANCEL_CREATE.ref, outcome="opened", target=AGENTS_HOME_REF),
        ),
        capabilities=(AGENT_CREATION,),
        surfaces=SurfaceSlots(active=AGENTS_CREATE_SURFACE),
        policy_refs=(policies.VERSION_TRUTH.ref, policies.EDIT_CONFLICT.ref),
    )
    return Feature(
        namespace="agents",
        nodes=(home, create),
        agent_policies=policies.AGENTS_AGENT_POLICIES,
        policy_refs=(
            policies.FEATURE_PROMPT.ref,
            policies.OWNER_SCOPE.ref,
            policies.VERSION_TRUTH.ref,
        ),
    )


__all__ = [
    "AGENTS_CREATE_SURFACE",
    "AGENTS_HOME_SURFACE",
    "AGENTS_ARCHIVE_REVIEW_SURFACE",
    "AGENTS_DELETE_REVIEW_SURFACE",
    "create_agents_feature",
]
