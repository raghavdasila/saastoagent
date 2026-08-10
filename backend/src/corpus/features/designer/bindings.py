from routedeck_core.app import FeatureBindings

from corpus.features.agents.operations import OpenAgentAreaHandler
from corpus.features.agents.ports import AgentOwnerScopeGateway
from corpus.features.agents.service import AgentService

from .declarations import APPROVE_DESIGN, CUSTOMIZE_DESIGN, DESIGN_CURRENT_PROVIDER, PROPOSE_DESIGN, REQUEST_BUILD, RETURN_TO_AGENT
from .operations import DesignerHandler
from .providers import CurrentDesignProvider
from .service import DesignerService


def create_designer_bindings(
    service: DesignerService,
    agent_service: AgentService,
    owner_scope: AgentOwnerScopeGateway,
) -> FeatureBindings:
    return FeatureBindings(handlers={
        PROPOSE_DESIGN.ref: DesignerHandler(service, owner_scope, PROPOSE_DESIGN.id),
        CUSTOMIZE_DESIGN.ref: DesignerHandler(service, owner_scope, CUSTOMIZE_DESIGN.id),
        APPROVE_DESIGN.ref: DesignerHandler(service, owner_scope, APPROVE_DESIGN.id),
        REQUEST_BUILD.ref: DesignerHandler(service, owner_scope, REQUEST_BUILD.id),
        RETURN_TO_AGENT.ref: OpenAgentAreaHandler(agent_service, owner_scope, RETURN_TO_AGENT.id, "hub"),
    }, providers={
        DESIGN_CURRENT_PROVIDER.ref: CurrentDesignProvider(service, owner_scope),
    }, guards={})


__all__ = ["create_designer_bindings"]
