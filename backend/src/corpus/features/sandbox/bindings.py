from routedeck_core.app import FeatureBindings

from corpus.features.agents.ports import AgentOwnerScopeGateway

from .declarations import RESUME_SANDBOX, START_SANDBOX
from .operations import ResumeSandboxHandler, StartSandboxHandler
from .service import SandboxService


def create_sandbox_bindings(service: SandboxService, owner_scope: AgentOwnerScopeGateway) -> FeatureBindings:
    return FeatureBindings(
        handlers={
            START_SANDBOX.ref: StartSandboxHandler(service, owner_scope),
            RESUME_SANDBOX.ref: ResumeSandboxHandler(service, owner_scope),
        },
        providers={},
        guards={},
    )


__all__ = ["create_sandbox_bindings"]
