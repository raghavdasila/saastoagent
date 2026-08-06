from routedeck_core.contracts.navigation import NodeRef
from routedeck_core.contracts.operations import ContextProvider
from routedeck_core.contracts.projection import FrozenJsonObject


HOME_REF = NodeRef(id="workspace.home")
WORKSPACE_OVERVIEW_PROVIDER = ContextProvider(
    id="workspace.overview_context",
    description=(
        "Current authenticated Workspace overview, including explicit "
        "unavailable sections."
    ),
    output_schema=FrozenJsonObject(
        {
            "type": "object",
            "properties": {
                "agent_count": {"type": "integer", "minimum": 0},
                "agents": {"$ref": "#/$defs/section"},
                "sources": {"$ref": "#/$defs/section"},
                "recent_activity": {"$ref": "#/$defs/section"},
            },
            "required": [
                "agent_count",
                "agents",
                "sources",
                "recent_activity",
            ],
            "additionalProperties": False,
            "$defs": {
                "section": {
                    "type": "object",
                    "properties": {
                        "status": {
                            "type": "string",
                            "enum": ["available", "empty", "unavailable"],
                        },
                        "message": {"type": "string"},
                    },
                    "required": ["status", "message"],
                    "additionalProperties": False,
                }
            },
        }
    ),
)

__all__ = ["HOME_REF", "WORKSPACE_OVERVIEW_PROVIDER"]
