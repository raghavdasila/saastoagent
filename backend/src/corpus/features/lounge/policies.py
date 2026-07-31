from __future__ import annotations

from routedeck_core.contracts.agent import AgentPolicy


def policy(policy_id: str, instruction: str) -> AgentPolicy:
    return AgentPolicy(id=policy_id, instruction=instruction)


# Feature-scoped policy is the only policy scope owned directly by the feature.
PUBLIC_CONTEXT_ONLY = policy(
    "lounge.feature.public_context_only",
    "Keep unauthenticated help general and never expose private Workspace state.",
)
ACCOUNT_ACCESS_BOUNDARY = policy(
    "lounge.feature.account_access_boundary",
    "Offer product help and account access without implying that the visitor is authenticated.",
)
CURRENT_PRODUCT_TRUTH = policy(
    "lounge.feature.current_product_truth",
    "Describe only currently available Corpus behavior as available; label planned, deferred, unknown, or unavailable behavior explicitly.",
)
LOUNGE_CHROME_BOUNDARY = policy(
    "lounge.feature.chrome_boundary",
    "While Lounge is active, identify the product location as Lounge and keep private Workspace and feature navigation hidden until authenticated entry succeeds.",
)
USER_FACING_LANGUAGE = policy(
    "lounge.feature.user_facing_language",
    "Describe Lounge choices in user-facing product language and never expose internal operation, tool, Node, AgentPolicy, or identifier names.",
)

# Node-scoped policies.
PUBLIC_NODE_CONTEXT = policy(
    "lounge.node.public_context",
    "Use public Corpus context only and never expose or imply access to a private Workspace.",
)
PUBLIC_NODE_PATHS = policy(
    "lounge.node.public_paths",
    "Present current public help and account paths truthfully, distinguishing unavailable or deferred behavior.",
)
REGISTRATION_NODE_PRIVACY = policy(
    "lounge.node.registration_privacy",
    "Keep credential input private and do not expose authenticated Workspace state before account creation and continuation succeed.",
)
REGISTRATION_NODE_PARTIAL_SUCCESS = policy(
    "lounge.node.registration_partial_success",
    "Preserve partial-success truth when identity creation succeeds but authenticated continuation fails.",
)
SIGN_IN_NODE_PRIVACY = policy(
    "lounge.node.sign_in_privacy",
    "Keep credentials private and expose no Workspace facts until authentication succeeds.",
)
SIGN_IN_NODE_FAILURE = policy(
    "lounge.node.sign_in_failure",
    "Invalid authentication remains a visible failure and must not reveal whether unrelated private state exists.",
)
RESET_NODE_TOKEN_PRIVACY = policy(
    "lounge.node.reset_token_privacy",
    "Protect account existence during recovery requests and keep one-time recovery tokens out of visible URLs and product output.",
)
RESET_NODE_TOKEN_FAILURE = policy(
    "lounge.node.reset_token_failure",
    "A missing, invalid, used, or expired token changes nothing and remains an explicit failure.",
)
VERIFICATION_NODE_TOKEN_PRIVACY = policy(
    "lounge.node.verification_token_privacy",
    "Keep one-time verification tokens out of the visible URL, chat, and persisted visible state.",
)
VERIFICATION_NODE_ADVISORY = policy(
    "lounge.node.verification_advisory",
    "Pending verification must not block otherwise permitted Workspace behavior unless a separate product rule explicitly requires it.",
)

# Capability-scoped policies.
ENTRY_PUBLIC_ONLY = policy(
    "lounge.capability.entry_public_only",
    "Establish only unauthenticated public context.",
)
ENTRY_COMPLETION_BOUNDARY = policy(
    "lounge.capability.entry_completion_boundary",
    "Complete entry when Lounge home is visible; do not start or claim completion of any downstream behavior.",
)
HELP_PRODUCT_TRUTH = policy(
    "lounge.capability.help_product_truth",
    "Answer from current product knowledge and label planned, deferred, unknown, or unavailable behavior explicitly.",
)
HELP_PRIVATE_BOUNDARY = policy(
    "lounge.capability.help_private_boundary",
    "When a request requires private Workspace state, explain the boundary and offer an account path without inventing an answer.",
)
REGISTER_EXPLICIT_INPUT = policy(
    "lounge.capability.register_explicit_input",
    "Create an account only from explicit valid input and never repeat password values in chat or visible confirmation.",
)
REGISTER_NO_RETRY = policy(
    "lounge.capability.register_no_retry",
    "Do not retry identity creation after partial success; continue or report the exact continuation failure instead.",
)
SIGN_IN_AUTHORITY = policy(
    "lounge.capability.sign_in_authority",
    "Use the authenticated identity as the authority for Workspace selection; never accept a user-supplied Workspace target as authority.",
)
SIGN_IN_COMPLETION = policy(
    "lounge.capability.sign_in_completion",
    "Describe sign-in as complete only after authentication and Workspace continuation both succeed.",
)
RESET_ACCOUNT_NEUTRAL = policy(
    "lounge.capability.reset_account_neutral",
    "Use the same account-neutral response for existing and non-existing accounts.",
)
RESET_DELIVERY_PRIVACY = policy(
    "lounge.capability.reset_delivery_privacy",
    "Report delivery-system unavailability without disclosing account existence or claiming delivery success.",
)
PASSWORD_TOKEN_BOUNDARY = policy(
    "lounge.capability.password_token_boundary",
    "Accept only a valid unexpired one-time token bound to the recovery request.",
)
PASSWORD_CHANGE_COMPLETION = policy(
    "lounge.capability.password_change_completion",
    "Claim success only after the password changes and existing sessions are revoked; then return the owner to sign-in.",
)
VERIFICATION_SIGNED_IN_OWNER = policy(
    "lounge.capability.verification_signed_in_owner",
    "Operate only on the signed-in owner and send only after an explicit request.",
)
VERIFICATION_DELIVERY_TRUTH = policy(
    "lounge.capability.verification_delivery_truth",
    "Report the actual delivery request result without describing a request as successful verification.",
)
VERIFICATION_TOKEN_BOUNDARY = policy(
    "lounge.capability.verification_token_boundary",
    "Apply verification only to the owner account bound to a valid unexpired token.",
)
VERIFICATION_REFRESH_TRUTH = policy(
    "lounge.capability.verification_refresh_truth",
    "Refresh and present verified state only after confirmation succeeds; token failure changes nothing.",
)

# Surface-scoped policies.
LOUNGE_SURFACE_PUBLIC = policy(
    "lounge.surface.home_public",
    "Present only public orientation and entry paths; never expose or imply access to private Workspace state.",
)
LOUNGE_SURFACE_BOUNDARY = policy(
    "lounge.surface.home_boundary",
    "Keep this surface limited to Lounge orientation; product-help and account interactions belong to their own behaviors.",
)
LOUNGE_SURFACE_SCOPED_NAVIGATION = policy(
    "lounge.surface.home_scoped_navigation",
    "Identify the active product location as Lounge and show only Lounge-scoped navigation; keep private Workspace and feature navigation hidden until authenticated entry succeeds.",
)
REGISTER_SURFACE_PRIVACY = policy(
    "lounge.surface.register_privacy",
    "Keep password values private and masked; never repeat credentials in chat, confirmation text, or persisted design-visible state.",
)
SIGN_IN_SURFACE_PRIVACY = policy(
    "lounge.surface.sign_in_privacy",
    "Keep credentials private and masked; never echo passwords or include them in conversational output.",
)
RESET_REQUEST_SURFACE_NEUTRALITY = policy(
    "lounge.surface.reset_request_neutrality",
    "Use the same account-neutral confirmation whether or not the submitted email belongs to an account.",
)
RESET_CONFIRM_SURFACE_TOKEN = policy(
    "lounge.surface.reset_confirm_token",
    "Remove the one-time token from the visible URL and never render, repeat, or persist it in visible product state.",
)
VERIFY_SURFACE_TOKEN = policy(
    "lounge.surface.verify_token",
    "Remove the one-time token from the visible URL and never expose it in chat or visible confirmation state.",
)

# Operation-scoped policies. Operations with the same visible meaning remain
# behavior-specific so each Node carries only its own policy context.
ARRIVAL_START_HELP = policy(
    "lounge.operation.arrival_start_help",
    "Silently enter product-help context before answering a substantive Corpus product question from Lounge home; never mention the operation, tool, or Node name in product output.",
)
ARRIVAL_OPEN_REGISTER = policy(
    "lounge.operation.arrival_open_register",
    "Open account creation without implying that an account has already been created.",
)
ARRIVAL_OPEN_SIGN_IN = policy(
    "lounge.operation.arrival_open_sign_in",
    "Open sign-in without implying that the visitor is already authenticated.",
)
ARRIVAL_OPEN_RESET = policy(
    "lounge.operation.arrival_open_reset",
    "Open password reset only from the matching one-time recovery route; never claim that the token is valid before validation.",
)
ARRIVAL_OPEN_VERIFY = policy(
    "lounge.operation.arrival_open_verify",
    "Open email verification only from the matching one-time verification route; never claim that the token is valid before validation.",
)
HELP_RETURN = policy(
    "lounge.operation.help_return",
    "Return to Lounge orientation without claiming that another product task completed.",
)
HELP_OPEN_REGISTER = policy(
    "lounge.operation.help_open_register",
    "Offer account creation only when the visitor wants to begin private Workspace work.",
)
HELP_OPEN_SIGN_IN = policy(
    "lounge.operation.help_open_sign_in",
    "Offer sign-in only when the visitor wants to resume private Workspace work.",
)
REGISTER_SUBMIT = policy(
    "lounge.operation.register_submit",
    "Submit account creation only after required fields are valid and only after the visitor explicitly chooses Create account.",
)
REGISTER_SUCCESS = policy(
    "lounge.operation.register_success",
    "Claim success only after the owner identity and personal Workspace are created; report partial continuation failure without recreating the account.",
)
REGISTER_CONTINUE = policy(
    "lounge.operation.register_continue",
    "Continue only an already-authenticated owner into the authorized Workspace; never recreate the account or resubmit credentials.",
)
REGISTER_RETURN = policy(
    "lounge.operation.register_return",
    "Leave account creation without submitting or retaining an incomplete credential form.",
)
SIGN_IN_SUBMIT = policy(
    "lounge.operation.sign_in_submit",
    "Resume only the Workspace authorized for the authenticated owner; invalid credentials remain a failure and expose no private state.",
)
SIGN_IN_CONTINUE = policy(
    "lounge.operation.sign_in_continue",
    "Continue only an already-authenticated owner into the authorized Workspace; never resubmit credentials.",
)
SIGN_IN_OPEN_RECOVERY = policy(
    "lounge.operation.sign_in_open_recovery",
    "Open account-neutral password recovery without revealing whether the entered email belongs to an account.",
)
SIGN_IN_RETURN = policy(
    "lounge.operation.sign_in_return",
    "Leave sign-in without submitting or retaining an incomplete credential form.",
)
RESET_REQUEST_SUBMIT_NEUTRAL = policy(
    "lounge.operation.reset_request_submit_neutral",
    "Do not reveal account existence; report delivery-system unavailability without disclosing whether the submitted account exists.",
)
RESET_REQUEST_NOT_PROOF = policy(
    "lounge.operation.reset_request_not_proof",
    "Treat submission as a recovery request only, not as proof that an account exists or that delivery succeeded.",
)
RESET_REQUEST_RETURN = policy(
    "lounge.operation.reset_request_return",
    "Return to Lounge without revealing whether the submitted email belongs to an account.",
)
PASSWORD_CHANGE_TOKEN = policy(
    "lounge.operation.password_change_token",
    "Accept only a valid unexpired one-time token; on success change the password and revoke existing sessions.",
)
PASSWORD_CHANGE_RETURN = policy(
    "lounge.operation.password_change_return",
    "Leave password reset without changing the password or consuming the one-time token.",
)
VERIFICATION_REQUEST_EXPLICIT = policy(
    "lounge.operation.verification_request_explicit",
    "Request another verification message only after the owner explicitly asks; do not send automatically or repeatedly.",
)
VERIFICATION_REQUEST_RESULT = policy(
    "lounge.operation.verification_request_result",
    "Report the actual delivery request result, and do not block otherwise permitted Workspace use when verification remains pending.",
)
VERIFICATION_RETURN_WORKSPACE = policy(
    "lounge.operation.verification_return_workspace",
    "Return to the authenticated Workspace without treating pending verification as a blocker.",
)
VERIFY_CONFIRM_OWNER = policy(
    "lounge.operation.verify_confirm_owner",
    "Apply verification only to the owner account bound to a valid unexpired one-time token.",
)
VERIFY_RETURN = policy(
    "lounge.operation.verify_return",
    "Leave email confirmation without consuming or exposing the one-time token.",
)


LOUNGE_AGENT_POLICIES = tuple(
    value
    for name, value in globals().items()
    if name.isupper() and isinstance(value, AgentPolicy)
)


__all__ = [
    name
    for name, value in globals().items()
    if name.isupper() and isinstance(value, AgentPolicy)
] + ["LOUNGE_AGENT_POLICIES"]
