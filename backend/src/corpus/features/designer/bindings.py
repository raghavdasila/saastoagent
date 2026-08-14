from routedeck_core.app import FeatureBindings

from corpus.auth.contracts import AgentOwnerScopeGateway

from .declarations import APPROVE_DESIGN, CUSTOMIZE_DESIGN, DESIGN_CURRENT_PROVIDER, GENERATE_FEATURE, PROPOSE_DESIGN, REQUEST_BUILD, RETURN_TO_AGENT
from .operations import DesignerHandler
from .providers import CurrentDesignProvider
from .service import DesignerService


def create_designer_bindings(
    service: DesignerService,
    owner_scope: AgentOwnerScopeGateway,
    return_to_agent_handler,
) -> FeatureBindings:
    return FeatureBindings(handlers={
        PROPOSE_DESIGN.ref: DesignerHandler(service, owner_scope, PROPOSE_DESIGN.id),
        GENERATE_FEATURE.ref: DesignerHandler(service, owner_scope, GENERATE_FEATURE.id),
        CUSTOMIZE_DESIGN.ref: DesignerHandler(service, owner_scope, CUSTOMIZE_DESIGN.id),
        APPROVE_DESIGN.ref: DesignerHandler(service, owner_scope, APPROVE_DESIGN.id),
        REQUEST_BUILD.ref: DesignerHandler(service, owner_scope, REQUEST_BUILD.id),
        RETURN_TO_AGENT.ref: return_to_agent_handler,
    }, providers={
        DESIGN_CURRENT_PROVIDER.ref: CurrentDesignProvider(service, owner_scope),
    }, guards={})


__all__ = ["create_designer_bindings"]
