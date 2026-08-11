from __future__ import annotations

from routedeck_core.contracts.operations import (
    Operation,
    OperationSource,
    SafetyClass,
)
from routedeck_core.contracts.projection import FrozenJsonObject

from corpus.auth.contracts import OWNER_CONTEXT_PROVIDER
from corpus.shared.schemas import EMPTY_OBJECT_SCHEMA

NAVIGATION_OUTCOME_SCHEMAS = FrozenJsonObject({"opened": EMPTY_OBJECT_SCHEMA})
OPEN_AGENTS = Operation(
    id="workspace.open_agents",
    title="Open Agents",
    description=(
        "Open Agents for explicit Agent inventory or configuration work, or after "
        "the Source prerequisite in an ongoing file-first setup has begun. Do not "
        "skip an attached API definition that the current request still needs added "
        "and analyzed."
    ),
    input_schema=FrozenJsonObject(EMPTY_OBJECT_SCHEMA),
    safety_class=SafetyClass.NAVIGATION,
    allowed_sources=frozenset({OperationSource.AGENT, OperationSource.SURFACE}),
    outcomes=("opened",),
    outcome_schemas=NAVIGATION_OUTCOME_SCHEMAS,
    provider_refs=(OWNER_CONTEXT_PROVIDER.ref,),
)
OPEN_SOURCES = Operation(
    id="workspace.open_sources",
    title="Open Sources",
    description=(
        "Open Sources for work owned by a Source. When the current request includes "
        "a staged API definition to add, analyze, or use in broader setup, open "
        "Sources first so that exact file becomes an identifiable Source before "
        "choosing or creating an Agent."
    ),
    input_schema=FrozenJsonObject(EMPTY_OBJECT_SCHEMA),
    safety_class=SafetyClass.NAVIGATION,
    allowed_sources=frozenset({OperationSource.AGENT, OperationSource.SURFACE}),
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
    allowed_sources=frozenset({OperationSource.AGENT, OperationSource.SURFACE}),
    outcomes=("opened",),
    outcome_schemas=NAVIGATION_OUTCOME_SCHEMAS,
    provider_refs=(OWNER_CONTEXT_PROVIDER.ref,),
)
__all__ = [
    "OPEN_AGENTS",
    "OPEN_SOURCES",
    "OPEN_VERIFICATION",
]
