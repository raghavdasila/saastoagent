from __future__ import annotations

from routedeck_core.contracts.navigation import NodeRef
from routedeck_core.contracts.operations import ContextProvider, Operation, SafetyClass
from routedeck_core.contracts.projection import FrozenJsonObject


EMPTY_OBJECT_SCHEMA = {
    "type": "object",
    "properties": {},
    "additionalProperties": False,
}
NAVIGATION_OUTCOME_SCHEMAS = FrozenJsonObject(
    {"opened": EMPTY_OBJECT_SCHEMA}
)

OPEN_SIGN_IN = Operation(
    id="workspace.open_sign_in",
    title="Sign in",
    description="Open the sign-in surface without claiming authentication success.",
    input_schema=FrozenJsonObject(EMPTY_OBJECT_SCHEMA),
    safety_class=SafetyClass.NAVIGATION,
    outcomes=("opened",),
    outcome_schemas=NAVIGATION_OUTCOME_SCHEMAS,
)
OPEN_REGISTRATION = Operation(
    id="workspace.open_registration",
    title="Create account",
    description=(
        "Open the registration surface without claiming account creation success."
    ),
    input_schema=FrozenJsonObject(EMPTY_OBJECT_SCHEMA),
    safety_class=SafetyClass.NAVIGATION,
    outcomes=("opened",),
    outcome_schemas=NAVIGATION_OUTCOME_SCHEMAS,
)
OWNER_CONTEXT_PROVIDER = ContextProvider(
    id="workspace.owner_context",
    description="Corpus owner and personal-organization context for this RouteDeck session.",
    output_schema=FrozenJsonObject(
        {
            "type": "object",
            "properties": {
                "display_name": {"type": ["string", "null"]},
                "organization_name": {"type": "string"},
                "organization_slug": {"type": "string"},
                "role": {"type": "string", "enum": ["owner", "admin", "member"]},
                "is_verified": {"type": "boolean"},
            },
            "required": [
                "display_name",
                "organization_name",
                "organization_slug",
                "role",
                "is_verified",
            ],
            "additionalProperties": False,
        }
    ),
)
AUTHENTICATION_COMPLETED = Operation(
    id="workspace.authentication_completed",
    title="Continue to Workspace",
    description="Continue an authenticated owner into their claimed Workspace.",
    input_schema=FrozenJsonObject(EMPTY_OBJECT_SCHEMA),
    safety_class=SafetyClass.NAVIGATION,
    outcomes=("opened",),
    outcome_schemas=NAVIGATION_OUTCOME_SCHEMAS,
    provider_refs=(OWNER_CONTEXT_PROVIDER.ref,),
)
OPEN_SOURCES = Operation(
    id="workspace.open_sources",
    title="Open Sources",
    description="Open the authenticated owner's Sources workspace.",
    input_schema=FrozenJsonObject(EMPTY_OBJECT_SCHEMA),
    safety_class=SafetyClass.NAVIGATION,
    outcomes=("opened",),
    outcome_schemas=NAVIGATION_OUTCOME_SCHEMAS,
    provider_refs=(OWNER_CONTEXT_PROVIDER.ref,),
)
OPEN_FORGOT_PASSWORD = Operation(
    id="workspace.open_forgot_password",
    title="Forgot password",
    description="Open the password-reset request surface.",
    input_schema=FrozenJsonObject(EMPTY_OBJECT_SCHEMA),
    safety_class=SafetyClass.NAVIGATION,
    outcomes=("opened",),
    outcome_schemas=NAVIGATION_OUTCOME_SCHEMAS,
)
OPEN_RESET_PASSWORD = Operation(
    id="workspace.open_reset_password",
    title="Reset password",
    description="Open the token-backed password reset surface.",
    input_schema=FrozenJsonObject(EMPTY_OBJECT_SCHEMA),
    safety_class=SafetyClass.NAVIGATION,
    outcomes=("opened",),
    outcome_schemas=NAVIGATION_OUTCOME_SCHEMAS,
)
OPEN_VERIFY_EMAIL = Operation(
    id="workspace.open_verify_email",
    title="Verify email",
    description="Open the token-backed email verification surface.",
    input_schema=FrozenJsonObject(EMPTY_OBJECT_SCHEMA),
    safety_class=SafetyClass.NAVIGATION,
    outcomes=("opened",),
    outcome_schemas=NAVIGATION_OUTCOME_SCHEMAS,
)
RETURN_TO_LOUNGE = Operation(
    id="workspace.return_to_lounge",
    title="Return to Lounge",
    description="Return to the unauthenticated Lounge.",
    input_schema=FrozenJsonObject(EMPTY_OBJECT_SCHEMA),
    safety_class=SafetyClass.NAVIGATION,
    outcomes=("opened",),
    outcome_schemas=NAVIGATION_OUTCOME_SCHEMAS,
)

LOUNGE_REF = NodeRef(id="workspace.lounge")
SIGN_IN_REF = NodeRef(id="workspace.sign_in")
REGISTER_REF = NodeRef(id="workspace.register")
FORGOT_PASSWORD_REF = NodeRef(id="workspace.forgot_password")
RESET_PASSWORD_REF = NodeRef(id="workspace.reset_password")
VERIFY_EMAIL_REF = NodeRef(id="workspace.verify_email")
HOME_REF = NodeRef(id="workspace.home")


__all__ = [
    "EMPTY_OBJECT_SCHEMA",
    "AUTHENTICATION_COMPLETED",
    "FORGOT_PASSWORD_REF",
    "HOME_REF",
    "LOUNGE_REF",
    "OPEN_REGISTRATION",
    "OPEN_FORGOT_PASSWORD",
    "OPEN_RESET_PASSWORD",
    "OPEN_VERIFY_EMAIL",
    "OPEN_SIGN_IN",
    "OPEN_SOURCES",
    "REGISTER_REF",
    "RESET_PASSWORD_REF",
    "RETURN_TO_LOUNGE",
    "SIGN_IN_REF",
    "VERIFY_EMAIL_REF",
    "OWNER_CONTEXT_PROVIDER",
]
