from __future__ import annotations

from collections.abc import Awaitable, Callable, Sequence
from contextlib import asynccontextmanager
from dataclasses import dataclass
from typing import Protocol

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from routedeck_core import RouteDeckRuntime
from routedeck_fastapi import (
    RouteDeckDependencyUnavailable,
    RouteDeckSessionSelector,
    SameOriginMutationPolicy,
    create_routedeck_router_from_runtime_provider,
)


class RouteDeckReadiness(Protocol):
    async def ready(self) -> bool: ...


@dataclass(frozen=True)
class LiveRouteDeckApplication:
    runtime: RouteDeckRuntime
    readiness: RouteDeckReadiness
    additional_close: tuple[Callable[[], Awaitable[None]], ...] = ()

    async def close(self) -> None:
        try:
            await self.runtime.close()
        finally:
            for close in reversed(self.additional_close):
                await close()


async def _runtime_from_request(request: Request) -> RouteDeckRuntime:
    runtime = getattr(request.app.state, "routedeck_runtime", None)
    if not isinstance(runtime, RouteDeckRuntime):
        raise RouteDeckDependencyUnavailable("RouteDeck runtime is not configured")
    return runtime


def create_routedeck_host(
    *,
    title: str,
    browser_origins: Sequence[str],
    session_selector: RouteDeckSessionSelector,
    runtime: RouteDeckRuntime | None = None,
    readiness: RouteDeckReadiness | None = None,
    live_runtime_factory: (
        Callable[[], Awaitable[LiveRouteDeckApplication]] | None
    ) = None,
) -> FastAPI:
    """Mount one generic RouteDeck transport and own its live lifecycle."""

    if live_runtime_factory is not None and (
        runtime is not None or readiness is not None
    ):
        raise ValueError(
            "Live runtime composition cannot be combined with injected ports"
        )
    application = FastAPI(
        title=title,
        lifespan=(
            None
            if live_runtime_factory is None
            else _live_lifespan(live_runtime_factory)
        ),
    )
    application.state.routedeck_runtime = runtime
    application.state.routedeck_readiness = readiness
    trusted_origins = frozenset(browser_origins)
    application.add_middleware(
        CORSMiddleware,
        allow_origins=sorted(trusted_origins),
        allow_credentials=False,
        allow_methods=["*"],
        allow_headers=["*"],
        expose_headers=[
            "X-Corpus-Auth-Tokens",
            "X-Corpus-Auth-Revoked",
            "X-Corpus-Conversation-ID",
        ],
    )
    application.include_router(
        create_routedeck_router_from_runtime_provider(
            _runtime_from_request,
            session_selector=session_selector,
            mutation_policy=SameOriginMutationPolicy(
                trusted_origins=trusted_origins
            ),
        )
    )

    @application.get("/healthz")
    async def health() -> dict[str, str]:
        return {"status": "ok"}

    @application.get("/readyz")
    async def ready(request: Request):
        probe = getattr(request.app.state, "routedeck_readiness", None)
        if probe is None or not await probe.ready():
            return JSONResponse(status_code=503, content={"status": "unavailable"})
        return {"status": "ready"}

    return application


def _live_lifespan(
    factory: Callable[[], Awaitable[LiveRouteDeckApplication]],
):
    @asynccontextmanager
    async def lifespan(application: FastAPI):
        live = await factory()
        try:
            application.state.routedeck_runtime = live.runtime
            application.state.routedeck_readiness = live.readiness
            yield
        finally:
            application.state.routedeck_runtime = None
            application.state.routedeck_readiness = None
            await live.close()

    return lifespan


__all__ = [
    "LiveRouteDeckApplication",
    "RouteDeckReadiness",
    "create_routedeck_host",
]
