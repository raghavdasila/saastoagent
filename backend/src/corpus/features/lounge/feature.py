from __future__ import annotations

from routedeck_core.app import Feature
from routedeck_core.contracts.application import Capability, Node
from routedeck_core.contracts.conversation import ConversationInputPolicy
from routedeck_core.contracts.navigation import DeepLinkPolicy, NodeKind, Route, Transition
from routedeck_core.contracts.projection import FrozenJsonObject
from routedeck_core.contracts.surfaces import Surface, SurfaceAffordance, SurfaceLifecycle, SurfaceSlots

from corpus.features.workspace.declarations import EMPTY_OBJECT_SCHEMA, OWNER_CONTEXT_PROVIDER

from .declarations import (
    AUTHENTICATION_COMPLETED,
    FORGOT_PASSWORD_REF,
    HOME_REF,
    LOUNGE_REF,
    OPEN_FORGOT_PASSWORD,
    OPEN_REGISTRATION,
    OPEN_RESET_PASSWORD,
    OPEN_SIGN_IN,
    OPEN_VERIFY_EMAIL,
    REGISTER_REF,
    RESET_PASSWORD_REF,
    RETURN_TO_LOUNGE,
    RETURN_TO_WORKSPACE,
    SIGN_IN_REF,
    VERIFICATION_PENDING_REF,
    VERIFY_EMAIL_REF,
)
from .policies import (
    ACCOUNT_ACCESS_BOUNDARY,
    ACCOUNT_NEUTRAL_RECOVERY,
    ARRIVAL_BOUNDARY,
    AUTHORIZATION_BOUNDARY,
    CREDENTIAL_PRIVACY,
    CURRENT_PRODUCT_TRUTH,
    LOUNGE_AGENT_POLICIES,
    ONE_TIME_RESET_TOKEN,
    ONE_TIME_VERIFICATION_TOKEN,
    PARTIAL_ACCOUNT_SUCCESS,
    PRODUCT_HELP_BOUNDARY,
    PUBLIC_CONTEXT_ONLY,
    VERIFICATION_DELIVERY,
    VERIFICATION_IS_ADVISORY,
)
from .prompt import LOUNGE_AGENT_PROMPT


CREDENTIAL_INPUT = ConversationInputPolicy(
    enabled=False,
    disabled_message="Chat is disabled while entering account credentials.",
)


def surface(surface_id, *affordances, policies=()):
    return Surface(
        id=surface_id,
        component=surface_id,
        lifecycle=SurfaceLifecycle.STABLE,
        public_props_schema=FrozenJsonObject(EMPTY_OBJECT_SCHEMA),
        affordances=affordances,
        policy_refs=tuple(policy.ref for policy in policies),
    )


LOUNGE_SURFACE = surface(
    "lounge.home",
    SurfaceAffordance(id="open_sign_in", event="open", operation=OPEN_SIGN_IN.ref),
    SurfaceAffordance(id="open_registration", event="open", operation=OPEN_REGISTRATION.ref),
    policies=(PUBLIC_CONTEXT_ONLY, ARRIVAL_BOUNDARY),
)
SIGN_IN_SURFACE = surface(
    "lounge.sign_in",
    SurfaceAffordance(id="return_to_lounge", event="open", operation=RETURN_TO_LOUNGE.ref),
    SurfaceAffordance(id="open_forgot_password", event="open", operation=OPEN_FORGOT_PASSWORD.ref),
    SurfaceAffordance(id="authentication_completed", event="submit", operation=AUTHENTICATION_COMPLETED.ref),
    policies=(CREDENTIAL_PRIVACY, AUTHORIZATION_BOUNDARY),
)
REGISTER_SURFACE = surface(
    "lounge.register",
    SurfaceAffordance(id="return_to_lounge", event="open", operation=RETURN_TO_LOUNGE.ref),
    SurfaceAffordance(id="authentication_completed", event="submit", operation=AUTHENTICATION_COMPLETED.ref),
    policies=(CREDENTIAL_PRIVACY, PARTIAL_ACCOUNT_SUCCESS),
)
FORGOT_PASSWORD_SURFACE = surface(
    "lounge.forgot_password",
    SurfaceAffordance(id="return_to_lounge", event="open", operation=RETURN_TO_LOUNGE.ref),
    policies=(ACCOUNT_NEUTRAL_RECOVERY,),
)
RESET_PASSWORD_SURFACE = surface(
    "lounge.reset_password",
    SurfaceAffordance(id="return_to_lounge", event="open", operation=RETURN_TO_LOUNGE.ref),
    policies=(CREDENTIAL_PRIVACY, ONE_TIME_RESET_TOKEN),
)
VERIFY_EMAIL_SURFACE = surface(
    "lounge.verify_email",
    SurfaceAffordance(id="return_to_lounge", event="open", operation=RETURN_TO_LOUNGE.ref),
    policies=(ONE_TIME_VERIFICATION_TOKEN,),
)
VERIFICATION_PENDING_SURFACE = surface(
    "lounge.verification_pending",
    SurfaceAffordance(id="return_to_workspace", event="open", operation=RETURN_TO_WORKSPACE.ref),
    policies=(VERIFICATION_DELIVERY, VERIFICATION_IS_ADVISORY),
)

LOUNGE_ENTRY = Capability(
    id="lounge.entry",
    title="Establish the public Lounge context",
    operations=(OPEN_SIGN_IN.ref, OPEN_REGISTRATION.ref, OPEN_RESET_PASSWORD.ref, OPEN_VERIFY_EMAIL.ref),
    surfaces=(LOUNGE_SURFACE.ref,),
    policy_refs=(ARRIVAL_BOUNDARY.ref,),
)
PRODUCT_HELP = Capability(
    id="lounge.product_help",
    title="Answer public questions about Corpus",
    operations=(),
    surfaces=(),
    policy_refs=(PRODUCT_HELP_BOUNDARY.ref, CURRENT_PRODUCT_TRUTH.ref),
)
SIGN_IN = Capability(
    id="lounge.authenticate_owner",
    title="Authenticate the owner and resume their authorized Workspace",
    operations=(RETURN_TO_LOUNGE.ref, OPEN_FORGOT_PASSWORD.ref, AUTHENTICATION_COMPLETED.ref),
    surfaces=(SIGN_IN_SURFACE.ref,),
    policy_refs=(CREDENTIAL_PRIVACY.ref, AUTHORIZATION_BOUNDARY.ref),
)
REGISTER = Capability(
    id="lounge.create_owner",
    title="Create the owner account and personal Workspace",
    operations=(RETURN_TO_LOUNGE.ref, AUTHENTICATION_COMPLETED.ref),
    surfaces=(REGISTER_SURFACE.ref,),
    policy_refs=(CREDENTIAL_PRIVACY.ref, PARTIAL_ACCOUNT_SUCCESS.ref),
)
REQUEST_RESET = Capability(
    id="lounge.request_password_recovery",
    title="Request account-neutral password recovery",
    operations=(RETURN_TO_LOUNGE.ref,),
    surfaces=(FORGOT_PASSWORD_SURFACE.ref,),
    policy_refs=(ACCOUNT_NEUTRAL_RECOVERY.ref,),
)
CONFIRM_RESET = Capability(
    id="lounge.set_new_password",
    title="Set a password with a valid one-time recovery link",
    operations=(RETURN_TO_LOUNGE.ref,),
    surfaces=(RESET_PASSWORD_SURFACE.ref,),
    policy_refs=(CREDENTIAL_PRIVACY.ref, ONE_TIME_RESET_TOKEN.ref),
)
REQUEST_VERIFICATION = Capability(
    id="lounge.request_verification",
    title="Request verification delivery for the signed-in owner",
    operations=(RETURN_TO_WORKSPACE.ref,),
    surfaces=(VERIFICATION_PENDING_SURFACE.ref,),
    policy_refs=(VERIFICATION_DELIVERY.ref, VERIFICATION_IS_ADVISORY.ref),
)
CONFIRM_VERIFICATION = Capability(
    id="lounge.confirm_verification",
    title="Confirm the owner email with a valid one-time link",
    operations=(RETURN_TO_LOUNGE.ref,),
    surfaces=(VERIFY_EMAIL_SURFACE.ref,),
    policy_refs=(ONE_TIME_VERIFICATION_TOKEN.ref, VERIFICATION_IS_ADVISORY.ref),
)

LOUNGE_NODE = Node(
    id=LOUNGE_REF.id,
    title="Lounge",
    kind=NodeKind.SECTION,
    route=Route(template="/", deep_link_policy=DeepLinkPolicy.SHAREABLE),
    operations=(OPEN_SIGN_IN, OPEN_REGISTRATION, OPEN_RESET_PASSWORD, OPEN_VERIFY_EMAIL),
    outgoing=(
        Transition(operation=OPEN_SIGN_IN.ref, outcome="opened", target=SIGN_IN_REF),
        Transition(operation=OPEN_REGISTRATION.ref, outcome="opened", target=REGISTER_REF),
        Transition(operation=OPEN_RESET_PASSWORD.ref, outcome="opened", target=RESET_PASSWORD_REF),
        Transition(operation=OPEN_VERIFY_EMAIL.ref, outcome="opened", target=VERIFY_EMAIL_REF),
    ),
    capabilities=(LOUNGE_ENTRY, PRODUCT_HELP),
    surfaces=SurfaceSlots(active=LOUNGE_SURFACE),
    policy_refs=(ARRIVAL_BOUNDARY.ref, PRODUCT_HELP_BOUNDARY.ref),
)
SIGN_IN_NODE = Node(
    id=SIGN_IN_REF.id,
    title="Sign in",
    kind=NodeKind.SECTION,
    parent=LOUNGE_REF,
    route=Route(template="/sign-in", deep_link_policy=DeepLinkPolicy.SHAREABLE),
    context_providers=(OWNER_CONTEXT_PROVIDER,),
    conversation_input=CREDENTIAL_INPUT,
    operations=(RETURN_TO_LOUNGE, OPEN_FORGOT_PASSWORD, AUTHENTICATION_COMPLETED),
    outgoing=(
        Transition(operation=RETURN_TO_LOUNGE.ref, outcome="opened", target=LOUNGE_REF),
        Transition(operation=OPEN_FORGOT_PASSWORD.ref, outcome="opened", target=FORGOT_PASSWORD_REF),
        Transition(operation=AUTHENTICATION_COMPLETED.ref, outcome="opened", target=HOME_REF),
    ),
    capabilities=(SIGN_IN,),
    surfaces=SurfaceSlots(active=SIGN_IN_SURFACE),
    policy_refs=(CREDENTIAL_PRIVACY.ref, AUTHORIZATION_BOUNDARY.ref),
)
REGISTER_NODE = Node(
    id=REGISTER_REF.id,
    title="Create account",
    kind=NodeKind.SECTION,
    parent=LOUNGE_REF,
    route=Route(template="/register", deep_link_policy=DeepLinkPolicy.SHAREABLE),
    context_providers=(OWNER_CONTEXT_PROVIDER,),
    conversation_input=CREDENTIAL_INPUT,
    operations=(RETURN_TO_LOUNGE, AUTHENTICATION_COMPLETED),
    outgoing=(
        Transition(operation=RETURN_TO_LOUNGE.ref, outcome="opened", target=LOUNGE_REF),
        Transition(operation=AUTHENTICATION_COMPLETED.ref, outcome="opened", target=HOME_REF),
    ),
    capabilities=(REGISTER,),
    surfaces=SurfaceSlots(active=REGISTER_SURFACE),
    policy_refs=(CREDENTIAL_PRIVACY.ref, PARTIAL_ACCOUNT_SUCCESS.ref),
)


def recovery_node(node_ref, title, path, active_surface, capability, policies):
    return Node(
        id=node_ref.id,
        title=title,
        kind=NodeKind.SECTION,
        parent=LOUNGE_REF,
        route=Route(template=path, deep_link_policy=DeepLinkPolicy.SHAREABLE),
        conversation_input=CREDENTIAL_INPUT,
        operations=(RETURN_TO_LOUNGE,),
        outgoing=(Transition(operation=RETURN_TO_LOUNGE.ref, outcome="opened", target=LOUNGE_REF),),
        capabilities=(capability,),
        surfaces=SurfaceSlots(active=active_surface),
        policy_refs=tuple(policy.ref for policy in policies),
    )


FORGOT_PASSWORD_NODE = recovery_node(FORGOT_PASSWORD_REF, "Request password recovery", "/forgot-password", FORGOT_PASSWORD_SURFACE, REQUEST_RESET, (ACCOUNT_NEUTRAL_RECOVERY,))
RESET_PASSWORD_NODE = recovery_node(RESET_PASSWORD_REF, "Set a new password", "/reset-password", RESET_PASSWORD_SURFACE, CONFIRM_RESET, (CREDENTIAL_PRIVACY, ONE_TIME_RESET_TOKEN))
VERIFY_EMAIL_NODE = recovery_node(VERIFY_EMAIL_REF, "Confirm email verification", "/verify", VERIFY_EMAIL_SURFACE, CONFIRM_VERIFICATION, (ONE_TIME_VERIFICATION_TOKEN, VERIFICATION_IS_ADVISORY))
VERIFICATION_PENDING_NODE = Node(
    id=VERIFICATION_PENDING_REF.id,
    title="Resend email verification",
    kind=NodeKind.SECTION,
    parent=LOUNGE_REF,
    route=Route(template="/verification-pending", deep_link_policy=DeepLinkPolicy.SESSION_BOUND),
    context_providers=(OWNER_CONTEXT_PROVIDER,),
    conversation_input=CREDENTIAL_INPUT,
    operations=(RETURN_TO_WORKSPACE,),
    outgoing=(Transition(operation=RETURN_TO_WORKSPACE.ref, outcome="opened", target=HOME_REF),),
    capabilities=(REQUEST_VERIFICATION,),
    surfaces=SurfaceSlots(active=VERIFICATION_PENDING_SURFACE),
    policy_refs=(VERIFICATION_DELIVERY.ref, VERIFICATION_IS_ADVISORY.ref),
)

LOUNGE_FEATURE = Feature(
    namespace="lounge",
    nodes=(LOUNGE_NODE, SIGN_IN_NODE, REGISTER_NODE, FORGOT_PASSWORD_NODE, RESET_PASSWORD_NODE, VERIFY_EMAIL_NODE, VERIFICATION_PENDING_NODE),
    agent_prompt=LOUNGE_AGENT_PROMPT,
    agent_policies=LOUNGE_AGENT_POLICIES,
    policy_refs=(PUBLIC_CONTEXT_ONLY.ref, ACCOUNT_ACCESS_BOUNDARY.ref, CURRENT_PRODUCT_TRUTH.ref),
)

__all__ = [
    "FORGOT_PASSWORD_NODE",
    "LOUNGE_FEATURE",
    "LOUNGE_NODE",
    "LOUNGE_SURFACE",
    "REGISTER_NODE",
    "RESET_PASSWORD_NODE",
    "SIGN_IN_NODE",
    "VERIFICATION_PENDING_NODE",
    "VERIFY_EMAIL_NODE",
]
