from routedeck_core.contracts.agent import AgentPolicy

from .prompt import WORKSPACE_AGENT_PROMPT


def policy(policy_id: str, instruction: str) -> AgentPolicy:
    return AgentPolicy(id=policy_id, instruction=instruction)


FEATURE_PROMPT = policy("workspace.feature.prompt", WORKSPACE_AGENT_PROMPT)
OWNER_SCOPE = policy(
    "workspace.feature.owner_scope",
    "Use only the authenticated owner's authorized Workspace context.",
)
OVERVIEW_ONLY = policy(
    "workspace.feature.overview_only",
    "Keep Workspace home oriented toward overview and navigation; do not edit domain records here.",
)
TRUTHFUL_STATE = policy(
    "workspace.node.truthful_state",
    "Distinguish authoritative counts, truthful empty states, and temporarily unavailable information.",
)

WORKSPACE_AGENT_POLICIES = (
    FEATURE_PROMPT,
    OWNER_SCOPE,
    OVERVIEW_ONLY,
    TRUTHFUL_STATE,
)

__all__ = [
    "FEATURE_PROMPT",
    "OVERVIEW_ONLY",
    "OWNER_SCOPE",
    "TRUTHFUL_STATE",
    "WORKSPACE_AGENT_POLICIES",
]
