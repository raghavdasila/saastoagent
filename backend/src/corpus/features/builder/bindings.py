from routedeck_core.app import FeatureBindings

from corpus.features.agents.ports import AgentOwnerScopeGateway

from .declarations import ASSEMBLE_BUILD, DELETE_BUILD, PAUSE_BUILD, RUN_BUILD, STOP_BUILD
from .operations import AssembleBuildHandler, BuildRuntimeLifecycleHandler
from .service import BuilderService


def create_builder_bindings(service: BuilderService, owner_scope: AgentOwnerScopeGateway) -> FeatureBindings:
    return FeatureBindings(
        handlers={
            ASSEMBLE_BUILD.ref: AssembleBuildHandler(service, owner_scope),
            RUN_BUILD.ref: BuildRuntimeLifecycleHandler(
                service, owner_scope, RUN_BUILD, "run"
            ),
            PAUSE_BUILD.ref: BuildRuntimeLifecycleHandler(
                service, owner_scope, PAUSE_BUILD, "pause"
            ),
            STOP_BUILD.ref: BuildRuntimeLifecycleHandler(
                service, owner_scope, STOP_BUILD, "stop"
            ),
            DELETE_BUILD.ref: BuildRuntimeLifecycleHandler(
                service, owner_scope, DELETE_BUILD, "delete"
            ),
        },
        providers={},
        guards={},
    )


__all__ = ["create_builder_bindings"]
