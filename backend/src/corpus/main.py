from __future__ import annotations

from datetime import timedelta

from routedeck_core.ports import SessionStoreError
from routedeck_fastapi import SameOriginMutationPolicy

from corpus.app.host import LiveRouteDeckApplication, create_routedeck_host
from corpus.app.source_composition import (
    create_source_routers,
    create_source_service,
)
from corpus.auth.database import AuthDatabase
from corpus.auth.http import (
    AuthHttpProblem,
    auth_problem_response,
    create_auth_router,
)
from corpus.auth.mail import create_mail_delivery
from corpus.auth.rate_limits import AuthRateLimiter
from corpus.auth.selector import CorpusSessionCookieSettings, CorpusSessionSelector
from corpus.auth.service import AuthService
from corpus.features.sources.http import (
    SourceHttpProblem,
    source_problem_response,
)
from corpus.runtime.application import open_live_corpus_application
from corpus.runtime.config import CorpusRuntimeSettings


def create_live_app(settings: CorpusRuntimeSettings | None = None):
    configured = settings or CorpusRuntimeSettings.from_env()
    auth_database = AuthDatabase(configured.auth.database_url)
    mail_delivery = create_mail_delivery(configured.auth)
    auth_service = AuthService(
        auth_database,
        reset_secret=configured.auth.reset_secret.get_secret_value(),
        verification_secret=(
            configured.auth.verification_secret.get_secret_value()
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
    selector = CorpusSessionSelector(
        auth_service,
        CorpusSessionCookieSettings(
            auth_name=configured.auth.auth_cookie_name,
            owner_route_name=configured.auth.owner_route_cookie_name,
            guest_name=configured.host.routedeck_guest_cookie_name,
            secure=configured.host.routedeck_guest_cookie_secure,
            path=configured.host.routedeck_guest_cookie_path,
        ),
    )
    source_service = create_source_service(
        source_settings=configured.sources,
        api_settings=configured.api_sources,
        toolrouter_settings=configured.toolrouter,
    )

    async def open_runtime():
        try:
            await auth_database.verify_revision(
                configured.auth.migration_revision
            )
            live = await open_live_corpus_application(
                configured,
                owner_context_resolver=auth_service,
            )
        except Exception:
            await auth_database.close()
            raise
        return LiveRouteDeckApplication(
            runtime=live.runtime,
            readiness=live.readiness,
            additional_close=(auth_database.close,),
        )

    async def route_session_exists(request, session_id: str) -> bool:
        runtime = getattr(request.app.state, "routedeck_runtime", None)
        if runtime is None:
            return False
        try:
            await runtime.services.store.load(session_id)
        except SessionStoreError:
            return False
        return True

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
    mutation_policy = SameOriginMutationPolicy(
        trusted_origins=frozenset(browser_origins)
    )
    app.add_exception_handler(AuthHttpProblem, auth_problem_response)
    app.add_exception_handler(SourceHttpProblem, source_problem_response)
    app.include_router(
        create_auth_router(
            service=auth_service,
            limiter=AuthRateLimiter(auth_database),
            mail=mail_delivery,
            settings=configured.auth,
            mutation_policy=mutation_policy,
            guest_cookie_name=host.routedeck_guest_cookie_name,
            guest_cookie_path=host.routedeck_guest_cookie_path,
            guest_cookie_secure=host.routedeck_guest_cookie_secure,
            route_session_exists=route_session_exists,
        )
    )
    for source_router in create_source_routers(
        service=source_service,
        auth_service=auth_service,
        auth_settings=configured.auth,
        mutation_policy=mutation_policy,
        api_settings=configured.api_sources,
    ):
        app.include_router(source_router)
    app.state.corpus_auth_service = auth_service
    app.state.corpus_source_service = source_service
    return app


__all__ = ["create_live_app"]
