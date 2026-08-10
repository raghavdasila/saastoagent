from routedeck_core.app import FeatureBindings

from corpus.features.agents.ports import AgentOwnerScopeGateway

from .declarations import PROMOTE_INTERACTION
from .operations import PromoteInteractionHandler
from .service import OperationsService


def create_operations_bindings(service: OperationsService, owner_scope: AgentOwnerScopeGateway) -> FeatureBindings:
    return FeatureBindings(
        handlers={PROMOTE_INTERACTION.ref: PromoteInteractionHandler(service, owner_scope)},
        providers={},
        guards={},
    )

__all__ = ["create_operations_bindings"]
