from __future__ import annotations

from dataclasses import dataclass
from typing import Callable

from corpus.app.agent_routedeck_runtime import AgentRouteDeckSupervisor
from corpus.app.agent_runtime_adapters import (
    CorpusAgentModelPort,
    CorpusApiExecutorPort,
    CorpusBuilderRuntimeGateway,
    CorpusEvaluationReviewerPort,
    CorpusEvaluationRuntimeGateway,
    CorpusExecutionBindingRegistry,
    CorpusSandboxRuntimeGateway,
    CorpusToolRouterPort,
    resolve_ollama_model_identity,
    resolve_openai_model_identity,
)
from corpus.app.agent_runtime_store import CorpusLocalAgentRuntimeStore
from corpus.app.builder_adapters import CorpusBuilderInputGateway
from corpus.app.source_composition import SourceRuntime
from corpus.features.agents.service import AgentService
from corpus.features.builder.repository import SqlAlchemyBuilderRepository
from corpus.features.builder.service import BuilderService
from corpus.features.sandbox.repository import SqlAlchemySandboxRepository
from corpus.features.sandbox.service import SandboxService
from corpus.integrations.agent_execution import (
    NeutralAgentExecutionAdapter,
    NeutralEvaluationAdapter,
)
from corpus.persistence import CorpusDatabase
from corpus.runtime.config import CorpusRuntimeSettings
from corpus.runtime.model import create_chat_model


@dataclass(frozen=True)
class AgentProductRuntime:
    runtime_store: CorpusLocalAgentRuntimeStore
    bindings: CorpusExecutionBindingRegistry
    supervisor: AgentRouteDeckSupervisor
    execution: NeutralAgentExecutionAdapter
    builder_repository: SqlAlchemyBuilderRepository
    builder_service: BuilderService
    sandbox_service: SandboxService
    evaluation_runtime: CorpusEvaluationRuntimeGateway


def create_agent_product_runtime(
    *,
    settings: CorpusRuntimeSettings,
    database: CorpusDatabase,
    sources: SourceRuntime,
    agents: AgentService,
) -> AgentProductRuntime:
    runtime_store = CorpusLocalAgentRuntimeStore(
        settings.sources.data_root.parent / "agent-execution" / "runtime.sqlite3"
    )
    bindings = CorpusExecutionBindingRegistry()
    plain_json = settings.model_provider == "ollama"
    model = CorpusAgentModelPort(
        create_chat_model(settings), plain_json=plain_json
    )
    router = CorpusToolRouterPort(sources.api_engine, bindings, runtime_store)
    executor = CorpusApiExecutorPort(
        sources.routed_execution_adapter, bindings, runtime_store
    )
    supervisor = AgentRouteDeckSupervisor(
        settings.sources.data_root.parent / "agent-routedeck",
        settings.host.routedeck_state_encryption_key.get_secret_value(),
        executor,
    )
    executor.attach_supervisor(supervisor)
    execution = NeutralAgentExecutionAdapter(
        store=runtime_store,
        model=model,
        router=router,
        executor=executor,
    )
    identity = _model_identity(settings)
    builder_repository = SqlAlchemyBuilderRepository(database)
    builder_service = BuilderService(
        builder_repository,
        CorpusBuilderInputGateway(
            database,
            sources.service.repository,
            sources.connection_profiles,
            sources.operation_curation_service,
        ),
        CorpusBuilderRuntimeGateway(execution, identity),
        agents,
    )
    sandbox_service = SandboxService(
        SqlAlchemySandboxRepository(database),
        CorpusSandboxRuntimeGateway(execution, bindings, supervisor),
        builder_service,
    )
    evaluation_runtime = CorpusEvaluationRuntimeGateway(
        NeutralEvaluationAdapter(
            runtime_store,
            CorpusEvaluationReviewerPort(
                model.model,
                identity,
                plain_json=plain_json,
            ),
        )
    )
    return AgentProductRuntime(
        runtime_store=runtime_store,
        bindings=bindings,
        supervisor=supervisor,
        execution=execution,
        builder_repository=builder_repository,
        builder_service=builder_service,
        sandbox_service=sandbox_service,
        evaluation_runtime=evaluation_runtime,
    )


def _model_identity(settings: CorpusRuntimeSettings) -> Callable[[], tuple[str, str]]:
    def identity() -> tuple[str, str]:
        if settings.model_provider == "ollama":
            assert settings.ollama_base_url is not None
            assert settings.ollama_model is not None
            return resolve_ollama_model_identity(
                str(settings.ollama_base_url).rstrip("/"), settings.ollama_model
            )
        assert settings.model_provider == "openai"
        assert settings.openai_model is not None
        return resolve_openai_model_identity(settings.openai_model)

    return identity


__all__ = ["AgentProductRuntime", "create_agent_product_runtime"]
