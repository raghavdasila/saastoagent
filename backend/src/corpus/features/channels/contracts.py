from routedeck_core.contracts.navigation import NodeRef

from corpus.features.agents.contracts import (
    OPEN_AGENT_BUILDS,
    OPEN_AGENT_EVALUATION,
    OPEN_AGENT_OPERATIONS,
    RETURN_TO_AGENT_HUB,
)
from corpus.features.deployment.contracts import (
    DEPLOY_AGENT,
    RETRY_DEPLOYMENT,
    ROLLBACK_DEPLOYMENT,
)

from .declarations import CREATE_CHANNEL, SET_CHANNEL_ENABLED

CHANNELS_HOME_REF = NodeRef(id="channels.home")
CHANNELS_AGENT_BOUND_OPERATION_IDS = tuple(
    operation.id
    for operation in (
        RETURN_TO_AGENT_HUB,
        OPEN_AGENT_EVALUATION,
        OPEN_AGENT_BUILDS,
        CREATE_CHANNEL,
        SET_CHANNEL_ENABLED,
        DEPLOY_AGENT,
        RETRY_DEPLOYMENT,
        ROLLBACK_DEPLOYMENT,
        OPEN_AGENT_OPERATIONS,
    )
)

__all__ = ["CHANNELS_AGENT_BOUND_OPERATION_IDS", "CHANNELS_HOME_REF"]
