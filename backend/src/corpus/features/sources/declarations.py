from __future__ import annotations

from routedeck_core.contracts.navigation import NodeRef
from routedeck_core.contracts.operations import Operation, OperationSource, SafetyClass
from routedeck_core.contracts.projection import FrozenJsonObject

from corpus.features.workspace.declarations import EMPTY_OBJECT_SCHEMA


RETURN_TO_HOME = Operation(
    id="sources.return_to_home",
    title="Return Home",
    description="Return from Sources to the authenticated owner home.",
    input_schema=FrozenJsonObject(EMPTY_OBJECT_SCHEMA),
    safety_class=SafetyClass.NAVIGATION,
    allowed_sources=frozenset({OperationSource.SURFACE}),
    outcomes=("opened",),
    outcome_schemas=FrozenJsonObject({"opened": EMPTY_OBJECT_SCHEMA}),
)

SOURCES_HOME_REF = NodeRef(id="sources.home")


__all__ = ["RETURN_TO_HOME", "SOURCES_HOME_REF"]
