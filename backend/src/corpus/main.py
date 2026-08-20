from __future__ import annotations

from datetime import timedelta

from fastapi import Request
from routedeck_core import RouteDeckRuntime
from routedeck_fastapi import SameOriginMutationPolicy

from corpus.app.host import LiveRouteDeckApplication, create_routedeck_host
from corpus.app.agents_adapters import AuthAgentOwnerScopeGateway, CorpusAgentSourceGateway
from corpus.app.agent_overview_adapters import CorpusAgentProductOverviewGateway
from corpus.app.workspace_adapters import CorpusWorkspaceOverviewGateway
from corpus.app.source_composition import (
    create_source_routers,
    create_source_runtime,
)
from corpus.app.source_lifecycle_adapters import CorpusSourceDependencyGateway
from corpus.features.sources.lifecycle import SourceLifecycleService
from corpus.auth.conversations import create_conversation_router
from corpus.auth.http import (
    AuthHttpProblem,
    auth_problem_response,
    create_auth_router,
)
from corpus.auth.mail import create_mail_delivery
from corpus.auth.operation_http import (
    AuthOperationTokenMiddleware,
    HttpCredentialTransition,
)
from corpus.auth.rate_limits import AuthRateLimiter
from corpus.auth.selector import CorpusSessionSelector
from corpus.auth.session_boundary import (
    RejectDirectRouteDeckSessionCreationMiddleware,
)
from corpus.auth.service import AuthService
from corpus.features.sources.http import (
    SourceHttpProblem,
    source_problem_response,
)
from corpus.features.agents.http import create_agents_router
from corpus.shared.http import CorpusHttpProblem, corpus_problem_response
from corpus.features.agents.repository import SqlAlchemyAgentRepository
from corpus.features.agents.service import AgentService
from corpus.features.agents.overview import AgentProductOverviewService
from corpus.app.designer_adapters import CorpusDesignerGenerationGateway, CorpusDesignerInputGateway
from corpus.features.designer.http import create_designer_router
from corpus.app.designer_repository import SqlAlchemyDesignerRepository
from corpus.app.evaluation_adapters import CorpusEvaluationGenerationGateway
from corpus.features.designer.service import DesignerService
from corpus.runtime.model import create_chat_model
from corpus.features.builder.http import create_builder_router
from corpus.features.builder.execution import BuilderAssemblyProcessor
from corpus.features.builder.tasks import register_builder_assembly_task
from corpus.features.sandbox.http import create_sandbox_router
from corpus.features.sandbox.deployment_service import SandboxDeploymentService
from corpus.features.evaluation.http import create_evaluation_router
from corpus.features.evaluation.repository import SqlAlchemyEvaluationRepository
from corpus.features.evaluation.service import EvaluationService
from corpus.features.evaluation.execution import EvaluationRunProcessor
from corpus.features.evaluation.generation import EvaluationGenerationProcessor
from corpus.features.evaluation.tasks import (
    register_evaluation_generation_task,
    register_evaluation_run_task,
)
from corpus.jobs import HueyDurableJobPort
from corpus.features.channels.http import create_channels_router
from corpus.features.channels.repository import SqlAlchemyChannelRepository
from corpus.features.channels.service import ChannelService
from corpus.features.deployment.repository import SqlAlchemyDeploymentRepository
from corpus.features.deployment.service import DeploymentService
from corpus.features.deployment.execution import DeploymentProcessor
from corpus.features.deployment.tasks import register_deployment_task
from corpus.features.operations.http import create_operations_router
from corpus.features.operations.service import OperationsService
from corpus.app.operations_adapters import CorpusOperationsLineageGateway
from corpus.app.agent_product_runtime import create_agent_product_runtime
from corpus.app.delivery_runtime_store import CorpusLocalDeliveryStore
from corpus.app.delivery_runtime_adapters import CorpusDeployedAgentRuntimePort
from corpus.app.delivery_adapters import CorpusEligibilityGateway
from corpus.integrations.agent_delivery import NeutralAgentDeliveryAdapter
from corpus.features.workspace.http import (
    WorkspaceHttpProblem,
    create_workspace_router,
    workspace_problem_response,
)
from corpus.features.workspace.service import WorkspaceService
from corpus.persistence import CorpusDatabase
from corpus.runtime.application import open_live_corpus_application
from corpus.runtime.config import CorpusRuntimeSettings


def create_live_app(settings: CorpusRuntimeSettings | None = None):
    configured = settings or CorpusRuntimeSettings.from_env()
    database = CorpusDatabase(configured.database.url)
    mail_delivery = create_mail_delivery(configured.auth)
    auth_service = AuthService(
        database,
        reset_secret=configured.auth.reset_secret.get_secret_value(),
        verification_secret=(
            configured.auth.verification_secret.get_secret_value()
        ),
        access_lifetime=timedelta(
            minutes=configured.auth.access_token_minutes
        ),
        idle_lifetime=timedelta(days=configured.auth.idle_session_days),
        absolute_lifetime=timedelta(
            days=configured.auth.absolute_session_days
        ),
        reset_token_lifetime=timedelta(
            hours=configured.auth.reset_token_hours
        ),
        verification_token_lifetime=timedelta(
            hours=configured.auth.verification_token_hours
        ),
    )
    auth_limiter = AuthRateLimiter(database)
    credential_transition = HttpCredentialTransition()
    selector = CorpusSessionSelector(auth_service)
    source_runtime = create_source_runtime(
        database=database,
        source_settings=configured.sources,
        api_settings=configured.api_sources,
        toolrouter_settings=configured.toolrouter,
        infrastructure_settings=configured.infrastructure,
    )
    source_service = source_runtime.service
    source_lifecycle_service = SourceLifecycleService(
        source_runtime.service.repository,
        CorpusSourceDependencyGateway(database),
    )
    agent_service = AgentService(
        SqlAlchemyAgentRepository(database),
        CorpusAgentSourceGateway(source_service),
    )
    agent_owner_scope = AuthAgentOwnerScopeGateway(auth_service)
    designer_service = DesignerService(
        SqlAlchemyDesignerRepository(database),
        CorpusDesignerInputGateway(
            agent_service,
            source_runtime.operation_curation_service,
            source_runtime.graph_presenter,
        ),
        CorpusDesignerGenerationGateway(
            create_chat_model(configured),
            plain_json=configured.model_provider == "ollama",
        ),
    )
    product_runtime = create_agent_product_runtime(
        settings=configured,
        database=database,
        sources=source_runtime,
        agents=agent_service,
    )
    runtime_store = product_runtime.runtime_store
    runtime_bindings = product_runtime.bindings
    agent_routedeck = product_runtime.supervisor
    neutral_execution = product_runtime.execution
    builder_repository = product_runtime.builder_repository
    builder_service = product_runtime.builder_service
    sandbox_service = product_runtime.sandbox_service
    evaluation_repository = SqlAlchemyEvaluationRepository(database)
    evaluation_generation_task = register_evaluation_generation_task(
        source_runtime.infrastructure.huey,
        EvaluationGenerationProcessor(
            source_runtime.infrastructure.job_repository,
            evaluation_repository,
            CorpusEvaluationGenerationGateway(
                builder_repository, source_runtime.api_engine
            ),
        ),
    )
    evaluation_jobs = HueyDurableJobPort(
        source_runtime.infrastructure.job_repository,
        source_runtime.infrastructure.huey,
        evaluation_generation_task,
    )
    evaluation_worker_service = EvaluationService(
        evaluation_repository,
        product_runtime.evaluation_runtime,
        builder_service,
        sandbox_service,
    )
    evaluation_run_task = register_evaluation_run_task(
        source_runtime.infrastructure.huey,
        EvaluationRunProcessor(
            source_runtime.infrastructure.job_repository,
            evaluation_repository,
            evaluation_worker_service,
        ),
    )
    evaluation_run_jobs = HueyDurableJobPort(
        source_runtime.infrastructure.job_repository,
        source_runtime.infrastructure.huey,
        evaluation_run_task,
    )
    evaluation_service = EvaluationService(
        evaluation_repository,
        product_runtime.evaluation_runtime,
        builder_service,
        sandbox_service,
        evaluation_jobs,
        evaluation_run_jobs,
    )
    builder_service.bind_initial_evaluation_scheduler(evaluation_service)
    builder_assembly_task = register_builder_assembly_task(
        source_runtime.infrastructure.huey,
        BuilderAssemblyProcessor(
            source_runtime.infrastructure.job_repository,
            builder_service,
        ),
    )
    builder_service.bind_assembly_jobs(
        HueyDurableJobPort(
            source_runtime.infrastructure.job_repository,
            source_runtime.infrastructure.huey,
            builder_assembly_task,
        )
    )
    delivery_store = CorpusLocalDeliveryStore(
        configured.sources.data_root.parent / "agent-delivery" / "runtime.sqlite3"
    )
    neutral_delivery = NeutralAgentDeliveryAdapter(
        delivery_store,
        CorpusDeployedAgentRuntimePort(
            neutral_execution, runtime_bindings, builder_service, agent_routedeck
        ),
    )
    channel_service = ChannelService(
        SqlAlchemyChannelRepository(database), neutral_delivery, agent_service
    )
    deployment_repository = SqlAlchemyDeploymentRepository(database)
    sandbox_deployment_service = SandboxDeploymentService(
        deployment_repository,
        builder_service,
        neutral_delivery,
        runtime_bindings,
    )
    evaluation_worker_service.bind_sandbox_deployment_runtime(
        sandbox_deployment_service
    )
    evaluation_service.bind_sandbox_deployment_runtime(
        sandbox_deployment_service
    )
    deployment_worker_service = DeploymentService(
        deployment_repository,
        channel_service,
        builder_service,
        CorpusEligibilityGateway(evaluation_repository),
        neutral_delivery,
        runtime_bindings,
    )
    deployment_task = register_deployment_task(
        source_runtime.infrastructure.huey,
        DeploymentProcessor(
            source_runtime.infrastructure.job_repository,
            deployment_repository,
            deployment_worker_service,
        ),
    )
    deployment_jobs = HueyDurableJobPort(
        source_runtime.infrastructure.job_repository,
        source_runtime.infrastructure.huey,
        deployment_task,
    )
    deployment_service = DeploymentService(
        deployment_repository,
        channel_service,
        builder_service,
        CorpusEligibilityGateway(evaluation_repository),
        neutral_delivery,
        runtime_bindings,
        deployment_jobs,
    )
    operations_service = OperationsService(
        neutral_delivery,
        CorpusOperationsLineageGateway(database, neutral_execution),
        evaluation_service,
    )
    agent_overview_service = AgentProductOverviewService(
        CorpusAgentProductOverviewGateway(
            agent_service,
            designer_service,
            builder_service,
            evaluation_service,
            channel_service,
            deployment_service,
            operations_service,
        )
    )
    workspace_service = WorkspaceService(
        CorpusWorkspaceOverviewGateway(auth_service, agent_service, source_service)
    )

    async def open_runtime():
        try:
            await database.verify_revision(
                configured.database.migration_revision
            )
            live = await open_live_corpus_application(
                configured,
                owner_context_resolver=auth_service,
                auth_service=auth_service,
                auth_limiter=auth_limiter,
                auth_mail=mail_delivery,
                credential_transition=credential_transition,
                agent_service=agent_service,
                agent_overview_service=agent_overview_service,
                designer_service=designer_service,
                builder_service=builder_service,
                sandbox_service=sandbox_service,
                evaluation_service=evaluation_service,
                channel_service=channel_service,
                deployment_service=deployment_service,
                operations_service=operations_service,
                workspace_service=workspace_service,
                source_service=source_service,
                source_graph_presenter=source_runtime.graph_presenter,
                source_connection_service=source_runtime.connection_service,
                source_contract_revision_service=source_runtime.contract_revision_service,
                source_connection_check_service=source_runtime.connection_check_service,
                source_operation_curation_service=source_runtime.operation_curation_service,
                source_route_plan_service=source_runtime.route_plan_service,
                source_routed_execution_service=source_runtime.routed_execution_service,
                source_staged_attachment_service=source_runtime.staged_attachment_service,
                source_staged_description_service=source_runtime.staged_description_service,
                source_lifecycle_service=source_lifecycle_service,
            )
        except Exception:
            await database.close()
            raise
        return LiveRouteDeckApplication(
            runtime=live.runtime,
            readiness=live.readiness,
            additional_close=(database.close,),
        )

    host = configured.host
    browser_origins = tuple(
        str(origin).rstrip("/") for origin in host.routedeck_browser_origins
    )
    app = create_routedeck_host(
        title="Corpus",
        live_runtime_factory=open_runtime,
        browser_origins=browser_origins,
        session_selector=selector,
    )
    app.add_middleware(
        AuthOperationTokenMiddleware,
        credential_transition=credential_transition,
        trusted_proxies=configured.auth.trusted_proxies,
    )
    app.add_middleware(RejectDirectRouteDeckSessionCreationMiddleware)
    mutation_policy = SameOriginMutationPolicy(
        trusted_origins=frozenset(browser_origins)
    )
    app.add_exception_handler(AuthHttpProblem, auth_problem_response)
    app.add_exception_handler(CorpusHttpProblem, corpus_problem_response)
    app.add_exception_handler(WorkspaceHttpProblem, workspace_problem_response)
    app.add_exception_handler(SourceHttpProblem, source_problem_response)
    app.include_router(
        create_auth_router(
            service=auth_service,
            limiter=auth_limiter,
            trusted_proxies=configured.auth.trusted_proxies,
            mutation_policy=mutation_policy,
        )
    )
    async def runtime_from_request(request: Request) -> RouteDeckRuntime:
        runtime = getattr(request.app.state, "routedeck_runtime", None)
        if not isinstance(runtime, RouteDeckRuntime):
            raise RuntimeError("RouteDeck runtime is not configured")
        return runtime

    app.include_router(
        create_conversation_router(
            service=auth_service,
            mutation_policy=mutation_policy,
            runtime_provider=runtime_from_request,
        )
    )
    app.include_router(
        create_agents_router(
            service=agent_service,
            owner_scope=agent_owner_scope,
            overview_service=agent_overview_service,
        )
    )
    app.include_router(create_designer_router(designer_service, agent_owner_scope))
    app.include_router(create_builder_router(builder_service, agent_owner_scope))
    app.include_router(create_sandbox_router(
        sandbox_service, sandbox_deployment_service, agent_owner_scope
    ))
    app.include_router(create_evaluation_router(evaluation_service, agent_owner_scope))
    app.include_router(create_channels_router(channel_service, deployment_service, agent_owner_scope, neutral_delivery))
    app.include_router(create_operations_router(operations_service, agent_owner_scope))
    app.include_router(create_workspace_router(workspace_service))
    for source_router in create_source_routers(
        service=source_service,
        auth_service=auth_service,
        auth_settings=configured.auth,
        mutation_policy=mutation_policy,
        api_settings=configured.api_sources,
        graph_presenter=source_runtime.graph_presenter,
        connection_profiles=source_runtime.connection_profiles,
        contract_revision_service=source_runtime.contract_revision_service,
        connection_check_service=source_runtime.connection_check_service,
        operation_curation_service=source_runtime.operation_curation_service,
        route_plan_service=source_runtime.route_plan_service,
        routed_execution_service=source_runtime.routed_execution_service,
        staged_attachment_service=source_runtime.staged_attachment_service,
        staged_description_service=source_runtime.staged_description_service,
        lifecycle_service=source_lifecycle_service,
    ):
        app.include_router(source_router)
    app.state.corpus_auth_service = auth_service
    app.state.corpus_agent_service = agent_service
    app.state.corpus_designer_service = designer_service
    app.state.corpus_builder_service = builder_service
    app.state.corpus_sandbox_service = sandbox_service
    app.state.corpus_sandbox_deployment_service = sandbox_deployment_service
    app.state.corpus_evaluation_service = evaluation_service
    app.state.corpus_channel_service = channel_service
    app.state.corpus_deployment_service = deployment_service
    app.state.corpus_operations_service = operations_service
    app.state.corpus_workspace_service = workspace_service
    app.state.corpus_source_service = source_service
    app.state.corpus_source_jobs = source_runtime.infrastructure.jobs
    return app


__all__ = ["create_live_app"]
