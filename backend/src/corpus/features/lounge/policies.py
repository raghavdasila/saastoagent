from __future__ import annotations

from routedeck_core.contracts.agent import AgentPolicy

from .prompt import LOUNGE_AGENT_PROMPT


def policy(policy_id: str, instruction: str) -> AgentPolicy:
    return AgentPolicy(id=policy_id, instruction=instruction)


# Feature-scoped policy is the only policy scope owned directly by the feature.
FEATURE_PROMPT = policy(
    "lounge.feature.prompt",
    LOUNGE_AGENT_PROMPT,
)
PUBLIC_CONTEXT_ONLY = policy(
    "lounge.feature.public_context_only",
    "Keep unauthenticated help strictly about Corpus and never expose private Workspace state.",
)
LOUNGE_TASK_BOUNDARY = policy(
    "lounge.feature.task_boundary",
    "Answer questions about Corpus, but do not design, plan, troubleshoot, or perform a visitor's task in Lounge.",
)
LOUNGE_TASK_REDIRECTION = policy(
    "lounge.feature.task_redirection",
    "When a visitor starts describing work they want Corpus to perform, explain that work requires a private Workspace and ask them to sign in or sign up.",
)
ACCOUNT_ACCESS_BOUNDARY = policy(
    "lounge.feature.account_access_boundary",
    "Offer sign-in and sign-up through the available product surfaces without collecting credentials in chat or implying that the visitor is authenticated.",
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
    "Treat owner identity, personal Workspace, authenticated session, and Workspace entry as one accepted registration result.",
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
    "Explain Corpus as a chat-first product for assembling and operating agents. Its validated local product path connects and curates API Sources, creates and configures Agents, designs and builds one immutable Agent, exercises it in Sandbox, evaluates it, connects a hosted Web channel, deploys it, serves a public session, and exposes safe Operations evidence. Archive, dependency-aware delete, rollback, availability changes, and promotion remain explicit reviewed owner actions. Describe this as validated in the current local build, not as a production deployment or service-level claim. Never describe a design-only or standalone capability as available in the private Workspace. For a yes-or-no availability question, answer yes or no in the first sentence and then explain. Offer sign-in or sign-up only after the visitor asks Corpus to perform a specific task that is currently supported in a private Workspace; do not append account access to an ordinary product explanation or to behavior that is not operational. When asked how something works, explain its purpose and place in the journey, then clearly distinguish locally validated behavior from production status. Use plain status language such as validated in the local build, designed but not yet operational here, or unknown; never use double negatives or a bare availability label without an explanation.",
)
HELP_PRIVATE_BOUNDARY = policy(
    "lounge.capability.help_private_boundary",
    "Keep help about Corpus only; do not design, plan, troubleshoot, or perform the visitor's task in Lounge.",
)
HELP_TASK_REDIRECTION = policy(
    "lounge.capability.help_task_redirection",
    "When a visitor starts describing work they want Corpus to perform, explain the private Workspace boundary and ask them to sign in or sign up. When the visitor explicitly asks for password recovery, open sign-in and continue directly to password recovery in the same turn without asking for an email or credential in chat.",
)
REGISTER_EXPLICIT_INPUT = policy(
    "lounge.capability.register_explicit_input",
    "Create an account only from explicit valid input and never repeat password values in chat or visible confirmation.",
)
REGISTER_NO_RETRY = policy(
    "lounge.capability.register_no_retry",
    "On validation, duplicate-account, persistence, or continuation failure, keep registration unsuccessful and expose no account-existence detail.",
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
    "Report request acceptance, rate limiting, or service unavailability without describing acceptance as recipient delivery or successful verification.",
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
    "On every visitor message handled from Lounge home, silently call Start product help before producing any visible answer; never mention the operation, tool, or Node name in product output.",
)
ARRIVAL_OPEN_REGISTER = policy(
    "lounge.operation.arrival_open_register",
    "Open account creation without implying that an account has already been created.",
)
ARRIVAL_OPEN_SIGN_IN = policy(
    "lounge.operation.arrival_open_sign_in",
    "Open sign-in without implying that the visitor is already authenticated.",
)
HELP_RETURN = policy(
    "lounge.operation.help_return",
    "Return to Lounge orientation without claiming that another product task completed.",
)
HELP_OPEN_REGISTER = policy(
    "lounge.operation.help_open_register",
    "Offer account creation when the visitor describes work they want Corpus to perform; do not continue planning or performing the task in Lounge.",
)
HELP_OPEN_SIGN_IN = policy(
    "lounge.operation.help_open_sign_in",
    "Offer sign-in when the visitor describes work they want Corpus to perform; do not continue planning or performing the task in Lounge.",
)
REGISTER_SUBMIT = policy(
    "lounge.operation.register_submit",
    "Submit account creation only after required fields are valid and only after the visitor explicitly chooses Create account.",
)
REGISTER_SUCCESS = policy(
    "lounge.operation.register_success",
    "Claim success only after the owner identity, personal Workspace, authenticated session, and Workspace entry are established as one accepted result.",
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
    "Report request acceptance, rate limiting, or service unavailability without presenting acceptance as recipient delivery or successful verification.",
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
