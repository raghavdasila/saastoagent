from routedeck_core.app import FeatureBindings

from corpus.auth.contracts import AgentOwnerScopeGateway

from .declarations import ACCEPT_SANDBOX_REVIEW, REJECT_SANDBOX_REVIEW, RESUME_SANDBOX, START_SANDBOX
from .operations import ResolveSandboxReviewHandler, ResumeSandboxHandler, StartSandboxHandler
from .service import SandboxService


def create_sandbox_bindings(service: SandboxService, owner_scope: AgentOwnerScopeGateway) -> FeatureBindings:
    return FeatureBindings(
        handlers={
            START_SANDBOX.ref: StartSandboxHandler(service, owner_scope),
            RESUME_SANDBOX.ref: ResumeSandboxHandler(service, owner_scope),
            ACCEPT_SANDBOX_REVIEW.ref: ResolveSandboxReviewHandler(service, owner_scope, True),
            REJECT_SANDBOX_REVIEW.ref: ResolveSandboxReviewHandler(service, owner_scope, False),
        },
        providers={},
        guards={},
    )


__all__ = ["create_sandbox_bindings"]
