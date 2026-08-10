"""Huey consumer entry point for real Source processing jobs."""

from corpus.app.source_composition import create_source_runtime
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


__all__ = ["huey"]
