from routedeck_core.app import FeatureBindings

from .declarations import (
    APPROVE_CONTRACT_REVISION,
    CONTRACT_REVISION_CURRENT_GUARD,
    CONTRACT_REVISION_PROPOSAL_PROVIDER,
    INSPECT_CURRENT_API,
    OPEN_API_CREATION,
    PREPARE_ROUTED_API_TEST,
    PROPOSE_CONTRACT_REVISION,
    RETRY_PROCESSING,
    RETURN_TO_HOME,
    SELECT_GRAPH_STAGE,
    SAVE_API_CONNECTION,
    SAVE_API_OPERATION_CURATION,
    TEST_API_CONNECTION,
    TEST_ROUTED_API_READ,
    TEST_ROUTED_API_WRITE,
    API_CONNECTION_CHECK_CURRENT_GUARD,
    API_OPERATION_CURATION_CURRENT_GUARD,
    ROUTED_API_READ_CURRENT_GUARD,
    ROUTED_API_WRITE_CURRENT_GUARD,
)
from .operations import (
    ApproveContractRevisionHandler,
    GraphStageSelectionHandler,
    InspectCurrentApiHandler,
    ProposeContractRevisionHandler,
    RetrySourceProcessingHandler,
    SaveApiConnectionHandler,
    SaveApiOperationCurationHandler,
    TestApiConnectionHandler,
    SourcesNavigationHandler,
    OpenApiRoutePlanHandler,
    RoutedApiExecutionHandler,
)
from .providers import ContractRevisionProposalProvider
from .guards import (
    ApiConnectionCheckCurrentGuard,
    ApiOperationCurationCurrentGuard,
    ContractRevisionCurrentGuard,
    RoutedApiExecutionCurrentGuard,
)
from .ports import SourceOwnerScopeGateway
from .service import SourceService


def create_sources_bindings(
    service: SourceService,
    owner_scope: SourceOwnerScopeGateway,
    graph_presenter,
    connection_service,
    private_forms,
    contract_revision_service,
    connection_check_service,
    operation_curation_service,
    routed_execution_service=None,
) -> FeatureBindings:
    return FeatureBindings(
        handlers={
            RETURN_TO_HOME.ref: SourcesNavigationHandler(RETURN_TO_HOME.id),
            OPEN_API_CREATION.ref: SourcesNavigationHandler(
                OPEN_API_CREATION.id
            ),
            PREPARE_ROUTED_API_TEST.ref: OpenApiRoutePlanHandler(),
            TEST_ROUTED_API_READ.ref: RoutedApiExecutionHandler(
                routed_execution_service, owner_scope, "read"
            ),
            TEST_ROUTED_API_WRITE.ref: RoutedApiExecutionHandler(
                routed_execution_service, owner_scope, "write"
            ),
            RETRY_PROCESSING.ref: RetrySourceProcessingHandler(
                service, owner_scope
            ),
            SELECT_GRAPH_STAGE.ref: GraphStageSelectionHandler(
                graph_presenter,
                owner_scope,
            ),
            INSPECT_CURRENT_API.ref: InspectCurrentApiHandler(
                graph_presenter,
                operation_curation_service,
                connection_check_service,
                owner_scope,
            ),
            SAVE_API_CONNECTION.ref: SaveApiConnectionHandler(
                connection_service,
                owner_scope,
                private_forms,
            ),
            TEST_API_CONNECTION.ref: TestApiConnectionHandler(
                connection_check_service,
                owner_scope,
            ),
            SAVE_API_OPERATION_CURATION.ref: SaveApiOperationCurationHandler(
                operation_curation_service,
                owner_scope,
            ),
            PROPOSE_CONTRACT_REVISION.ref: ProposeContractRevisionHandler(
                contract_revision_service,
                owner_scope,
            ),
            APPROVE_CONTRACT_REVISION.ref: ApproveContractRevisionHandler(
                contract_revision_service,
                owner_scope,
            ),
        },
        providers={
            CONTRACT_REVISION_PROPOSAL_PROVIDER.ref: ContractRevisionProposalProvider(),
        },
        guards={
            CONTRACT_REVISION_CURRENT_GUARD.ref: ContractRevisionCurrentGuard(
                contract_revision_service,
                owner_scope,
            ),
            API_CONNECTION_CHECK_CURRENT_GUARD.ref: ApiConnectionCheckCurrentGuard(
                connection_check_service,
                owner_scope,
            ),
            API_OPERATION_CURATION_CURRENT_GUARD.ref: ApiOperationCurationCurrentGuard(
                operation_curation_service,
                owner_scope,
            ),
            ROUTED_API_READ_CURRENT_GUARD.ref: RoutedApiExecutionCurrentGuard(
                routed_execution_service, owner_scope, "read"
            ),
            ROUTED_API_WRITE_CURRENT_GUARD.ref: RoutedApiExecutionCurrentGuard(
                routed_execution_service, owner_scope, "write"
            ),
        },
    )


__all__ = ["create_sources_bindings"]
