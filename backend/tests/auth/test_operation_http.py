from __future__ import annotations

import json
from datetime import UTC, datetime, timedelta
import pytest

from fastapi import FastAPI
from fastapi.testclient import TestClient

from corpus.auth.operation_http import (
    AUTH_REVOKED_HEADER,
    AUTH_TOKENS_HEADER,
    AuthOperationTokenMiddleware,
    HttpCredentialTransition,
)
from corpus.auth.schemas import AnonymousPrincipalView, TokenPairView


def test_operation_credentials_are_explicit_headers_not_cookies_or_projection() -> None:
    now = datetime.now(UTC)
    tokens = TokenPairView(
        access_token="access-secret",
        access_expires_at=now + timedelta(minutes=15),
        refresh_token="refresh-secret",
        refresh_idle_expires_at=now + timedelta(days=7),
        refresh_absolute_expires_at=now + timedelta(days=30),
        principal=AnonymousPrincipalView(),
    )
    app = FastAPI()
    transition = HttpCredentialTransition()
    app.add_middleware(
        AuthOperationTokenMiddleware,
        credential_transition=transition,
    )

    @app.post("/issue")
    async def issue():
        transition.publish_issued_tokens(tokens)
        return {"projection": {"status": "ready"}}

    @app.post("/revoke")
    async def revoke():
        transition.publish_revocation()
        return {"projection": {"status": "ready"}}

    with TestClient(app) as client:
        issued = client.post("/issue")
        revoked = client.post("/revoke")

    assert json.loads(issued.headers[AUTH_TOKENS_HEADER]) == tokens.model_dump(
        mode="json"
    )
    assert "access-secret" not in issued.text
    assert "set-cookie" not in issued.headers
    assert revoked.headers[AUTH_REVOKED_HEADER] == "true"


def test_credential_transition_requires_an_http_request_context() -> None:
    transition = HttpCredentialTransition()

    with pytest.raises(RuntimeError, match="HTTP request context"):
        transition.publish_revocation()
