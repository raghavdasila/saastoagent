from routedeck_core.contracts.navigation import NodeRef

from corpus.features.agents.contracts import (
    OPEN_AGENT_BUILDS,
    OPEN_AGENT_CHANNELS,
    RETURN_TO_AGENT_HUB,
)

from .declarations import (
    CREATE_CASE,
    DELETE_CASE,
    EDIT_CASE,
    GENERATE_SET,
    RETRY_CASE_RUN,
    RETRY_GENERATION,
    RUN_CASE,
)

EVALUATION_HOME_REF = NodeRef(id="evaluation.home")
EVALUATION_AGENT_BOUND_OPERATION_IDS = tuple(
    operation.id
    for operation in (
        RETURN_TO_AGENT_HUB,
        OPEN_AGENT_BUILDS,
        GENERATE_SET,
        RETRY_GENERATION,
        CREATE_CASE,
        EDIT_CASE,
        DELETE_CASE,
        RUN_CASE,
        OPEN_AGENT_CHANNELS,
        RETRY_CASE_RUN,
    )
)

__all__ = ["EVALUATION_AGENT_BOUND_OPERATION_IDS", "EVALUATION_HOME_REF"]
