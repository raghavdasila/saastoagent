from __future__ import annotations

from dataclasses import dataclass

from fastapi import APIRouter
from routedeck_fastapi import SameOriginMutationPolicy

from corpus.auth.config import AuthSettings
from corpus.app.infrastructure import (
    SharedInfrastructure,
    SharedInfrastructureSettings,
    create_shared_infrastructure,
)
from corpus.features.sources import LocalSourceRepository, SourceService
from corpus.features.sources.config import SourceSettings
from corpus.features.sources.connectors.api import (
    ApiGraphPresenter,
    ApiSourceConnector,
    ApiSourceSettings,
    create_api_source_router,
)
from corpus.features.sources.connectors.api.connections import (
    ApiConnectionProfileRepository,
    ApiConnectionService,
)
from corpus.features.sources.connectors.api.contract_revisions import (
    ApiContractRevisionService,
)
from corpus.features.sources.connectors.api.connection_checks import (
    ApiConnectionCheckRepository,
    ApiConnectionCheckService,
)
from corpus.features.sources.connectors.api.operation_curation import (
    ApiOperationCurationService,
)
from corpus.features.sources.connectors.api.route_plans import ApiRoutePlanService
from corpus.integrations.api_execution.adapters import SafeApiExecutionAdapter
from corpus.integrations.api_execution.routed import RoutedApiExecutionAdapter
from corpus.features.sources.connectors.api.routed_executions import (
    ApiRoutedExecutionRepository,
    ApiRoutedExecutionService,
)
from corpus.features.sources.connectors.api.staged_attachments import (
    ApiStagedAttachmentRepository,
    ApiStagedAttachmentService,
)
from corpus.features.sources.connectors.api.staged_descriptions import (
    ApiStagedDescriptionRepository,
    ApiStagedDescriptionService,
)
from corpus.features.sources.lifecycle import SourceLifecycleService
from corpus.app.toolrouter_source_adapter import (
    ToolRouterApiSourceEngine,
)
from corpus.integrations.medusa_acceptance import MedusaContractAcceptanceAdapter
from corpus.features.sources.http import (
    OwnerSessionResolver,
    create_sources_router,
)
from corpus.integrations.toolrouter import ToolRouterAdapter, ToolRouterSettings
from corpus.features.sources.service import SourceJobProcessor
from corpus.features.sources.tasks import register_source_processing_task
from corpus.jobs import SqlAlchemyDurableJobRepository
from corpus.persistence import CorpusDatabase


@dataclass(frozen=True)
class SourceRuntime:
    service: SourceService
    infrastructure: SharedInfrastructure
    graph_presenter: ApiGraphPresenter
    connection_profiles: ApiConnectionProfileRepository
    connection_service: ApiConnectionService
    contract_revision_service: ApiContractRevisionService
    connection_check_service: ApiConnectionCheckService
    operation_curation_service: ApiOperationCurationService
    route_plan_service: ApiRoutePlanService
    routed_execution_service: ApiRoutedExecutionService
    api_engine: ToolRouterApiSourceEngine
    routed_execution_adapter: RoutedApiExecutionAdapter
    staged_attachment_service: ApiStagedAttachmentService
    staged_description_service: ApiStagedDescriptionService


def create_source_runtime(
    *,
    database: CorpusDatabase,
    source_settings: SourceSettings,
    api_settings: ApiSourceSettings,
    toolrouter_settings: ToolRouterSettings,
    infrastructure_settings: SharedInfrastructureSettings,
) -> SourceRuntime:
    """Compose the concrete launch connector behind the generic Sources service."""
    api_engine = ToolRouterApiSourceEngine(ToolRouterAdapter(toolrouter_settings))
    repository = LocalSourceRepository(source_settings.data_root)
    api_connector = ApiSourceConnector(
        api_engine,
        max_upload_bytes=api_settings.max_upload_bytes,
    )
    connectors = (api_connector,)
    processor = SourceJobProcessor(
        repository,
        SqlAlchemyDurableJobRepository(database),
        connectors=connectors,
    )
    infrastructure = create_shared_infrastructure(
        database=database,
        settings=infrastructure_settings,
        job_task_factory=lambda huey: register_source_processing_task(
            huey, processor
        ),
    )
    connection_profiles = ApiConnectionProfileRepository(repository)
    connection_checks = ApiConnectionCheckRepository(repository)
    operation_curations = ApiOperationCurationService(repository)
    route_plans = ApiRoutePlanService(
        sources=repository,
        curations=operation_curations,
        profiles=connection_profiles,
        engine=api_engine,
    )
    routed_records = ApiRoutedExecutionRepository(repository)
    routed_execution_adapter = RoutedApiExecutionAdapter(
        credentials=infrastructure.credentials,
        allowed_base_urls=api_settings.safe_check_allowed_base_urls,
    )
    staged_attachments = ApiStagedAttachmentService(
        repository=ApiStagedAttachmentRepository(source_settings.data_root),
        sources=repository,
        connector=api_connector,
    )
    staged_descriptions = ApiStagedDescriptionService(
        repository=ApiStagedDescriptionRepository(source_settings.data_root),
        sources=repository,
    )
    return SourceRuntime(
        service=SourceService(
            repository,
            connectors=connectors,
            jobs=infrastructure.jobs,
        ),
        infrastructure=infrastructure,
        graph_presenter=ApiGraphPresenter(repository),
        connection_profiles=connection_profiles,
        connection_service=ApiConnectionService(
            connection_profiles,
            infrastructure.credentials,
        ),
        contract_revision_service=MedusaContractAcceptanceAdapter(repository),
        connection_check_service=ApiConnectionCheckService(
            sources=repository,
            profiles=connection_profiles,
            records=connection_checks,
            credentials=infrastructure.credentials,
            execution=SafeApiExecutionAdapter(
                credentials=infrastructure.credentials,
                allowed_base_urls=api_settings.safe_check_allowed_base_urls,
            ),
        ),
        operation_curation_service=operation_curations,
        route_plan_service=route_plans,
        routed_execution_service=ApiRoutedExecutionService(
            sources=repository,
            plans=route_plans,
            records=routed_records,
            execution=routed_execution_adapter,
        ),
        api_engine=api_engine,
        routed_execution_adapter=routed_execution_adapter,
        staged_attachment_service=staged_attachments,
        staged_description_service=staged_descriptions,
    )


def create_source_routers(
    *,
    service: SourceService,
    auth_service: OwnerSessionResolver,
    auth_settings: AuthSettings,
    mutation_policy: SameOriginMutationPolicy,
    api_settings: ApiSourceSettings,
    graph_presenter: ApiGraphPresenter,
    connection_profiles: ApiConnectionProfileRepository,
    contract_revision_service: ApiContractRevisionService,
    connection_check_service: ApiConnectionCheckService,
    operation_curation_service: ApiOperationCurationService,
    route_plan_service: ApiRoutePlanService,
    routed_execution_service: ApiRoutedExecutionService,
    staged_attachment_service: ApiStagedAttachmentService,
    staged_description_service: ApiStagedDescriptionService,
    lifecycle_service: SourceLifecycleService,
) -> tuple[APIRouter, ...]:
    """Compose generic Source transport with connector-owned API upload transport."""
    return (
        create_sources_router(
            service=service,
            auth_service=auth_service,
            mutation_policy=mutation_policy,
            lifecycle_service=lifecycle_service,
        ),
        create_api_source_router(
            service=service,
            auth_service=auth_service,
            mutation_policy=mutation_policy,
            max_upload_bytes=api_settings.max_upload_bytes,
            graph_presenter=graph_presenter,
            connection_profiles=connection_profiles,
            contract_revision_service=contract_revision_service,
            connection_check_service=connection_check_service,
            operation_curation_service=operation_curation_service,
            route_plan_service=route_plan_service,
            routed_execution_service=routed_execution_service,
            staged_attachment_service=staged_attachment_service,
            staged_description_service=staged_description_service,
        ),
    )


__all__ = ["SourceRuntime", "create_source_routers", "create_source_runtime"]
