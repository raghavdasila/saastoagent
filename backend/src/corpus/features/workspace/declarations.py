from __future__ import annotations

from routedeck_core.contracts.navigation import NodeRef
from routedeck_core.contracts.operations import ContextProvider, Operation, SafetyClass
from routedeck_core.contracts.projection import FrozenJsonObject


EMPTY_OBJECT_SCHEMA = {
    "type": "object",
    "properties": {},
    "additionalProperties": False,
}
NAVIGATION_OUTCOME_SCHEMAS = FrozenJsonObject({"opened": EMPTY_OBJECT_SCHEMA})
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
OPEN_VERIFICATION = Operation(
    id="workspace.open_verification",
    title="Manage email verification",
    description="Open verification delivery for the signed-in owner.",
    input_schema=FrozenJsonObject(EMPTY_OBJECT_SCHEMA),
    safety_class=SafetyClass.NAVIGATION,
    outcomes=("opened",),
    outcome_schemas=NAVIGATION_OUTCOME_SCHEMAS,
    provider_refs=(OWNER_CONTEXT_PROVIDER.ref,),
)
HOME_REF = NodeRef(id="workspace.home")


__all__ = [
    "EMPTY_OBJECT_SCHEMA",
    "HOME_REF",
    "OPEN_SOURCES",
    "OPEN_VERIFICATION",
    "OWNER_CONTEXT_PROVIDER",
]
