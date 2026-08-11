"""Huey consumer entry point for real Source processing jobs."""

from corpus.app.source_composition import create_source_runtime
from corpus.app.agent_product_runtime import create_agent_product_runtime
from corpus.app.agents_adapters import CorpusAgentSourceGateway
from corpus.features.agents.repository import SqlAlchemyAgentRepository
from corpus.features.agents.service import AgentService
from corpus.features.evaluation.execution import EvaluationRunProcessor
from corpus.features.evaluation.generation import EvaluationGenerationProcessor
from corpus.features.evaluation.repository import SqlAlchemyEvaluationRepository
from corpus.features.evaluation.service import EvaluationService
from corpus.features.evaluation.tasks import (
    register_evaluation_generation_task,
    register_evaluation_run_task,
)
from corpus.app.delivery_adapters import CorpusEligibilityGateway
from corpus.app.delivery_runtime_adapters import CorpusDeployedAgentRuntimePort
from corpus.app.delivery_runtime_store import CorpusLocalDeliveryStore
from corpus.features.channels.repository import SqlAlchemyChannelRepository
from corpus.features.channels.service import ChannelService
from corpus.features.deployment.execution import DeploymentProcessor
from corpus.features.deployment.repository import SqlAlchemyDeploymentRepository
from corpus.features.deployment.service import DeploymentService
from corpus.features.deployment.tasks import register_deployment_task
from corpus.integrations.agent_delivery import NeutralAgentDeliveryAdapter
from corpus.persistence import CorpusDatabase
from corpus.runtime.config import CorpusRuntimeSettings


settings = CorpusRuntimeSettings.from_env()
database = CorpusDatabase(settings.database.url)
runtime = create_source_runtime(
    database=database,
    source_settings=settings.sources,
    api_settings=settings.api_sources,
    toolrouter_settings=settings.toolrouter,
    infrastructure_settings=settings.infrastructure,
)
huey = runtime.infrastructure.huey
agents = AgentService(
    SqlAlchemyAgentRepository(database),
    CorpusAgentSourceGateway(runtime.service),
)
product_runtime = create_agent_product_runtime(
    settings=settings,
    database=database,
    sources=runtime,
    agents=agents,
)
evaluation_repository = SqlAlchemyEvaluationRepository(database)
register_evaluation_generation_task(
    huey,
    EvaluationGenerationProcessor(
        runtime.infrastructure.job_repository,
        evaluation_repository,
        product_runtime.builder_repository,
        runtime.api_engine,
    ),
)
register_evaluation_run_task(
    huey,
    EvaluationRunProcessor(
        runtime.infrastructure.job_repository,
        evaluation_repository,
        EvaluationService(
            evaluation_repository,
            product_runtime.evaluation_runtime,
            product_runtime.builder_service,
            product_runtime.sandbox_service,
        ),
    ),
)
delivery_store = CorpusLocalDeliveryStore(
    settings.sources.data_root.parent / "agent-delivery" / "runtime.sqlite3"
)
neutral_delivery = NeutralAgentDeliveryAdapter(
    delivery_store,
    CorpusDeployedAgentRuntimePort(
        product_runtime.execution,
        product_runtime.bindings,
        product_runtime.builder_service,
        product_runtime.supervisor,
    ),
)
channel_service = ChannelService(
    SqlAlchemyChannelRepository(database), neutral_delivery, agents
)
deployment_repository = SqlAlchemyDeploymentRepository(database)
register_deployment_task(
    huey,
    DeploymentProcessor(
        runtime.infrastructure.job_repository,
        deployment_repository,
        DeploymentService(
            deployment_repository,
            channel_service,
            product_runtime.builder_service,
            CorpusEligibilityGateway(evaluation_repository),
            neutral_delivery,
            product_runtime.bindings,
        ),
    ),
)


__all__ = ["huey"]
