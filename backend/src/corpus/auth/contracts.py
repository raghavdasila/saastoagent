from __future__ import annotations

from dataclasses import dataclass

from routedeck_core.contracts.operations import ContextProvider
from routedeck_core.contracts.projection import FrozenJsonObject


OWNER_CONTEXT_PROVIDER = ContextProvider(
    id="corpus.owner_context",
    description=(
        "Authenticated Corpus owner and organization context for this "
        "RouteDeck session."
    ),
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


@dataclass(frozen=True)
class OwnerRouteContext:
    display_name: str | None
    organization_name: str
    organization_slug: str
    role: str
    is_verified: bool


__all__ = ["OWNER_CONTEXT_PROVIDER", "OwnerRouteContext"]
