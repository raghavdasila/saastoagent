from __future__ import annotations

from routedeck_core.contracts.agent import AgentPolicyRef
from routedeck_core.contracts.operations import (
    ContextProvider,
    EntityInput,
    EntityProvider,
    Guard,
    Operation,
    OperationSource,
    ProviderRef,
    ReviewPolicy,
    SafetyClass,
)
from routedeck_core.contracts.projection import FrozenJsonObject

from corpus.auth.contracts import OWNER_CONTEXT_PROVIDER
from corpus.shared.schemas import EMPTY_OBJECT_SCHEMA

from . import policies
from .schemas import (
    AgentLifecycleArguments,
    AttachSourceArguments,
    DetachSourceArguments,
    CreateAgentArguments,
    OpenAgentChoiceForSourceArguments,
    OpenAgentCreationArguments,
    SelectAgentArguments,
    OpenBuildSourceReferenceArguments,
    OpenAttachedSourceArguments,
    UpdateAgentArguments,
)


AGENT_ENTITY_PROVIDER = EntityProvider(
    id="agents.selected_agent",
    entity_kind="agent",
    description="The exact selected Agent binding already retained in the RouteDeck session.",
    output_schema=FrozenJsonObject(EMPTY_OBJECT_SCHEMA),
)
SELECTED_AGENT_OVERVIEW_PROVIDER = ContextProvider(
    id="agents.selected_overview",
    description=(
        "Authoritative current product lifecycle summary for the exact selected Agent."
    ),
    output_schema=FrozenJsonObject(
        {
            "type": "object",
            "properties": {
                "agent_id": {"type": "string", "format": "uuid"},
                "agent_version": {"type": "integer", "minimum": 1},
                "source_count": {"type": "integer", "minimum": 0},
                "design_status": {"type": "string", "enum": ["missing", "draft", "accepted"]},
                "design_revision": {"type": ["integer", "null"], "minimum": 1},
                "build_status": {"type": ["string", "null"]},
                "build_runtime_lifecycle": {"type": ["string", "null"]},
                "evaluation_status": {"type": ["string", "null"]},
                "evaluation_case_count": {"type": "integer", "minimum": 0},
                "evaluation_eligible": {"type": ["boolean", "null"]},
                "delivery_status": {
                    "type": "string",
                    "enum": ["none", "channel_only", "deploying", "live", "disabled", "failed"],
                },
                "hosted_path": {"type": ["string", "null"]},
                "operations_count": {"type": "integer", "minimum": 0},
                "next_step": {"type": "string"},
            },
            "additionalProperties": False,
        }
    ),
)
PENDING_SOURCE_CONTEXT_PROVIDER = ContextProvider(
    id="agents.pending_source",
    description=(
        "The exact ready Source and analyzed API version retained while the owner "
        "chooses or creates an Agent."
    ),
    output_schema=FrozenJsonObject(
        {
            "type": "object",
            "properties": {
                "source_id": {"type": "string", "minLength": 16, "maxLength": 16},
                "source_revision_id": {"type": "string", "minLength": 16, "maxLength": 16},
                "display_name": {"type": "string", "minLength": 1, "maxLength": 240},
            },
            "additionalProperties": False,
        }
    ),
)
ARCHIVE_CURRENT_GUARD = Guard(
    id="agents.archive_current",
    description="Requires the exact selected Agent to remain active at review and acceptance time.",
)
DELETE_DEPENDENCIES_GUARD = Guard(
    id="agents.delete_dependencies_clear",
    description="Requires the exact selected active Agent to have no declared dependencies at review and acceptance time.",
)


def operation(
    operation_id: str,
    title: str,
    description: str,
    outcome: str,
    *,
    input_schema: dict = EMPTY_OBJECT_SCHEMA,
    safety_class: SafetyClass = SafetyClass.NAVIGATION,
    sources: frozenset[OperationSource] = frozenset(
        {OperationSource.AGENT, OperationSource.SURFACE}
    ),
    entity_inputs: tuple[EntityInput, ...] = (),
    review_policy: ReviewPolicy = ReviewPolicy.NONE,
    guard_refs=(),
    policy_refs: tuple[AgentPolicyRef, ...] = (),
    public_metadata: dict | None = None,
    additional_provider_refs=(),
) -> Operation:
    return Operation(
        id=operation_id,
        title=title,
        description=description,
        input_schema=FrozenJsonObject(input_schema),
        safety_class=safety_class,
        allowed_sources=sources,
        outcomes=(outcome,),
        outcome_schemas=FrozenJsonObject({outcome: EMPTY_OBJECT_SCHEMA}),
        provider_refs=(OWNER_CONTEXT_PROVIDER.ref, *additional_provider_refs),
        entity_inputs=entity_inputs,
        review_policy=review_policy,
        guard_refs=guard_refs,
        policy_refs=policy_refs,
        public_metadata=FrozenJsonObject(public_metadata or {}),
    )


OPEN_CREATE = operation(
    "agents.open_create",
    "Open agent creation",
    (
        "Begin a distinct new-Agent configuration only when the owner's current "
        "request still needs a new Agent. This navigation creates nothing and must "
        "not follow a successful agent creation for that same request."
    ),
    "opened",
    input_schema=OpenAgentCreationArguments.model_json_schema(),
    policy_refs=(policies.OPEN_CREATE_SETUP.ref,),
)
OPEN_EXISTING_AGENT_FOR_SOURCE = operation(
    "agents.choose_existing_for_source",
    "Choose existing Agent for this Source",
    (
        "Open the Agent inventory with the exact ready Source and analyzed API version "
        "retained as the pending attachment. Navigation attaches nothing."
    ),
    "opened",
    input_schema=OpenAgentChoiceForSourceArguments.model_json_schema(),
    policy_refs=(policies.CHOOSE_EXISTING_SOURCE_CONTEXT.ref,),
)
RETURN_TO_WORKSPACE = operation(
    "agents.return_to_workspace",
    "Return to Workspace",
    "Return to the authenticated Workspace overview.",
    "opened",
)
RETURN_TO_AGENT_HUB = operation(
    "agents.return_to_hub",
    "Return to selected Agent",
    (
        "Return to the exact selected Agent hub when the owner asks to move from the current "
        "area to another selected-agent work area, including design, builds, a private trial, "
        "evaluation, hosted delivery, or deployed interaction evidence. This navigation does "
        "not change downstream work."
    ),
    "opened",
    input_schema=AgentLifecycleArguments.model_json_schema(),
    entity_inputs=(EntityInput(argument_name="agent_ref", entity_kind="agent"),),
)
CREATE_AGENT = operation(
    "agents.create_agent",
    "Create agent",
    (
        "Create an active agent with configuration version 1. During an ongoing file-first setup, "
        "when the owner has chosen creation and supplied a clear role phrase and responsibilities "
        "but no separate display name, derive a concise display name from the owner's exact role "
        "phrase and map only the stated responsibilities into description and instructions; do not "
        "invent capabilities. Otherwise ask for any genuinely missing required identity input."
    ),
    "created",
    input_schema=CreateAgentArguments.model_json_schema(),
    safety_class=SafetyClass.DRAFT,
    additional_provider_refs=(PENDING_SOURCE_CONTEXT_PROVIDER.ref,),
)
SAVE_AGENT_CHANGES = operation(
    "agents.save_changes",
    "Save agent changes",
    "Create the next immutable configuration version for the selected agent.",
    "saved",
    input_schema=UpdateAgentArguments.model_json_schema(),
    safety_class=SafetyClass.DRAFT,
)
CANCEL_CREATE = operation(
    "agents.cancel_create",
    "Cancel agent creation",
    "Return to the agent inventory without creating an agent.",
    "opened",
    additional_provider_refs=(PENDING_SOURCE_CONTEXT_PROVIDER.ref,),
)
SELECT_AGENT = operation(
    "agents.select_agent",
    "Select agent",
    "Select one owner-scoped Agent for attachment work.",
    "selected",
    input_schema=SelectAgentArguments.model_json_schema(),
    safety_class=SafetyClass.STATE_SELECTION,
    additional_provider_refs=(PENDING_SOURCE_CONTEXT_PROVIDER.ref,),
)
ATTACH_SOURCE = operation(
    "agents.attach_source",
    "Attach Source to Agent",
    (
        "Pin the exact ready API version chosen by the owner to the selected Agent, keeping "
        "one attachment per Source. Repeating the same current version is idempotent; when that "
        "Source has a newer reviewed ready API version, advance its pinned revision without changing "
        "historical build lineage. When source_id is omitted, resolve only one eligible ready Source "
        "that is unattached or pinned to an earlier version, and only when the owner's ongoing setup "
        "request authorizes that exact attachment."
    ),
    "attached",
    input_schema=AttachSourceArguments.model_json_schema(),
    safety_class=SafetyClass.DRAFT,
    entity_inputs=(EntityInput(argument_name="agent_ref", entity_kind="agent"),),
    additional_provider_refs=(PENDING_SOURCE_CONTEXT_PROVIDER.ref,),
    policy_refs=(
        policies.ATTACH_EXACT_SOURCE.ref,
        policies.ATTACH_PERSISTED_SUCCESS.ref,
        policies.SETUP_ATTACH_READY.ref,
    ),
)
DETACH_SOURCE = operation(
    "agents.detach_source",
    "Detach Source from Agent",
    (
        "Remove only the exact current Source association selected by the owner from the "
        "selected Agent. Preserve the Source and every immutable accepted design, historical "
        "build, runtime, deployment, and Operations record."
    ),
    "detached",
    input_schema=DetachSourceArguments.model_json_schema(),
    safety_class=SafetyClass.DRAFT,
    entity_inputs=(EntityInput(argument_name="agent_ref", entity_kind="agent"),),
    policy_refs=(policies.DETACH_EXACT_SOURCE.ref, policies.DETACH_PERSISTED_SUCCESS.ref),
)
OPEN_SOURCE_CREATION = operation(
    "agents.open_source_creation",
    "Create and attach a Source",
    "Begin intake for a new API definition the owner wants to add to the selected Agent, retaining that Agent and making no attachment yet.",
    "opened",
    input_schema={
        "type": "object",
        "properties": {"agent_ref": {"type": "string", "minLength": 1}},
        "required": ["agent_ref"],
        "additionalProperties": False,
    },
    entity_inputs=(EntityInput(argument_name="agent_ref", entity_kind="agent"),),
    policy_refs=(policies.SOURCE_CREATION_NAVIGATION.ref,),
)
ATTACH_CREATED_SOURCE = operation(
    "agents.attach_created_source",
    "Attach Source created from this Agent",
    (
        "Pin the newly created ready API version and return to the selected Agent only when "
        "Source creation was opened from that already-existing selected Agent and the Source is "
        "not already attached. Never use this operation in a file-first setup where the Agent "
        "did not exist when Source intake began; use the regular eligible Source attachment after "
        "creating that Agent. Never use it after updating or reviewing an API version already "
        "attached to the Agent."
    ),
    "attached",
    input_schema=AttachSourceArguments.model_json_schema(),
    safety_class=SafetyClass.DRAFT,
    entity_inputs=(EntityInput(argument_name="agent_ref", entity_kind="agent"),),
    policy_refs=(policies.ATTACH_CREATED_ELIGIBILITY.ref,),
)
OPEN_ATTACHED_SOURCE = operation(
    "agents.open_attached_source",
    "Open attached Source",
    (
        "Open one exact persisted Source attachment in Source Hub. This opens the API version "
        "currently pinned to the Agent; after a newer API version is accepted, do not use this "
        "operation to remain with or continue setting up that newer version."
    ),
    "opened",
    input_schema=OpenAttachedSourceArguments.model_json_schema(),
    entity_inputs=(EntityInput(argument_name="agent_ref", entity_kind="agent"),),
    policy_refs=(policies.OPEN_SOURCE_CONTEXT.ref,),
)
ARCHIVE_AGENT = operation(
    "agents.archive_agent",
    "Archive agent",
    "Move the reviewed exact active Agent out of the active inventory without deleting it.",
    "archived",
    input_schema=AgentLifecycleArguments.model_json_schema(),
    safety_class=SafetyClass.DESTRUCTIVE,
    entity_inputs=(EntityInput(argument_name="agent_ref", entity_kind="agent"),),
    review_policy=ReviewPolicy.REQUIRED,
    guard_refs=(ARCHIVE_CURRENT_GUARD.ref,),
    policy_refs=(policies.ARCHIVE_EXACT_AGENT.ref, policies.LIFECYCLE_PERSISTED_SUCCESS.ref),
    public_metadata={"review_surface_id": "agents.archive_review"},
)
DELETE_AGENT = operation(
    "agents.delete_agent",
    "Delete agent",
    "Permanently delete the reviewed exact active Agent only when declared dependencies permit it.",
    "deleted",
    input_schema=AgentLifecycleArguments.model_json_schema(),
    safety_class=SafetyClass.DESTRUCTIVE,
    entity_inputs=(EntityInput(argument_name="agent_ref", entity_kind="agent"),),
    review_policy=ReviewPolicy.REQUIRED,
    guard_refs=(DELETE_DEPENDENCIES_GUARD.ref,),
    policy_refs=(policies.DELETE_EXACT_AGENT.ref, policies.LIFECYCLE_PERSISTED_SUCCESS.ref),
    public_metadata={"review_surface_id": "agents.delete_review"},
)
RETURN_FROM_SOURCE = operation(
    "agents.return_from_source",
    "Return to selected Agent",
    (
        "Return from Source Hub to the selected Agent without changing either record. "
        "Use this only when the owner explicitly asks to leave the current API setup and return "
        "to the selected Agent, or explicitly asks for an Agent action that cannot be completed in "
        "API Source. If the owner asks to remain with the current API, continue its setup, or choose "
        "what it may access, do not use this operation. Returning never attaches or updates a Source."
    ),
    "opened",
    input_schema={
        "type": "object",
        "properties": {"agent_ref": {"type": "string", "minLength": 1}},
        "required": ["agent_ref"],
        "additionalProperties": False,
    },
    entity_inputs=(EntityInput(argument_name="agent_ref", entity_kind="agent"),),
    additional_provider_refs=(ProviderRef(id="sources.selected_api_source"),),
)

OPEN_AGENT_OPERATIONS = operation(
    "agents.open_operations",
    "Open agent operations",
    (
        "Open owner-only deployed interaction history, redacted execution evidence, and "
        "exact build/deployment lineage for the selected Agent. Use this when the owner asks "
        "how a completed public request ran."
    ),
    "opened",
    input_schema=AgentLifecycleArguments.model_json_schema(),
    entity_inputs=(EntityInput(argument_name="agent_ref", entity_kind="agent"),),
)
OPEN_AGENT_DESIGNER = operation(
    "agents.open_designer",
    "Open Agent Designer",
    "Open Designer context for the exact selected Agent without changing a design. Use it to propose, customize, review, accept, or request a design build; do not use it to assemble a build whose request already exists.",
    "opened",
    input_schema=AgentLifecycleArguments.model_json_schema(),
    entity_inputs=(EntityInput(argument_name="agent_ref", entity_kind="agent"),),
)
OPEN_AGENT_BUILDS = operation(
    "agents.open_builds",
    "Open Agent Builds",
    "Continue the selected Agent's current task in immutable build history without starting a build. Use this legal navigation after an accepted Designer build request when the owner asks for a runnable build; reaching Builds is not task completion.",
    "opened",
    input_schema=AgentLifecycleArguments.model_json_schema(),
    entity_inputs=(EntityInput(argument_name="agent_ref", entity_kind="agent"),),
)
OPEN_AGENT_SANDBOX = operation(
    "agents.open_sandbox",
    "Open Agent Sandbox",
    (
        "Open or view Sandbox context for the exact selected Agent without starting a "
        "Sandbox run. This navigation does not start, enable, or resume a stopped build "
        "runtime; that separate build lifecycle action must complete first. Use this only "
        "after that prerequisite when the owner asks to continue into a private trial."
    ),
    "opened",
    input_schema=AgentLifecycleArguments.model_json_schema(),
    entity_inputs=(EntityInput(argument_name="agent_ref", entity_kind="agent"),),
)
OPEN_AGENT_EVALUATION = operation(
    "agents.open_evaluation",
    "Open Agent Evaluation",
    (
        "Open Evaluation context for the exact selected Agent. Use this when the owner asks "
        "to keep a private trial as an evaluation case or check a build against saved cases; "
        "opening the context alone does not start an evaluation."
    ),
    "opened",
    input_schema=AgentLifecycleArguments.model_json_schema(),
    entity_inputs=(EntityInput(argument_name="agent_ref", entity_kind="agent"),),
)
OPEN_AGENT_CHANNELS = operation(
    "agents.open_channels",
    "Open Agent Channels",
    (
        "Open hosted channel, deployment, rollback, and availability configuration for the "
        "selected Agent. Use this when the owner asks to set up a hosted address or publish "
        "an eligible build. Do not use this to inspect how a completed public request ran."
    ),
    "opened",
    input_schema=AgentLifecycleArguments.model_json_schema(),
    entity_inputs=(EntityInput(argument_name="agent_ref", entity_kind="agent"),),
)
OPEN_BUILD_SOURCE_REVISION = operation(
    "agents.open_build_source_revision",
    "Open referenced API version",
    "Open only the exact API version retained by one immutable historical build.",
    "opened",
    input_schema=OpenBuildSourceReferenceArguments.model_json_schema(),
    entity_inputs=(EntityInput(argument_name="agent_ref", entity_kind="agent"),),
)

__all__ = [
    "AGENT_ENTITY_PROVIDER",
    "ARCHIVE_AGENT",
    "ARCHIVE_CURRENT_GUARD",
    "ATTACH_CREATED_SOURCE",
    "ATTACH_SOURCE",
    "DETACH_SOURCE",
    "CANCEL_CREATE",
    "CREATE_AGENT",
    "DELETE_AGENT",
    "DELETE_DEPENDENCIES_GUARD",
    "OPEN_ATTACHED_SOURCE",
    "OPEN_AGENT_BUILDS",
    "OPEN_AGENT_CHANNELS",
    "OPEN_AGENT_DESIGNER",
    "OPEN_AGENT_EVALUATION",
    "OPEN_AGENT_OPERATIONS",
    "OPEN_AGENT_SANDBOX",
    "OPEN_BUILD_SOURCE_REVISION",
    "OPEN_CREATE",
    "OPEN_EXISTING_AGENT_FOR_SOURCE",
    "OPEN_SOURCE_CREATION",
    "RETURN_FROM_SOURCE",
    "RETURN_TO_AGENT_HUB",
    "RETURN_TO_WORKSPACE",
    "SAVE_AGENT_CHANGES",
    "SELECT_AGENT",
    "PENDING_SOURCE_CONTEXT_PROVIDER",
]
