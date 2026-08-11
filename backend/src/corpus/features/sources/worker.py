"""Huey consumer entry point for real Source processing jobs."""

from corpus.app.source_composition import create_source_runtime
from corpus.features.builder.repository import SqlAlchemyBuilderRepository
from corpus.features.evaluation.generation import EvaluationGenerationProcessor
from corpus.features.evaluation.repository import SqlAlchemyEvaluationRepository
from corpus.features.evaluation.tasks import register_evaluation_generation_task
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
register_evaluation_generation_task(
    huey,
    EvaluationGenerationProcessor(
        runtime.infrastructure.job_repository,
        SqlAlchemyEvaluationRepository(database),
        SqlAlchemyBuilderRepository(database),
        runtime.api_engine,
    ),
)


__all__ = ["huey"]
