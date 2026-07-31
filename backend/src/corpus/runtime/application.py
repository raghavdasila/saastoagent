from __future__ import annotations

from dataclasses import dataclass
from datetime import timedelta

from ollama import AsyncClient, RequestError, ResponseError
from routedeck_core import RouteDeckRuntime, RouteDeckRuntimeServices
from routedeck_core.ports import SessionStoreError, SessionStoreErrorCode
from routedeck_langgraph import (
    RouteDeckLangGraphDriverFactory,
    RouteDeckLangGraphGraphs,
)
from routedeck_sqlalchemy import (
    RouteDeckInstanceLeaseLost,
    SqlAlchemyRuntimeResources,
    open_sqlalchemy_routedeck_runtime,
)

from corpus.app.host import LiveRouteDeckApplication
from corpus.bindings import bind_corpus_app
from corpus.composition import compile_corpus_app
from corpus.session import create_guest_session, initialize_guest_session

from .agent import create_corpus_agent, create_corpus_entry_agent
from .config import CorpusRuntimeSettings
from .model import create_ollama_chat_model


_READINESS_SESSION_ID = "routedeck-readiness-probe"


@dataclass(frozen=True)
class CorpusReadiness:
    runtime: RouteDeckRuntime
    settings: CorpusRuntimeSettings

    async def ready(self) -> bool:
        if not await self._store_ready():
            return False
        return await self._model_ready()

    async def _store_ready(self) -> bool:
        try:
            await self.runtime.services.store.load(_READINESS_SESSION_ID)
        except SessionStoreError as error:
            return error.code in {
                SessionStoreErrorCode.SESSION_NOT_FOUND,
                SessionStoreErrorCode.SESSION_EXPIRED,
            }
        except RouteDeckInstanceLeaseLost:
            return False
        return True

    async def _model_ready(self) -> bool:
        try:
            async with AsyncClient(
                host=str(self.settings.ollama_base_url).rstrip("/"),
                timeout=5.0,
            ) as client:
                response = await client.list()
        except (RequestError, ResponseError):
            return False
        return any(
            model.model == self.settings.ollama_model
            for model in response.models
        )


async def open_live_corpus_application(
    settings: CorpusRuntimeSettings | None = None,
    *,
    owner_context_resolver,
    auth_service,
    auth_limiter,
    auth_mail,
    credential_transition,
) -> LiveRouteDeckApplication:
    configured = settings or CorpusRuntimeSettings.from_env()
    compiled = compile_corpus_app()

    def application_factory(
        resources: SqlAlchemyRuntimeResources,
    ):
        return bind_corpus_app(
            compiled,
            owner_context_resolver,
            auth_service=auth_service,
            auth_limiter=auth_limiter,
            auth_mail=auth_mail,
            auth_settings=configured.auth,
            private_form_store=resources.store,
            private_form_codec=resources.codec,
            credential_transition=credential_transition,
        )

    runtime = await open_sqlalchemy_routedeck_runtime(
        compiled_app=compiled,
        application_factory=application_factory,
        session_factory=create_guest_session,
        session_initializer=initialize_guest_session,
        public_key_validator_factory=lambda _session: None,
        agent_driver_factory=RouteDeckLangGraphDriverFactory(
            graph_factory=lambda services: _create_graphs(configured, services)
        ),
        database_url=configured.host.routedeck_database_url,
        encryption_key=(
            configured.host.routedeck_state_encryption_key.get_secret_value()
        ),
        instance_id=configured.host.routedeck_instance_id,
        review_ttl=timedelta(
            seconds=configured.host.routedeck_review_ttl_seconds
        ),
        resume_capability_ttl=timedelta(
            seconds=configured.host.routedeck_resume_capability_ttl_seconds
        ),
        worker_count=configured.host.routedeck_worker_count,
    )
    return LiveRouteDeckApplication(
        runtime=runtime,
        readiness=CorpusReadiness(runtime=runtime, settings=configured),
    )


def _create_graphs(
    settings: CorpusRuntimeSettings,
    services: RouteDeckRuntimeServices,
) -> RouteDeckLangGraphGraphs:
    return RouteDeckLangGraphGraphs(
        user_message=create_corpus_agent(
            model=create_ollama_chat_model(settings),
            runtime=services,
        ),
        assistant_initiated=create_corpus_entry_agent(
            model=create_ollama_chat_model(settings),
            runtime=services,
        ),
        ignored_event_tags=frozenset(),
    )


__all__ = [
    "CorpusReadiness",
    "open_live_corpus_application",
]
