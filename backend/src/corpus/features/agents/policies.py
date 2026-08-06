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

AGENTS_AGENT_POLICIES = (
    FEATURE_PROMPT,
    OWNER_SCOPE,
    VERSION_TRUTH,
    HOME_TRUTH,
    EDIT_CONFLICT,
)

__all__ = [
    "AGENTS_AGENT_POLICIES",
    "EDIT_CONFLICT",
    "FEATURE_PROMPT",
    "HOME_TRUTH",
    "OWNER_SCOPE",
    "VERSION_TRUTH",
]
