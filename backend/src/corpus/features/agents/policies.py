from routedeck_core.contracts.agent import AgentPolicy

from .prompt import AGENTS_AGENT_PROMPT


def policy(policy_id: str, instruction: str) -> AgentPolicy:
    return AgentPolicy(id=policy_id, instruction=instruction)


FEATURE_PROMPT = policy("agents.feature.prompt", AGENTS_AGENT_PROMPT)
OWNER_SCOPE = policy(
    "agents.feature.owner_scope",
    "Use only agents owned by the authenticated organization in the current Workspace.",
)
VERSION_TRUTH = policy(
    "agents.feature.version_truth",
    "Keep current configuration, immutable historical versions, and deployment state distinct.",
)
HOME_TRUTH = policy(
    "agents.node.inventory_truth",
    "Show authoritative agents or a truthful empty state; never invent agents or activity.",
)
EDIT_CONFLICT = policy(
    "agents.node.edit_conflict",
    "A stale edit is a visible version conflict and must never overwrite a newer configuration.",
)
SELECTED_AGENT_TRUTH = policy(
    "agents.node.selected_agent_truth",
    "Keep every presented or changed fact bound to the exact selected agent.",
)
LIFECYCLE_STATE_TRUTH = policy(
    "agents.node.lifecycle_state_truth",
    "Keep current configuration, historical runnable versions, and active deployment state distinct.",
)
ATTACHMENT_ELIGIBILITY = policy(
    "agents.capability.attachment_eligibility",
    (
        "Attach only eligible sources from the same Workspace and keep one attachment per Source. "
        "Repeating the same current revision is idempotent; when the owner's ongoing setup reaches "
        "a newer reviewed ready API version, advance only that Source's pinned revision without "
        "rewriting immutable build lineage."
    ),
)
SOURCE_HANDOFF_CONTEXT = policy(
    "agents.capability.source_handoff_context",
    "Preserve the selected agent across Source Hub and API Source handoffs; navigation alone does not attach or edit a source.",
)
SETUP_CONTINUATION = policy(
    "agents.capability.setup_continuation",
    (
        "When an owner asks to set up an Agent from the API definition already added in this "
        "conversation, preserve that task across Source and Agent areas. Ask only for missing "
        "agent choice, goal, responsibilities, or operation-selection intent; create an Agent "
        "only after the owner chooses creation. When the owner supplies a clear role phrase and "
        "responsibilities but omits a separate display name during this continuation, derive a "
        "concise display name from that exact role phrase and map only the stated responsibilities "
        "into the Agent configuration; do not ask another question solely for a name and do not "
        "invent capabilities. Attach only the exact ready authorized Source."
    ),
)
SETUP_ATTACH_READY = policy(
    "agents.operation.setup_attach_ready",
    (
        "For an ongoing file-first setup request, attach only the exact ready Source the owner "
        "authorized after the Agent choice and required Agent details are established. Never "
        "invent operation selection or treat queued analysis as ready. If that Source is already "
        "attached to an earlier API version, advance its single attachment to the exact current "
        "reviewed ready version; do not create a duplicate attachment or rewrite prior build history."
    ),
)
OPEN_CREATE_SETUP = policy(
    "agents.operation.open_create_setup",
    (
        "Open creation only after the owner chooses a new agent; do not treat the earlier "
        "setup request as permission to bypass missing goal or responsibility input."
    ),
)
CHOOSE_EXISTING_SOURCE_CONTEXT = policy(
    "agents.operation.choose_existing_source_context",
    (
        "Open the Agent inventory with the exact ready Source and analyzed API "
        "version retained as the pending attachment choice. Navigation attaches "
        "nothing and must not substitute another same-named Source."
    ),
)
SOURCE_PICKER_ELIGIBILITY = policy(
    "agents.surface.source_picker_eligibility",
    "Show only eligible sources from the same Workspace, including readiness and whether each source is already attached.",
)
ATTACH_EXACT_SOURCE = policy(
    "agents.operation.attach_exact_source",
    (
        "Attach only the exact source selected by the owner and keep one attachment for it. "
        "Repeating its current API version is idempotent; if the ongoing setup reaches a newer "
        "reviewed ready API version, advance that single pin without rewriting prior build lineage."
    ),
)
ATTACH_PERSISTED_SUCCESS = policy(
    "agents.operation.attach_persisted_success",
    "Claim success only after the association is persisted and the originating agent shows the attached source.",
)
DETACH_EXACT_SOURCE = policy(
    "agents.operation.detach_exact_source",
    "Remove only the exact current Agent-to-Source attachment selected by the owner. Preserve the Source, immutable accepted designs, historical builds, deployed runtimes, and Operations evidence.",
)
DETACH_PERSISTED_SUCCESS = policy(
    "agents.operation.detach_persisted_success",
    "Claim success only after the current attachment is absent from the authoritative Agent view; missing, stale, or unauthorized attachment leaves all state unchanged.",
)
SOURCE_CREATION_NAVIGATION = policy(
    "agents.operation.source_creation_navigation",
    "Navigation to source creation does not attach a source and must not be presented as task completion.",
)
ATTACH_CREATED_ELIGIBILITY = policy(
    "agents.operation.attach_created_eligibility",
    "Attach only a successfully created eligible source; cancellation or source-creation failure returns without changing the agent.",
)
OPEN_SOURCE_CONTEXT = policy(
    "agents.operation.open_source_context",
    "Preserve the originating agent and return context when navigating to the selected source.",
)
LIFECYCLE_DEPENDENCY_TRUTH = policy(
    "agents.capability.lifecycle_dependency_truth",
    "Identify the exact selected Agent, current lifecycle, and declared dependencies before consequential review.",
)
LIFECYCLE_REVIEW_TRUTH = policy(
    "agents.surface.lifecycle_review_truth",
    "Show the exact selected Agent and distinguish archive from permanent deletion before confirmation.",
)
ARCHIVE_EXACT_AGENT = policy(
    "agents.operation.archive_exact_agent",
    "Archive only the explicitly selected active Agent; preserve its record, history, Source attachments, and immutable references.",
)
DELETE_EXACT_AGENT = policy(
    "agents.operation.delete_exact_agent",
    "Delete only the explicitly selected active Agent when authoritative dependency inspection is clear; never cascade or detach dependencies.",
)
LIFECYCLE_PERSISTED_SUCCESS = policy(
    "agents.operation.lifecycle_persisted_success",
    "Report archive or deletion only after the exact mutation is persisted; stale state, blockers, rejection, or failure leave the Agent unchanged.",
)

AGENTS_AGENT_POLICIES = (
    FEATURE_PROMPT,
    OWNER_SCOPE,
    VERSION_TRUTH,
    HOME_TRUTH,
    EDIT_CONFLICT,
    SELECTED_AGENT_TRUTH,
    LIFECYCLE_STATE_TRUTH,
    ATTACHMENT_ELIGIBILITY,
    SOURCE_HANDOFF_CONTEXT,
    SETUP_CONTINUATION,
    SETUP_ATTACH_READY,
    OPEN_CREATE_SETUP,
    CHOOSE_EXISTING_SOURCE_CONTEXT,
    SOURCE_PICKER_ELIGIBILITY,
    ATTACH_EXACT_SOURCE,
    ATTACH_PERSISTED_SUCCESS,
    DETACH_EXACT_SOURCE,
    DETACH_PERSISTED_SUCCESS,
    SOURCE_CREATION_NAVIGATION,
    ATTACH_CREATED_ELIGIBILITY,
    OPEN_SOURCE_CONTEXT,
    LIFECYCLE_DEPENDENCY_TRUTH,
    LIFECYCLE_REVIEW_TRUTH,
    ARCHIVE_EXACT_AGENT,
    DELETE_EXACT_AGENT,
    LIFECYCLE_PERSISTED_SUCCESS,
)

__all__ = [
    "AGENTS_AGENT_POLICIES",
    "EDIT_CONFLICT",
    "FEATURE_PROMPT",
    "HOME_TRUTH",
    "OWNER_SCOPE",
    "VERSION_TRUTH",
    "SELECTED_AGENT_TRUTH",
    "LIFECYCLE_STATE_TRUTH",
    "ATTACHMENT_ELIGIBILITY",
    "SOURCE_HANDOFF_CONTEXT",
    "SETUP_CONTINUATION",
    "SETUP_ATTACH_READY",
    "OPEN_CREATE_SETUP",
    "CHOOSE_EXISTING_SOURCE_CONTEXT",
    "SOURCE_PICKER_ELIGIBILITY",
    "ATTACH_EXACT_SOURCE",
    "ATTACH_PERSISTED_SUCCESS",
    "DETACH_EXACT_SOURCE",
    "DETACH_PERSISTED_SUCCESS",
    "SOURCE_CREATION_NAVIGATION",
    "ATTACH_CREATED_ELIGIBILITY",
    "OPEN_SOURCE_CONTEXT",
    "LIFECYCLE_DEPENDENCY_TRUTH",
    "LIFECYCLE_REVIEW_TRUTH",
    "ARCHIVE_EXACT_AGENT",
    "DELETE_EXACT_AGENT",
    "LIFECYCLE_PERSISTED_SUCCESS",
]
