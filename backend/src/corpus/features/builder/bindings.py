from routedeck_core.app import FeatureBindings

from corpus.features.agents.ports import AgentOwnerScopeGateway

from .declarations import ASSEMBLE_BUILD
from .operations import AssembleBuildHandler
from .service import BuilderService


def create_builder_bindings(service: BuilderService, owner_scope: AgentOwnerScopeGateway) -> FeatureBindings:
    return FeatureBindings(
        handlers={ASSEMBLE_BUILD.ref: AssembleBuildHandler(service, owner_scope)},
        providers={},
        guards={},
    )


__all__ = ["create_builder_bindings"]
