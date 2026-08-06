from routedeck_core.app import FeatureBindings

from .declarations import (
    CANCEL_CREATE,
    CREATE_AGENT,
    OPEN_CREATE,
    RETURN_TO_WORKSPACE,
    SAVE_AGENT_CHANGES,
)
from .operations import AgentNavigationHandler, CreateAgentHandler, SaveAgentChangesHandler
from .ports import AgentOwnerScopeGateway
from .service import AgentService


def create_agents_bindings(
    service: AgentService,
    owner_scope: AgentOwnerScopeGateway,
) -> FeatureBindings:
    return FeatureBindings(
        handlers={
            OPEN_CREATE.ref: AgentNavigationHandler(OPEN_CREATE.id),
            RETURN_TO_WORKSPACE.ref: AgentNavigationHandler(RETURN_TO_WORKSPACE.id),
            CANCEL_CREATE.ref: AgentNavigationHandler(CANCEL_CREATE.id),
            CREATE_AGENT.ref: CreateAgentHandler(service, owner_scope),
            SAVE_AGENT_CHANGES.ref: SaveAgentChangesHandler(service, owner_scope),
        },
        providers={},
        guards={},
    )


__all__ = ["create_agents_bindings"]
