from routedeck_core.contracts.navigation import NodeRef

from corpus.features.agents.contracts import RETURN_TO_AGENT_HUB

OPERATIONS_HOME_REF = NodeRef(id="operations.home")
OPERATIONS_AGENT_BOUND_OPERATION_IDS = (RETURN_TO_AGENT_HUB.id,)

__all__ = ["OPERATIONS_AGENT_BOUND_OPERATION_IDS", "OPERATIONS_HOME_REF"]
