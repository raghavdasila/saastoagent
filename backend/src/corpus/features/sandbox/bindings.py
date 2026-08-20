from routedeck_core.app import FeatureBindings

from corpus.auth.contracts import AgentOwnerScopeGateway

from .service import SandboxService


def create_sandbox_bindings(service: SandboxService, owner_scope: AgentOwnerScopeGateway) -> FeatureBindings:
    return FeatureBindings(
        handlers={},
        providers={},
        guards={},
    )


__all__ = ["create_sandbox_bindings"]
