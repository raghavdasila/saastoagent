from routedeck_core.app import FeatureBindings

from corpus.auth.contracts import AgentOwnerScopeGateway

from .declarations import (
    CREATE_CASE,
    CURRENT_EVALUATION_PROVIDER,
    DELETE_CASE,
    EDIT_CASE,
    GENERATE_SET,
    RETRY_CASE_RUN,
    RETRY_GENERATION,
    RUN_CASE,
)
from .operations import (
    CreateCaseHandler,
    DeleteCaseHandler,
    EditCaseHandler,
    GenerateSetHandler,
    RetryCaseRunHandler,
    RetryGenerationHandler,
    RunCaseHandler,
)
from .providers import CurrentEvaluationProvider
from .service import EvaluationService


def create_evaluation_bindings(
    service: EvaluationService,
    owner_scope: AgentOwnerScopeGateway,
) -> FeatureBindings:
    return FeatureBindings(handlers={
        CREATE_CASE.ref: CreateCaseHandler(service, owner_scope),
        GENERATE_SET.ref: GenerateSetHandler(service, owner_scope),
        RETRY_GENERATION.ref: RetryGenerationHandler(service, owner_scope),
        RETRY_CASE_RUN.ref: RetryCaseRunHandler(service, owner_scope),
        EDIT_CASE.ref: EditCaseHandler(service, owner_scope),
        DELETE_CASE.ref: DeleteCaseHandler(service, owner_scope),
        RUN_CASE.ref: RunCaseHandler(service, owner_scope),
    }, providers={
        CURRENT_EVALUATION_PROVIDER.ref: CurrentEvaluationProvider(service, owner_scope),
    }, guards={})

__all__ = ["create_evaluation_bindings"]
