from __future__ import annotations

import asyncio
import uuid
from datetime import UTC, datetime

import httpx

from corpus.credentials.domain import CredentialReference, ResolvedCredential
from corpus.integrations.api_execution._snapshot.contract_revision import openapi_document_hash
from corpus.integrations.api_execution.routed import (
    RoutedApiExecutionAdapter,
    RoutedApiExecutionTarget,
)


OWNER = uuid.UUID("00000000-0000-0000-0000-000000000001")
CREDENTIAL = uuid.UUID("00000000-0000-0000-0000-000000000011")
SECRET = "phase-f-adapter-secret-canary"


class FixedVault:
    async def resolve(self, *, owner_id: uuid.UUID, credential_id: uuid.UUID):
        assert owner_id == OWNER
        assert credential_id == CREDENTIAL
        now = datetime.now(UTC)
        return ResolvedCredential(
            reference=CredentialReference(
                id=CREDENTIAL,
                owner_id=OWNER,
                label="Medusa",
                kind="api_connection_api_key",
                version=3,
                created_at=now,
                updated_at=now,
            ),
            values={"header_name": "x-publishable-api-key", "value": SECRET},
        )


def test_routed_read_executes_once_and_retains_only_redacted_response_identity() -> None:
    seen: list[httpx.Request] = []

    async def respond(request: httpx.Request) -> httpx.Response:
        seen.append(request)
        return httpx.Response(
            200,
            headers={"content-type": "application/json"},
            json={"product_type": {"id": "ptyp_123", "value": SECRET}},
        )

    outcome = asyncio.run(
        _execute(
            operation_id="GetProductTypesId",
            path={"id": "ptyp_123"},
            transport=httpx.MockTransport(respond),
        )
    )

    assert outcome.status == "succeeded"
    assert outcome.delivery == "response_received"
    assert outcome.http_call_count == 1
    assert outcome.outcome_verified is True
    assert outcome.response_body_sha256 is not None
    assert outcome.response_byte_count > 0
    assert len(seen) == 1
    assert seen[0].url.path == "/store/product-types/ptyp_123"
    assert seen[0].headers["x-publishable-api-key"] == SECRET
    retained = repr(outcome)
    assert SECRET not in retained
    assert "response_body=" not in retained
    assert "headers" not in retained


def test_agent_execution_receives_validated_body_only_from_the_in_memory_boundary() -> None:
    async def respond(request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            200,
            headers={"content-type": "application/json"},
            json={"product_type": {"id": "ptyp_123", "value": SECRET}},
        )

    document = _document()
    adapter = RoutedApiExecutionAdapter(
        credentials=FixedVault(),  # type: ignore[arg-type]
        allowed_base_urls=("https://example.com",),
        transport=httpx.MockTransport(respond),
    )
    outcome, response_body = asyncio.run(adapter.execute_for_agent(
        RoutedApiExecutionTarget(
            execution_id="execution-agent1",
            owner_id=OWNER,
            connection_profile_id="profileopaque001",
            base_url="https://example.com",
            authentication_method="api_key",
            credential_name="x-publishable-api-key",
            credential_reference_id=CREDENTIAL,
            credential_version=3,
            document_hash=openapi_document_hash(document),
            document=document,
            operation_id="GetProductTypesId",
            path={"id": "ptyp_123"},
        )
    ))

    assert response_body == {"product_type": {"id": "ptyp_123", "value": SECRET}}
    assert SECRET not in repr(outcome)
    assert outcome.http_call_count == 1


def test_routed_write_requires_explicit_approval_before_transport_and_calls_once() -> None:
    calls = 0

    async def respond(request: httpx.Request) -> httpx.Response:
        nonlocal calls
        calls += 1
        return httpx.Response(
            200,
            headers={"content-type": "application/json"},
            json={"cart": {"id": "cart_123"}},
        )

    blocked = asyncio.run(
        _execute(
            operation_id="CreateCart",
            approved_write=False,
            transport=httpx.MockTransport(respond),
        )
    )
    assert blocked.status == "failed"
    assert blocked.delivery == "not_sent"
    assert blocked.error_code == "write_approval_required"
    assert blocked.http_call_count == 0
    assert calls == 0

    accepted = asyncio.run(
        _execute(
            operation_id="CreateCart",
            approved_write=True,
            transport=httpx.MockTransport(respond),
        )
    )
    assert accepted.status == "succeeded"
    assert accepted.delivery == "response_received"
    assert accepted.http_call_count == 1
    assert calls == 1


def test_routed_write_response_contract_failure_is_unknown_without_retry() -> None:
    calls = 0

    async def respond(request: httpx.Request) -> httpx.Response:
        nonlocal calls
        calls += 1
        return httpx.Response(
            200,
            headers={"content-type": "application/json"},
            json={"unexpected": SECRET},
        )

    outcome = asyncio.run(
        _execute(
            operation_id="CreateCart",
            approved_write=True,
            transport=httpx.MockTransport(respond),
        )
    )

    assert outcome.status == "outcome_unknown"
    assert outcome.delivery == "response_received"
    assert outcome.error_code == "response_contract_outcome_unknown"
    assert outcome.validation_issue_count > 0
    assert outcome.http_call_count == 1
    assert calls == 1
    assert SECRET not in repr(outcome)


def test_routed_read_connect_failure_is_provably_not_sent_with_zero_calls() -> None:
    outcome = asyncio.run(
        _execute(
            operation_id="GetProductTypesId",
            path={"id": "ptyp_123"},
            transport=ConnectFailureTransport(),
        )
    )

    assert outcome.status == "failed"
    assert outcome.delivery == "not_sent"
    assert outcome.error_code == "transport_failed"
    assert outcome.http_call_count == 0


def test_routed_read_timeout_is_possibly_sent_once_and_never_retried() -> None:
    transport = ReadTimeoutTransport()
    outcome = asyncio.run(
        _execute(
            operation_id="GetProductTypesId",
            path={"id": "ptyp_123"},
            transport=transport,
        )
    )

    assert outcome.status == "failed"
    assert outcome.delivery == "possibly_sent"
    assert outcome.error_code == "transport_failed"
    assert outcome.http_call_count == 1
    assert transport.attempts == 1


class ConnectFailureTransport(httpx.AsyncBaseTransport):
    async def handle_async_request(self, request: httpx.Request) -> httpx.Response:
        raise httpx.ConnectError("connection refused", request=request)


class ReadTimeoutTransport(httpx.AsyncBaseTransport):
    def __init__(self) -> None:
        self.attempts = 0

    async def handle_async_request(self, request: httpx.Request) -> httpx.Response:
        self.attempts += 1
        raise httpx.ReadTimeout("response timed out", request=request)


async def _execute(
    *,
    operation_id: str,
    transport: httpx.AsyncBaseTransport,
    path: dict[str, object] | None = None,
    approved_write: bool = False,
):
    document = _document()
    return await RoutedApiExecutionAdapter(
        credentials=FixedVault(),  # type: ignore[arg-type]
        allowed_base_urls=("https://example.com",),
        transport=transport,
    ).execute(
        RoutedApiExecutionTarget(
            execution_id="execution-routed1",
            owner_id=OWNER,
            connection_profile_id="profileopaque001",
            base_url="https://example.com",
            authentication_method="api_key",
            credential_name="x-publishable-api-key",
            credential_reference_id=CREDENTIAL,
            credential_version=3,
            document_hash=openapi_document_hash(document),
            document=document,
            operation_id=operation_id,
            path=path or {},
            approved_write=approved_write,
        )
    )


def _document() -> dict[str, object]:
    return {
        "openapi": "3.0.3",
        "info": {"title": "Routed API", "version": "1"},
        "paths": {
            "/store/product-types/{id}": {
                "get": {
                    "operationId": "GetProductTypesId",
                    "parameters": [
                        {
                            "name": "id",
                            "in": "path",
                            "required": True,
                            "schema": {"type": "string"},
                        },
                        {
                            "name": "x-publishable-api-key",
                            "in": "header",
                            "required": True,
                            "schema": {"type": "string"},
                        },
                    ],
                    "responses": {
                        "200": {
                            "description": "Product type",
                            "content": {
                                "application/json": {
                                    "schema": {
                                        "type": "object",
                                        "required": ["product_type"],
                                        "properties": {
                                            "product_type": {"type": "object"}
                                        },
                                    }
                                }
                            },
                        }
                    },
                }
            },
            "/store/carts": {
                "post": {
                    "operationId": "CreateCart",
                    "parameters": [
                        {
                            "name": "x-publishable-api-key",
                            "in": "header",
                            "required": True,
                            "schema": {"type": "string"},
                        }
                    ],
                    "requestBody": {
                        "required": False,
                        "content": {
                            "application/json": {"schema": {"type": "object"}}
                        },
                    },
                    "responses": {
                        "200": {
                            "description": "Cart",
                            "content": {
                                "application/json": {
                                    "schema": {
                                        "type": "object",
                                        "required": ["cart"],
                                        "properties": {"cart": {"type": "object"}},
                                    }
                                }
                            },
                        }
                    },
                }
            },
        },
    }
