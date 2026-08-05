from __future__ import annotations

from routedeck_core.app import Feature
from routedeck_core.contracts.application import Capability, Node
from routedeck_core.contracts.conversation import (
    ConversationInputPolicy,
    EntryTurnDeclaration,
)
from routedeck_core.contracts.navigation import (
    DeepLinkPolicy,
    NodeKind,
    Route,
    Transition,
)
from routedeck_core.contracts.projection import FrozenJsonObject
from routedeck_core.contracts.suggestions import SuggestedAction
from routedeck_core.contracts.surfaces import (
    PrivateFormBinding,
    Surface,
    SurfaceAffordance,
    SurfaceLifecycle,
    SurfaceSlots,
)

from corpus.features.workspace.declarations import (
    EMPTY_OBJECT_SCHEMA,
    HOME_REF,
    OWNER_CONTEXT_PROVIDER,
)

from . import policies
from .declarations import (
    ARRIVAL_OPEN_REGISTRATION,
    ARRIVAL_OPEN_SIGN_IN,
    AUTHENTICATE_OWNER,
    CHANGE_OWNER_PASSWORD,
    CHANGE_PASSWORD_RETURN_TO_LOUNGE,
    CONFIRM_EMAIL_RETURN_TO_LOUNGE,
    CONFIRM_OWNER_EMAIL,
    CREATE_OWNER_ACCOUNT,
    FORGOT_PASSWORD_REF,
    HELP_OPEN_REGISTRATION,
    HELP_OPEN_SIGN_IN,
    HELP_RETURN_TO_LOUNGE,
    LOUNGE_REF,
    OPEN_PRODUCT_HELP,
    PRODUCT_HELP_REF,
    REGISTER_FORM_ID,
    REGISTER_REF,
    REGISTRATION_CONTINUE_TO_WORKSPACE,
    REGISTRATION_RETURN_TO_LOUNGE,
    REQUEST_PASSWORD_RESET,
    REQUEST_RESET_RETURN_TO_LOUNGE,
    REQUEST_VERIFICATION_DELIVERY,
    RESET_CONFIRM_FORM_ID,
    RESET_PASSWORD_REF,
    RESET_REQUEST_FORM_ID,
    SIGN_IN_CONTINUE_TO_WORKSPACE,
    SIGN_IN_FORM_ID,
    SIGN_IN_OPEN_PASSWORD_RECOVERY,
    SIGN_IN_REF,
    SIGN_IN_RETURN_TO_LOUNGE,
    VERIFICATION_PENDING_REF,
    VERIFICATION_RETURN_TO_WORKSPACE,
    VERIFY_EMAIL_FORM_ID,
    VERIFY_EMAIL_REF,
)


CREDENTIAL_INPUT = ConversationInputPolicy(
    enabled=False,
    disabled_message="Chat is disabled while entering private account information.",
)


def public_surface(surface_id, *affordances, policy_values=()):
    return Surface(
        id=surface_id,
        component=surface_id,
        lifecycle=SurfaceLifecycle.STABLE,
        public_props_schema=FrozenJsonObject(EMPTY_OBJECT_SCHEMA),
        affordances=affordances,
        policy_refs=tuple(value.ref for value in policy_values),
    )


def private_surface(
    surface_id,
    form_id,
    field_names,
    *affordances,
    policy_values=(),
):
    return Surface(
        id=surface_id,
        component=surface_id,
        lifecycle=SurfaceLifecycle.STABLE,
        public_props_schema=FrozenJsonObject(
            {
                "type": "object",
                "properties": {
                    "form_handle": {"type": "string", "const": form_id},
                },
                "required": ["form_handle"],
                "additionalProperties": False,
            }
        ),
        private_form_binding=PrivateFormBinding(
            form_id_prop="form_handle",
            allowed_field_names=field_names,
        ),
        affordances=affordances,
        policy_refs=tuple(value.ref for value in policy_values),
    )


LOUNGE_SURFACE = public_surface(
    "lounge.home",
    SurfaceAffordance(
        id="start_product_help", event="open", operation=OPEN_PRODUCT_HELP.ref
    ),
    SurfaceAffordance(
        id="open_sign_in", event="open", operation=ARRIVAL_OPEN_SIGN_IN.ref
    ),
    SurfaceAffordance(
        id="open_registration",
        event="open",
        operation=ARRIVAL_OPEN_REGISTRATION.ref,
    ),
    policy_values=(
        policies.LOUNGE_SURFACE_PUBLIC,
        policies.LOUNGE_SURFACE_BOUNDARY,
        policies.LOUNGE_SURFACE_SCOPED_NAVIGATION,
    ),
)
REGISTER_SURFACE = private_surface(
    "lounge.register",
    REGISTER_FORM_ID,
    ("display_name", "email", "password"),
    SurfaceAffordance(
        id="create_owner_account", event="submit", operation=CREATE_OWNER_ACCOUNT.ref
    ),
    SurfaceAffordance(
        id="continue_to_workspace",
        event="open",
        operation=REGISTRATION_CONTINUE_TO_WORKSPACE.ref,
    ),
    SurfaceAffordance(
        id="return_to_lounge",
        event="open",
        operation=REGISTRATION_RETURN_TO_LOUNGE.ref,
    ),
    policy_values=(policies.REGISTER_SURFACE_PRIVACY,),
)
SIGN_IN_SURFACE = private_surface(
    "lounge.sign_in",
    SIGN_IN_FORM_ID,
    ("email", "password"),
    SurfaceAffordance(
        id="authenticate_owner", event="submit", operation=AUTHENTICATE_OWNER.ref
    ),
    SurfaceAffordance(
        id="continue_to_workspace",
        event="open",
        operation=SIGN_IN_CONTINUE_TO_WORKSPACE.ref,
    ),
    SurfaceAffordance(
        id="open_password_recovery",
        event="open",
        operation=SIGN_IN_OPEN_PASSWORD_RECOVERY.ref,
    ),
    SurfaceAffordance(
        id="return_to_lounge",
        event="open",
        operation=SIGN_IN_RETURN_TO_LOUNGE.ref,
    ),
    policy_values=(policies.SIGN_IN_SURFACE_PRIVACY,),
)
FORGOT_PASSWORD_SURFACE = private_surface(
    "lounge.forgot_password",
    RESET_REQUEST_FORM_ID,
    ("email",),
    SurfaceAffordance(
        id="request_password_recovery",
        event="submit",
        operation=REQUEST_PASSWORD_RESET.ref,
    ),
    SurfaceAffordance(
        id="return_to_lounge",
        event="open",
        operation=REQUEST_RESET_RETURN_TO_LOUNGE.ref,
    ),
    policy_values=(policies.RESET_REQUEST_SURFACE_NEUTRALITY,),
)
RESET_PASSWORD_SURFACE = private_surface(
    "lounge.reset_password",
    RESET_CONFIRM_FORM_ID,
    ("new_password", "token"),
    SurfaceAffordance(
        id="change_owner_password",
        event="submit",
        operation=CHANGE_OWNER_PASSWORD.ref,
    ),
    SurfaceAffordance(
        id="return_to_lounge",
        event="open",
        operation=CHANGE_PASSWORD_RETURN_TO_LOUNGE.ref,
    ),
    policy_values=(policies.RESET_CONFIRM_SURFACE_TOKEN,),
)
VERIFY_EMAIL_SURFACE = private_surface(
    "lounge.verify_email",
    VERIFY_EMAIL_FORM_ID,
    ("token",),
    SurfaceAffordance(
        id="confirm_owner_email",
        event="submit",
        operation=CONFIRM_OWNER_EMAIL.ref,
    ),
    SurfaceAffordance(
        id="return_to_lounge",
        event="open",
        operation=CONFIRM_EMAIL_RETURN_TO_LOUNGE.ref,
    ),
    policy_values=(policies.VERIFY_SURFACE_TOKEN,),
)


LOUNGE_ENTRY = Capability(
    id="lounge.entry",
    title="Establish the unauthenticated Lounge context and present Lounge home",
    operations=(
        OPEN_PRODUCT_HELP.ref,
        ARRIVAL_OPEN_REGISTRATION.ref,
        ARRIVAL_OPEN_SIGN_IN.ref,
    ),
    surfaces=(LOUNGE_SURFACE.ref,),
    policy_refs=(
        policies.ENTRY_PUBLIC_ONLY.ref,
        policies.ENTRY_COMPLETION_BOUNDARY.ref,
    ),
)
PRODUCT_HELP = Capability(
    id="lounge.product_help",
    title="Answer unauthenticated questions about Corpus and explain next steps",
    operations=(
        HELP_RETURN_TO_LOUNGE.ref,
        HELP_OPEN_REGISTRATION.ref,
        HELP_OPEN_SIGN_IN.ref,
    ),
    surfaces=(),
    policy_refs=(
        policies.HELP_PRODUCT_TRUTH.ref,
        policies.HELP_PRIVATE_BOUNDARY.ref,
        policies.HELP_TASK_REDIRECTION.ref,
    ),
)
REGISTER = Capability(
    id="lounge.create_owner",
    title="Create the owner identity and personal Workspace",
    operations=(
        CREATE_OWNER_ACCOUNT.ref,
        REGISTRATION_CONTINUE_TO_WORKSPACE.ref,
        REGISTRATION_RETURN_TO_LOUNGE.ref,
    ),
    surfaces=(REGISTER_SURFACE.ref,),
    policy_refs=(
        policies.REGISTER_EXPLICIT_INPUT.ref,
        policies.REGISTER_NO_RETRY.ref,
    ),
)
SIGN_IN = Capability(
    id="lounge.authenticate_owner",
    title="Authenticate the owner and resume the authorized Workspace",
    operations=(
        AUTHENTICATE_OWNER.ref,
        SIGN_IN_CONTINUE_TO_WORKSPACE.ref,
        SIGN_IN_OPEN_PASSWORD_RECOVERY.ref,
        SIGN_IN_RETURN_TO_LOUNGE.ref,
    ),
    surfaces=(SIGN_IN_SURFACE.ref,),
    policy_refs=(policies.SIGN_IN_AUTHORITY.ref, policies.SIGN_IN_COMPLETION.ref),
)
REQUEST_RESET = Capability(
    id="lounge.request_password_recovery",
    title="Request password-reset delivery without disclosing account existence",
    operations=(REQUEST_PASSWORD_RESET.ref, REQUEST_RESET_RETURN_TO_LOUNGE.ref),
    surfaces=(FORGOT_PASSWORD_SURFACE.ref,),
    policy_refs=(
        policies.RESET_ACCOUNT_NEUTRAL.ref,
        policies.RESET_DELIVERY_PRIVACY.ref,
    ),
)
CONFIRM_RESET = Capability(
    id="lounge.set_new_password",
    title="Change the password with a valid one-time recovery link",
    operations=(CHANGE_OWNER_PASSWORD.ref, CHANGE_PASSWORD_RETURN_TO_LOUNGE.ref),
    surfaces=(RESET_PASSWORD_SURFACE.ref,),
    policy_refs=(
        policies.PASSWORD_TOKEN_BOUNDARY.ref,
        policies.PASSWORD_CHANGE_COMPLETION.ref,
    ),
)
REQUEST_VERIFICATION = Capability(
    id="lounge.request_verification",
    title="Request a fresh verification message for the signed-in owner",
    operations=(
        REQUEST_VERIFICATION_DELIVERY.ref,
        VERIFICATION_RETURN_TO_WORKSPACE.ref,
    ),
    surfaces=(),
    policy_refs=(
        policies.VERIFICATION_SIGNED_IN_OWNER.ref,
        policies.VERIFICATION_DELIVERY_TRUTH.ref,
    ),
)
CONFIRM_VERIFICATION = Capability(
    id="lounge.confirm_verification",
    title="Validate a one-time verification link and refresh owner state",
    operations=(CONFIRM_OWNER_EMAIL.ref, CONFIRM_EMAIL_RETURN_TO_LOUNGE.ref),
    surfaces=(VERIFY_EMAIL_SURFACE.ref,),
    policy_refs=(
        policies.VERIFICATION_TOKEN_BOUNDARY.ref,
        policies.VERIFICATION_REFRESH_TRUTH.ref,
    ),
)


LOUNGE_NODE = Node(
    id=LOUNGE_REF.id,
    title="Lounge",
    kind=NodeKind.SECTION,
    route=Route(template="/", deep_link_policy=DeepLinkPolicy.SHAREABLE),
    entry_turn=EntryTurnDeclaration(id="welcome"),
    operations=(
        OPEN_PRODUCT_HELP,
        ARRIVAL_OPEN_REGISTRATION,
        ARRIVAL_OPEN_SIGN_IN,
    ),
    outgoing=(
        Transition(operation=OPEN_PRODUCT_HELP.ref, outcome="opened", target=PRODUCT_HELP_REF),
        Transition(operation=ARRIVAL_OPEN_REGISTRATION.ref, outcome="opened", target=REGISTER_REF),
        Transition(operation=ARRIVAL_OPEN_SIGN_IN.ref, outcome="opened", target=SIGN_IN_REF),
    ),
    capabilities=(LOUNGE_ENTRY,),
    surfaces=SurfaceSlots(active=LOUNGE_SURFACE),
    policy_refs=(policies.PUBLIC_NODE_CONTEXT.ref, policies.PUBLIC_NODE_PATHS.ref),
)
PRODUCT_HELP_NODE = Node(
    id=PRODUCT_HELP_REF.id,
    title="Product help",
    kind=NodeKind.SECTION,
    parent=LOUNGE_REF,
    route=Route(template="/help", deep_link_policy=DeepLinkPolicy.SHAREABLE),
    operations=(HELP_RETURN_TO_LOUNGE, HELP_OPEN_REGISTRATION, HELP_OPEN_SIGN_IN),
    outgoing=(
        Transition(operation=HELP_RETURN_TO_LOUNGE.ref, outcome="opened", target=LOUNGE_REF),
        Transition(operation=HELP_OPEN_REGISTRATION.ref, outcome="opened", target=REGISTER_REF),
        Transition(operation=HELP_OPEN_SIGN_IN.ref, outcome="opened", target=SIGN_IN_REF),
    ),
    capabilities=(PRODUCT_HELP,),
    surfaces=SurfaceSlots(),
    suggested_actions=(
        SuggestedAction(
            id="lounge.product_help.sign_in",
            operation_id=HELP_OPEN_SIGN_IN.id,
            label="Sign in",
        ),
        SuggestedAction(
            id="lounge.product_help.sign_up",
            operation_id=HELP_OPEN_REGISTRATION.id,
            label="Sign up",
        ),
    ),
    policy_refs=(policies.PUBLIC_NODE_CONTEXT.ref, policies.PUBLIC_NODE_PATHS.ref),
)
REGISTER_NODE = Node(
    id=REGISTER_REF.id,
    title="Create account",
    kind=NodeKind.SECTION,
    parent=LOUNGE_REF,
    route=Route(template="/register", deep_link_policy=DeepLinkPolicy.SHAREABLE),
    context_providers=(OWNER_CONTEXT_PROVIDER,),
    conversation_input=CREDENTIAL_INPUT,
    operations=(
        CREATE_OWNER_ACCOUNT,
        REGISTRATION_CONTINUE_TO_WORKSPACE,
        REGISTRATION_RETURN_TO_LOUNGE,
    ),
    outgoing=(
        Transition(operation=CREATE_OWNER_ACCOUNT.ref, outcome="created", target=HOME_REF),
        Transition(operation=REGISTRATION_CONTINUE_TO_WORKSPACE.ref, outcome="opened", target=HOME_REF),
        Transition(operation=REGISTRATION_RETURN_TO_LOUNGE.ref, outcome="opened", target=LOUNGE_REF),
    ),
    capabilities=(REGISTER,),
    surfaces=SurfaceSlots(active=REGISTER_SURFACE),
    suggested_actions=(
        SuggestedAction(id="lounge.register.submit", operation_id=CREATE_OWNER_ACCOUNT.id, label="Sign up"),
        SuggestedAction(id="lounge.register.continue", operation_id=REGISTRATION_CONTINUE_TO_WORKSPACE.id, label="Continue to Workspace"),
    ),
    policy_refs=(
        policies.REGISTRATION_NODE_PRIVACY.ref,
        policies.REGISTRATION_NODE_PARTIAL_SUCCESS.ref,
    ),
)
SIGN_IN_NODE = Node(
    id=SIGN_IN_REF.id,
    title="Sign in",
    kind=NodeKind.SECTION,
    parent=LOUNGE_REF,
    route=Route(template="/sign-in", deep_link_policy=DeepLinkPolicy.SHAREABLE),
    context_providers=(OWNER_CONTEXT_PROVIDER,),
    conversation_input=CREDENTIAL_INPUT,
    operations=(
        AUTHENTICATE_OWNER,
        SIGN_IN_CONTINUE_TO_WORKSPACE,
        SIGN_IN_OPEN_PASSWORD_RECOVERY,
        SIGN_IN_RETURN_TO_LOUNGE,
    ),
    outgoing=(
        Transition(operation=AUTHENTICATE_OWNER.ref, outcome="authenticated", target=HOME_REF),
        Transition(operation=SIGN_IN_CONTINUE_TO_WORKSPACE.ref, outcome="opened", target=HOME_REF),
        Transition(operation=SIGN_IN_OPEN_PASSWORD_RECOVERY.ref, outcome="opened", target=FORGOT_PASSWORD_REF),
        Transition(operation=SIGN_IN_RETURN_TO_LOUNGE.ref, outcome="opened", target=LOUNGE_REF),
    ),
    capabilities=(SIGN_IN,),
    surfaces=SurfaceSlots(active=SIGN_IN_SURFACE),
    suggested_actions=(
        SuggestedAction(id="lounge.sign_in.submit", operation_id=AUTHENTICATE_OWNER.id, label="Sign in"),
        SuggestedAction(id="lounge.sign_in.continue", operation_id=SIGN_IN_CONTINUE_TO_WORKSPACE.id, label="Continue to Workspace"),
    ),
    policy_refs=(policies.SIGN_IN_NODE_PRIVACY.ref, policies.SIGN_IN_NODE_FAILURE.ref),
)
FORGOT_PASSWORD_NODE = Node(
    id=FORGOT_PASSWORD_REF.id,
    title="Request password recovery",
    kind=NodeKind.SECTION,
    parent=LOUNGE_REF,
    route=Route(template="/forgot-password", deep_link_policy=DeepLinkPolicy.SHAREABLE),
    conversation_input=CREDENTIAL_INPUT,
    operations=(REQUEST_PASSWORD_RESET, REQUEST_RESET_RETURN_TO_LOUNGE),
    outgoing=(
        Transition(operation=REQUEST_PASSWORD_RESET.ref, outcome="requested", target=FORGOT_PASSWORD_REF),
        Transition(operation=REQUEST_RESET_RETURN_TO_LOUNGE.ref, outcome="opened", target=LOUNGE_REF),
    ),
    capabilities=(REQUEST_RESET,),
    surfaces=SurfaceSlots(active=FORGOT_PASSWORD_SURFACE),
    suggested_actions=(
        SuggestedAction(id="lounge.password_reset.request", operation_id=REQUEST_PASSWORD_RESET.id, label="Send recovery link"),
    ),
    policy_refs=(policies.RESET_NODE_TOKEN_PRIVACY.ref, policies.RESET_NODE_TOKEN_FAILURE.ref),
)
RESET_PASSWORD_NODE = Node(
    id=RESET_PASSWORD_REF.id,
    title="Set a new password",
    kind=NodeKind.SECTION,
    parent=LOUNGE_REF,
    route=Route(template="/reset-password", deep_link_policy=DeepLinkPolicy.SHAREABLE),
    conversation_input=CREDENTIAL_INPUT,
    operations=(CHANGE_OWNER_PASSWORD, CHANGE_PASSWORD_RETURN_TO_LOUNGE),
    outgoing=(
        Transition(operation=CHANGE_OWNER_PASSWORD.ref, outcome="changed", target=SIGN_IN_REF),
        Transition(operation=CHANGE_PASSWORD_RETURN_TO_LOUNGE.ref, outcome="opened", target=LOUNGE_REF),
    ),
    capabilities=(CONFIRM_RESET,),
    surfaces=SurfaceSlots(active=RESET_PASSWORD_SURFACE),
    suggested_actions=(
        SuggestedAction(id="lounge.password_reset.confirm", operation_id=CHANGE_OWNER_PASSWORD.id, label="Set new password"),
    ),
    policy_refs=(policies.RESET_NODE_TOKEN_PRIVACY.ref, policies.RESET_NODE_TOKEN_FAILURE.ref),
)
VERIFICATION_PENDING_NODE = Node(
    id=VERIFICATION_PENDING_REF.id,
    title="Resend email verification",
    kind=NodeKind.SECTION,
    parent=LOUNGE_REF,
    route=Route(template="/verification-pending", deep_link_policy=DeepLinkPolicy.SESSION_BOUND),
    context_providers=(OWNER_CONTEXT_PROVIDER,),
    operations=(REQUEST_VERIFICATION_DELIVERY, VERIFICATION_RETURN_TO_WORKSPACE),
    outgoing=(
        Transition(operation=REQUEST_VERIFICATION_DELIVERY.ref, outcome="requested", target=VERIFICATION_PENDING_REF),
        Transition(operation=VERIFICATION_RETURN_TO_WORKSPACE.ref, outcome="opened", target=HOME_REF),
    ),
    capabilities=(REQUEST_VERIFICATION,),
    surfaces=SurfaceSlots(),
    suggested_actions=(
        SuggestedAction(id="lounge.verification.resend", operation_id=REQUEST_VERIFICATION_DELIVERY.id, label="Resend verification"),
        SuggestedAction(id="lounge.verification.return", operation_id=VERIFICATION_RETURN_TO_WORKSPACE.id, label="Return to Workspace"),
    ),
    policy_refs=(
        policies.VERIFICATION_NODE_TOKEN_PRIVACY.ref,
        policies.VERIFICATION_NODE_ADVISORY.ref,
    ),
)
VERIFY_EMAIL_NODE = Node(
    id=VERIFY_EMAIL_REF.id,
    title="Confirm email verification",
    kind=NodeKind.SECTION,
    parent=LOUNGE_REF,
    route=Route(template="/verify", deep_link_policy=DeepLinkPolicy.SHAREABLE),
    conversation_input=CREDENTIAL_INPUT,
    operations=(CONFIRM_OWNER_EMAIL, CONFIRM_EMAIL_RETURN_TO_LOUNGE),
    outgoing=(
        Transition(operation=CONFIRM_OWNER_EMAIL.ref, outcome="confirmed", target=VERIFY_EMAIL_REF),
        Transition(operation=CONFIRM_EMAIL_RETURN_TO_LOUNGE.ref, outcome="opened", target=LOUNGE_REF),
    ),
    capabilities=(CONFIRM_VERIFICATION,),
    surfaces=SurfaceSlots(active=VERIFY_EMAIL_SURFACE),
    suggested_actions=(
        SuggestedAction(id="lounge.verification.confirm", operation_id=CONFIRM_OWNER_EMAIL.id, label="Verify email"),
    ),
    policy_refs=(
        policies.VERIFICATION_NODE_TOKEN_PRIVACY.ref,
        policies.VERIFICATION_NODE_ADVISORY.ref,
    ),
)


LOUNGE_FEATURE = Feature(
    namespace="lounge",
    nodes=(
        LOUNGE_NODE,
        PRODUCT_HELP_NODE,
        REGISTER_NODE,
        SIGN_IN_NODE,
        FORGOT_PASSWORD_NODE,
        RESET_PASSWORD_NODE,
        VERIFICATION_PENDING_NODE,
        VERIFY_EMAIL_NODE,
    ),
    agent_policies=policies.LOUNGE_AGENT_POLICIES,
    policy_refs=(
        policies.FEATURE_PROMPT.ref,
        policies.PUBLIC_CONTEXT_ONLY.ref,
        policies.LOUNGE_TASK_BOUNDARY.ref,
        policies.LOUNGE_TASK_REDIRECTION.ref,
        policies.ACCOUNT_ACCESS_BOUNDARY.ref,
        policies.LOUNGE_CHROME_BOUNDARY.ref,
        policies.USER_FACING_LANGUAGE.ref,
    ),
)


__all__ = [
    "FORGOT_PASSWORD_NODE",
    "LOUNGE_FEATURE",
    "LOUNGE_NODE",
    "LOUNGE_SURFACE",
    "PRODUCT_HELP_NODE",
    "REGISTER_NODE",
    "RESET_PASSWORD_NODE",
    "SIGN_IN_NODE",
    "VERIFICATION_PENDING_NODE",
    "VERIFY_EMAIL_NODE",
]
