from routedeck_core.app import FeatureBindings

from corpus.features.agents.ports import AgentOwnerScopeGateway

from .declarations import CREATE_CASE, RUN_CASE
from .operations import CreateCaseHandler, RunCaseHandler
from .service import EvaluationService


def create_evaluation_bindings(service: EvaluationService, owner_scope: AgentOwnerScopeGateway) -> FeatureBindings:
    return FeatureBindings(handlers={
        CREATE_CASE.ref: CreateCaseHandler(service, owner_scope),
        RUN_CASE.ref: RunCaseHandler(service, owner_scope),
    }, providers={}, guards={})

__all__ = ["create_evaluation_bindings"]
