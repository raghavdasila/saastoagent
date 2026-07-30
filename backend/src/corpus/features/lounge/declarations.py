from __future__ import annotations

from routedeck_core.contracts.navigation import NodeRef
from routedeck_core.contracts.operations import Operation, SafetyClass
from routedeck_core.contracts.projection import FrozenJsonObject

from corpus.features.workspace.declarations import (
    EMPTY_OBJECT_SCHEMA,
    HOME_REF,
    NAVIGATION_OUTCOME_SCHEMAS,
    OWNER_CONTEXT_PROVIDER,
)


def navigation_operation(
    operation_id: str,
    title: str,
    description: str,
    *,
    authenticated: bool = False,
) -> Operation:
    return Operation(
        id=operation_id,
        title=title,
        description=description,
        input_schema=FrozenJsonObject(EMPTY_OBJECT_SCHEMA),
        safety_class=SafetyClass.NAVIGATION,
        outcomes=("opened",),
        outcome_schemas=NAVIGATION_OUTCOME_SCHEMAS,
        provider_refs=(OWNER_CONTEXT_PROVIDER.ref,) if authenticated else (),
    )


OPEN_SIGN_IN = navigation_operation(
    "lounge.open_sign_in", "Sign in", "Open the sign-in surface."
)
OPEN_REGISTRATION = navigation_operation(
    "lounge.open_registration", "Create account", "Open the account-creation surface."
)
OPEN_FORGOT_PASSWORD = navigation_operation(
    "lounge.open_forgot_password", "Forgot password", "Open password recovery."
)
OPEN_RESET_PASSWORD = navigation_operation(
    "lounge.open_reset_password", "Reset password", "Open token-backed password reset."
)
OPEN_VERIFY_EMAIL = navigation_operation(
    "lounge.open_verify_email", "Verify email", "Open token-backed email verification."
)
RETURN_TO_LOUNGE = navigation_operation(
    "lounge.return_to_lounge", "Return to Lounge", "Return to the public Lounge."
)
AUTHENTICATION_COMPLETED = navigation_operation(
    "lounge.authentication_completed",
    "Continue to Workspace",
    "Continue an authenticated owner into their Workspace.",
    authenticated=True,
)
RETURN_TO_WORKSPACE = navigation_operation(
    "lounge.return_to_workspace",
    "Return to Workspace",
    "Return the signed-in owner to Workspace.",
    authenticated=True,
)

LOUNGE_REF = NodeRef(id="lounge.home")
SIGN_IN_REF = NodeRef(id="lounge.sign_in")
REGISTER_REF = NodeRef(id="lounge.register")
FORGOT_PASSWORD_REF = NodeRef(id="lounge.forgot_password")
RESET_PASSWORD_REF = NodeRef(id="lounge.reset_password")
VERIFY_EMAIL_REF = NodeRef(id="lounge.verify_email")
VERIFICATION_PENDING_REF = NodeRef(id="lounge.verification_pending")

__all__ = [
    "AUTHENTICATION_COMPLETED",
    "FORGOT_PASSWORD_REF",
    "HOME_REF",
    "LOUNGE_REF",
    "OPEN_FORGOT_PASSWORD",
    "OPEN_REGISTRATION",
    "OPEN_RESET_PASSWORD",
    "OPEN_SIGN_IN",
    "OPEN_VERIFY_EMAIL",
    "REGISTER_REF",
    "RESET_PASSWORD_REF",
    "RETURN_TO_LOUNGE",
    "RETURN_TO_WORKSPACE",
    "SIGN_IN_REF",
    "VERIFY_EMAIL_REF",
    "VERIFICATION_PENDING_REF",
]
