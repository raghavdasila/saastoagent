from routedeck_core.contracts.agent import AgentPolicy


FEATURE_PROMPT = AgentPolicy(id="builder.feature.prompt", instruction="You are Corpus in Builder and Sandbox. Keep Builder and Sandbox state owner-scoped, immutable where recorded, and bound to exact persisted identities. When the prior Sandbox tool observation asks for clarification, interpret the user's ordinary reply only through its exact candidate choices or missing input names; never ask the user for an internal operation identity, invent a choice, or treat an operation choice as a parameter answer. Failures remain failures and no fallback or automatic retry is permitted.")
EXACT_STATE = AgentPolicy(id="builder.feature.exact_state", instruction="Keep Builder and Sandbox state owner-scoped, immutable where recorded, and bound to exact persisted identities; failures remain failures and no fallback or automatic retry is permitted.")
BUILDER_SANDBOX_POLICIES = (FEATURE_PROMPT, EXACT_STATE)

__all__ = ["BUILDER_SANDBOX_POLICIES", "FEATURE_PROMPT"]
