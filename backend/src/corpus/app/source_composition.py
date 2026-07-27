from __future__ import annotations

from fastapi import APIRouter
from routedeck_fastapi import SameOriginMutationPolicy

from corpus.auth.config import AuthSettings
from corpus.features.sources import LocalSourceRepository, SourceService
from corpus.features.sources.config import SourceSettings
from corpus.features.sources.connectors.api import (
    ApiSourceConnector,
    ApiSourceSettings,
    create_api_source_router,
)
from corpus.features.sources.connectors.api.toolrouter import (
    ToolRouterApiSourceEngine,
)
from corpus.features.sources.http import (
    OwnerSessionResolver,
    create_sources_router,
)
from corpus.integrations.toolrouter import ToolRouterAdapter, ToolRouterSettings


def create_source_service(
    *,
    source_settings: SourceSettings,
    api_settings: ApiSourceSettings,
    toolrouter_settings: ToolRouterSettings,
) -> SourceService:
    """Compose the concrete launch connector behind the generic Sources service."""
    api_engine = ToolRouterApiSourceEngine(ToolRouterAdapter(toolrouter_settings))
    return SourceService(
        LocalSourceRepository(source_settings.data_root),
        connectors=(
            ApiSourceConnector(
                api_engine,
                max_upload_bytes=api_settings.max_upload_bytes,
            ),
        ),
    )


def create_source_routers(
    *,
    service: SourceService,
    auth_service: OwnerSessionResolver,
    auth_settings: AuthSettings,
    mutation_policy: SameOriginMutationPolicy,
    api_settings: ApiSourceSettings,
) -> tuple[APIRouter, ...]:
    """Compose generic Source transport with connector-owned API upload transport."""
    return (
        create_sources_router(
            service=service,
            auth_service=auth_service,
            auth_settings=auth_settings,
            mutation_policy=mutation_policy,
        ),
        create_api_source_router(
            service=service,
            auth_service=auth_service,
            auth_settings=auth_settings,
            mutation_policy=mutation_policy,
            max_upload_bytes=api_settings.max_upload_bytes,
        ),
    )


__all__ = ["create_source_routers", "create_source_service"]
