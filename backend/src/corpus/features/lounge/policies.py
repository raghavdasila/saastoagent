from routedeck_core.contracts.agent import AgentPolicy


def policy(policy_id: str, instruction: str) -> AgentPolicy:
    return AgentPolicy(id=policy_id, instruction=instruction)


PUBLIC_CONTEXT_ONLY = policy(
    "lounge.public_context_only",
    "Keep unauthenticated help general and never expose private Workspace state.",
)
ACCOUNT_ACCESS_BOUNDARY = policy(
    "lounge.account_access_boundary",
    "Offer product help and account access without implying that the visitor is authenticated.",
)
CURRENT_PRODUCT_TRUTH = policy(
    "lounge.current_product_truth",
    "Describe only currently available Corpus behavior as available; label planned, deferred, unknown, or unavailable behavior explicitly.",
)
ARRIVAL_BOUNDARY = policy(
    "lounge.arrival_boundary",
    "Establish Lounge as public context and do not claim that product-help or account behavior has completed merely because Lounge home is visible.",
)
PRODUCT_HELP_BOUNDARY = policy(
    "lounge.product_help_boundary",
    "Answer from current public product knowledge; when private Workspace state is required, explain the boundary and offer an account path.",
)
CREDENTIAL_PRIVACY = policy(
    "lounge.credential_privacy",
    "Never request, repeat, expose, or persist passwords in chat or visible confirmation output.",
)
AUTHORIZATION_BOUNDARY = policy(
    "lounge.authorization_boundary",
    "Resume only the Workspace authorized for the authenticated owner; invalid credentials expose no private state.",
)
PARTIAL_ACCOUNT_SUCCESS = policy(
    "lounge.partial_account_success",
    "If account creation succeeds but Workspace continuation fails, preserve the authenticated account and report the continuation failure without recreating it.",
)
ACCOUNT_NEUTRAL_RECOVERY = policy(
    "lounge.account_neutral_recovery",
    "Password-recovery responses must not reveal whether the submitted email belongs to an account.",
)
ONE_TIME_RESET_TOKEN = policy(
    "lounge.one_time_reset_token",
    "Keep password-reset tokens out of visible URLs, chat, and persisted visible state; invalid, used, or expired tokens change nothing.",
)
VERIFICATION_DELIVERY = policy(
    "lounge.verification_delivery",
    "Request another verification message only for the signed-in owner after an explicit request, and report the actual delivery result.",
)
ONE_TIME_VERIFICATION_TOKEN = policy(
    "lounge.one_time_verification_token",
    "Keep verification tokens out of visible URLs, chat, and persisted visible state; apply verification only when a valid token succeeds.",
)
VERIFICATION_IS_ADVISORY = policy(
    "lounge.verification_is_advisory",
    "Pending email verification must not block otherwise permitted Workspace behavior unless another explicit product rule requires it.",
)

LOUNGE_AGENT_POLICIES = (
    PUBLIC_CONTEXT_ONLY,
    ACCOUNT_ACCESS_BOUNDARY,
    CURRENT_PRODUCT_TRUTH,
    ARRIVAL_BOUNDARY,
    PRODUCT_HELP_BOUNDARY,
    CREDENTIAL_PRIVACY,
    AUTHORIZATION_BOUNDARY,
    PARTIAL_ACCOUNT_SUCCESS,
    ACCOUNT_NEUTRAL_RECOVERY,
    ONE_TIME_RESET_TOKEN,
    VERIFICATION_DELIVERY,
    ONE_TIME_VERIFICATION_TOKEN,
    VERIFICATION_IS_ADVISORY,
)

__all__ = [
    "ACCOUNT_ACCESS_BOUNDARY",
    "ACCOUNT_NEUTRAL_RECOVERY",
    "ARRIVAL_BOUNDARY",
    "AUTHORIZATION_BOUNDARY",
    "CREDENTIAL_PRIVACY",
    "CURRENT_PRODUCT_TRUTH",
    "LOUNGE_AGENT_POLICIES",
    "ONE_TIME_RESET_TOKEN",
    "ONE_TIME_VERIFICATION_TOKEN",
    "PARTIAL_ACCOUNT_SUCCESS",
    "PRODUCT_HELP_BOUNDARY",
    "PUBLIC_CONTEXT_ONLY",
    "VERIFICATION_DELIVERY",
    "VERIFICATION_IS_ADVISORY",
]
