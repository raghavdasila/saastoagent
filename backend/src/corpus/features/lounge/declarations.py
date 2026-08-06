from __future__ import annotations

from routedeck_core.contracts.navigation import NodeRef
from routedeck_core.contracts.operations import Operation, OperationSource, SafetyClass
from routedeck_core.contracts.projection import FrozenJsonObject

from corpus.auth.contracts import OWNER_CONTEXT_PROVIDER
from corpus.shared.schemas import EMPTY_OBJECT_SCHEMA

from . import policies


def operation(
    operation_id: str,
    title: str,
    description: str,
    outcome: str,
    *policy_values,
    allowed_sources: frozenset[OperationSource],
    safety_class: SafetyClass = SafetyClass.NAVIGATION,
    authenticated: bool = False,
) -> Operation:
    return Operation(
        id=operation_id,
        title=title,
        description=description,
        input_schema=FrozenJsonObject(EMPTY_OBJECT_SCHEMA),
        safety_class=safety_class,
        allowed_sources=allowed_sources,
        outcomes=(outcome,),
        outcome_schemas=FrozenJsonObject({outcome: EMPTY_OBJECT_SCHEMA}),
        provider_refs=(OWNER_CONTEXT_PROVIDER.ref,) if authenticated else (),
        policy_refs=tuple(value.ref for value in policy_values),
    )


OPEN_PRODUCT_HELP = operation(
    "lounge.open_product_help",
    "Start product help",
    "Move the public conversation into product-help context.",
    "opened",
    policies.ARRIVAL_START_HELP,
    allowed_sources=frozenset({OperationSource.AGENT, OperationSource.SURFACE}),
)
ARRIVAL_OPEN_REGISTRATION = operation(
    "lounge.arrival.open_registration",
    "Open owner registration",
    "Open owner registration from Lounge home.",
    "opened",
    policies.ARRIVAL_OPEN_REGISTER,
    allowed_sources=frozenset({OperationSource.AGENT, OperationSource.SURFACE}),
)
ARRIVAL_OPEN_SIGN_IN = operation(
    "lounge.arrival.open_sign_in",
    "Open owner sign-in",
    "Open owner sign-in from Lounge home.",
    "opened",
    policies.ARRIVAL_OPEN_SIGN_IN,
    allowed_sources=frozenset({OperationSource.AGENT, OperationSource.SURFACE}),
)

HELP_RETURN_TO_LOUNGE = operation(
    "lounge.product_help.return_to_lounge",
    "Return to Lounge",
    "Return from product help to Lounge orientation.",
    "opened",
    policies.HELP_RETURN,
    allowed_sources=frozenset({OperationSource.AGENT}),
)
HELP_OPEN_REGISTRATION = operation(
    "lounge.product_help.open_registration",
    "Open owner registration",
    "Open registration when product help reaches private Workspace work.",
    "opened",
    policies.HELP_OPEN_REGISTER,
    allowed_sources=frozenset({OperationSource.AGENT, OperationSource.SURFACE}),
)
HELP_OPEN_SIGN_IN = operation(
    "lounge.product_help.open_sign_in",
    "Open owner sign-in",
    "Open sign-in when product help reaches private Workspace work.",
    "opened",
    policies.HELP_OPEN_SIGN_IN,
    allowed_sources=frozenset({OperationSource.AGENT, OperationSource.SURFACE}),
)

CREATE_OWNER_ACCOUNT = operation(
    "lounge.create_owner_account",
    "Create owner account",
    "Create the owner identity and personal Workspace from the private form.",
    "created",
    policies.REGISTER_SUBMIT,
    policies.REGISTER_SUCCESS,
    allowed_sources=frozenset({OperationSource.SURFACE}),
    safety_class=SafetyClass.CREDENTIAL,
)
REGISTRATION_CONTINUE_TO_WORKSPACE = operation(
    "lounge.registration.continue_to_workspace",
    "Continue to Workspace",
    "Continue an authenticated owner into the authorized Workspace.",
    "opened",
    policies.REGISTER_CONTINUE,
    allowed_sources=frozenset({OperationSource.SURFACE}),
    authenticated=True,
)
REGISTRATION_RETURN_TO_LOUNGE = operation(
    "lounge.registration.return_to_lounge",
    "Return to Lounge",
    "Leave registration and return to Lounge.",
    "opened",
    policies.REGISTER_RETURN,
    allowed_sources=frozenset({OperationSource.SURFACE}),
)

AUTHENTICATE_OWNER = operation(
    "lounge.authenticate_owner_account",
    "Authenticate owner",
    "Authenticate the owner from the private sign-in form.",
    "authenticated",
    policies.SIGN_IN_SUBMIT,
    allowed_sources=frozenset({OperationSource.SURFACE}),
    safety_class=SafetyClass.CREDENTIAL,
)
SIGN_IN_CONTINUE_TO_WORKSPACE = operation(
    "lounge.sign_in.continue_to_workspace",
    "Continue to Workspace",
    "Continue an authenticated owner into the authorized Workspace.",
    "opened",
    policies.SIGN_IN_CONTINUE,
    allowed_sources=frozenset({OperationSource.SURFACE}),
    authenticated=True,
)
SIGN_IN_OPEN_PASSWORD_RECOVERY = operation(
    "lounge.sign_in.open_password_recovery",
    "Open password recovery",
    "Open account-neutral password recovery.",
    "opened",
    policies.SIGN_IN_OPEN_RECOVERY,
    allowed_sources=frozenset({OperationSource.AGENT, OperationSource.SURFACE}),
)
SIGN_IN_RETURN_TO_LOUNGE = operation(
    "lounge.sign_in.return_to_lounge",
    "Return to Lounge",
    "Leave sign-in and return to Lounge.",
    "opened",
    policies.SIGN_IN_RETURN,
    allowed_sources=frozenset({OperationSource.SURFACE}),
)

REQUEST_PASSWORD_RESET = operation(
    "lounge.request_password_reset",
    "Request password recovery",
    "Request an account-neutral password recovery message from the private form.",
    "requested",
    policies.RESET_REQUEST_SUBMIT_NEUTRAL,
    policies.RESET_REQUEST_NOT_PROOF,
    allowed_sources=frozenset({OperationSource.SURFACE}),
    safety_class=SafetyClass.CREDENTIAL,
)
REQUEST_RESET_RETURN_TO_LOUNGE = operation(
    "lounge.request_password_reset.return_to_lounge",
    "Return to Lounge",
    "Leave password recovery and return to Lounge.",
    "opened",
    policies.RESET_REQUEST_RETURN,
    allowed_sources=frozenset({OperationSource.SURFACE}),
)

CHANGE_OWNER_PASSWORD = operation(
    "lounge.change_owner_password",
    "Change owner password",
    "Change the password from the private one-time-token form.",
    "changed",
    policies.PASSWORD_CHANGE_TOKEN,
    allowed_sources=frozenset({OperationSource.SURFACE}),
    safety_class=SafetyClass.CREDENTIAL,
)
CHANGE_PASSWORD_RETURN_TO_LOUNGE = operation(
    "lounge.change_password.return_to_lounge",
    "Return to Lounge",
    "Leave password reset and return to Lounge.",
    "opened",
    policies.PASSWORD_CHANGE_RETURN,
    allowed_sources=frozenset({OperationSource.SURFACE}),
)

REQUEST_VERIFICATION_DELIVERY = operation(
    "lounge.request_verification_delivery",
    "Request verification delivery",
    "Request a fresh verification message for the signed-in owner.",
    "requested",
    policies.VERIFICATION_REQUEST_EXPLICIT,
    policies.VERIFICATION_REQUEST_RESULT,
    allowed_sources=frozenset({OperationSource.SURFACE}),
    safety_class=SafetyClass.CREDENTIAL,
    authenticated=True,
)
VERIFICATION_RETURN_TO_WORKSPACE = operation(
    "lounge.verification_delivery.return_to_workspace",
    "Return to Workspace",
    "Return to the authenticated Workspace without changing verification state.",
    "opened",
    policies.VERIFICATION_RETURN_WORKSPACE,
    allowed_sources=frozenset({OperationSource.SURFACE}),
    authenticated=True,
)

CONFIRM_OWNER_EMAIL = operation(
    "lounge.confirm_owner_email",
    "Confirm owner email",
    "Confirm the owner email from the private one-time-token form.",
    "confirmed",
    policies.VERIFY_CONFIRM_OWNER,
    allowed_sources=frozenset({OperationSource.SURFACE}),
    safety_class=SafetyClass.CREDENTIAL,
)
CONFIRM_EMAIL_RETURN_TO_LOUNGE = operation(
    "lounge.confirm_email.return_to_lounge",
    "Return to Lounge",
    "Leave email confirmation and return to Lounge.",
    "opened",
    policies.VERIFY_RETURN,
    allowed_sources=frozenset({OperationSource.SURFACE}),
)


LOUNGE_REF = NodeRef(id="lounge.home")
PRODUCT_HELP_REF = NodeRef(id="lounge.product_help")
SIGN_IN_REF = NodeRef(id="lounge.sign_in")
REGISTER_REF = NodeRef(id="lounge.register")
FORGOT_PASSWORD_REF = NodeRef(id="lounge.forgot_password")
RESET_PASSWORD_REF = NodeRef(id="lounge.reset_password")
VERIFICATION_PENDING_REF = NodeRef(id="lounge.verification_pending")
VERIFY_EMAIL_REF = NodeRef(id="lounge.verify_email")

REGISTER_FORM_ID = "lounge-register"
SIGN_IN_FORM_ID = "lounge-sign-in"
RESET_REQUEST_FORM_ID = "lounge-password-reset-request"
RESET_CONFIRM_FORM_ID = "lounge-password-reset-confirm"
VERIFY_EMAIL_FORM_ID = "lounge-email-verification"


__all__ = [
    "ARRIVAL_OPEN_REGISTRATION",
    "ARRIVAL_OPEN_SIGN_IN",
    "AUTHENTICATE_OWNER",
    "CHANGE_OWNER_PASSWORD",
    "CHANGE_PASSWORD_RETURN_TO_LOUNGE",
    "CONFIRM_EMAIL_RETURN_TO_LOUNGE",
    "CONFIRM_OWNER_EMAIL",
    "CREATE_OWNER_ACCOUNT",
    "FORGOT_PASSWORD_REF",
    "HELP_OPEN_REGISTRATION",
    "HELP_OPEN_SIGN_IN",
    "HELP_RETURN_TO_LOUNGE",
    "LOUNGE_REF",
    "OPEN_PRODUCT_HELP",
    "PRODUCT_HELP_REF",
    "REGISTER_FORM_ID",
    "REGISTER_REF",
    "REGISTRATION_CONTINUE_TO_WORKSPACE",
    "REGISTRATION_RETURN_TO_LOUNGE",
    "REQUEST_PASSWORD_RESET",
    "REQUEST_RESET_RETURN_TO_LOUNGE",
    "REQUEST_VERIFICATION_DELIVERY",
    "RESET_CONFIRM_FORM_ID",
    "RESET_PASSWORD_REF",
    "RESET_REQUEST_FORM_ID",
    "SIGN_IN_CONTINUE_TO_WORKSPACE",
    "SIGN_IN_FORM_ID",
    "SIGN_IN_OPEN_PASSWORD_RECOVERY",
    "SIGN_IN_REF",
    "SIGN_IN_RETURN_TO_LOUNGE",
    "VERIFICATION_PENDING_REF",
    "VERIFICATION_RETURN_TO_WORKSPACE",
    "VERIFY_EMAIL_FORM_ID",
    "VERIFY_EMAIL_REF",
]
