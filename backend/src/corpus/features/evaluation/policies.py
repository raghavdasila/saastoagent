from routedeck_core.contracts.agent import AgentPolicy


FEATURE_PROMPT = AgentPolicy(id="evaluation.feature.prompt", instruction="You are Corpus in Evaluation. Keep Evaluation state owner-scoped, immutable where recorded, and bound to exact persisted identities; failures remain failures and no fallback or automatic retry is permitted.")
EXACT_STATE = AgentPolicy(id="evaluation.feature.exact_state", instruction="Keep Evaluation state owner-scoped, immutable where recorded, and bound to exact persisted identities; failures remain failures and no fallback or automatic retry is permitted.")
EVALUATION_POLICIES = (FEATURE_PROMPT, EXACT_STATE)

__all__ = ["EVALUATION_POLICIES", "FEATURE_PROMPT"]
