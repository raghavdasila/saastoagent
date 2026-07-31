from __future__ import annotations

from fastapi import FastAPI
from fastapi.testclient import TestClient

from corpus.auth.session_boundary import (
    RejectDirectRouteDeckSessionCreationMiddleware,
)


def test_direct_routedeck_session_creation_is_rejected_before_handler() -> None:
    called = False
    app = FastAPI()

    @app.post("/api/routedeck/sessions")
    async def legacy_create():
        nonlocal called
        called = True
        return {"created": True}

    app.add_middleware(RejectDirectRouteDeckSessionCreationMiddleware)
    with TestClient(app) as client:
        response = client.post("/api/routedeck/sessions")

    assert response.status_code == 409
    assert response.json()["code"] == "conversation_creation_required"
    assert called is False
