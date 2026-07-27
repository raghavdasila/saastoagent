from __future__ import annotations

from collections.abc import Awaitable, Callable
from dataclasses import dataclass
from typing import Any

import pytest
from fastapi.testclient import TestClient
from routedeck_fastapi import GuestCookieSessionSelector, GuestCookieSettings

from corpus.app.host import LiveRouteDeckApplication, create_routedeck_host


class ReadinessProbe:
    def __init__(self, ready: bool) -> None:
        self._ready = ready

    async def ready(self) -> bool:
        return self._ready


@dataclass
class RuntimeProbe:
    closed: bool = False

    async def close(self) -> None:
        self.closed = True


def guest_selector() -> GuestCookieSessionSelector:
    return GuestCookieSessionSelector(
        GuestCookieSettings(name="framework_guest", secure=False, path="/")
    )


def live_factory(
    runtime: RuntimeProbe,
    readiness: ReadinessProbe,
) -> Callable[[], Awaitable[LiveRouteDeckApplication]]:
    async def open_live() -> LiveRouteDeckApplication:
        return LiveRouteDeckApplication(
            runtime=runtime,  # type: ignore[arg-type]
            readiness=readiness,
        )

    return open_live


def test_host_mounts_transport_and_closes_the_live_runtime() -> None:
    runtime = RuntimeProbe()
    app = create_routedeck_host(
        title="Framework contract",
        live_runtime_factory=live_factory(runtime, ReadinessProbe(True)),
        browser_origins=("http://127.0.0.1:5199",),
        session_selector=guest_selector(),
    )

    with TestClient(app) as client:
        assert client.get("/healthz").json() == {"status": "ok"}
        assert client.get("/readyz").json() == {"status": "ready"}
        assert "/api/routedeck/session" in app.openapi()["paths"]

    assert runtime.closed is True


def test_host_reports_dependency_unavailability_as_readiness_failure() -> None:
    app = create_routedeck_host(
        title="Framework contract",
        live_runtime_factory=live_factory(RuntimeProbe(), ReadinessProbe(False)),
        browser_origins=("http://127.0.0.1:5199",),
        session_selector=guest_selector(),
    )

    with TestClient(app) as client:
        response = client.get("/readyz")

    assert response.status_code == 503
    assert response.json() == {"status": "unavailable"}


def test_host_rejects_mixed_live_and_injected_composition() -> None:
    with pytest.raises(
        ValueError,
        match="Live runtime composition cannot be combined with injected ports",
    ):
        create_routedeck_host(
            title="Framework contract",
            runtime=Any,  # type: ignore[arg-type]
            readiness=ReadinessProbe(True),
            live_runtime_factory=live_factory(RuntimeProbe(), ReadinessProbe(True)),
            browser_origins=("http://127.0.0.1:5199",),
            session_selector=guest_selector(),
        )
